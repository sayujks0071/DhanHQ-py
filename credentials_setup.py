#!/usr/bin/env python3
"""
Credentials Setup for Production Trading Bot
Secure credential management for live deployment
"""

import os
from ai_trading_bot import AITradingBot, TradeRecommendation

class CredentialManager:
    """Secure credential management for production deployment"""
    
    def __init__(self):
        self.credentials = {}
        self.load_credentials()
    
    def load_credentials(self):
        """Load credentials from environment variables or .env file"""
        self.credentials = {
            "client_id": os.getenv("DHAN_CLIENT_ID"),
            "access_token": os.getenv("DHAN_ACCESS_TOKEN"),
            "ai_studio_api_key": os.getenv("AI_STUDIO_API_KEY")
        }
    
    def validate_credentials(self):
        """Validate that all required credentials are present"""
        required_credentials = ["client_id", "access_token", "ai_studio_api_key"]
        missing_credentials = []
        
        for cred in required_credentials:
            if not self.credentials.get(cred):
                missing_credentials.append(cred)
        
        if missing_credentials:
            print("❌ Missing credentials:")
            for cred in missing_credentials:
                print(f"  - {cred}")
            return False
        
        print("✅ All credentials loaded successfully")
        return True
    
    def get_credentials(self):
        """Get validated credentials"""
        if self.validate_credentials():
            return self.credentials
        return None

def create_production_bot_with_credentials():
    """Create production bot with real credentials"""
    print("🔐 Setting up Production Trading Bot with Credentials")
    print("=" * 60)
    
    # Load credentials
    cred_manager = CredentialManager()
    credentials = cred_manager.get_credentials()
    
    if not credentials:
        print("\n❌ Credential setup failed!")
        print("\n📋 To set up credentials:")
        print("1. Create a .env file in the project root")
        print("2. Add your credentials:")
        print("   DHAN_CLIENT_ID=your_actual_client_id")
        print("   DHAN_ACCESS_TOKEN=your_actual_access_token")
        print("   AI_STUDIO_API_KEY=your_actual_ai_studio_api_key")
        print("3. Run this script again")
        return None
    
    # Create production bot with credentials
    bot = AITradingBot(
        client_id=credentials["client_id"],
        access_token=credentials["access_token"],
        ai_studio_api_key=credentials["ai_studio_api_key"]
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
    
    # Ensure all testing overrides are disabled
    if hasattr(bot, 'override_trading_hours'):
        bot.override_trading_hours = False
    if hasattr(bot, 'dry_run_mode'):
        bot.dry_run_mode = False
    if hasattr(bot, 'test_mode'):
        bot.test_mode = False
    
    print("✅ Production bot created with real credentials")
    print("✅ All testing overrides disabled")
    print("✅ Trading hours enforcement enabled")
    
    return bot

def test_credentials_connection(bot):
    """Test connection with real credentials"""
    print("\n🔍 Testing Credential Connection")
    print("=" * 40)
    
    try:
        # Test DhanHQ connection
        print("Testing DhanHQ connection...")
        funds = bot._get_available_funds()
        if funds is not None:
            print(f"✅ DhanHQ connection successful - Available funds: ₹{funds:,.2f}")
        else:
            print("⚠️  DhanHQ connection - No funds data (may be normal for new accounts)")
        
        # Test AI Studio connection (mock test)
        print("Testing AI Studio connection...")
        # Note: We don't actually call AI Studio here to avoid API costs
        print("✅ AI Studio credentials loaded (connection test skipped)")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def market_hours_test(bot):
    """Test during market hours to confirm trades execute"""
    print("\n🕐 Market Hours Test")
    print("=" * 40)
    
    from datetime import datetime, time as dt_time
    
    current_time = datetime.now().time()
    trading_start = dt_time(9, 15)
    trading_end = dt_time(15, 30)
    
    print(f"Current time: {current_time.strftime('%H:%M:%S')}")
    print(f"Trading hours: {trading_start.strftime('%H:%M')} - {trading_end.strftime('%H:%M')}")
    
    within_trading_hours = bot._within_trading_hours()
    print(f"Within trading hours: {within_trading_hours}")
    
    if within_trading_hours:
        print("✅ Market is open - trades will execute if conditions are met")
        
        # Test with sample market data
        sample_market_data = {
            "security_id": "1333",
            "last_price": 1650.50,
            "volume": 45000,
            "high": 1665.00,
            "low": 1645.00,
            "open": 1655.00
        }
        
        # Test percentage stop-loss
        rec = TradeRecommendation(
            action="BUY",
            confidence=0.8,
            quantity=0,
            stop_loss=0.05  # 5% percentage
        )
        
        quantity = bot._determine_order_quantity(rec, "1333", sample_market_data)
        should_execute = bot._should_execute_trade(rec, "1333", quantity)
        
        print(f"Sample trade test:")
        print(f"  Quantity: {quantity}")
        print(f"  Should execute: {should_execute}")
        
    else:
        print("⏰ Market is closed - trades will be blocked until 09:15 AM")
        print("   Run this script during market hours (09:15-15:30) to test trade execution")

def main():
    """Main credential setup and testing function"""
    print("🚀 Enhanced AI Trading Bot - Credential Setup")
    print("=" * 60)
    
    try:
        # Create production bot with credentials
        bot = create_production_bot_with_credentials()
        
        if not bot:
            return
        
        # Test credential connection
        if test_credentials_connection(bot):
            print("\n✅ Credential connection successful!")
            
            # Test market hours behavior
            market_hours_test(bot)
            
            print("\n🎯 Ready for Market Hours Testing:")
            print("1. Run this script during market hours (09:15-15:30)")
            print("2. Monitor trade execution behavior")
            print("3. Validate risk management and safety mechanisms")
            print("4. Deploy with live trading when ready")
            
        else:
            print("\n❌ Credential connection failed!")
            print("Please check your credentials and try again.")
            
    except Exception as e:
        print(f"❌ Credential setup failed: {e}")
        raise

if __name__ == "__main__":
    main()



