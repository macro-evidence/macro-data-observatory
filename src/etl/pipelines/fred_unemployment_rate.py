"""Entry point: FRED unemployment rate ingestion.

Run directly:
    python -m etl.pipelines.fred_unemployment_rate

Does not use common.run_pipeline. That runner is bound to the flat
indicator_observations table and load_indicator (decision 0009's
Consequences flagged this explicitly). FRED writes to series/observations
instead, which needs a database-assigned series_id resolved before
observations can be loaded — see load.load_fred_series_observations'
docstring. A genuinely different shape, not an oversight or duplication
of common.py by mistake.
"""
from __future__ import annotations

import logging

from ..db import create_tables, get_engine
from ..load import load_fred_series_observations
from ..sources.fred import (
    fetch_series_metadata,
    fetch_series_observations,
    get_series_spec,
    verify_registered_metadata,
)
from ..transform import fred_observations_to_frame
from ..validate import validate_observations_frame

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)

CONCEPT = "unemployment_rate"


def run() -> int:
    logger = logging.getLogger(f"etl.pipelines.{CONCEPT}")
    logger.info("Starting FRED ingestion (%s)", CONCEPT)

    spec = get_series_spec(CONCEPT)

    engine = get_engine()
    create_tables(engine)

    live_metadata = fetch_series_metadata(spec.series_id)
    verify_registered_metadata(CONCEPT, live_metadata)
    logger.info(
        "Registry metadata verified against live FRED data for %s", spec.series_id
    )

    raw_observations = fetch_series_observations(spec.series_id)
    logger.info(
        "Extracted %s raw observations for %s", len(raw_observations), spec.series_id
    )

    frame = fred_observations_to_frame(raw_observations)
    logger.info("Transformed to %s observation rows", len(frame))

    validate_observations_frame(frame, CONCEPT)

    row_count = load_fred_series_observations(
        frame, engine, spec.series_id, spec.country_code, live_metadata
    )
    logger.info("Pipeline complete: %s rows loaded", row_count)
    return row_count


if __name__ == "__main__":
    run()
