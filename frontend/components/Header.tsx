'use client'
import { useEffect, useState } from 'react'

export function Header() {
  const [utc, setUtc] = useState('')

  useEffect(() => {
    const fmt = () => setUtc(new Date().toUTCString().replace('GMT', 'UTC').split(' ').slice(0, 5).join(' '))
    fmt()
    const id = setInterval(fmt, 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="border-b border-bb-border px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <span className="text-bb-amber font-bold tracking-widest text-sm">
          BTC-TRUSTEE QUANT V3
        </span>
        <span className="text-bb-dim text-xs">KXBTC15M · AI SIGNAL ENGINE</span>
      </div>
      <div className="flex items-center gap-6 text-xs text-bb-muted">
        <span>{utc}</span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-bb-green animate-pulse inline-block" />
          LIVE
        </span>
      </div>
    </div>
  )
}
