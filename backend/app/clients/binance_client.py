"""Binance Testnet API client with authentication and trading functionality."""

import hashlib
import hmac
import time
import requests
from typing import Dict, Optional, List
from decimal import Decimal
from urllib.parse import urlencode

from app.utils.logging import get_logger
from app.config import settings

logger = get_logger(__name__)


class BinanceClient:
    """Binance Testnet API client for trading operations."""

    def __init__(self):
        """Initialize Binance Testnet client."""
        self.base_url = "https://testnet.binance.vision"
        self.api_key = settings.binance_api_key
        self.api_secret = settings.binance_api_secret
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })

    def _generate_signature(self, params: Dict) -> str:
        """Generate HMAC SHA256 signature for authenticated requests."""
        query_string = urlencode(params)
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False) -> Optional[Dict]:
        """Make authenticated request to Binance API."""
        if params is None:
            params = {}

        url = f"{self.base_url}{endpoint}"

        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Binance API request failed",
                         method=method, endpoint=endpoint, error=str(e))
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Binance API request",
                         method=method, endpoint=endpoint, error=str(e))
            return None

    def get_account_info(self) -> Optional[Dict]:
        """Get account information including balances."""
        return self._make_request('GET', '/api/v3/account', signed=True)

    def get_balance(self, asset: str = 'USDT') -> Decimal:
        """
        Get balance for specific asset.

        Args:
            asset: Asset symbol (default: USDT)

        Returns:
            Available balance as Decimal
        """
        account_info = self.get_account_info()
        if not account_info:
            logger.error("Failed to get account info")
            return Decimal('0')

        for balance in account_info.get('balances', []):
            if balance['asset'] == asset:
                return Decimal(balance['free'])

        logger.warning(f"Asset {asset} not found in account balances")
        return Decimal('0')

    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get trading symbol information."""
        exchange_info = self._make_request('GET', '/api/v3/exchangeInfo')
        if not exchange_info:
            return None

        for symbol_info in exchange_info.get('symbols', []):
            if symbol_info['symbol'] == symbol:
                return symbol_info

        return None

    def get_ticker_price(self, symbol: str) -> Optional[Decimal]:
        """Get current ticker price for symbol."""
        response = self._make_request(
            'GET', '/api/v3/ticker/price', {'symbol': symbol})
        if response:
            return Decimal(response['price'])
        return None

    def place_market_order(self, symbol: str, side: str, quantity: Decimal) -> Optional[Dict]:
        """
        Place a market order.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity

        Returns:
            Order response or None if failed
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': str(quantity)
        }

        logger.info(f"Placing market order",
                    symbol=symbol, side=side, quantity=str(quantity))

        response = self._make_request(
            'POST', '/api/v3/order', params, signed=True)

        if response:
            logger.info(f"Market order placed successfully",
                        order_id=response.get('orderId'),
                        symbol=symbol, side=side)
        else:
            logger.error(f"Failed to place market order",
                         symbol=symbol, side=side, quantity=str(quantity))

        return response

    def place_limit_order(self, symbol: str, side: str, quantity: Decimal, price: Decimal) -> Optional[Dict]:
        """
        Place a limit order.

        Args:
            symbol: Trading pair symbol
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            price: Limit price

        Returns:
            Order response or None if failed
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'LIMIT',
            'timeInForce': 'GTC',  # Good Till Cancelled
            'quantity': str(quantity),
            'price': str(price)
        }

        logger.info(f"Placing limit order",
                    symbol=symbol, side=side, quantity=str(quantity), price=str(price))

        response = self._make_request(
            'POST', '/api/v3/order', params, signed=True)

        if response:
            logger.info(f"Limit order placed successfully",
                        order_id=response.get('orderId'),
                        symbol=symbol, side=side)
        else:
            logger.error(f"Failed to place limit order",
                         symbol=symbol, side=side, quantity=str(quantity), price=str(price))

        return response

    def place_stop_loss_order(self, symbol: str, side: str, quantity: Decimal, stop_price: Decimal) -> Optional[Dict]:
        """
        Place a stop-loss order.

        Args:
            symbol: Trading pair symbol
            side: Order side ('BUY' or 'SELL')
            quantity: Order quantity
            stop_price: Stop price

        Returns:
            Order response or None if failed
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'STOP_LOSS_LIMIT',
            'timeInForce': 'GTC',
            'quantity': str(quantity),
            # Limit price (same as stop price for simplicity)
            'price': str(stop_price),
            'stopPrice': str(stop_price)
        }

        logger.info(f"Placing stop-loss order",
                    symbol=symbol, side=side, quantity=str(quantity), stop_price=str(stop_price))

        response = self._make_request(
            'POST', '/api/v3/order', params, signed=True)

        if response:
            logger.info(f"Stop-loss order placed successfully",
                        order_id=response.get('orderId'),
                        symbol=symbol, side=side)
        else:
            logger.error(f"Failed to place stop-loss order",
                         symbol=symbol, side=side, quantity=str(quantity), stop_price=str(stop_price))

        return response

    def cancel_order(self, symbol: str, order_id: int) -> Optional[Dict]:
        """Cancel an existing order."""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }

        logger.info(f"Cancelling order", symbol=symbol, order_id=order_id)

        response = self._make_request(
            'DELETE', '/api/v3/order', params, signed=True)

        if response:
            logger.info(f"Order cancelled successfully", order_id=order_id)
        else:
            logger.error(f"Failed to cancel order", order_id=order_id)

        return response

    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get all open orders for symbol or all symbols."""
        params = {}
        if symbol:
            params['symbol'] = symbol

        response = self._make_request(
            'GET', '/api/v3/openOrders', params, signed=True)
        return response if response else []

    def get_order_status(self, symbol: str, order_id: int) -> Optional[Dict]:
        """Get order status by order ID."""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }

        return self._make_request('GET', '/api/v3/order', params, signed=True)

    def test_connectivity(self) -> bool:
        """Test API connectivity."""
        response = self._make_request('GET', '/api/v3/ping')
        return response is not None

    def get_server_time(self) -> Optional[int]:
        """Get server time."""
        response = self._make_request('GET', '/api/v3/time')
        return response.get('serverTime') if response else None
