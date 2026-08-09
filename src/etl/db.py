"""Database engine and schema for MDO's Local ETL stage.

Deliberately a single flat table at this stage. Dimensional modeling
(separate country/indicator dimensions) is Stage 2 — Structured Data
Warehouse — per ORGANIZATION_CHARTER.md's Development Roadmap. See
decisions/0001 for the reasoning.
"""
from __future__ import annotations

from sqlalchemy import (
    Column,
    Date,
    Float,
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


def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, future=True)


def create_tables(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    metadata.create_all(engine)
