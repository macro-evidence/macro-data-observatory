"""Unit tests for the FRED unemployment rate pipeline. No network or DB
required — get_engine and create_tables are mocked, unlike test_fred_load.py
which deliberately does use a real (in-memory) engine for the load layer
itself. This file tests orchestration/wiring; test_fred_load.py tests the
actual database behavior.
"""
from unittest.mock import patch

import pandas as pd

from etl.pipelines import fred_unemployment_rate

LIVE_METADATA = {
    "title": "Unemployment Rate",
    "frequency": "Monthly",
    "frequency_short": "M",
    "units": "Percent",
    "units_short": "%",
    "seasonal_adjustment": "Seasonally Adjusted",
    "seasonal_adjustment_short": "SA",
}
RAW_OBSERVATIONS = [{"date": "1948-01-01", "value": "3.4"}]


@patch("etl.pipelines.fred_unemployment_rate.load_fred_series_observations")
@patch("etl.pipelines.fred_unemployment_rate.validate_observations_frame")
@patch("etl.pipelines.fred_unemployment_rate.fetch_series_observations")
@patch("etl.pipelines.fred_unemployment_rate.verify_registered_metadata")
@patch("etl.pipelines.fred_unemployment_rate.fetch_series_metadata")
@patch("etl.pipelines.fred_unemployment_rate.create_tables")
@patch("etl.pipelines.fred_unemployment_rate.get_engine")
def test_run_wires_verify_extract_transform_validate_load(
    mock_get_engine,
    mock_create_tables,
    mock_fetch_metadata,
    mock_verify,
    mock_fetch_observations,
    mock_validate,
    mock_load,
):
    mock_fetch_metadata.return_value = LIVE_METADATA
    mock_fetch_observations.return_value = RAW_OBSERVATIONS
    mock_load.return_value = 1

    row_count = fred_unemployment_rate.run()

    assert row_count == 1
    mock_fetch_metadata.assert_called_once_with("UNRATE")
    mock_verify.assert_called_once_with("unemployment_rate", LIVE_METADATA)
    mock_fetch_observations.assert_called_once_with("UNRATE")
    mock_validate.assert_called_once()
    mock_load.assert_called_once()
    load_args = mock_load.call_args.args
    assert load_args[2] == "UNRATE"
    assert load_args[3] == "USA"
    assert load_args[4] == LIVE_METADATA


@patch("etl.pipelines.fred_unemployment_rate.load_fred_series_observations")
@patch("etl.pipelines.fred_unemployment_rate.validate_observations_frame")
@patch("etl.pipelines.fred_unemployment_rate.fetch_series_observations")
@patch("etl.pipelines.fred_unemployment_rate.verify_registered_metadata")
@patch("etl.pipelines.fred_unemployment_rate.fetch_series_metadata")
@patch("etl.pipelines.fred_unemployment_rate.create_tables")
@patch("etl.pipelines.fred_unemployment_rate.get_engine")
def test_run_verifies_before_extracting_observations(
    mock_get_engine,
    mock_create_tables,
    mock_fetch_metadata,
    mock_verify,
    mock_fetch_observations,
    mock_validate,
    mock_load,
):
    """Metadata drift should be caught before spending a second API call
    pulling the full observation history."""
    mock_fetch_metadata.return_value = LIVE_METADATA
    mock_verify.side_effect = ValueError("drift detected")

    try:
        fred_unemployment_rate.run()
        assert False, "should have raised"
    except ValueError:
        pass

    mock_fetch_observations.assert_not_called()
    mock_load.assert_not_called()
