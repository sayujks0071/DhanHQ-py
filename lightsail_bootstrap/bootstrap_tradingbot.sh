#!/usr/bin/env bash
# Bootstrap script for Ubuntu 22.04 Lightsail VPS.
# Installs dependencies, deploys a Dhan trading bot scaffold, and enables a
# systemd service with automatic restarts plus daily token rotation helper.
set -euo pipefail

########################################
# -------- Configuration block -------- #
########################################
DHAN_CLIENT_ID="${DHAN_CLIENT_ID:-CHANGE_ME_CLIENT_ID}"
INITIAL_ACCESS_TOKEN="${INITIAL_ACCESS_TOKEN:-CHANGE_ME_ACCESS_TOKEN}"
SYMBOLS="${SYMBOLS:-BANKNIFTY,NIFTY}"
POSITION_SIZE="${POSITION_SIZE:-1}"
REPO_URL="${REPO_URL:-}"            # Optional Git remote (https://… or git@…)
PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/tradingbot}"
PYTHON_BIN="${PYTHON_BIN:-python3.11}"
VENVDIR="$PROJECT_DIR/.venv"
SERVICE_NAME="tradingbot"
TOKEN_FILE="/etc/dhan_access_token.txt"
ENV_FILE="/etc/tradingbot.env"
TOKEN_HELPER="/usr/local/bin/dhan_token_update"

########################################
# ------------- Helpers --------------- #
########################################
log() { printf "\n[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

ensure_pkg() {
  if ! dpkg -s "$1" >/dev/null 2>&1; then
    sudo apt-get -y install "$1"
  fi
}

write_if_missing() {
  local path="$1" owner="$2" perms="$3" payload="$4"
  if [[ -f "$path" ]]; then
    log "$path already exists, leaving in place."
    return
  fi
  log "Creating $path"
  printf '%s\n' "$payload" | sudo tee "$path" >/dev/null
  sudo chown "$owner" "$path"
  sudo chmod "$perms" "$path"
}

########################################
# -------- System preparation -------- #
########################################
log "Updating apt cache and upgrading base system…"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

log "Installing base packages…"
sudo apt-get install -y build-essential git unzip curl fail2ban ufw

log "Installing Python toolchain (${PYTHON_BIN})…"
if ! sudo apt-get install -y "$PYTHON_BIN" "${PYTHON_BIN}-venv" python3-pip; then
  log "Preferred interpreter $PYTHON_BIN not available – falling back to system python3."
  PYTHON_BIN="python3"
  sudo apt-get install -y python3 python3-venv python3-pip
fi

log "Configuring timezone to Asia/Kolkata…"
sudo timedatectl set-timezone Asia/Kolkata

log "Enabling UFW firewall (SSH only)…"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw --force enable

########################################
# -------- Python environment -------- #
########################################
log "Preparing project directory at $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"

if [[ ! -d "$VENVDIR" ]]; then
  log "Creating virtual environment with $PYTHON_BIN"
  "$PYTHON_BIN" -m venv "$VENVDIR"
fi

log "Upgrading pip and installing dependencies…"
source "$VENVDIR/bin/activate"
pip install --upgrade pip
# Core dependencies
pip install pandas numpy pytz requests websockets python-dotenv
# Prefer SDK, fallback to plain HTTP if unavailable
pip install dhanhq || true
deactivate

########################################
# -------- Secrets / Env files ------- #
########################################
env_payload=$(cat <<EOF
# ---- NEVER COMMIT THIS FILE ----
DHAN_CLIENT_ID=${DHAN_CLIENT_ID}
DHAN_ACCESS_TOKEN_FILE=${TOKEN_FILE}
SYMBOLS=${SYMBOLS}
POSITION_SIZE=${POSITION_SIZE}
# Uncomment to force REST fallback:
# DHAN_FORCE_REST=1
EOF
)
write_if_missing "$ENV_FILE" root:root 600 "$env_payload"

write_if_missing "$TOKEN_FILE" root:root 600 "${INITIAL_ACCESS_TOKEN}"

########################################
# ------------ Code files ------------ #
########################################
if [[ -n "$REPO_URL" ]]; then
  log "Cloning repository $REPO_URL into $PROJECT_DIR (if not present)…"
  if [[ ! -d "$PROJECT_DIR/.git" ]]; then
    git clone "$REPO_URL" "$PROJECT_DIR"
  else
    log "Git repo already present, skipping clone."
  fi
fi

log "Writing broker.py (SDK-first, REST fallback)…"
cat > "$PROJECT_DIR/broker.py" <<'PY'
"""
Broker abstraction that prefers the official `dhanhq` SDK and gracefully
falls back to raw REST calls when the SDK is unavailable.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import requests


class TokenFile:
    """Helper that returns the latest token value when the backing file changes."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self._token: Optional[str] = None
        self._mtime: Optional[float] = None

    def read(self) -> str:
        """Return the current token, reloading when the file timestamp changes."""
        stat = self.path.stat()
        if self._mtime is None or stat.st_mtime != self._mtime:
            token = self.path.read_text(encoding="utf-8").strip()
            if not token:
                raise ValueError(f"Access token file {self.path} is empty.")
            self._token = token
            self._mtime = stat.st_mtime
        assert self._token is not None
        return self._token


def _to_side_label(side: str) -> str:
    normalized = side.strip().upper()
    if normalized in {"BUY", "B"}:
        return "BUY"
    if normalized in {"SELL", "S"}:
        return "SELL"
    raise ValueError(f"Unsupported side value: {side}")


def _transaction_defaults(product_type: Optional[str]) -> str:
    if product_type:
        return product_type.upper()
    return os.environ.get("DHAN_DEFAULT_PRODUCT_TYPE", "INTRA").upper()


@dataclass
class OrderPayload:
    security_id: str
    exchange_segment: str
    transaction_type: str
    quantity: int
    product_type: str
    order_type: str
    price: float
    trigger_price: float = 0.0
    disclosed_quantity: int = 0
    validity: str = "DAY"
    after_market_order: bool = False
    tag: Optional[str] = None

    def to_rest_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "securityId": self.security_id,
            "exchangeSegment": self.exchange_segment.upper(),
            "transactionType": self.transaction_type.upper(),
            "quantity": int(self.quantity),
            "orderType": self.order_type.upper(),
            "productType": self.product_type.upper(),
            "price": float(self.price),
            "triggerPrice": float(self.trigger_price),
            "afterMarketOrder": bool(self.after_market_order),
            "validity": self.validity.upper(),
            "disclosedQuantity": int(self.disclosed_quantity),
        }
        if self.tag:
            payload["correlationId"] = self.tag
        return payload

    def to_sdk_kwargs(self) -> Dict[str, Any]:
        return {
            "security_id": self.security_id,
            "exchange_segment": self.exchange_segment,
            "transaction_type": self.transaction_type,
            "quantity": int(self.quantity),
            "order_type": self.order_type,
            "product_type": self.product_type,
            "price": float(self.price),
            "trigger_price": float(self.trigger_price),
            "disclosed_quantity": int(self.disclosed_quantity),
            "after_market_order": bool(self.after_market_order),
            "validity": self.validity,
            "tag": self.tag,
        }


