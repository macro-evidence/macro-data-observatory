"""Environment configuration for MDO ETL pipelines."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    request_timeout: int = 30


def get_settings() -> Settings:
    """Read settings from the environment. Raises only when actually called,
    not on import, so importing this module never requires a live .env.
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and fill it in."
        )
    return Settings(database_url=database_url)
