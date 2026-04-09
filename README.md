# Utah Healthcare Workforce Intelligence Dashboard
## Design Document v0.1

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Target User](#2-target-user)
3. [Data Sources](#3-data-sources)
4. [Data Pipeline Architecture](#4-data-pipeline-architecture)
5. [Feature Engineering](#5-feature-engineering)
6. [Model Design](#6-model-design)
7. [Dashboard Sections](#7-dashboard-sections)
8. [Tech Stack & Deployment](#8-tech-stack--deployment)
9. [Project Structure](#9-project-structure)
10. [Limitations & Known Constraints](#10-limitations--known-constraints)
11. [Future Work](#11-future-work)

---

## 1. Problem Statement

Healthcare organizations in Utah — mid-size health systems, specialty clinic chains, outpatient surgery centers, and staffing agencies — make hiring, compensation, and capacity planning decisions largely without access to forward-looking labor market intelligence.

The Utah state government publishes workforce data through the **Health Workforce Information Center (HWIC)** and the **Department of Workforce Services (DWS)**, but these are retrospective reports, published infrequently, and not designed for operational decision-making. National tools like Lightcast and TalentNeuron exist but are expensive enterprise contracts inaccessible to mid-size organizations.

No open-source, publicly available, deployed tool currently exists that:
- Combines FRED macroeconomic data with Utah-specific labor series
- Applies time series forecasting to project workforce conditions 6 months forward
- Presents output in a decision-oriented dashboard designed for a non-technical healthcare operator

This project builds that tool.

### The Core Business Question

> *"Based on current and projected labor market conditions in Utah, should our organization be accelerating hiring now, holding steady, or preparing for wage pressure over the next 6 months?"*

---

## 2. Target User

### Primary: Healthcare HR Director / Workforce Planning Director
**Organization size:** 5–20 location health systems, specialty clinic chains, urgent care networks in Utah

**Decisions they make with this tool:**
- Whether to accelerate or slow hiring pace in the next quarter
- Whether to increase reliance on contract/travel staff vs. permanent hires
- How to frame compensation budget requests to the CFO
- When to launch retention initiatives proactively vs. reactively

**What they need from the dashboard:**
- A clear directional signal, not just raw numbers
- Regional specificity — Utah, not national averages
- A short time horizon (6 months) that maps to budget and staffing cycles
- Plain language interpretation of what the data means for their decisions

### Secondary: CFO / COO at a Mid-Size Utah Health System
**Decisions they make:**
- Annual labor budget allocation
- Capital planning informed by expected wage trajectory
- Whether to pursue agency contract renegotiations now vs. later

---

## 3. Data Sources

### 3.1 FRED API (Primary)

All series are pulled via the `fredapi` Python library using a FRED API key stored as an environment variable (`FRED_API_KEY`). **All series IDs below have been manually verified against the FRED website as of April 2026.**

#### Utah-Specific Series

| Series ID | Description | Frequency | Verified Status |
|-----------|-------------|-----------|-----------------|
| `UTNA` | All Employees: Total Nonfarm in Utah | Monthly | ✅ Active — SA version, prefer for modeling |
| `UTNAN` | All Employees: Total Nonfarm in Utah | Monthly | ✅ Active — NSA version, Dec 2025: 1,791.7k |
| `UTEDUH` | All Employees: Ed & Health Services (Private) in Utah | Monthly | ✅ **Active and current** — Dec 2025: 257.7k, SA |
| `UTEDUHN` | All Employees: Ed & Health Services in Utah | Monthly | ✅ Active — NSA version of UTEDUH |
| `SMU49000006562100001SA` | Ambulatory Health Care Services in Utah | Monthly | ✅ Active — Dec 2025: 87.7k, SA. Key subsector. |
| `SMS49000006562000001` | Health Care & Social Assistance in Utah | Monthly | ✅ Active — NSA subsector series |
| `UTURN` | Unemployment Rate in Utah | Monthly | ✅ Active — **correct ID is UTURN not UTUR** |
| `LBSSA49` | Labor Force Participation Rate for Utah | Monthly | ✅ Active, SA. NSA version: `LBSNSA49` |
| `UTICLAIMS` | Initial Claims in Utah | Weekly | ✅ Active — Utah-specific, use instead of national ICSA |
| `UTCCLAIMS` | Continued Claims in Utah | Weekly | ✅ Active — pairs with initial claims |
| `UTCEMPLOY` | Covered Employment in Utah | Weekly | ✅ Active — updated Jan 2026 |
| `UTPCEHLTHCARE` | PCE: Healthcare — Utah | Annual | ✅ Active — annual only, context use only |
| `SMU49000000500000003` | Avg Hourly Earnings: All Private — Utah | Monthly | ✅ Active — Utah-specific wage baseline |

#### National Healthcare Series (Leading Indicators)

| Series ID | Description | Frequency | Verified Status |
|-----------|-------------|-----------|-----------------|
| `CES6562000001` | All Employees: Healthcare & Social Assistance | Monthly | ✅ Active — Jan 2026, SA |
| `CES6562000101` | All Employees: Healthcare (excl. social assistance) | Monthly | ✅ Active, SA |
| `CES6562160001` | All Employees: Home Health Care Services | Monthly | ✅ Active, SA |
| `JTS6200JOL` | Job Openings Rate: Healthcare & Social Assistance (SA) | Monthly | ✅ Active — **corrected from original doc** |
| `JTS6200JOR` | Job Openings Level: Healthcare & Social Assistance (SA) | Monthly | ✅ Active — level in thousands |
| `JTS6200QUR` | Quit Rate: Healthcare & Social Assistance (SA) | Monthly | ✅ Active — **key stress indicator** |
| `JTS6200HIL` | Hires Level: Healthcare & Social Assistance (SA) | Monthly | ✅ Active |
| `CES6500000003` | Avg Hourly Earnings: Private Ed & Health Services | Monthly | ✅ Active — best available national wage proxy |
| `ECIALLCIV` | Employment Cost Index: Civilian Workers | Quarterly | ✅ Active |

> **⚠️ JOLTS ID Correction:** The original draft listed `JTS6200000000000000JOL` etc. — these IDs do not exist on FRED. The correct format is `JTS6200JOL`, `JTS6200QUR`, `JTS6200HIL`. The `JTS` prefix = seasonally adjusted; `JTU` prefix = not seasonally adjusted. Use SA (`JTS`) versions for modeling.

> **⚠️ Wage Series Correction:** `CES6562000003` listed in the original draft does not exist. The correct series for average hourly earnings in the healthcare/education supersector is `CES6500000003`.

#### Macro Context Series

| Series ID | Description | Frequency | Verified Status |
|-----------|-------------|-----------|-----------------|
| `UNRATE` | National Unemployment Rate | Monthly | ✅ Active |
| `CIVPART` | Labor Force Participation Rate (National) | Monthly | ✅ Active |
| `CPIAUCSL` | Consumer Price Index (All Urban, SA) | Monthly | ✅ Active |
| `FEDFUNDS` | Federal Funds Rate | Monthly | ✅ Active |
| `ICSA` | Initial Claims (National, SA) | Weekly | ✅ Active — keep as national context alongside `UTICLAIMS` |

### 3.2 Utah Department of Workforce Services (Secondary)

**URL:** `https://jobs.utah.gov/wi/`

The DWS publishes monthly employment situation press releases with Utah-specific sector breakdowns. Now that `UTEDUH` is confirmed active on FRED, DWS serves primarily as a cross-validation source rather than a data gap filler.

- Data format: PDF press releases + Utah Economic Data Viewer tool
- Update cadence: Monthly
- Integration approach: Manual cross-validation during EDA; automated scraping deferred to v2

### 3.3 UTEDUH Status — Correction to Original Draft

**The original draft incorrectly stated that `UTEDUH` was discontinued in March 2022. This was wrong.**

During series verification, `UTEDUH` was confirmed to be fully active and updating as of January 28, 2026 (latest value: December 2025 = 257.7 thousand employees, seasonally adjusted). The ratio imputation method described in the original draft is not needed and has been removed.

**Key clarifications on UTEDUH:**
- Full title: "All Employees: Education and Health Services: **Private** Education and Health Services in Utah" — covers private sector only, which is appropriate for this analysis
- SA version: `UTEDUH` — use for modeling
- NSA version: `UTEDUHN` — use for seasonal decomposition validation
- History goes back to January 1990

**New subseries discovered during verification:**
`SMU49000006562100001SA` — Ambulatory Health Care Services in Utah — covers clinics, physician offices, and outpatient services. This is arguably the most relevant subsector for the target user (mid-size outpatient health systems and clinic chains) and should be featured prominently in the dashboard.

---

## 4. Data Pipeline Architecture

### 4.1 Overview

```
FRED API ──────────────────────────────┐
                                       ▼
Utah DWS (supplemental) ──────► Raw Data Ingestion Layer
                                       │
                                       ▼
                              Data Validation & Quality Checks
                                       │
                                       ▼
                              Preprocessing & Feature Engineering
                                       │
                                       ▼
                              Model Inference (6-month forecast)
                                       │
                                       ▼
                              Processed Data Store (JSON / SQLite)
                                       │
                                       ▼
                              FastAPI Backend ◄──── React Frontend
```

### 4.2 Ingestion Layer

- **Library:** `fredapi` (Python)
- **Scheduling:** APScheduler or a simple cron job running on Render
- **Update frequency:** Daily check; most series update monthly so the pipeline re-fetches and diffs
- **Storage:** Raw series stored in SQLite with timestamps; each pull versioned so model retraining is reproducible
- **Error handling:** If FRED API is unavailable, serve cached data with a staleness warning in the dashboard

### 4.3 Data Validation Checks

Before any series enters the preprocessing pipeline:
- Check for unexpected nulls or gaps beyond known discontinuations
- Check that the latest observation date is within expected range (flag if stale)
- Check for outliers using IQR method — flag but do not auto-remove (COVID period must be handled explicitly, not treated as outlier noise)

### 4.4 COVID Period Treatment

The 2020–2021 COVID shock creates structural breaks in nearly every series in scope. Treatment options considered:

| Approach | Tradeoff |
|----------|----------|
| Exclude 2020 entirely | Loses information, may underfit post-COVID labor dynamics |
| Include with dummy variable | Preferred — add a binary `covid_shock` feature for 2020 Q1–Q3 |
| Interpolate over the gap | Distorts the actual shape of the recovery, avoid |

**Decision:** Include full history with a `covid_shock` dummy variable. This is standard in macro time series work and is defensible to explain to a non-technical user.

---

## 5. Feature Engineering

### 5.1 Mixed Frequency Alignment

Before any feature engineering, all series are aligned to a common monthly frequency. This is a required step given the mix of weekly, monthly, quarterly, and annual series in scope.

| Source Frequency | Alignment Method | Rationale |
|-----------------|------------------|-----------|
| Weekly (UTICLAIMS, UTCCLAIMS, UTCEMPLOY) | Last observation of the month | Consistent with how BLS handles claims in monthly context |
| Monthly | No change | Native frequency |
| Quarterly (ECIALLCIV) | Forward-fill | Carry last known value forward until next release |
| Annual (UTPCEHLTHCARE) | Forward-fill | Context use only, not a model input |

All alignment is done before feature engineering so every derived feature operates on a consistent monthly index. The alignment decisions are documented in `preprocessing_config.yaml`.

### 5.2 Stationarity Processing

Most employment and wage series are non-stationary (they trend upward over time). Before modeling:

1. **Augmented Dickey-Fuller (ADF) test** applied to each series
2. Series that fail the ADF test (non-stationary) are **first-differenced** — modeling the month-over-month change rather than the level
3. Series that remain non-stationary after first differencing are second-differenced
4. Log transformation applied to level series before differencing to stabilize variance

The stationarity decisions for each series are documented in `preprocessing_config.yaml` in the repo, making them transparent, reproducible, and editable without touching code.

**`preprocessing_config.yaml` schema:**

```yaml
series:
  - id: UTEDUH
    label: "Utah Ed & Health Services Employment"
    frequency: monthly
    seasonal_adjustment: SA
    log_transform: true          # Apply log before differencing to stabilize variance
    differencing: 1              # Number of differences to achieve stationarity (from ADF test)
    adf_pvalue: 0.031            # Recorded ADF p-value after differencing (populated during EDA)
    role: target                 # target | feature | context
    include_in_model: true

  - id: JTS6200QUR
    label: "Quit Rate: Healthcare & Social Assistance"
    frequency: monthly
    seasonal_adjustment: SA
    log_transform: false
    differencing: 0              # Already stationary as a rate
    adf_pvalue: 0.004
    role: feature
    include_in_model: true
    lag_months: [1, 2, 3]        # Lag windows to construct as features

  - id: ECIALLCIV
    label: "Employment Cost Index: Civilian"
    frequency: quarterly
    seasonal_adjustment: SA
    monthly_alignment: forward_fill
    log_transform: false
    differencing: 1
    adf_pvalue: null             # To be populated during EDA
    role: feature
    include_in_model: true
```

This file is populated during the EDA notebooks before any production code is written. The `adf_pvalue` fields are filled in from notebook output and committed to the repo, providing a permanent record of the stationarity analysis decisions.

### 5.3 Derived Features

Beyond the raw series, the following derived features will be constructed:

| Feature | Derivation | Rationale |
|---------|-----------|-----------|
| `healthcare_employment_share_ut` | Utah healthcare emp / Utah total nonfarm | How dependent Utah economy is on healthcare sector |
| `jolts_openings_to_unemployed_ratio` | Healthcare job openings / national unemployed | Market tightness ratio — classic Fed indicator |
| `quit_rate_3m_ma` | 3-month moving average of healthcare quit rate | Smooth out noise in monthly quit data |
| `wage_growth_yoy` | YoY % change in avg hourly earnings, healthcare | Annualized wage pressure signal |
| `real_wage_growth` | Wage growth minus CPI | Whether wages are keeping pace with inflation |
| `ut_employment_mom_change` | Month-over-month change in Utah total nonfarm | Short-term momentum signal |
| `labor_market_tightness_index` | Composite of quit rate + openings rate + hire rate | Summary of JOLTS pressure signals |
| `covid_shock` | Binary: 1 for March 2020 – September 2021 | Structural break control |

### 5.4 Lag Features

For forecasting 6 months forward, lag features are constructed for key series at 1, 3, and 6 month lags. The quit rate and job openings series historically lead employment and wage outcomes by 2–4 months, making them particularly valuable as lagged predictors.

### 5.5 Seasonal Decomposition

Healthcare employment has strong seasonal patterns (flu season, summer hiring cycles, year-end budget effects). STL decomposition (Seasonal-Trend decomposition using LOESS) is applied to extract:
- **Trend component** — for the forecast target
- **Seasonal component** — reattached to forecasts for interpretable output
- **Residual component** — for anomaly detection

---

## 6. Model Design

### 6.1 Forecast Target

The primary forecast target is: **Utah healthcare employment (monthly, 6-month horizon)**

`UTEDUH` (Utah Education & Health Services Employment, Private, SA) is the primary series, confirmed active and updating monthly through December 2025. No imputation is required.

Secondary forecast targets (each modeled independently):
- Healthcare quit rate (national, used as a Utah proxy) — `JTS6200QUR`
- Average hourly earnings in healthcare/education — `CES6500000003`
- Utah unemployment rate — `UTURN`

### 6.2 Model Candidates

Three models are implemented and compared. The goal is not to find the best theoretical model but to find the most defensible, interpretable model that outperforms a naive baseline.

#### Baseline: Naive Seasonal
Forecast = same month last year. This is surprisingly hard to beat for monthly employment series and serves as the floor all other models must clear.

#### Model 1: SARIMAX
Seasonal ARIMA with exogenous variables. The workhorse of monthly macro time series forecasting.

- Handles seasonality explicitly via the seasonal component
- Exogenous variables: `jolts_openings_to_unemployed_ratio`, `quit_rate_3m_ma`, `covid_shock`
- Order selection via AIC/BIC grid search over reasonable (p,d,q)(P,D,Q) ranges
- Produces native confidence intervals — important for the dashboard

**Why this is the likely winner:** interpretable, well-understood, produces calibrated uncertainty estimates, explainable to a healthcare operator.

#### Model 2: Facebook Prophet
Designed for business time series with strong seasonality and holiday effects.

- Handles the COVID structural break well via the changepoint detection mechanism
- Produces confidence intervals natively
- Less flexible for incorporating exogenous variables than SARIMAX but easier to tune

#### Model 3: VAR (Vector Autoregression) — Exploratory Only

Models multiple series jointly to capture lead-lag relationships between variables.

**Status: exploratory notebook only — not deployed to production API in v1.**

VAR is included in the comparison notebooks because it can theoretically capture the lagged relationship between national JOLTS signals and Utah employment outcomes. However, several practical constraints make it unsuitable as the primary production model:

- Requires all included series to be jointly stationary — with the mix of differenced and level series in this project, satisfying this constraint for 5+ series simultaneously is non-trivial
- Parameter count grows as O(k²p) where k = number of series and p = lag order — overfitting risk is real with monthly data going back to 2010
- The COVID structural break creates severe instability in VAR estimates unless handled carefully, requiring manual intervention that undermines automation
- Forecast intervals require bootstrap simulation rather than being analytically derived, adding computational overhead

If VAR outperforms SARIMAX meaningfully in the backtesting notebooks, it can be revisited for v2 with a more careful specification. For v1, SARIMAX is the deployed model and Prophet is the secondary comparison.

### 6.3 Model Evaluation

**Backtesting approach:** Walk-forward validation with an expanding window

- Training window: 2010–2021 (pre-COVID clean period as initial training set)
- Test window: 2022–2024 (post-COVID, out-of-sample)
- Forecast horizon evaluated: 1, 3, and 6 months

**Metrics:**
- **MAE** (Mean Absolute Error) — primary metric, interpretable in jobs units
- **MAPE** (Mean Absolute Percentage Error) — scale-independent comparison across series
- **Coverage** — do the 80% and 95% confidence intervals actually contain the true value at those rates?

**Decision rule:** The model with the best 6-month MAE on the 2022–2024 out-of-sample period is used in production. If no model beats naive seasonal at 6 months, the dashboard uses naive seasonal with honest caveats.

### 6.4 Model Serialization & Serving

Trained models are persisted to disk using `joblib` and loaded at API startup. Models are **never retrained on a live request** — inference always reads from the persisted artifact.

**Serialization approach:**

```
backend/models/artifacts/
├── sarimax_current.joblib       # Currently deployed model
├── sarimax_previous.joblib      # Previous version — kept for rollback
├── prophet_current.joblib       # Prophet comparison model
└── model_metadata.json          # Version, training date, MAE, naive baseline MAE
```

`model_metadata.json` structure:
```json
{
  "model_type": "sarimax",
  "trained_at": "2026-04-01T06:00:00Z",
  "training_window": "2010-01 to 2026-03",
  "out_of_sample_mae_6m": 3.2,
  "naive_baseline_mae_6m": 4.1,
  "beats_baseline": true,
  "fred_series_last_updated": {
    "UTEDUH": "2026-01-28",
    "JTS6200QUR": "2026-03-11"
  }
}
```

At FastAPI startup, the model artifact and metadata are loaded into memory once and held for the lifetime of the process. The `/api/metadata` endpoint serves the metadata directly so the frontend can display data freshness and model version to the user.

### 6.5 Retraining Schedule

- Model retrained monthly, triggered by APScheduler job on the first Monday of each month
- Before promotion to `sarimax_current.joblib`, the new model must beat both the naive baseline and the previous deployed model on 6-month MAE
- If either condition fails, the existing model is retained, the new artifact is saved as `sarimax_candidate.joblib` for manual review, and a warning is logged
- Previous version is always preserved as `sarimax_previous.joblib` to enable one-step rollback

---

## 7. Dashboard Sections

### Section 1: Headline — Workforce Stress Signal

**What it shows:**
A single directional indicator with three states: **Tightening**, **Stable**, **Easing**.

**How it is calculated — explicit definition:**

The signal is rules-based, derived from three inputs each expressed as a percentile rank relative to their 2010–2019 pre-pandemic baseline distribution:

1. **Quit rate percentile** — `JTS6200QUR` current value ranked against 2010–2019 monthly values
2. **Job openings rate percentile** — `JTS6200JOL` current value ranked against 2010–2019 monthly values
3. **Utah healthcare wage growth** — `UTEDUH`-implied wage pressure via `CES6500000003` YoY % change, ranked against 2010–2019 baseline

These three percentiles are averaged into a single **Composite Stress Score (CSS)** between 0 and 100.

| CSS Range | Signal State | Color | Interpretation |
|-----------|-------------|-------|----------------|
| CSS ≥ 67 | 🔴 Tightening | Red | Labor market is under significant stress vs. historical norms — accelerate retention efforts, review compensation |
| 33 ≤ CSS < 67 | 🟡 Stable | Yellow | Conditions are within historical norms — maintain current workforce strategy |
| CSS < 33 | 🟢 Easing | Green | Labor market is loosening — favorable hiring conditions, reduce contract labor reliance |

**Why rules-based rather than model-derived:**
The signal is deliberately rules-based rather than derived from the forecast model output. This makes it auditable, explainable to a non-technical user, and stable — it doesn't change every time the model is retrained. The forecast model informs the *direction* panel (is the CSS trending up or down?) but the current state determination uses the rules above.

**Directional annotation:**
Alongside the current state, a secondary indicator shows whether the CSS has been rising, flat, or falling over the trailing 3 months. This gives the user a sense of momentum without requiring them to read a chart.

**Plain language output example:**
> *"Utah healthcare labor conditions are currently Tightening (Stress Score: 74/100). Quit rates and job openings in healthcare remain elevated relative to pre-2020 norms. Wage growth is tracking at the 81st percentile of historical observations. Organizations should expect continued pressure on clinical staffing costs over the next two quarters."*

**Why this matters:** A busy HR Director needs a signal, not a spreadsheet. This is the first thing they see. The explicit definition also means any technically minded reviewer — a hiring manager, a peer reviewing your GitHub — can immediately understand and critique the methodology, which is a feature not a weakness.

---

### Section 2: Leading Indicators Panel

**What it shows:**
A multi-panel view of the key JOLTS indicators over a 36-month trailing window:
- Healthcare quit rate (national) with Utah unemployment overlay
- Healthcare job openings (national)
- Healthcare hire rate (national)
- Each panel annotated with its current percentile relative to 2010–2019 baseline

**Design note:** Percentile annotations ("Currently at 78th percentile vs. pre-pandemic norms") are more interpretable than raw values for a non-technical user.

---

### Section 3: Wage Pressure Panel

**What it shows:**
- Average hourly earnings in healthcare (YoY % change), trailing 24 months
- Real wage growth (adjusted for CPI)
- 6-month forward forecast with confidence band
- Comparison line: national CPI for context

**Business output:** "Based on current trajectory, expect 5–7% wage growth in clinical roles over the next 2 quarters, outpacing general inflation."

---

### Section 4: Utah Employment Trend

**What it shows:**
- Utah healthcare employment (`UTEDUH`), trailing 5 years
- Ambulatory care subsector (`SMU49000006562100001SA`) overlaid as a secondary line — more granular signal for outpatient-focused organizations
- Seasonal decomposition: trend vs. seasonal component
- 6-month forward forecast with 80% confidence band
- Annotation marking where the forecast begins (dashed vertical line)

**Note on transparency:** The chart distinguishes historical actuals from forecast values with a clear visual break. The ambulatory care overlay is labeled so users understand they are seeing two distinct series on the same chart.

---

### Section 5: Forecast Summary Table

**What it shows:**
A clean 6-row table — one row per forecast month — showing:

| Month | Projected Employment | Lower Bound (80%) | Upper Bound (80%) | Projected Quit Rate | Signal |
|-------|---------------------|-------------------|-------------------|---------------------|--------|
| May 2026 | 142,300 | 140,100 | 144,500 | 3.2% | 🟡 Stable |
| Jun 2026 | 143,100 | 140,500 | 145,700 | 3.3% | 🟡 Stable |
| ... | | | | | |

> *Note: Values above are illustrative examples only — not real forecasts.*

**Why a table:** Executives often want to screenshot something and drop it into a presentation or budget document. A clean table is more portable and actionable than a chart for that purpose.

---

### Section 6: Methodology & Data Notes

**What it shows:**
A collapsible section (not buried in a separate page) containing:
- List of FRED series used with verified series IDs and last update dates
- Description of the frequency alignment decisions (weekly → monthly aggregation)
- Description of the stationarity treatment applied to each series (references `preprocessing_config.yaml`)
- Model selected, its order parameters, and out-of-sample MAE vs. naive baseline
- Composite Stress Score calculation methodology — inputs, baseline period, thresholds
- Data freshness timestamp for each series

**Why this matters:** This is what separates a credible analytical tool from a black box. A healthcare CFO or an analytically curious hiring manager will look for this. It also demonstrates your statistical maturity directly in the product.

---

## 8. Tech Stack & Deployment

### 8.1 Backend

| Component | Tool | Rationale |
|-----------|------|-----------|
| Package manager | `uv` | Fast, modern Python packaging |
| API framework | FastAPI | Async, fast, auto-generates OpenAPI docs |
| Data library | `fredapi`, `pandas`, `statsmodels` | FRED access, data manipulation, SARIMAX/VAR modeling |
| Forecasting | `statsmodels`, `prophet` | SARIMAX and Prophet modeling |
| Scheduling | `APScheduler` | In-process job scheduling for data refresh |
| Database | SQLite (dev), PostgreSQL (prod) | Lightweight for solo project, upgradeable |
| Hosting | Render (free tier to start) | Easy deploy from GitHub, supports background workers |

### 8.2 Frontend

| Component | Tool | Rationale |
|-----------|------|-----------|
| Framework | React (Vite) | Fast build, familiar to full stack devs |
| Charts | Recharts or Plotly.js | Both have good React support; Plotly better for financial-style charts with confidence bands |
| Styling | Tailwind CSS | Fast, consistent, professional-looking without a design system |
| Hosting | GitHub Pages | Free, auto-deploys from `gh-pages` branch on push |
| API calls | Axios or native fetch | Simple REST calls to FastAPI backend |

### 8.3 API Endpoints

```
GET /api/health                    — service health check
GET /api/series/{series_id}        — raw series data (trailing N months)
GET /api/indicators/leading        — processed leading indicators panel data
GET /api/indicators/wages          — wage pressure panel data
GET /api/forecast/employment       — 6-month employment forecast with bounds
GET /api/forecast/quit-rate        — 6-month quit rate forecast with bounds
GET /api/signal                    — current workforce stress signal (Tightening/Stable/Easing)
GET /api/metadata                  — data freshness, model version, series update timestamps
```

### 8.4 Environment Variables

`.env.example` — commit this file; never commit `.env`:

```bash
# FRED API
FRED_API_KEY=your_fred_api_key_here

# Database
DATABASE_URL=sqlite:///./data/workforce.db   # Local dev
# DATABASE_URL=postgresql://user:pass@host/db  # Production on Render

# App
ENV=development                              # development | production
PORT=8000

# Scheduling
MODEL_RETRAIN_CRON="0 6 1 * *"             # 6am on the 1st of each month

# CORS — comma-separated list of allowed frontend origins
# Dev: include localhost; prod: GitHub Pages URL only
CORS_ORIGINS=http://localhost:5173,https://yourusername.github.io
```

### 8.5 CORS Configuration

Because the React frontend is hosted on GitHub Pages and the FastAPI backend is on Render, cross-origin requests require explicit CORS configuration. Without this, the browser will block every API call from the frontend silently.

**FastAPI CORS setup in `main.py`:**

```python
from fastapi.middleware.cors import CORSMiddleware
import os

origins = os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Explicit list — never use ["*"] in production
    allow_credentials=False,      # No auth cookies needed for read-only public API
    allow_methods=["GET"],        # Read-only API — GET only
    allow_headers=["*"],
)
```

**Key points:**
- `CORS_ORIGINS` is set as an environment variable on Render — update it when the GitHub Pages URL is known
- Using `["*"]` for `allow_origins` works but is sloppy for a deployed API — explicit origins are better practice
- `allow_credentials=False` is correct here since there is no authentication in v1

### 8.6 Deployment Architecture

```
GitHub (main branch)
    │
    ├── Push to main ──► Render auto-deploys FastAPI backend
    │                         │
    │                    Background worker pulls FRED data daily
    │                    Model retrains monthly
    │
    └── Push to gh-pages ──► GitHub Pages serves React frontend
                                   │
                              React calls Render backend API
                              CORS configured on FastAPI
```

---

## 9. Project Structure

```
utah-healthcare-workforce/
│
├── backend/
│   ├── pyproject.toml              # uv-managed dependencies
│   ├── .env.example                # Template — copy to .env, never commit .env
│   ├── main.py                     # FastAPI app entry point
│   ├── api/
│   │   ├── routes/
│   │   │   ├── forecast.py
│   │   │   ├── indicators.py
│   │   │   └── signal.py
│   ├── data/
│   │   ├── ingestion.py            # FRED API pull logic
│   │   ├── validation.py           # Data quality checks
│   │   └── storage.py              # SQLite read/write with revision tracking
│   ├── features/
│   │   ├── preprocessing.py        # Frequency alignment, stationarity, differencing
│   │   ├── engineering.py          # Derived features, lag construction
│   │   └── preprocessing_config.yaml  # Per-series: log_transform, differencing, lags, ADF p-values
│   ├── models/
│   │   ├── sarimax_model.py
│   │   ├── prophet_model.py
│   │   ├── baseline.py             # Naive seasonal baseline
│   │   ├── evaluate.py             # Walk-forward validation, MAE/MAPE/coverage
│   │   ├── registry.py             # Model promotion logic, version management
│   │   └── artifacts/              # Serialized model files (gitignored except metadata)
│   │       ├── sarimax_current.joblib
│   │       ├── sarimax_previous.joblib
│   │       └── model_metadata.json
│   └── scheduler/
│       └── jobs.py                 # APScheduler: ingest, retrain, promote
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── HeadlineSignal.jsx      # CSS score + Tightening/Stable/Easing
│       │   ├── LeadingIndicatorsPanel.jsx
│       │   ├── WagePressurePanel.jsx
│       │   ├── EmploymentTrendPanel.jsx
│       │   ├── ForecastTable.jsx
│       │   └── MethodologySection.jsx
│       ├── hooks/
│       │   └── useForecastData.js
│       └── api/
│           └── client.js           # Axios instance with base URL from env var
│
├── notebooks/
│   ├── 01_data_exploration.ipynb       # Pull all series, check shapes and date ranges
│   ├── 02_stationarity_analysis.ipynb  # ADF tests, populate preprocessing_config.yaml
│   ├── 03_feature_validation.ipynb     # Correlation/lag analysis — do features actually predict target?
│   ├── 04_model_comparison.ipynb       # SARIMAX vs Prophet vs naive baseline
│   └── 05_backtesting_results.ipynb    # Walk-forward validation, MAE/MAPE, coverage plots
│
├── .github/
│   └── workflows/
│       └── deploy.yml              # CI/CD: backend to Render, frontend to GH Pages
│
├── .env.example                    # Root-level for documentation clarity
├── .gitignore                      # Must include: .env, *.joblib, data/*.db
└── README.md
```

---

## 10. Limitations & Known Constraints

### Data Limitations

- **No Utah-specific JOLTS data:** JOLTS quit rates, hire rates, and job openings are only available at the national level. National healthcare labor dynamics are used as proxies for Utah, which is a reasonable but imperfect assumption given Utah's faster-than-average population and employment growth. This is the single largest data gap remaining after series verification.

- **UTEDUH covers private sector only:** `UTEDUH` covers private education and health services employment in Utah. Government-employed healthcare workers (VA hospitals, state health departments, university health systems) are excluded. For most target users — mid-size private health systems and clinic chains — this is appropriate, but it should be disclosed.

- **Ambulatory subseries SA methodology:** `SMU49000006562100001SA` is seasonally adjusted by the St. Louis Fed using statsmodels X-13ARIMA-SEATS, not by the BLS directly. Occasionally when data updates are insufficient to trigger seasonal adjustment, the NSA values are substituted. The pipeline should check for this and flag it when it occurs.

- **Annual PCE healthcare data:** `UTPCEHLTHCARE` is annual, limiting its use as a real-time demand signal. Used for contextual annual trend analysis only.

- **Mixed frequency alignment:** Series in this project span weekly (UTICLAIMS, UTCCLAIMS, UTCEMPLOY), monthly (most series), and quarterly/annual (ECI, PCE) frequencies. All series are aligned to monthly frequency for modeling. Weekly series are aggregated to monthly using end-of-month observation. Quarterly ECI is forward-filled at monthly frequency. Annual PCE is used only for context, not as a model input.

- **Revision risk:** FRED series are subject to revision. The pipeline tracks and logs revisions by storing each pull with a timestamp rather than silently overwriting historical values. This enables detection of significant revisions that might affect model behavior.

### Model Limitations

- **Exogenous shocks are not forecastable:** As discussed in the project's analytical framing, the model captures the structural and cyclical components of Utah healthcare employment. Black swan events (pandemic, recession, sudden policy changes) are not predictable and will cause forecast errors. Confidence bands widen at the 6-month horizon to partially reflect this.

- **6-month horizon is ambitious:** Labor market forecasting accuracy degrades meaningfully beyond 3 months. The 6-month forecast is presented with explicit uncertainty bands and the methodology section communicates this to users honestly.

- **National series as Utah proxies:** Utah's labor market has historically outperformed national trends. A fixed adjustment factor is used to account for this, but the relationship may shift over time.

### Operational Limitations

- **Free tier hosting:** Render's free tier spins down after inactivity. For a production tool, a paid tier or alternative hosting is needed. For a portfolio demo, the spin-up delay is acceptable.

- **No authentication on v1:** The dashboard is public-facing with read-only data. No sensitive data is involved. Authentication is deferred to v2 if the tool evolves toward a multi-tenant product.

---

## 11. Future Work

The following are explicitly out of scope for v1 but worth noting as natural extensions:

- **County-level disaggregation:** Salt Lake vs. Utah vs. Washington County dynamics differ meaningfully. The BLS publishes county-level employment data that could be added as a regional selector.

- **Specialty-level forecasting:** Nursing, physician, allied health, and administrative roles have different supply/demand dynamics. Adding specialty filters would significantly increase the tool's usefulness for workforce planning.

- **Internal data integration:** A health system willing to share internal turnover and vacancy data could use it alongside FRED signals to produce a hybrid forecast combining macro leading indicators with their own operational data.

- **Alert system:** Email or Slack notifications when the workforce stress signal changes state (e.g., from Stable to Tightening), so users don't need to check the dashboard proactively.

- **Utah DWS automated ingestion:** Automating the DWS press release scraping to replace the current manual supplementation process.

- **Comparable state benchmarking:** Adding Idaho, Nevada, and Colorado as comparison states to help Utah health systems understand whether their labor market dynamics are Utah-specific or regional.

---

*Document version: 0.1 | Last updated: April 2026 | Author: [Your Name]*

*Data sources: Federal Reserve Bank of St. Louis (FRED), Utah Department of Workforce Services (DWS), Utah Health Workforce Information Center (HWIC)*

# Pretty good introspection done. I think I do want to sink some time into a ML backend, infrastructe, and frontend to figure out where I really want to head.