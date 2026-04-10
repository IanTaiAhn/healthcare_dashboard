"""
Data validation layer.

Runs quality checks on raw FRED series before they enter preprocessing.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


@dataclass
class ValidationResult:
    series_id: str
    passed: bool
    warnings: list[str]
    errors: list[str]
    latest_date: str | None
    observation_count: int


def validate_series(series_id: str, data: pd.Series) -> ValidationResult:
    """
    Run all validation checks on a single series.

    Checks:
        1. Not empty
        2. No unexpected nulls beyond known gaps
        3. Latest observation is reasonably recent (within 90 days)
        4. No extreme outliers (IQR method, flagged but not removed)
    """
    warnings = []
    errors = []

    # Check 1: Empty
    if data is None or len(data) == 0:
        return ValidationResult(
            series_id=series_id,
            passed=False,
            warnings=[],
            errors=["Series is empty or None"],
            latest_date=None,
            observation_count=0,
        )

    # Check 2: Null values
    null_count = data.isna().sum()
    if null_count > 0:
        null_pct = null_count / len(data) * 100
        msg = f"{null_count} null values ({null_pct:.1f}%)"
        if null_pct > 5:
            errors.append(msg)
        else:
            warnings.append(msg)

    # Check 3: Staleness
    latest = data.dropna().index.max()
    days_stale = (datetime.now() - pd.Timestamp(latest)).days
    if days_stale > 90:
        warnings.append(
            f"Latest observation is {days_stale} days old ({latest.strftime('%Y-%m-%d')})"
        )

    # Check 4: Outliers (IQR method — flag, don't remove)
    clean = data.dropna()
    q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 3.0 * iqr, q3 + 3.0 * iqr
    outliers = clean[(clean < lower) | (clean > upper)]
    if len(outliers) > 0:
        # Check if outliers are in COVID period — expected, not a data issue
        covid_outliers = outliers[
            (outliers.index >= "2020-03-01") & (outliers.index <= "2021-09-01")
        ]
        non_covid_outliers = outliers.drop(covid_outliers.index, errors="ignore")
        if len(covid_outliers) > 0:
            warnings.append(
                f"{len(covid_outliers)} outlier(s) in COVID period (expected, not removed)"
            )
        if len(non_covid_outliers) > 0:
            warnings.append(
                f"{len(non_covid_outliers)} outlier(s) outside COVID period — review manually"
            )

    passed = len(errors) == 0
    return ValidationResult(
        series_id=series_id,
        passed=passed,
        warnings=warnings,
        errors=errors,
        latest_date=latest.strftime("%Y-%m-%d") if latest is not None else None,
        observation_count=len(data),
    )


def validate_all(series_dict: dict[str, pd.Series]) -> list[ValidationResult]:
    """Validate all series and return results."""
    results = []
    for sid, data in series_dict.items():
        result = validate_series(sid, data)
        status = "✓" if result.passed else "✗"
        print(f"  {status} {sid}: {result.observation_count} obs, {len(result.warnings)} warnings")
        results.append(result)
    return results
