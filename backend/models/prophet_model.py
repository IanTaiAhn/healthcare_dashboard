"""
Facebook Prophet model — secondary comparison model.

Prophet handles COVID changepoints well via its built-in changepoint
detection. Used as a comparison against SARIMAX in backtesting notebooks.
"""

from dataclasses import dataclass

import pandas as pd

# from prophet import Prophet  # Uncomment when ready


def fit_prophet(
    series: pd.Series,
    changepoint_prior_scale: float = 0.05,
    seasonality_mode: str = "multiplicative",
    yearly_seasonality: bool = True,
    weekly_seasonality: bool = False,
    daily_seasonality: bool = False,
) -> object:
    """
    Fit a Prophet model on a monthly series.

    Args:
        series: pandas Series with DatetimeIndex and values
        changepoint_prior_scale: Flexibility of trend changes (higher = more flexible)
        seasonality_mode: 'additive' or 'multiplicative'

    Returns:
        Fitted Prophet model
    """
    # Prophet expects a DataFrame with columns 'ds' and 'y'
    # df = pd.DataFrame({
    #     "ds": series.index,
    #     "y": series.values,
    # })
    #
    # model = Prophet(
    #     changepoint_prior_scale=changepoint_prior_scale,
    #     seasonality_mode=seasonality_mode,
    #     yearly_seasonality=yearly_seasonality,
    #     weekly_seasonality=weekly_seasonality,
    #     daily_seasonality=daily_seasonality,
    # )
    # model.fit(df)
    # return model
    raise NotImplementedError("Wire up Prophet")


def forecast_prophet(
    fitted_model,
    periods: int = 6,
    freq: str = "MS",
) -> pd.DataFrame:
    """
    Generate Prophet forecast.

    Returns:
        DataFrame with columns: ds, yhat, yhat_lower, yhat_upper
        where bounds represent the 80% credible interval by default.
    """
    # future = fitted_model.make_future_dataframe(periods=periods, freq=freq)
    # forecast = fitted_model.predict(future)
    # return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)
    raise NotImplementedError("Wire up Prophet forecast")
