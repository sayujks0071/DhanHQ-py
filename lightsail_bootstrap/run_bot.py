#!/usr/bin/env python3
"""
Minimal trading bot loop for VPS deployments.
Reads rotating Dhan tokens from disk, emits heartbeats, and delegates decisions
to `strategy.on_heartbeat`.
"""

from __future__ import annotations

import os
import signal
import sys
import time
from datetime import datetime
from typing import List

import pytz

from broker import make_broker
import strategy

IST = pytz.timezone("Asia/Kolkata")
RUNNING = True


def now_ist() -> datetime:
    return datetime.now(IST)


def fmt(ts: datetime | None = None) -> str:
    return (ts or now_ist()).strftime("%Y-%m-%d %H:%M:%S")


def handle_signal(signum, frame):  # type: ignore[override]
    global RUNNING
    RUNNING = False
    print(f"[{fmt()}] Received signal {signum}; shutting down...", flush=True)


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


def parse_symbols(raw: str) -> List[str]:
    return [sym.strip().upper() for sym in raw.split(",") if sym.strip()]


def main() -> int:
    broker = make_broker()
    symbols = parse_symbols(os.environ.get("SYMBOLS", ""))
    position_size = int(os.environ.get("POSITION_SIZE", "1"))
    heartbeat_interval = float(os.environ.get("HEARTBEAT_INTERVAL", "1.0"))

    print(
        f"[{fmt()}] Bot starting. symbols={symbols or ['(none)']} "
        f"size={position_size} transport={broker.__class__.__name__}",
        flush=True,
    )

    while RUNNING:
        hb = broker.heartbeat()
        if not hb.get("ok"):
            print(f"[{fmt()}] heartbeat FAIL: {hb}", flush=True)
        else:
            decision = strategy.on_heartbeat(
                broker=broker,
                symbols=symbols,
                position_size=position_size,
                heartbeat=hb,
            )
            print(f"[{fmt()}] heartbeat ok | decision={decision}", flush=True)

        time.sleep(max(heartbeat_interval, 0.5))

    print(f"[{fmt()}] Bot stopped cleanly.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
