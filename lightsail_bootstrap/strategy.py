"""
Strategy stub used by `run_bot.py`.
Fill in your live logic inside `on_heartbeat` – by default it only checks
market hours and returns a structured heartbeat payload.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

import pytz

IST = pytz.timezone("Asia/Kolkata")


def market_open_now(now: dt.datetime | None = None) -> bool:
    now = now.astimezone(IST) if now else dt.datetime.now(IST)
    if now.weekday() >= 5:  # Saturday/Sunday
        return False
    session_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    session_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return session_start <= now <= session_end


def on_heartbeat(
    *,
    broker: Any,
    symbols: List[str],
    position_size: int,
    heartbeat: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Called once per loop from `run_bot.py`. Replace the body with your own
    trade logic. Return a dict so logs stay structured.
    """

    info: Dict[str, Any] = {"action": "idle", "symbols": symbols}

    if not market_open_now():
        info["action"] = "market_closed"
        return info

    # Example placeholder: pull positions once market is open.
    try:
        info["positions"] = broker.get_positions()
    except Exception as exc:  # pragma: no cover - defensive
        info["positions_error"] = str(exc)

    # Replace with real signal logic (order placement, exits, etc.).
    info["action"] = "hold"
    info["position_size"] = position_size
    return info
