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

All series are pulled via the `fredapi` Python library using a FRED API key stored as an environment variable (`FRED_API_KEY`).

#### Utah-Specific Series

| Series ID | Description | Frequency | Notes |
|-----------|-------------|-----------|-------|
| `UTNAN` | All Employees: Total Nonfarm in Utah | Monthly | Baseline employment, SA, back to 1939 |
| `UTEDUH` | All Employees: Education & Health Services in Utah | Monthly | **Discontinued March 2022** — see data gap handling |
| `UTUR` | Unemployment Rate in Utah | Monthly | Key labor market slack indicator |
| `LBSSA49` | Labor Force Participation Rate for Utah | Monthly | Structural labor availability signal |
| `UTCEMPLOY` | Covered Employment in Utah | Weekly | High-frequency leading signal |
| `ICSA` | Initial Jobless Claims (National) | Weekly | National proxy for labor market direction |
| `UTPCEHLTHCARE` | Personal Consumption Expenditures: Healthcare — Utah | Annual | Demand-side context; low frequency |

#### National Healthcare Series (Used as Leading Indicators)

| Series ID | Description | Frequency | Notes |
|-----------|-------------|-----------|-------|
| `CES6562000001` | All Employees: Healthcare & Social Assistance | Monthly | Broad healthcare employment signal |
| `CES6562000101` | All Employees: Healthcare (excl. social assistance) | Monthly | Cleaner healthcare-specific signal |
| `CES6562160001` | All Employees: Home Health Care Services | Monthly | Fast-growing subsector, useful leading signal |
| `JTS6200000000000000JOL` | Job Openings: Healthcare & Social Assistance (JOLTS) | Monthly | Demand signal — unfilled positions |
| `JTS6200000000000000QUR` | Quit Rate: Healthcare & Social Assistance (JOLTS) | Monthly | **Key stress indicator** — high quits = tight market |
| `JTS6200000000000000HIR` | Hire Rate: Healthcare & Social Assistance (JOLTS) | Monthly | Supply/demand balance indicator |
| `CES6562000003` | Avg Hourly Earnings: Healthcare & Social Assistance | Monthly | Wage pressure — lagging but reliable |
| `ECIALLCIV` | Employment Cost Index: Civilian Workers | Quarterly | Broader compensation cost pressure |

#### Macro Context Series

| Series ID | Description | Frequency | Notes |
|-----------|-------------|-----------|-------|
| `UNRATE` | National Unemployment Rate | Monthly | Macro backdrop |
| `CIVPART` | Labor Force Participation Rate (National) | Monthly | Structural comparison to Utah |
| `CPIAUCSL` | Consumer Price Index (All Urban) | Monthly | Inflation context for real wage analysis |
| `FEDFUNDS` | Federal Funds Rate | Monthly | Affects health system borrowing costs |

### 3.2 Utah Department of Workforce Services (Secondary)

**URL:** `https://jobs.utah.gov/wi/`

The DWS publishes monthly employment situation press releases with Utah-specific healthcare employment figures. Since `UTEDUH` was discontinued in March 2022, this source fills the gap for recent Utah healthcare employment data.

- Data format: PDF press releases + the Utah Economic Data Viewer tool
- Update cadence: Monthly
- Integration approach: Manual supplementation initially; automated scraping considered for v2

### 3.3 Data Gap: UTEDUH Discontinuation

`UTEDUH` (Utah Education & Health Services Employment) stopped updating in April 2022. This is the most directly relevant Utah-specific series and its discontinuation is a significant constraint.

**Handling strategy:**
1. Use `UTEDUH` for the historical baseline (1990–2022)
2. Estimate post-2022 Utah healthcare employment using a **ratio method**: apply the Utah healthcare employment share (from the pre-2022 period) to total nonfarm `UTNAN` to extend the series
3. Cross-validate estimates against Utah DWS press release figures
4. Flag the imputed portion clearly in the dashboard with a methodology note

This limitation is worth documenting and even writing about — it's a real data engineering problem that demonstrates statistical maturity.

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

### 5.1 Stationarity Processing

Most employment and wage series are non-stationary (they trend upward over time). Before modeling:

1. **Augmented Dickey-Fuller (ADF) test** applied to each series
2. Series that fail the ADF test (non-stationary) are **first-differenced** — modeling the month-over-month change rather than the level
3. Series that remain non-stationary after first differencing are second-differenced
4. Log transformation applied to level series before differencing to stabilize variance

The stationarity decisions for each series will be documented in a `preprocessing_config.yaml` file in the repo, making them transparent and reproducible.

### 5.2 Derived Features

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

### 5.3 Lag Features

For forecasting 6 months forward, lag features are constructed for key series at 1, 3, and 6 month lags. The quit rate and job openings series historically lead employment and wage outcomes by 2–4 months, making them particularly valuable as lagged predictors.

### 5.4 Seasonal Decomposition

Healthcare employment has strong seasonal patterns (flu season, summer hiring cycles, year-end budget effects). STL decomposition (Seasonal-Trend decomposition using LOESS) is applied to extract:
- **Trend component** — for the forecast target
- **Seasonal component** — reattached to forecasts for interpretable output
- **Residual component** — for anomaly detection

---

## 6. Model Design

### 6.1 Forecast Target

The primary forecast target is: **Utah healthcare employment (monthly, 6-month horizon)**

Because `UTEDUH` is discontinued, the target series is the extended/imputed series described in Section 3.3, with uncertainty bounds that account for the imputation.

