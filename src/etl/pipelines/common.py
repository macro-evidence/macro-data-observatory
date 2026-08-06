"""Shared orchestration for pipelines.

`run_pipeline` is source-agnostic: it wires extract -> transform ->
validate -> load identically for every pipeline. Each source supplies
its own `extract` (indicator_code -> raw payload, whatever shape that
source needs) and `transform` (raw payload -> tidy indicator_observations
frame). This is what lets IMF, World Bank, and future sources (FRED)
share validation and load behavior without sharing extraction shape.

`run_world_bank_indicator` is a thin World-Bank-specific binding kept
for the existing World Bank pipeline entry points.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

import pandas as pd

from ..db import create_tables, get_engine
from ..load import load_indicator
from ..sources.world_bank import fetch_indicator as fetch_world_bank_indicator
from ..transform import world_bank_records_to_frame
from ..validate import validate_frame

WORLD_BANK_SOURCE = "world_bank"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


def run_pipeline(
    indicator_code: str,
    source: str,
    extract: Callable[[str], Any],
    transform: Callable[[Any], pd.DataFrame],
) -> int:
    """Extract, transform, validate, and load a single indicator.

    ``extract`` takes the indicator code and returns whatever raw payload
    the source needs — a list of records, a values dict, a bundle of
    values plus metadata, etc. Its shape is opaque to this function.
    ``transform`` takes that payload and returns the tidy
    indicator_observations-shaped frame. Every pipeline shares this
    runner, so validation and load behavior stay identical across
    sources regardless of how each source's extraction is shaped.
    """
    logger = logging.getLogger(f"etl.pipelines.{indicator_code}")
    logger.info("Starting %s ingestion (%s)", source, indicator_code)

    engine = get_engine()
    create_tables(engine)

    raw = extract(indicator_code)
    logger.info("Extracted raw data for %s", indicator_code)

    frame = transform(raw)
    logger.info("Transformed to %s country-year rows", len(frame))

    validate_frame(frame, indicator_code)

    row_count = load_indicator(frame, engine, source=source, indicator_code=indicator_code)
    logger.info("Pipeline complete: %s rows loaded", row_count)
    return row_count


def run_world_bank_indicator(indicator_code: str) -> int:
    """Extract, transform, and load a single World Bank indicator.

    Binds World Bank's extraction and transform steps into `run_pipeline`,
    so every existing World Bank pipeline entry point keeps working
    unchanged.
    """
    return run_pipeline(
        indicator_code=indicator_code,
        source=WORLD_BANK_SOURCE,
        extract=fetch_world_bank_indicator,
        transform=lambda records: world_bank_records_to_frame(
            records, source=WORLD_BANK_SOURCE
        ),
    )
