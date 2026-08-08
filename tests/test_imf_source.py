"""Unit tests for IMF source extraction. No network or DB required."""
from unittest.mock import Mock, patch

import pytest

from etl.sources import imf

SAMPLE_RESPONSE = {
    "values": {
        "NGDP_RPCH": {
            "USA": {"2022": 1.9, "2023": 2.9, "2024": 2.8},
            "IND": {"2022": 7.6, "2023": 9.2, "2024": 6.5},
        }
    }
}

SAMPLE_INDICATORS_RESPONSE = {
    "indicators": {
        "NGDP_RPCH": {
            "label": "Real GDP growth",
            "unit": "Annual percent change",
        }
    }
}

SAMPLE_COUNTRIES_RESPONSE = {
    "countries": {
        "USA": {"label": "United States"},
        "IND": {"label": "India"},
    }
}


@patch("etl.sources.imf.requests.get")
def test_fetches_all_country_series(mock_get):
    response = Mock()
    response.json.return_value = SAMPLE_RESPONSE
    mock_get.return_value = response

    values = imf.fetch_indicator("NGDP_RPCH")

    assert values == SAMPLE_RESPONSE["values"]["NGDP_RPCH"]
    mock_get.assert_called_once_with(
        f"{imf._BASE_URL}/NGDP_RPCH", timeout=30
    )
    response.raise_for_status.assert_called_once_with()


@patch("etl.sources.imf.requests.get")
def test_fetches_single_country_series(mock_get):
    response = Mock()
    response.json.return_value = SAMPLE_RESPONSE
    mock_get.return_value = response

    values = imf.fetch_indicator("NGDP_RPCH", country="USA", timeout=10)

    assert values == {"USA": {"2022": 1.9, "2023": 2.9, "2024": 2.8}}
    mock_get.assert_called_once_with(
        f"{imf._BASE_URL}/NGDP_RPCH/USA", timeout=10
    )


@patch("etl.sources.imf.requests.get")
def test_rejects_unexpected_response_shape(mock_get):
    response = Mock()
    response.json.return_value = {"values": {}}
    mock_get.return_value = response

    with pytest.raises(ValueError, match="Unexpected IMF response shape"):
        imf.fetch_indicator("NGDP_RPCH")


@patch("etl.sources.imf.requests.get")
def test_fetches_indicator_name(mock_get):
    response = Mock()
    response.json.return_value = SAMPLE_INDICATORS_RESPONSE
    mock_get.return_value = response

    name = imf.fetch_indicator_name("NGDP_RPCH", timeout=10)

    assert name == "Real GDP growth"
    mock_get.assert_called_once_with(f"{imf._BASE_URL}/indicators", timeout=10)
    response.raise_for_status.assert_called_once_with()


@patch("etl.sources.imf.requests.get")
def test_rejects_unknown_indicator_metadata(mock_get):
    response = Mock()
    response.json.return_value = {"indicators": {}}
    mock_get.return_value = response

    with pytest.raises(ValueError, match="Unexpected IMF indicator metadata"):
        imf.fetch_indicator_name("NGDP_RPCH")


@patch("etl.sources.imf.requests.get")
def test_lists_all_indicators(mock_get):
    response = Mock()
    response.json.return_value = {
        "indicators": {
            "NGDP_RPCH": {"label": "Real GDP growth", "unit": "Annual percent change"},
            "PCPIPCH": {"label": "Inflation rate, average consumer prices", "unit": "Annual percent change"},
        }
    }
    mock_get.return_value = response

    indicators = imf.list_indicators(timeout=10)

    assert indicators == {
        "NGDP_RPCH": "Real GDP growth",
        "PCPIPCH": "Inflation rate, average consumer prices",
    }
    mock_get.assert_called_once_with(f"{imf._BASE_URL}/indicators", timeout=10)
    response.raise_for_status.assert_called_once_with()


@patch("etl.sources.imf.requests.get")
def test_list_indicators_skips_malformed_entries(mock_get):
    """A malformed entry (missing/non-string label) is dropped rather than
    crashing the whole listing — useful for a discovery-time function
    where the goal is a usable overview, not strict validation."""
    response = Mock()
    response.json.return_value = {
        "indicators": {
            "NGDP_RPCH": {"label": "Real GDP growth"},
            "BROKEN": {"unit": "no label here"},
            "ALSO_BROKEN": "not even a dict",
        }
    }
    mock_get.return_value = response

    indicators = imf.list_indicators()

    assert indicators == {"NGDP_RPCH": "Real GDP growth"}


@patch("etl.sources.imf.requests.get")
def test_list_indicators_rejects_unexpected_response_shape(mock_get):
    response = Mock()
    response.json.return_value = {"indicators": []}
    mock_get.return_value = response

    with pytest.raises(ValueError, match="Unexpected IMF indicator metadata"):
        imf.list_indicators()


@patch("etl.sources.imf.requests.get")
def test_fetches_country_names(mock_get):
    response = Mock()
    response.json.return_value = SAMPLE_COUNTRIES_RESPONSE
    mock_get.return_value = response

    country_names = imf.fetch_country_names(timeout=10)

    assert country_names == {"USA": "United States", "IND": "India"}
    mock_get.assert_called_once_with(f"{imf._BASE_URL}/countries", timeout=10)
    response.raise_for_status.assert_called_once_with()


@patch("etl.sources.imf.requests.get")
def test_rejects_unexpected_country_metadata(mock_get):
    response = Mock()
    response.json.return_value = {"countries": []}
    mock_get.return_value = response

    with pytest.raises(ValueError, match="Unexpected IMF country metadata"):
        imf.fetch_country_names()
