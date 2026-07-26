"""Unit tests for data-quality validation. No network or DB required."""
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


def test_duplicate_rows_raise():
    frame = pd.concat([_base_frame(), _base_frame()], ignore_index=True)
    with pytest.raises(ValidationError):
        validate_frame(frame, "NY.GDP.MKTP.CD")


def test_high_null_rate_warns_not_raises(caplog):
    frame = _base_frame(value=[None])
    with caplog.at_level("WARNING"):
        validate_frame(frame, "NY.GDP.MKTP.CD")  # should not raise
    assert "null" in caplog.text.lower()
