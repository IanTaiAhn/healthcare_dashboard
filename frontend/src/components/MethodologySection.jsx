/**
 * Section 6: Methodology & Data Notes
 *
 * Collapsible section showing data sources, preprocessing decisions,
 * model details, and the Composite Stress Score methodology.
 * This is what separates a credible tool from a black box.
 */

import { useState } from "react";

const FRED_SERIES_USED = [
  { id: "UTEDUH", desc: "Utah Ed & Health Services Employment (Private, SA)", role: "Primary target" },
  { id: "SMU49000006562100001SA", desc: "Ambulatory Health Care Services in Utah (SA)", role: "Secondary target" },
  { id: "JTS6200QUR", desc: "Quit Rate: Healthcare & Social Assistance (SA)", role: "CSS input, feature" },
  { id: "JTS6200JOL", desc: "Job Openings Rate: Healthcare & Social Assistance (SA)", role: "CSS input, feature" },
  { id: "JTS6200HIL", desc: "Hires Level: Healthcare & Social Assistance (SA)", role: "Feature" },
  { id: "CES6500000003", desc: "Avg Hourly Earnings: Private Ed & Health Services", role: "CSS input, feature" },
  { id: "UTURN", desc: "Unemployment Rate in Utah", role: "Feature" },
  { id: "UTICLAIMS", desc: "Initial Claims in Utah", role: "Feature" },
  { id: "CPIAUCSL", desc: "Consumer Price Index (All Urban, SA)", role: "CPI adjustment" },
  { id: "ECIALLCIV", desc: "Employment Cost Index: Civilian Workers", role: "Feature" },
  { id: "UTNA", desc: "All Employees: Total Nonfarm in Utah (SA)", role: "Denominator" },
];

export default function MethodologySection({ metadata }) {
  const [open, setOpen] = useState(false);

  return (
    <section>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-lg font-semibold text-surface-900 hover:text-blue-700 transition-colors"
      >
        <span
          className="text-sm transition-transform"
          style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)" }}
        >
          ▶
        </span>
        Methodology & Data Notes
      </button>

      {open && (
        <div className="mt-4 space-y-6 text-sm text-surface-800/80 leading-relaxed">
          {/* Data Sources */}
          <div>
            <h3 className="font-semibold text-surface-900 mb-2">
              FRED Series Used
            </h3>
            <div className="bg-white rounded-lg border border-surface-200 overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-surface-50 border-b border-surface-200">
                    <th className="text-left px-3 py-2 font-medium">Series ID</th>
                    <th className="text-left px-3 py-2 font-medium">Description</th>
                    <th className="text-left px-3 py-2 font-medium">Role</th>
                  </tr>
                </thead>
                <tbody>
                  {FRED_SERIES_USED.map((s) => (
                    <tr key={s.id} className="border-b border-surface-100">
                      <td className="px-3 py-1.5 font-mono text-blue-700">
                        <a
                          href={`https://fred.stlouisfed.org/series/${s.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline"
                        >
                          {s.id}
                        </a>
                      </td>
                      <td className="px-3 py-1.5">{s.desc}</td>
                      <td className="px-3 py-1.5 text-surface-800/50">{s.role}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Preprocessing */}
          <div>
            <h3 className="font-semibold text-surface-900 mb-2">
              Preprocessing
            </h3>
            <p>
              All series are aligned to monthly frequency before feature engineering.
              Weekly series (UTICLAIMS, UTCCLAIMS) use the last observation of each month.
              Quarterly series (ECIALLCIV) are forward-filled to monthly.
              Stationarity is tested with the Augmented Dickey-Fuller test; non-stationary
              series are first-differenced (with log transform applied before differencing
              for level series to stabilize variance). All decisions are documented in{" "}
              <code className="bg-surface-100 px-1 rounded text-xs">
                preprocessing_config.yaml
              </code>.
            </p>
            <p className="mt-2">
              The COVID period (March 2020 – September 2021) is handled with a binary
              dummy variable rather than exclusion or interpolation.
            </p>
          </div>

          {/* Model */}
          <div>
            <h3 className="font-semibold text-surface-900 mb-2">
              Forecasting Model
            </h3>
            <p>
              The primary model is SARIMAX (Seasonal ARIMA with exogenous variables),
              selected via AIC/BIC grid search and validated with walk-forward backtesting
              on the 2022–2024 out-of-sample period. Exogenous variables include the
              JOLTS openings-to-unemployed ratio, healthcare quit rate (3-month MA),
              and a COVID shock dummy.
            </p>
            {metadata && (
              <div className="mt-2 bg-surface-50 rounded border border-surface-200 p-3 font-mono text-xs">
                <p>Model type: {metadata.model_type || "—"}</p>
                <p>Trained at: {metadata.trained_at || "not yet trained"}</p>
                <p>
                  6-month MAE: {metadata.out_of_sample_mae_6m ?? "—"} ·
                  Naive baseline MAE: {metadata.naive_baseline_mae_6m ?? "—"}
                </p>
                <p>
                  Beats baseline:{" "}
                  {metadata.beats_baseline ? "✓ Yes" : "✗ No / not evaluated"}
                </p>
              </div>
            )}
          </div>

          {/* CSS Methodology */}
          <div>
            <h3 className="font-semibold text-surface-900 mb-2">
              Composite Stress Score (CSS)
            </h3>
            <p>
              The headline signal is rules-based, not model-derived. Three inputs
              are each percentile-ranked against their 2010–2019 pre-pandemic
              baseline distribution:
            </p>
            <ol className="list-decimal list-inside mt-2 space-y-1">
              <li>Healthcare quit rate (JTS6200QUR)</li>
              <li>Healthcare job openings rate (JTS6200JOL)</li>
              <li>Healthcare/education wage growth YoY (CES6500000003)</li>
            </ol>
            <p className="mt-2">
              The three percentiles are averaged into a single score (0–100).
              Thresholds: ≥67 = Tightening (red), 33–66 = Stable (yellow),
              &lt;33 = Easing (green). The 3-month momentum indicator shows whether
              the CSS is rising, flat, or falling.
            </p>
          </div>

          {/* Limitations */}
          <div>
            <h3 className="font-semibold text-surface-900 mb-2">
              Key Limitations
            </h3>
            <p>
              JOLTS data is national — no Utah-specific quit rate or openings data
              exists. UTEDUH covers private sector only (excludes VA, state health
              departments, university health systems). The 6-month forecast horizon
              is ambitious; accuracy degrades meaningfully beyond 3 months. Confidence
              bands widen accordingly. Exogenous shocks (policy changes, pandemics)
              are not forecastable and will cause forecast errors.
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
