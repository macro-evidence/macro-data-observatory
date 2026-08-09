# Architecture Decision Records

Non-trivial technical decisions for Macro Data Observatory are recorded here, per [`GOVERNANCE.md`](https://github.com/macro-evidence/governance/blob/main/GOVERNANCE.md) §5.

These are decisions specific to this repository. Decisions that genuinely apply across multiple Macro Evidence repositories are recorded in [`governance/decisions/`](https://github.com/macro-evidence/governance/tree/main/decisions) instead — see that folder's own README for the distinction.

## Format

One file per decision: `NNNN-short-title.md`, numbered sequentially, using:

```
# NNNN. Short title

**Status:** Proposed / Accepted / Superseded
**Date:** YYYY-MM-DD

## Context
What problem or question this addresses.

## Decision
What was decided.

## Consequences
Expected benefits, trade-offs, risks, and follow-up implications.
```

## Decisions

- [0001. Single flat table for Stage 1 ETL, not a dimensional model](0001-single-table-schema-for-stage-1-etl.md)
- [0002. Hard-fail structural checks, soft-warn data anomalies](0002-data-quality-validation.md)
- [0003. Generalize the pipeline runner for pluggable sources](0003-generalized-pipeline-runner.md)
- [0004. IMF source starts on DataMapper, not SDMX](0004-imf-datamapper-discovery-phase.md)
- [0005. Widen validation's year ceiling for forecast-carrying sources](0005-widen-validation-year-ceiling.md)
- [0006. Second IMF indicator: inflation, average consumer prices (PCPIPCH)](0006-second-imf-indicator-inflation.md)
- [0007. Continuous integration via GitHub Actions](0007-continuous-integration.md)
- [0008. ADR placement moves to per-repository decisions folders](0008-adr-placement-per-repository.md)
