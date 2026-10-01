"""Load validated observations into MDO's canonical series-first schema.

World Bank and IMF are loaded as one canonical series per country; FRED is
loaded as one canonical series per pipeline call. Active load paths write only
to ``series`` and ``observations``.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from .db import observations, series

logger = logging.getLogger(__name__)


def load_fred_series_observations(
    frame: pd.DataFrame,
    engine: Engine,
    source_series_id: str,
    country_code: str,
    live_metadata: dict[str, Any],
) -> int:
    """Get-or-create the series row, then full-refresh its observations.

    The series row must exist, and its database-assigned id must be resolved,
    before observations can reference it via foreign key.
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
class AnnualSeriesSpec:
    """Canonical metadata for one annual World Bank/IMF series family.

    Decision 0012 established these frequency, seasonal-adjustment, units,
    and year-to-date conventions during migration to the series-first schema.
    They remain active metadata for current ingestion after the legacy table's
    retirement.
    """

    frequency: str
    frequency_short: str
    seasonal_adjustment: str
    seasonal_adjustment_short: str
    units: str
    units_short: str
    date_convention: str  # "stock" or "flow"


ANNUAL_SERIES_REGISTRY: dict[tuple[str, str], AnnualSeriesSpec] = {
    ("world_bank", "NY.GDP.MKTP.CD"): AnnualSeriesSpec(
        frequency="Annual", frequency_short="A",
        seasonal_adjustment="Not Seasonally Adjusted", seasonal_adjustment_short="NSA",
        units="Current US$", units_short="USD",
        date_convention="flow",
    ),
    ("world_bank", "SP.POP.TOTL"): AnnualSeriesSpec(
        frequency="Annual", frequency_short="A",
        seasonal_adjustment="Not Seasonally Adjusted", seasonal_adjustment_short="NSA",
        units="Persons", units_short="Count",
        date_convention="stock",
    ),
    ("imf", "NGDP_RPCH"): AnnualSeriesSpec(
        frequency="Annual", frequency_short="A",
        seasonal_adjustment="Not Seasonally Adjusted", seasonal_adjustment_short="NSA",
        units="Annual percent change", units_short="%",
        date_convention="flow",
    ),
    ("imf", "PCPIPCH"): AnnualSeriesSpec(
        frequency="Annual", frequency_short="A",
        seasonal_adjustment="Not Seasonally Adjusted", seasonal_adjustment_short="NSA",
        units="Annual percent change", units_short="%",
        date_convention="flow",
    ),
}


def get_annual_series_spec(source: str, indicator_code: str) -> AnnualSeriesSpec:
    """Look up canonical annual-series metadata for a source/indicator pair.

    Raises ``KeyError`` if the pair is not registered. New annual indicators
    require an explicit metadata decision rather than guessed units, frequency,
    seasonal adjustment, or date convention.
    """
    try:
        return ANNUAL_SERIES_REGISTRY[(source, indicator_code)]
    except KeyError as exc:
        raise KeyError(
            f"({source!r}, {indicator_code!r}) is not in "
            "ANNUAL_SERIES_REGISTRY. Add an entry with its frequency, "
            "seasonal adjustment, units, and date convention before loading "
            "this indicator."
        ) from exc


def _year_to_date(year: int, date_convention: str) -> date:
    if date_convention == "stock":
        return date(year, 7, 1)
    if date_convention == "flow":
        return date(year, 1, 1)
    raise ValueError(f"Unknown date_convention: {date_convention!r}")


def load_annual_indicator_series(
    frame: pd.DataFrame, engine: Engine, source: str, indicator_code: str
) -> int:
    """Load a multi-country annual indicator frame into series/observations.

    Structurally different from load_fred_series_observations: FRED is
    one series per pipeline call, but one World Bank/IMF indicator spans
    up to 260 countries in a single frame. One get-or-create series row
    per country, then that country's observations loaded under it --
    full-refresh per country, same semantics as every other load function
    here, just applied per group instead of once per call.

    Expects the annual indicator frame produced by the World Bank and IMF
    transforms: source, indicator_code, indicator_name, country_code,
    country_name, year, value, and loaded_at.
    """
    if frame.empty:
        logger.warning(
            "Nothing to load for %s / %s -- empty frame", source, indicator_code
        )
        return 0

    spec = get_annual_series_spec(source, indicator_code)
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
        "Loaded %s observations across %s countries for %s / %s",
        total_rows, country_count, source, indicator_code,
    )
    return total_rows
