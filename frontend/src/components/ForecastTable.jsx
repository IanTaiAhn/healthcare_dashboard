/**
 * Section 5: Forecast Summary Table
 *
 * A clean 6-row table designed to be screenshot-friendly for
 * executives dropping it into a budget deck or staffing presentation.
 */

const SIGNAL_BADGE = {
  tightening: "bg-red-100 text-red-700",
  stable: "bg-yellow-100 text-yellow-700",
  easing: "bg-green-100 text-green-700",
};

function classifyMonth(projected, lower, upper) {
  // Simple heuristic for per-month signal based on spread width
  // In production, run the CSS calc per-month using forecasted values
  const spread = upper - lower;
  const ratio = spread / projected;
  if (ratio > 0.04) return "tightening";
  if (ratio > 0.025) return "stable";
  return "easing";
}

export default function ForecastTable({ employmentForecast, quitForecast }) {
  if (!employmentForecast?.forecast) return null;

  const empRows = employmentForecast.forecast;
  const quitRows = quitForecast?.forecast || [];

  // Zip employment + quit rate rows by index
  const rows = empRows.map((emp, i) => ({
    month: emp.month,
    projected: emp.projected,
    lower: emp.lower_80,
    upper: emp.upper_80,
    quitRate: quitRows[i]?.projected ?? null,
    signal: classifyMonth(emp.projected, emp.lower_80, emp.upper_80),
  }));

  return (
    <section>
      <h2 className="text-lg font-semibold text-surface-900 mb-1">
        Forecast Summary
      </h2>
      <p className="text-sm text-surface-800/50 mb-4">
        6-month forward projections — Utah healthcare employment + national
        quit rate. Values in thousands (employment) and percent (quit rate).
      </p>

      <div className="bg-white rounded-lg border border-surface-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-50 border-b border-surface-200">
              <th className="text-left px-4 py-3 font-medium text-surface-800/60">
                Month
              </th>
              <th className="text-right px-4 py-3 font-medium text-surface-800/60">
                Projected Employment
              </th>
              <th className="text-right px-4 py-3 font-medium text-surface-800/60">
                Lower (80%)
              </th>
              <th className="text-right px-4 py-3 font-medium text-surface-800/60">
                Upper (80%)
              </th>
              <th className="text-right px-4 py-3 font-medium text-surface-800/60">
                Quit Rate
              </th>
              <th className="text-center px-4 py-3 font-medium text-surface-800/60">
                Signal
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={row.month}
                className={i % 2 === 0 ? "bg-white" : "bg-surface-50/50"}
              >
                <td className="px-4 py-2.5 font-mono text-surface-800">
                  {formatMonth(row.month)}
                </td>
                <td className="px-4 py-2.5 text-right font-mono font-semibold text-surface-900">
                  {row.projected.toFixed(1)}k
                </td>
                <td className="px-4 py-2.5 text-right font-mono text-surface-800/50">
                  {row.lower.toFixed(1)}k
                </td>
                <td className="px-4 py-2.5 text-right font-mono text-surface-800/50">
                  {row.upper.toFixed(1)}k
                </td>
                <td className="px-4 py-2.5 text-right font-mono text-surface-800">
                  {row.quitRate != null ? `${row.quitRate.toFixed(1)}%` : "—"}
                </td>
                <td className="px-4 py-2.5 text-center">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-xs font-medium capitalize ${
                      SIGNAL_BADGE[row.signal] || SIGNAL_BADGE.stable
                    }`}
                  >
                    {row.signal}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-surface-800/40 mt-2 italic">
        Note: Values are model estimates with uncertainty. See methodology for
        model details and baseline comparison.
      </p>
    </section>
  );
}

function formatMonth(monthStr) {
  // "2026-05" → "May 2026"
  const [year, month] = monthStr.split("-");
  const names = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];
  return `${names[parseInt(month, 10) - 1]} ${year}`;
}
