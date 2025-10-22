#!/usr/bin/env python3
"""
Unit tests for the OptionStrategyAnalyzer module.
"""

import unittest
from typing import Dict

from ai_option_strategies import OptionStrategyAnalyzer


class DummyDhan:
    """Small stub of the Dhan client returning deterministic historical data."""

    NSE_FNO = "NSE_FNO"
    NSE = "NSE_EQ"

    def historical_daily_data(
        self,
        security_id: str,
        exchange_segment: str,
        instrument_type: str,
        from_date: str,
        to_date: str,
    ) -> Dict:
        candles = []
        base = 1500.0 if security_id == "BULLISH" else 1200.0
        for idx in range(10):
            price = base + idx * (2 if security_id == "BULLISH" else (-2 if security_id == "BEARISH" else 0))
            candles.append([0, price - 5, price + 5, price - 10, price, 1000 + idx * 50])
        return {"status": "success", "data": {"candles": candles}}


class OptionStrategyAnalyzerTest(unittest.TestCase):
    """Validate strategy selection heuristics."""

    def setUp(self):
        self.logger_messages = []

        class Logger:
            def info(inner_self, msg, *args):
                self.logger_messages.append(msg % args if args else msg)

            def debug(inner_self, msg, *args):
                pass

            def error(inner_self, msg, *args):
                self.logger_messages.append(msg % args if args else msg)

        self.analyzer = OptionStrategyAnalyzer(
            DummyDhan(),
            Logger(),
            exchange_segment="NSE_FNO",
            instrument_type="EQUITY",
        )

    def test_bullish_environment_prefers_bullish_strategy(self):
        """Assert that bullish conditions surface a bullish strategy."""
        snapshot = {
            "last_price": 1650,
            "open": 1600,
            "high": 1660,
            "low": 1595,
            "volume": 150000,
        }
        history = [{"last_price": 1500 + i * 10, "volume": 100000 + i * 1000} for i in range(10)]
        recommendation = self.analyzer.select_best_strategy(
            "BULLISH",
            snapshot,
            market_history=history,
            position={"netQuantity": 100},
        )
        self.assertIsNotNone(recommendation)
        self.assertGreater(recommendation.score, 0)
        bearish_strategies = {"Bear Put Spread", "Bear Call Spread"}
        self.assertNotIn(
            recommendation.name,
            bearish_strategies,
            f"Bullish regime should not prefer bearish strategy {recommendation.name}",
        )
        self.assertGreaterEqual(len(recommendation.legs), 1)

    def test_range_bound_environment_prefers_neutral_strategy(self):
        """Neutral market conditions should favour iron structures."""
        snapshot = {
            "last_price": 1500,
            "open": 1505,
            "high": 1510,
            "low": 1495,
            "volume": 90000,
        }
        # Flat history to mimic range-bound market
        history = [{"last_price": 1500 + ((-1) ** i), "volume": 85000} for i in range(12)]
        ranked = self.analyzer.rank_strategies(
            "NEUTRAL",
            snapshot,
            market_history=history,
            position=None,
        )
        top_three = {rec.name for rec in ranked[:3]}
        self.assertTrue(
            {"Iron Condor", "Iron Butterfly"} & top_three,
            f"Neutral regime expected iron strategies in top picks, found {top_three}",
        )

    def test_rank_strategies_returns_sorted_results(self):
        """Ensure rank_strategies provides a sorted list."""
        snapshot = {
            "last_price": 1300,
            "open": 1310,
            "high": 1325,
            "low": 1290,
            "volume": 110000,
        }
        history = [{"last_price": 1300 + i * 5, "volume": 105000} for i in range(8)]
        ranked = self.analyzer.rank_strategies(
            "BULLISH",
            snapshot,
            market_history=history,
            position={"netQuantity": 50},
        )
        self.assertGreaterEqual(len(ranked), 5)
        scores = [rec.score for rec in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
