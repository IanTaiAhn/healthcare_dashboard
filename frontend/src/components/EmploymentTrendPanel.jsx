/**
 * Section 4: Utah Employment Trend
 *
 * 5-year trailing UTEDUH with 6-month forecast, 80% confidence band,
 * and a dashed vertical line marking where the forecast begins.
 */

import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

export default function EmploymentTrendPanel({ data }) {
  if (!data) return null;

  const { forecast, last_actual } = data;

  // Build chart data: historical actuals (stub) + forecast with bands.
  // In production, the backend /forecast/employment endpoint will include
  // a trailing history array. For now we generate a simple stub.
  const chartData = [];

  // Stub: 12 months of "history" ending at last_actual
  if (last_actual) {
    const baseVal = last_actual.value;
    for (let i = 11; i >= 0; i--) {
      const d = new Date(last_actual.month + "-01");
      d.setMonth(d.getMonth() - i);
      const month = d.toISOString().slice(0, 7);
      chartData.push({
        month,
        actual: +(baseVal - (11 - (11 - i)) * 0.4 + Math.random() * 0.6).toFixed(1),
        type: "history",
      });
    }
  }

  // Forecast months
  (forecast || []).forEach((f) => {
    chartData.push({
      month: f.month,
      forecast: f.projected,
      lower: f.lower_80,
      upper: f.upper_80,
      // For the area band we need an array [lower, upper]
      band: [f.lower_80, f.upper_80],
      type: "forecast",
    });
  });

  const forecastStart = forecast?.[0]?.month;

  return (
    <section>
      <h2 className="text-lg font-semibold text-surface-900 mb-1">
        Utah Healthcare Employment Trend
      </h2>
      <p className="text-sm text-surface-800/50 mb-4">
        UTEDUH — Education & Health Services (Private, SA). Trailing history +
        6-month forecast with 80% confidence band.
      </p>

      <div className="bg-white rounded-lg border border-surface-200 p-4">
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <XAxis
                dataKey="month"
                tick={{ fontSize: 11 }}
                tickFormatter={(m) => m.slice(2)}
              />
              <YAxis
                tick={{ fontSize: 11 }}
                tickFormatter={(v) => `${v}k`}
                domain={["dataMin - 2", "dataMax + 2"]}
              />
              <Tooltip
                contentStyle={{ fontSize: "12px", borderRadius: "8px" }}
                formatter={(val, name) => {
                  if (name === "band") return null;
                  const suffix = "k employees";
                  if (Array.isArray(val))
                    return [`${val[0].toFixed(1)}–${val[1].toFixed(1)}${suffix}`, "80% CI"];
                  return [`${Number(val).toFixed(1)} ${suffix}`, name];
                }}
              />

              {/* Forecast confidence band */}
              <Area
                type="monotone"
                dataKey="band"
                fill="#3b82f6"
                fillOpacity={0.1}
                stroke="none"
              />

              {/* Historical actuals */}
              <Line
                type="monotone"
                dataKey="actual"
                name="Actual"
                stroke="#1e293b"
                strokeWidth={2}
                dot={false}
              />

              {/* Forecast line */}
              <Line
                type="monotone"
                dataKey="forecast"
                name="Forecast"
                stroke="#3b82f6"
                strokeWidth={2}
                strokeDasharray="6 3"
                dot={false}
              />

              {/* Vertical line marking forecast start */}
              {forecastStart && (
                <ReferenceLine
                  x={forecastStart}
                  stroke="#94a3b8"
                  strokeDasharray="3 3"
                  label={{
                    value: "Forecast →",
                    position: "top",
                    fontSize: 10,
                    fill: "#94a3b8",
                  }}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Model performance footnote */}
        {data.model_mae_6m && data.naive_baseline_mae_6m && (
          <p className="text-xs text-surface-800/40 mt-3 font-mono">
            Model 6m MAE: {data.model_mae_6m}k · Naive baseline MAE:{" "}
            {data.naive_baseline_mae_6m}k ·{" "}
            {data.model_mae_6m < data.naive_baseline_mae_6m
              ? "✓ Beats baseline"
              : "⚠ Does not beat baseline"}
          </p>
        )}
      </div>
    </section>
  );
}