Secondary forecast targets (each modeled independently):
- Healthcare quit rate (national, used as a Utah proxy)
- Average hourly earnings in healthcare (national)
- Utah unemployment rate

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

#### Model 3: VAR (Vector Autoregression)
Models multiple series jointly to capture lead-lag relationships.

- Captures the relationship between national healthcare JOLTS series and Utah employment
- More complex to tune and explain but potentially more accurate if cross-series dynamics matter
- Forecast intervals derived via bootstrap

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

### 6.4 Retraining Schedule

- Model retrained monthly when new FRED data is published
- Retrained model is evaluated against the naive baseline before deployment
- If the new model is worse than the previous version, the previous version is retained and an alert is logged

---

## 7. Dashboard Sections

### Section 1: Headline — Workforce Stress Signal

**What it shows:**
A single directional indicator with three states: **Tightening**, **Stable**, **Easing**. Derived from the composite of quit rate, job openings rate, and wage growth, compared to historical norms for Utah.

**Plain language output example:**
> *"Utah healthcare labor conditions are currently tightening. Quit rates remain elevated above pre-2020 norms and job openings in healthcare have increased for the third consecutive month. Organizations should expect continued wage pressure and longer time-to-fill for clinical roles over the next 2–3 quarters."*

**Why this matters:** A busy HR Director needs a signal, not a spreadsheet. This is the first thing they see.

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
- Utah healthcare employment (extended series), trailing 5 years
- Seasonal decomposition: trend vs. seasonal component
- 6-month forward forecast with confidence band
- Annotation marking the UTEDUH data gap and imputation period

**Note on transparency:** The imputation boundary is visually marked with a dashed line and a tooltip explaining the methodology. This is a feature, not a bug — it demonstrates rigor.

---

### Section 5: Forecast Summary Table

**What it shows:**
A clean 6-row table — one row per forecast month — showing:

| Month | Projected Employment | Lower Bound (80%) | Upper Bound (80%) | Projected Quit Rate | Signal |
|-------|---------------------|-------------------|-------------------|---------------------|--------|
| May 2026 | 142,300 | 140,100 | 144,500 | 3.2% | 🟡 Stable |
| Jun 2026 | 143,100 | 140,500 | 145,700 | 3.3% | 🟡 Stable |
| ... | | | | | |

**Why a table:** Executives often want to screenshot something and put it in a presentation. A clean table is more useful than a chart for that purpose.

---

### Section 6: Methodology & Data Notes

**What it shows:**
A collapsible section (not buried in a separate page) containing:
- List of FRED series used with series IDs and last update dates
- Description of the stationarity treatment applied to each series
- Model selected and its out-of-sample performance vs. naive baseline
- Explanation of the UTEDUH data gap and imputation methodology
- Data freshness timestamp

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

```bash
FRED_API_KEY=your_fred_api_key_here
DATABASE_URL=sqlite:///./data/workforce.db   # or postgres URL in prod
ENV=development                              # or production
MODEL_RETRAIN_CRON="0 6 * * 1"             # Mondays at 6am
```

### 8.5 Deployment Architecture

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
│   ├── main.py                     # FastAPI app entry point
│   ├── api/
│   │   ├── routes/
│   │   │   ├── forecast.py
│   │   │   ├── indicators.py
│   │   │   └── signal.py
│   ├── data/
│   │   ├── ingestion.py            # FRED API pull logic
│   │   ├── validation.py           # Data quality checks
│   │   └── storage.py              # SQLite read/write
│   ├── features/
│   │   ├── preprocessing.py        # Stationarity, differencing, transforms
│   │   ├── engineering.py          # Derived features, lag construction
│   │   └── preprocessing_config.yaml  # Stationarity decisions per series
│   ├── models/
│   │   ├── sarimax_model.py
│   │   ├── prophet_model.py
│   │   ├── var_model.py
│   │   ├── baseline.py             # Naive seasonal baseline
│   │   ├── evaluate.py             # Walk-forward validation, MAE/MAPE
│   │   └── registry.py             # Model versioning, selection logic
│   └── scheduler/
│       └── jobs.py                 # APScheduler jobs: ingest, retrain
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── HeadlineSignal.jsx
│       │   ├── LeadingIndicatorsPanel.jsx
│       │   ├── WagePressurePanel.jsx
│       │   ├── EmploymentTrendPanel.jsx
│       │   ├── ForecastTable.jsx
│       │   └── MethodologySection.jsx
│       ├── hooks/
│       │   └── useForecastData.js
│       └── api/
│           └── client.js
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_stationarity_analysis.ipynb
│   ├── 03_model_comparison.ipynb
│   └── 04_backtesting_results.ipynb
│
├── .github/
│   └── workflows/
│       └── deploy.yml              # CI/CD: backend to Render, frontend to GH Pages
│
└── README.md
```

---

## 10. Limitations & Known Constraints

### Data Limitations

- **UTEDUH discontinued (2022):** The most directly relevant Utah healthcare employment series stopped updating. Post-2022 values are imputed using the ratio method described in Section 3.3. This introduces estimation uncertainty that is propagated into forecast confidence bands.

- **No Utah-specific JOLTS data:** JOLTS quit rates, hire rates, and job openings are only available at the national level. National healthcare labor dynamics are used as proxies for Utah, which is a reasonable but imperfect assumption given Utah's faster-than-average population and employment growth.

- **Annual PCE healthcare data:** The Utah healthcare consumption expenditure series is annual, limiting its use as a real-time demand signal. Used for contextual annual trend analysis only.

- **Revision risk:** FRED series are subject to revision. The pipeline should track and log revisions rather than silently overwriting historical values.

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