from __future__ import annotations
import os
import time
import hmac
import hashlib
import logging
import json
from typing import Optional, Dict, Any
from urllib.parse import urlencode

# Optional dependency
try:
    from binance.client import Client as BinanceClient
    HAVE_PYBINANCE = True
except Exception:
    HAVE_PYBINANCE = False

import requests

logger = logging.getLogger("FuturesBroker")
if not logger.handlers:
    # basic configuration - you can replace with more advanced config in your app
    handler = logging.StreamHandler()
    fmt = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s')
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class BrokerException(Exception):
    pass


class ValidationError(BrokerException):
    pass


class Broker:
    """
    Minimal wrapper for Binance USDT-M Futures (fapi) operations.
    """

    def __init__(self,
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None,
                 testnet: Optional[bool] = None,
                 base_url: Optional[str] = None,
                 recv_window: int = 5000,
                 timeout: float = 10.0):
        """
        Initialize broker.

        If python-binance is installed it will be used; otherwise a lightweight REST client will be used.
        """

        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        env_test = os.getenv("BINANCE_TESTNET", None)
        if testnet is None:
            self.testnet = (str(env_test).lower() in ("1", "true", "yes"))
        else:
            self.testnet = testnet

        # Default base URLs for Binance Futures (USDT-M)
        # Allow override by env var
        env_base = os.getenv("BINANCE_BASE_URL")
        if base_url:
            self.base_url = base_url.rstrip('/')
        elif env_base:
            self.base_url = env_base.rstrip('/')
        else:
            # defaults:
            # production: https://fapi.binance.com
            # testnet: https://testnet.binancefuture.com  (set BINANCE_TESTNET=1 to use)
            self.base_url = "https://testnet.binancefuture.com" if self.testnet else "https://fapi.binance.com"

        self.recv_window = recv_window
        self.timeout = timeout

        self._use_pybinance = HAVE_PYBINANCE and self.api_key and self.api_secret
        self._client = None

        if self._use_pybinance:
            try:
                # python-binance Client initialization
                # Note: python-binance has separate futures endpoints methods (client.futures_*)
                self._client = BinanceClient(self.api_key, self.api_secret)
                logger.info("Using python-binance client for FuturesBroker.")
            except Exception as e:
                logger.warning("python-binance import succeeded but Client init failed: %s", e)
                self._use_pybinance = False

        if not self._use_pybinance:
            logger.info("Using REST fallback for FuturesBroker. Base URL: %s", self.base_url)

        # cache exchangeInfo for symbol validation
        self._exchange_info_cache: Optional[Dict[str, Any]] = None
        self._exchange_info_cache_ts: float = 0
        self._exchange_info_ttl = 120  # seconds

    # ---------------------------
    # Low-level REST helpers
    # ---------------------------
    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a params dict with the API secret for Binance API.
        Returns a new dict including the signature param.
        """
        if not self.api_secret:
            raise BrokerException("API secret missing for signed request.")
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'),
                             hashlib.sha256).hexdigest()
        signed = dict(params)
        signed['signature'] = signature
        return signed

    def _public_request(self, method: str, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        logger.debug("PUBLIC REQUEST %s %s %s", method, url, params or {})
        try:
            if method.upper() == "GET":
                resp = requests.get(url, params=params, timeout=self.timeout)
            else:
                resp = requests.request(method.upper(), url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            logger.exception("HTTP error in public request: %s %s", url, e)
            raise BrokerException(f"HTTP error: {e} - {resp.text if 'resp' in locals() else ''}")
        except Exception as e:
            logger.exception("Error in public request: %s %s", url, e)
            raise BrokerException(str(e))

    def _signed_request(self, method: str, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        if not params:
            params = {}
        params = dict(params)  # copy
        params['timestamp'] = self._timestamp()
        params['recvWindow'] = self.recv_window
        signed = self._sign_params(params)
        url = f"{self.base_url}{path}"
        headers = {"X-MBX-APIKEY": self.api_key} if self.api_key else {}
        logger.debug("SIGNED REQUEST %s %s %s", method, url, {k: v for k, v in signed.items() if k not in ('signature',)})
        try:
            if method.upper() == "GET":
                resp = requests.get(url, params=signed, headers=headers, timeout=self.timeout)
            else:
                resp = requests.post(url, params=signed, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            # try to include Binance error body
            body = ""
            try:
                body = resp.json()
            except Exception:
                body = resp.text if 'resp' in locals() else ''
            logger.exception("HTTP error in signed request: %s %s", url, e)
            raise BrokerException(f"HTTP error: {e} - {body}")
        except Exception as e:
            logger.exception("Error in signed request: %s %s", url, e)
            raise BrokerException(str(e))

    # ---------------------------
    # Exchange info & helpers
    # ---------------------------
    def _ensure_exchange_info(self) -> None:
        now = time.time()
        if self._exchange_info_cache and (now - self._exchange_info_cache_ts) < self._exchange_info_ttl:
            return
        logger.info("Fetching exchange info from Binance.")
        try:
            if self._use_pybinance:
                info = self._client.futures_exchange_info()
            else:
                info = self._public_request("GET", "/fapi/v1/exchangeInfo")
            self._exchange_info_cache = info
            self._exchange_info_cache_ts = now
        except Exception as e:
            logger.exception("Failed to fetch exchange info: %s", e)
            raise BrokerException("Could not obtain exchange info for symbol validation.") from e

    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Returns exchange info for a given symbol (e.g., 'BTCUSDT').
        Raises BrokerException if not found.
        """
        self._ensure_exchange_info()
        info = self._exchange_info_cache or {}
        symbols = info.get("symbols", [])
        for s in symbols:
            if s.get("symbol") == symbol:
                return s
        raise BrokerException(f"Symbol info not found for {symbol}")

    # ---------------------------
    # Core order methods
    # ---------------------------
    def place_market_order(self, symbol: str, side: str, quantity: float, **kwargs) -> Dict[str, Any]:
        """
        Place a MARKET futures order.
        kwargs passes through to the underlying API (e.g., reduceOnly, positionSide, newClientOrderId).
        """
        side = side.upper()
        assert side in ("BUY", "SELL"), "side must be BUY or SELL"
        payload = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": float(quantity),
        }
        payload.update(kwargs)
        logger.info("Placing MARKET order: %s", {k: payload[k] for k in ("symbol", "side", "quantity")})
        return self._place_order(payload)

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                          timeInForce: str = "GTC", **kwargs) -> Dict[str, Any]:
        """
        Place a LIMIT futures order.
        """
        side = side.upper()
        assert side in ("BUY", "SELL"), "side must be BUY or SELL"
        payload = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": float(quantity),
            "price": float(price),
            "timeInForce": timeInForce
        }
        payload.update(kwargs)
        logger.info("Placing LIMIT order: %s", {k: payload[k] for k in ("symbol", "side", "quantity", "price")})
        return self._place_order(payload)

    def place_stop_limit(self, symbol: str, side: str, quantity: float, stop_price: float, price: float,
                         reduceOnly: bool = False, timeInForce: str = "GTC", **kwargs) -> Dict[str, Any]:
        """
        Place a stop-limit style order on futures. Behavior can depend on exchange API.
        For Binance futures, we send type=STOP with stopPrice and price. Exchange may also support STOP_MARKET etc.
        """
        side = side.upper()
        assert side in ("BUY", "SELL"), "side must be BUY or SELL"
        payload = {
            "symbol": symbol,
            "side": side,
            "type": "STOP",
            "quantity": float(quantity),
            "stopPrice": float(stop_price),
            "price": float(price),
            "timeInForce": timeInForce,
            "reduceOnly": reduceOnly
        }
        payload.update(kwargs)
        logger.info("Placing STOP-LIMIT order: %s", {k: payload[k] for k in ("symbol", "side", "quantity", "stopPrice", "price")})
        return self._place_order(payload)

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal order placer. Uses python-binance if available, else REST.
        Always logs request and response.
        """
        # Basic validation pass-through: ensure symbol exists
        try:
            self.get_symbol_info(payload.get("symbol"))
        except Exception as e:
            logger.exception("Validation failed for symbol: %s", payload.get("symbol"))
            raise ValidationError(str(e)) from e

        if self._use_pybinance:
            # Map payload to python-binance futures_create_order args
            try:
                # python-binance futures_create_order accepts kwargs in form used here
                res = self._client.futures_create_order(**payload)
                logger.info("Order placed. client response: %s", res)
                return res
            except Exception as e:
                logger.exception("Error placing order via python-binance: %s", e)
                raise BrokerException(str(e)) from e
        else:
            try:
                res = self._signed_request("POST", "/fapi/v1/order", params=payload)
                logger.info("Order placed (REST). response: %s", res)
                return res
            except Exception as e:
                logger.exception("Error placing order (REST): %s", e)
                raise

    # ---------------------------
    # Cancel / Query methods
    # ---------------------------
    def cancel_order(self, symbol: str, orderId: Optional[int] = None, origClientOrderId: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an order by orderId or origClientOrderId.
        """
        if not (orderId or origClientOrderId):
            raise ValidationError("Specify orderId or origClientOrderId to cancel an order.")

        params = {"symbol": symbol}
        if orderId:
            params["orderId"] = int(orderId)
        if origClientOrderId:
            params["origClientOrderId"] = origClientOrderId

        logger.info("Canceling order: %s", params)
        if self._use_pybinance:
            try:
                res = self._client.futures_cancel_order(**params)
                logger.info("Cancel response: %s", res)
                return res
            except Exception as e:
                logger.exception("Error canceling order via python-binance: %s", e)
                raise BrokerException(str(e)) from e
        else:
            try:
                res = self._signed_request("DELETE" if False else "POST", "/fapi/v1/order", params=params)
                # NOTE: some endpoints accept DELETE; using POST with signature is common for Binance
                logger.info("Cancel response (REST): %s", res)
                return res
            except Exception as e:
                logger.exception("Error canceling order (REST): %s", e)
                raise

    def get_order_status(self, symbol: str, orderId: Optional[int] = None, origClientOrderId: Optional[str] = None) -> Dict[str, Any]:
        """
        Query order status. Provide orderId or origClientOrderId.
        """
        if not (orderId or origClientOrderId):
            raise ValidationError("Specify orderId or origClientOrderId to query an order.")

        params = {"symbol": symbol}
        if orderId:
            params["orderId"] = int(orderId)
        if origClientOrderId:
            params["origClientOrderId"] = origClientOrderId

        logger.info("Querying order status: %s", params)
        if self._use_pybinance:
            try:
                res = self._client.futures_get_order(**params)
                logger.info("Order status: %s", res)
                return res
            except Exception as e:
                logger.exception("Error querying order via python-binance: %s", e)
                raise BrokerException(str(e)) from e
        else:
            try:
                res = self._signed_request("GET", "/fapi/v1/order", params=params)
                logger.info("Order status (REST): %s", res)
                return res
            except Exception as e:
                logger.exception("Error querying order (REST): %s", e)
                raise

    # ---------------------------
    # Utility / account endpoints
    # ---------------------------
    def get_account_balance(self) -> Dict[str, Any]:
        """
        Returns futures account balance (position margin / wallet balance).
        """
        logger.info("Fetching futures account balance.")
        if self._use_pybinance:
            try:
                res = self._client.futures_account_balance()
                return res
            except Exception as e:
                logger.exception("Error fetching balance via python-binance: %s", e)
                raise BrokerException(str(e)) from e
        else:
            try:
                res = self._signed_request("GET", "/fapi/v2/balance")
                return res
            except Exception as e:
                logger.exception("Error fetching balance (REST): %s", e)
                raise

    def get_open_positions(self) -> Dict[str, Any]:
        """
        Returns positions from futures account.
        """
        logger.info("Fetching futures account positions.")
        if self._use_pybinance:
            try:
                res = self._client.futures_account()
                return res.get("positions", [])
            except Exception as e:
                logger.exception("Error fetching positions via python-binance: %s", e)
                raise BrokerException(str(e)) from e
        else:
            try:
                res = self._signed_request("GET", "/fapi/v2/account")
                return res.get("positions", [])
            except Exception as e:
                logger.exception("Error fetching positions (REST): %s", e)
                raise


# Simple usage example (for manual testing, not executed on import)
if __name__ == "__main__":
    # Quick local test scaffolding:
    logging.basicConfig(level=logging.INFO)
    broker = Broker()
    try:
        info = broker.get_symbol_info("BTCUSDT")
        print("Symbol info keys:", list(info.keys()))
    except Exception as e:
        print("Error:", e)
