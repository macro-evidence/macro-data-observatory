"""Unit tests for FRED observation transformation. No network or DB required."""
from datetime import date

from etl.transform import fred_observations_to_frame


def test_converts_dot_to_null():
    raw = [
        {"date": "1948-01-01", "value": "3.4"},
        {"date": "1948-02-01", "value": "."},
    ]
    frame = fred_observations_to_frame(raw)

    assert len(frame) == 2
    assert frame.loc[0, "value"] == 3.4
    assert frame.loc[1, "value"] is None or frame.loc[1, "value"] != frame.loc[1, "value"]  # NaN


def test_parses_real_dates():
    raw = [{"date": "1948-01-01", "value": "3.4"}]
    frame = fred_observations_to_frame(raw)

    assert frame.loc[0, "date"] == date(1948, 1, 1)


def test_sets_loaded_at():
    raw = [{"date": "1948-01-01", "value": "3.4"}]
    frame = fred_observations_to_frame(raw)

    assert frame.loc[0, "loaded_at"] == date.today()


def test_drops_duplicate_dates():
    raw = [
        {"date": "1948-01-01", "value": "3.4"},
        {"date": "1948-01-01", "value": "3.5"},
    ]
    frame = fred_observations_to_frame(raw)

    assert len(frame) == 1


def test_sorts_by_date():
    raw = [
        {"date": "1948-03-01", "value": "4.0"},
        {"date": "1948-01-01", "value": "3.4"},
        {"date": "1948-02-01", "value": "3.8"},
    ]
    frame = fred_observations_to_frame(raw)

    assert list(frame["date"]) == [date(1948, 1, 1), date(1948, 2, 1), date(1948, 3, 1)]


def test_skips_malformed_records():
    raw = [
        {"date": "1948-01-01", "value": "3.4"},
        {"value": "no date here"},
        {"date": "not-a-date", "value": "1.0"},
    ]
    frame = fred_observations_to_frame(raw)

    assert len(frame) == 1


def test_empty_input_returns_empty_frame():
    frame = fred_observations_to_frame([])
    assert frame.empty
