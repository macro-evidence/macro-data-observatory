"""Tests for load_fred_series_observations, using in-memory SQLite.

No live/credentialed database required — this is a self-contained,
ephemeral engine, consistent with every other test file's "no DB
required" standard, not a live-database integration test.

load.py has no other test coverage in this repo (load_indicator is only
exercised indirectly, mocked away in test_pipelines_common.py). FRED's
get-or-create-then-load flow is genuinely more complex — a real regression
test here is warranted, not just parity with existing precedent.
"""
from datetime import date

from sqlalchemy import create_engine, func, select

from etl.db import metadata, observations, series
from etl.load import load_fred_series_observations
from etl.transform import fred_observations_to_frame

LIVE_METADATA = {
    "title": "Unemployment Rate",
    "frequency": "Monthly",
    "frequency_short": "M",
    "units": "Percent",
    "units_short": "%",
    "seasonal_adjustment": "Seasonally Adjusted",
    "seasonal_adjustment_short": "SA",
}


def _fresh_engine():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


def test_first_load_creates_series_and_observations():
    engine = _fresh_engine()
    frame = fred_observations_to_frame(
        [{"date": "1948-01-01", "value": "3.4"}, {"date": "1948-02-01", "value": "."}]
    )

    row_count = load_fred_series_observations(
        frame, engine, "UNRATE", "USA", LIVE_METADATA
    )

    assert row_count == 2
    with engine.connect() as conn:
        series_rows = conn.execute(select(series)).fetchall()
        assert len(series_rows) == 1
        assert series_rows[0].source == "fred"
        assert series_rows[0].source_series_id == "UNRATE"
        assert series_rows[0].indicator_name == "Unemployment Rate"

        obs_count = conn.execute(select(func.count()).select_from(observations)).scalar()
        assert obs_count == 2


def test_rerun_reuses_series_row_not_duplicated():
    engine = _fresh_engine()
    frame = fred_observations_to_frame([{"date": "1948-01-01", "value": "3.4"}])

    load_fred_series_observations(frame, engine, "UNRATE", "USA", LIVE_METADATA)
    load_fred_series_observations(frame, engine, "UNRATE", "USA", LIVE_METADATA)

    with engine.connect() as conn:
        series_rows = conn.execute(select(series)).fetchall()
        assert len(series_rows) == 1, "series row must not be duplicated on re-run"


def test_rerun_refreshes_observations_not_duplicated():
    engine = _fresh_engine()
    frame = fred_observations_to_frame([{"date": "1948-01-01", "value": "3.4"}])

    load_fred_series_observations(frame, engine, "UNRATE", "USA", LIVE_METADATA)
    load_fred_series_observations(frame, engine, "UNRATE", "USA", LIVE_METADATA)

    with engine.connect() as conn:
        obs_count = conn.execute(select(func.count()).select_from(observations)).scalar()
        assert obs_count == 1, "observations must be full-refreshed, not duplicated"


def test_updated_values_replace_old_ones_on_rerun():
    """A revised value for the same date must replace the old one, not
    coexist with it — the actual point of full-refresh semantics."""
    engine = _fresh_engine()
    frame_v1 = fred_observations_to_frame([{"date": "1948-01-01", "value": "3.4"}])
    frame_v2 = fred_observations_to_frame([{"date": "1948-01-01", "value": "3.9"}])

    load_fred_series_observations(frame_v1, engine, "UNRATE", "USA", LIVE_METADATA)
    load_fred_series_observations(frame_v2, engine, "UNRATE", "USA", LIVE_METADATA)

    with engine.connect() as conn:
        rows = conn.execute(select(observations.c.value)).fetchall()
        assert len(rows) == 1
        assert rows[0].value == 3.9


def test_empty_frame_loads_nothing():
    engine = _fresh_engine()
    frame = fred_observations_to_frame([])

    row_count = load_fred_series_observations(frame, engine, "UNRATE", "USA", LIVE_METADATA)

    assert row_count == 0
    with engine.connect() as conn:
        series_rows = conn.execute(select(series)).fetchall()
        assert len(series_rows) == 0, "no series row should be created for an empty load"
