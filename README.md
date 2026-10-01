# Macro Data Observatory (MDO)

[![Verification](https://github.com/macro-evidence/macro-data-observatory/actions/workflows/verification.yml/badge.svg)](https://github.com/macro-evidence/macro-data-observatory/actions/workflows/verification.yml)

Macro Data Observatory (MDO) is the flagship and foundational platform of [Macro Evidence](https://github.com/macro-evidence): open-source macroeconomic data infrastructure for acquiring, validating, structuring, and maintaining data from authoritative public sources through engineered, reproducible pipelines.

The current implementation is a Python ETL system backed by PostgreSQL. It ingests selected World Bank, International Monetary Fund (IMF), and Federal Reserve Economic Data (FRED) series, validates provider data before load, and persists observations through a shared series-first schema.

## Current implementation

| Provider | Indicator or series | Source identifier |
| --- | --- | --- |
| World Bank | GDP (current US$) | `NY.GDP.MKTP.CD` |
| World Bank | Population, total | `SP.POP.TOTL` |
| IMF | Real GDP growth | `NGDP_RPCH` |
| IMF | Inflation, average consumer prices | `PCPIPCH` |
| FRED | US unemployment rate | `UNRATE` |

Provider data is fetched from the providers' public interfaces at run time; this repository does not vendor those upstream datasets.

## Architecture

MDO uses one shared ingestion shape:

```text
source API -> extract -> transform -> validate -> load -> PostgreSQL
```

The active persistence model is series-first:

- `series` stores canonical series metadata and is unique by source, source-series identifier, and country code.
- `observations` stores dated values keyed to a `series` row.
- World Bank and IMF annual indicators use an explicit metadata registry for units, frequency, seasonal adjustment, and year-to-date conventions.
- FRED pipelines verify registered metadata against the provider's live series metadata before loading observations.
- Active load paths use transactional full-refresh semantics for the affected series or country-series group.

The earlier flat `indicator_observations` schema was superseded by the series-first model and physically retired after the proving and verification period defined in [ADR 0013](decisions/0013-indicator-observations-removal-timeline.md). The active database model is documented in [ADR 0009](decisions/0009-series-first-dimensional-schema.md), [ADR 0012](decisions/0012-migrate-world-bank-imf-to-series-schema.md), and the current source under [`src/etl/`](src/etl/).

PostgreSQL access is mediated through SQLAlchemy. MDO uses Psycopg 3 as the PostgreSQL driver; see [ADR 0014](decisions/0014-adopt-psycopg-3-postgresql-driver.md).

## Repository structure

```text
.github/                  CI and dependency-automation configuration
decisions/                repository-specific architecture decision records
src/etl/
  pipelines/              executable ingestion pipelines
  sources/                provider-specific API clients and metadata checks
  db.py                   canonical SQLAlchemy schema and engine
  load.py                 persistence logic and annual-series registry
  transform.py            transformation logic
  validate.py             structural and data-quality validation
tests/                    automated test suite
.env.example              local configuration template
pyproject.toml            package metadata and direct dependency ranges
requirements.txt          fully pinned development/CI environment
```

Organization-wide community-health files such as the Code of Conduct, contribution guide, security policy, issue forms, and pull-request template are inherited from [`macro-evidence/.github`](https://github.com/macro-evidence/.github).

## Local development

### Prerequisites

- Python 3.11 or later
- PostgreSQL
- Node.js and npm only when running the Markdown lint command locally; they are not MDO runtime dependencies

Create and activate a virtual environment:

```text
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install the reviewed development/CI environment, then install MDO itself in editable mode without re-resolving dependencies:

```text
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python -m pip check
```

`pyproject.toml` is the source of MDO's direct runtime dependency ranges and package metadata. `requirements.txt` is the concrete, fully pinned development/CI environment; it deliberately selects Psycopg 3's binary implementation for installation simplicity.

Create the local environment file:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Update `DATABASE_URL` in `.env` with your PostgreSQL connection details. FRED ingestion also requires the API key documented in `.env.example`. Never commit `.env` or credentials.

## Running pipelines

Run a specific ingestion pipeline from the repository root:

```text
python -m etl.pipelines.world_bank_gdp
python -m etl.pipelines.world_bank_population
python -m etl.pipelines.imf_real_gdp_growth
python -m etl.pipelines.imf_inflation
python -m etl.pipelines.fred_unemployment_rate
```

Each pipeline extracts provider data, transforms it into the repository's expected shape, validates it, and loads it transactionally into PostgreSQL.

## Verification

Run the Python test suite:

```text
python -m pytest -v
```

Lint maintained Markdown:

```text
npx --yes markdownlint-cli@0.49.1 --ignore-path .gitignore --ignore decisions/0006-second-imf-indicator-inflation.md --ignore decisions/0012-migrate-world-bank-imf-to-series-schema.md "**/*.md"
npx --yes markdownlint-cli@0.49.1 --config .markdownlint-adr0006.jsonc decisions/0006-second-imf-indicator-inflation.md
npx --yes markdownlint-cli@0.49.1 --config .markdownlint-adr0012.jsonc decisions/0012-migrate-world-bank-imf-to-series-schema.md
```

The main Markdown configuration enables the standard rule set except line-length enforcement. Two accepted historical ADRs retain narrow file-specific formatting exceptions without weakening the repository-wide rule set.

GitHub Actions runs Markdown verification plus the Python suite on every push and on pull requests targeting `main`. Python tests run against the declared minimum Python version and the current upper tested development line; see [`.github/workflows/verification.yml`](.github/workflows/verification.yml).

## Updating dependencies

Treat `pyproject.toml` and `requirements.txt` as different layers:

- change direct supported dependency ranges in `pyproject.toml` deliberately;
- regenerate `requirements.txt` only from a clean temporary virtual environment;
- review the complete pin diff rather than freezing an existing maintainer environment;
- run `pip check`, the full test suite, and the applicable live integration gates before accepting the update.

A controlled full refresh starts from a clean temporary environment using the current upper CI development line (currently Python 3.14) and the CI-pinned pip version:

```text
python -m pip install --upgrade pip==26.2.1
python -m pip install -e ".[dev]"
python -m pip install "psycopg[binary]>=3.3.5,<4"
python -m pip check
python -m pip freeze --exclude-editable > requirements.next.txt
```

`pip freeze` records Psycopg's base and binary distributions as separate pins; `requirements.txt` intentionally mirrors that concrete installed state. Review `requirements.next.txt` against `requirements.txt`. Replace the committed pin set only after the dependency changes are understood and verified; do not regenerate it from an environment that already contains unrelated packages. Routine version-update pull requests may update individual pins, but a full refresh must still use this clean-environment procedure.

## Architecture decisions

Repository-specific architectural decisions are recorded in [`decisions/`](decisions/). Material changes should follow the ADR grammar and lifecycle rules in Macro Evidence's [Documentation Standards](https://github.com/macro-evidence/governance/blob/main/DOCUMENTATION_STANDARDS.md).

Cross-repository decisions belong in the [Governance decision log](https://github.com/macro-evidence/governance/tree/main/decisions), as established by [ADR 0008](decisions/0008-adr-placement-per-repository.md).

## Governance, contribution, and security

MDO is governed by Macro Evidence's public organization-level policies and standards:

- [Governance](https://github.com/macro-evidence/governance/blob/main/GOVERNANCE.md) defines decision-making and repository stewardship.
- [Documentation Standards](https://github.com/macro-evidence/governance/blob/main/DOCUMENTATION_STANDARDS.md) owns shared documentation and ADR conventions.
- [Contribution Policy](https://github.com/macro-evidence/governance/blob/main/CONTRIBUTION_POLICY.md) owns organization-wide participation, acceptance, provenance, and contributor-rights requirements.
- The organization [contribution guide](https://github.com/macro-evidence/.github/blob/main/CONTRIBUTING.md) provides the default GitHub contribution process.
- Security vulnerabilities should follow the organization [Security Policy](https://github.com/macro-evidence/.github/blob/main/SECURITY.md) and private vulnerability-reporting path rather than public issues.

Repository-specific setup, implementation, tests, and ADRs remain owned here rather than being duplicated in governance documents.

## License and upstream data

Macro Data Observatory is distributed under the [GNU Affero General Public License v3.0-only](LICENSE) (`AGPL-3.0-only`).

Data retrieved from the World Bank, IMF, FRED, or another upstream provider remains subject to the applicable provider terms, licenses, attribution requirements, and source limitations. The MDO project license does not relicense upstream provider data.

Rights in Macro Evidence's name, logos, and visual identity are separate from the project license; see the organization [Trademarks Policy](https://github.com/macro-evidence/governance/blob/main/TRADEMARKS.md).
