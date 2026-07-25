"""Shared orchestration for single-indicator World Bank pipelines."""
from __future__ import annotations

import logging

from ..db import create_tables, get_engine
from ..load import load_indicator
from ..sources.world_bank import fetch_indicator
from ..transform import world_bank_records_to_frame

SOURCE = "world_bank"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


def run_world_bank_indicator(indicator_code: str) -> int:
    """Extract, transform, and load a single World Bank indicator.

    Shared by every per-indicator entry point in this package.
    """
    logger = logging.getLogger(f"etl.pipelines.{indicator_code}")
    logger.info("Starting World Bank ingestion (%s)", indicator_code)

    engine = get_engine()
    create_tables(engine)

    raw_records = fetch_indicator(indicator_code)
    logger.info("Fetched %s raw records", len(raw_records))

    frame = world_bank_records_to_frame(raw_records, source=SOURCE)
    logger.info("Transformed to %s country-year rows", len(frame))

    row_count = load_indicator(frame, engine, source=SOURCE, indicator_code=indicator_code)
    logger.info("Pipeline complete: %s rows loaded", row_count)
    return row_count
