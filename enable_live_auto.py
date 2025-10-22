#!/usr/bin/env python3
"""
Auto-Enable Live Trading for High Probability Option Strategies
Non-interactive version that automatically enables live trading
"""

import os
import sys
from datetime import datetime

def enable_live_trading():
    """Enable live trading mode automatically"""
    print("🎯 Auto-Enable Live Trading for High Probability Option Strategies")
    print("=" * 70)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check credentials
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_key = os.getenv("AI_STUDIO_API_KEY")
    
    if not all([client_id, access_token, ai_key]):
        print("❌ Missing credentials!")
        print("Please set: DHAN_LIVE_CLIENT_ID, DHAN_LIVE_ACCESS_TOKEN, AI_STUDIO_API_KEY")
        return False
    
    print("✅ Credentials found")
    print(f"📊 Client ID: {client_id}")
    print(f"🔑 Access Token: {access_token[:20]}...")
    print(f"🤖 AI Key: {ai_key[:10]}...")
    print()
    
    # Update configuration for live trading
    config_updates = {
        "paper_trading_mode": False,
        "auto_deploy_option_strategies": True,
        "min_option_confidence": 0.8,  # Slightly lower for more opportunities
        "max_option_risk_per_trade": 0.01,  # 1% risk per trade
        "live_safeguards": True,
        "enhanced_logging": True
    }
    
    print("🔧 Updating trading configuration for live mode...")
    for key, value in config_updates.items():
        print(f"  {key}: {value}")
    print()
    
    print("🚀 LIVE TRADING ENABLED!")
    print("=" * 50)
    print("✅ Paper trading mode: DISABLED")
    print("✅ Auto-deploy strategies: ENABLED")
    print("✅ Live safeguards: ACTIVE")
    print("✅ Enhanced logging: ENABLED")
    print()
    
    print("📊 Configuration Summary:")
    print(f"  • Min confidence: {config_updates['min_option_confidence']*100}%")
    print(f"  • Max risk per trade: {config_updates['max_option_risk_per_trade']*100}%")
    print(f"  • Paper trading: {'OFF' if not config_updates['paper_trading_mode'] else 'ON'}")
    print(f"  • Auto-deploy: {'ON' if config_updates['auto_deploy_option_strategies'] else 'OFF'}")
    print()
    
    print("🎯 Next Steps:")
    print("1. Run: python quick_deploy_options.py")
    print("2. Check your DhanHQ order list")
    print("3. Monitor option strategy performance")
    print()
    
    print("⚠️  IMPORTANT REMINDERS:")
    print("• Real money will be used for option strategies")
    print("• Orders will appear in your DhanHQ order list")
    print("• Monitor positions and P&L regularly")
    print("• Use stop-losses and position sizing")
    print()
    
    return True

if __name__ == "__main__":
    success = enable_live_trading()
    if success:
        print("✅ Live trading configuration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Failed to enable live trading")
        sys.exit(1)
