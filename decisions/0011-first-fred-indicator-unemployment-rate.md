# 0011. First FRED indicator: unemployment rate (UNRATE)

**Status:** Accepted
**Date:** 2026-08-15

## Context

ADR 0010 established FRED's access pattern (curated series registry) and deliberately left indicator selection to a follow-up decision, noting FRED's search results skew heavily toward US-specific series, distinct from World Bank/IMF's cross-country coverage.

Two live queries were run directly against `fred/series` (exact-ID metadata lookup, not search) before this decision:

- **`UNRATE`**: "Unemployment Rate," Monthly, Seasonally Adjusted, Percent, observation range 1948-01-01–2026-07-01, source code `LNS14000000`.
- **`UNRATENSA`**: same title and range, Not Seasonally Adjusted, source code `LNU04000000`.

This confirms a real, live SA/NSA pair for this specific concept — not just that FRED has SA/NSA pairs somewhere in general (already shown in ADR 0010's `GDP`/`FYFSGDA188S` search results), but that the actual candidate indicator has one.

Two structural facts favor this indicator over the alternative considered (US GDP, already directly verified live in ADR 0010's evidence-gathering):

- **World Bank and IMF already carry US GDP data.** A third GDP figure, from a third source, at a different frequency, creates exactly the "which number is authoritative" ambiguity a data-governance-minded catalogue should avoid introducing. No source in MDO currently carries an unemployment rate for any country — no competing figure to reconcile.
- **`GDP`'s `series/search` result (ADR 0010) showed only a SAAR variant, no confirmed NSA pair.** `UNRATE` has both, live-confirmed above — a more direct exercise of the two properties ADR 0009's schema was built around: real frequency granularity (monthly, not annual) and seasonal adjustment as a genuine per-series dimension, not a hypothetical one.

## Decision

The first FRED pipeline targets `UNRATE` — U.S. unemployment rate, seasonally adjusted, monthly. `UNRATENSA` is not part of this pipeline; ingesting both at once would be building past what a first pipeline needs to prove the pattern end-to-end.

## Consequences

- The FRED series registry (the next implementation artifact per ADR 0010) gets its first real entry: `UNRATE` → country `USA`, frequency `Monthly`/`M`, units `Percent`/`%`, seasonal adjustment `Seasonally Adjusted`/`SA`.
- `UNRATENSA` is now a live-confirmed, ready candidate for a natural second FRED indicator once the first pipeline is proven — mirroring how IMF's `PCPIPCH` (ADR 0006) followed `NGDP_RPCH` (ADR 0004) as a second, evidence-based step rather than being decided upfront. Not decided here; noted because the evidence already exists and shouldn't need rediscovering later.
- `UNRATE`'s observation range starts 1948-01-01, earlier than `validate.py`'s current `MIN_YEAR = 1960`. Whatever date-aware validation logic eventually replaces the year-based check (flagged as a certain, not conditional, need in ADR 0010's Consequences) must not inherit `1960` as a blanket floor across sources — it would incorrectly reject genuine early `UNRATE` data.
