#!/usr/bin/env python3
"""
feeds/kraken_ws.py — Kraken Spot WebSocket feed

Connects to wss://ws.kraken.com and streams XBT/USD ticker + trade data.
Kraken specifics:
  - Heartbeat message every ~1 second when subscribed
  - Must maintain at least one active subscription or disconnected after ~60s
  - JSON messages, no special encoding

Run standalone:
    python feeds/kraken_ws.py
"""

import asyncio, json, logging
from datetime import datetime, timezone

log = logging.getLogger("kraken-ws")

WS_URL = "wss://ws.kraken.com/v2"

SUBSCRIBE_MSG = {
    "method": "subscribe",
    "params": {
        "channel": "ticker",
        "symbol":  ["BTC/USD"],
    },
}

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
            async with websockets.connect(WS_URL, ping_interval=20) as ws:
                log.info("Connected to Kraken — subscribing to BTC/USD ticker…")
                await ws.send(json.dumps(SUBSCRIBE_MSG))
                backoff = 1

                async for raw in ws:
                    msg = json.loads(raw)

                    # Heartbeat — just acknowledge, no action needed
                    if msg.get("channel") == "heartbeat":
                        continue

                    # Ticker update
                    if msg.get("channel") == "ticker" and msg.get("type") in ("snapshot", "update"):
                        for d in msg.get("data", []):
                            tick = {
                                "source":   "kraken",
                                "price":    float(d.get("last", d.get("bid", 0))),
                                "bid":      float(d.get("bid", 0)),
                                "ask":      float(d.get("ask", 0)),
                                "ts":       datetime.now(timezone.utc).timestamp(),
                                "datetime": datetime.now(timezone.utc).isoformat(),
                            }
                            if tick["price"] > 0 and not price_queue.full():
                                await price_queue.put(tick)

        except Exception as e:
            log.warning(f"WS error: {e} — reconnecting in {backoff}s…")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)


async def _print_consumer():
    while True:
        tick = await price_queue.get()
        ts   = tick["datetime"].split("T")[1][:8]
        print(f"[{ts}] XBT/USD (Kraken)  {tick['price']:>14,.2f}   bid:{tick['bid']:,.2f}  ask:{tick['ask']:,.2f}")


async def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s  %(levelname)-7s %(message)s",
                        datefmt="%H:%M:%S")
    await asyncio.gather(_connect(), _print_consumer())


if __name__ == "__main__":
    asyncio.run(main())
