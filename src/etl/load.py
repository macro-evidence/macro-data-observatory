"""Load transformed data into Postgres.

Full-refresh per (source, indicator_code): delete existing rows for that
pair, then bulk-insert the fresh frame, in a single transaction. Simple
and correct at this data volume — see governance/decisions/0001.
"""
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.engine import Engine

from .db import indicator_observations

logger = logging.getLogger(__name__)


def load_indicator(
    frame: pd.DataFrame, engine: Engine, source: str, indicator_code: str
) -> int:
    """Replace all rows for (source, indicator_code) with the given frame.

    Delete + insert happen in one transaction: a failed insert rolls the
    delete back too, so a failed run never leaves the table half-empty.
    """
    if frame.empty:
        logger.warning(
            "Nothing to load for %s / %s — empty frame", source, indicator_code
        )
        return 0

    with engine.begin() as conn:
        conn.execute(
            delete(indicator_observations).where(
                indicator_observations.c.source == source,
                indicator_observations.c.indicator_code == indicator_code,
            )
        )
        frame.to_sql(
            indicator_observations.name,
            con=conn,
            if_exists="append",
            index=False,
        )

    logger.info("Loaded %s rows for %s / %s", len(frame), source, indicator_code)
    return len(frame)
