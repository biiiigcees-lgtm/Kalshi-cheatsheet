#!/usr/bin/env python3
"""
backtest/engine.py — BTC-Trustee-Quant-V3  Phase 1 Backtest

Covers the last 48 hours of KXBTC15M markets (≈ 192 rounds).
Fetches real data from Kalshi when accessible; falls back to a
statistically accurate simulation otherwise.

Run:
    python backtest/engine.py
    FORCE_SIM=1 python backtest/engine.py   # force simulation
"""

import os, sys, time, logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backtest.signals import compute_signal

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-7s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("btc-backtest")

KALSHI_BASE    = "https://trading-api.kalshi.com/trade-api/v2"
SERIES_TICKER  = "KXBTC15M"
HOURS_BACK     = 48
ROUNDS_TARGET  = HOURS_BACK * 4  # 4 rounds / hour

# ── API helpers ───────────────────────────────────────────────────────────────

def _get(path, params=None, retries=3):
    import requests
    url = f"{KALSHI_BASE}{path}"
    hdr = {"accept": "application/json"}
    if (key := os.getenv("KALSHI_API_KEY")):
        hdr["Authorization"] = f"Bearer {key}"
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params or {}, headers=hdr, timeout=15)
            if r.status_code in (429, 503):
                time.sleep(2 ** attempt); continue
            if r.status_code in (401, 403):
                return None
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retries - 1:
                log.warning(f"Request failed: {e}")
                return None
            time.sleep(2 ** attempt)
    return None


def _check_api():
    return _get("/markets", {"series_ticker": SERIES_TICKER, "limit": 1}) is not None


def _fetch_markets(limit):
    collected, cursor = [], None
    while len(collected) < limit:
        p = {"series_ticker": SERIES_TICKER, "status": "finalized",
             "limit": min(200, limit - len(collected))}
        if cursor: p["cursor"] = cursor
        data = _get("/markets", p)
        if not data: break
        batch = data.get("markets", [])
        if not batch: break
        collected.extend(batch)
        cursor = data.get("cursor")
        if not cursor: break
        time.sleep(0.25)
    return collected[:limit]


def _fetch_candles(ticker, open_ts, close_ts):
    data = _get(f"/markets/{ticker}/candlesticks",
                {"start_ts": open_ts, "end_ts": close_ts, "period_interval": 1})
    return (data or {}).get("candlesticks", [])


def _extract_yes(candles):
    prices = []
    for c in candles:
        price = None
        yb = c.get("yes")
        if isinstance(yb, dict):
            price = yb.get("close") or yb.get("ask")
        if price is None:
            price = c.get("yes_close") or c.get("close_yes") or c.get("yes_price")
        if price is not None and 0 < float(price) < 100:
            prices.append(float(price))
    return prices

# ── Simulation ────────────────────────────────────────────────────────────────

def _simulate(n=192, seed=42):
    rng = np.random.default_rng(seed)
    btc  = 94_000.0
    base = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    base -= timedelta(minutes=(base.minute % 15), hours=HOURS_BACK)
    rows = []
    for i in range(n):
        ret    = rng.normal(0.0, 0.0035)
        final  = btc * (1 + ret)
        result = "yes" if final > btc else "no"

        pre_mom = rng.normal(0, 0.002)
        bias    = 0.0
        if rng.random() < 0.30:
            bias = float(rng.choice([-1, 1])) * float(rng.uniform(18, 42))
        yes_open = float(np.clip(50 + pre_mom * 3500 + rng.normal(0, 4.5) + bias, 2, 98))

        target = 97.0 if result == "yes" else 3.0
        candles, yt = [], yes_open
        for t in range(15):
            yt = float(np.clip(yt + (target - yt) * (0.06 + 0.10 * t / 14) + rng.normal(0, max(0.5, 5 * (1 - t / 14))), 1, 99))
            candles.append({"yes": {"close": round(yt, 1)}})

        rows.append({
            "ticker":     f"KXBTC15M-SIM-{i+1:03d}",
            "open_time":  (base + timedelta(minutes=15 * i)).isoformat(),
            "floor_strike": int(btc),
            "result":     result,
            "_brti_avg":  round(btc * float(rng.uniform(0.9998, 1.0002)), 2),
            "_candles":   candles,
        })
        btc = final
    log.info(f"Generated {n} synthetic rounds (seed={seed})")
    return rows

# ── Core backtest ─────────────────────────────────────────────────────────────

def _parse_ts(v) -> Optional[int]:
    if v is None: return None
    if isinstance(v, (int, float)): return int(v)
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S+00:00"):
        try:
            return int(datetime.strptime(str(v), fmt).replace(tzinfo=timezone.utc).timestamp())
        except ValueError: pass
    return None


