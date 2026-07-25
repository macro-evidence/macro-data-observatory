"""Entry point: World Bank total population ingestion.

Run directly:
    python -m etl.pipelines.world_bank_population
"""
from __future__ import annotations

from .common import run_world_bank_indicator

INDICATOR_CODE = "SP.POP.TOTL"


def run() -> int:
    return run_world_bank_indicator(INDICATOR_CODE)


if __name__ == "__main__":
    run()
