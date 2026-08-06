"""Transform raw source records into the indicator_observations shape."""
from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd


def world_bank_records_to_frame(
    records: list[dict[str, Any]], source: str = "world_bank"
) -> pd.DataFrame:
    """Convert raw World Bank API records into a tidy DataFrame.

    Drops aggregate/region rows (e.g. "World", "Sub-Saharan Africa",
    income-level groups) — these are returned by the same endpoint but
    don't carry a real 3-letter ISO3 country code, so this table stays
    country-level only. World Bank sometimes returns an empty string and
    sometimes a non-ISO3 placeholder for these; checking the length
    covers both.
    """
    rows = []
    for rec in records:
        iso3 = rec.get("countryiso3code")
        if not iso3 or len(iso3) != 3:
            continue

        try:
            year = int(rec.get("date"))
        except (TypeError, ValueError):
            continue

        rows.append(
            {
                "source": source,
                "indicator_code": rec["indicator"]["id"],
                "indicator_name": rec["indicator"]["value"],
                "country_code": iso3,
                "country_name": rec["country"]["value"],
                "year": year,
                "value": rec.get("value"),
                "loaded_at": date.today(),
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame = frame.drop_duplicates(
        subset=["source", "indicator_code", "country_code", "year"]
    )
    return frame.sort_values(["country_code", "year"]).reset_index(drop=True)


def imf_indicator_values_to_frame(
    values: dict[str, dict[str, Any]],
    indicator_code: str,
    indicator_name: str,
    country_names: dict[str, str],
    source: str = "imf",
) -> pd.DataFrame:
    """Convert IMF country/year values into a tidy DataFrame.

    ``country_names`` is the country metadata supplied by the caller. Only
    country codes present in that mapping are emitted, keeping aggregate and
    analytical-group series out of the country-level observation table.
    """
    rows = []
    for country_code, observations in values.items():
        country_name = country_names.get(country_code)
        if not country_name:
            continue

        for year_text, value in observations.items():
            try:
                year = int(year_text)
            except (TypeError, ValueError):
                continue

            rows.append(
                {
                    "source": source,
                    "indicator_code": indicator_code,
                    "indicator_name": indicator_name,
                    "country_code": country_code,
                    "country_name": country_name,
                    "year": year,
                    "value": value,
                    "loaded_at": date.today(),
                }
            )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame = frame.drop_duplicates(
        subset=["source", "indicator_code", "country_code", "year"]
    )
    return frame.sort_values(["country_code", "year"]).reset_index(drop=True)
