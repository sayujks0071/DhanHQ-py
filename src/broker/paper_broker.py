"""
Paper trading broker for simulation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json

from ..config import Config

logger = logging.getLogger(__name__)


@dataclass
class PaperPosition:
    """Paper trading position."""
    symbol: str
    quantity: int
    average_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin_used: float
    entry_time: datetime


@dataclass
class PaperOrder:
    """Paper trading order."""
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    order_type: str
    status: str
    created_time: datetime
    filled_time: Optional[datetime] = None
    filled_price: Optional[float] = None
    commission: float = 0.0


class PaperBroker:
    """
    Paper trading broker for simulation.
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Trading state
        self.positions: Dict[str, PaperPosition] = {}
        self.orders: Dict[str, PaperOrder] = {}
        self.cash = config.initial_capital
        self.margin_used = 0.0
        self.order_counter = 0
        
        # Market data simulation
        self.market_data = {}
        self.subscriptions = set()
        
        # State persistence
        self.state_file = "data/paper_broker_state.json"
        self._load_state()
    
    def test_connection(self) -> bool:
        """Test connection (always successful for paper trading)."""
        return True
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        return {
            'status': 'active',
            'available_cash': self.cash,
            'margin_used': self.margin_used,
            'total_value': self._calculate_total_value(),
            'unrealized_pnl': self._calculate_unrealized_pnl(),
            'realized_pnl': self._calculate_realized_pnl()
        }
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current positions."""
        positions = {}
        for symbol, position in self.positions.items():
            positions[symbol] = {
                'quantity': position.quantity,
                'average_price': position.average_price,
                'unrealized_pnl': position.unrealized_pnl,
                'realized_pnl': position.realized_pnl,
                'margin_used': position.margin_used,
                'entry_time': position.entry_time.isoformat()
            }
        return positions
    
    def get_orders(self) -> Dict[str, Any]:
        """Get current orders."""
        orders = {}
        for order_id, order in self.orders.items():
            orders[order_id] = {
                'symbol': order.symbol,
                'side': order.side,
                'quantity': order.quantity,
                'price': order.price,
                'order_type': order.order_type,
                'status': order.status,
                'created_time': order.created_time.isoformat(),
                'filled_time': order.filled_time.isoformat() if order.filled_time else None,
                'filled_price': order.filled_price,
                'commission': order.commission
            }
        return orders
    
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
            # Generate order ID
            order_id = f"PAPER_{self.order_counter:06d}"
            self.order_counter += 1
            
            # Get current market price if market order
            if order_type == 'MARKET':
                current_price = self._get_current_price(symbol)
                if current_price is None:
                    return {'success': False, 'error': f'No market data for {symbol}'}
                price = current_price
            
            # Check if we can execute the order
            if not self._can_execute_order(symbol, side, quantity, price):
                return {'success': False, 'error': 'Insufficient funds or position'}
            
            # Create order
            order = PaperOrder(
                order_id=order_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_type=order_type,
                status='PENDING',
                created_time=datetime.now()
            )
            
            # Store order
            self.orders[order_id] = order
            
            # Execute order immediately (simplified)
            self._execute_order(order)
            
            logger.info(f"Paper order placed: {order_id} {side} {quantity} {symbol} at {price}")
            
            return {
                'success': True,
                'order_id': order_id,
                'status': order.status,
                'filled_price': order.filled_price,
                'commission': order.commission
            }
            
        except Exception as e:
            logger.error(f"Error placing paper order: {e}")
            return {'success': False, 'error': str(e)}
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order."""
        try:
            if order_id not in self.orders:
                return {'success': False, 'error': 'Order not found'}
            
            order = self.orders[order_id]
            
            if order.status not in ['PENDING', 'SUBMITTED']:
                return {'success': False, 'error': 'Order cannot be cancelled'}
            
            order.status = 'CANCELLED'
            
            logger.info(f"Paper order cancelled: {order_id}")
            
            return {'success': True, 'order_id': order_id, 'status': order.status}
            
        except Exception as e:
            logger.error(f"Error cancelling paper order: {e}")
            return {'success': False, 'error': str(e)}
    
    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Modify an order."""
        try:
            if order_id not in self.orders:
                return {'success': False, 'error': 'Order not found'}
            
            order = self.orders[order_id]
            
            if order.status not in ['PENDING', 'SUBMITTED']:
                return {'success': False, 'error': 'Order cannot be modified'}
            
            if quantity is not None:
                order.quantity = quantity
            if price is not None:
                order.price = price
            
            logger.info(f"Paper order modified: {order_id}")
            
            return {'success': True, 'order_id': order_id, 'status': order.status}
            
        except Exception as e:
            logger.error(f"Error modifying paper order: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """Get quotes for symbols."""
        quotes = {}
        
        for symbol in symbols:
            current_price = self._get_current_price(symbol)
            if current_price is not None:
                quotes[symbol] = {
                    'close': current_price,
                    'bid': current_price * 0.999,  # Simulate bid-ask spread
                    'ask': current_price * 1.001,
                    'volume': np.random.randint(1000, 10000),
                    'open_interest': np.random.randint(100, 1000),
                    'timestamp': datetime.now()
                }
        
        return quotes
    
    def subscribe_quotes(self, symbol: str):
        """Subscribe to quotes for a symbol."""
        self.subscriptions.add(symbol)
        logger.info(f"Subscribed to quotes for {symbol}")
    
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = '1min'
    ) -> pd.DataFrame:
        """Get historical data for a symbol."""
        try:
            # Generate mock historical data
            date_range = pd.date_range(start=start_date, end=end_date, freq=interval)
            
            # Generate random walk data
            np.random.seed(hash(symbol) % 2**32)  # Consistent seed for same symbol
            returns = np.random.normal(0, 0.01, len(date_range))
            prices = 100 * np.exp(np.cumsum(returns))
            
            df = pd.DataFrame({
                'open': prices * (1 + np.random.normal(0, 0.005, len(date_range))),
                'high': prices * (1 + np.abs(np.random.normal(0, 0.01, len(date_range)))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.01, len(date_range)))),
                'close': prices,
                'volume': np.random.randint(1000, 10000, len(date_range))
            }, index=date_range)
            
            return df
            
        except Exception as e:
            logger.error(f"Error generating historical data: {e}")
            return pd.DataFrame()
    
    def get_option_chain(self, underlying: str, expiry: datetime) -> Dict[str, Any]:
        """Get option chain for underlying and expiry."""
        try:
            # Generate mock option chain
            current_price = self._get_current_price(underlying)
            if current_price is None:
                return {}
            
            # Generate strikes around current price
            strikes = []
            for i in range(-10, 11):
                strike = current_price + (i * current_price * 0.05)  # 5% intervals
                strikes.append(round(strike, 2))
            
            option_chain = {
                'underlying': underlying,
                'expiry': expiry.isoformat(),
                'current_price': current_price,
                'strikes': strikes,
                'calls': {},
                'puts': {}
            }
            
            # Generate call options
            for strike in strikes:
                option_symbol = f"{underlying}_CALL_{strike}_{expiry.strftime('%Y%m%d')}"
                option_chain['calls'][strike] = {
                    'symbol': option_symbol,
                    'strike': strike,
                    'bid': max(0.05, (current_price - strike) * 0.1),
                    'ask': max(0.05, (current_price - strike) * 0.1 + 0.05),
                    'volume': np.random.randint(0, 1000),
                    'open_interest': np.random.randint(0, 5000),
                    'iv': np.random.uniform(0.1, 0.5)
                }
            
            # Generate put options
            for strike in strikes:
                option_symbol = f"{underlying}_PUT_{strike}_{expiry.strftime('%Y%m%d')}"
                option_chain['puts'][strike] = {
                    'symbol': option_symbol,
                    'strike': strike,
                    'bid': max(0.05, (strike - current_price) * 0.1),
                    'ask': max(0.05, (strike - current_price) * 0.1 + 0.05),
                    'volume': np.random.randint(0, 1000),
                    'open_interest': np.random.randint(0, 5000),
                    'iv': np.random.uniform(0.1, 0.5)
                }
            
            return option_chain
            
        except Exception as e:
            logger.error(f"Error generating option chain: {e}")
            return {}
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        if symbol in self.market_data:
            return self.market_data[symbol]
        
        # Generate mock price if not available
        np.random.seed(hash(symbol) % 2**32)
        base_price = 100 + (hash(symbol) % 1000)
        price = base_price * (1 + np.random.normal(0, 0.01))
        
        self.market_data[symbol] = price
        return price
    
    def _can_execute_order(self, symbol: str, side: str, quantity: int, price: float) -> bool:
        """Check if we can execute an order."""
        total_cost = quantity * price
        
        if side == 'BUY':
            # Check if we have enough cash
            return self.cash >= total_cost
        else:  # SELL
            # Check if we have the position
            if symbol in self.positions:
                return self.positions[symbol].quantity >= quantity
            return False
    
    def _execute_order(self, order: PaperOrder):
        """Execute an order."""
        try:
            # Calculate commission
            commission = self._calculate_commission(order.symbol, order.quantity, order.price)
            
            # Update order
            order.status = 'FILLED'
            order.filled_time = datetime.now()
            order.filled_price = order.price
            order.commission = commission
            
            # Update positions
            if order.side == 'BUY':
                self._add_position(order.symbol, order.quantity, order.price, commission)
            else:  # SELL
                self._reduce_position(order.symbol, order.quantity, order.price, commission)
            
            # Update cash
            if order.side == 'BUY':
                self.cash -= (total_cost + commission)
            else:  # SELL
                self.cash += (total_cost - commission)
            
            logger.info(f"Paper order executed: {order.order_id}")
            
        except Exception as e:
            logger.error(f"Error executing paper order: {e}")
            order.status = 'REJECTED'
    
    def _add_position(self, symbol: str, quantity: int, price: float, commission: float):
        """Add to position."""
        if symbol not in self.positions:
            self.positions[symbol] = PaperPosition(
                symbol=symbol,
                quantity=0,
                average_price=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                margin_used=0.0,
                entry_time=datetime.now()
            )
        
        position = self.positions[symbol]
        
        # Update average price
        new_quantity = position.quantity + quantity
        new_avg_price = (
            (position.average_price * position.quantity + price * quantity) 
            / new_quantity
        )
        
        position.quantity = new_quantity
        position.average_price = new_avg_price
        position.margin_used += quantity * price * 0.1  # 10% margin
    
    def _reduce_position(self, symbol: str, quantity: int, price: float, commission: float):
        """Reduce position."""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Calculate realized P&L
        realized_pnl = (price - position.average_price) * quantity
        position.realized_pnl += realized_pnl
        
        # Reduce position
        position.quantity -= quantity
        position.margin_used -= quantity * price * 0.1  # 10% margin
        
        # Remove position if quantity is zero
        if position.quantity == 0:
            del self.positions[symbol]
    
    def _calculate_commission(self, symbol: str, quantity: int, price: float) -> float:
        """Calculate commission for a trade."""
        notional = quantity * price
        
        if 'OPT' in symbol:
            return quantity * self.config.options_commission
        else:
            return notional * self.config.equity_commission / 100
    
    def _calculate_total_value(self) -> float:
        """Calculate total portfolio value."""
        total_value = self.cash
        
        for position in self.positions.values():
            current_price = self._get_current_price(position.symbol)
            if current_price is not None:
                total_value += position.quantity * current_price
        
        return total_value
    
    def _calculate_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        unrealized_pnl = 0.0
        
        for position in self.positions.values():
            current_price = self._get_current_price(position.symbol)
            if current_price is not None:
                unrealized_pnl += (current_price - position.average_price) * position.quantity
        
        return unrealized_pnl
    
    def _calculate_realized_pnl(self) -> float:
        """Calculate realized P&L."""
        realized_pnl = 0.0
        
        for position in self.positions.values():
            realized_pnl += position.realized_pnl
        
        return realized_pnl
    
    def _save_state(self):
        """Save broker state to file."""
        state = {
            'positions': {
                symbol: {
                    'quantity': pos.quantity,
                    'average_price': pos.average_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'realized_pnl': pos.realized_pnl,
                    'margin_used': pos.margin_used,
                    'entry_time': pos.entry_time.isoformat()
                }
                for symbol, pos in self.positions.items()
            },
            'orders': {
                order_id: {
                    'symbol': order.symbol,
                    'side': order.side,
                    'quantity': order.quantity,
                    'price': order.price,
                    'order_type': order.order_type,
                    'status': order.status,
                    'created_time': order.created_time.isoformat(),
                    'filled_time': order.filled_time.isoformat() if order.filled_time else None,
                    'filled_price': order.filled_price,
                    'commission': order.commission
                }
                for order_id, order in self.orders.items()
            },
            'cash': self.cash,
            'margin_used': self.margin_used,
            'order_counter': self.order_counter,
            'subscriptions': list(self.subscriptions)
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self):
        """Load broker state from file."""
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Restore positions
            self.positions = {}
            for symbol, pos_data in state.get('positions', {}).items():
                self.positions[symbol] = PaperPosition(
                    symbol=symbol,
                    quantity=pos_data['quantity'],
                    average_price=pos_data['average_price'],
                    unrealized_pnl=pos_data['unrealized_pnl'],
                    realized_pnl=pos_data['realized_pnl'],
                    margin_used=pos_data['margin_used'],
                    entry_time=datetime.fromisoformat(pos_data['entry_time'])
                )
            
            # Restore orders
            self.orders = {}
            for order_id, order_data in state.get('orders', {}).items():
                self.orders[order_id] = PaperOrder(
                    order_id=order_id,
                    symbol=order_data['symbol'],
                    side=order_data['side'],
                    quantity=order_data['quantity'],
                    price=order_data['price'],
                    order_type=order_data['order_type'],
                    status=order_data['status'],
                    created_time=datetime.fromisoformat(order_data['created_time']),
                    filled_time=datetime.fromisoformat(order_data['filled_time']) if order_data['filled_time'] else None,
                    filled_price=order_data['filled_price'],
                    commission=order_data['commission']
                )
            
            # Restore other state
            self.cash = state.get('cash', self.config.initial_capital)
            self.margin_used = state.get('margin_used', 0.0)
            self.order_counter = state.get('order_counter', 0)
            self.subscriptions = set(state.get('subscriptions', []))
            
            logger.info("Loaded paper broker state from file")
            
        except FileNotFoundError:
            logger.info("No existing state file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def get_trading_status(self) -> Dict[str, Any]:
        """Get trading status."""
        return {
            'account_status': 'active',
            'available_cash': self.cash,
            'margin_used': self.margin_used,
            'total_value': self._calculate_total_value(),
            'position_count': len(self.positions),
            'active_orders': len([o for o in self.orders.values() if o.status == 'PENDING']),
            'last_updated': datetime.now().isoformat()
        }
