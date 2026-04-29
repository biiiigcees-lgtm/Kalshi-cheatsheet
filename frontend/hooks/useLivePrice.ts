'use client'
import { useState, useEffect, useRef } from 'react'
import type { PriceData } from '@/types'

const POLL_MS = 3_000

// Binance public REST — no API key, no CORS issues from browsers
async function fetchBinancePrice(): Promise<{ price: number; changePct: number }> {
  const res = await fetch(
    'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT',
    { cache: 'no-store' }
  )
  if (!res.ok) throw new Error(`Binance ${res.status}`)
  const j = await res.json()
  return {
    price:     parseFloat(j.lastPrice),
    changePct: parseFloat(j.priceChangePercent),
  }
}

export function useLivePrice(): PriceData | null {
  const [data, setData] = useState<PriceData | null>(null)
  const prevPrice = useRef<number | null>(null)

  useEffect(() => {
    let mounted = true

    const tick = async () => {
      try {
        const { price, changePct } = await fetchBinancePrice()
        if (!mounted) return
        setData({
          price,
          change24h:    prevPrice.current !== null ? price - prevPrice.current : 0,
          changePct24h: changePct,
          lastUpdated:  new Date(),
        })
        prevPrice.current = price
      } catch {
        // silently retry on next tick
      }
    }

    tick()
    const id = setInterval(tick, POLL_MS)
    return () => { mounted = false; clearInterval(id) }
  }, [])

  return data
}
