# 0013. indicator_observations removal timeline

**Status:** Accepted
**Date:** 2026-08-19

## Context

Decision 0012 froze `indicator_observations` (no longer written to by any pipeline) but explicitly deferred its exact removal timeline as a follow-up decision. This is that decision.

Live evidence since the freeze took effect: the backfill (2026-08-17) and a full live re-run of all four repointed pipelines (same day) both confirmed `indicator_observations`'s row count matching exactly — 52,863 both times, before and after real pipeline execution against live external APIs. The freeze is holding correctly in production, not just in code.

**What removing the table actually costs, precisely:** the underlying economic data itself is not at risk — it's already verified present and matching exactly in `series`/`observations` (row counts, spot-checked missing values, both date conventions confirmed against real data). What would be lost is the old flat table's own format as a historical artifact, not the data it once held.

**What removing it too early risks:** less production-proving time for `load_indicator_observations_by_country` — the get-or-create-per-country load pattern, exercised for the first time in production during this migration — before the fallback reference is gone.

**The table's value as a fallback does not compound with more waiting time.** It's frozen; it will never reflect data more recent than the migration moment. A longer wait doesn't make the old table a *better* safety net, it only makes it a more stale one. The case for waiting is entirely about building confidence in the new load pattern through observed real-world cycles, not about the old table itself becoming more valuable.

## Decision

`indicator_observations` is retained, frozen, for **30 calendar days from the migration's verified completion (2026-08-17 → 2026-09-16)**, then dropped. Thirty days is chosen to allow at least one natural World Bank/IMF data-refresh cycle to be observed under the new load pattern in production, without treating the old table's continued existence as an open-ended requirement its own decaying value doesn't justify.

## Consequences

- On or after 2026-09-16, `indicator_observations` can be dropped — a deliberate manual action (a small script or direct `DROP TABLE`), not an automated or scheduled deletion.
- Before dropping, re-verify `series`/`observations` still matches the expected state at that time (row counts, spot checks) — the same evidence standard used throughout this migration, not assumed to still hold just because it held on 2026-08-17.
- Until then, `indicator_observations` remains in the database exactly as it is now — frozen, 52,863 rows, negligible storage cost, purely a rollback reference.
