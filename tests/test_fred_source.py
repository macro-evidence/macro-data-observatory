"""Unit tests for FRED source extraction. No network or DB required."""
from unittest.mock import Mock, patch

import pytest

from etl.sources import fred

SAMPLE_METADATA_RESPONSE = {
    "seriess": [
        {
            "id": "UNRATE",
            "title": "Unemployment Rate",
            "frequency": "Monthly",
            "frequency_short": "M",
            "units": "Percent",
            "units_short": "%",
            "seasonal_adjustment": "Seasonally Adjusted",
            "seasonal_adjustment_short": "SA",
            "observation_start": "1948-01-01",
            "observation_end": "2026-07-01",
        }
    ]
}

SAMPLE_OBSERVATIONS_RESPONSE = {
    "observations": [
        {"date": "1948-01-01", "value": "3.4"},
        {"date": "1948-02-01", "value": "."},
    ]
}


def test_registry_has_unemployment_rate_entry():
    spec = fred.get_series_spec("unemployment_rate")
    assert spec.series_id == "UNRATE"
    assert spec.country_code == "USA"
    assert spec.expected_frequency_short == "M"
    assert spec.expected_seasonal_adjustment_short == "SA"


def test_unregistered_concept_raises_key_error():
    with pytest.raises(KeyError, match="not in FRED_SERIES_REGISTRY"):
        fred.get_series_spec("gdp_nowhere")


def test_verify_registered_metadata_passes_on_match():
    fred.verify_registered_metadata(
        "unemployment_rate",
        {"frequency_short": "M", "seasonal_adjustment_short": "SA"},
    )  # should not raise


def test_verify_registered_metadata_raises_on_drift():
    with pytest.raises(ValueError, match="metadata drift detected"):
        fred.verify_registered_metadata(
            "unemployment_rate",
            {"frequency_short": "M", "seasonal_adjustment_short": "NSA"},
        )


@patch("etl.sources.fred.get_settings")
@patch("etl.sources.fred.requests.get")
def test_fetch_series_metadata(mock_get, mock_settings):
    mock_settings.return_value = Mock(fred_api_key="fake_key")
    response = Mock()
    response.json.return_value = SAMPLE_METADATA_RESPONSE
    mock_get.return_value = response

    metadata = fred.fetch_series_metadata("UNRATE", timeout=10)

    assert metadata == SAMPLE_METADATA_RESPONSE["seriess"][0]
    mock_get.assert_called_once_with(
        f"{fred._BASE_URL}/series",
        params={"api_key": "fake_key", "series_id": "UNRATE", "file_type": "json"},
        timeout=10,
    )
    response.raise_for_status.assert_called_once_with()


@patch("etl.sources.fred.get_settings")
def test_fetch_series_metadata_requires_api_key(mock_settings):
    mock_settings.return_value = Mock(fred_api_key=None)

    with pytest.raises(RuntimeError, match="FRED_API_KEY is not set"):
        fred.fetch_series_metadata("UNRATE")


@patch("etl.sources.fred.get_settings")
@patch("etl.sources.fred.requests.get")
def test_fetch_series_metadata_rejects_unexpected_shape(mock_get, mock_settings):
    mock_settings.return_value = Mock(fred_api_key="fake_key")
    response = Mock()
    response.json.return_value = {"seriess": []}
    mock_get.return_value = response

    with pytest.raises(ValueError, match="Unexpected FRED series response"):
        fred.fetch_series_metadata("UNRATE")


@patch("etl.sources.fred.get_settings")
@patch("etl.sources.fred.requests.get")
def test_fetch_series_observations(mock_get, mock_settings):
    mock_settings.return_value = Mock(fred_api_key="fake_key")
    response = Mock()
    response.json.return_value = SAMPLE_OBSERVATIONS_RESPONSE
    mock_get.return_value = response

    observations = fred.fetch_series_observations("UNRATE", timeout=10)

    assert observations == SAMPLE_OBSERVATIONS_RESPONSE["observations"]
    mock_get.assert_called_once_with(
        f"{fred._BASE_URL}/series/observations",
        params={"api_key": "fake_key", "series_id": "UNRATE", "file_type": "json"},
        timeout=10,
    )


@patch("etl.sources.fred.get_settings")
def test_fetch_series_observations_requires_api_key(mock_settings):
    mock_settings.return_value = Mock(fred_api_key=None)

    with pytest.raises(RuntimeError, match="FRED_API_KEY is not set"):
        fred.fetch_series_observations("UNRATE")


@patch("etl.sources.fred.get_settings")
@patch("etl.sources.fred.requests.get")
def test_fetch_series_observations_rejects_unexpected_shape(mock_get, mock_settings):
    mock_settings.return_value = Mock(fred_api_key="fake_key")
    response = Mock()
    response.json.return_value = {"observations": "not a list"}
    mock_get.return_value = response

    with pytest.raises(ValueError, match="Unexpected FRED observations response"):
        fred.fetch_series_observations("UNRATE")
