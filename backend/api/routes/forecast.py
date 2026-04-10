"""
Forecast endpoints — 6-month employment and quit rate projections.
"""

from fastapi import APIRouter, Request

router = APIRouter(tags=["forecast"])


# ── Dummy forecast data for frontend development ────────────────────────────
# Replace with real model inference once pipeline is wired up.

DUMMY_EMPLOYMENT_FORECAST = {
    "series_id": "UTEDUH",
    "series_label": "Utah Ed & Health Services Employment (Private, SA)",
    "unit": "thousands",
    "model": "sarimax",
    "forecast": [
        {"month": "2026-05", "projected": 259.1, "lower_80": 256.8, "upper_80": 261.4},
        {"month": "2026-06", "projected": 259.8, "lower_80": 257.0, "upper_80": 262.6},
        {"month": "2026-07", "projected": 260.4, "lower_80": 257.1, "upper_80": 263.7},
        {"month": "2026-08", "projected": 261.0, "lower_80": 257.2, "upper_80": 264.8},
        {"month": "2026-09", "projected": 261.5, "lower_80": 257.1, "upper_80": 265.9},
        {"month": "2026-10", "projected": 262.1, "lower_80": 257.0, "upper_80": 267.2},
    ],
    "last_actual": {"month": "2026-04", "value": 258.5},
    "naive_baseline_mae_6m": 4.1,
    "model_mae_6m": 3.2,
}

DUMMY_QUIT_RATE_FORECAST = {
    "series_id": "JTS6200QUR",
    "series_label": "Quit Rate: Healthcare & Social Assistance (SA)",
    "unit": "percent",
    "model": "sarimax",
    "forecast": [
        {"month": "2026-05", "projected": 2.8, "lower_80": 2.5, "upper_80": 3.1},
        {"month": "2026-06", "projected": 2.9, "lower_80": 2.5, "upper_80": 3.3},
        {"month": "2026-07", "projected": 2.9, "lower_80": 2.4, "upper_80": 3.4},
        {"month": "2026-08", "projected": 3.0, "lower_80": 2.4, "upper_80": 3.6},
        {"month": "2026-09", "projected": 3.0, "lower_80": 2.3, "upper_80": 3.7},
        {"month": "2026-10", "projected": 3.1, "lower_80": 2.3, "upper_80": 3.9},
    ],
    "last_actual": {"month": "2026-03", "value": 2.7},
}


@router.get("/forecast/employment")
async def forecast_employment(request: Request):
    """6-month Utah healthcare employment forecast with confidence bands."""
    # TODO: Replace with real inference from request.app.state.model
    return DUMMY_EMPLOYMENT_FORECAST


@router.get("/forecast/quit-rate")
async def forecast_quit_rate(request: Request):
    """6-month healthcare quit rate forecast with confidence bands."""
    # TODO: Replace with real inference
    return DUMMY_QUIT_RATE_FORECAST
