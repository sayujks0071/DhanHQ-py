"""
Event-driven backtesting engine with realistic execution simulation.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from ..config import Config
from ..data.candles import CandleData
from ..options.greeks import GreeksCalculator
from ..strategies.base import BaseStrategy
from ..risk.manager import RiskManager

logger = logging.getLogger(__name__)


@dataclass
class Fill:
    """Represents a trade fill with execution details."""
    timestamp: datetime
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    commission: float
    slippage: float
    order_id: str


@dataclass
class Position:
    """Represents a position in the portfolio."""
    symbol: str
    quantity: int
    avg_price: float
    unrealized_pnl: float
    realized_pnl: float
    margin_used: float


class BacktestEngine:
    """
    Event-driven backtesting engine with realistic execution simulation.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.positions: Dict[str, Position] = {}
        self.fills: List[Fill] = []
        self.cash = config.initial_capital
        self.margin_used = 0.0
        self.daily_pnl = []
        self.current_date = None
        
        # Risk management
        self.risk_manager = RiskManager(config)
        
        # Greeks calculator for options
        self.greeks_calc = GreeksCalculator()
        
        # Performance tracking
        self.equity_curve = []
        self.drawdown_curve = []
        self.max_drawdown = 0.0
        
    def run_backtest(
        self,
        strategy: BaseStrategy,
        start_date: datetime,
        end_date: datetime,
        universe: List[str]
    ) -> Dict[str, Any]:
        """
        Run backtest for a strategy over the specified period.
        """
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # Get historical data for all symbols
        data = self._load_historical_data(universe, start_date, end_date)
        
        # Initialize strategy
        strategy.initialize(data, self.config)
        
        # Run event loop
        for timestamp, market_data in self._generate_market_events(data):
            self.current_date = timestamp.date()
            
            # Update positions with current market data
            self._update_positions(market_data)
            
            # Generate strategy signals
            signals = strategy.generate_signals(timestamp, market_data, self.positions)
            
            # Execute signals
            for signal in signals:
                self._execute_signal(signal, market_data)
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Check risk limits
            if not self.risk_manager.check_limits(self.positions, self.cash, self.margin_used):
                logger.warning("Risk limits breached, stopping backtest")
                break
        
        # Calculate final metrics
        metrics = self._calculate_metrics()
        
        logger.info(f"Backtest completed. Final P&L: {metrics['total_pnl']:.2f}")
        return metrics
    
    def _load_historical_data(
        self, 
        universe: List[str], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """Load historical data for all symbols in universe."""
        # This would integrate with your data layer
        # For now, return empty dict - implement based on your data source
        return {}
    
    def _generate_market_events(self, data: Dict[str, pd.DataFrame]):
        """Generate market events in chronological order."""
        # Combine all timestamps and sort
        all_timestamps = set()
        for symbol_data in data.values():
            all_timestamps.update(symbol_data.index)
        
        for timestamp in sorted(all_timestamps):
            market_data = {}
            for symbol, symbol_data in data.items():
                if timestamp in symbol_data.index:
                    market_data[symbol] = symbol_data.loc[timestamp]
            
            yield timestamp, market_data
    
    def _execute_signal(self, signal: Dict[str, Any], market_data: Dict[str, Any]):
        """Execute a trading signal with realistic execution simulation."""
        symbol = signal['symbol']
        side = signal['side']
        quantity = signal['quantity']
        
        if symbol not in market_data:
            logger.warning(f"No market data for {symbol}")
            return
        
        # Get current market price
        current_price = market_data[symbol]['close']
        
        # Apply slippage
        slippage = self._calculate_slippage(symbol, quantity, side)
        execution_price = current_price + slippage if side == 'BUY' else current_price - slippage
        
        # Calculate commission
        commission = self._calculate_commission(symbol, quantity, execution_price)
        
        # Check if we have sufficient capital/margin
        if not self._check_capital_requirements(symbol, side, quantity, execution_price):
            logger.warning(f"Insufficient capital for {symbol} {side} {quantity}")
            return
        
        # Create fill
        fill = Fill(
            timestamp=self.current_date,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=execution_price,
            commission=commission,
            slippage=slippage,
            order_id=f"{symbol}_{side}_{self.current_date}"
        )
        
        # Update positions
        self._update_position_with_fill(fill)
        self.fills.append(fill)
        
        logger.info(f"Executed {side} {quantity} {symbol} at {execution_price:.2f}")
    
    def _calculate_slippage(self, symbol: str, quantity: int, side: str) -> float:
        """Calculate realistic slippage based on market conditions."""
        # Base slippage from config
        base_slippage = self.config.slippage_bps / 10000
        
        # Volume-based slippage (higher for larger orders)
        volume_factor = min(quantity / 1000, 2.0)  # Cap at 2x
        
        # Time-based slippage (higher during market open/close)
        hour = self.current_date.hour if self.current_date else 9
        time_factor = 1.5 if hour in [9, 15] else 1.0
        
        return base_slippage * volume_factor * time_factor
    
    def _calculate_commission(self, symbol: str, quantity: int, price: float) -> float:
        """Calculate commission based on symbol type and quantity."""
        notional = quantity * price
        
        if 'OPT' in symbol:
            # Options commission (per contract)
            return quantity * self.config.options_commission
        else:
            # Equity/Futures commission (percentage)
            return notional * self.config.equity_commission / 100
    
    def _check_capital_requirements(
        self, 
        symbol: str, 
        side: str, 
        quantity: int, 
        price: float
    ) -> bool:
        """Check if we have sufficient capital/margin for the trade."""
        notional = quantity * price
        
        if side == 'BUY':
            # For buying, check cash
            return self.cash >= notional
        else:
            # For selling, check if we have the position
            if symbol in self.positions:
                return self.positions[symbol].quantity >= quantity
            return False
    
    def _update_position_with_fill(self, fill: Fill):
        """Update position based on a fill."""
        symbol = fill.symbol
        
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=0,
                avg_price=0.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                margin_used=0.0
            )
        
        position = self.positions[symbol]
        
        if fill.side == 'BUY':
            # Add to position
            new_quantity = position.quantity + fill.quantity
            new_avg_price = (
                (position.avg_price * position.quantity + fill.price * fill.quantity) 
                / new_quantity
            )
            position.quantity = new_quantity
            position.avg_price = new_avg_price
            
            # Update cash
            self.cash -= (fill.quantity * fill.price + fill.commission)
            
        else:  # SELL
            # Reduce position
            position.quantity -= fill.quantity
            
            # Calculate realized P&L
            realized_pnl = (fill.price - position.avg_price) * fill.quantity
            position.realized_pnl += realized_pnl
            
            # Update cash
            self.cash += (fill.quantity * fill.price - fill.commission)
            
            # Remove position if quantity is zero
            if position.quantity == 0:
                del self.positions[symbol]
    
    def _update_positions(self, market_data: Dict[str, Any]):
        """Update unrealized P&L for all positions."""
        for symbol, position in self.positions.items():
            if symbol in market_data:
                current_price = market_data[symbol]['close']
                position.unrealized_pnl = (current_price - position.avg_price) * position.quantity
    
    def _update_performance_metrics(self):
        """Update performance metrics."""
        # Calculate total portfolio value
        total_value = self.cash
        for position in self.positions.values():
            total_value += position.quantity * position.avg_price + position.unrealized_pnl
        
        self.equity_curve.append(total_value)
        
        # Calculate drawdown
        if len(self.equity_curve) > 1:
            peak = max(self.equity_curve)
            current_dd = (peak - total_value) / peak
            self.drawdown_curve.append(current_dd)
            self.max_drawdown = max(self.max_drawdown, current_dd)
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive backtest metrics."""
        if not self.equity_curve:
            return {}
        
        equity_series = pd.Series(self.equity_curve)
        returns = equity_series.pct_change().dropna()
        
        # Basic metrics
        total_return = (equity_series.iloc[-1] - equity_series.iloc[0]) / equity_series.iloc[0]
        annualized_return = (1 + total_return) ** (252 / len(equity_series)) - 1
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Drawdown metrics
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak
        max_drawdown = drawdown.min()
        
        # Trade metrics
        total_trades = len(self.fills)
        winning_trades = sum(1 for fill in self.fills if fill.side == 'SELL' and 
                           self._get_trade_pnl(fill) > 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': equity_series.iloc[-1] - equity_series.iloc[0],
            'final_equity': equity_series.iloc[-1]
        }
    
    def _get_trade_pnl(self, fill: Fill) -> float:
        """Calculate P&L for a specific trade."""
        # This would need to track entry/exit pairs
        # Simplified for now
        return 0.0
