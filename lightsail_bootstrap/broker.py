"""
Broker abstraction that prefers the official `dhanhq` SDK and gracefully
falls back to raw REST calls when the SDK is unavailable.

Designed for Lightsail-style VPS deployments where the access token rotates
daily and is stored in a root-owned file (defaults to `/etc/dhan_access_token.txt`).
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
        assert self._token is not None  # for type-checkers
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
    # INTRA keeps latency low for intraday strategies; override via env if needed.
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
        """Map fields onto the keyword arguments expected by `dhanhq.place_order`."""
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
        from dhanhq import DhanContext, dhanhq  # imported lazily

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

    # ---- Public interface -------------------------------------------------

    def heartbeat(self) -> Dict[str, Any]:
        """Return fund limits as a heartbeat payload."""
        try:
            response = self._client_handle().get_fund_limits()
            return {"ok": True, "limits": response}
        except Exception as exc:  # pragma: no cover - defensive
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
    """
    REST fallback when the SDK import fails. Offers the same surface as
    `DhanSDKBroker`, keeping the trading loop agnostic to the transport.
    """

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

    # ---- Internal helpers -------------------------------------------------

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

    # ---- Public interface -------------------------------------------------

    def heartbeat(self) -> Dict[str, Any]:
        try:
            return {"ok": True, "limits": self.get_limits()}
        except Exception as exc:  # pragma: no cover - defensive
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
            exchange_segment=exchange_segment,
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
            exchange_segment=exchange_segment,
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
    """
    Instantiate the preferred broker. Uses the SDK by default and falls back
    to REST when the import fails or when `DHAN_FORCE_REST=1` is present.
    """

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


__all__ = [
    "DhanSDKBroker",
    "DhanRESTBroker",
    "make_broker",
]
