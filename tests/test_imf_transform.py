"""Unit tests for IMF value transformation. No network or DB required."""
import math

from etl.transform import imf_indicator_values_to_frame

SAMPLE_VALUES = {
    "USA": {"2023": 2.9, "2022": None},
    "IND": {"2023": 9.2, "not-a-year": 7.6},
    "WORLD": {"2023": 3.2},
}

COUNTRY_NAMES = {
    "USA": "United States",
    "IND": "India",
}


def test_drops_series_not_in_country_metadata():
    frame = imf_indicator_values_to_frame(
        SAMPLE_VALUES,
        indicator_code="NGDP_RPCH",
        indicator_name="Real GDP growth",
        country_names=COUNTRY_NAMES,
    )

    assert set(frame["country_code"]) == {"USA", "IND"}
    assert "WORLD" not in set(frame["country_code"])
    assert len(frame) == 3


def test_drops_invalid_years_and_preserves_null_values():
    frame = imf_indicator_values_to_frame(
        SAMPLE_VALUES,
        indicator_code="NGDP_RPCH",
        indicator_name="Real GDP growth",
        country_names=COUNTRY_NAMES,
    )

    assert set(frame["year"]) == {2022, 2023}
    usa_2022 = frame[
        (frame["country_code"] == "USA") & (frame["year"] == 2022)
    ].iloc[0]
    assert usa_2022["value"] is None or math.isnan(usa_2022["value"])


def test_output_columns_and_metadata():
    frame = imf_indicator_values_to_frame(
        SAMPLE_VALUES,
        indicator_code="NGDP_RPCH",
        indicator_name="Real GDP growth",
        country_names=COUNTRY_NAMES,
    )

    expected = {
        "source", "indicator_code", "indicator_name",
        "country_code", "country_name", "year", "value", "loaded_at",
    }
    assert set(frame.columns) == expected
    assert set(frame["source"]) == {"imf"}
    assert set(frame["indicator_name"]) == {"Real GDP growth"}


def test_empty_input_returns_empty_frame():
    frame = imf_indicator_values_to_frame(
        {},
        indicator_code="NGDP_RPCH",
        indicator_name="Real GDP growth",
        country_names=COUNTRY_NAMES,
    )

    assert frame.empty


def test_requires_country_metadata_to_emit_a_series():
    frame = imf_indicator_values_to_frame(
        {"USA": {"2023": 2.9}},
        indicator_code="NGDP_RPCH",
        indicator_name="Real GDP growth",
        country_names={},
    )

    assert frame.empty
