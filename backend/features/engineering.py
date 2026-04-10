"""
Feature engineering — derived features, lag construction, composite scores.

All features documented in the design doc Section 5.3.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

CONFIG_PATH = Path(__file__).parent / "preprocessing_config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def build_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct lag features for series that specify lag_months in config.
    Column naming: {series_id}_lag{N}
    """
    config = load_config()
    series_configs = {s["id"]: s for s in config["series"]}
    result = df.copy()

    for sid, sc in series_configs.items():
        if sid not in df.columns:
            continue
        lags = sc.get("lag_months", [])
        for lag in lags:
            result[f"{sid}_lag{lag}"] = df[sid].shift(lag)

    return result


def compute_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived features from raw series.

    These are computed on LEVEL data (before differencing) where indicated,
    so callers may need to pass both raw and processed DataFrames.
    """
    result = df.copy()

    # Healthcare employment share of Utah total
    if "UTEDUH" in df.columns and "UTNA" in df.columns:
        result["healthcare_employment_share_ut"] = df["UTEDUH"] / df["UTNA"]

    # Quit rate 3-month moving average
    if "JTS6200QUR" in df.columns:
        result["quit_rate_3m_ma"] = df["JTS6200QUR"].rolling(3).mean()

    # YoY wage growth
    if "CES6500000003" in df.columns:
        result["wage_growth_yoy"] = df["CES6500000003"].pct_change(12) * 100

    # Real wage growth (wage growth minus CPI growth)
    if "CES6500000003" in df.columns and "CPIAUCSL" in df.columns:
        wage_yoy = df["CES6500000003"].pct_change(12) * 100
        cpi_yoy = df["CPIAUCSL"].pct_change(12) * 100
        result["real_wage_growth"] = wage_yoy - cpi_yoy

    # Utah employment momentum (month-over-month change)
    if "UTNA" in df.columns:
        result["ut_employment_mom_change"] = df["UTNA"].diff()

    return result


def compute_composite_stress_score(
    quit_rate_series: pd.Series,
    openings_rate_series: pd.Series,
    wage_growth_series: pd.Series,
    baseline_start: str = "2010-01",
    baseline_end: str = "2019-12",
) -> pd.DataFrame:
    """
    Compute the Composite Stress Score (CSS) — the headline dashboard signal.

    Each input is percentile-ranked against the 2010-2019 baseline,
    then averaged into a single 0-100 score.

    Args:
        quit_rate_series: Healthcare quit rate (level)
        openings_rate_series: Healthcare job openings rate (level)
        wage_growth_series: Healthcare wage growth YoY % (level)
        baseline_start/end: Pre-pandemic baseline for percentile ranking

    Returns:
        DataFrame with columns: quit_pct, openings_pct, wage_pct, css, signal_state
    """

    def percentile_vs_baseline(series: pd.Series, start: str, end: str) -> pd.Series:
        baseline = series[start:end].dropna()
        if len(baseline) == 0:
            return pd.Series(50, index=series.index)
        return series.apply(lambda x: (baseline < x).sum() / len(baseline) * 100)

    quit_pct = percentile_vs_baseline(quit_rate_series, baseline_start, baseline_end)
    openings_pct = percentile_vs_baseline(openings_rate_series, baseline_start, baseline_end)
    wage_pct = percentile_vs_baseline(wage_growth_series, baseline_start, baseline_end)

    css = (quit_pct + openings_pct + wage_pct) / 3

    def classify(score):
        if score >= 67:
            return "tightening"
        elif score >= 33:
            return "stable"
        else:
            return "easing"

    result = pd.DataFrame(
        {
            "quit_pct": quit_pct,
            "openings_pct": openings_pct,
            "wage_pct": wage_pct,
            "css": css,
            "signal_state": css.apply(classify),
        }
    )

    return result
