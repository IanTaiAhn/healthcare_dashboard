"""
Model registry — promotion logic, version management, rollback.

Rules:
  1. New model must beat naive baseline on 6-month MAE
  2. New model must beat (or match) the currently deployed model
  3. If either condition fails, candidate is saved but NOT promoted
  4. Previous version always kept for one-step rollback
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

import joblib

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


def load_metadata() -> dict:
    meta_path = ARTIFACTS_DIR / "model_metadata.json"
    if meta_path.exists():
        with open(meta_path) as f:
            return json.load(f)
    return {}


def save_metadata(metadata: dict):
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACTS_DIR / "model_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)


def promote_model(
    candidate_model,
    candidate_mae_6m: float,
    naive_mae_6m: float,
    training_window: str,
    series_timestamps: dict[str, str],
) -> bool:
    """
    Attempt to promote a candidate model to production.

    Returns True if promoted, False if conditions not met.
    """
    metadata = load_metadata()
    current_mae = metadata.get("out_of_sample_mae_6m", float("inf"))

    # Check promotion conditions
    beats_baseline = candidate_mae_6m < naive_mae_6m
    beats_current = candidate_mae_6m <= current_mae

    if not beats_baseline:
        print(
            f"  ✗ Candidate MAE ({candidate_mae_6m:.2f}) does not beat "
            f"naive baseline ({naive_mae_6m:.2f}). Not promoted."
        )
        # Save as candidate for manual review
        joblib.dump(candidate_model, ARTIFACTS_DIR / "sarimax_candidate.joblib")
        return False

    if not beats_current:
        print(
            f"  ✗ Candidate MAE ({candidate_mae_6m:.2f}) does not beat "
            f"current model ({current_mae:.2f}). Not promoted."
        )
        joblib.dump(candidate_model, ARTIFACTS_DIR / "sarimax_candidate.joblib")
        return False

    # Promote: rotate current → previous, candidate → current
    current_path = ARTIFACTS_DIR / "sarimax_current.joblib"
    previous_path = ARTIFACTS_DIR / "sarimax_previous.joblib"

    if current_path.exists():
        shutil.copy2(current_path, previous_path)

    joblib.dump(candidate_model, current_path)

    # Update metadata
    new_metadata = {
        "model_type": "sarimax",
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "training_window": training_window,
        "out_of_sample_mae_6m": candidate_mae_6m,
        "naive_baseline_mae_6m": naive_mae_6m,
        "beats_baseline": True,
        "fred_series_last_updated": series_timestamps,
        "previous_mae_6m": current_mae if current_mae != float("inf") else None,
    }
    save_metadata(new_metadata)

    print(
        f"  ✓ Model promoted. MAE: {candidate_mae_6m:.2f} "
        f"(baseline: {naive_mae_6m:.2f}, previous: {current_mae:.2f})"
    )
    return True


def rollback() -> bool:
    """Roll back to the previous model version."""
    current_path = ARTIFACTS_DIR / "sarimax_current.joblib"
    previous_path = ARTIFACTS_DIR / "sarimax_previous.joblib"

    if not previous_path.exists():
        print("  ✗ No previous model to roll back to.")
        return False

    shutil.copy2(previous_path, current_path)
    print("  ✓ Rolled back to previous model.")
    return True


def load_production_model():
    """Load the current production model. Returns None if not found."""
    path = ARTIFACTS_DIR / "sarimax_current.joblib"
    if not path.exists():
        return None
    return joblib.load(path)
