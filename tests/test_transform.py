"""Unit tests for World Bank record transformation. No network or DB required."""
import math

from etl.transform import world_bank_records_to_frame

SAMPLE_RECORDS = [
    {
        "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
        "country": {"id": "US", "value": "United States"},
        "countryiso3code": "USA",
        "date": "2023",
        "value": 27360935000000.0,
    },
    {
        "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
        "country": {"id": "US", "value": "United States"},
        "countryiso3code": "USA",
        "date": "2022",
        "value": None,  # World Bank has real reporting gaps
    },
    {
        # Aggregate/region row — no real ISO3 code, must be dropped
        "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
        "country": {"id": "1W", "value": "World"},
        "countryiso3code": "",
        "date": "2023",
        "value": 105000000000000.0,
    },
]


def test_drops_aggregate_rows_without_iso3():
    frame = world_bank_records_to_frame(SAMPLE_RECORDS)
    assert set(frame["country_code"]) == {"USA"}
    assert len(frame) == 2


def test_preserves_null_values():
    frame = world_bank_records_to_frame(SAMPLE_RECORDS)
    row_2022 = frame[frame["year"] == 2022].iloc[0]
    assert row_2022["value"] is None or math.isnan(row_2022["value"])


def test_output_columns():
    frame = world_bank_records_to_frame(SAMPLE_RECORDS)
    expected = {
        "source", "indicator_code", "indicator_name",
        "country_code", "country_name", "year", "value", "loaded_at",
    }
    assert set(frame.columns) == expected


def test_empty_input_returns_empty_frame():
    frame = world_bank_records_to_frame([])
    assert frame.empty
