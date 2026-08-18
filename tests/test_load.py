"""Tests for the World Bank/IMF migration path in load.py (decision 0012).
Real in-memory SQLite, no live DB required -- same pattern as test_fred_load.py.
"""
from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine, select, func

from etl.db import metadata, series, observations
from etl.load import (
    SERIES_MIGRATION_REGISTRY,
    get_migration_spec,
    load_indicator_observations_by_country,
    _year_to_date,
)


def _fresh_engine():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


# --- registry and lookup ---

def test_registry_covers_all_four_decision_0012_indicators():
    assert set(SERIES_MIGRATION_REGISTRY) == {
        ("world_bank", "NY.GDP.MKTP.CD"),
        ("world_bank", "SP.POP.TOTL"),
        ("imf", "NGDP_RPCH"),
        ("imf", "PCPIPCH"),
    }


def test_gdp_and_inflation_use_flow_convention():
    assert get_migration_spec("world_bank", "NY.GDP.MKTP.CD").date_convention == "flow"
    assert get_migration_spec("imf", "NGDP_RPCH").date_convention == "flow"
    assert get_migration_spec("imf", "PCPIPCH").date_convention == "flow"


def test_population_uses_stock_convention():
    assert get_migration_spec("world_bank", "SP.POP.TOTL").date_convention == "stock"


def test_unregistered_pair_raises_key_error():
    with pytest.raises(KeyError, match="not in SERIES_MIGRATION_REGISTRY"):
        get_migration_spec("world_bank", "NOT.REGISTERED")


# --- _year_to_date ---

def test_year_to_date_flow_uses_january_first():
    assert _year_to_date(2023, "flow") == date(2023, 1, 1)


def test_year_to_date_stock_uses_july_first():
    assert _year_to_date(2023, "stock") == date(2023, 7, 1)


def test_year_to_date_unknown_convention_raises():
    with pytest.raises(ValueError, match="Unknown date_convention"):
        _year_to_date(2023, "quarterly")


# --- load_indicator_observations_by_country ---

def _frame(**overrides):
    data = {
        "source": ["world_bank"], "indicator_code": ["NY.GDP.MKTP.CD"],
        "indicator_name": ["GDP (current US$)"], "country_code": ["USA"],
        "country_name": ["United States"], "year": [2023], "value": [27000000000000.0],
        "loaded_at": [date.today()],
    }
    data.update(overrides)
    return pd.DataFrame(data)


def test_creates_one_series_row_per_country():
    engine = _fresh_engine()
    frame = pd.concat([
        _frame(country_code=["USA"], country_name=["United States"], value=[27e12]),
        _frame(country_code=["IND"], country_name=["India"], value=[3.7e12]),
    ], ignore_index=True)

    n = load_indicator_observations_by_country(frame, engine, "world_bank", "NY.GDP.MKTP.CD")

    assert n == 2
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(series)).scalar() == 2


def test_missing_value_stored_as_null():
    engine = _fresh_engine()
    frame = _frame(value=[None])

    load_indicator_observations_by_country(frame, engine, "world_bank", "NY.GDP.MKTP.CD")

    with engine.connect() as conn:
        value = conn.execute(select(observations.c.value)).scalar()
    assert value is None


def test_flow_indicator_date_is_january_first():
    engine = _fresh_engine()
    load_indicator_observations_by_country(_frame(year=[2023]), engine, "world_bank", "NY.GDP.MKTP.CD")

    with engine.connect() as conn:
        obs_date = conn.execute(select(observations.c.date)).scalar()
    assert obs_date == date(2023, 1, 1)


def test_stock_indicator_date_is_july_first():
    engine = _fresh_engine()
    frame = _frame(
        indicator_code=["SP.POP.TOTL"], indicator_name=["Population, total"],
        year=[2023], value=[335000000.0],
    )
    load_indicator_observations_by_country(frame, engine, "world_bank", "SP.POP.TOTL")

    with engine.connect() as conn:
        obs_date = conn.execute(select(observations.c.date)).scalar()
    assert obs_date == date(2023, 7, 1)


def test_rerun_reuses_series_rows_not_duplicated():
    engine = _fresh_engine()
    frame = _frame()

    load_indicator_observations_by_country(frame, engine, "world_bank", "NY.GDP.MKTP.CD")
    load_indicator_observations_by_country(frame, engine, "world_bank", "NY.GDP.MKTP.CD")

    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(series)).scalar() == 1


def test_rerun_refreshes_observations_not_duplicated():
    engine = _fresh_engine()
    frame = _frame()

    load_indicator_observations_by_country(frame, engine, "world_bank", "NY.GDP.MKTP.CD")
    load_indicator_observations_by_country(frame, engine, "world_bank", "NY.GDP.MKTP.CD")

    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(observations)).scalar() == 1


def test_updated_value_replaces_old_one_on_rerun():
    engine = _fresh_engine()
    load_indicator_observations_by_country(_frame(value=[27e12]), engine, "world_bank", "NY.GDP.MKTP.CD")
    load_indicator_observations_by_country(_frame(value=[28e12]), engine, "world_bank", "NY.GDP.MKTP.CD")

    with engine.connect() as conn:
        value = conn.execute(select(observations.c.value)).scalar()
    assert value == 28e12


def test_empty_frame_loads_nothing():
    engine = _fresh_engine()
    n = load_indicator_observations_by_country(pd.DataFrame(), engine, "world_bank", "NY.GDP.MKTP.CD")

    assert n == 0
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(series)).scalar() == 0
