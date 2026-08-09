# Macro Data Observatory (MDO)

[![Tests](https://github.com/macro-evidence/macro-data-observatory/actions/workflows/tests.yml/badge.svg)](https://github.com/macro-evidence/macro-data-observatory/actions/workflows/tests.yml)

Macro Data Observatory is an open-source data engineering project for building reproducible ETL pipelines that collect, transform, and store macroeconomic indicators from authoritative public data providers such as the World Bank, IMF, and FRED.

---

## Purpose

The project provides the engineering foundation for collecting, standardizing, and storing macroeconomic indicators in PostgreSQL, forming a reliable data layer for future analytics, dashboards, and forecasting workloads.

---

## Features

- Modular ETL pipeline architecture
- PostgreSQL data storage
- SQLAlchemy database integration
- Environment-based configuration
- Automated testing with Pytest, run in CI on every push
- World Bank and IMF API ingestion
- Structured transformation layer

---

## Data Sources

The project is designed to support data ingestion from:

- World Bank
- International Monetary Fund (IMF)
- Federal Reserve Economic Data (FRED)

---

## Setup

Create and activate a virtual environment before installing dependencies.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install --upgrade pip

pip install -r requirements.txt
pip install -e .

Copy-Item .env.example .env
```

After copying the environment file, update `DATABASE_URL` with your PostgreSQL connection details.

---

Execute a pipeline for a specific indicator:

```
python -m etl.pipelines.world_bank_gdp          # GDP, current US$
python -m etl.pipelines.world_bank_population   # Total population
python -m etl.pipelines.imf_real_gdp_growth     # IMF real GDP growth
python -m etl.pipelines.imf_inflation           # IMF inflation, average consumer prices
```

Each pipeline:

- Downloads the indicator from the source's public API (World Bank or IMF)
- Transforms the raw observations into the project schema
- Validates the result (structural checks; see `src/etl/validate.py`)
- Loads the processed records into the PostgreSQL database

---

## Testing

Run the automated test suite.

```bash
pytest tests/
```

The same suite runs automatically on every push and pull request via [GitHub Actions](.github/workflows/tests.yml), against both the minimum supported Python version and the version used in local development.

---

## Project Status

Implemented:

- World Bank GDP (Current US$) ingestion pipeline
- World Bank total population ingestion pipeline
- IMF real GDP growth ingestion pipeline (DataMapper source; see [decision 0004](decisions/0004-imf-datamapper-discovery-phase.md))
- IMF inflation (average consumer prices) ingestion pipeline (see [decision 0006](decisions/0006-second-imf-indicator-inflation.md))
- Generalized pipeline runner supporting pluggable extract/transform steps per source (`src/etl/pipelines/common.py`; see [decision 0003](decisions/0003-generalized-pipeline-runner.md))
- Data-quality validation before load, including a forecast-aware year ceiling for sources with forward-looking data (see [decision 0005](decisions/0005-widen-validation-year-ceiling.md))
- Continuous integration via GitHub Actions, run on every push and PR (see [decision 0007](decisions/0007-continuous-integration.md))
- End-to-end ETL workflow
- PostgreSQL persistence
- Automated transformation, pipeline, and validation tests

---

## Roadmap

Planned additions include:

- Additional World Bank and IMF indicators
- FRED data integration
- Expanded transformation library
- Pipeline orchestration

---

## Governance

Repository development follows the organization-wide engineering standards maintained in the
[Governance](https://github.com/macro-evidence/governance).

Architectural decisions and significant technical changes specific to this repository are documented in
[`decisions/`](decisions/) before implementation. Decisions that genuinely apply across multiple Macro Evidence repositories are recorded in [governance's `decisions/`](https://github.com/macro-evidence/governance/tree/main/decisions) instead — see [decision 0008](decisions/0008-adr-placement-per-repository.md) for that split.

---

## License

Licensed under the [GNU Affero General Public License v3.0-only](LICENSE) (AGPL-3.0-only).

This license governs the code in this repository. It does not itself grant rights to Macro Evidence's name, logos, or visual identity — see [`TRADEMARKS.md`](https://github.com/macro-evidence/governance/blob/main/TRADEMARKS.md) in the [Governance](https://github.com/macro-evidence/governance) for that separate policy.