'use client'
import { useState, useEffect, useRef } from 'react'
import type { RoundState } from '@/types'

function getRoundOpenTime(): Date {
  const now  = new Date()
  const open = new Date(now)
  open.setMinutes(Math.floor(now.getMinutes() / 15) * 15, 0, 0)
  return open
}

function getNextRoundTime(): Date {
  const open = getRoundOpenTime()
  return new Date(open.getTime() + 15 * 60 * 1000)
}

/**
 * Tracks the current KXBTC15M round state and the rolling 60-second BRTI average.
 *
 * @param currentPrice  Current BTC price from useLivePrice
 */
export function useRound(currentPrice: number | null): RoundState {
  const [state, setState] = useState<RoundState>({
    openPrice:   null,
    brtiAvg:     null,
    secondsLeft: 0,
    roundIndex:  0,
  })

  // Accumulate the first-60s price samples for the current round
  const samples    = useRef<number[]>([])
  const lastOpen   = useRef<Date>(getRoundOpenTime())
  const capturedMs = useRef<number>(0)

  useEffect(() => {
    const tick = () => {
      const now          = new Date()
      const roundOpen    = getRoundOpenTime()
      const nextRound    = getNextRoundTime()
      const secondsLeft  = Math.max(0, Math.round((nextRound.getTime() - now.getTime()) / 1000))
      const roundIndex   = Math.floor(now.getHours() * 4 + now.getMinutes() / 15)

      // Detect round transition
      if (roundOpen > lastOpen.current) {
        lastOpen.current = roundOpen
        samples.current  = []
        capturedMs.current = 0
        setState(prev => ({ ...prev, openPrice: currentPrice, brtiAvg: null, secondsLeft, roundIndex }))
      } else {
        setState(prev => ({ ...prev, secondsLeft, roundIndex }))
      }

      // Collect BRTI samples for first 60 seconds of the round
      const msIntoRound = now.getTime() - roundOpen.getTime()
      if (msIntoRound <= 60_000 && currentPrice !== null) {
        // Only push a new sample if at least ~1s has passed since last one
        if (msIntoRound - capturedMs.current >= 900) {
          capturedMs.current = msIntoRound
          samples.current    = [...samples.current, currentPrice]
          const avg = samples.current.reduce((a, b) => a + b, 0) / samples.current.length
          setState(prev => ({ ...prev, brtiAvg: avg }))
        }
      }
    }

    tick()
    const id = setInterval(tick, 1_000)
    return () => clearInterval(id)
  }, [currentPrice])

  return state
}
