#!/usr/bin/env python3
"""
Unit tests for the enhanced risk management features
This provides controlled testing of individual risk management components
"""

import json
import time
import unittest
from datetime import datetime, time as dt_time
from unittest.mock import Mock, patch

from ai_trading_bot import AITradingBot, TradeRecommendation

class TestRiskManagement(unittest.TestCase):
    """Test suite for risk management features"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = AITradingBot(
            client_id="test_client",
            access_token="test_token",
            ai_studio_api_key="test_key"
        )
        
        # Mock available funds
        self.bot.funds_cache = {"timestamp": time.time(), "amount": 100000.0}
        
        # Add some market history
        for i in range(20):
            self.bot.market_history["1333"].append({
                "last_price": 1500 + i * 5,
                "volume": 1000 + i * 50
            })
    
    def test_trade_recommendation_model(self):
        """Test TradeRecommendation dataclass"""
        # Test basic creation
        rec = TradeRecommendation()
        self.assertEqual(rec.action, "HOLD")
        self.assertEqual(rec.confidence, 0.0)
        self.assertFalse(rec.is_actionable())
        
        # Test actionable recommendations
        buy_rec = TradeRecommendation(action="BUY", confidence=0.8, quantity=100)
        self.assertTrue(buy_rec.is_actionable())
        self.assertEqual(buy_rec.action, "BUY")
        
        sell_rec = TradeRecommendation(action="SELL", confidence=0.9, quantity=50)
        self.assertTrue(sell_rec.is_actionable())
        self.assertEqual(sell_rec.action, "SELL")
    
    def test_market_features_calculation(self):
        """Test market feature calculation"""
        market_data = {
            "security_id": "1333",
            "last_price": 1600,
            "volume": 5000,
            "open": 1550,
            "high": 1650,
            "low": 1540
        }
        
        features = self.bot._calculate_market_features("1333", market_data)
        
        # Verify key features are calculated
        self.assertIn("short_ma", features)
        self.assertIn("long_ma", features)
        self.assertIn("momentum_pct", features)
        self.assertIn("intraday_return_pct", features)
        self.assertIn("range_position", features)
        self.assertIn("relative_volume", features)
        self.assertIn("history_depth", features)
        
        # Verify feature values are reasonable
        self.assertGreater(features["history_depth"], 0)
        self.assertGreaterEqual(features["range_position"], 0)
        self.assertLessEqual(features["range_position"], 1)
    
    def test_risk_based_quantity_calculation(self):
        """Test risk-based quantity calculation"""
        market_data = {"last_price": 1000}
        quantity = self.bot._calculate_risk_based_quantity(market_data, 0.05)
        
        # Should calculate based on 2% risk per trade and 5% stop loss
        # Max loss = 100000 * 0.02 = 2000
        # Per share risk = 1000 * 0.05 = 50
        # Expected quantity = 2000 / 50 = 40
        expected_quantity = int((100000 * 0.02) / (1000 * 0.05))
        self.assertEqual(quantity, expected_quantity)
    
    def test_position_quantity_extraction(self):
        """Test position quantity extraction from various formats"""
        test_cases = [
            ({"netQuantity": 100}, 100.0),
            ({"netQty": 50}, 50.0),
            ({"quantity": 25}, 25.0),
            ({"qty": 10}, 10.0),
            (None, 0.0),
            ({}, 0.0)
        ]
        
        for position, expected in test_cases:
            qty = self.bot._extract_net_quantity(position)
            self.assertEqual(qty, expected, f"Expected {expected}, got {qty} for {position}")
    
    def test_trading_hours_validation(self):
        """Test trading hours validation"""
        # Test time parsing
        parsed_time = self.bot._parse_time("09:15")
        self.assertEqual(parsed_time, dt_time(9, 15))
        
        parsed_time = self.bot._parse_time("15:30")
        self.assertEqual(parsed_time, dt_time(15, 30))
        
        # Test invalid time
        parsed_time = self.bot._parse_time("invalid")
        self.assertIsNone(parsed_time)
    
    def test_daily_trade_limits(self):
        """Test daily trade limit enforcement"""
        # Test trade recording
        self.bot._record_trade("1333")
        self.bot._record_trade("1333")
        self.bot._record_trade("11536")
        
        self.assertEqual(self.bot.daily_trade_counts["1333"], 2)
        self.assertEqual(self.bot.daily_trade_counts["11536"], 1)
        self.assertEqual(self.bot.daily_trade_counts["__TOTAL__"], 3)
    
    def test_ai_response_parsing(self):
        """Test AI response parsing and normalization"""
        ai_response = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"action": "BUY", "confidence": 0.85, "quantity": 100, "reasoning": "Strong momentum", "stop_loss": 1500, "take_profit": 1600}'
                    }]
                }
            }]
        }
        
        parsed = self.bot._parse_ai_response(ai_response)
        self.assertEqual(parsed["action"], "BUY")
        self.assertEqual(parsed["confidence"], 0.85)
        self.assertEqual(parsed["quantity"], 100)
        
        # Test normalization
        rec = self.bot._normalize_recommendation(parsed)
        self.assertIsInstance(rec, TradeRecommendation)
        self.assertEqual(rec.action, "BUY")
        self.assertEqual(rec.confidence, 0.85)
        self.assertEqual(rec.quantity, 100)
        self.assertEqual(rec.reasoning, "Strong momentum")
        self.assertEqual(rec.stop_loss, 1500)
        self.assertEqual(rec.take_profit, 1600)
    
    def test_safety_checks(self):
        """Test comprehensive safety checks"""
        # Test low confidence rejection
        rec = TradeRecommendation(action="BUY", confidence=0.5, quantity=100)
        should_execute = self.bot._should_execute_trade(rec, "1333", 100)
        self.assertFalse(should_execute, "Low confidence trade should be rejected")
        
        # Test zero quantity rejection
        rec = TradeRecommendation(action="BUY", confidence=0.8, quantity=0)
        should_execute = self.bot._should_execute_trade(rec, "1333", 0)
        self.assertFalse(should_execute, "Zero quantity trade should be rejected")
    
    def test_enhanced_prompt_generation(self):
        """Test enhanced prompt generation with market features"""
        # Add a mock position
        self.bot.active_positions["1333"] = {"netQuantity": 50, "averagePrice": 1550}
        
        market_data = {
            "security_id": "1333",
            "last_price": 1600,
            "volume": 2000,
            "high": 1650,
            "low": 1550,
            "open": 1580
        }
        
        prompt = self.bot._create_analysis_prompt(market_data)
        
        # Verify prompt contains key elements
        self.assertIn("Current Market Data:", prompt)
        self.assertIn("Computed Market Features:", prompt)
        self.assertIn("Current Position:", prompt)
        self.assertIn("Risk Profile:", prompt)
        self.assertIn("JSON format", prompt)
    
    def test_fund_caching(self):
        """Test fund caching mechanism"""
        # Test cache hit
        funds1 = self.bot._get_available_funds()
        funds2 = self.bot._get_available_funds()
        self.assertEqual(funds1, funds2)  # Should return cached value
        
        # Test cache miss after TTL
        self.bot.funds_cache["timestamp"] = time.time() - 100  # Old timestamp
        with patch.object(self.bot.dhan, 'get_fund_limits') as mock_funds:
            mock_funds.return_value = {
                "status": "success",
                "data": {"availabelBalance": 50000.0}
            }
            funds = self.bot._get_available_funds()
            self.assertEqual(funds, 50000.0)
            mock_funds.assert_called_once()
    
    def test_position_sizing_with_limits(self):
        """Test position sizing with various limits"""
        # Test with position limits
        self.bot.trading_config["max_position_size"] = 50
        
        market_data = {"last_price": 1000}
        recommendation = TradeRecommendation(action="BUY", confidence=0.8, quantity=100)
        
        quantity = self.bot._determine_order_quantity(recommendation, "1333", market_data)
        self.assertLessEqual(quantity, 50)  # Should respect position limit
        
        # Test with existing position
        self.bot.active_positions["1333"] = {"netQuantity": 30}
        quantity = self.bot._determine_order_quantity(recommendation, "1333", market_data)
        self.assertLessEqual(quantity, 20)  # Should respect remaining limit
    
    def test_daily_trade_limit_enforcement(self):
        """Test daily trade limit enforcement"""
        self.bot.trading_config["max_daily_trades"] = 2
        
        # Record 2 trades
        self.bot._record_trade("1333")
        self.bot._record_trade("1333")
        
        # Third trade should be rejected
        rec = TradeRecommendation(action="BUY", confidence=0.8, quantity=100)
        should_execute = self.bot._should_execute_trade(rec, "1333", 100)
        self.assertFalse(should_execute, "Should be rejected due to daily limit")

def run_risk_management_tests():
    """Run all risk management tests"""
    print("🧪 Running Risk Management Unit Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRiskManagement)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 All risk management tests passed!")
        print("\n📋 Risk Management Features Validated:")
        print("✅ TradeRecommendation model")
        print("✅ Market feature calculation")
        print("✅ Risk-based position sizing")
        print("✅ Position quantity extraction")
        print("✅ Trading hours validation")
        print("✅ Daily trade limits")
        print("✅ AI response parsing")
        print("✅ Safety checks")
        print("✅ Enhanced prompt generation")
        print("✅ Fund caching")
        print("✅ Position sizing with limits")
        print("✅ Daily trade limit enforcement")
    else:
        print("\n❌ Some tests failed. Please review the output above.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_risk_management_tests()

