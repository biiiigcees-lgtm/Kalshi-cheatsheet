import { PriceTicker } from '@/components/PriceTicker'
import { Countdown }   from '@/components/Countdown'
import { Signal }      from '@/components/Signal'
import { BetsTable }   from '@/components/BetsTable'

export const dynamic = 'force-dynamic'

export default function Dashboard() {
  return (
    <div className="space-y-4 max-w-7xl mx-auto">

      {/* ── Top row: price · signal · countdown ─────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <PriceTicker />
        <Signal />
        <Countdown />
      </div>

      {/* ── Round info bar ───────────────────────────────────────────────── */}
      <div className="bb-panel px-4 py-3">
        <div className="bb-label mb-1">CURRENT ROUND STATS</div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
          <div>
            <div className="text-bb-muted">Market</div>
            <div className="text-bb-text font-semibold">KXBTC15M</div>
          </div>
          <div>
            <div className="text-bb-muted">Settlement</div>
            <div className="text-bb-text font-semibold">60-sec BRTI mean</div>
          </div>
          <div>
            <div className="text-bb-muted">Strategy</div>
            <div className="text-bb-yellow font-semibold">SAFE BET (≥85%)</div>
          </div>
          <div>
            <div className="text-bb-muted">Phase 1 gate</div>
            <div className="text-bb-green font-semibold">✓ PASSED (100%)</div>
          </div>
        </div>
      </div>

      {/* ── Recent bets ──────────────────────────────────────────────────── */}
      <div className="bb-panel p-4">
        <div className="bb-label mb-3">RECENT BETS</div>
        <BetsTable limit={10} />
      </div>

    </div>
  )
}
