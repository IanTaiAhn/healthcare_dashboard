"""
Scheduled jobs — daily data refresh + monthly model retraining.

Jobs:
  1. Daily: Pull latest FRED data, validate, store
  2. Monthly (1st Monday): Retrain model, evaluate, conditionally promote
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def daily_data_refresh():
    """
    Pull latest FRED data for all configured series.

    Runs daily but most series only update monthly, so most runs
    will detect no new data. When new data arrives, it's validated
    and stored with a fresh timestamp for revision tracking.
    """
    logger.info(f"[{datetime.utcnow().isoformat()}] Starting daily data refresh...")

    # TODO: Wire up the full pipeline:
    # 1. ingestion.fetch_all_series()
    # 2. validation.validate_all(series)
    # 3. storage.store_series() for each that passes validation
    # 4. Log results

    logger.info("Daily refresh complete.")


def monthly_retrain():
    """
    Retrain SARIMAX model and conditionally promote.

    Steps:
      1. Load all series from SQLite
      2. Run preprocessing pipeline
      3. Build feature matrix
      4. Fit new SARIMAX model
      5. Run walk-forward evaluation
      6. Compare against naive baseline and current model
      7. Promote if both conditions met, otherwise save as candidate
    """
    logger.info(f"[{datetime.utcnow().isoformat()}] Starting monthly model retrain...")

    # TODO: Wire up:
    # 1. storage.load_series() for each configured series
    # 2. preprocessing.preprocess_all(raw_series)
    # 3. engineering.build_lag_features() + engineering.compute_derived_features()
    # 4. sarimax_model.fit_sarimax(endog, exog)
    # 5. evaluate.walk_forward_evaluation()
    # 6. baseline.compute_naive_mae()
    # 7. registry.promote_model() or save candidate

    logger.info("Monthly retrain complete.")


def setup_scheduler(app):
    """
    Initialize APScheduler with daily refresh and monthly retrain jobs.
    Call this from FastAPI lifespan startup.
    """
    # from apscheduler.schedulers.asyncio import AsyncIOScheduler
    #
    # scheduler = AsyncIOScheduler()
    #
    # # Daily at 6am UTC
    # scheduler.add_job(daily_data_refresh, "cron", hour=6, minute=0)
    #
    # # First Monday of each month at 6am UTC
    # scheduler.add_job(
    #     monthly_retrain,
    #     "cron",
    #     day="1st mon",
    #     hour=6,
    #     minute=0,
    # )
    #
    # scheduler.start()
    # app.state.scheduler = scheduler
    # logger.info("Scheduler started: daily refresh + monthly retrain")
    pass
