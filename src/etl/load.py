"""Load transformed data into Postgres.

Full-refresh per (source, indicator_code): delete existing rows for that
pair, then bulk-insert the fresh frame, in a single transaction. Simple
and correct at this data volume — see decisions/0001.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from .db import indicator_observations, observations, series

logger = logging.getLogger(__name__)


def load_indicator(
    frame: pd.DataFrame, engine: Engine, source: str, indicator_code: str
) -> int:
    """Replace all rows for (source, indicator_code) with the given frame.

    Delete + insert happen in one transaction: a failed insert rolls the
    delete back too, so a failed run never leaves the table half-empty.

    FROZEN as of decision 0012 -- no longer called by any pipeline
    (common.run_pipeline was repointed to load_indicator_observations_by_country;
    verified via a real, non-mocked test that indicator_observations
    receives zero new rows). Kept only because indicator_observations
    itself is frozen, not dropped -- decision 0012 left the table's exact
    removal timeline undecided. Do not wire this into a new pipeline;
    use load_indicator_observations_by_country instead.
    """
    if frame.empty:
        logger.warning(
            "Nothing to load for %s / %s — empty frame", source, indicator_code
        )
        return 0

    with engine.begin() as conn:
        conn.execute(
            delete(indicator_observations).where(
                indicator_observations.c.source == source,
                indicator_observations.c.indicator_code == indicator_code,
            )
        )
        frame.to_sql(
            indicator_observations.name,
            con=conn,
            if_exists="append",
            index=False,
        )

    logger.info("Loaded %s rows for %s / %s", len(frame), source, indicator_code)
    return len(frame)


def load_fred_series_observations(
    frame: pd.DataFrame,
    engine: Engine,
    source_series_id: str,
    country_code: str,
    live_metadata: dict[str, Any],
) -> int:
    """Get-or-create the series row, then full-refresh its observations.

    Two-step write the flat indicator_observations table never needed
    (decision 0009): the series row must exist, and its database-assigned
    id resolved, before observations can reference it via foreign key.
    Both steps happen in one transaction — a failed observations insert
    rolls back a just-created series row too, so a failed run never leaves
    an orphaned series with no data.

    ``live_metadata`` is FRED's own fred/series response for this series
    (title, frequency, units, seasonal_adjustment, and their _short forms)
    — expected already verified against the registry via
    ``sources.fred.verify_registered_metadata`` before this is called;
    this function writes what it's given, it doesn't re-check drift.
    """
    if frame.empty:
        logger.warning("Nothing to load for FRED series %s — empty frame", source_series_id)
        return 0

    with engine.begin() as conn:
        existing = conn.execute(
            select(series.c.id).where(
                series.c.source == "fred",
                series.c.source_series_id == source_series_id,
            )
        ).first()

        if existing is not None:
            series_pk = existing.id
        else:
            result = conn.execute(
                insert(series).values(
                    source="fred",
                    source_series_id=source_series_id,
                    indicator_name=live_metadata["title"],
                    country_code=country_code,
                    frequency=live_metadata["frequency"],
                    frequency_short=live_metadata["frequency_short"],
                    units=live_metadata["units"],
                    units_short=live_metadata["units_short"],
                    seasonal_adjustment=live_metadata["seasonal_adjustment"],
                    seasonal_adjustment_short=live_metadata["seasonal_adjustment_short"],
                    created_at=date.today(),
                )
            )
            series_pk = result.inserted_primary_key[0]

        conn.execute(delete(observations).where(observations.c.series_id == series_pk))

        frame = frame.copy()
        frame["series_id"] = series_pk
        frame.to_sql(observations.name, con=conn, if_exists="append", index=False)

    logger.info(
        "Loaded %s observations for FRED series %s (series_id=%s)",
        len(frame), source_series_id, series_pk,
    )
    return len(frame)


@dataclass(frozen=True)
class SeriesMigrationSpec:
    """Migration metadata for one (source, indicator_code) pair, per
    decision 0012 -- frequency, seasonal adjustment, and units for World
    Bank/IMF's annual indicators, plus which year-to-date convention
    applies (stock: July 1, matching World Bank's own stated midyear
    estimates; flow: January 1, a labeled convention choice, no source
    states a specific within-year timing for GDP or inflation).
    """

    frequency: str
    frequency_short: str
    seasonal_adjustment: str
    seasonal_adjustment_short: str
    units: str
    units_short: str
    date_convention: str  # "stock" or "flow"


SERIES_MIGRATION_REGISTRY: dict[tuple[str, str], SeriesMigrationSpec] = {
    ("world_bank", "NY.GDP.MKTP.CD"): SeriesMigrationSpec(
        frequency="Annual", frequency_short="A",
        seasonal_adjustment="Not Seasonally Adjusted", seasonal_adjustment_short="NSA",
        units="Current US$", units_short="USD",
        date_convention="flow",
    ),
    ("world_bank", "SP.POP.TOTL"): SeriesMigrationSpec(
        frequency="Annual", frequency_short="A",
        seasonal_adjustment="Not Seasonally Adjusted", seasonal_adjustment_short="NSA",
        units="Persons", units_short="Count",
        date_convention="stock",
    ),
    ("imf", "NGDP_RPCH"): SeriesMigrationSpec(
        frequency="Annual", frequency_short="A",
        seasonal_adjustment="Not Seasonally Adjusted", seasonal_adjustment_short="NSA",
        units="Annual percent change", units_short="%",
        date_convention="flow",
    ),
    ("imf", "PCPIPCH"): SeriesMigrationSpec(
        frequency="Annual", frequency_short="A",
        seasonal_adjustment="Not Seasonally Adjusted", seasonal_adjustment_short="NSA",
        units="Annual percent change", units_short="%",
        date_convention="flow",
    ),
}


def get_migration_spec(source: str, indicator_code: str) -> SeriesMigrationSpec:
    """Look up migration metadata for a (source, indicator_code) pair.

    Raises KeyError if not registered -- curated per decision 0012, same
    reasoning as FRED's registry: an unregistered indicator means adding
    an entry, not guessing values at migration time.
    """
    try:
        return SERIES_MIGRATION_REGISTRY[(source, indicator_code)]
    except KeyError as exc:
        raise KeyError(
            f"({source!r}, {indicator_code!r}) is not in "
            "SERIES_MIGRATION_REGISTRY. Add an entry with its frequency, "
            "seasonal adjustment, units, and date convention (decision "
            "0012) before migrating this indicator."
        ) from exc


def _year_to_date(year: int, date_convention: str) -> date:
    if date_convention == "stock":
        return date(year, 7, 1)
    if date_convention == "flow":
        return date(year, 1, 1)
    raise ValueError(f"Unknown date_convention: {date_convention!r}")


def load_indicator_observations_by_country(
    frame: pd.DataFrame, engine: Engine, source: str, indicator_code: str
) -> int:
    """Migrate a multi-country indicator_observations-shaped frame into
    series/observations (decision 0012).

    Structurally different from load_fred_series_observations: FRED is
    one series per pipeline call, but one World Bank/IMF indicator spans
    up to 260 countries in a single frame. One get-or-create series row
    per country, then that country's observations loaded under it --
    full-refresh per country, same semantics as every other load function
    here, just applied per group instead of once per call.

    Expects the same frame shape world_bank_records_to_frame and
    imf_indicator_values_to_frame already produce (source, indicator_code,
    indicator_name, country_code, country_name, year, value, loaded_at) --
    the existing indicator_observations shape, not a new one.
    """
    if frame.empty:
        logger.warning(
            "Nothing to migrate for %s / %s -- empty frame", source, indicator_code
        )
        return 0

    spec = get_migration_spec(source, indicator_code)
    total_rows = 0
    country_count = 0

    with engine.begin() as conn:
        for country_code, country_frame in frame.groupby("country_code"):
            country_count += 1
            indicator_name = country_frame["indicator_name"].iloc[0]

            existing = conn.execute(
                select(series.c.id).where(
                    series.c.source == source,
                    series.c.source_series_id == indicator_code,
                    series.c.country_code == country_code,
                )
            ).first()

            if existing is not None:
                series_pk = existing.id
            else:
                result = conn.execute(
                    insert(series).values(
                        source=source,
                        source_series_id=indicator_code,
                        indicator_name=indicator_name,
                        country_code=country_code,
                        frequency=spec.frequency,
                        frequency_short=spec.frequency_short,
                        units=spec.units,
                        units_short=spec.units_short,
                        seasonal_adjustment=spec.seasonal_adjustment,
                        seasonal_adjustment_short=spec.seasonal_adjustment_short,
                        created_at=date.today(),
                    )
                )
                series_pk = result.inserted_primary_key[0]

            conn.execute(delete(observations).where(observations.c.series_id == series_pk))

            obs_rows = [
                {
                    "series_id": series_pk,
                    "date": _year_to_date(int(row.year), spec.date_convention),
                    "value": None if pd.isna(row.value) else float(row.value),
                    "loaded_at": row.loaded_at,
                }
                for row in country_frame.itertuples()
            ]
            if obs_rows:
                conn.execute(insert(observations), obs_rows)
                total_rows += len(obs_rows)

    logger.info(
        "Migrated %s observations across %s countries for %s / %s",
        total_rows, country_count, source, indicator_code,
    )
    return total_rows
