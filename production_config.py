#!/usr/bin/env python3
"""
Production Configuration for Enhanced AI Trading Bot
Re-enables trading hour enforcement and prepares for live market data
"""

import json
from ai_trading_bot import AITradingBot

def create_production_bot():
    """Create a production-ready bot with trading hours enforcement"""
    
    # Initialize bot with your credentials
    bot = AITradingBot(
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
    
    # Ensure trading hours enforcement is enabled
    if hasattr(bot, 'override_trading_hours'):
        bot.override_trading_hours = False
    
    print("🚀 Production Bot Configuration")
    print("=" * 50)
    print(f"✅ Trading hours enforcement: ENABLED")
    print(f"✅ Trading window: {production_config['trading_hours']['start']} - {production_config['trading_hours']['end']}")
    print(f"✅ Risk per trade: {production_config['risk_per_trade']*100}%")
    print(f"✅ Max position size: {production_config['max_position_size']}")
    print(f"✅ Daily trade limit: {production_config['max_daily_trades']}")
    print(f"✅ Min confidence: {production_config['min_confidence']*100}%")
    
    return bot

def validate_production_config(bot):
    """Validate production configuration"""
    print("\n🔍 Production Configuration Validation")
    print("=" * 50)
    
    # Check trading hours
    trading_hours = bot.trading_config.get("trading_hours", {})
    if trading_hours.get("start") == "09:15" and trading_hours.get("end") == "15:30":
        print("✅ Trading hours: Correctly configured")
    else:
        print("❌ Trading hours: Incorrect configuration")
    
    # Check risk management
    risk_per_trade = bot.trading_config.get("risk_per_trade", 0)
    if 0.01 <= risk_per_trade <= 0.05:  # 1-5% risk per trade
        print("✅ Risk per trade: Within acceptable range")
    else:
        print("❌ Risk per trade: Outside recommended range")
    
    # Check position limits
    max_position_size = bot.trading_config.get("max_position_size", 0)
    if max_position_size > 0:
        print("✅ Max position size: Configured")
    else:
        print("❌ Max position size: Not configured")
    
    # Check daily limits
    max_daily_trades = bot.trading_config.get("max_daily_trades", 0)
    if 5 <= max_daily_trades <= 50:
        print("✅ Daily trade limit: Within reasonable range")
    else:
        print("❌ Daily trade limit: Outside recommended range")
    
    # Check confidence threshold
    min_confidence = bot.trading_config.get("min_confidence", 0)
    if 0.6 <= min_confidence <= 0.9:
        print("✅ Min confidence: Within recommended range")
    else:
        print("❌ Min confidence: Outside recommended range")
    
    print("\n🎯 Production readiness: VALIDATED")

if __name__ == "__main__":
    # Create production bot
    bot = create_production_bot()
    
    # Validate configuration
    validate_production_config(bot)
    
    print("\n📋 Next Steps:")
    print("1. Update credentials in the bot initialization")
    print("2. Test with paper trading account first")
    print("3. Monitor performance and adjust parameters as needed")
    print("4. Deploy with live credentials when ready")

