# 0014. Adopt Psycopg 3 as the PostgreSQL driver

**Status:** Accepted
**Date:** 2026-09-17

## Context

MDO accesses PostgreSQL through SQLAlchemy and does not call Psycopg-specific APIs directly. The project had been using `psycopg2-binary` in its concrete development environment. MDO now declares its direct runtime dependencies in `pyproject.toml`, making the PostgreSQL adapter an explicit package contract rather than only a local environment detail.

[Psycopg's current project guidance](https://www.psycopg.org/) treats Psycopg 2 as the legacy generation for existing applications and directs new projects to Psycopg 3. Its [Psycopg 2-to-3 migration guidance](https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html) recommends `psycopg[binary]` for environments that previously used `psycopg2-binary`. [SQLAlchemy 2's PostgreSQL documentation](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#psycopg) provides a dedicated synchronous Psycopg 3 dialect through the `postgresql+psycopg://` URL.

Keeping `psycopg2-binary` as MDO's published runtime dependency would also make the package contract depend on the Psycopg 2 binary distribution, which [Psycopg 2's installation guidance](https://www.psycopg.org/docs/install.html#quick-install) advises published-package maintainers not to use as the package dependency.

## Decision

MDO adopts Psycopg 3 as its PostgreSQL driver.

- `pyproject.toml` declares the base `psycopg` package as the runtime dependency.
- The concrete development/CI environment installs `psycopg[binary]` so contributors and hosted CI do not require a separately provisioned local `libpq` toolchain.
- SQLAlchemy connection URLs use the explicit `postgresql+psycopg://` dialect.
- MDO continues to access PostgreSQL through SQLAlchemy; adopting Psycopg 3 does not introduce driver-specific application APIs as a new architectural dependency.

## Consequences

- Existing private/local `DATABASE_URL` values using `postgresql+psycopg2://` must be migrated explicitly before live execution under the new dependency set.
- The base package metadata remains implementation-neutral with respect to Psycopg's optional C/binary acceleration. The tested development/CI environment deliberately selects the binary implementation for installation simplicity. A future deployment may choose another supported Psycopg implementation without changing MDO's SQLAlchemy-facing architecture, subject to normal verification.
- Psycopg 3 server-side parameter binding and other behavioral differences remain an implementation risk to be caught by live database verification; no compatibility is assumed solely from passing unit tests.
