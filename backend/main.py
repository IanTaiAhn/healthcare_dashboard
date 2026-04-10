"""
Utah Healthcare Workforce Intelligence Dashboard — API Entry Point

Serves forecast data, leading indicators, wage pressure signals,
and composite workforce stress scores to the React frontend.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import forecast, indicators, signal

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: load model artifacts into memory, initialize scheduler.
    Shutdown: gracefully stop scheduler.
    """
    # TODO: Load SARIMAX model from artifacts/sarimax_current.joblib
    # TODO: Load model_metadata.json
    # TODO: Start APScheduler for daily data refresh + monthly retrain
    print("[startup] Loading model artifacts...")
    app.state.model = None  # Placeholder — replace with joblib.load()
    app.state.metadata = {
        "model_type": "sarimax",
        "trained_at": None,
        "status": "not_trained",
    }
    yield
    # Shutdown
    print("[shutdown] Stopping scheduler...")
    # TODO: scheduler.shutdown()


app = FastAPI(
    title="Utah Healthcare Workforce Intelligence",
    description="Forward-looking labor market intelligence for Utah healthcare organizations.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── Routes ──────────────────────────────────────────────────────────────────
app.include_router(forecast.router, prefix="/api")
app.include_router(indicators.router, prefix="/api")
app.include_router(signal.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "model_loaded": app.state.model is not None}


@app.get("/api/metadata")
async def metadata():
    """Data freshness, model version, series update timestamps."""
    return app.state.metadata