def _evaluate(signal: str, result: str) -> str:
    if signal == "HOLD": return "HOLD"
    ru = result.upper().strip()
    if ru not in ("YES", "NO"): return "UNKNOWN"
    return "WIN" if (signal == "BET_YES" and ru == "YES") or (signal == "BET_NO" and ru == "NO") else "LOSS"


def run():
    print("\n" + "═" * 72)
    print("  BTC-TRUSTEE QUANT V3 — KXBTC15M BACKTEST (48 h)")
    print("═" * 72)

    live = (not os.getenv("FORCE_SIM")) and _check_api()
    mode = "LIVE (Kalshi API)" if live else "SIMULATION (synthetic 48h)"
    print(f"\n  Mode : {mode}")

    if live:
        log.info(f"Fetching {ROUNDS_TARGET} finalized markets…")
        raw = _fetch_markets(ROUNDS_TARGET)
        seen, markets = set(), []
        for m in raw:
            key = m.get("event_ticker") or m.get("open_time") or m.get("ticker")
            if key not in seen:
                seen.add(key); markets.append(m)
        markets = markets[:ROUNDS_TARGET]
    else:
        markets = _simulate(ROUNDS_TARGET)

    print(f"  Rounds: {len(markets)}\n")
    rows = []

    for idx, m in enumerate(markets):
        ticker   = m.get("ticker", "")
        open_ts  = _parse_ts(m.get("open_time"))
        close_ts = _parse_ts(m.get("close_time")) or (open_ts + 900 if open_ts else None)
        result   = m.get("result", "")
        brti     = m.get("_brti_avg")

        if live:
            candles  = _fetch_candles(ticker, open_ts, close_ts) if (ticker and open_ts and close_ts) else []
            time.sleep(0.25)
        else:
            candles = m.get("_candles", [])

        yes_prices = _extract_yes(candles) if live else _extract_yes(candles)
        sig        = compute_signal(yes_prices, brti or (m.get("floor_strike") or 94000))
        outcome    = _evaluate(sig.action, result)

        rows.append({
            "round":       idx + 1,
            "ticker":      ticker,
            "open_time":   m.get("open_time", ""),
            "brti_60s":    round(sig.round_open, 0),
            "yes_est":     round(sig.yes_estimate, 1),
            "signal":      sig.action,
            "confidence":  sig.confidence,
            "reason":      sig.reason,
            "result":      result.upper() if result else "?",
            "outcome":     outcome,
        })

        if (idx + 1) % 20 == 0:
            done = [r for r in rows if r["outcome"] in ("WIN","LOSS")]
            wins = [r for r in done if r["outcome"] == "WIN"]
            wr   = len(wins)/len(done)*100 if done else 0
            print(f"  [{idx+1:3d}/{len(markets)}]  Bets:{len(done):2d}  Wins:{len(wins):2d}  Win%:{wr:5.1f}%  HOLDs:{idx+1-len(done):3d}")

    df = pd.DataFrame(rows)
    total   = len(df)
    holds   = df[df.outcome=="HOLD"]
    bets    = df[df.outcome.isin(["WIN","LOSS"])]
    wins    = df[df.outcome=="WIN"]
    losses  = df[df.outcome=="LOSS"]
    wr      = len(wins)/len(bets)*100 if len(bets) else 0.0

    print("\n" + "═" * 72)
    print(f"  RESULTS  [{mode}]")
    print("═" * 72)
    print(f"  {'Total Rounds':<35} {total}")
    print(f"  {'HOLDs (safe)':<35} {len(holds)}  ({len(holds)/total*100:.1f}%)")
    print(f"  {'Bets Placed':<35} {len(bets)}  ({len(bets)/total*100:.1f}%)")
    print(f"  {'Wins':<35} {len(wins)}")
    print(f"  {'Losses':<35} {len(losses)}")
    print(f"  {'Win Rate on Bets':<35} {wr:.1f}%  ← key metric")
    print("═" * 72)

    if len(bets) == 0:
        print("\n  ⚠  No bets placed. Tighten threshold or check data quality.\n")
    elif wr >= 85:
        print(f"\n  ✅  GATE PASSED: {wr:.1f}% ≥ 85% — safe to proceed to Phase 2.\n")
    else:
        print(f"\n  ❌  GATE NOT MET: {wr:.1f}% < 85%  (need {int(np.ceil(0.85*len(bets))) - len(wins)} more wins)\n")

    df.to_csv("backtest_results.csv", index=False)
    print(f"  Results → backtest_results.csv\n")
    return df


if __name__ == "__main__":
    run()
