"""Unit tests for the shared pipeline runner. No network or DB required."""
from unittest.mock import Mock, patch

import pandas as pd

from etl.pipelines import common


@patch("etl.pipelines.common.load_annual_indicator_series", return_value=3)
@patch("etl.pipelines.common.validate_frame")
@patch("etl.pipelines.common.create_tables")
@patch("etl.pipelines.common.get_engine")
def test_run_pipeline_wires_extract_transform_validate_load(
    mock_get_engine, mock_create_tables, mock_validate, mock_load
):
    engine = Mock()
    mock_get_engine.return_value = engine
    frame = pd.DataFrame({"country_code": ["USA"]})
    extract = Mock(return_value={"raw": True})
    transform = Mock(return_value=frame)

    row_count = common.run_pipeline(
        indicator_code="NY.GDP.MKTP.CD",
        source="world_bank",
        extract=extract,
        transform=transform,
    )

    assert row_count == 3
    mock_create_tables.assert_called_once_with(engine)
    extract.assert_called_once_with("NY.GDP.MKTP.CD")
    transform.assert_called_once_with({"raw": True})
    mock_validate.assert_called_once_with(frame, "NY.GDP.MKTP.CD")
    mock_load.assert_called_once_with(frame, engine, "world_bank", "NY.GDP.MKTP.CD")


@patch("etl.pipelines.common.run_pipeline")
def test_run_world_bank_indicator_binds_source_and_world_bank_steps(mock_run_pipeline):
    mock_run_pipeline.return_value = 5

    row_count = common.run_world_bank_indicator("NY.GDP.MKTP.CD")

    assert row_count == 5
    mock_run_pipeline.assert_called_once()
    _, kwargs = mock_run_pipeline.call_args
    assert kwargs["indicator_code"] == "NY.GDP.MKTP.CD"
    assert kwargs["source"] == "world_bank"
    assert callable(kwargs["extract"])
    assert callable(kwargs["transform"])


def test_run_world_bank_indicator_extract_and_transform_are_wired_correctly():
    """Confirm the bound extract/transform actually call the right
    World Bank functions, rather than just being any callables."""
    with patch("etl.pipelines.common.fetch_world_bank_indicator") as mock_fetch, \
         patch("etl.pipelines.common.world_bank_records_to_frame") as mock_transform, \
         patch("etl.pipelines.common.get_engine"), \
         patch("etl.pipelines.common.create_tables"), \
         patch("etl.pipelines.common.validate_frame"), \
         patch("etl.pipelines.common.load_annual_indicator_series", return_value=7):
        mock_fetch.return_value = [{"raw": True}]
        mock_transform.return_value = pd.DataFrame({"country_code": ["USA"]})

        row_count = common.run_world_bank_indicator("NY.GDP.MKTP.CD")

        assert row_count == 7
        mock_fetch.assert_called_once_with("NY.GDP.MKTP.CD")
        mock_transform.assert_called_once_with(
            [{"raw": True}], source="world_bank"
        )


def test_run_pipeline_persists_only_canonical_series_schema():
    """The shared runner writes World Bank/IMF data to series/observations only."""
    from datetime import date
    from sqlalchemy import create_engine, inspect, select, func
    from etl.db import metadata, series, observations

    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)

    frame = pd.DataFrame([
        {"source": "world_bank", "indicator_code": "NY.GDP.MKTP.CD",
         "indicator_name": "GDP (current US$)", "country_code": "USA",
         "country_name": "United States", "year": 2023, "value": 27000000000000.0,
         "loaded_at": date.today()},
    ])

    with patch("etl.pipelines.common.get_engine", return_value=engine), \
         patch("etl.pipelines.common.create_tables"), \
         patch("etl.pipelines.common.validate_frame"):
        common.run_pipeline(
            indicator_code="NY.GDP.MKTP.CD", source="world_bank",
            extract=lambda code: "raw", transform=lambda raw: frame,
        )

    assert set(inspect(engine).get_table_names()) == {"observations", "series"}
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(series)).scalar() == 1
        assert conn.execute(select(func.count()).select_from(observations)).scalar() == 1
