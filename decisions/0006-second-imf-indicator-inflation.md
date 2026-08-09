# 0006. Second IMF indicator: inflation, average consumer prices (PCPIPCH)

**Status:** Accepted
**Date:** 2026-08-08

## Context

With `list_indicators()` built and run live against the IMF DataMapper API, the observatory's mission — infrastructure for high-stakes economic and financial decisions — points at inflation as the natural second indicator: real GDP growth plus inflation is the standard two-series macro snapshot underlying most such decisions.

`list_indicators()`'s live output surfaced four inflation-labeled codes, forming two pairs on the same pattern already seen with GDP growth (`NGDP_RPCH` vs `NGDP_R_PCH`) — two codes per concept, one canonical and one thin/legacy:

| Code | Label |
|---|---|
| `PCPIPCH` | Inflation rate, average consumer prices |
| `PCPI_PCH` | Consumer Prices, Average (Annual % Change) |
| `PCPIEPCH` | Inflation rate, end of period consumer prices |
| `PCPIE_PCH` | Consumer Prices, End of Period (Annual % Change) |

Two decisions were needed: which concept (average vs. end-of-period), and which code for that concept.

## Decision

**Concept:** average consumer prices — this is IMF WEO's own headline inflation figure, the one that appears alongside real GDP growth in WEO's standard summary tables.

**Code:** `PCPIPCH`, confirmed against live data rather than by naming pattern alone. Fetching both average-CPI candidates directly:

- `PCPIPCH`: 228 countries, 10,789 data points, USA populated back to 1980.
- `PCPI_PCH`: 67 countries, 1,592 data points, USA empty.

This matches the `NGDP_RPCH`/`NGDP_R_PCH` pattern exactly — the no-underscore-before-`PCH` form is the real, actively-populated DataMapper series; the underscore variant is thin or legacy. `PCPIPCH` is the pick.

## Consequences

- `imf_inflation.py` ships as a thin binding over the shared `run_pipeline` runner, identical in shape to `imf_real_gdp_growth.py` — no changes needed to `common.py`, `validate.py`, or the transform layer.
- The naming-pattern hypothesis (no-underscore form = canonical) held for a second indicator pair, but this decision was made from live evidence for this specific pair, not by extending the pattern on faith — worth re-verifying per-indicator if a third pair of duplicate-looking codes shows up for a future indicator, rather than assuming the pattern always holds.
- Inflation values can legitimately be negative (deflation); no validation change was needed since `validate.py` doesn't constrain value sign or range, only structural shape.
