"""
Preprocessing pipeline — frequency alignment, stationarity transforms.

All decisions are driven by preprocessing_config.yaml — no hardcoded
transform logic. Change the YAML, change the pipeline.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

CONFIG_PATH = Path(__file__).parent / "preprocessing_config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def align_to_monthly(series: pd.Series, series_config: dict) -> pd.Series:
    """
    Align a series to monthly frequency based on its config.

    Weekly → last observation of the month
    Quarterly → forward-fill to monthly
    Annual → forward-fill to monthly
    Monthly → no change
    """
    freq = series_config.get("frequency", "monthly")
    alignment = series_config.get("monthly_alignment", None)

    if freq == "weekly":
        # Resample to month-end, take last observation
        return series.resample("MS").last()
    elif freq == "quarterly":
        # Forward-fill quarterly to monthly
        monthly_index = pd.date_range(
            series.index.min(), series.index.max(), freq="MS"
        )
        return series.reindex(monthly_index).ffill()
    elif freq == "annual":
        monthly_index = pd.date_range(
            series.index.min(), series.index.max(), freq="MS"
        )
        return series.reindex(monthly_index).ffill()
    else:
        return series


def apply_transforms(series: pd.Series, series_config: dict) -> pd.Series:
    """
    Apply log transform and differencing per config.

    Order: log → difference (standard in macro econometrics).
    """
    result = series.copy()

    # Log transform (stabilizes variance for level series)
    if series_config.get("log_transform", False):
        result = np.log(result)

    # Differencing (achieves stationarity)
    diff_order = series_config.get("differencing", 0)
    for _ in range(diff_order):
        result = result.diff()

    return result.dropna()


def add_covid_dummy(index: pd.DatetimeIndex, config: dict) -> pd.Series:
    """Create binary covid_shock feature for the configured period."""
    covid_start = pd.Timestamp(config["covid_shock_period"]["start"])
    covid_end = pd.Timestamp(config["covid_shock_period"]["end"])
    return pd.Series(
        ((index >= covid_start) & (index <= covid_end)).astype(int),
        index=index,
        name="covid_shock",
    )


def preprocess_all(raw_series: dict[str, pd.Series]) -> pd.DataFrame:
    """
    Full preprocessing pipeline:
      1. Align all series to monthly
      2. Apply log + differencing per config
      3. Join into a single DataFrame
      4. Add covid_shock dummy

    Args:
        raw_series: dict mapping series_id → raw pandas Series

    Returns:
        DataFrame with monthly index, one column per processed series + covid_shock
    """
    config = load_config()
    series_configs = {s["id"]: s for s in config["series"]}

    processed = {}
    for sid, data in raw_series.items():
        if sid not in series_configs:
            print(f"  ⚠ {sid} not in config, skipping")
            continue

        sc = series_configs[sid]
        aligned = align_to_monthly(data, sc)
        transformed = apply_transforms(aligned, sc)
        processed[sid] = transformed

    if not processed:
        return pd.DataFrame()

    # Join on common monthly index
    df = pd.DataFrame(processed)

    # Add COVID dummy
    df["covid_shock"] = add_covid_dummy(df.index, config)

    return df
