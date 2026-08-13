# 0010. FRED source: curated series registry, not runtime search

**Status:** Accepted
**Date:** 2026-08-13

## Context

Live verification was performed directly against FRED's API (`fred/series/search` and `fred/series/observations`, raw JSON responses reviewed) before this decision, following the same evidence standard used for every prior source in this repository.

Confirmed directly from live responses:

- **FRED is fundamentally series-atomic**, not indicator+country like World Bank/IMF. A single `series_id` (e.g. `GDP`, `GFDEGDQ188S`) already identifies one fully-specified concept, frequency, seasonal-adjustment status, and unit combination. There is no equivalent of DataMapper's indicator-code-plus-country-code combinator.
- **`fred/series/search` returns rich per-series metadata that maps directly onto ADR 0009's `series` table**: `id`, `frequency`/`frequency_short`, `units`/`units_short`, `seasonal_adjustment`/`seasonal_adjustment_short`, `observation_start`/`observation_end`, `last_updated`. A single search for "GDP" returned 80,216 matches, including genuinely distinct series for the same underlying concept at different frequencies and seasonal-adjustment status (`GDP`: quarterly, SAAR; `FYFSGDA188S`: annual, NSA) — direct, first-hand confirmation of the premise ADR 0009 reasoned from documentation alone, and the first live confirmation that those columns are shaped correctly for a real second source.
- **Missing values are represented as the literal string `"."`** in `series/observations` responses (confirmed: four consecutive `"."` values for `GDP` at quarterly points in 1946, before real values begin in 1947). `"."` is not `null`, not absent, not zero — an explicit transform step is required before validation/load, or it will silently corrupt anything expecting a numeric-or-empty field.
- **`realtime_start`/`realtime_end` genuinely control point-in-time access, and vintage access works as documented** — confirmed by requesting the same series with two different explicit dates and observing the response's `realtime_start`/`realtime_end` fields change to match (observation values unchanged in this test; no revision fell inside the tested window). Left unspecified, the parameters default to the request date. This closes the loop on the one FRED-specific unknown ADR 0009 flagged but couldn't verify at the time — the deferral itself is unchanged by this confirmation.
- **The observation response's `observation_start`/`observation_end` fields (`1600-01-01`/`9999-12-31` by default) are the query window's bounds, not the series' actual data range.** The real range comes from `series/search`'s own `observation_start`/`observation_end` fields (`1947-01-01`–`2026-04-01` for `GDP`). Conflating the two would misrepresent a series' actual coverage.
- **FRED's own key-registration documentation does not itself state a numeric rate limit**; third-party sources converge on ~120 requests/minute with a registered key, but this remains unconfirmed against FRED's primary documentation.
- **FRED's search results skew heavily toward series scoped specifically to the United States** (federal debt, federal surplus/deficit, US GDP), distinct in kind from World Bank/IMF's cross-country coverage.

## Decision

Series identification uses a curated registry, not runtime search. `fred/series/search` is a discovery-time tool — used above to find and verify candidate `series_id`s — not a runtime dependency of any pipeline. Each FRED pipeline targets one explicit, hardcoded `series_id`, the same pattern IMF pipelines already use for `NGDP_RPCH`/`PCPIPCH` after discovery determined those specific codes. Querying 80,216 search results at pipeline runtime to re-derive a `series_id` the pipeline already knows would be pure overhead with no benefit.

## Consequences

- A FRED series registry (mapping an MDO concept name to a specific `series_id`, expected frequency, and expected seasonal-adjustment status) is the next concrete implementation artifact — structurally similar to how `list_indicators()` supports IMF, but registry-based rather than discovery-based at runtime.
- FRED's transform layer needs to convert the literal `"."` missing-value marker to a proper null before validation — a source-specific transform step, the same way IMF's transform layer already handles that source's own missing-value conventions. Not a separate architectural decision; implementation work that follows directly from integrating this source.
- Existing `validate.py` structural checks should be reviewed against a FRED series before assuming they apply unchanged — not evaluated here, since no FRED pipeline has been built yet to validate against.
- Which specific FRED indicator ships first is not decided by this ADR. Mirroring how ADR 0004 settled IMF's access pattern before any specific indicator was chosen (with indicator selection following as its own evidence-based step, e.g. ADR 0006 for the second one), indicator selection here is deliberately left to a follow-up decision, informed by FRED's US-focused scope noted in Context.
- The unconfirmed rate limit (Context, third-party sources only) means the eventual FRED pipeline should handle `429`-style responses defensively rather than assume a specific numeric ceiling — a real risk to design for, not a blocker to this decision.
