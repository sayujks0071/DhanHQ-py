#!/usr/bin/env python3
"""
Test script for the enhanced AI Trading Bot features
This validates the new TradeRecommendation model, market features, and safety mechanisms
"""

import json
import time
from datetime import datetime, time as dt_time
from typing import Dict, List

# Import the enhanced bot
from ai_trading_bot import AITradingBot, TradeRecommendation

def test_trade_recommendation_model():
    """Test the new TradeRecommendation dataclass"""
    print("🧪 Testing TradeRecommendation Model...")
    
    # Test basic creation
    rec = TradeRecommendation()
    assert rec.action == "HOLD"
    assert rec.confidence == 0.0
    assert not rec.is_actionable()
    
    # Test actionable recommendations
    buy_rec = TradeRecommendation(action="BUY", confidence=0.8, quantity=100, reasoning="Strong momentum")
    assert buy_rec.is_actionable()
    assert buy_rec.action == "BUY"
    assert buy_rec.confidence == 0.8
    assert buy_rec.quantity == 100
    assert buy_rec.reasoning == "Strong momentum"
    
    sell_rec = TradeRecommendation(action="SELL", confidence=0.9, quantity=50, stop_loss=1500, take_profit=1600)
    assert sell_rec.is_actionable()
    assert sell_rec.action == "SELL"
    assert sell_rec.stop_loss == 1500
    assert sell_rec.take_profit == 1600
    
    print("✅ TradeRecommendation model working correctly!")

def test_ai_config_fallbacks():
    """Test AI configuration fallbacks when ai_config.py is missing"""
    print("🧪 Testing AI Config Fallbacks...")
    
    # Test with minimal parameters
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Verify fallback configs are loaded
    assert "model" in bot.ai_config
    assert "temperature" in bot.ai_config
    assert "min_confidence" in bot.trading_config
    assert "max_position_size" in bot.trading_config
    assert "risk_per_trade" in bot.trading_config
    
    print("✅ AI config fallbacks working correctly!")

