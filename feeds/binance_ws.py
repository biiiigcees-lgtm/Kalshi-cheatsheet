#!/usr/bin/env python3
"""
feeds/binance_ws.py — Binance USDM Futures WebSocket feed

Connects to wss://fstream.binance.com and streams real-time BTC/USDT
mark price updates. Publishes to an in-process queue that the signal
engine can consume.

Binance guidelines followed:
  - Ping every 3 minutes to keep connection alive
  - Reconnect with exponential backoff on disconnect
  - Process WS messages asynchronously (no blocking on the main thread)
  - Rate limit: 10 subscribe messages / second

Run standalone:
    python feeds/binance_ws.py
"""

import asyncio, json, logging, time
from datetime import datetime, timezone

log = logging.getLogger("binance-ws")

WS_URL    = "wss://fstream.binance.com/ws/btcusdt@markPrice"
PING_SECS = 180

price_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)


async def _connect():
    try:
        import websockets
    except ImportError:
        raise ImportError("Install websockets: pip install websockets")

    backoff = 1
    while True:
        try:
            log.info(f"Connecting to {WS_URL}…")
            async with websockets.connect(WS_URL, ping_interval=PING_SECS) as ws:
                log.info("Connected to Binance USDM mark-price stream")
                backoff = 1
                async for raw in ws:
                    msg = json.loads(raw)
                    if msg.get("e") == "markPriceUpdate":
                        tick = {
                            "source":    "binance",
                            "price":     float(msg["p"]),
                            "index":     float(msg.get("i", msg["p"])),
                            "ts":        msg["E"] / 1000,
                            "datetime":  datetime.fromtimestamp(msg["E"] / 1000, tz=timezone.utc).isoformat(),
                        }
                        if not price_queue.full():
                            await price_queue.put(tick)
        except Exception as e:
            log.warning(f"WS error: {e} — reconnecting in {backoff}s…")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


async def _print_consumer():
    """Demo consumer — prints every tick to stdout."""
    while True:
        tick = await price_queue.get()
        ts   = tick["datetime"].split("T")[1][:8]
        print(f"[{ts}] BTC/USD  {tick['price']:>14,.2f}   (index: {tick['index']:>14,.2f})")


async def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s  %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")
    await asyncio.gather(_connect(), _print_consumer())


if __name__ == "__main__":
    asyncio.run(main())
