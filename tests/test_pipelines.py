"""Smoke tests for pipeline entry points — confirms each thin wrapper
targets the right indicator, without needing network or DB access."""
from etl.pipelines import imf_real_gdp_growth, world_bank_gdp, world_bank_population


def test_gdp_pipeline_indicator_code():
    assert world_bank_gdp.INDICATOR_CODE == "NY.GDP.MKTP.CD"
    assert callable(world_bank_gdp.run)


def test_population_pipeline_indicator_code():
    assert world_bank_population.INDICATOR_CODE == "SP.POP.TOTL"
    assert callable(world_bank_population.run)


def test_pipelines_target_different_indicators():
    assert world_bank_gdp.INDICATOR_CODE != world_bank_population.INDICATOR_CODE


def test_imf_pipeline_indicator_code():
    assert imf_real_gdp_growth.INDICATOR_CODE == "NGDP_RPCH"
    assert callable(imf_real_gdp_growth.run)
