"""Load transformed data into Postgres.

Full-refresh per (source, indicator_code): delete existing rows for that
pair, then bulk-insert the fresh frame, in a single transaction. Simple
and correct at this data volume — see decisions/0001.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from .db import indicator_observations, observations, series

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


def load_fred_series_observations(
    frame: pd.DataFrame,
    engine: Engine,
    source_series_id: str,
    country_code: str,
    live_metadata: dict[str, Any],
) -> int:
    """Get-or-create the series row, then full-refresh its observations.

    Two-step write the flat indicator_observations table never needed
    (decision 0009): the series row must exist, and its database-assigned
    id resolved, before observations can reference it via foreign key.
    Both steps happen in one transaction — a failed observations insert
    rolls back a just-created series row too, so a failed run never leaves
    an orphaned series with no data.

    ``live_metadata`` is FRED's own fred/series response for this series
    (title, frequency, units, seasonal_adjustment, and their _short forms)
    — expected already verified against the registry via
    ``sources.fred.verify_registered_metadata`` before this is called;
    this function writes what it's given, it doesn't re-check drift.
    """
    if frame.empty:
        logger.warning("Nothing to load for FRED series %s — empty frame", source_series_id)
        return 0

    with engine.begin() as conn:
        existing = conn.execute(
            select(series.c.id).where(
                series.c.source == "fred",
                series.c.source_series_id == source_series_id,
            )
        ).first()

        if existing is not None:
            series_pk = existing.id
        else:
            result = conn.execute(
                insert(series).values(
                    source="fred",
                    source_series_id=source_series_id,
                    indicator_name=live_metadata["title"],
                    country_code=country_code,
                    frequency=live_metadata["frequency"],
                    frequency_short=live_metadata["frequency_short"],
                    units=live_metadata["units"],
                    units_short=live_metadata["units_short"],
                    seasonal_adjustment=live_metadata["seasonal_adjustment"],
                    seasonal_adjustment_short=live_metadata["seasonal_adjustment_short"],
                    created_at=date.today(),
                )
            )
            series_pk = result.inserted_primary_key[0]

        conn.execute(delete(observations).where(observations.c.series_id == series_pk))

        frame = frame.copy()
        frame["series_id"] = series_pk
        frame.to_sql(observations.name, con=conn, if_exists="append", index=False)

    logger.info(
        "Loaded %s observations for FRED series %s (series_id=%s)",
        len(frame), source_series_id, series_pk,
    )
    return len(frame)
