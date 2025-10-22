"""
Option Strategy Analyzer for the AI Trading Bot
Chooses among multiple predefined option strategies using market and historical data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass
class StrategyLeg:
    """Describes a single leg of an option strategy."""

    action: str  # BUY or SELL
    option_type: str  # CALL or PUT
    moneyness: str  # ITM / ATM / OTM
    quantity: int
    notes: str = ""


@dataclass
class StrategyRecommendation:
    """Represents the outcome of a strategy evaluation."""

    name: str
    score: float
    rationale: str
    risk_profile: str
    legs: List[StrategyLeg] = field(default_factory=list)
    expected_move: Optional[str] = None
    confidence: float = 0.0
    diagnostics: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> Dict:
        """Return a JSON-serialisable representation."""
        return {
            "name": self.name,
            "score": round(self.score, 4),
            "confidence": round(self.confidence, 4),
            "risk_profile": self.risk_profile,
            "expected_move": self.expected_move,
            "rationale": self.rationale,
            "legs": [leg.__dict__ for leg in self.legs],
            "diagnostics": {k: round(v, 4) for k, v in self.diagnostics.items()},
        }


class OptionStrategyAnalyzer:
    """
    Analyze market conditions and pick one of the predefined option strategies.

    The class relies on lightweight quantitative features derived from live market data
    and (if available) recent historical candles fetched through the DhanHQ SDK.
    """

    # Strategy registry: (name, risk_profile, description, default legs)
    _STRATEGIES: Tuple[Dict, ...] = (
        {
            "name": "Covered Call",
            "risk_profile": "Moderate",
            "bias": "bullish",
            "legs": [
                StrategyLeg("HOLD", "STOCK", "LONG", 1, "Existing long equity position"),
                StrategyLeg("SELL", "CALL", "OTM", 1, "Write 1 OTM call for income"),
            ],
        },
        {
            "name": "Protective Put",
            "risk_profile": "Moderate",
            "bias": "bullish_risk_off",
            "legs": [
                StrategyLeg("HOLD", "STOCK", "LONG", 1, "Maintain long equity exposure"),
                StrategyLeg("BUY", "PUT", "ATM", 1, "Buy ATM put as insurance"),
            ],
        },
        {
            "name": "Bull Call Spread",
            "risk_profile": "Moderate",
            "bias": "bullish",
            "legs": [
                StrategyLeg("BUY", "CALL", "ATM", 1, "Buy ATM call"),
                StrategyLeg("SELL", "CALL", "OTM", 1, "Sell higher strike call"),
            ],
        },
        {
            "name": "Bear Put Spread",
            "risk_profile": "Moderate",
            "bias": "bearish",
            "legs": [
                StrategyLeg("BUY", "PUT", "ATM", 1, "Buy ATM put"),
                StrategyLeg("SELL", "PUT", "OTM", 1, "Sell lower strike put"),
            ],
        },
        {
            "name": "Bull Put Spread",
            "risk_profile": "Moderate",
            "bias": "bullish_income",
            "legs": [
                StrategyLeg("SELL", "PUT", "OTM", 1, "Sell OTM put to collect premium"),
                StrategyLeg("BUY", "PUT", "lower_OTM", 1, "Buy further OTM put for protection"),
            ],
        },
        {
            "name": "Bear Call Spread",
            "risk_profile": "Moderate",
            "bias": "bearish_income",
            "legs": [
                StrategyLeg("SELL", "CALL", "OTM", 1, "Sell OTM call to collect premium"),
                StrategyLeg("BUY", "CALL", "higher_OTM", 1, "Buy further OTM call for protection"),
            ],
        },
        {
            "name": "Iron Condor",
            "risk_profile": "Neutral",
            "bias": "range_bound",
            "legs": [
                StrategyLeg("SELL", "CALL", "OTM", 1, "Sell OTM call spread"),
                StrategyLeg("BUY", "CALL", "higher_OTM", 1, "Buy further OTM call"),
                StrategyLeg("SELL", "PUT", "OTM", 1, "Sell OTM put spread"),
                StrategyLeg("BUY", "PUT", "lower_OTM", 1, "Buy further OTM put"),
            ],
        },
        {
            "name": "Iron Butterfly",
            "risk_profile": "Neutral",
            "bias": "range_bound_tight",
            "legs": [
                StrategyLeg("SELL", "CALL", "ATM", 1, "Sell ATM call"),
                StrategyLeg("SELL", "PUT", "ATM", 1, "Sell ATM put"),
                StrategyLeg("BUY", "CALL", "OTM", 1, "Buy higher strike call"),
                StrategyLeg("BUY", "PUT", "OTM", 1, "Buy lower strike put"),
            ],
        },
        {
            "name": "Long Straddle",
            "risk_profile": "Aggressive",
            "bias": "volatility_expansion",
            "legs": [
                StrategyLeg("BUY", "CALL", "ATM", 1, "Buy ATM call"),
                StrategyLeg("BUY", "PUT", "ATM", 1, "Buy ATM put"),
            ],
        },
        {
            "name": "Long Strangle",
            "risk_profile": "Aggressive",
            "bias": "volatility_expansion",
            "legs": [
                StrategyLeg("BUY", "CALL", "OTM", 1, "Buy slightly OTM call"),
                StrategyLeg("BUY", "PUT", "OTM", 1, "Buy slightly OTM put"),
            ],
        },
    )

    def __init__(self, dhan, logger, *, exchange_segment: Optional[str] = None, instrument_type: str = "EQUITY"):
        self.dhan = dhan
        self.logger = logger
        self.exchange_segment = exchange_segment or getattr(self.dhan, "NSE", "NSE_EQ")
        self.instrument_type = instrument_type

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def select_best_strategy(
        self,
        security_id: str,
        market_snapshot: Dict,
        *,
        market_history: Optional[Sequence[Dict]] = None,
        position: Optional[Dict] = None,
    ) -> StrategyRecommendation:
        """
        Evaluate all strategies and return the top recommendation.
        """
        features = self._build_feature_context(market_snapshot, market_history or [])
        historical = self._fetch_historical_context(security_id)
        net_qty = self._extract_position_size(position)

        best: Optional[StrategyRecommendation] = None
        scores: List[StrategyRecommendation] = []

        for strategy in self._STRATEGIES:
            recommendation = self._score_strategy(
                strategy,
                features,
                historical,
                net_qty=net_qty,
            )
            scores.append(recommendation)
            if best is None or recommendation.score > best.score:
                best = recommendation

        if not best:
            best = StrategyRecommendation(
                name="No Strategy",
                score=0.0,
                confidence=0.0,
                rationale="Insufficient data to evaluate strategies.",
                risk_profile="N/A",
            )
        best.diagnostics["top_two_gap"] = self._compute_top_gap(scores, best.score)
        return best

    def rank_strategies(
        self,
        security_id: str,
        market_snapshot: Dict,
        *,
        market_history: Optional[Sequence[Dict]] = None,
        position: Optional[Dict] = None,
    ) -> List[StrategyRecommendation]:
        """Return all strategies sorted by score."""
        features = self._build_feature_context(market_snapshot, market_history or [])
        historical = self._fetch_historical_context(security_id)
        net_qty = self._extract_position_size(position)

        recommendations = [
            self._score_strategy(strategy, features, historical, net_qty=net_qty)
            for strategy in self._STRATEGIES
        ]
        recommendations.sort(key=lambda rec: rec.score, reverse=True)
        self._annotate_top_gap(recommendations)
        return recommendations

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _build_feature_context(
        self,
        snapshot: Dict,
        history: Sequence[Dict],
    ) -> Dict[str, float]:
        last_price = float(snapshot.get("last_price") or snapshot.get("lastPrice") or 0.0)
        open_price = float(snapshot.get("open") or 0.0)
        high_price = float(snapshot.get("high") or 0.0)
        low_price = float(snapshot.get("low") or 0.0)
        volume = float(snapshot.get("volume") or 0.0)

        closes = [float(item.get("last_price", 0.0) or 0.0) for item in history if item.get("last_price") is not None]
        closes = [price for price in closes if price > 0]
        if last_price:
            closes.append(last_price)

        short_ma = self._moving_average(closes, 5)
        long_ma = self._moving_average(closes, 20)
        trend_strength = 0.0
        if short_ma and long_ma:
            trend_strength = (short_ma - long_ma) / long_ma if long_ma else 0.0

        momentum_pct = 0.0
        if len(closes) >= 2:
            momentum_pct = (closes[-1] - closes[0]) / closes[0] if closes[0] else 0.0

        volatility_pct = self._annualised_volatility(closes) if len(closes) >= 6 else 0.0
        intraday_return_pct = 0.0
        if open_price:
            intraday_return_pct = (last_price - open_price) / open_price

        range_position = 0.5
        if high_price and low_price and high_price != low_price:
            range_position = (last_price - low_price) / (high_price - low_price)

        relative_volume = 1.0
        hist_vols = [float(item.get("volume") or 0.0) for item in history if item.get("volume") is not None]
        hist_vols = [vol for vol in hist_vols if vol > 0]
        if hist_vols:
            avg_volume = sum(hist_vols[-min(len(hist_vols), 10):]) / min(len(hist_vols), 10)
            relative_volume = volume / avg_volume if avg_volume else 1.0

        feature_context = {
            "last_price": last_price,
            "trend_strength": trend_strength,
            "momentum_pct": momentum_pct,
            "volatility_pct": volatility_pct,
            "intraday_return_pct": intraday_return_pct,
            "range_position": range_position,
            "relative_volume": relative_volume,
        }
        return feature_context

    def _fetch_historical_context(self, security_id: str) -> Dict[str, float]:
        """
        Fetch recent historical candles to compute swing metrics.
        Gracefully degrades to empty dict if API access fails.
        """
        try:
            to_date = datetime.now().date()
            from_date = to_date - timedelta(days=21)
            response = self.dhan.historical_daily_data(
                security_id=security_id,
                exchange_segment=self.exchange_segment,
                instrument_type=self.instrument_type,
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat(),
            )
            if response.get("status") != "success":
                return {}
            data = response.get("data") or {}
            candles = data.get("candles") or []
            closes = [float(candle[4]) for candle in candles if len(candle) >= 5]
            if len(closes) < 5:
                return {}
            swing_high = max(closes)
            swing_low = min(closes)
            swing_range_pct = (swing_high - swing_low) / swing_low if swing_low else 0.0
            recent_direction = (closes[-1] - closes[0]) / closes[0] if closes[0] else 0.0
            return {
                "swing_high": swing_high,
                "swing_low": swing_low,
                "swing_range_pct": swing_range_pct,
                "recent_direction": recent_direction,
            }
        except Exception as exc:  # pragma: no cover - dependent on live API
            self.logger.debug("Historical data fetch failed for %s: %s", security_id, exc)
            return {}

    def _score_strategy(
        self,
        strategy: Dict,
        features: Dict[str, float],
        historical: Dict[str, float],
        *,
        net_qty: float,
    ) -> StrategyRecommendation:
        name = strategy["name"]
        bias = strategy["bias"]

        trend = features.get("trend_strength", 0.0)
        momentum = features.get("momentum_pct", 0.0)
        volatility = features.get("volatility_pct", 0.0)
        intraday = features.get("intraday_return_pct", 0.0)
        range_position = features.get("range_position", 0.5)
        relative_volume = features.get("relative_volume", 1.0)
        swing_range = historical.get("swing_range_pct", 0.0)
        recent_direction = historical.get("recent_direction", 0.0)

        score = 0.0
        rationale_bits: List[str] = []

        # Generic adjustments
        if abs(trend) > 0.02:
            score += 10 * abs(trend)
        score += 5 * relative_volume
        score += 5 * min(max(swing_range, 0.0), 0.2)

        # Bias-specific heuristics
        if bias == "bullish":
            raw = (trend + momentum + intraday) * 100
            score += raw
            if raw > 0:
                rationale_bits.append("Bullish momentum and trend detected")
            if net_qty > 0:
                score += 15
                rationale_bits.append("Existing long position enables income overlay")

        elif bias == "bullish_risk_off":
            raw = (trend + recent_direction) * 80 - volatility * 20
            score += raw
            if raw > 0:
                rationale_bits.append("Uptrend with desire for downside protection")

        elif bias == "bearish":
            raw = (-(trend + momentum) + -intraday) * 90
            score += raw
            if raw > 0:
                rationale_bits.append("Bearish momentum warrants downside exposure")

        elif bias == "bearish_income":
            raw = (-(trend + momentum) + volatility * 30)
            score += raw
            if raw > 0:
                rationale_bits.append("Bearish lean with elevated volatility for premium")

        elif bias == "bullish_income":
            raw = (trend + momentum) * 70 + max(0.0, 0.05 - abs(intraday)) * 50
            score += raw
            if raw > 0:
                rationale_bits.append("Bullish bias with controlled volatility")

        elif bias == "range_bound":
            raw = max(0.0, 0.06 - abs(trend)) * 80 + max(0.0, 0.06 - abs(momentum)) * 60
            raw += max(0.0, 0.05 - swing_range) * 40
            raw -= volatility * 15
            score += raw
            if raw > 0:
                rationale_bits.append("Range-bound conditions favour short premium structures")

        elif bias == "range_bound_tight":
            raw = max(0.0, 0.04 - abs(trend)) * 90 + max(0.0, 0.04 - abs(momentum)) * 70
            raw -= volatility * 20
            score += raw
            if raw > 0:
                rationale_bits.append("Very tight range suggests Iron Butterfly")

        elif bias == "volatility_expansion":
            raw = (volatility * 120) + (relative_volume * 10)
            if swing_range > 0.08:
                raw += swing_range * 40
            score += raw
            if raw > 0:
                rationale_bits.append("Elevated volatility regime supports long gamma strategies")

        # Position-based adjustments for hedged strategies
        if name == "Covered Call" and net_qty <= 0:
            score -= 50
            rationale_bits.append("Requires existing long shares")
        if name == "Protective Put" and net_qty <= 0:
            score -= 15
            rationale_bits.append("Best suited for long equity exposure")

        confidence = self._score_to_confidence(score)
        rationale = "; ".join(rationale_bits) if rationale_bits else "Strategy aligns with quantitative signals."

        recommendation = StrategyRecommendation(
            name=name,
            score=score,
            confidence=confidence,
            rationale=rationale,
            risk_profile=strategy["risk_profile"],
            legs=strategy["legs"],
            expected_move=self._infer_expected_move(bias, trend, volatility),
            diagnostics={
                "trend_strength": trend,
                "momentum_pct": momentum,
                "volatility_pct": volatility,
                "intraday_return_pct": intraday,
                "range_position": range_position,
                "relative_volume": relative_volume,
                "swing_range_pct": swing_range,
            },
        )
        return recommendation

    # ------------------------------------------------------------------ #
    # Numeric helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _moving_average(series: Sequence[float], window: int) -> Optional[float]:
        if not series or len(series) < window:
            return None
        subset = series[-window:]
        return sum(subset) / len(subset)

    @staticmethod
    def _annualised_volatility(series: Sequence[float]) -> float:
        if len(series) < 2:
            return 0.0
        returns = []
        for i in range(1, len(series)):
            prev = series[i - 1]
            curr = series[i]
            if prev:
                returns.append((curr - prev) / prev)
        if not returns:
            return 0.0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        daily_vol = math.sqrt(variance)
        return daily_vol * math.sqrt(252)

    @staticmethod
    def _score_to_confidence(score: float) -> float:
        if score <= 0:
            return 0.0
        if score >= 200:
            return 0.99
        return min(max(score / 200.0, 0.0), 0.95)

    @staticmethod
    def _extract_position_size(position: Optional[Dict]) -> float:
        if not position or not isinstance(position, dict):
            return 0.0
        for key in ("netQuantity", "netQty", "qty", "quantity"):
            value = position.get(key)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return 0.0

    @staticmethod
    def _infer_expected_move(bias: str, trend: float, volatility: float) -> str:
        if bias in {"bullish", "bullish_income", "bullish_risk_off"}:
            return "Upside continuation expected"
        if bias in {"bearish", "bearish_income"}:
            return "Downside continuation expected"
        if bias in {"range_bound", "range_bound_tight"}:
            return "Price expected to stay within a range"
        if bias == "volatility_expansion":
            if volatility > 0.4:
                return "Major volatility spike anticipated"
            return "Volatility expansion expected"
        return "Neutral outlook"

    @staticmethod
    def _compute_top_gap(recommendations: Sequence[StrategyRecommendation], best_score: float) -> float:
        if not recommendations:
            return 0.0
        sorted_scores = sorted((rec.score for rec in recommendations), reverse=True)
        if len(sorted_scores) < 2:
            return 0.0
        return best_score - sorted_scores[1]

    @staticmethod
    def _annotate_top_gap(recommendations: List[StrategyRecommendation]) -> None:
        if not recommendations:
            return
        top_score = recommendations[0].score
        for rec in recommendations:
            rec.diagnostics["top_two_gap"] = top_score - rec.score if rec != recommendations[0] else top_score - recommendations[1].score if len(recommendations) > 1 else top_score

