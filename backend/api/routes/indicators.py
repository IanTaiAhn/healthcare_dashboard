"""
Indicator endpoints — leading indicators panel and wage pressure data.
"""

from fastapi import APIRouter

router = APIRouter(tags=["indicators"])


# ── Dummy trailing data for frontend development ────────────────────────────

DUMMY_LEADING_INDICATORS = {
    "window_months": 36,
    "baseline_period": "2010-01 to 2019-12",
    "indicators": {
        "quit_rate": {
            "series_id": "JTS6200QUR",
            "label": "Healthcare Quit Rate (National)",
            "current_value": 2.7,
            "current_percentile": 62,
            "unit": "percent",
            "trailing": [
                {"month": "2023-05", "value": 2.5},
                {"month": "2023-06", "value": 2.6},
                # ... truncated — full 36 months populated by pipeline
                {"month": "2026-03", "value": 2.7},
            ],
        },
        "job_openings_rate": {
            "series_id": "JTS6200JOL",
            "label": "Healthcare Job Openings Rate (National)",
            "current_value": 7.1,
            "current_percentile": 74,
            "unit": "percent",
            "trailing": [
                {"month": "2023-05", "value": 6.8},
                {"month": "2026-03", "value": 7.1},
            ],
        },
        "hires_level": {
            "series_id": "JTS6200HIL",
            "label": "Healthcare Hires Level (National)",
            "current_value": 682,
            "current_percentile": 55,
            "unit": "thousands",
            "trailing": [
                {"month": "2023-05", "value": 670},
                {"month": "2026-03", "value": 682},
            ],
        },
        "ut_unemployment": {
            "series_id": "UTURN",
            "label": "Utah Unemployment Rate",
            "current_value": 3.1,
            "current_percentile": 38,
            "unit": "percent",
            "trailing": [
                {"month": "2023-05", "value": 2.6},
                {"month": "2026-03", "value": 3.1},
            ],
        },
    },
}

DUMMY_WAGE_DATA = {
    "window_months": 24,
    "series": {
        "nominal_wage_growth_yoy": {
            "series_id": "CES6500000003",
            "label": "Avg Hourly Earnings YoY % Change (Healthcare/Ed)",
            "current_value": 5.3,
            "trailing": [
                {"month": "2024-04", "value": 4.8},
                {"month": "2026-03", "value": 5.3},
            ],
        },
        "real_wage_growth_yoy": {
            "label": "Real Wage Growth (CPI-adjusted)",
            "current_value": 2.1,
            "trailing": [
                {"month": "2024-04", "value": 1.2},
                {"month": "2026-03", "value": 2.1},
            ],
        },
        "cpi_yoy": {
            "series_id": "CPIAUCSL",
            "label": "CPI YoY % Change",
            "current_value": 3.2,
            "trailing": [
                {"month": "2024-04", "value": 3.6},
                {"month": "2026-03", "value": 3.2},
            ],
        },
    },
    "forecast": {
        "wage_growth_6m": {
            "label": "Projected wage growth range (next 6 months)",
            "low": 4.8,
            "high": 6.2,
            "unit": "percent_yoy",
        },
    },
}


@router.get("/indicators/leading")
async def leading_indicators():
    """JOLTS-based leading indicators with percentile annotations."""
    return DUMMY_LEADING_INDICATORS


@router.get("/indicators/wages")
async def wage_pressure():
    """Wage pressure panel — nominal, real, CPI context, and forward forecast."""
    return DUMMY_WAGE_DATA
