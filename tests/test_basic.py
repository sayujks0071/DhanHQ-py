"""
Basic tests for the Liquid F&O Trading System.
"""

import pytest
import sys
import os
from datetime import datetime, date

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import config
from src.utils.timezone import ISTTimezone
from src.strategies.fut_donchian import DonchianBreakoutStrategy
from src.strategies.opt_iron_fly import IronFlyStrategy
from src.options.greeks import GreeksCalculator
from src.options.iv import IVCalculator


class TestConfiguration:
    """Test configuration loading."""
    
    def test_config_loaded(self):
        """Test that configuration is loaded."""
        assert config is not None
        assert hasattr(config, 'settings')
    
    def test_live_trading_config(self):
        """Test live trading configuration."""
        # Should be False by default for safety
        assert isinstance(config.is_live_trading_enabled, bool)
    
    def test_options_enabled(self):
        """Test options trading configuration."""
        assert isinstance(config.is_options_enabled, bool)


class TestTimezone:
    """Test timezone utilities."""
    
    def test_ist_timezone(self):
        """Test IST timezone functionality."""
        current_time = ISTTimezone.now()
        assert current_time is not None
        assert isinstance(current_time, datetime)
    
    def test_market_hours(self):
        """Test market hours detection."""
        is_open = ISTTimezone.is_market_hours()
        assert isinstance(is_open, bool)
    
    def test_weekly_expiry(self):
        """Test weekly expiry detection."""
        is_weekly_expiry = ISTTimezone.is_weekly_expiry_day()
        assert isinstance(is_weekly_expiry, bool)


class TestStrategies:
    """Test trading strategies."""
    
    def test_donchian_strategy(self):
        """Test Donchian breakout strategy."""
        strategy = DonchianBreakoutStrategy()
        assert strategy is not None
        assert strategy.lookback_period == 20
        assert strategy.atr_multiplier == 2.0
    
    def test_iron_fly_strategy(self):
        """Test Iron Butterfly strategy."""
        strategy = IronFlyStrategy()
        assert strategy is not None
        assert strategy.delta_hedge is True
        assert strategy.iv_rank_min == 0.3
    
    def test_strategy_reset(self):
        """Test strategy reset functionality."""
        strategy = DonchianBreakoutStrategy()
        strategy.reset_strategy()
        assert strategy.position is None
        assert strategy.entry_time is None


class TestOptionsEngine:
    """Test options engine components."""
    
    def test_greeks_calculator(self):
        """Test Greeks calculator."""
        calc = GreeksCalculator()
        assert calc is not None
        
        # Test basic Greeks calculation
        greeks = calc.calculate_greeks(
            spot_price=24000,
            strike_price=24000,
            time_to_expiry=0.1,
            risk_free_rate=0.06,
            volatility=0.2,
            option_type='CALL'
        )
        
        assert greeks is not None
        assert hasattr(greeks, 'delta')
        assert hasattr(greeks, 'gamma')
        assert hasattr(greeks, 'theta')
        assert hasattr(greeks, 'vega')
        assert hasattr(greeks, 'rho')
    
    def test_iv_calculator(self):
        """Test IV calculator."""
        calc = IVCalculator()
        assert calc is not None
        
        # Test IV calculation
        iv = calc.calculate_iv(
            spot_price=24000,
            strike_price=24000,
            time_to_expiry=0.1,
            risk_free_rate=0.06,
            market_price=150.0,
            option_type='CALL'
        )
        
        # IV should be positive if calculation succeeds
        if iv is not None:
            assert iv > 0


class TestDataStructures:
    """Test data structures and classes."""
    
    def test_donchian_signal(self):
        """Test Donchian signal data structure."""
        from src.strategies.fut_donchian import DonchianSignal
        
        signal = DonchianSignal(
            signal_type='BUY',
            entry_price=24000.0,
            stop_loss=23800.0,
            take_profit=24200.0,
            confidence=0.8,
            timestamp=ISTTimezone.now(),
            rationale='Test signal'
        )
        
        assert signal.signal_type == 'BUY'
        assert signal.entry_price == 24000.0
        assert signal.confidence == 0.8
    
    def test_iron_fly_signal(self):
        """Test Iron Fly signal data structure."""
        from src.strategies.opt_iron_fly import IronFlySignal
        
        signal = IronFlySignal(
            signal_type='ENTER',
            strategy_legs=[],
            max_profit=100.0,
            max_loss=200.0,
            breakeven_points=(23900.0, 24100.0),
            confidence=0.7,
            timestamp=ISTTimezone.now(),
            rationale='Test Iron Fly signal'
        )
        
        assert signal.signal_type == 'ENTER'
        assert signal.max_profit == 100.0
        assert signal.max_loss == 200.0


class TestPerformanceMetrics:
    """Test performance metrics calculation."""
    
    def test_donchian_performance(self):
        """Test Donchian strategy performance metrics."""
        strategy = DonchianBreakoutStrategy()
        
        # Simulate some trades
        strategy.total_trades = 10
        strategy.winning_trades = 6
        strategy.total_pnl = 1000.0
        
        metrics = strategy.get_performance_metrics()
        
        assert metrics['total_trades'] == 10
        assert metrics['win_rate'] == 0.6
        assert metrics['total_pnl'] == 1000.0
        assert metrics['avg_pnl'] == 100.0
    
    def test_iron_fly_performance(self):
        """Test Iron Fly strategy performance metrics."""
        strategy = IronFlyStrategy()
        
        # Simulate some trades
        strategy.total_trades = 5
        strategy.winning_trades = 4
        strategy.total_pnl = 800.0
        
        metrics = strategy.get_performance_metrics()
        
        assert metrics['total_trades'] == 5
        assert metrics['win_rate'] == 0.8
        assert metrics['total_pnl'] == 800.0
        assert metrics['avg_pnl'] == 160.0


class TestRiskManagement:
    """Test risk management components."""
    
    def test_risk_config(self):
        """Test risk configuration."""
        risk_config = config.get_risk_config()
        assert risk_config is not None
        assert hasattr(risk_config, 'max_daily_dd')
        assert hasattr(risk_config, 'max_per_trade_risk')
        assert hasattr(risk_config, 'max_concurrent_positions')
    
    def test_universe_config(self):
        """Test universe configuration."""
        universe_config = config.get_universe_config()
        assert universe_config is not None
        assert hasattr(universe_config, 'max_instruments')


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
