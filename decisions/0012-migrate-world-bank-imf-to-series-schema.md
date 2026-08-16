# 0012. Migrate World Bank and IMF onto the series-first schema

**Status:** Accepted
**Date:** 2026-08-16

## Context

ADR 0009 deferred World Bank/IMF migration explicitly until "FRED discovery starts and a real FRED pipeline exists to prove the new schema against." That condition is now met — ADR 0010 and 0011 produced a live, tested FRED pipeline (943 real observations loaded, 75/75 tests passing). This is that deferred decision, not a new one.

Live evidence gathered directly from the production database and both providers' own APIs before this decision:

| Source | Indicator | Countries | Rows | Years |
|---|---|---|---|---|
| World Bank | `NY.GDP.MKTP.CD` | 260 | 17,160 | 1960–2025 |
| World Bank | `SP.POP.TOTL` | 260 | 17,160 | 1960–2025 |
| IMF | `NGDP_RPCH` | 197 | 9,309 | 1980–2031 |
| IMF | `PCPIPCH` | 197 | 9,234 | 1980–2031 |

**Total: 914 candidate `series` rows, 52,863 candidate `observations` rows.** Both providers already filter aggregate/region rows before load — World Bank via a strict ISO3-validity check, IMF via requiring the country code to appear in a real country-names mapping (confirmed by reading `transform.py` directly). The 260-vs-197 gap reflects World Bank tracking more small economies/territories than IMF, not a data-quality difference. IMF's data extends to 2031 — genuine forecast data, already true under the current `year` column and already handled by the existing year-ceiling logic; the semantics of a sometimes-future date don't change with this migration.

**`indicator_code` is not unique per source for these two providers** — `NY.GDP.MKTP.CD` alone spans all 260 countries. This is structurally different from FRED, where a `series_id` already implies exactly one country.

**Unit metadata was checked live, not assumed, for all four indicators:**
- World Bank's own `unit` field is empirically blank for both indicators (confirmed via `https://api.worldbank.org/v2/indicator/{code}`) — the real unit lives in the `name` field text instead: `"GDP (current US$)"`, `"Population, total"`.
- IMF's `unit` field is populated and directly usable: `"Annual percent change"` for both `NGDP_RPCH` and `PCPIPCH`, verbatim from the live response.
- Population has no unit qualifier in its name at all — a count needs none — so its `units` value is a reasonable inference, not an extracted fact, unlike the other three.

**World Bank's own `sourceNote` for `SP.POP.TOTL` states plainly: "The values shown are midyear estimates."** Population is a stock variable (a snapshot at a point in time); GDP and inflation are flow variables aggregated across a full year, where no single day is more correct than another. These are not the same kind of quantity and don't get the same year-to-date conversion.

**FRED's own live data already establishes real precedent for annual frequency and seasonal adjustment**: `FYFSGDA188S` (confirmed in ADR 0010's evidence) is a genuinely annual FRED series carrying `seasonal_adjustment_short: "NSA"`, not a separate "not applicable" category. FRED — the actual source of this metadata convention — doesn't distinguish "seasonality removed" from "seasonality doesn't apply"; both are NSA in its own real data.

**All four existing pipelines already funnel through one shared chokepoint.** `world_bank_gdp.py` and `world_bank_population.py` call `run_world_bank_indicator()`, which calls `run_pipeline()`; `imf_real_gdp_growth.py` and `imf_inflation.py` call `run_pipeline()` directly. `run_pipeline()` itself is the single place currently hardcoded to `load_indicator()` (confirmed by reading `common.py` directly). Repointing write-behavior is one shared change, not four separate pipeline rewrites.

**`indicator_observations` has no backfill or vintage capability** (ADR 0001, restated in ADR 0009) — full-refresh only. This is the actual table being deprecated below, and its own known limitation is part of why leaving it as a permanent, increasingly-stale parallel copy is worse than a bounded deprecation.

## Decision

Migrate World Bank and IMF fully onto the series-first schema: **backfill existing data into `series`/`observations`, repoint all four pipelines' write path to the new tables going forward, and deprecate `indicator_observations` on a bounded timeline** (frozen once pipelines are repointed, removed after a defined proving period) — not left as an indefinitely-coexisting second copy.

These three parts are one decision, not three: backfilling without repointing the pipelines means the very next pipeline run updates the old table while the new one silently goes stale, undoing the backfill and recreating the exact "which number is authoritative" problem a redundant FRED GDP indicator was rejected for earlier in this project. Deciding to migrate without deciding what happens to the table being migrated *from* would leave the decision's own boundary undefined, the same reasoning ADR 0009 used to bundle its schema decision with its scope.

## Consequences

- `series`'s uniqueness constraint (currently `(source, source_series_id)`, correct for FRED) needs extending to `(source, source_series_id, country_code)` — a required change, not a judgment call, since `indicator_code` alone isn't unique per source for these two providers.
- `source_series_id` = the existing `indicator_code` value verbatim (`"NY.GDP.MKTP.CD"`, `"SP.POP.TOTL"`, `"NGDP_RPCH"`, `"PCPIPCH"`) — already the established, meaningful identifier for each.
- `frequency`/`frequency_short` = `"Annual"`/`"A"`; `seasonal_adjustment`/`seasonal_adjustment_short` = `"Not Seasonally Adjusted"`/`"NSA"` for all four — matching FRED's own real convention for its own annual data, not a new category invented for this migration.
- `units`/`units_short`: `NY.GDP.MKTP.CD` → "Current US$"/"USD"; `SP.POP.TOTL` → "Persons"/"Count" (inferred, not extracted — the one value here without a direct source citation); `NGDP_RPCH` and `PCPIPCH` → "Annual percent change"/"%" (both verbatim from IMF's live response).
- Year-to-date conversion is not uniform across the four series: `SP.POP.TOTL` uses July 1 of the year (evidence-based — World Bank's own stated midyear convention); the other three use January 1 (a labeled convention choice, not an extracted fact, since none of the three sources states a specific within-year timing).
- `common.py`'s shared `run_pipeline()` is the actual implementation target for repointing write-behavior, not four separate pipeline files — smaller real scope than "migrate four pipelines" might suggest on its face.
- The exact deprecation timeline for `indicator_observations` (how long it stays frozen before removal) is **not decided here** — a follow-up decision once the migration is proven in production, mirroring how FRED's indicator selection was deliberately left to its own follow-up ADR (0011) after the access-pattern decision (0010).
- Implementation itself — the backfill script, the `run_pipeline()` change, and the freeze of `indicator_observations` — is separate future work following this decision, same pattern as every prior ADR in this repository.
