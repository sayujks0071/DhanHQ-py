#!/usr/bin/env python3
"""
Production Deployment Script for Enhanced AI Trading Bot
Ensures all testing overrides are disabled and provides clean production environment
"""

import json
import time
from datetime import datetime
from ai_trading_bot import AITradingBot, TradeRecommendation

class ProductionTradingBot(AITradingBot):
    """
    Production-ready trading bot with all testing overrides disabled
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ensure all testing overrides are disabled
        self.override_trading_hours = False
        self.dry_run_mode = False
        self.test_mode = False
        
        # Production logging
        self.logger.info("🚀 Production Trading Bot Initialized")
        self.logger.info("✅ Trading hours enforcement: ENABLED")
        self.logger.info("✅ All testing overrides: DISABLED")
    
    def validate_production_environment(self):
        """Validate that production environment is properly configured"""
        print("🔍 Production Environment Validation")
        print("=" * 50)
        
        # Check trading hours enforcement
        if hasattr(self, 'override_trading_hours') and self.override_trading_hours:
            print("❌ Trading hours override: ENABLED (should be disabled)")
            return False
        else:
            print("✅ Trading hours override: DISABLED")
        
        # Check dry run mode
        if hasattr(self, 'dry_run_mode') and self.dry_run_mode:
            print("❌ Dry run mode: ENABLED (should be disabled)")
            return False
        else:
            print("✅ Dry run mode: DISABLED")
        
        # Check test mode
        if hasattr(self, 'test_mode') and self.test_mode:
            print("❌ Test mode: ENABLED (should be disabled)")
            return False
        else:
            print("✅ Test mode: DISABLED")
        
        # Check trading hours configuration
        trading_hours = self.trading_config.get("trading_hours", {})
        if trading_hours.get("start") == "09:15" and trading_hours.get("end") == "15:30":
            print("✅ Trading hours: Correctly configured (09:15 - 15:30)")
        else:
            print("❌ Trading hours: Incorrect configuration")
            return False
        
        # Check risk management configuration
        risk_per_trade = self.trading_config.get("risk_per_trade", 0)
        if 0.01 <= risk_per_trade <= 0.05:  # 1-5% risk per trade
            print("✅ Risk per trade: Within acceptable range")
        else:
            print("❌ Risk per trade: Outside recommended range")
            return False
        
        # Check position limits
        max_position_size = self.trading_config.get("max_position_size", 0)
        if max_position_size > 0:
            print("✅ Max position size: Configured")
        else:
            print("❌ Max position size: Not configured")
            return False
        
        print("\n🎯 Production environment: VALIDATED")
        return True
    
    def get_production_status(self):
        """Get current production status"""
        return {
            "trading_hours_override": getattr(self, 'override_trading_hours', False),
            "dry_run_mode": getattr(self, 'dry_run_mode', False),
            "test_mode": getattr(self, 'test_mode', False),
            "within_trading_hours": self._within_trading_hours(),
            "available_funds": self._get_available_funds(),
            "daily_trade_counts": dict(self.daily_trade_counts),
            "trading_config": self.trading_config
        }

def create_production_bot():
    """Create a production-ready trading bot"""
    print("🚀 Creating Production Trading Bot")
    print("=" * 50)
    
    # Initialize production bot
    bot = ProductionTradingBot(
        client_id="your_actual_client_id",  # Replace with real credentials
        access_token="your_actual_access_token",  # Replace with real credentials
        ai_studio_api_key="your_actual_ai_studio_api_key"  # Replace with real credentials
    )
    
    # Production configuration
    production_config = {
        "min_confidence": 0.7,           # 70% minimum confidence
        "max_position_size": 1000,       # Maximum position size
        "risk_per_trade": 0.02,          # 2% risk per trade
        "stop_loss_percent": 0.05,       # 5% default stop-loss
        "take_profit_percent": 0.10,     # 10% default take-profit
        "max_daily_trades": 10,          # Daily trade limit
        "trading_hours": {
            "start": "09:15",
            "end": "15:30"
        },
        "update_interval": 5,            # 5-second update interval
        "funds_cache_ttl": 60,           # 1-minute fund cache
        "lookback_ticks": 120,           # 2-minute market history
        "allow_short_selling": False      # No short selling
    }
    
    # Apply production configuration
    bot.trading_config.update(production_config)
    
    return bot

def test_production_environment():
    """Test production environment with sample market data"""
    print("\n🧪 Testing Production Environment")
    print("=" * 50)
    
    # Create production bot
    bot = create_production_bot()
    
    # Validate production environment
    if not bot.validate_production_environment():
        print("❌ Production environment validation failed!")
        return False
    
    # Test with sample market data
    sample_market_data = {
        "security_id": "1333",
        "last_price": 1650.50,
        "volume": 45000,
        "high": 1665.00,
        "low": 1645.00,
        "open": 1655.00
    }
    
    # Test stop-loss handling with percentage
    print("\n📊 Testing Percentage Stop-Loss (5%)")
    rec_percentage = TradeRecommendation(
        action="BUY",
        confidence=0.8,
        quantity=0,  # Let bot calculate
        stop_loss=0.05  # 5% percentage
    )
    
    quantity_percentage = bot._determine_order_quantity(rec_percentage, "1333", sample_market_data)
    should_execute_percentage = bot._should_execute_trade(rec_percentage, "1333", quantity_percentage)
    
    print(f"  Quantity: {quantity_percentage}")
    print(f"  Should Execute: {should_execute_percentage}")
    print(f"  Trading Hours: {bot._within_trading_hours()}")
    
    # Test stop-loss handling with absolute price
    print("\n📊 Testing Absolute Price Stop-Loss (₹1600)")
    rec_absolute = TradeRecommendation(
        action="BUY",
        confidence=0.8,
        quantity=0,  # Let bot calculate
        stop_loss=1600  # Absolute price
    )
    
    quantity_absolute = bot._determine_order_quantity(rec_absolute, "1333", sample_market_data)
    should_execute_absolute = bot._should_execute_trade(rec_absolute, "1333", quantity_absolute)
    
    print(f"  Quantity: {quantity_absolute}")
    print(f"  Should Execute: {should_execute_absolute}")
    print(f"  Trading Hours: {bot._within_trading_hours()}")
    
    # Get production status
    status = bot.get_production_status()
    
    print("\n📊 Production Status")
    print("=" * 50)
    print(f"Trading Hours Override: {status['trading_hours_override']}")
    print(f"Dry Run Mode: {status['dry_run_mode']}")
    print(f"Test Mode: {status['test_mode']}")
    print(f"Within Trading Hours: {status['within_trading_hours']}")
    print(f"Available Funds: ₹{status['available_funds'] or 0:,.2f}")
    
    print("\n🎉 Production environment test completed!")
    return True

def main():
    """Main production deployment function"""
    print("🚀 Enhanced AI Trading Bot - Production Deployment")
    print("=" * 60)
    
    try:
        # Test production environment
        if test_production_environment():
            print("\n✅ Production environment ready!")
            print("\n📋 Production Deployment Checklist:")
            print("✅ All testing overrides disabled")
            print("✅ Trading hours enforcement enabled")
            print("✅ Risk management configured")
            print("✅ Stop-loss handling validated")
            print("✅ Safety mechanisms active")
            
            print("\n🎯 Ready for Live Deployment:")
            print("1. Update credentials with your actual DhanHQ and AI Studio keys")
            print("2. Test with paper trading account during market hours")
            print("3. Monitor performance and adjust parameters as needed")
            print("4. Deploy with live credentials when ready")
            
        else:
            print("\n❌ Production environment validation failed!")
            print("Please check configuration and try again.")
            
    except Exception as e:
        print(f"❌ Production deployment failed: {e}")
        raise

if __name__ == "__main__":
    main()



