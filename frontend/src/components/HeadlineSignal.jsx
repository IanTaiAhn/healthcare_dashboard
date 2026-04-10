/**
 * Section 1: Headline Workforce Stress Signal
 *
 * Shows the Composite Stress Score (0-100) with a directional
 * indicator (Tightening / Stable / Easing) and plain language narrative.
 */

const SIGNAL_STYLES = {
  tightening: {
    bg: "bg-red-50",
    border: "border-red-200",
    badge: "bg-red-600 text-white",
    text: "text-red-800",
    dot: "bg-red-500",
    label: "Tightening",
  },
  stable: {
    bg: "bg-yellow-50",
    border: "border-yellow-200",
    badge: "bg-yellow-600 text-white",
    text: "text-yellow-800",
    dot: "bg-yellow-500",
    label: "Stable",
  },
  easing: {
    bg: "bg-green-50",
    border: "border-green-200",
    badge: "bg-green-600 text-white",
    text: "text-green-800",
    dot: "bg-green-500",
    label: "Easing",
  },
};

const MOMENTUM_ARROWS = {
  rising: "↑",
  flat: "→",
  falling: "↓",
};

export default function HeadlineSignal({ data }) {
  if (!data) return null;

  const style = SIGNAL_STYLES[data.signal_state] || SIGNAL_STYLES.stable;
  const arrow = MOMENTUM_ARROWS[data.momentum?.direction] || "→";

  return (
    <section className={`rounded-xl border ${style.border} ${style.bg} p-6`}>
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold ${style.badge}`}
            >
              <span className={`w-2 h-2 rounded-full bg-white/80`} />
              {style.label}
            </span>
            <span className="text-sm font-mono text-surface-800/50">
              {arrow} {data.momentum?.direction}
            </span>
          </div>
          <p className={`mt-4 text-sm leading-relaxed ${style.text} max-w-3xl`}>
            {data.narrative}
          </p>
        </div>

        {/* Score circle */}
        <div className="flex-shrink-0 ml-6 text-center">
          <div
            className={`w-20 h-20 rounded-full border-4 ${style.border} flex items-center justify-center`}
          >
            <span className={`text-2xl font-bold ${style.text}`}>
              {data.composite_stress_score}
            </span>
          </div>
          <p className="text-xs text-surface-800/40 mt-1">CSS / 100</p>
        </div>
      </div>

      {/* Component breakdown */}
      <div className="mt-5 pt-4 border-t border-surface-200/50 flex gap-8">
        {Object.entries(data.components || {}).map(([key, value]) => (
          <div key={key} className="text-xs">
            <span className="text-surface-800/50">
              {key.replace(/_/g, " ")}
            </span>
            <span className={`ml-2 font-mono font-semibold ${style.text}`}>
              {value}th
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
