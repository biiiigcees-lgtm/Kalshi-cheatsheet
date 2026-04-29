"""
backtest/signals.py — AI signal engine (Python equivalent of frontend/lib/signal.ts)

Mirrors the exact thresholds in CLAUDE.md so the backtest and live frontend
use identical decision logic.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Literal

SignalAction = Literal["BET_YES", "BET_NO", "HOLD"]

# ── Thresholds (match CLAUDE.md) ──────────────────────────────────────────────
NEUTRAL_LO        = 42
NEUTRAL_HI        = 58
VOLATILITY_LIMIT  = 18     # σ of YES prices (0–100 scale)
CONFIDENCE_MIN    = 0.60
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SignalResult:
    action:          SignalAction
    confidence:      float          # 0–1
    reason:          str
    yes_estimate:    float          # estimated Kalshi YES price 0–100
    round_open:      float          # 60-sec BRTI average at round open
    current_price:   float


def _slope(arr: np.ndarray) -> float:
    """Linear slope via least-squares (price units per sample)."""
    n = len(arr)
    if n < 3:
        return 0.0
    x = np.arange(n, dtype=float)
    mx, my = x.mean(), arr.mean()
    denom = ((x - mx) ** 2).sum()
    return float(((x - mx) * (arr - my)).sum() / denom) if denom else 0.0


def compute_signal(
    yes_prices: list[float],
    brti_avg:   float,
) -> SignalResult:
    """
    Compute a trading signal from a list of YES contract prices for one round.

    Parameters
    ----------
    yes_prices : list[float]
        YES contract prices (0–100) sampled during the round, oldest first.
    brti_avg : float
        The 60-second arithmetic mean of BRTI at the start of the round
        (used only as metadata; yes_prices already encode market sentiment).
    """
    base = dict(round_open=brti_avg, current_price=brti_avg, yes_estimate=50.0)

    if len(yes_prices) < 1:
        return SignalResult(action="HOLD", confidence=0.0,
                            reason="no_candle_data", **base)

    arr = np.array(yes_prices, dtype=float)

    # ── 60-second BRTI signal: mean of the opening candles ───────────────────
    n_first     = max(1, min(2, len(arr)))
    brti_signal = float(arr[:n_first].mean())
    base["yes_estimate"] = brti_signal

    # ── Volatility filter ─────────────────────────────────────────────────────
    vol = float(arr.std()) if len(arr) > 1 else 0.0
    if vol > VOLATILITY_LIMIT:
        return SignalResult(action="HOLD", confidence=round(vol / 100, 3),
                            reason=f"high_vol_{vol:.1f}", **base)

    # ── Neutral zone ──────────────────────────────────────────────────────────
    if NEUTRAL_LO <= brti_signal <= NEUTRAL_HI:
        return SignalResult(action="HOLD", confidence=0.40,
                            reason=f"neutral_{brti_signal:.1f}", **base)

    # ── Momentum ──────────────────────────────────────────────────────────────
    slope = _slope(arr)     # YES-price units per candle

    bullish = brti_signal > 50

    if (bullish and slope <= 0) or (not bullish and slope >= 0):
        return SignalResult(action="HOLD", confidence=0.45,
                            reason=f"{'bullish' if bullish else 'bearish'}_no_momentum_{brti_signal:.1f}",
                            **base)

    # ── Confidence ────────────────────────────────────────────────────────────
    distance = abs(brti_signal - 50.0)
    conf     = min(0.95, distance / 50.0)
    conf     = min(0.95, conf + abs(slope) / 100.0)     # momentum bonus
    conf     = round(conf * max(0.5, 1.0 - vol / 50.0), 3)  # vol penalty

    if conf < CONFIDENCE_MIN:
        return SignalResult(action="HOLD", confidence=conf,
                            reason=f"low_conf_{conf:.2f}", **base)

    action = "BET_YES" if bullish else "BET_NO"
    return SignalResult(
        action=action, confidence=conf,
        reason=f"{'bullish' if bullish else 'bearish'}_{brti_signal:.1f}_m{slope:+.2f}",
        **base,
    )