class DhanSDKBroker:
    """Primary broker that uses the official `dhanhq` SDK."""

    def __init__(self, client_id: str, token_file: TokenFile) -> None:
        from dhanhq import DhanContext, dhanhq

        self._client_id = client_id
        self._token_file = token_file
        self._dhan_cls = dhanhq
        self._context_cls = DhanContext

        self._token: Optional[str] = None
        self._context: Optional[Any] = None
        self._client: Optional[Any] = None

        self._refresh_client()

    def _refresh_client(self) -> None:
        token = self._token_file.read()
        if token == self._token and self._client is not None:
            return
        self._token = token
        self._context = self._context_cls(self._client_id, token)
        self._client = self._dhan_cls(self._context)

    def _client_handle(self):
        self._refresh_client()
        assert self._client is not None
        return self._client

    def heartbeat(self) -> Dict[str, Any]:
        try:
            response = self._client_handle().get_fund_limits()
            return {"ok": True, "limits": response}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def get_limits(self) -> Dict[str, Any]:
        return self._client_handle().get_fund_limits()

    def get_positions(self) -> Dict[str, Any]:
        return self._client_handle().get_positions()

    def get_order(self, order_id: str) -> Dict[str, Any]:
        return self._client_handle().get_order_by_id(order_id)

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return self._client_handle().cancel_order(order_id)

    def place_market_order(
        self,
        *,
        security_id: str,
        exchange_segment: str,
        side: str,
        quantity: int,
        product_type: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = OrderPayload(
            security_id=security_id,
            exchange_segment=exchange_segment.upper(),
            transaction_type=_to_side_label(side),
            quantity=quantity,
            product_type=_transaction_defaults(product_type),
            order_type="MARKET",
            price=0.0,
            trigger_price=0.0,
            tag=tag,
        )
        return self._client_handle().place_order(**payload.to_sdk_kwargs())

    def place_limit_order(
        self,
        *,
        security_id: str,
        exchange_segment: str,
        side: str,
        quantity: int,
        price: float,
        product_type: Optional[str] = None,
        validity: str = "DAY",
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = OrderPayload(
            security_id=security_id,
            exchange_segment=exchange_segment.upper(),
            transaction_type=_to_side_label(side),
            quantity=quantity,
            product_type=_transaction_defaults(product_type),
            order_type="LIMIT",
            price=price,
            validity=validity,
            tag=tag,
        )
        return self._client_handle().place_order(**payload.to_sdk_kwargs())


class DhanRESTBroker:
    """REST fallback when the SDK import fails."""

    def __init__(self, base_url: str, client_id: str, token_file: TokenFile) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self._token_file = token_file
        self._token: Optional[str] = None

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "client-id": client_id,
            }
        )

    def _ensure_token(self) -> None:
        token = self._token_file.read()
        if token != self._token:
            self.session.headers["access-token"] = token
            self._token = token

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        self._ensure_token()
        url = f"{self.base_url}{path}"
        response = self.session.request(method, url, timeout=5, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path} failed: {response.status_code} {response.text}")
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"raw": response.text, "status": response.status_code}

    def heartbeat(self) -> Dict[str, Any]:
        try:
            return {"ok": True, "limits": self.get_limits()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def get_limits(self) -> Dict[str, Any]:
        return self._request("GET", "/fundlimit")

    def get_positions(self) -> Dict[str, Any]:
        return self._request("GET", "/positions")

    def get_order(self, order_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/orders/{order_id}")

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/orders/{order_id}")

    def place_market_order(
        self,
        *,
        security_id: str,
        exchange_segment: str,
        side: str,
        quantity: int,
        product_type: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = OrderPayload(
            security_id=security_id,
            exchange_segment=exchange_segment.upper(),
            transaction_type=_to_side_label(side),
            quantity=quantity,
            product_type=_transaction_defaults(product_type),
            order_type="MARKET",
            price=0.0,
            trigger_price=0.0,
            tag=tag,
        )
        return self._request("POST", "/orders", json=payload.to_rest_payload())

    def place_limit_order(
        self,
        *,
        security_id: str,
        exchange_segment: str,
        side: str,
        quantity: int,
        price: float,
        product_type: Optional[str] = None,
        validity: str = "DAY",
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = OrderPayload(
            security_id=security_id,
            exchange_segment=exchange_segment.upper(),
            transaction_type=_to_side_label(side),
            quantity=quantity,
            product_type=_transaction_defaults(product_type),
            order_type="LIMIT",
            price=price,
            validity=validity,
            tag=tag,
        )
        return self._request("POST", "/orders", json=payload.to_rest_payload())


def make_broker() -> DhanSDKBroker | DhanRESTBroker:
    client_id = os.environ["DHAN_CLIENT_ID"]
    token_path = os.environ.get("DHAN_ACCESS_TOKEN_FILE", "/etc/dhan_access_token.txt")
    token_file = TokenFile(token_path)
    force_rest = os.environ.get("DHAN_FORCE_REST", "0").strip() in {"1", "true", "yes"}

    if not force_rest:
        try:
            return DhanSDKBroker(client_id, token_file)
        except Exception as exc:
            print(f"[broker] SDK initialisation failed, falling back to REST: {exc}", file=sys.stderr)

    base = os.environ.get("DHAN_API_BASE", "https://api.dhan.co/v2")
    return DhanRESTBroker(base, client_id, token_file)
PY

log "Writing strategy.py stub…"
cat > "$PROJECT_DIR/strategy.py" <<'PY'
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
    if now.weekday() >= 5:
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
    info: Dict[str, Any] = {"action": "idle", "symbols": symbols}

    if not market_open_now():
        info["action"] = "market_closed"
        return info

    try:
        info["positions"] = broker.get_positions()
    except Exception as exc:
        info["positions_error"] = str(exc)

    info["action"] = "hold"
    info["position_size"] = position_size
    return info
PY

log "Writing run_bot.py loop…"
cat > "$PROJECT_DIR/run_bot.py" <<'PY'
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


def handle_signal(signum, frame):
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
PY
chmod +x "$PROJECT_DIR/run_bot.py"

########################################
# -------- Systemd integration ------- #
########################################
log "Creating systemd service ${SERVICE_NAME}.service"
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" >/dev/null <<UNIT
[Unit]
Description=Trading Bot (Dhan)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${VENVDIR}/bin/python ${PROJECT_DIR}/run_bot.py
Restart=always
RestartSec=2
KillSignal=SIGTERM
StandardOutput=append:/var/log/${SERVICE_NAME}.log
StandardError=append:/var/log/${SERVICE_NAME}.log

[Install]
WantedBy=multi-user.target
UNIT

log "Reloading systemd daemon and enabling service…"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

########################################
# -------- Token update helper ------- #
########################################
log "Installing token update helper at ${TOKEN_HELPER}"
sudo tee "${TOKEN_HELPER}" >/dev/null <<'SH'
#!/usr/bin/env bash
set -euo pipefail
TOKFILE="/etc/dhan_access_token.txt"

if [[ $# -lt 1 ]]; then
  echo "Usage: dhan_token_update <NEW_TOKEN>"
  exit 1
fi

TMP="$(mktemp)"
printf "%s" "$1" >"$TMP"
chmod 600 "$TMP"
chown root:root "$TMP"
mv -f "$TMP" "$TOKFILE"
echo "Dhan access token updated at $(date)."
SH
sudo chmod +x "${TOKEN_HELPER}"

########################################
# -------------- Summary ------------- #
########################################
log "Bootstrap complete. Tail the service with:"
echo "  sudo tail -f /var/log/${SERVICE_NAME}.log"
