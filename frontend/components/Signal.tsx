'use client'
import { useLivePrice } from '@/hooks/useLivePrice'
import { useRound } from '@/hooks/useRound'
import { computeSignal } from '@/lib/signal'
import { useEffect, useRef, useState } from 'react'
import type { SignalResult } from '@/types'

const ACTION_STYLE = {
  BET_YES: { text: 'BET YES ▲', color: 'text-bb-green',  bg: 'bg-bb-green/10  border-bb-green/30' },
  BET_NO:  { text: 'BET NO ▼',  color: 'text-bb-red',    bg: 'bg-bb-red/10    border-bb-red/30'   },
  HOLD:    { text: 'HOLD  ■',   color: 'text-bb-yellow', bg: 'bg-bb-yellow/10 border-bb-yellow/30' },
}

export function Signal() {
  const priceData = useLivePrice()
  const round     = useRound(priceData?.price ?? null)
  const history   = useRef<number[]>([])
  const [sig, setSig] = useState<SignalResult | null>(null)

  useEffect(() => {
    if (priceData?.price == null) return
    history.current = [...history.current.slice(-49), priceData.price]

    const openPrice = round.brtiAvg ?? round.openPrice ?? priceData.price
    setSig(computeSignal(history.current, openPrice))
  }, [priceData?.price, round.brtiAvg, round.openPrice])

  if (!sig) {
    return (
      <div className="bb-panel p-4">
        <div className="bb-label mb-2">AI SIGNAL</div>
        <div className="text-bb-dim text-xl bb-cursor">ANALYSING</div>
      </div>
    )
  }

  const style = ACTION_STYLE[sig.action]

  return (
    <div className="bb-panel p-4">
      <div className="bb-label mb-2">AI SIGNAL  <span className="text-bb-dim">KXBTC15M</span></div>

      {/* Main signal pill */}
      <div className={`inline-block border px-4 py-1.5 rounded text-lg font-bold
        tracking-widest ${style.color} ${style.bg} mb-3`}>
        {style.text}
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
        <div className="text-bb-muted">Confidence</div>
        <div className={`font-semibold tabular-nums ${style.color}`}>
          {(sig.confidence * 100).toFixed(1)}%
        </div>

        <div className="text-bb-muted">YES estimate</div>
        <div className="text-bb-amber font-semibold tabular-nums">
          {sig.yesEstimate.toFixed(1)}¢
        </div>

        <div className="text-bb-muted">BRTI avg</div>
        <div className="text-bb-text tabular-nums">
          ${sig.roundOpenPrice.toLocaleString('en-US', { maximumFractionDigits: 0 })}
        </div>

        <div className="text-bb-muted">Reason</div>
        <div className="text-bb-dim truncate" title={sig.reason}>{sig.reason}</div>
      </div>
    </div>
  )
}
