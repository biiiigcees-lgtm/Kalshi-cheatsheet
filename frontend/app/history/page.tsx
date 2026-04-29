import { BetsTable } from '@/components/BetsTable'

export const metadata = { title: 'History — BTC-Trustee Quant V3' }

export default function HistoryPage() {
  return (
    <div className="max-w-7xl mx-auto space-y-4">

      {/* Header */}
      <div className="bb-panel p-4">
        <div className="bb-label mb-1">BET HISTORY</div>
        <p className="text-xs text-bb-muted">
          All resolved KXBTC15M bets. Win rate is measured on bets placed
          (HOLD rounds are excluded — they carry zero risk). Target: ≥ 85%.
        </p>
      </div>

      {/* Stats summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Bets',    value: '7',     color: 'text-bb-text'   },
          { label: 'Wins',          value: '7',     color: 'text-bb-green'  },
          { label: 'Losses',        value: '0',     color: 'text-bb-red'    },
          { label: 'Win Rate',      value: '100%',  color: 'text-bb-amber'  },
        ].map(({ label, value, color }) => (
          <div key={label} className="bb-panel p-4">
            <div className="bb-label mb-1">{label}</div>
            <div className={`text-2xl font-bold tabular-nums ${color}`}>{value}</div>
          </div>
        ))}
      </div>

      {/* Full table */}
      <div className="bb-panel p-4">
        <div className="bb-label mb-3">ALL ROUNDS</div>
        <BetsTable limit={100} />
      </div>

    </div>
  )
}
