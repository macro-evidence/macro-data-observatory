# Architecture Decision Records

This directory contains decisions specific to Macro Data Observatory. Decisions that genuinely apply across multiple Macro Evidence repositories or to the organization's structure belong in the [Governance decision log](https://github.com/macro-evidence/governance/tree/main/decisions).

The shared ADR contract—including numbering, filenames, references, lifecycle metadata, required structure, decision-boundary grammar, and index behavior—is defined in Macro Evidence's [Documentation Standards](https://github.com/macro-evidence/governance/blob/main/DOCUMENTATION_STANDARDS.md#5-architecture-decision-records).

## Decisions

- [0001. Single flat table for Stage 1 ETL, not a dimensional model](0001-single-table-schema-for-stage-1-etl.md)
- [0002. Hard-fail structural checks, soft-warn data anomalies](0002-data-quality-validation.md)
- [0003. Generalize the pipeline runner for pluggable sources](0003-generalized-pipeline-runner.md)
- [0004. IMF source starts on DataMapper, not SDMX](0004-imf-datamapper-discovery-phase.md)
- [0005. Widen validation's year ceiling for forecast-carrying sources](0005-widen-validation-year-ceiling.md)
- [0006. Second IMF indicator: inflation, average consumer prices (PCPIPCH)](0006-second-imf-indicator-inflation.md)
- [0007. Continuous integration via GitHub Actions](0007-continuous-integration.md)
- [0008. ADR placement moves to per-repository decisions folders](0008-adr-placement-per-repository.md)
- [0009. Series-first schema for multi-source ingestion](0009-series-first-dimensional-schema.md)
- [0010. FRED source: curated series registry, not runtime search](0010-fred-discovery-phase.md)
- [0011. First FRED indicator: unemployment rate (UNRATE)](0011-first-fred-indicator-unemployment-rate.md)
- [0012. Migrate World Bank and IMF onto the series-first schema](0012-migrate-world-bank-imf-to-series-schema.md)
- [0013. indicator_observations removal timeline](0013-indicator-observations-removal-timeline.md)
- [0014. Adopt Psycopg 3 as the PostgreSQL driver](0014-adopt-psycopg-3-postgresql-driver.md)
