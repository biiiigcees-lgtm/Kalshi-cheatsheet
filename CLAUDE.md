# Kalshi KXBTC15M — AI Betting Cheatsheet Build Plan

## Overview
An AI-powered decision engine for Kalshi's KXBTC15M (Bitcoin 15-minute) prediction markets.
The system calculates the 60-second BRTI opening average for each round, applies signal
analysis to determine edge, and either places a directional bet (YES/NO) or HOLDs.

**Core principle:** Only bet when confidence is high. HOLD = no loss.

---

## Data Sources
- **Kalshi REST API** — `https://api.elections.kalshi.com/trade-api/v2`
  - `GET /markets?series_ticker=KXBTC15M&status=finalized` — historical rounds
  - `GET /markets/{ticker}/candlesticks` — YES/NO price history per round
- **CoinGecko API** — `https://api.coingecko.com/api/v3`
  - `GET /coins/bitcoin/market_chart/range` — BTC/USD price for BRTI proxy

---

## Phase 1: Backtest Engine ← CURRENT
**Goal:** Prove the logic works before touching any UI.

**Script:** `backtest_engine.py`

Steps per round:
1. Fetch last 100 resolved KXBTC15M markets from Kalshi
2. For each round, pull BTC price data to compute the 60-second BRTI average
3. Fetch Kalshi candlestick data (YES contract price history during the round)
4. Run AI signal engine → BET_YES | BET_NO | HOLD
5. Compare signal to actual resolution (YES/NO)
6. Report: Total Rounds, Win Rate, HOLDs taken, Losses made

**Gate:** Win rate on bets placed must reach **≥ 85%** before Phase 2 begins.

### Signal Logic
| Condition | Action |
|---|---|
| First-60s YES price in 42–58 range | HOLD (neutral zone) |
| Volatility (σ of YES prices) > 18 | HOLD (too choppy) |
| Confidence score < 0.60 | HOLD (insufficient edge) |
| YES > 60 with upward momentum | BET_YES |
| YES < 40 with downward momentum | BET_NO |

---

## Phase 2: Vercel / Next.js Dashboard
**Unlocks only when Phase 1 gate (≥ 85%) is met.**

- Real-time BRTI price feed
- Live signal dashboard (BET / HOLD indicator per round)
- Historical win-rate chart
- Next round countdown timer

---

## Key Files
| File | Purpose |
|---|---|
| `backtest_engine.py` | Phase 1 backtest script |
| `backtest_results.csv` | Raw round-by-round results |
| `main.py` | Existing FastAPI service (BTC price prediction) |
| `requirements.txt` | Python dependencies |

---

## Environment Variables
| Variable | Description |
|---|---|
| `KALSHI_API_KEY` | Optional Kalshi API key (public endpoints work without it) |

---

## Running Phase 1
```bash
pip install -r requirements.txt
python backtest_engine.py
```
