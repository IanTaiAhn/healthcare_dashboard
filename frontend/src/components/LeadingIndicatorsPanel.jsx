/**
 * Section 2: Leading Indicators Panel
 *
 * Multi-panel view of JOLTS indicators over a 36-month trailing window.
 * Each indicator shows its current percentile vs. 2010-2019 baseline.
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

function IndicatorCard({ label, currentValue, percentile, unit, trailing }) {
  const percentileColor =
    percentile >= 67
      ? "text-red-600"
      : percentile >= 33
      ? "text-yellow-600"
      : "text-green-600";

  return (
    <div className="bg-white rounded-lg border border-surface-200 p-4">
      <div className="flex items-baseline justify-between mb-3">
        <h3 className="text-sm font-medium text-surface-800/70 truncate pr-2">
          {label}
        </h3>
        <span className={`text-xs font-mono font-semibold ${percentileColor}`}>
          {percentile}th pct
        </span>
      </div>

      <div className="flex items-baseline gap-2 mb-3">
        <span className="text-2xl font-bold text-surface-900">
          {currentValue}
        </span>
        <span className="text-xs text-surface-800/40">{unit}</span>
      </div>

      {/* Sparkline chart */}
      {trailing && trailing.length > 1 && (
        <div className="h-16">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trailing}>
              <Line
                type="monotone"
                dataKey="value"
                stroke="#64748b"
                strokeWidth={1.5}
                dot={false}
              />
              <Tooltip
                contentStyle={{
                  fontSize: "11px",
                  padding: "4px 8px",
                  borderRadius: "6px",
                }}
                formatter={(val) => [`${val}${unit === "percent" ? "%" : ""}`, ""]}
                labelFormatter={(label) => label}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default function LeadingIndicatorsPanel({ data }) {
  if (!data) return null;

  const indicators = data.indicators || {};

  return (
    <section>
      <h2 className="text-lg font-semibold text-surface-900 mb-1">
        Leading Indicators
      </h2>
      <p className="text-sm text-surface-800/50 mb-4">
        National JOLTS data — healthcare & social assistance. Percentiles vs.
        2010–2019 baseline.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(indicators).map(([key, ind]) => (
          <IndicatorCard
            key={key}
            label={ind.label}
            currentValue={ind.current_value}
            percentile={ind.current_percentile}
            unit={ind.unit}
            trailing={ind.trailing}
          />
        ))}
      </div>
    </section>
  );
}
