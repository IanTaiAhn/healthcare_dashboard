# Utah Healthcare Workforce Intelligence Dashboard

Forward-looking labor market intelligence for Utah healthcare organizations. Combines FRED macroeconomic data with Utah-specific employment series, applies time series forecasting (SARIMAX), and presents output in a decision-oriented dashboard.

**Live demo:** _Not yet deployed — see setup instructions below to run locally._

---

## Prerequisites

You need three things installed:

- **Python 3.11+** — check with `python3 --version`
- **uv** — Python package manager. Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node.js 18+** — check with `node --version`. Install from [nodejs.org](https://nodejs.org/) or via `nvm`

You'll also want a **FRED API key** (free):
1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
2. Create an account and request a key
3. You'll paste it into your `.env` file below

---

## Quick Start (run everything locally)

### 1. Clone and enter the repo

```bash
git clone https://github.com/YOUR_USERNAME/utah-healthcare-workforce.git
cd utah-healthcare-workforce
```

### 2. Start the backend (FastAPI)

```bash
cd backend

# Create your environment file
cp .env.example .env
# Open .env and paste your FRED_API_KEY (or leave the placeholder — dummy data works without it)

# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Run the API server
uvicorn main:app --reload --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
[startup] Loading model artifacts...
```

**Verify it works** — open a new terminal:

```bash
curl http://localhost:8000/api/health
# → {"status":"ok","model_loaded":false}

curl http://localhost:8000/api/signal
# → {"composite_stress_score":68,"signal_state":"tightening",...}
```

All endpoints return dummy data by default, so the frontend works immediately without a FRED key or trained model.

### 3. Start the frontend (React + Vite)

Open a **second terminal**:

```bash
cd frontend

# Install Node dependencies
npm install

# Start the dev server
npm run dev
```

You should see:

```
  VITE v5.x.x  ready in Xms

  ➜  Local:   http://localhost:5173/
```

**Open http://localhost:5173** in your browser. You should see the full dashboard with all six sections rendering from dummy data.

Vite proxies `/api` requests to `localhost:8000` automatically (configured in `vite.config.js`), so the frontend and backend talk to each other without any extra setup.

---

## Project Structure

```
utah-healthcare-workforce/
├── backend/                         # Python — FastAPI + forecasting pipeline
│   ├── pyproject.toml               # Dependencies (managed by uv)
│   ├── .env.example                 # Copy to .env, add your FRED key
│   ├── main.py                      # FastAPI app entry point
│   ├── api/routes/                  # REST endpoints
│   │   ├── forecast.py              # /api/forecast/employment, /quit-rate
│   │   ├── indicators.py            # /api/indicators/leading, /wages
│   │   └── signal.py                # /api/signal (Composite Stress Score)
│   ├── data/                        # Data ingestion, validation, storage
│   │   ├── ingestion.py             # FRED API client + dummy data generator
│   │   ├── validation.py            # Quality checks (nulls, staleness, outliers)
│   │   └── storage.py               # SQLite with revision tracking
│   ├── features/                    # Preprocessing + feature engineering
│   │   ├── preprocessing_config.yaml  # THE config file — series registry
│   │   ├── preprocessing.py         # Frequency alignment, log/diff transforms
│   │   └── engineering.py           # Derived features, lags, CSS calculation
│   ├── models/                      # Forecasting models
│   │   ├── baseline.py              # Naive seasonal (fully implemented)
│   │   ├── sarimax_model.py         # SARIMAX wrapper (stubbed)
│   │   ├── prophet_model.py         # Prophet wrapper (stubbed)
│   │   ├── evaluate.py              # Walk-forward backtesting framework
│   │   ├── registry.py              # Model promotion/rollback logic
│   │   └── artifacts/               # Serialized models + metadata
│   └── scheduler/jobs.py            # Daily data refresh + monthly retrain
│
├── frontend/                        # React + Vite + Tailwind
│   ├── package.json
│   ├── vite.config.js               # Dev proxy to backend
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx                  # Dashboard layout (all 6 sections)
│       ├── api/client.js            # Axios instance
│       ├── hooks/useDashboardData.js  # Fetches all endpoints on mount
│       └── components/
│           ├── HeadlineSignal.jsx        # Section 1: CSS score
│           ├── LeadingIndicatorsPanel.jsx # Section 2: JOLTS sparklines
│           ├── WagePressurePanel.jsx      # Section 3: Wage charts
│           ├── EmploymentTrendPanel.jsx   # Section 4: Forecast chart
│           ├── ForecastTable.jsx          # Section 5: 6-row table
│           └── MethodologySection.jsx     # Section 6: Transparency
│
├── notebooks/                       # Jupyter — run in order
│   ├── 01_data_exploration.ipynb
│   ├── 02_stationarity_analysis.ipynb
│   ├── 03_feature_validation.ipynb
│   ├── 04_model_comparison.ipynb
│   └── 05_backtesting_results.ipynb
│
└── .github/workflows/deploy.yml     # CI/CD: lint → test → deploy
```

---

## Running the Notebooks

The notebooks are meant to be run in order. They import from the backend modules, so you need the backend virtualenv active.

```bash
cd backend
source .venv/bin/activate
cd ../notebooks
jupyter notebook
```

Start with `01_data_exploration.ipynb`. It works with dummy data out of the box. Once you add your FRED API key, switch from `generate_dummy_series()` to `fetch_all_series()` in the first notebook.

---

## API Endpoints

All endpoints return JSON. In development, access at `http://localhost:8000`.

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Service health check |
| `GET /api/metadata` | Model version, training date, data freshness |
| `GET /api/signal` | Composite Stress Score — Tightening / Stable / Easing |
| `GET /api/forecast/employment` | 6-month Utah healthcare employment forecast |
| `GET /api/forecast/quit-rate` | 6-month healthcare quit rate forecast |
| `GET /api/indicators/leading` | JOLTS leading indicators with percentiles |
| `GET /api/indicators/wages` | Wage pressure — nominal, real, CPI |

---

## Development Workflow

### Backend: add a new FRED series

1. Add the series entry to `backend/features/preprocessing_config.yaml`
2. Run notebook 02 to get its ADF p-value and confirm differencing order
3. The preprocessing pipeline picks it up automatically — no code changes

### Backend: swap in real FRED data

1. Add your `FRED_API_KEY` to `backend/.env`
2. In `backend/data/ingestion.py`, uncomment the `from fredapi import Fred` line and the `return Fred(api_key=api_key)` line in `get_fred_client()`
3. In notebook 01, switch from `generate_dummy_series()` to `fetch_all_series()`

### Backend: wire up the SARIMAX model

1. Run notebooks 01–04 to select model order parameters
2. In `backend/models/sarimax_model.py`, uncomment the statsmodels imports and fill in the order from your grid search
3. In `backend/api/routes/forecast.py`, replace the `DUMMY_EMPLOYMENT_FORECAST` with a call to the model

### Frontend: iterate on a component

The frontend hot-reloads via Vite. Edit any `.jsx` file and the browser updates instantly. All components consume the same JSON shape from the API, so you can restyle without touching the backend.

---

## Building for Production

### Frontend

```bash
cd frontend
npm run build
# Output in frontend/dist/ — deploy to GitHub Pages, Netlify, or Vercel
```

To set the production API URL:

```bash
VITE_API_BASE_URL=https://your-app.onrender.com npm run build
```

### Backend

Deploy to Render by connecting your GitHub repo. Set these environment variables in Render's dashboard:

- `FRED_API_KEY` — your key
- `DATABASE_URL` — Render provides a PostgreSQL URL, or use SQLite for demos
- `CORS_ORIGINS` — your GitHub Pages URL (e.g., `https://yourname.github.io`)
- `ENV` — `production`

Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## Limitations

- **No FRED key = dummy data only.** The API serves realistic dummy responses without a key, but forecasts won't be real.
- **Model not trained by default.** Run the notebooks to train and promote a model. Until then, endpoints return placeholder forecasts.
- **JOLTS data is national.** No Utah-specific quit rate or job openings data exists on FRED. National healthcare JOLTS is used as a proxy.
- **Free tier Render spins down.** First request after inactivity takes 30-60 seconds.

---

## License

MIT

---

*Data sources: Federal Reserve Bank of St. Louis (FRED), Utah Department of Workforce Services (DWS)*
