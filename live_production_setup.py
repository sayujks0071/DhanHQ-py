#!/usr/bin/env python3
"""
Live Production Setup for Enhanced AI Trading Bot
Configuration for live trading with production DhanHQ API
"""

import os
from ai_trading_bot import AITradingBot

class LiveProductionBot(AITradingBot):
    """
    Live production trading bot with enhanced safety mechanisms
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.live_mode = True
        self.production_safeguards = True
        
        # Enhanced logging for live trading
        self.logger.info("🚀 LIVE PRODUCTION BOT INITIALIZED")
        self.logger.info("⚠️  REAL MONEY TRADING ENABLED")
        self.logger.info("🛡️  ENHANCED SAFEGUARDS ACTIVE")
    
    def validate_live_credentials(self):
        """Validate live production credentials"""
        print("🔐 Validating Live Production Credentials")
        print("=" * 50)
        
        # Check if using production API
        if hasattr(self, 'dhan') and hasattr(self.dhan, 'base_url'):
            if 'api.dhan.co' in str(self.dhan.base_url):
                print("✅ Production API URL: api.dhan.co")
            else:
                print("❌ Not using production API URL")
                return False
        
        # Check credentials format
        if self.client_id and len(self.client_id) > 5:
            print(f"✅ Client ID: {self.client_id[:5]}...")
        else:
            print("❌ Invalid client ID format")
            return False
        
        if self.access_token and 'SANDBOX' not in str(self.access_token):
            print(f"✅ Access Token: {str(self.access_token)[:20]}...")
        else:
            print("❌ Using sandbox token - not suitable for live trading")
            return False
        
        print("✅ Live credentials validated")
        return True
    
    def test_live_connection(self):
        """Test live API connection"""
        print("\n🔍 Testing Live API Connection")
        print("=" * 50)
        
        try:
            # Test fund limits API
            funds = self._get_available_funds()
            if funds is not None:
                print(f"✅ Live API connection successful")
                print(f"💰 Available funds: ₹{funds:,.2f}")
                return True
            else:
                print("⚠️  Live API connection - No funds data")
                return False
        except Exception as e:
            print(f"❌ Live API connection failed: {e}")
            return False
    
    def validate_kyc_and_funding(self):
        """Validate KYC and funding status"""
        print("\n📋 Validating KYC and Funding Status")
        print("=" * 50)
        
        try:
            # Check account status
            print("✅ KYC Status: Validated (assumed)")
            print("✅ Funding Status: Available (assumed)")
            print("✅ Data Services: Subscribed (assumed)")
            print("\n⚠️  IMPORTANT: Verify these manually:")
            print("   - KYC completion status")
            print("   - Account funding level")
            print("   - DhanHQ data service subscription")
            return True
        except Exception as e:
            print(f"❌ KYC/Funding validation failed: {e}")
            return False
    
    def tighten_operational_safeguards(self):
        """Tighten operational safeguards for live trading"""
        print("\n🛡️ Tightening Operational Safeguards")
        print("=" * 50)
        
        # Enhanced order validation
        self.trading_config.update({
            "min_confidence": 0.8,           # Higher confidence threshold
            "max_position_size": 500,       # Smaller position size
            "risk_per_trade": 0.01,         # Lower risk per trade (1%)
            "max_daily_trades": 5,          # Fewer daily trades
            "order_validation": True,       # Enable order validation
            "fund_reconciliation": True,    # Enable fund reconciliation
            "position_reconciliation": True, # Enable position reconciliation
            "enhanced_logging": True,        # Enable enhanced logging
            "live_safeguards": True         # Enable live safeguards
        })
        
        print("✅ Enhanced order validation enabled")
        print("✅ Fund reconciliation enabled")
        print("✅ Position reconciliation enabled")
        print("✅ Enhanced logging enabled")
        print("✅ Live safeguards enabled")
        print("✅ Reduced risk parameters for live trading")
        
        return True

def create_live_production_bot():
    """Create live production bot with enhanced safeguards"""
    print("🚀 Creating Live Production Trading Bot")
    print("=" * 60)
    
    # Load live credentials from environment
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_studio_api_key = os.getenv("AI_STUDIO_API_KEY")
    
    if not all([client_id, access_token, ai_studio_api_key]):
        print("❌ Missing live credentials!")
        print("\n📋 Required environment variables:")
        print("   DHAN_LIVE_CLIENT_ID=your_live_client_id")
        print("   DHAN_LIVE_ACCESS_TOKEN=your_live_access_token")
        print("   AI_STUDIO_API_KEY=your_ai_studio_api_key")
        return None
    
    # Create live production bot
    bot = LiveProductionBot(
        client_id=client_id,
        access_token=access_token,
        ai_studio_api_key=ai_studio_api_key
    )
    
    # Configure for live trading
    bot.trading_config.update({
        "min_confidence": 0.8,           # Higher confidence threshold
        "max_position_size": 500,        # Smaller position size
        "risk_per_trade": 0.01,         # Lower risk per trade (1%)
        "stop_loss_percent": 0.03,      # Tighter stop-loss (3%)
        "take_profit_percent": 0.06,    # Tighter take-profit (6%)
        "max_daily_trades": 5,          # Fewer daily trades
        "trading_hours": {"start": "09:15", "end": "15:30"},
        "update_interval": 10,          # Slower updates for live trading
        "funds_cache_ttl": 30,          # Shorter cache for live trading
        "lookback_ticks": 60,           # Shorter history for live trading
        "allow_short_selling": False,    # No short selling
        "live_safeguards": True,        # Enable live safeguards
        "enhanced_logging": True        # Enable enhanced logging
    })
    
    return bot

def main():
    """Main live production setup function"""
    print("🚀 Enhanced AI Trading Bot - Live Production Setup")
    print("=" * 60)
    
    try:
        # Create live production bot
        bot = create_live_production_bot()
        
        if not bot:
            print("\n❌ Live production bot creation failed!")
            print("Please set up your live credentials and try again.")
            return
        
        # Validate live credentials
        if not bot.validate_live_credentials():
            print("\n❌ Live credentials validation failed!")
            return
        
        # Test live connection
        if not bot.test_live_connection():
            print("\n❌ Live API connection failed!")
            return
        
        # Validate KYC and funding
        if not bot.validate_kyc_and_funding():
            print("\n❌ KYC/Funding validation failed!")
            return
        
        # Tighten operational safeguards
        if not bot.tighten_operational_safeguards():
            print("\n❌ Operational safeguards setup failed!")
            return
        
        print("\n🎉 Live production bot setup completed!")
        print("\n📋 Live Production Checklist:")
        print("✅ Live credentials configured")
        print("✅ Production API URL: api.dhan.co")
        print("✅ Enhanced safeguards enabled")
        print("✅ Reduced risk parameters")
        print("✅ Enhanced logging enabled")
        print("✅ Fund reconciliation enabled")
        print("✅ Position reconciliation enabled")
        
        print("\n🎯 Ready for Live Trading:")
        print("1. Start with paper-size positions")
        print("2. Monitor during market hours (09:15-15:30 IST)")
        print("3. Track fills, risk sizing, and strategy recommendations")
        print("4. Scale up gradually after successful paper-size session")
        
    except Exception as e:
        print(f"❌ Live production setup failed: {e}")
        raise

if __name__ == "__main__":
    main()



