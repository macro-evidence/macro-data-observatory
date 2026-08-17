"""Shared orchestration for pipelines.

`run_pipeline` is source-agnostic: it wires extract -> transform ->
validate -> load identically for every pipeline currently using it
(World Bank and IMF). FRED does not use this runner -- see
pipelines/fred_unemployment_rate.py's own docstring for why. Each
source supplies its own `extract` (indicator_code -> raw payload) and
`transform` (raw payload -> tidy indicator_observations-shaped frame).
Load writes into series/observations, one series row per country, per
decision 0012 -- indicator_observations itself is no longer written to
by this runner as of that decision's repointing.

`run_world_bank_indicator` is a thin World-Bank-specific binding kept
for the existing World Bank pipeline entry points.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

import pandas as pd

from ..db import create_tables, get_engine
from ..load import load_indicator_observations_by_country
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
    indicator_observations-shaped frame — this shape is unchanged by
    decision 0012; only where the validated frame gets loaded changes.
    Every pipeline sharing this runner keeps identical validation
    behavior regardless of how each source's extraction is shaped.

    Loads via load_indicator_observations_by_country (decision 0012) --
    one series row per country, get-or-create plus full-refresh, not the
    old flat indicator_observations table.
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

    row_count = load_indicator_observations_by_country(
        frame, engine, source, indicator_code
    )
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
