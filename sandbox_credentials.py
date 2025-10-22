#!/usr/bin/env python3
"""
Sandbox Credentials for DhanHQ AI Trading Bot
Use these credentials for testing in sandbox environment
"""

# DhanHQ Sandbox Credentials
DHAN_SANDBOX_CLIENT_ID = "2508041206"
DHAN_SANDBOX_ACCESS_TOKEN = "SANDBOXTOKEN-eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJwYXJ0bmVySWQiOiIiLCJkaGFuQ2xpZW50SWQiOiIyNTA4MDQxMjA2Iiwid2ViaG9va1VybCI6Imh0dHA6Ly8xMjcuMC4wLjE6ODA0MCIsImlzcyI6ImRoYW4iLCJleHAiOjE3NjEwNzAxMzl9.Me4igDNHkq8twutQMs96clGS81Y4CiWfFKO4o6xd7mTG4t0GApoGb_W1OUycWuj6jAGNsr_i_O576s9freudIA"

# AI Studio API Key (you'll need to add your actual AI Studio API key)
AI_STUDIO_API_KEY = "your_ai_studio_api_key_here"

# Sandbox Configuration
SANDBOX_CONFIG = {
    "client_id": DHAN_SANDBOX_CLIENT_ID,
    "access_token": DHAN_SANDBOX_ACCESS_TOKEN,
    "ai_studio_api_key": AI_STUDIO_API_KEY,
    "environment": "sandbox",
    "redirect_url": "http://127.0.0.1:8040"
}

def get_sandbox_credentials():
    """Get sandbox credentials for testing"""
    return SANDBOX_CONFIG

def create_sandbox_bot():
    """Create AI trading bot with sandbox credentials"""
    from ai_trading_bot import AITradingBot
    
    bot = AITradingBot(
        client_id=DHAN_SANDBOX_CLIENT_ID,
        access_token=DHAN_SANDBOX_ACCESS_TOKEN,
        ai_studio_api_key=AI_STUDIO_API_KEY
    )
    
    # Configure for sandbox testing
    bot.trading_config.update({
        "min_confidence": 0.7,
        "max_position_size": 100,  # Smaller size for sandbox
        "risk_per_trade": 0.01,    # 1% risk for sandbox
        "max_daily_trades": 5,     # Fewer trades for sandbox
        "trading_hours": {"start": "09:15", "end": "15:30"},
        "update_interval": 10,     # Slower updates for sandbox
        "funds_cache_ttl": 120,    # Longer cache for sandbox
        "lookback_ticks": 60,      # Shorter history for sandbox
        "allow_short_selling": False
    })
    
    print("🚀 Sandbox AI Trading Bot Created")
    print("=" * 50)
    print(f"✅ Client ID: {DHAN_SANDBOX_CLIENT_ID}")
    print(f"✅ Access Token: {DHAN_SANDBOX_ACCESS_TOKEN[:20]}...")
    print(f"✅ Environment: Sandbox")
    print(f"✅ Redirect URL: http://127.0.0.1:8040")
    print(f"⚠️  AI Studio API Key: {AI_STUDIO_API_KEY}")
    
    return bot

if __name__ == "__main__":
    # Test sandbox bot creation
    try:
        bot = create_sandbox_bot()
        print("\n🎉 Sandbox bot created successfully!")
        print("\n📋 Next Steps:")
        print("1. Add your AI Studio API key")
        print("2. Test with sandbox credentials")
        print("3. Run market hours test during 09:15-15:30 IST")
    except Exception as e:
        print(f"❌ Error creating sandbox bot: {e}")



