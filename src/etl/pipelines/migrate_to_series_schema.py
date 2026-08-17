"""One-time backfill: migrate indicator_observations into series/observations
(decision 0012).

Run directly:
    python -m etl.pipelines.migrate_to_series_schema

Reads every (source, indicator_code) pair registered in
SERIES_MIGRATION_REGISTRY from indicator_observations and loads it into
series/observations via load_indicator_observations_by_country. Idempotent
-- safe to re-run, since the load function itself is get-or-create plus
full-refresh -- but this is a one-time migration step per decision 0012,
not a recurring pipeline. It isn't scheduled or re-run routinely once
World Bank/IMF pipelines are repointed (a separate, later task).

Read-only against indicator_observations. Does not delete, freeze, or
otherwise modify it -- that's decision 0012's deprecation step, undertaken
separately once this backfill and the repointed pipelines are both
verified, not part of this script.
"""
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import select

from ..db import create_tables, get_engine, indicator_observations
from ..load import SERIES_MIGRATION_REGISTRY, load_indicator_observations_by_country

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


def run() -> dict[tuple[str, str], int]:
    logger = logging.getLogger("etl.pipelines.migrate_to_series_schema")
    engine = get_engine()
    create_tables(engine)

    results: dict[tuple[str, str], int] = {}

    for source, indicator_code in SERIES_MIGRATION_REGISTRY:
        with engine.connect() as conn:
            rows = conn.execute(
                select(indicator_observations).where(
                    indicator_observations.c.source == source,
                    indicator_observations.c.indicator_code == indicator_code,
                )
            ).mappings().all()

        if not rows:
            logger.warning(
                "No rows found for %s / %s -- skipping", source, indicator_code
            )
            results[(source, indicator_code)] = 0
            continue

        frame = pd.DataFrame(rows)
        logger.info(
            "Read %s rows for %s / %s from indicator_observations",
            len(frame), source, indicator_code,
        )

        n = load_indicator_observations_by_country(frame, engine, source, indicator_code)
        results[(source, indicator_code)] = n

    total = sum(results.values())
    logger.info(
        "Backfill complete: %s total observations migrated across %s indicators",
        total, len(results),
    )
    return results


if __name__ == "__main__":
    run()
