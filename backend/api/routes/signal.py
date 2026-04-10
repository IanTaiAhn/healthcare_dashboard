"""
Workforce Stress Signal endpoint — Composite Stress Score (CSS).

The CSS is rules-based, NOT model-derived:
  1. Quit rate percentile vs. 2010-2019 baseline
  2. Job openings rate percentile vs. 2010-2019 baseline
  3. Wage growth percentile vs. 2010-2019 baseline

Average of the three → CSS (0-100).
  CSS >= 67  → Tightening (red)
  33 <= CSS < 67 → Stable (yellow)
  CSS < 33  → Easing (green)
"""

from fastapi import APIRouter

router = APIRouter(tags=["signal"])

# ── Dummy signal for frontend development ───────────────────────────────────

DUMMY_SIGNAL = {
    "composite_stress_score": 68,
    "signal_state": "tightening",
    "signal_color": "red",
    "components": {
        "quit_rate_percentile": 62,
        "job_openings_percentile": 74,
        "wage_growth_percentile": 69,
    },
    "baseline_period": "2010-01 to 2019-12",
    "momentum": {
        "direction": "rising",
        "css_3m_ago": 61,
        "css_current": 68,
        "description": "CSS has risen 7 points over the trailing 3 months.",
    },
    "narrative": (
        "Utah healthcare labor conditions are currently Tightening "
        "(Stress Score: 68/100). Job openings in healthcare remain elevated "
        "relative to pre-2020 norms (74th percentile). Quit rates sit at the "
        "62nd percentile and wage growth is tracking at the 69th percentile. "
        "The stress score has been rising over the past 3 months, suggesting "
        "increasing pressure on clinical staffing costs."
    ),
    "thresholds": {
        "tightening": ">= 67",
        "stable": "33 to 66",
        "easing": "< 33",
    },
}


@router.get("/signal")
async def workforce_stress_signal():
    """Current workforce stress signal — Tightening / Stable / Easing."""
    return DUMMY_SIGNAL
