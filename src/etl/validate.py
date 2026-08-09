"""Data-quality checks run before load.

Hard failures (raise) catch structural problems that mean the data
shouldn't be loaded at all. Soft warnings (log only) flag things worth
a human's attention without blocking an otherwise-valid run — missing
values are normal for some country/year combinations, a high null rate
might not be.
"""
from __future__ import annotations

import logging
from datetime import date

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "source", "indicator_code", "indicator_name",
    "country_code", "country_name", "year", "value", "loaded_at",
}
MIN_YEAR = 1960
# IMF's WEO-based indicators (e.g. NGDP_RPCH) carry forward-looking
# forecasts, typically ~5 years past the current year. World Bank data
# is actuals-only, so this ceiling is generous for it but necessary for
# IMF. See decisions/0005.
MAX_YEAR_OFFSET = 5
NULL_RATE_WARNING_THRESHOLD = 0.5


class ValidationError(ValueError):
    """Raised when a frame fails a hard data-quality check."""


def validate_frame(frame: pd.DataFrame, indicator_code: str) -> None:
    """Run quality checks on a transformed frame before it's loaded.

    Raises ValidationError on structural problems. Logs a warning for
    conditions that are suspicious but not necessarily wrong.
    """
    if frame.empty:
        raise ValidationError(f"{indicator_code}: transformed frame is empty")

    missing_cols = REQUIRED_COLUMNS - set(frame.columns)
    if missing_cols:
        raise ValidationError(f"{indicator_code}: missing columns {missing_cols}")

    bad_codes = frame.loc[frame["country_code"].str.len() != 3, "country_code"].unique()
    if len(bad_codes) > 0:
        raise ValidationError(
            f"{indicator_code}: non-ISO3 country codes slipped through: {list(bad_codes)}"
        )

    current_year = date.today().year
    max_year = current_year + MAX_YEAR_OFFSET
    out_of_range = frame[(frame["year"] < MIN_YEAR) | (frame["year"] > max_year)]
    if not out_of_range.empty:
        raise ValidationError(
            f"{indicator_code}: {len(out_of_range)} rows with year outside "
            f"[{MIN_YEAR}, {max_year}]"
        )

    dupes = frame.duplicated(subset=["source", "indicator_code", "country_code", "year"])
    if dupes.any():
        raise ValidationError(
            f"{indicator_code}: {int(dupes.sum())} duplicate (country_code, year) rows"
        )

    null_rate = frame["value"].isna().mean()
    if null_rate > NULL_RATE_WARNING_THRESHOLD:
        logger.warning(
            "%s: %.0f%% of values are null — verify this is expected, not an API regression",
            indicator_code, null_rate * 100,
        )

    logger.info("%s: validation passed (%s rows)", indicator_code, len(frame))
