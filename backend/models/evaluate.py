"""
Model evaluation — walk-forward validation with expanding window.

Training window: 2010–2021 (initial)
Test window: 2022–2024 (out-of-sample)
Horizons evaluated: 1, 3, 6 months
Metrics: MAE, MAPE, coverage (80% and 95% CI)
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class EvaluationResult:
    model_name: str
    horizon: int
    mae: float
    mape: float
    coverage_80: float | None  # % of actuals within 80% CI
    coverage_95: float | None  # % of actuals within 95% CI
    n_windows: int


def compute_mae(actuals: np.ndarray, forecasts: np.ndarray) -> float:
    return float(np.mean(np.abs(actuals - forecasts)))


def compute_mape(actuals: np.ndarray, forecasts: np.ndarray) -> float:
    mask = actuals != 0
    if mask.sum() == 0:
        return float("inf")
    return float(np.mean(np.abs((actuals[mask] - forecasts[mask]) / actuals[mask])) * 100)


def compute_coverage(
    actuals: np.ndarray,
    lowers: np.ndarray,
    uppers: np.ndarray,
) -> float:
    """What fraction of actuals fall within [lower, upper]?"""
    within = (actuals >= lowers) & (actuals <= uppers)
    return float(within.mean())


def walk_forward_evaluation(
    series: pd.Series,
    model_fit_fn,
    model_forecast_fn,
    train_end: str = "2021-12-31",
    test_start: str = "2022-01-01",
    test_end: str = "2024-12-31",
    horizons: list[int] = [1, 3, 6],
    expanding: bool = True,
) -> list[EvaluationResult]:
    """
    Walk-forward backtesting with expanding window.

    Args:
        series: Full time series
        model_fit_fn: Callable(train_series) → fitted_model
        model_forecast_fn: Callable(fitted_model, horizon) → DataFrame with 'forecast' column
        train_end: End of initial training window
        test_start: Start of test period
        test_end: End of test period
        horizons: List of forecast horizons to evaluate
        expanding: If True, expand training window at each step

    Returns:
        List of EvaluationResult, one per horizon
    """
    test_dates = series[test_start:test_end].index
    results = []

    for horizon in horizons:
        actuals_list = []
        forecasts_list = []

        for i, test_date in enumerate(test_dates):
            if i + horizon > len(test_dates):
                break

            # Define training window
            if expanding:
                train = series[:test_date - pd.DateOffset(months=1)]
            else:
                train = series[train_end : test_date - pd.DateOffset(months=1)]

            if len(train) < 24:  # Need minimum history
                continue

            try:
                model = model_fit_fn(train)
                fc = model_forecast_fn(model, horizon)

                # The forecast for `horizon` steps ahead
                if len(fc) >= horizon:
                    forecast_value = fc.iloc[horizon - 1]["forecast"]
                    actual_value = series.iloc[
                        series.index.get_loc(test_date) + horizon - 1
                    ]
                    actuals_list.append(actual_value)
                    forecasts_list.append(forecast_value)
            except Exception as e:
                print(f"  Walk-forward step {i} failed for horizon {horizon}: {e}")
                continue

        if len(actuals_list) == 0:
            results.append(
                EvaluationResult(
                    model_name="unknown",
                    horizon=horizon,
                    mae=float("inf"),
                    mape=float("inf"),
                    coverage_80=None,
                    coverage_95=None,
                    n_windows=0,
                )
            )
            continue

        actuals_arr = np.array(actuals_list)
        forecasts_arr = np.array(forecasts_list)

        results.append(
            EvaluationResult(
                model_name="unknown",  # Caller should set this
                horizon=horizon,
                mae=compute_mae(actuals_arr, forecasts_arr),
                mape=compute_mape(actuals_arr, forecasts_arr),
                coverage_80=None,  # TODO: add CI tracking
                coverage_95=None,
                n_windows=len(actuals_list),
            )
        )

    return results


def format_comparison_table(
    results_by_model: dict[str, list[EvaluationResult]],
) -> pd.DataFrame:
    """
    Format evaluation results into a comparison table for notebooks.

    Returns DataFrame with columns: model, horizon, mae, mape, coverage_80, n_windows
    """
    rows = []
    for model_name, results in results_by_model.items():
        for r in results:
            rows.append({
                "model": model_name,
                "horizon": r.horizon,
                "mae": round(r.mae, 2),
                "mape": round(r.mape, 2),
                "coverage_80": round(r.coverage_80, 2) if r.coverage_80 else None,
                "n_windows": r.n_windows,
            })
    return pd.DataFrame(rows)
