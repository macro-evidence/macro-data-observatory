"""Unit tests for the IMF inflation pipeline. No network or DB required."""
from unittest.mock import patch

import pandas as pd

from etl.pipelines import imf_inflation

SAMPLE_VALUES = {"USA": {"2023": -1.2}}
COUNTRY_NAMES = {"USA": "United States"}


@patch("etl.pipelines.imf_inflation.fetch_country_names")
@patch("etl.pipelines.imf_inflation.fetch_indicator_name")
@patch("etl.pipelines.imf_inflation.fetch_indicator")
def test_extract_bundles_values_and_metadata(
    mock_fetch_indicator, mock_fetch_indicator_name, mock_fetch_country_names
):
    mock_fetch_indicator.return_value = SAMPLE_VALUES
    mock_fetch_indicator_name.return_value = "Inflation rate, average consumer prices"
    mock_fetch_country_names.return_value = COUNTRY_NAMES

    raw = imf_inflation._extract("PCPIPCH")

    assert raw == {
        "values": SAMPLE_VALUES,
        "indicator_name": "Inflation rate, average consumer prices",
        "country_names": COUNTRY_NAMES,
    }
    mock_fetch_indicator.assert_called_once_with("PCPIPCH")
    mock_fetch_indicator_name.assert_called_once_with("PCPIPCH")
    mock_fetch_country_names.assert_called_once_with()


@patch("etl.pipelines.imf_inflation.imf_indicator_values_to_frame")
def test_transform_delegates_to_imf_transform(mock_transform):
    frame = pd.DataFrame({"country_code": ["USA"]})
    mock_transform.return_value = frame
    raw = {
        "values": SAMPLE_VALUES,
        "indicator_name": "Inflation rate, average consumer prices",
        "country_names": COUNTRY_NAMES,
    }

    result = imf_inflation._transform(raw)

    assert result is frame
    mock_transform.assert_called_once_with(
        SAMPLE_VALUES,
        indicator_code="PCPIPCH",
        indicator_name="Inflation rate, average consumer prices",
        country_names=COUNTRY_NAMES,
        source="imf",
    )


@patch("etl.pipelines.imf_inflation.run_pipeline")
def test_run_delegates_to_shared_runner(mock_run_pipeline):
    mock_run_pipeline.return_value = 1

    row_count = imf_inflation.run()

    assert row_count == 1
    mock_run_pipeline.assert_called_once_with(
        indicator_code="PCPIPCH",
        source="imf",
        extract=imf_inflation._extract,
        transform=imf_inflation._transform,
    )
