import { DiaryTable } from '@/components/DiaryTable'

export const metadata = { title: 'Diary — BTC-Trustee Quant V3' }

export default function DiaryPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-4">

      {/* Header */}
      <div className="bb-panel p-4">
        <div className="flex items-center gap-3 mb-2">
          <div className="bb-label">SECRET DIARY</div>
          <span className="text-bb-dim text-xs border border-bb-border px-2 py-0.5 rounded">
            HOLD DECISIONS ONLY
          </span>
        </div>
        <p className="text-xs text-bb-muted">
          Every round the AI decided to HOLD is logged here with its shadow
          prediction, confidence score, and the reason it stepped back.
          This is how the engine avoids bad bets — transparency on every
          non-trade decision.
        </p>
      </div>

      {/* Explainer */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
        {[
          { icon: '◉', title: 'Neutral Zone',       desc: 'YES price 42–58¢ — market is uncertain, edge is zero.' },
          { icon: '⚡', title: 'High Volatility',    desc: 'σ > 18 on YES prices — chop drowns signal, skip round.' },
          { icon: '⚖', title: 'Low Confidence',     desc: 'Composite score < 0.60 — not enough conviction to risk capital.' },
        ].map(({ icon, title, desc }) => (
          <div key={title} className="bb-panel p-4">
            <div className="text-bb-amber text-lg mb-1">{icon} {title}</div>
            <div className="text-bb-muted">{desc}</div>
          </div>
        ))}
      </div>

      {/* Diary table */}
      <div className="bb-panel p-4">
        <div className="bb-label mb-3">HOLD LOG</div>
        <DiaryTable />
      </div>

    </div>
  )
}
