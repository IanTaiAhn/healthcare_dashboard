import { useDashboardData } from "./hooks/useDashboardData";
import HeadlineSignal from "./components/HeadlineSignal";
import LeadingIndicatorsPanel from "./components/LeadingIndicatorsPanel";
import WagePressurePanel from "./components/WagePressurePanel";
import EmploymentTrendPanel from "./components/EmploymentTrendPanel";
import ForecastTable from "./components/ForecastTable";
import MethodologySection from "./components/MethodologySection";

export default function App() {
  const { signal, forecast, quitForecast, leading, wages, metadata, loading, error } =
    useDashboardData();

  return (
    <div className="min-h-screen bg-surface-50">
      {/* Header */}
      <header className="border-b border-surface-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-5">
          <div className="flex items-baseline justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-surface-900">
                Utah Healthcare Workforce Intelligence
              </h1>
              <p className="mt-1 text-sm text-surface-800/60">
                Forward-looking labor market signals for workforce planning
              </p>
            </div>
            {metadata && (
              <span className="text-xs font-mono text-surface-800/40">
                Model: {metadata.model_type || "—"} · Status:{" "}
                {metadata.status || "not_trained"}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Loading / Error states */}
        {loading && (
          <div className="text-center py-20 text-surface-800/50">
            <p className="text-lg">Loading dashboard data…</p>
            <p className="text-sm mt-2">
              If the backend is on Render free tier, this may take 30-60s on
              first load.
            </p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 font-medium">Failed to load data</p>
            <p className="text-red-700 text-sm mt-1">{error}</p>
            <p className="text-red-600 text-xs mt-2">
              Make sure the FastAPI backend is running on port 8000.
            </p>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* Section 1: Headline Signal */}
            <HeadlineSignal data={signal} />

            {/* Section 2: Leading Indicators */}
            <LeadingIndicatorsPanel data={leading} />

            {/* Section 3: Wage Pressure */}
            <WagePressurePanel data={wages} />

            {/* Section 4: Employment Trend + Forecast Chart */}
            <EmploymentTrendPanel data={forecast} />

            {/* Section 5: Forecast Summary Table */}
            <ForecastTable
              employmentForecast={forecast}
              quitForecast={quitForecast}
            />

            {/* Section 6: Methodology & Data Notes */}
            <MethodologySection metadata={metadata} />
          </>
        )}
      </main>

      <footer className="border-t border-surface-200 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 text-xs text-surface-800/40">
          Data sources: Federal Reserve Bank of St. Louis (FRED), Utah
          Department of Workforce Services. Not financial advice. Forecasts are
          model estimates with uncertainty — see methodology section.
        </div>
      </footer>
    </div>
  );
}
