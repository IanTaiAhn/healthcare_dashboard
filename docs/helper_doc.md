Start here: the config file that drives everything
Read first: backend/features/preprocessing_config.yaml
This is the spine of the entire project. Every FRED series used — its ID, frequency, whether to log-transform it, how many times to difference it, what role it plays (target, feature, context) — lives in this one file. Almost every other backend module reads from it. If you understand this file, you understand what data flows through the system and how it gets transformed.
The key fields per series are role (is this what we're predicting, or an input to the prediction?), differencing (how we make it stationary), and lag_months (how far back we look for predictive signal). The adf_pvalue fields are null right now — you fill them in by running notebook 02.
The backend, in the order data flows through it
Think of the backend as a pipeline. Data enters at the left and exits as API responses on the right:
FRED API → ingestion → validation → storage → preprocessing → engineering → model → API routes
Here's each step:
backend/data/ingestion.py — This is where data enters the system. It reads the YAML config to know which series to pull, then calls the FRED API for each one. Right now the fetch_series() function is stubbed out (you need a FRED API key), but generate_dummy_series() at the bottom creates realistic fake data shaped exactly like real FRED output. This is what the frontend develops against before you wire up the real API.
backend/data/validation.py — Every series passes through here before it's used. It checks four things: is the series empty, does it have unexpected nulls, is the latest observation suspiciously old (stale), and are there outliers. The outlier check uses the IQR method but specifically handles the COVID period — outliers during March 2020 through September 2021 are flagged as expected rather than treated as data problems. Nothing is auto-removed; everything is flagged for you to review.
backend/data/storage.py — SQLite storage with revision tracking. The important design choice here is that every time you pull data from FRED, it's stored with a fetched_at timestamp. FRED revises historical data sometimes — employment numbers from three months ago might get adjusted. By storing each pull separately rather than overwriting, you can detect when revisions happen and understand if they'd affect your model. load_series() always grabs the most recent pull for each date.
backend/features/preprocessing.py — This reads the YAML config and does two things: frequency alignment (turning weekly claims data and quarterly ECI into monthly) and stationarity transforms (log + differencing). The functions are generic — they look at each series' config entry and apply the right transforms. If you change the YAML, the pipeline behavior changes without touching code.
backend/features/engineering.py — Builds the derived features on top of the preprocessed series. Things like the healthcare employment share of Utah's economy (UTEDUH divided by total nonfarm), the quit rate smoothed over 3 months, real wage growth adjusted for CPI. The most important function here is compute_composite_stress_score() — this is the headline signal on the dashboard. It percentile-ranks three inputs against their 2010–2019 baseline and averages them into a single 0-100 score. The function also classifies into tightening/stable/easing based on threshold rules.
backend/models/ — Four files that form the modeling layer:

baseline.py — The naive seasonal model (forecast = same month last year). This is fully implemented and is the floor every other model must beat. Read this first among the model files because it's the simplest and the most important — if SARIMAX can't beat this, you ship this.
sarimax_model.py — Wrapper around statsmodels SARIMAX. The fit_sarimax(), forecast_sarimax(), and grid_search_order() functions are stubbed. You'll fill these in after running through notebooks 02-04 and selecting model parameters.
prophet_model.py — Same pattern, wrapped around Facebook Prophet. Serves as the comparison model.
evaluate.py — The backtesting framework. walk_forward_evaluation() does expanding-window walk-forward validation: train on data up to month T, forecast H months ahead, compare to actuals, slide forward, repeat. It computes MAE, MAPE, and confidence interval coverage. This is model-agnostic — you pass in any fit/forecast function pair and it evaluates it.
registry.py — Model promotion logic. When a new model is trained, promote_model() checks two conditions: does it beat the naive baseline, and does it beat the currently deployed model. If both pass, it rotates sarimax_current.joblib → sarimax_previous.joblib and saves the new one as current. If either fails, it saves the candidate for manual review but doesn't promote. rollback() does a one-step undo.

backend/models/artifacts/model_metadata.json — A JSON file that records what model is deployed, when it was trained, its MAE, and when each FRED series was last updated. The frontend reads this through the /api/metadata endpoint and displays it in the methodology section.
backend/main.py — The FastAPI entry point. The lifespan context manager loads the model artifact into memory at startup (so inference never hits disk on a live request). CORS is configured from an environment variable — this is critical because the React frontend on GitHub Pages and the API on Render are different origins. All routes are mounted under /api.
backend/api/routes/ — Three route files, each returning dummy data shaped exactly like the real pipeline output will look:

signal.py → GET /api/signal — Returns the CSS score, signal state, component breakdown, momentum direction, and a plain-language narrative paragraph.
forecast.py → GET /api/forecast/employment and /forecast/quit-rate — Returns 6-month forecasts with 80% confidence bounds.
indicators.py → GET /api/indicators/leading and /indicators/wages — Returns trailing JOLTS data with percentile annotations and wage growth with CPI overlay.

backend/scheduler/jobs.py — Two scheduled jobs: daily_data_refresh() pulls new FRED data (most series update monthly, so most daily runs find nothing new), and monthly_retrain() retrains the model on the first Monday of each month and attempts promotion through the registry.
The frontend, top to bottom
Read frontend/src/App.jsx first. It's the layout file — you can see all six dashboard sections in order, each mapping to a component. The useDashboardData hook fires on mount, calls all six API endpoints in parallel, and hands the results to each section.
frontend/src/hooks/useDashboardData.js — Single hook that makes all the API calls. Uses Promise.all so the dashboard loads in one batch rather than six sequential requests.
frontend/src/api/client.js — Axios instance. In development, Vite's proxy forwards /api calls to localhost:8000. In production, you set VITE_API_BASE_URL to your Render URL.
The six components in frontend/src/components/, in dashboard order:

HeadlineSignal.jsx — The big signal at the top. Takes the CSS score and renders a colored banner (red/yellow/green) with the narrative text and component breakdown. This is the first thing an HR director sees.
LeadingIndicatorsPanel.jsx — Four cards in a grid, each showing a JOLTS indicator with its current percentile and a sparkline chart. Uses Recharts LineChart for the sparklines.
WagePressurePanel.jsx — Dual-line chart (nominal vs. real wage growth) with CPI as a dashed reference line, plus summary cards and a 6-month projection callout.
EmploymentTrendPanel.jsx — The main forecast chart. Shows historical actuals as a solid line transitioning to a dashed forecast line with a shaded 80% confidence band. A vertical reference line marks where the forecast begins. Uses Recharts ComposedChart to layer the area (band) and lines.
ForecastTable.jsx — A clean 6-row HTML table designed to be screenshotted and dropped into a budget presentation. Month, projected employment, confidence bounds, quit rate, signal badge.
MethodologySection.jsx — Collapsible section with a table of every FRED series used (linking to FRED pages), descriptions of preprocessing, the model, the CSS methodology, and limitations. This is the credibility section.

frontend/tailwind.config.js — Defines custom colors for the signal states (tightening red, stable yellow, easing green) and the typography (DM Sans for body, JetBrains Mono for data).
The notebooks, in sequence
These are meant to be run in order, each producing artifacts the next one needs:

01_data_exploration — Pull all series, check shapes, plot everything, spot problems. Confirms the YAML config is correct.
02_stationarity_analysis — ADF tests on every series. The output of this notebook is the adf_pvalue values you write back into preprocessing_config.yaml. This is where the config file gets populated with real analysis results.
03_feature_validation — Correlation matrix and cross-correlation lag analysis. Answers the question: do the features we built actually predict the target? If the quit rate at lag 3 doesn't correlate with UTEDUH changes, there's no point putting it in the model.
04_model_comparison — Fits SARIMAX (with grid search over order parameters), Prophet, and naive baseline. Compares all three on the 2022–2024 out-of-sample period.
05_backtesting_results — Full walk-forward validation of the winning model. Produces the forecast-vs-actual plots and coverage analysis that go into the methodology section and README.

The CI/CD
.github/workflows/deploy.yml — On push to main: lint and test the Python backend, then build the React frontend and deploy it to GitHub Pages. Render picks up the backend deploy separately via its own GitHub integration.
Where to actually start working
The order I'd recommend:

Read preprocessing_config.yaml end to end
Get a FRED API key (free, takes 2 minutes)
Run notebook 01 with real FRED data to verify all series pull correctly
Run notebook 02 to fill in ADF p-values
Run notebook 03 to validate feature relationships
Uncomment the SARIMAX code in notebook 04, run the grid search, select parameters
Wire ingestion.py to real FRED (uncomment the fredapi lines)
Wire sarimax_model.py (uncomment statsmodels, plug in your selected order)
At that point the dummy data in the API routes gets replaced with real pipeline output, and the frontend just works