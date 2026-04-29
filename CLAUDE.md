# BTC-Trustee-Quant-V3 — Build Plan

## Overview
A full-stack, real-time AI betting engine for Kalshi KXBTC15M (Bitcoin 15-minute)
prediction markets. Pulls live BTC price from Binance & Kraken WebSocket feeds,
computes the official 60-second BRTI settlement average, runs an AI signal engine,
and renders a Bloomberg-style Next.js dashboard.

---

## 1. Kalshi KXBTC15M Contracts & BRTI Settlement

Each KXBTC15M contract asks: *"Will Bitcoin's price at the end of the 15-minute
window be above the opening price?"* YES/NO shares are quoted 0–99¢ (= implied
probability). Settlement uses the **CME CF Bitcoin Real-Time Index (BRTI)**:
- BRTI is published **once per second**
- The official settlement value is the **arithmetic mean of the 60 BRTI seconds**
  immediately before expiration
- Our engine must track BRTI ticks and compute this 60-second mean as the
  resolution price

---

## 2. Real-Time Data Feeds

| Feed | URL | Use |
|---|---|---|
| Binance USDM Futures | `wss://fstream.binance.com` | Primary sub-50ms BTC feed |
| Kraken Spot | `wss://ws.kraken.com` | Secondary / cross-check |
| Coinbase REST | `https://api.coinbase.com/v2/prices/BTC-USD/spot` | Browser price polling |

### Binance Notes
- Combined streams, 24h connection lifetime
- Lowercase symbols, ping/pong every 3 min
- Maintain local orderbook: fetch REST snapshot → apply buffered WS diff updates
- Rate limit: 10 msg/sec on subscribe

### Kraken Notes
- Heartbeat every second when subscribed
- Subscribe to `ticker` + `trade` channels for `XBT/USD`
- Keep at least one active subscription (idle disconnects after ~60 s)

---

## 3. Backtest Engine (48h BRTI)

**Script:** `backtest/engine.py`

Steps per round:
1. Fetch last 192 resolved KXBTC15M markets from Kalshi (48 h × 4/h)
2. Reconstruct the 60-second BRTI average from CF Benchmarks / raw Coinbase trades
3. Run AI signal engine → BET_YES | BET_NO | HOLD
4. Compare signal to actual resolution (YES/NO)
5. Report: Total Rounds, Win Rate, HOLDs taken, Losses made

**Gate:** Win rate on bets placed must reach **≥ 85%** before Phase 2 goes live.

### Signal Logic
| Condition | Action |
|---|---|
| 60s avg YES price in 42–58 range | HOLD (neutral zone) |
| Volatility σ > 18 | HOLD (too choppy) |
| Confidence score < 0.60 | HOLD (insufficient edge) |
| YES > 60 with upward momentum | BET_YES |
| YES < 40 with downward momentum | BET_NO |

---

## 4. Backend Architecture

### Supabase (Postgres + Realtime)
Tables:
- **`bets`** — win/loss ledger
- **`diary`** — HOLD decisions with shadow prediction & confidence

Enable Row-Level Security. Use `auth.users` for multi-user support.
Use Supabase Realtime for live dashboard updates.

### Novu Notifications
Trigger "Secure Bet" push notification when high-confidence signal fires.
Register device tokens from the frontend; dispatch via `notifications/novu_client.py`.

---

## 5. Frontend: Next.js 15 + Tailwind CSS

**Theme:** Bloomberg Terminal — black bg, amber/orange primary data, green/red
P&L, monospace font (JetBrains Mono).

**Pages:**
| Route | Content |
|---|---|
| `/` | Live dashboard: BTC ticker, 15-min countdown, current signal, round stats, recent bets |
| `/history` | Full bet history table from Supabase |
| `/diary` | HOLD decision log (shadow predictions + confidence) |

**Deploy:** Vercel — root directory `frontend/`

---

## Project Structure
```
frontend/           ← Next.js 15 app (Vercel deployment)
  app/
  components/
  hooks/
  lib/
  types/
backtest/           ← Python 48-h backtest engine
feeds/              ← Binance & Kraken WebSocket feed handlers
supabase/           ← schema.sql
notifications/      ← Novu push notification client
```

---

## Environment Variables
| Variable | Where used | Description |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | frontend | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | frontend | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | server routes | Service role key (never exposed client-side) |
| `NOVU_API_KEY` | notifications/ | Novu API key |
| `KALSHI_API_KEY` | backtest/ | Optional Kalshi API key |

---

## Running

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backtest
pip install -r feeds/requirements.txt
python backtest/engine.py

# WebSocket feeds (runs in background)
python feeds/binance_ws.py &
python feeds/kraken_ws.py &
```
