# 0003. Generalize the pipeline runner for pluggable sources

**Status:** Accepted
**Date:** 2026-08-05

## Context

`common.py`'s `run_world_bank_indicator` orchestrates extract, transform, validate, and load for every World Bank pipeline, giving each a 4-line thin wrapper. IMF ingestion needs the same validate/load guarantees (per ADR 0002), but its extraction shape differs: World Bank's single `fetch_indicator` call returns ready-to-transform records, while IMF needs three calls — values, indicator label, and country names — bundled before transform can run. `run_world_bank_indicator`'s signature has no room for that.

## Decision

Split `common.py` into two layers:

- `run_pipeline(indicator_code, source, extract, transform)`: the actual orchestration (engine, table creation, validate, load), taking `extract` and `transform` as source-supplied callables. `extract` returns whatever raw payload the source needs; `transform` turns that payload into the tidy `indicator_observations` frame. Neither is constrained in shape beyond that.
- `run_world_bank_indicator(indicator_code)`: a thin World-Bank-specific binding over `run_pipeline`, preserved so `world_bank_gdp.py` and `world_bank_population.py` don't change.

IMF's pipeline (`imf_real_gdp_growth.py`) defines its own `_extract` (bundles the three IMF calls into one payload) and `_transform` (unpacks that payload into `imf_indicator_values_to_frame`), then calls `run_pipeline` directly — the same shape as the World Bank binding, just not given its own named wrapper function since it's the only IMF pipeline so far.

## Consequences

- Every current and future pipeline (World Bank, IMF, FRED) gets validation and load behavior from one place, restoring the guarantee ADR 0002 described.
- Sources with unusual extraction shapes (like IMF's three-call bundle) no longer have to fight a runner built around a single fetch call.
- A second IMF pipeline would either get its own thin wrapper (mirroring `run_world_bank_indicator`) or keep calling `run_pipeline` directly — revisit once there's a second one to compare against, not before.
- No change to `validate.py` or `load.py`; both already operated on the tidy frame regardless of source.
