# 0001. Single flat table for Stage 1 ETL, not a dimensional model

**Status:** Accepted
**Date:** 2026-07-24

## Context

MDO's first pipeline (World Bank GDP ingestion) needs somewhere to land data in Postgres. The long-term roadmap calls for a "Structured Data Warehouse" at Stage 2, implying proper dimensional modeling — separate country and indicator dimension tables, with a fact table referencing them.

## Decision

For Stage 1, use a single flat table, `indicator_observations`, with a natural composite key (`source`, `indicator_code`, `country_code`, `year`), rather than building dimension tables now.

Also: each pipeline run does a full delete-and-reinsert for its `(source, indicator_code)` pair, rather than row-level upsert logic. At GDP's data volume (on the order of 10,000–15,000 rows across all countries and years), a full refresh is fast and trivially idempotent — there's no meaningful cost to accept from skipping upsert logic at this stage.

## Consequences

- Faster to ship a working pipeline; no schema-migration tooling needed yet.
- Some redundancy across rows (country and indicator names repeated per row) that a dimensional model would normalize away — acceptable at this data volume.
- Revisit at Stage 2, once a second and third source (IMF, FRED) exist and the actual query patterns against this data are known — designing dimensions before that is guessing at requirements, which the decision criteria (necessity, simplicity) argue against.
- Full-refresh load is wrapped in a single transaction, so a failed mid-run fetch can't corrupt existing data — but it does mean every run re-fetches the entire indicator rather than only new data. Acceptable given the World Bank API has no rate limit this volume would hit.
