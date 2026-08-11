# 0009. Series-first schema for multi-source ingestion

**Status:** Accepted
**Date:** 2026-08-11

## Context

The current schema (ADR 0001) is a single flat table, `indicator_observations`, keyed on `(source, indicator_code, country_code, year)`. It was deliberately kept flat rather than dimensional, with the explicit plan to revisit "once a second and third source (IMF, FRED) exist and the actual query patterns against this data are known." IMF now exists; FRED is next.

World Bank and IMF share a property the flat schema fits well: one value per country per year, annual only. FRED does not:

- **Frequency varies per series** — daily, weekly, monthly, quarterly, or annual, not fixed at annual. The schema's `year: Integer` column has no way to express a monthly or weekly observation date.
- **Seasonal adjustment is a first-class, queryable attribute** — the same economic concept commonly exists as two separate series, one seasonally adjusted and one not. There is no column anywhere in the current schema for this; it would have to be smuggled into `indicator_code` naming, which the World Bank/IMF pipelines have never needed to do.
- **FRED supports vintage/real-time revision access** — querying a series as it was known as of a past date. Neither World Bank nor IMF pipelines use or need this today; both load a single current snapshot.

Prior art exists among general-purpose open economic-data aggregation projects that ingest from multiple national/international statistical sources into a common schema. The recurring pattern across them is a dimensional split — a `series` table carrying attributes like frequency, unit, seasonal adjustment, and source, joined to an `observations` fact table keyed on `(series_id, date)` — rather than one flat table with source-specific columns added ad hoc. That pattern is corroborating context, not the basis for this decision; the basis is FRED's own API shape, confirmed directly against FRED's documentation.

## Decisions

Two decisions, deliberately scoped narrower than adopting a full dimensional warehouse:

**1. Move to a series-first schema now, ahead of a working FRED pipeline.**
Introduce a `series` table (one row per distinct source + indicator + country + frequency + seasonal-adjustment combination) and an `observations` table (one row per `series_id` + `date`, replacing the per-source `year: Integer` with a real `date`). This is not the full Stage 2 dimensional warehouse ADR 0001 deferred — no separate country or indicator dimension tables yet. It's the minimum change that lets a series carry frequency and seasonal-adjustment as real columns instead of leaving them unrepresented.

**2. Explicitly defer vintage/bi-temporal tracking.**
`observations` stores one `value` per `(series_id, date)` — the latest known value, not a full revision history. FRED's vintage data stays out of scope until a concrete use case needs it. A known technical path exists to add it later — an `observation_vintages` table keyed on `(series_id, date, vintage_date)`, additive to what's decided here — so this defers the work without foreclosing it.

**Sequencing:** World Bank and IMF stay on the current flat schema until FRED discovery starts and a real FRED pipeline exists to prove the new schema against. Migrating World Bank/IMF first, based on FRED's shape alone and before any FRED pipeline has run against it, would mean designing from a specification rather than from evidence — the same failure mode ADR 0001 avoided by deferring dimensional modeling until a second source made the requirements concrete.

## Consequences

- FRED discovery targets the `series`/`observations` shape directly from the start — no throwaway work built against the old flat table for a source that never uses it.
- World Bank and IMF's existing `indicator_observations` table and pipelines are untouched by this decision and keep working exactly as they do today. Their migration onto the new schema is separate, later work, undertaken only after a FRED pipeline has exercised the new schema against real data.
- World Bank and IMF's full-refresh (delete-and-reinsert) loading, per ADR 0001, has no backfill or vintage capability of its own — a prior run's data is gone once overwritten. That's a pre-existing, accepted property of those two sources, independent of this decision. It's noted here only to be explicit that the new schema's deferred vintage support does not retroactively apply to them.
- `validate.py`'s structural checks (required columns, ISO3 codes, year range, duplicate rows) assume annual data via `MAX_YEAR_OFFSET`-style logic. A second validation path for date-based series will be needed once FRED pipelines exist. That change belongs to FRED's own implementation work, not this ADR.
- The `series` + `observations` split referenced under prior art reflects a pattern common across comparable projects, not a specific implementation adopted wholesale — table names, column set, and scope here are decided independently, based on what FRED's API and MDO's own needs actually require.
