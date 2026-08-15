"""Unit tests for data-quality validation. No network or DB required."""
from datetime import date

import pandas as pd
import pytest

from etl.validate import ValidationError, validate_frame


def _base_frame(**overrides):
    data = {
        "source": ["world_bank"],
        "indicator_code": ["NY.GDP.MKTP.CD"],
        "indicator_name": ["GDP (current US$)"],
        "country_code": ["USA"],
        "country_name": ["United States"],
        "year": [2023],
        "value": [27360935000000.0],
        "loaded_at": [pd.Timestamp.today().date()],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_valid_frame_passes():
    validate_frame(_base_frame(), "NY.GDP.MKTP.CD")  # should not raise


def test_empty_frame_raises():
    with pytest.raises(ValidationError):
        validate_frame(pd.DataFrame(), "NY.GDP.MKTP.CD")


def test_missing_column_raises():
    frame = _base_frame().drop(columns=["country_name"])
    with pytest.raises(ValidationError):
        validate_frame(frame, "NY.GDP.MKTP.CD")


def test_bad_country_code_raises():
    frame = _base_frame(country_code=["US"])  # 2 chars, not ISO3
    with pytest.raises(ValidationError):
        validate_frame(frame, "NY.GDP.MKTP.CD")


def test_year_out_of_range_raises():
    frame = _base_frame(year=[1900])
    with pytest.raises(ValidationError):
        validate_frame(frame, "NY.GDP.MKTP.CD")


def test_near_future_forecast_year_passes():
    """IMF's WEO-based indicators carry forecasts several years out —
    those years must not be rejected as structurally invalid."""
    forecast_year = date.today().year + 5
    frame = _base_frame(source=["imf"], indicator_code=["NGDP_RPCH"], year=[forecast_year])
    validate_frame(frame, "NGDP_RPCH")  # should not raise


def test_far_future_year_raises():
    """Years further out than any known forecast horizon should still
    be treated as structurally suspicious."""
    frame = _base_frame(year=[date.today().year + 20])
    with pytest.raises(ValidationError):
        validate_frame(frame, "NY.GDP.MKTP.CD")


def test_duplicate_rows_raise():
    frame = pd.concat([_base_frame(), _base_frame()], ignore_index=True)
    with pytest.raises(ValidationError):
        validate_frame(frame, "NY.GDP.MKTP.CD")


def test_high_null_rate_warns_not_raises(caplog):
    frame = _base_frame(value=[None])
    with caplog.at_level("WARNING"):
        validate_frame(frame, "NY.GDP.MKTP.CD")  # should not raise
    assert "null" in caplog.text.lower()


# --- validate_observations_frame: series-first, date-keyed sources (decision 0010) ---

from etl.validate import validate_observations_frame  # noqa: E402


def _obs_frame(**overrides):
    data = {
        "date": [date(2023, 1, 1)],
        "value": [4.1],
        "loaded_at": [date.today()],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_observations_valid_frame_passes():
    validate_observations_frame(_obs_frame(), "unemployment_rate")  # should not raise


def test_observations_empty_frame_raises():
    with pytest.raises(ValidationError):
        validate_observations_frame(pd.DataFrame(), "unemployment_rate")


def test_observations_missing_column_raises():
    frame = _obs_frame().drop(columns=["loaded_at"])
    with pytest.raises(ValidationError):
        validate_observations_frame(frame, "unemployment_rate")


def test_observations_pre_1960_date_is_accepted():
    """The exact regression this function exists to prevent (decision 0011):
    UNRATE starts 1948-01-01, which the old year-based MIN_YEAR=1960 would
    have wrongly rejected."""
    frame = _obs_frame(date=[date(1948, 1, 1)])
    validate_observations_frame(frame, "unemployment_rate")  # should not raise


def test_observations_implausible_early_date_raises():
    frame = _obs_frame(date=[date(1850, 1, 1)])
    with pytest.raises(ValidationError):
        validate_observations_frame(frame, "unemployment_rate")


def test_observations_far_future_date_raises():
    frame = _obs_frame(date=[date(date.today().year + 20, 1, 1)])
    with pytest.raises(ValidationError):
        validate_observations_frame(frame, "unemployment_rate")


def test_observations_duplicate_dates_raise():
    frame = pd.concat([_obs_frame(), _obs_frame()], ignore_index=True)
    with pytest.raises(ValidationError):
        validate_observations_frame(frame, "unemployment_rate")


def test_observations_high_null_rate_warns_not_raises(caplog):
    frame = _obs_frame(value=[None])
    with caplog.at_level("WARNING"):
        validate_observations_frame(frame, "unemployment_rate")  # should not raise
    assert "null" in caplog.text.lower()
