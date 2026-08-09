# 0005. Widen validation's year ceiling for forecast-carrying sources

**Status:** Accepted
**Date:** 2026-08-07

## Context

`validate.py`'s hard-fail year-range check used `current_year + 1` as its upper bound. That was correct for World Bank data, which is actuals-only and never carries a future year. Running the IMF real GDP growth pipeline against the live DataMapper API for the first time surfaced the gap directly: 756 of 9,309 transformed rows — exactly 189 countries × 4 years — were rejected as "out of range," because IMF's `NGDP_RPCH` (WEO-based) carries forecasts through 2031, five years past the current year. This is evidence from a real, live run, not a hypothetical.

The check's intent was always to catch structurally corrupt years (typos, encoding bugs, garbage timestamps) — not to assume every source is historical-actuals-only. That assumption held by coincidence while only World Bank existed.

## Decision

Replace the fixed `current_year + 1` ceiling with `current_year + MAX_YEAR_OFFSET`, where `MAX_YEAR_OFFSET = 5` — generous enough to cover IMF's WEO forecast horizon, still tight enough to catch genuinely corrupt years. The check stays a single shared constant across all sources rather than becoming source-aware; World Bank never produces a future year in practice, so the wider ceiling doesn't weaken its protection, and a shared constant stays simple per "necessity over novelty."

Because the offset is computed from `date.today()` each run rather than hardcoded to a specific year, it stays correct as time passes without manual updates — next year's ceiling is next year's `current_year + 5`, automatically.

## Consequences

- IMF's forecast years load correctly without weakening the check's ability to catch actually-corrupt data (a year 20+ years out still hard-fails; covered by `test_far_future_year_raises`).
- If a future source's forecast horizon exceeds 5 years, this constant is the one place to revisit — not a reason to add per-source configuration preemptively.
- This decision exists because a live pipeline run against real data caught a gap that no unit test (all written against synthetic frames) had surfaced. Recorded here rather than silently patched, per this project's evidence-based standard.
