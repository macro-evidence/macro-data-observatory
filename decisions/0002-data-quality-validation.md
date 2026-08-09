# 0002. Hard-fail structural checks, soft-warn data anomalies

**Status:** Accepted
**Date:** 2026-07-25

## Context

Two pipelines now share `common.py`'s orchestration, both currently trusting `transform.py`'s output completely — if the World Bank API changed shape, or a transform bug silently dropped most rows, the pipeline would "succeed" with wrong data and nothing would notice. This becomes riskier as more pipelines, and eventually more sources, get added on the same trust assumption.

## Decision

Add a validation step (`validate.py`) between transform and load, called from `common.py`. Two tiers:

- **Hard failures (raise, block the load):** empty frame, missing required columns, non-ISO3 country codes, years outside a sane range, duplicate (country_code, year) rows. These indicate the data is structurally wrong, not just sparse.
- **Soft warnings (log only, load proceeds):** high null-rate in `value`. Missing values are normal — the World Bank has real reporting gaps — so this can't be a hard failure, but a sudden jump is worth a human noticing.

## Consequences

- Every future pipeline (IMF, FRED, additional World Bank indicators) gets this for free by going through `common.py`.
- A legitimately sparse indicator could trip the null-rate warning. It's a warning, not a failure, specifically so this doesn't block a real run — revisit the threshold if it turns out noisy in practice.
- This is structural validation, not statistical/outlier validation (e.g., no check for implausible year-over-year jumps). Reasonable later addition, not required now — no evidence yet it's needed.
