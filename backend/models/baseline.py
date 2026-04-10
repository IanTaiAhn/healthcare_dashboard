"""
Naive seasonal baseline — the floor all other models must beat.

Forecast = same month last year. Surprisingly competitive for
monthly employment series with strong seasonal patterns.
"""

import pandas as pd


def forecast_naive_seasonal(
    series: pd.Series,
    horizon: int = 6,
) -> pd.DataFrame:
    """
    Naive seasonal forecast: each future month = same month one year prior.

    Args:
        series: Monthly time series with DatetimeIndex
        horizon: Number of months to forecast

    Returns:
        DataFrame with columns: month, projected (no confidence bands — it's naive)
    """
    if len(series) < 12:
        raise ValueError("Need at least 12 months of history for seasonal naive baseline")

    last_date = series.index.max()
    forecasts = []

    for h in range(1, horizon + 1):
        forecast_date = last_date + pd.DateOffset(months=h)
        # Look back exactly 12 months from the forecast date
        lookback_date = forecast_date - pd.DateOffset(months=12)

        # Find closest available date in the series
        nearest_idx = series.index.get_indexer([lookback_date], method="nearest")[0]
        value = series.iloc[nearest_idx]

        forecasts.append({
            "month": forecast_date.strftime("%Y-%m"),
            "projected": float(value),
        })

    return pd.DataFrame(forecasts)


def compute_naive_mae(
    series: pd.Series,
    test_start: str = "2022-01-01",
    horizon: int = 6,
) -> float:
    """
    Compute MAE of the naive seasonal baseline on the test period.

    Walk-forward: at each month in test_start..end, forecast `horizon`
    months ahead using same-month-last-year, then compute MAE over
    all horizon-step-ahead forecasts.
    """
    test_data = series[test_start:]
    errors = []

    for i in range(len(test_data) - horizon):
        actual_future = test_data.iloc[i + horizon]
        # Same month, one year before the forecast target
        target_date = test_data.index[i + horizon]
        lookback = target_date - pd.DateOffset(months=12)
        nearest_idx = series.index.get_indexer([lookback], method="nearest")[0]
        naive_forecast = series.iloc[nearest_idx]
        errors.append(abs(actual_future - naive_forecast))

    return sum(errors) / len(errors) if errors else float("inf")
