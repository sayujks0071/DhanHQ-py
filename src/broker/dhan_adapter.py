"""
DhanHQ broker adapter for live trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import requests
import json

from ..config import Config

logger = logging.getLogger(__name__)


@dataclass
class DhanCredentials:
    """DhanHQ credentials."""
    client_id: str
    access_token: str
    base_url: str = "https://api.dhan.co"


class DhanAdapter:
    """
    DhanHQ broker adapter for live trading.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.credentials = DhanCredentials(
            client_id=config.dhan_client_id,
            access_token=config.dhan_access_token
        )
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.credentials.access_token}',
            'Content-Type': 'application/json'
        })
        
        # Trading state
        self.positions = {}
        self.orders = {}
        self.account_info = {}
        
    def test_connection(self) -> bool:
        """Test connection to DhanHQ."""
        try:
            response = self.session.get(f"{self.credentials.base_url}/api/v1/profile")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        try:
            response = self.session.get(f"{self.credentials.base_url}/api/v1/profile")
            if response.status_code == 200:
                self.account_info = response.json()
                return self.account_info
            else:
                logger.error(f"Failed to get account info: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {}
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current positions."""
        try:
            response = self.session.get(f"{self.credentials.base_url}/api/v1/positions")
            if response.status_code == 200:
                positions_data = response.json()
                self.positions = self._parse_positions(positions_data)
                return self.positions
            else:
                logger.error(f"Failed to get positions: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return {}
    
    def get_orders(self) -> Dict[str, Any]:
        """Get current orders."""
        try:
            response = self.session.get(f"{self.credentials.base_url}/api/v1/orders")
            if response.status_code == 200:
                orders_data = response.json()
                self.orders = self._parse_orders(orders_data)
                return self.orders
            else:
                logger.error(f"Failed to get orders: {response.text}")
                return {}
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return {}
    
    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        order_type: str = 'MARKET',
        product_type: str = 'INTRADAY',
        validity: str = 'DAY'
    ) -> Dict[str, Any]:
        """
        Place an order.
        
        Args:
            symbol: Symbol to trade
            side: 'BUY' or 'SELL'
            quantity: Quantity to trade
            price: Price (0 for market orders)
            order_type: 'MARKET' or 'LIMIT'
            product_type: 'INTRADAY', 'DELIVERY', 'MARGIN'
            validity: 'DAY', 'IOC', 'GTC'
            
        Returns:
            Order result
        """
        try:
            order_data = {
                'dhanClientId': self.credentials.client_id,
                'transactionType': side,
                'exchangeSegment': self._get_exchange_segment(symbol),
                'productType': product_type,
                'orderType': order_type,
                'validity': validity,
                'tradingSymbol': symbol,
                'securityId': self._get_security_id(symbol),
                'quantity': quantity,
                'price': price,
                'disclosedQuantity': 0,
                'offMarketFlag': False,
                'stopPrice': 0,
                'squareOff': 0,
                'trailingStop': 0,
                'boProfitValue': 0,
                'boStopLossValue': 0,
                'boTrailingStop': 0
            }
            
            response = self.session.post(
                f"{self.credentials.base_url}/api/v1/orders",
                json=order_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Order placed successfully: {result}")
                return result
            else:
                logger.error(f"Order placement failed: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        try:
            response = self.session.delete(f"{self.credentials.base_url}/api/v1/orders/{order_id}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Order cancelled successfully: {result}")
                return result
            else:
                logger.error(f"Order cancellation failed: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {'success': False, 'error': str(e)}
    
    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Modify an order."""
        try:
            modify_data = {}
            if quantity is not None:
                modify_data['quantity'] = quantity
            if price is not None:
                modify_data['price'] = price
            
            response = self.session.put(
                f"{self.credentials.base_url}/api/v1/orders/{order_id}",
                json=modify_data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Order modified successfully: {result}")
                return result
            else:
                logger.error(f"Order modification failed: {response.text}")
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Error modifying order: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get quotes for symbols."""
        try:
            # DhanHQ API expects symbols in specific format
            quote_data = {
                'IDX_I': symbols  # Index symbols
            }
            
            response = self.session.post(
                f"{self.credentials.base_url}/api/v1/quotes",
                json=quote_data
            )
            
            if response.status_code == 200:
                quotes = response.json()
                return self._parse_quotes(quotes)
            else:
                logger.error(f"Failed to get quotes: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting quotes: {e}")
            return {}
    
    def subscribe_quotes(self, symbol: str):
        """Subscribe to quotes for a symbol."""
        try:
            # This would implement WebSocket subscription
            # For now, just log the subscription
            logger.info(f"Subscribed to quotes for {symbol}")
        except Exception as e:
            logger.error(f"Error subscribing to quotes: {e}")
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = '1min'
    ) -> pd.DataFrame:
        """Get historical data for a symbol."""
        try:
            params = {
                'symbol': symbol,
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'interval': interval
            }
            
            response = self.session.get(
                f"{self.credentials.base_url}/api/v1/historical",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_historical_data(data)
            else:
                logger.error(f"Failed to get historical data: {response.text}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return pd.DataFrame()
    
    def get_option_chain(self, underlying: str, expiry: datetime) -> Dict[str, Any]:
        """Get option chain for underlying and expiry."""
        try:
            params = {
                'underlying': underlying,
                'expiry': expiry.strftime('%Y-%m-%d')
            }
            
            response = self.session.get(
                f"{self.credentials.base_url}/api/v1/option-chain",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_option_chain(data)
            else:
                logger.error(f"Failed to get option chain: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            return {}
    
    def _get_exchange_segment(self, symbol: str) -> str:
        """Get exchange segment for symbol."""
        # This would need to be implemented based on your symbol mapping
        # For now, return placeholder
        return 'NSE'
    
    def _get_security_id(self, symbol: str) -> str:
        """Get security ID for symbol."""
        # This would need to be implemented based on your symbol mapping
        # For now, return placeholder
        return symbol
    
    def _parse_positions(self, positions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse positions data."""
        positions = {}
        
        for pos in positions_data:
            symbol = pos.get('tradingSymbol', '')
            positions[symbol] = {
                'quantity': pos.get('quantity', 0),
                'average_price': pos.get('averagePrice', 0.0),
                'unrealized_pnl': pos.get('unrealizedPnl', 0.0),
                'realized_pnl': pos.get('realizedPnl', 0.0),
                'margin_used': pos.get('marginUsed', 0.0)
            }
        
        return positions
    
    def _parse_orders(self, orders_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse orders data."""
        orders = {}
        
        for order in orders_data:
            order_id = order.get('orderId', '')
            orders[order_id] = {
                'symbol': order.get('tradingSymbol', ''),
                'side': order.get('transactionType', ''),
                'quantity': order.get('quantity', 0),
                'price': order.get('price', 0.0),
                'status': order.get('orderStatus', ''),
                'order_type': order.get('orderType', ''),
                'created_time': order.get('orderTime', ''),
                'updated_time': order.get('modifiedTime', '')
            }
        
        return orders
    
    def _parse_quotes(self, quotes_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse quotes data."""
        quotes = {}
        
        for symbol, quote in quotes_data.items():
            quotes[symbol] = {
                'close': quote.get('lastPrice', 0.0),
                'bid': quote.get('bidPrice', 0.0),
                'ask': quote.get('askPrice', 0.0),
                'volume': quote.get('volume', 0),
                'open_interest': quote.get('openInterest', 0),
                'timestamp': datetime.now()
            }
        
        return quotes
    
    def _parse_historical_data(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Parse historical data."""
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def _parse_option_chain(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse option chain data."""
        # This would need to be implemented based on DhanHQ's option chain format
        # For now, return placeholder
        return {}
    
    def get_margin_required(self, symbol: str, quantity: int, price: float) -> float:
        """Get margin required for a trade."""
        try:
            # This would call DhanHQ's margin calculation API
            # For now, return placeholder calculation
            return quantity * price * 0.1  # 10% margin
        except Exception as e:
            logger.error(f"Error calculating margin: {e}")
            return 0.0
    
    def get_available_margin(self) -> float:
        """Get available margin."""
        try:
            account_info = self.get_account_info()
            return account_info.get('availableMargin', 0.0)
        except Exception as e:
            logger.error(f"Error getting available margin: {e}")
            return 0.0
    
    def close_all_positions(self) -> Dict[str, Any]:
        """Close all positions."""
        try:
            positions = self.get_positions()
            results = {}
            
            for symbol, position in positions.items():
                if position['quantity'] > 0:
                    # Close long position
                    result = self.place_order(
                        symbol=symbol,
                        side='SELL',
                        quantity=position['quantity'],
                        price=0,  # Market order
                        order_type='MARKET'
                    )
                    results[symbol] = result
                elif position['quantity'] < 0:
                    # Close short position
                    result = self.place_order(
                        symbol=symbol,
                        side='BUY',
                        quantity=abs(position['quantity']),
                        price=0,  # Market order
                        order_type='MARKET'
                    )
                    results[symbol] = result
            
            return results
            
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            return {}
    
    def get_trading_status(self) -> Dict[str, Any]:
        """Get trading status."""
        try:
            account_info = self.get_account_info()
            positions = self.get_positions()
            orders = self.get_orders()
            
            return {
                'account_status': account_info.get('status', 'unknown'),
                'available_cash': account_info.get('availableCash', 0.0),
                'margin_used': account_info.get('marginUsed', 0.0),
                'position_count': len(positions),
                'active_orders': len([o for o in orders.values() if o['status'] == 'ACTIVE']),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting trading status: {e}")
            return {}
