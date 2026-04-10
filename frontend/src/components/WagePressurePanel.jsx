/**
 * Section 3: Wage Pressure Panel
 *
 * Shows trailing 24-month wage growth (nominal + real), CPI overlay,
 * and a forward projection callout.
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

export default function WagePressurePanel({ data }) {
  if (!data) return null;

  const { series, forecast: fc } = data;

  // Merge trailing data into a single array for the chart.
  // In production the backend will return aligned arrays — for now
  // we zip the dummy stub points.
  const nominal = series.nominal_wage_growth_yoy?.trailing || [];
  const real = series.real_wage_growth_yoy?.trailing || [];
  const cpi = series.cpi_yoy?.trailing || [];

  // Build merged chart data keyed by month
  const byMonth = {};
  nominal.forEach((d) => (byMonth[d.month] = { ...byMonth[d.month], month: d.month, nominal: d.value }));
  real.forEach((d) => (byMonth[d.month] = { ...byMonth[d.month], month: d.month, real: d.value }));
  cpi.forEach((d) => (byMonth[d.month] = { ...byMonth[d.month], month: d.month, cpi: d.value }));
  const chartData = Object.values(byMonth).sort((a, b) => a.month.localeCompare(b.month));

  const wageForecast = fc?.wage_growth_6m;

  return (
    <section>
      <h2 className="text-lg font-semibold text-surface-900 mb-1">
        Wage Pressure
      </h2>
      <p className="text-sm text-surface-800/50 mb-4">
        Average hourly earnings in healthcare/education — year-over-year % change,
        trailing 24 months.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Chart — spans 2 cols */}
        <div className="lg:col-span-2 bg-white rounded-lg border border-surface-200 p-4">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(m) => m.slice(2)} /* 2024-04 → 24-04 */
                />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => `${v}%`}
                  domain={["auto", "auto"]}
                />
                <Tooltip
                  contentStyle={{ fontSize: "12px", borderRadius: "8px" }}
                  formatter={(val) => [`${val.toFixed(1)}%`, ""]}
                />
                <Legend
                  iconType="plainline"
                  wrapperStyle={{ fontSize: "12px" }}
                />
                <ReferenceLine y={0} stroke="#cbd5e1" strokeDasharray="3 3" />
                <Line
                  type="monotone"
                  dataKey="nominal"
                  name="Nominal Wage Growth"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="real"
                  name="Real Wage Growth"
                  stroke="#16a34a"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="cpi"
                  name="CPI YoY"
                  stroke="#94a3b8"
                  strokeWidth={1}
                  strokeDasharray="4 4"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Summary cards */}
        <div className="space-y-4">
          <SummaryCard
            label="Nominal Wage Growth"
            value={series.nominal_wage_growth_yoy?.current_value}
            unit="% YoY"
            accent="text-blue-600"
          />
          <SummaryCard
            label="Real Wage Growth"
            value={series.real_wage_growth_yoy?.current_value}
            unit="% YoY (CPI-adj)"
            accent="text-green-600"
          />
          <SummaryCard
            label="CPI Inflation"
            value={series.cpi_yoy?.current_value}
            unit="% YoY"
            accent="text-surface-800/60"
          />
          {wageForecast && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-700 font-medium">
                6-Month Projection
              </p>
              <p className="text-sm text-blue-900 mt-1">
                Expect{" "}
                <span className="font-semibold">
                  {wageForecast.low}–{wageForecast.high}%
                </span>{" "}
                wage growth in clinical roles over the next 2 quarters.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function SummaryCard({ label, value, unit, accent }) {
  return (
    <div className="bg-white rounded-lg border border-surface-200 p-3">
      <p className="text-xs text-surface-800/50">{label}</p>
      <p className={`text-xl font-bold ${accent} mt-0.5`}>
        {value != null ? `${value}%` : "—"}
      </p>
      <p className="text-xs text-surface-800/40">{unit}</p>
    </div>
  );
}
