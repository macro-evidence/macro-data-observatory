"""Entry point: World Bank GDP (current US$) ingestion.

Run directly:
    python -m etl.pipelines.world_bank_gdp
"""
from __future__ import annotations

import logging

from ..db import create_tables, get_engine
from ..load import load_indicator
from ..sources.world_bank import fetch_indicator
from ..transform import world_bank_records_to_frame

INDICATOR_CODE = "NY.GDP.MKTP.CD"
SOURCE = "world_bank"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def run() -> int:
    logger.info("Starting World Bank GDP ingestion (%s)", INDICATOR_CODE)

    engine = get_engine()
    create_tables(engine)

    raw_records = fetch_indicator(INDICATOR_CODE)
    logger.info("Fetched %s raw records", len(raw_records))

    frame = world_bank_records_to_frame(raw_records, source=SOURCE)
    logger.info("Transformed to %s country-year rows", len(frame))

    row_count = load_indicator(frame, engine, source=SOURCE, indicator_code=INDICATOR_CODE)
    logger.info("Pipeline complete: %s rows loaded", row_count)
    return row_count


if __name__ == "__main__":
    run()
