"""Extraction from the Federal Reserve Economic Data (FRED) API.

FRED is series-atomic (decision 0010): one series_id already identifies a
concept, country, frequency, and seasonal-adjustment combination. There is
no indicator+country combinator the way World Bank/IMF have, so FRED series
are looked up by exact ID via a curated registry (FRED_SERIES_REGISTRY
below), not discovered at runtime through fred/series/search. Search is a
discovery-time tool for humans, not a pipeline dependency (decision 0010).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests

from ..config import get_settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.stlouisfed.org/fred"


@dataclass(frozen=True)
class FredSeriesSpec:
    """A curated FRED series registration.

    ``expected_frequency_short``/``expected_seasonal_adjustment_short`` are
    checked against FRED's own live metadata (``fetch_series_metadata``) at
    pipeline run time — a registered series whose actual metadata has
    drifted from what was registered here is a data-governance problem to
    surface loudly, not load silently.
    """

    series_id: str
    country_code: str
    expected_frequency_short: str
    expected_seasonal_adjustment_short: str


FRED_SERIES_REGISTRY: dict[str, FredSeriesSpec] = {
    "unemployment_rate": FredSeriesSpec(
        series_id="UNRATE",
        country_code="USA",
        expected_frequency_short="M",
        expected_seasonal_adjustment_short="SA",
    ),
}
"""MDO concept name -> curated FRED series. See decision 0011 for
``unemployment_rate``'s selection rationale and its live-verified metadata.
"""


def get_series_spec(concept: str) -> FredSeriesSpec:
    """Look up a registered FRED series by MDO concept name.

    Raises KeyError if the concept isn't registered. The registry is
    curated, not runtime-discovered (decision 0010) — an unregistered
    concept means adding a registry entry, not searching for one at
    request time.
    """
    try:
        return FRED_SERIES_REGISTRY[concept]
    except KeyError as exc:
        raise KeyError(
            f"{concept!r} is not in FRED_SERIES_REGISTRY. FRED series are "
            "registered explicitly (decision 0010); add an entry rather "
            "than discovering one at runtime."
        ) from exc


def verify_registered_metadata(concept: str, live_metadata: dict[str, Any]) -> None:
    """Confirm a series' live metadata still matches its registry entry.

    Raises ValueError on drift — a registered series whose actual
    frequency or seasonal-adjustment status no longer matches what was
    registered is a data-governance problem to surface loudly (per this
    module's registry docstring), not something a pipeline should load
    past silently.
    """
    spec = get_series_spec(concept)
    live_frequency = live_metadata.get("frequency_short")
    live_seasonal_adjustment = live_metadata.get("seasonal_adjustment_short")

    mismatches = []
    if live_frequency != spec.expected_frequency_short:
        mismatches.append(
            f"frequency_short: expected {spec.expected_frequency_short!r}, "
            f"got {live_frequency!r}"
        )
    if live_seasonal_adjustment != spec.expected_seasonal_adjustment_short:
        mismatches.append(
            f"seasonal_adjustment_short: expected "
            f"{spec.expected_seasonal_adjustment_short!r}, got "
            f"{live_seasonal_adjustment!r}"
        )

    if mismatches:
        raise ValueError(
            f"{concept!r} ({spec.series_id}) metadata drift detected: "
            + "; ".join(mismatches)
        )


def fetch_series_metadata(series_id: str, timeout: int = 30) -> dict[str, Any]:
    """Fetch a FRED series' own metadata (frequency, units, seasonal
    adjustment, coverage) via ``fred/series``.

    Used to verify a registry entry's expected metadata against FRED's
    live, authoritative record before a pipeline trusts it — not used for
    discovery.
    """
    settings = get_settings()
    if not settings.fred_api_key:
        raise RuntimeError(
            "FRED_API_KEY is not set. Copy .env.example to .env and fill it in."
        )

    response = requests.get(
        f"{_BASE_URL}/series",
        params={
            "api_key": settings.fred_api_key,
            "series_id": series_id,
            "file_type": "json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    seriess = payload.get("seriess") if isinstance(payload, dict) else None
    if not isinstance(seriess, list) or not seriess:
        raise ValueError(f"Unexpected FRED series response for {series_id}: {payload!r}")

    logger.info("Fetched FRED series metadata for %s", series_id)
    return seriess[0]


def fetch_series_observations(
    series_id: str, timeout: int = 30
) -> list[dict[str, Any]]:
    """Fetch all observations for a FRED series via
    ``fred/series/observations``.

    Returns the raw observation records (``date``/``value`` pairs, plus
    FRED's own ``realtime_start``/``realtime_end`` on each) exactly as FRED
    returns them. Missing values arrive as the literal string ``"."``
    (confirmed live, decision 0010) — left untouched here; converting
    ``"."`` to null is transform's job, not extraction's.
    """
    settings = get_settings()
    if not settings.fred_api_key:
        raise RuntimeError(
            "FRED_API_KEY is not set. Copy .env.example to .env and fill it in."
        )

    response = requests.get(
        f"{_BASE_URL}/series/observations",
        params={
            "api_key": settings.fred_api_key,
            "series_id": series_id,
            "file_type": "json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()

    observations = payload.get("observations") if isinstance(payload, dict) else None
    if not isinstance(observations, list):
        raise ValueError(
            f"Unexpected FRED observations response for {series_id}: {payload!r}"
        )

    logger.info(
        "Fetched %s observations for FRED series %s", len(observations), series_id
    )
    return observations
