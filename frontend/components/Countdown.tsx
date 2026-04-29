'use client'
import { useRound } from '@/hooks/useRound'
import { useLivePrice } from '@/hooks/useLivePrice'

export function Countdown() {
  const price = useLivePrice()
  const round = useRound(price?.price ?? null)

  const m   = String(Math.floor(round.secondsLeft / 60)).padStart(2, '0')
  const s   = String(round.secondsLeft % 60).padStart(2, '0')
  const pct = (round.secondsLeft / (15 * 60)) * 100
  const urgent = round.secondsLeft < 60

  return (
    <div className="bb-panel p-4">
      <div className="bb-label mb-2">
        ROUND {round.roundIndex + 1}  <span className="text-bb-dim">OF 96 TODAY</span>
      </div>

      {/* Big timer */}
      <div className={`font-mono text-4xl font-bold tabular-nums tracking-tight
        ${urgent ? 'text-bb-red animate-pulse' : 'text-bb-amber'}`}>
        {m}:{s}
      </div>

      {/* Progress bar */}
      <div className="mt-3 h-1 w-full bg-bb-border rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-1000
            ${urgent ? 'bg-bb-red' : 'bg-bb-amber'}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="mt-2 text-xs text-bb-muted">
        {urgent ? 'SETTLING SOON' : 'UNTIL ROUND CLOSES'}
      </div>
    </div>
  )
}
