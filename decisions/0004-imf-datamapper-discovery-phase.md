# 0004. IMF source starts on DataMapper, not SDMX

**Status:** Accepted
**Date:** 2026-08-05

## Context

IMF exposes at least two surfaces: the DataMapper API (used by imf.org's own dashboards) and the SDMX API (the IMF's standards-based statistical data surface). SDMX's migration status as of this decision is unconfirmed — IMF's broader SDMX offering was reported to be mid-migration in 2025, and its current state hasn't been independently verified. DataMapper's behavior has been live-verified directly: it ignores country-path filtering (returns all countries regardless of the path segment, so filtering has to happen client-side) and omits years with null values rather than including them explicitly (so absence of a year key means missing data, not a zero).

## Decision

Build the IMF Foundation milestone against DataMapper. Keep the transport specifics private to `src/etl/sources/imf.py` — `fetch_indicator`, `fetch_indicator_name`, and `fetch_country_names` return IMF concepts (country/year values, labels, names) rather than a DataMapper-shaped response envelope, so a future switch to SDMX only touches this module's internals, not its callers.

## Consequences

- Ships now against a verified, working endpoint instead of blocking on confirming SDMX's migration status.
- The two DataMapper quirks (client-side country filtering, null-omission) are handled once, inside `imf.py` and `transform.py`'s `imf_indicator_values_to_frame`, rather than leaking into every future IMF pipeline.
- If SDMX's status is later confirmed and preferred, migrating means writing new private functions inside `imf.py` with the same public interface — `imf_real_gdp_growth.py` and any future IMF pipeline shouldn't need to change.
- This decision is scoped to the IMF Foundation milestone's discovery phase, not a permanent commitment to DataMapper over SDMX.
