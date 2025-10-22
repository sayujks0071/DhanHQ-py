#!/usr/bin/env python3
"""
Example AI Trading Bot Usage
This script demonstrates how to use the AI trading bot
"""

import os
from dotenv import load_dotenv
from ai_trading_bot import AITradingBot

def main():
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    client_id = os.getenv('DHAN_CLIENT_ID')
    access_token = os.getenv('DHAN_ACCESS_TOKEN')
    ai_api_key = os.getenv('AI_STUDIO_API_KEY')
    
    if not all([client_id, access_token, ai_api_key]):
        print("❌ Please set your credentials in the .env file")
        print("Edit .env file and add your:")
        print("- DHAN_CLIENT_ID")
        print("- DHAN_ACCESS_TOKEN") 
        print("- AI_STUDIO_API_KEY")
        return
    
    # Initialize AI Trading Bot
    print("🤖 Initializing AI Trading Bot...")
    bot = AITradingBot(client_id, access_token, ai_api_key)
    
    # Example securities to trade
    securities = ["1333", "11536", "288"]  # HDFC Bank, Reliance, TCS
    
    print(f"📊 Starting AI trading for securities: {securities}")
    print("⚠️  This is a demo - no real trades will be executed")
    
    # Run trading bot (in demo mode)
    try:
        bot.run_ai_trading_loop(securities)
    except KeyboardInterrupt:
        print("\n🛑 Trading bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
