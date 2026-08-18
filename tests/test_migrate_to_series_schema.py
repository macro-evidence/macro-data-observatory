"""Tests for the one-time backfill script (decision 0012). Real in-memory
SQLite, no live DB required -- same pattern as test_fred_load.py.
"""
from datetime import date

from sqlalchemy import create_engine, insert, select, func

from etl.db import metadata, indicator_observations, series, observations
from etl.pipelines import migrate_to_series_schema


def _seeded_engine(rows):
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(insert(indicator_observations), rows)
    return engine


def _row(**overrides):
    data = {
        "source": "world_bank", "indicator_code": "NY.GDP.MKTP.CD",
        "indicator_name": "GDP (current US$)", "country_code": "USA",
        "country_name": "United States", "year": 2023, "value": 27e12,
        "loaded_at": date.today(),
    }
    data.update(overrides)
    return data


def test_migrates_all_four_registered_indicators(monkeypatch):
    rows = [
        _row(),
        _row(indicator_code="SP.POP.TOTL", indicator_name="Population, total", value=335e6),
        _row(source="imf", indicator_code="NGDP_RPCH", indicator_name="Real GDP growth", value=2.5),
        _row(source="imf", indicator_code="PCPIPCH", indicator_name="Inflation rate", value=3.1),
    ]
    engine = _seeded_engine(rows)
    monkeypatch.setattr(migrate_to_series_schema, "get_engine", lambda: engine)

    results = migrate_to_series_schema.run()

    assert results == {
        ("world_bank", "NY.GDP.MKTP.CD"): 1,
        ("world_bank", "SP.POP.TOTL"): 1,
        ("imf", "NGDP_RPCH"): 1,
        ("imf", "PCPIPCH"): 1,
    }
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(series)).scalar() == 4
        assert conn.execute(select(func.count()).select_from(observations)).scalar() == 4


def test_indicator_observations_is_never_written_to(monkeypatch):
    """The actual invariant the backfill's 'read-only' claim depends on."""
    rows = [_row()]
    engine = _seeded_engine(rows)
    monkeypatch.setattr(migrate_to_series_schema, "get_engine", lambda: engine)

    migrate_to_series_schema.run()

    with engine.connect() as conn:
        count = conn.execute(select(func.count()).select_from(indicator_observations)).scalar()
    assert count == len(rows)


def test_missing_indicator_returns_zero_not_an_error(monkeypatch):
    """No World Bank rows at all -- registered indicators with nothing to
    migrate should be skipped cleanly, not raise."""
    rows = [_row(source="imf", indicator_code="NGDP_RPCH", indicator_name="Real GDP growth")]
    engine = _seeded_engine(rows)
    monkeypatch.setattr(migrate_to_series_schema, "get_engine", lambda: engine)

    results = migrate_to_series_schema.run()

    assert results[("world_bank", "NY.GDP.MKTP.CD")] == 0
    assert results[("imf", "NGDP_RPCH")] == 1


def test_rerun_is_idempotent(monkeypatch):
    rows = [_row()]
    engine = _seeded_engine(rows)
    monkeypatch.setattr(migrate_to_series_schema, "get_engine", lambda: engine)

    migrate_to_series_schema.run()
    migrate_to_series_schema.run()

    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(series)).scalar() == 1
        assert conn.execute(select(func.count()).select_from(observations)).scalar() == 1
