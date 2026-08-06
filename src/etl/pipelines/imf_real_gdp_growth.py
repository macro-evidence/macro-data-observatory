"""Entry point: IMF real GDP growth ingestion.

Run directly:
    python -m etl.pipelines.imf_real_gdp_growth
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from ..sources.imf import fetch_country_names, fetch_indicator, fetch_indicator_name
from ..transform import imf_indicator_values_to_frame
from .common import run_pipeline

SOURCE = "imf"
INDICATOR_CODE = "NGDP_RPCH"


def _extract(indicator_code: str) -> dict[str, Any]:
    """Fetch IMF values plus the indicator/country metadata needed to
    label them. Three calls bundled into one payload for `_transform`.
    """
    return {
        "values": fetch_indicator(indicator_code),
        "indicator_name": fetch_indicator_name(indicator_code),
        "country_names": fetch_country_names(),
    }


def _transform(raw: dict[str, Any]) -> pd.DataFrame:
    return imf_indicator_values_to_frame(
        raw["values"],
        indicator_code=INDICATOR_CODE,
        indicator_name=raw["indicator_name"],
        country_names=raw["country_names"],
        source=SOURCE,
    )


def run() -> int:
    return run_pipeline(
        indicator_code=INDICATOR_CODE,
        source=SOURCE,
        extract=_extract,
        transform=_transform,
    )


if __name__ == "__main__":
    run()
