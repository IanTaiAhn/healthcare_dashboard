"""
SARIMAX model — primary production forecasting model.

Wraps statsmodels SARIMAX with project-specific defaults,
order selection, and forecast output formatting.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

# from statsmodels.tsa.statespace.sarimax import SARIMAX  # Uncomment when ready


@dataclass
class ForecastResult:
    """Structured forecast output for API consumption."""

    series_id: str
    model_type: str
    forecast: list[dict]       # [{month, projected, lower_80, upper_80}, ...]
    last_actual_date: str
    last_actual_value: float
    mae_6m: float | None
    naive_mae_6m: float | None


def fit_sarimax(
    endog: pd.Series,
    exog: pd.DataFrame | None = None,
    order: tuple = (1, 1, 1),
    seasonal_order: tuple = (1, 1, 1, 12),
) -> object:
    """
    Fit a SARIMAX model.

    Args:
        endog: Target series (should be stationary or differenced per config)
        exog: Exogenous features DataFrame, aligned to endog index
        order: (p, d, q) — non-seasonal ARIMA order
        seasonal_order: (P, D, Q, s) — seasonal order, s=12 for monthly

    Returns:
        Fitted SARIMAX results object
    """
    # model = SARIMAX(
    #     endog,
    #     exog=exog,
    #     order=order,
    #     seasonal_order=seasonal_order,
    #     enforce_stationarity=False,
    #     enforce_invertibility=False,
    # )
    # return model.fit(disp=False)
    raise NotImplementedError("Wire up statsmodels SARIMAX")


def forecast_sarimax(
    fitted_model,
    steps: int = 6,
    exog_future: pd.DataFrame | None = None,
    alpha: float = 0.20,
) -> pd.DataFrame:
    """
    Generate forecast with confidence intervals.

    Args:
        fitted_model: Result from fit_sarimax()
        steps: Number of months to forecast
        exog_future: Future exogenous values (must be provided if model uses exog)
        alpha: Significance level for CI (0.20 → 80% CI)

    Returns:
        DataFrame with columns: forecast, lower, upper
    """
    # forecast_obj = fitted_model.get_forecast(steps=steps, exog=exog_future, alpha=alpha)
    # return pd.DataFrame({
    #     "forecast": forecast_obj.predicted_mean,
    #     "lower": forecast_obj.conf_int().iloc[:, 0],
    #     "upper": forecast_obj.conf_int().iloc[:, 1],
    # })
    raise NotImplementedError("Wire up forecast generation")


def grid_search_order(
    endog: pd.Series,
    exog: pd.DataFrame | None = None,
    p_range: range = range(0, 3),
    d_range: range = range(0, 2),
    q_range: range = range(0, 3),
    seasonal_p_range: range = range(0, 2),
    seasonal_d_range: range = range(0, 2),
    seasonal_q_range: range = range(0, 2),
    s: int = 12,
) -> dict:
    """
    Grid search over SARIMAX orders using AIC.

    Returns dict with best_order, best_seasonal_order, best_aic.
    This runs in notebooks, not in production — results are hardcoded
    after selection.
    """
    # TODO: Implement grid search — this is a notebook-phase function
    raise NotImplementedError("Implement in notebook 04_model_comparison.ipynb")
