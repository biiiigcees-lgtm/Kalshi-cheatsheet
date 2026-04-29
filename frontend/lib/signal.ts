import type { SignalResult } from '@/types'

// ── helpers ───────────────────────────────────────────────────────────────────

function stdDev(arr: number[]): number {
  if (arr.length < 2) return 0
  const mean = arr.reduce((a, b) => a + b, 0) / arr.length
  return Math.sqrt(arr.reduce((acc, v) => acc + (v - mean) ** 2, 0) / arr.length)
}

function linearSlope(arr: number[]): number {
  const n = arr.length
  if (n < 3) return 0
  const mx = (n - 1) / 2
  const my = arr.reduce((a, b) => a + b, 0) / n
  const num = arr.reduce((acc, y, i) => acc + (i - mx) * (y - my), 0)
  const den = arr.reduce((acc, _, i) => acc + (i - mx) ** 2, 0)
  return den !== 0 ? num / den : 0
}

// ── Signal thresholds (mirrors CLAUDE.md) ────────────────────────────────────
const NEUTRAL_LO       = 42
const NEUTRAL_HI       = 58
const VOLATILITY_LIMIT = 0.50   // σ of pct-returns (%)
const CONFIDENCE_MIN   = 0.60

/**
 * computeSignal — AI signal engine for the frontend.
 *
 * @param prices        Recent BTC price ticks (newest last). Min 3 required.
 * @param roundOpenPrice BTC price recorded at round open (= 60s BRTI average).
 */
export function computeSignal(prices: number[], roundOpenPrice: number): SignalResult {
  const currentPrice = prices.at(-1) ?? roundOpenPrice
  const base: Omit<SignalResult, 'action' | 'confidence' | 'reason'> = {
    yesEstimate: 50,
    roundOpenPrice,
    currentPrice,
  }

  if (prices.length < 3) {
    return { ...base, action: 'HOLD', confidence: 0, reason: 'insufficient_data' }
  }

  // ── Pct-change from round open ─────────────────────────────────────────────
  const pctChange = (currentPrice - roundOpenPrice) / roundOpenPrice * 100

  // ── Short-window volatility (returns over last 10 ticks) ──────────────────
  const window = prices.slice(-10)
  const returns = window.slice(1).map((p, i) => (p - window[i]) / window[i] * 100)
  const vol = stdDev(returns)

  if (vol > VOLATILITY_LIMIT) {
    return { ...base, action: 'HOLD', confidence: 0.3,
             reason: `high_vol_${vol.toFixed(2)}`, yesEstimate: 50 }
  }

  // ── Estimate YES contract price ────────────────────────────────────────────
  // Approximation: z-score of BTC move relative to realised vol → YES price
  const zScore   = vol > 0 ? pctChange / vol : 0
  const yesEst   = Math.max(2, Math.min(98, 50 + zScore * 12))
  base.yesEstimate = yesEst

  // ── Neutral zone ──────────────────────────────────────────────────────────
  if (yesEst >= NEUTRAL_LO && yesEst <= NEUTRAL_HI) {
    return { ...base, action: 'HOLD', confidence: 0.40, reason: 'neutral_zone' }
  }

  // ── Momentum (slope of last 10 prices, normalised as %/tick) ─────────────
  const slopePct = linearSlope(prices.slice(-10)) / roundOpenPrice * 100

  const bullish = yesEst > 50

  // Momentum must confirm direction
  if ((bullish && slopePct <= 0) || (!bullish && slopePct >= 0)) {
    return { ...base, action: 'HOLD', confidence: 0.45, reason: 'momentum_mismatch' }
  }

  // ── Confidence ────────────────────────────────────────────────────────────
  const distance = Math.abs(yesEst - 50)
  let conf = Math.min(0.95, distance / 50)
  conf = Math.min(0.95, conf + Math.abs(slopePct) / 2)   // momentum bonus
  conf = Math.max(0, conf * Math.max(0.5, 1 - vol / 2))  // vol penalty

  if (conf < CONFIDENCE_MIN) {
    return { ...base, action: 'HOLD', confidence: conf, reason: `low_conf_${conf.toFixed(2)}` }
  }

  return {
    ...base,
    action:     bullish ? 'BET_YES' : 'BET_NO',
    confidence: conf,
    reason:     `${bullish ? 'bullish' : 'bearish'}_y${yesEst.toFixed(0)}_m${slopePct.toFixed(3)}`,
  }
}
