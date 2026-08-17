"""Database engine and schema for MDO's Local ETL stage.

Two schemas coexist deliberately, per decisions/0009: the original flat
`indicator_observations` table (World Bank, IMF — annual-only, no
frequency or seasonal-adjustment concept) stays exactly as it is, untouched
by this addition. `series`/`observations` is the new series-first shape,
used by FRED and any future source with real frequency/seasonal-adjustment
variation. World Bank and IMF migrate onto the new shape only later,
per 0009's explicit sequencing — not part of this change.
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.engine import Engine

from .config import get_settings

metadata = MetaData()

indicator_observations = Table(
    "indicator_observations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String(32), nullable=False),
    Column("indicator_code", String(64), nullable=False),
    Column("indicator_name", String(256), nullable=False),
    Column("country_code", String(8), nullable=False),
    Column("country_name", String(128), nullable=False),
    Column("year", Integer, nullable=False),
    Column("value", Float, nullable=True),
    Column("loaded_at", Date, nullable=False),
    UniqueConstraint(
        "source", "indicator_code", "country_code", "year",
        name="uq_indicator_observation",
    ),
)

series = Table(
    "series",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String(32), nullable=False),
    Column("source_series_id", String(64), nullable=False),
    Column("indicator_name", String(256), nullable=False),
    Column("country_code", String(8), nullable=False),
    Column("frequency", String(32), nullable=False),
    Column("frequency_short", String(8), nullable=False),
    Column("units", String(128), nullable=False),
    Column("units_short", String(32), nullable=False),
    Column("seasonal_adjustment", String(64), nullable=False),
    Column("seasonal_adjustment_short", String(8), nullable=False),
    Column("created_at", Date, nullable=False),
    UniqueConstraint(
        "source", "source_series_id", "country_code",
        name="uq_series_source_id_country",
    ),
)

observations = Table(
    "observations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("series_id", Integer, ForeignKey("series.id"), nullable=False),
    Column("date", Date, nullable=False),
    Column("value", Float, nullable=True),
    Column("loaded_at", Date, nullable=False),
    UniqueConstraint(
        "series_id", "date",
        name="uq_observation_series_date",
    ),
)


def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, future=True)


def create_tables(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    metadata.create_all(engine)
