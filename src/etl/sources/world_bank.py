"""Extraction from the World Bank Indicators API (V2).

No API key required. V1 was discontinued in 2020 — the /v2/ path
segment is mandatory. Docs:
https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
"""
from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.worldbank.org/v2"
DEFAULT_PER_PAGE = 1000


def fetch_indicator(
    indicator_code: str,
    country: str = "all",
    per_page: int = DEFAULT_PER_PAGE,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """Fetch every page of an indicator for the given country scope.

    Returns raw World Bank records (list of dicts), unfiltered — includes
    aggregate/region rows, which `transform.py` drops.
    """
    url = f"{BASE_URL}/country/{country}/indicator/{indicator_code}"
    params: dict[str, Any] = {"format": "json", "per_page": per_page, "page": 1}

    records: list[dict[str, Any]] = []
    page, total_pages = 1, 1

    while page <= total_pages:
        params["page"] = page
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, list) or len(payload) != 2:
            raise ValueError(
                f"Unexpected World Bank response shape for {indicator_code} "
                f"page {page}: {payload!r}"
            )

        meta, page_records = payload
        if page_records is None:
            break

        records.extend(page_records)
        total_pages = meta.get("pages", 1) or 1
        logger.info(
            "Fetched page %s/%s (%s records so far)", page, total_pages, len(records)
        )
        page += 1

    return records
