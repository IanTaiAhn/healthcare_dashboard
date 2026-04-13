"""
FRED API data ingestion layer.

Pulls all series defined in preprocessing_config.yaml, validates them,
and stores raw values in SQLite with revision tracking.
"""

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from fredapi import Fred  # Uncomment when FRED_API_KEY is configured
from dotenv import load_dotenv
load_dotenv()

CONFIG_PATH = Path(__file__).parent.parent / "features" / "preprocessing_config.yaml"


def load_series_config() -> list[dict]:
    """Load series definitions from preprocessing_config.yaml."""
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    return config["series"]


def get_fred_client():
    """Initialize FRED API client from environment variable."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key or api_key == "your_fred_api_key_here":
        raise EnvironmentError(
            "FRED_API_KEY not set. Copy .env.example to .env and add your key. "
            "Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    return Fred(api_key=api_key)
    # raise NotImplementedError("Uncomment fredapi import and return when ready")


def fetch_series(series_id: str, start_date: str = "2005-01-01") -> pd.Series:
    """
    Fetch a single FRED series.

    Args:
        series_id: FRED series identifier (e.g., 'UTEDUH')
        start_date: Earliest date to pull

    Returns:
        pandas Series indexed by date
    """
    fred = get_fred_client()
    return fred.get_series(series_id, observation_start=start_date)
    # raise NotImplementedError("Wire up FRED client")


def fetch_all_series() -> dict[str, pd.Series]:
    """
    Fetch every series listed in preprocessing_config.yaml.

    Returns:
        Dict mapping series_id → pandas Series
    """
    config = load_series_config()
    results = {}
    errors = []

    for entry in config:
        sid = entry["id"]
        try:
            results[sid] = fetch_series(sid)
            print(f"  ✓ {sid} — {len(results[sid])} observations")
        except Exception as e:
            errors.append((sid, str(e)))
            print(f"  ✗ {sid} — {e}")

    if errors:
        print(f"\n⚠ {len(errors)} series failed to fetch:")
        for sid, err in errors:
            print(f"  {sid}: {err}")

    return results


def generate_dummy_series() -> dict[str, pd.DataFrame]:
    """
    Generate dummy data for all configured series.
    Use this for frontend development before FRED key is configured.
    """
    import numpy as np

    config = load_series_config()
    rng = np.random.default_rng(42)
    dates = pd.date_range("2010-01-01", "2026-03-01", freq="MS")
    results = {}

    dummy_baselines = {
        "UTEDUH": (200, 260, 0.3),         # start, end, noise_pct
        "UTNA": (1200, 1790, 0.2),
        "UTURN": (5.5, 3.1, 0.15),
        "JTS6200QUR": (2.0, 2.7, 0.1),
        "JTS6200JOL": (4.5, 7.1, 0.12),
        "CES6500000003": (22, 32, 0.05),
        "CPIAUCSL": (218, 315, 0.02),
    }

    for entry in config:
        sid = entry["id"]
        start, end, noise = dummy_baselines.get(sid, (100, 120, 0.1))
        trend = np.linspace(start, end, len(dates))
        seasonal = np.sin(np.arange(len(dates)) * 2 * np.pi / 12) * (end - start) * 0.02
        noise_vals = rng.normal(0, abs(end - start) * noise, len(dates))
        values = trend + seasonal + noise_vals

        # COVID shock
        covid_mask = (dates >= "2020-03-01") & (dates <= "2020-09-01")
        if sid in ("UTEDUH", "UTNA"):
            values[covid_mask] *= 0.92
        elif sid == "UTURN":
            values[covid_mask] *= 2.5

        results[sid] = pd.DataFrame(
            {"date": dates, "value": values, "series_id": sid}
        )

    return results

## Code to test the dummy data generation
# if __name__ == "__main__":
#     # Quick test: generate dummy data
#     dummy = generate_dummy_series()
#     for sid, df in dummy.items():
#         print(f"{sid}: {len(df)} rows, range [{df['value'].min():.1f}, {df['value'].max():.1f}]")
if __name__ == "__main__":
    series = fetch_all_series()
    for sid, data in series.items():
        print(f"{sid}: {len(data)} observations, latest={data.index.max().strftime('%Y-%m')}")