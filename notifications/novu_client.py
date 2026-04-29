"""
notifications/novu_client.py — Novu push notification client

Sends a "Secure Bet" push notification when the AI signal engine
identifies a high-confidence trade opportunity.

Setup:
  1. Create a Novu account at https://novu.co
  2. Add a push provider (Firebase FCM or OneSignal) in Novu dashboard
  3. Create a workflow named "secure-bet" with a push step
  4. Set NOVU_API_KEY in your environment

Usage:
    from notifications.novu_client import notify_signal
    notify_signal(
        subscriber_id="user-uuid",
        signal="BET_YES",
        ticker="KXBTC15M-25APR29-T94000",
        confidence=0.82,
        yes_estimate=87.3,
    )
"""

import os, logging, requests

log = logging.getLogger("novu")

NOVU_BASE     = "https://api.novu.co/v1"
WORKFLOW_ID   = "secure-bet"


def _headers() -> dict:
    key = os.getenv("NOVU_API_KEY", "")
    if not key:
        raise EnvironmentError("NOVU_API_KEY environment variable is not set")
    return {
        "Authorization": f"ApiKey {key}",
        "Content-Type":  "application/json",
    }


def upsert_subscriber(subscriber_id: str, email: str = "", name: str = "") -> None:
    """Create or update a Novu subscriber (call once per user on login)."""
    requests.post(
        f"{NOVU_BASE}/subscribers",
        headers=_headers(),
        json={"subscriberId": subscriber_id, "email": email, "firstName": name},
        timeout=10,
    ).raise_for_status()


def notify_signal(
    subscriber_id: str,
    signal: str,          # "BET_YES" | "BET_NO"
    ticker: str,
    confidence: float,
    yes_estimate: float,
) -> None:
    """
    Trigger the 'secure-bet' Novu workflow for a high-confidence signal.
    The push notification arrives on the user's device via FCM / OneSignal.
    """
    action_label = "🟢 BET YES ▲" if signal == "BET_YES" else "🔴 BET NO ▼"
    payload = {
        "name":         WORKFLOW_ID,
        "to":           {"subscriberId": subscriber_id},
        "payload": {
            "signal":      action_label,
            "ticker":      ticker,
            "confidence":  f"{confidence * 100:.1f}%",
            "yes_price":   f"{yes_estimate:.1f}¢",
            "message":     (
                f"{action_label} — {ticker}\n"
                f"Confidence: {confidence*100:.1f}%  |  YES est: {yes_estimate:.1f}¢"
            ),
        },
    }
    resp = requests.post(
        f"{NOVU_BASE}/events/trigger",
        headers=_headers(),
        json=payload,
        timeout=10,
    )
    if resp.ok:
        log.info(f"Novu notification sent → subscriber {subscriber_id} ({signal})")
    else:
        log.error(f"Novu error {resp.status_code}: {resp.text[:200]}")
