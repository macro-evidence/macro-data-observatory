"""Database engine and canonical series-first schema for MDO.

All active sources persist through ``series`` and ``observations``. The legacy
``indicator_observations`` table was retired under decisions 0012 and 0013
after the bounded production proving period completed.
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
