"""Unit tests for the IMF real GDP growth pipeline. No network or DB required."""
from unittest.mock import patch

import pandas as pd

from etl.pipelines import imf_real_gdp_growth

SAMPLE_VALUES = {"USA": {"2023": 2.9}}
COUNTRY_NAMES = {"USA": "United States"}


@patch("etl.pipelines.imf_real_gdp_growth.fetch_country_names")
@patch("etl.pipelines.imf_real_gdp_growth.fetch_indicator_name")
@patch("etl.pipelines.imf_real_gdp_growth.fetch_indicator")
def test_extract_bundles_values_and_metadata(
    mock_fetch_indicator, mock_fetch_indicator_name, mock_fetch_country_names
):
    mock_fetch_indicator.return_value = SAMPLE_VALUES
    mock_fetch_indicator_name.return_value = "Real GDP growth"
    mock_fetch_country_names.return_value = COUNTRY_NAMES

    raw = imf_real_gdp_growth._extract("NGDP_RPCH")

    assert raw == {
        "values": SAMPLE_VALUES,
        "indicator_name": "Real GDP growth",
        "country_names": COUNTRY_NAMES,
    }
    mock_fetch_indicator.assert_called_once_with("NGDP_RPCH")
    mock_fetch_indicator_name.assert_called_once_with("NGDP_RPCH")
    mock_fetch_country_names.assert_called_once_with()


@patch("etl.pipelines.imf_real_gdp_growth.imf_indicator_values_to_frame")
def test_transform_delegates_to_imf_transform(mock_transform):
    frame = pd.DataFrame({"country_code": ["USA"]})
    mock_transform.return_value = frame
    raw = {
        "values": SAMPLE_VALUES,
        "indicator_name": "Real GDP growth",
        "country_names": COUNTRY_NAMES,
    }

    result = imf_real_gdp_growth._transform(raw)

    assert result is frame
    mock_transform.assert_called_once_with(
        SAMPLE_VALUES,
        indicator_code="NGDP_RPCH",
        indicator_name="Real GDP growth",
        country_names=COUNTRY_NAMES,
        source="imf",
    )


@patch("etl.pipelines.imf_real_gdp_growth.run_pipeline")
def test_run_delegates_to_shared_runner(mock_run_pipeline):
    mock_run_pipeline.return_value = 1

    row_count = imf_real_gdp_growth.run()

    assert row_count == 1
    mock_run_pipeline.assert_called_once_with(
        indicator_code="NGDP_RPCH",
        source="imf",
        extract=imf_real_gdp_growth._extract,
        transform=imf_real_gdp_growth._transform,
    )
