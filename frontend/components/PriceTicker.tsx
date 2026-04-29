'use client'
import { useLivePrice } from '@/hooks/useLivePrice'

function fmt(n: number) {
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function PriceTicker() {
  const data = useLivePrice()

  if (!data) {
    return (
      <div className="bb-panel p-4">
        <div className="bb-label mb-2">BTC / USD</div>
        <div className="bb-num text-bb-dim bb-cursor">——————</div>
        <div className="text-xs text-bb-dim mt-1">connecting…</div>
      </div>
    )
  }

  const up     = data.changePct24h >= 0
  const clr    = up ? 'text-bb-green' : 'text-bb-red'
  const arrow  = up ? '▲' : '▼'
  const secAgo = Math.round((Date.now() - data.lastUpdated.getTime()) / 1000)

  return (
    <div className="bb-panel p-4">
      <div className="bb-label mb-2">BTC / USD  <span className="text-bb-dim">(BINANCE)</span></div>
      <div className="bb-num">${fmt(data.price)}</div>
      <div className={`text-sm font-semibold mt-1 ${clr}`}>
        {arrow} {up ? '+' : ''}{data.changePct24h.toFixed(2)}%
        <span className="text-bb-dim font-normal ml-2 text-xs">{secAgo}s ago</span>
      </div>
    </div>
  )
}
