"""Extraction from the International Monetary Fund (IMF).

The transport endpoint is private to this module. ``fetch_indicator``
returns IMF country/year values rather than a transport-specific response
envelope, so callers depend on IMF concepts only.
"""
from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.imf.org/external/datamapper/api/v1"


def fetch_indicator(
    indicator_code: str,
    country: str = "all",
    timeout: int = 30,
) -> dict[str, dict[str, Any]]:
    """Fetch country-year values for an IMF indicator.

    ``country`` defaults to ``"all"``. Supplying an IMF country code limits
    the result to that country.
    """
    url = f"{_BASE_URL}/{indicator_code}"
    if country != "all":
        url = f"{url}/{country}"

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(
            f"Unexpected IMF response shape for {indicator_code}: {payload!r}"
        )

    values = payload.get("values")
    indicator_values = values.get(indicator_code) if isinstance(values, dict) else None
    if not isinstance(indicator_values, dict):
        raise ValueError(
            f"Unexpected IMF response shape for {indicator_code}: {payload!r}"
        )

    if country != "all":
        indicator_values = (
            {country: indicator_values[country]}
            if country in indicator_values
            else {}
        )

    logger.info(
        "Fetched IMF indicator %s for %s (%s country series)",
        indicator_code,
        country,
        len(indicator_values),
    )
    return indicator_values


def fetch_indicator_name(indicator_code: str, timeout: int = 30) -> str:
    """Fetch the authoritative IMF label for an indicator code."""
    response = requests.get(f"{_BASE_URL}/indicators", timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    indicators = payload.get("indicators") if isinstance(payload, dict) else None
    indicator = indicators.get(indicator_code) if isinstance(indicators, dict) else None
    label = indicator.get("label") if isinstance(indicator, dict) else None
    if not isinstance(label, str):
        raise ValueError(
            f"Unexpected IMF indicator metadata for {indicator_code}: {payload!r}"
        )

    logger.info("Fetched IMF indicator metadata for %s", indicator_code)
    return label


def fetch_country_names(timeout: int = 30) -> dict[str, str]:
    """Fetch the authoritative IMF country-code-to-name mapping."""
    response = requests.get(f"{_BASE_URL}/countries", timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    countries = payload.get("countries") if isinstance(payload, dict) else None
    if not isinstance(countries, dict):
        raise ValueError(f"Unexpected IMF country metadata: {payload!r}")

    country_names = {
        country_code: metadata["label"]
        for country_code, metadata in countries.items()
        if isinstance(metadata, dict) and isinstance(metadata.get("label"), str)
    }
    logger.info("Fetched IMF country metadata (%s countries)", len(country_names))
    return country_names
