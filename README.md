# Macro Data Observatory

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
- Automated testing with Pytest
- World Bank API ingestion
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

## Run

Execute the World Bank GDP ingestion pipeline.

```bash
python -m etl.pipelines.world_bank_gdp
```

The pipeline:

- Downloads GDP (Current US$) data from the World Bank API
- Transforms the raw observations into the project schema
- Loads the processed records into the PostgreSQL database

---

## Testing

Run the automated test suite.

```bash
pytest tests/
```

---

## Project Status

Implemented:

- World Bank GDP (Current US$) ingestion pipeline
- End-to-end ETL workflow
- PostgreSQL persistence
- Automated transformation tests

---

## Roadmap

Planned additions include:

- Additional World Bank indicators
- IMF data integration
- FRED data integration
- Expanded transformation library
- Data quality validation
- Pipeline orchestration

---

## Governance

Repository development follows the organization-wide engineering standards maintained in the
[Governance](https://github.com/macro-evidence/governance).

Architectural decisions and significant technical changes are documented in the
[`decisions/`](https://github.com/macro-evidence/governance/tree/main/decisions)
directory before implementation.