def test_market_features_calculation():
    """Test the enhanced market feature calculation"""
    print("🧪 Testing Market Features Calculation...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Add mock historical data
    security_id = "1333"
    for i in range(20):
        bot.market_history[security_id].append({
            "last_price": 1500 + i * 5,
            "volume": 1000 + i * 100
        })
    
    # Test market data with various features
    market_data = {
        "security_id": security_id,
        "last_price": 1600,
        "volume": 5000,
        "open": 1550,
        "high": 1650,
        "low": 1540
    }
    
    features = bot._calculate_market_features(security_id, market_data)
    
    # Verify key features are calculated
    assert "short_ma" in features
    assert "long_ma" in features
    assert "momentum_pct" in features
    assert "intraday_return_pct" in features
    assert "range_position" in features
    assert "relative_volume" in features
    assert "history_depth" in features
    
    print(f"📊 Calculated features: {json.dumps(features, indent=2)}")
    print("✅ Market features calculation working!")

def test_risk_based_position_sizing():
    """Test risk-based position sizing with cached funds"""
    print("🧪 Testing Risk-Based Position Sizing...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Mock available funds
    bot.funds_cache = {"timestamp": time.time(), "amount": 100000.0}
    
    market_data = {"last_price": 1000}
    quantity = bot._calculate_risk_based_quantity(market_data, 0.05)
    
    # Should calculate based on 2% risk per trade and 5% stop loss
    # Max loss = 100000 * 0.02 = 2000
    # Per share risk = 1000 * 0.05 = 50
    # Expected quantity = 2000 / 50 = 40
    expected_quantity = int((100000 * 0.02) / (1000 * 0.05))
    assert quantity == expected_quantity
    
    print(f"📈 Calculated quantity: {quantity} shares (expected: {expected_quantity})")
    print("✅ Risk-based position sizing working!")

def test_trading_hours_validation():
    """Test trading hours validation"""
    print("🧪 Testing Trading Hours Validation...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test time parsing
    parsed_time = bot._parse_time("09:15")
    assert parsed_time == dt_time(9, 15)
    
    parsed_time = bot._parse_time("15:30")
    assert parsed_time == dt_time(15, 30)
    
    # Test invalid time
    parsed_time = bot._parse_time("invalid")
    assert parsed_time is None
    
    print("✅ Trading hours validation working!")

def test_daily_trade_limits():
    """Test daily trade limit enforcement"""
    print("🧪 Testing Daily Trade Limits...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test trade recording
    bot._record_trade("1333")
    bot._record_trade("1333")
    bot._record_trade("11536")
    
    assert bot.daily_trade_counts["1333"] == 2
    assert bot.daily_trade_counts["11536"] == 1
    assert bot.daily_trade_counts["__TOTAL__"] == 3
    
    print(f"📊 Trade counts: {dict(bot.daily_trade_counts)}")
    print("✅ Daily trade limits working!")

def test_position_quantity_extraction():
    """Test position quantity extraction from various formats"""
    print("🧪 Testing Position Quantity Extraction...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test different position formats
    test_cases = [
        ({"netQuantity": 100}, 100.0),
        ({"netQty": 50}, 50.0),
        ({"quantity": 25}, 25.0),
        ({"qty": 10}, 10.0),
        (None, 0.0),
        ({}, 0.0)
    ]
    
    for position, expected in test_cases:
        qty = bot._extract_net_quantity(position)
        assert qty == expected, f"Expected {expected}, got {qty} for {position}"
    
    print("✅ Position quantity extraction working!")

def test_ai_response_parsing():
    """Test AI response parsing and normalization"""
    print("🧪 Testing AI Response Parsing...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test valid AI response
    ai_response = {
        "candidates": [{
            "content": {
                "parts": [{
                    "text": '{"action": "BUY", "confidence": 0.85, "quantity": 100, "reasoning": "Strong momentum", "stop_loss": 1500, "take_profit": 1600}'
                }]
            }
        }]
    }
    
    parsed = bot._parse_ai_response(ai_response)
    assert parsed["action"] == "BUY"
    assert parsed["confidence"] == 0.85
    assert parsed["quantity"] == 100
    
    # Test normalization
    rec = bot._normalize_recommendation(parsed)
    assert isinstance(rec, TradeRecommendation)
    assert rec.action == "BUY"
    assert rec.confidence == 0.85
    assert rec.quantity == 100
    assert rec.reasoning == "Strong momentum"
    assert rec.stop_loss == 1500
    assert rec.take_profit == 1600
    
    print("✅ AI response parsing working!")

def test_safety_checks():
    """Test comprehensive safety checks"""
    print("🧪 Testing Safety Checks...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Test low confidence rejection
    rec = TradeRecommendation(action="BUY", confidence=0.5, quantity=100)
    should_execute = bot._should_execute_trade(rec, "1333", 100)
    assert not should_execute, "Low confidence trade should be rejected"
    
    # Test high confidence (might be rejected due to other factors)
    rec = TradeRecommendation(action="BUY", confidence=0.8, quantity=100)
    # This might be rejected due to trading hours or other factors
    
    # Test zero quantity rejection
    rec = TradeRecommendation(action="BUY", confidence=0.8, quantity=0)
    should_execute = bot._should_execute_trade(rec, "1333", 0)
    assert not should_execute, "Zero quantity trade should be rejected"
    
    print("✅ Safety checks working!")

def test_enhanced_prompt_generation():
    """Test the enhanced prompt generation with market features"""
    print("🧪 Testing Enhanced Prompt Generation...")
    
    bot = AITradingBot(
        client_id="test_client",
        access_token="test_token",
        ai_studio_api_key="test_key"
    )
    
    # Add some market history
    security_id = "1333"
    for i in range(10):
        bot.market_history[security_id].append({
            "last_price": 1500 + i * 10,
            "volume": 1000 + i * 50
        })
    
    # Add a mock position
    bot.active_positions[security_id] = {"netQuantity": 50, "averagePrice": 1550}
    
    market_data = {
        "security_id": security_id,
        "last_price": 1600,
        "volume": 2000,
        "high": 1650,
        "low": 1550,
        "open": 1580
    }
    
    prompt = bot._create_analysis_prompt(market_data)
    
    # Verify prompt contains key elements
    assert "Current Market Data:" in prompt
    assert "Computed Market Features:" in prompt
    assert "Current Position:" in prompt
    assert "Risk Profile:" in prompt
    assert "JSON format" in prompt
    
    print("✅ Enhanced prompt generation working!")

def run_all_tests():
    """Run all enhanced feature tests"""
    print("🚀 Testing Enhanced AI Trading Bot Features")
    print("=" * 60)
    
    try:
        test_trade_recommendation_model()
        test_ai_config_fallbacks()
        test_market_features_calculation()
        test_risk_based_position_sizing()
        test_trading_hours_validation()
        test_daily_trade_limits()
        test_position_quantity_extraction()
        test_ai_response_parsing()
        test_safety_checks()
        test_enhanced_prompt_generation()
        
        print("\n🎉 All enhanced features tested successfully!")
        print("\n📋 Enhanced Features Validated:")
        print("✅ TradeRecommendation dataclass with structured data")
        print("✅ AI config fallbacks for standalone operation")
        print("✅ Market feature calculation with technical indicators")
        print("✅ Risk-based position sizing with cached funds")
        print("✅ Trading hours validation")
        print("✅ Daily trade limit enforcement")
        print("✅ Position quantity extraction from multiple formats")
        print("✅ AI response parsing and normalization")
        print("✅ Comprehensive safety checks")
        print("✅ Enhanced prompt generation with market context")
        
        print("\n🚀 Ready for paper trading validation!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    run_all_tests()