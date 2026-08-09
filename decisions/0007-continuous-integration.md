# 0007. Continuous integration via GitHub Actions

**Status:** Accepted
**Date:** 2026-08-08

## Context

Every pipeline and validation change so far has been verified by manually running `pytest` locally before committing. That's worked, but it's opt-in — nothing stops a future commit from skipping it, and `macro-data-observatory` is now a public AGPL-3.0-only repository where automated verification on every push is a reasonable baseline, not an extra.

Two things made this a small addition rather than a real design problem:

- Every test file is explicitly written to need no network and no database (`get_settings()` only raises when actually called, never on import; every pipeline test mocks around the real DB/engine calls). So CI needs no secrets, no `DATABASE_URL`, and no Postgres service — just checkout, install, run.
- `pyproject.toml` declares `requires-python = ">=3.11"`, but local development runs 3.14.3. Nothing had ever verified the `>=3.11` floor was actually true.

## Decision

Add `.github/workflows/tests.yml`: runs `pytest -v` on every push and on pull requests targeting `main`, across a two-entry matrix (`3.11`, `3.14`) rather than a single version — testing the declared floor and the actually-used version, not just one of them. No services, no secrets required.

A CI status badge was added to `README.md` as a visible trust signal for a public repository, and the Testing section now notes that the same suite runs automatically.

## Consequences

- Every push and PR gets independent verification, closing the gap where a broken commit could land without anyone running the suite.
- CI verifies test-suite correctness only — it does not and cannot replace the real-pipeline-run-against-a-live-API-and-DB gate that caught the IMF forecast-year validation gap (ADR 0005). That gap required live network and a live database, which CI deliberately doesn't have. The two checks are complementary, not redundant: CI catches regressions the unit suite already covers, on every push; the manual live-run gate catches what the unit suite can't, before a milestone ships.
- If `requires-python`'s floor ever changes, the matrix in this workflow should change with it — the two should stay in sync as a matter of course, not by separate reminder.
