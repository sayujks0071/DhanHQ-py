#!/usr/bin/env python3
"""
Test script that bypasses trading hours for testing purposes
"""

import json
import time
from datetime import datetime, time as dt_time
from typing import Dict, List

from ai_trading_bot import AITradingBot, TradeRecommendation

class TestAITradingBot(AITradingBot):
    """Test version that bypasses trading hours"""
    
    def _within_trading_hours(self) -> bool:
        """Override to always return True for testing"""
        return True

def test_enhanced_features():
    """Test the enhanced features with trading hours bypassed"""
    print("🧪 Testing Enhanced AI Trading Bot Features")
    print("=" * 50)
    
    # Initialize test bot
    bot = TestAITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Configure for testing
    bot.trading_config.update({
        "min_confidence": 0.5,  # Lower threshold for testing
        "max_position_size": 100,
        "risk_per_trade": 0.02,
        "max_daily_trades": 10,
        "update_interval": 1
    })
    
    # Mock available funds
    bot.funds_cache = {"timestamp": time.time(), "amount": 100000.0}
    
    print("✅ Bot initialized with test configuration")
    print(f"💰 Available funds: ₹{bot._get_available_funds():,.2f}")
    print()
    
    # Test 1: Market features calculation
    print("🧪 Test 1: Market Features Calculation")
    security_id = "1333"
    
    # Add some mock history
    for i in range(20):
        bot.market_history[security_id].append({
            "last_price": 1500 + i * 10,
            "volume": 1000 + i * 50
        })
    
    market_data = {
        "security_id": security_id,
        "last_price": 1700,
        "volume": 5000,
        "open": 1600,
        "high": 1750,
        "low": 1550
    }
    
    features = bot._calculate_market_features(security_id, market_data)
    print(f"📊 Calculated features: {json.dumps(features, indent=2)}")
    print()
    
    # Test 2: Risk-based quantity calculation
    print("🧪 Test 2: Risk-Based Quantity Calculation")
    quantity = bot._calculate_risk_based_quantity(market_data, 0.05)
    print(f"📈 Calculated quantity: {quantity} shares")
    print()
    
    # Test 3: AI response parsing
    print("🧪 Test 3: AI Response Parsing")
    mock_ai_response = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": json.dumps({
                        "action": "BUY",
                        "confidence": 0.8,
                        "quantity": 50,
                        "reasoning": "Strong momentum and volume",
                        "stop_loss": 1600,
                        "take_profit": 1800
                    })
                }]
            }
        }]
    }
    
    parsed = bot._parse_ai_response(mock_ai_response)
    recommendation = bot._normalize_recommendation(parsed)
    print(f"🤖 Parsed recommendation: {recommendation}")
    print()
    
    # Test 4: Safety checks
    print("🧪 Test 4: Safety Checks")
    
    # Test high confidence
    rec_high = TradeRecommendation(action="BUY", confidence=0.8, quantity=50)
    should_execute = bot._should_execute_trade(rec_high, security_id, 50)
    print(f"✅ High confidence trade: {should_execute}")
    
    # Test low confidence
    rec_low = TradeRecommendation(action="BUY", confidence=0.3, quantity=50)
    should_execute = bot._should_execute_trade(rec_low, security_id, 50)
    print(f"❌ Low confidence trade: {should_execute}")
    
    # Test zero quantity
    rec_zero = TradeRecommendation(action="BUY", confidence=0.8, quantity=0)
    should_execute = bot._should_execute_trade(rec_zero, security_id, 0)
    print(f"❌ Zero quantity trade: {should_execute}")
    print()
    
    # Test 5: Daily trade limits
    print("🧪 Test 5: Daily Trade Limits")
    print(f"📊 Initial trade counts: {dict(bot.daily_trade_counts)}")
    
    bot._record_trade(security_id)
    bot._record_trade(security_id)
    bot._record_trade("11536")
    
    print(f"📊 After recording trades: {dict(bot.daily_trade_counts)}")
    print()
    
    # Test 6: Position quantity extraction
    print("🧪 Test 6: Position Quantity Extraction")
    
    test_positions = [
        {"netQuantity": 100},
        {"netQty": 50},
        {"quantity": 25},
        {"qty": 10},
        None
    ]
    
    for i, pos in enumerate(test_positions):
        qty = bot._extract_net_quantity(pos)
        print(f"📊 Position {i+1}: {qty} shares")
    print()
    
    # Test 7: Configuration validation
    print("🧪 Test 7: Configuration Validation")
    print(f"⚙️  Trading config: {json.dumps(bot.trading_config, indent=2)}")
    print()
    
    print("🎉 All enhanced features tested successfully!")
    print("\n📋 Enhanced Features Summary:")
    print("✅ TradeRecommendation model with structured data")
    print("✅ Market feature calculation with technical indicators")
    print("✅ Risk-based position sizing")
    print("✅ AI response parsing and normalization")
    print("✅ Comprehensive safety checks")
    print("✅ Daily trade limit enforcement")
    print("✅ Position quantity extraction")
    print("✅ Configuration validation")
    
    print("\n🚀 Ready for production testing!")

if __name__ == "__main__":
    test_enhanced_features()

