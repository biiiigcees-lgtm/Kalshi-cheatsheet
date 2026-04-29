export type SignalAction = 'BET_YES' | 'BET_NO' | 'HOLD'

export interface SignalResult {
  action:         SignalAction
  confidence:     number        // 0–1
  reason:         string
  yesEstimate:    number        // estimated Kalshi YES price 0–100
  roundOpenPrice: number        // BTC price at round open (60s BRTI avg)
  currentPrice:   number
}

export interface PriceData {
  price:         number
  change24h:     number
  changePct24h:  number
  lastUpdated:   Date
}

export interface RoundState {
  openPrice:    number | null   // BTC price recorded at round open
  brtiAvg:      number | null   // 60-second arithmetic mean of BRTI samples
  secondsLeft:  number          // seconds until round closes
  roundIndex:   number          // which 15-min slot (0–95) today
}

export interface Bet {
  id:               string
  user_id:          string
  ticker:           string
  bet_type:         'YES' | 'NO'
  amount:           number
  outcome:          'WIN' | 'LOSS' | 'PENDING'
  payout:           number | null
  floor_strike:     number
  settlement_price: number | null
  created_at:       string
}

export interface DiaryEntry {
  id:                string
  user_id:           string
  ticker:            string
  decision:          'HOLD'
  shadow_prediction: 'YES' | 'NO'
  confidence:        number
  reason_text:       string
  created_at:        string
}
