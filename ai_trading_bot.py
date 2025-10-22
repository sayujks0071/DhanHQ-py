"""
AI-Powered Trading Bot using DhanHQ SDK and Google AI Studio
This module demonstrates how to integrate AI decision making with real-time trading
"""

import json
import time
import logging
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, time as dt_time
from typing import Deque, Dict, List, Optional

import requests

from dhanhq import DhanContext, MarketFeed, dhanhq

from ai_option_strategies import OptionStrategyAnalyzer, StrategyRecommendation
try:
    from ai_config import AI_STUDIO_CONFIG, TRADING_CONFIG, SECURITY_MAPPINGS
except ImportError:  # pragma: no cover - fallback for standalone usage
    AI_STUDIO_CONFIG = {
        "api_key": "",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
        "model": "gemini-pro",
        "temperature": 0.1,
        "max_tokens": 512,
        "top_k": 40,
        "top_p": 0.95,
    }
    TRADING_CONFIG = {
        "min_confidence": 0.7,
        "max_position_size": 1000,
        "risk_per_trade": 0.02,
        "stop_loss_percent": 0.05,
        "take_profit_percent": 0.1,
        "max_daily_trades": 10,
        "trading_hours": {"start": "09:15", "end": "15:30"},
        "update_interval": 5,
        "enable_option_strategy_ai": True,
        "auto_deploy_option_strategies": False,
        "option_strategy_exchange_segment": "NSE_FNO",
        "option_strategy_instrument_type": "EQUITY",
    }
    SECURITY_MAPPINGS = {}


@dataclass
class TradeRecommendation:
    """Normalized trade recommendation returned by the AI layer."""

    action: str = "HOLD"
    confidence: float = 0.0
    quantity: int = 0
    reasoning: str = ""
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    def is_actionable(self) -> bool:
        return self.action in {"BUY", "SELL"}

class AITradingBot:
    """
    AI-Powered Trading Bot that integrates DhanHQ SDK with Google AI Studio
    """
    
    def __init__(
        self,
        client_id: str,
        access_token: str,
        ai_studio_api_key: str,
        *,
        ai_config: Optional[Dict] = None,
        trading_config: Optional[Dict] = None,
    ):
        """
        Initialize the AI Trading Bot
        
        Args:
            client_id: DhanHQ client ID
            access_token: DhanHQ access token
            ai_studio_api_key: Google AI Studio API key
        """
        self.dhan_context = DhanContext(client_id, access_token)
        self.dhan = dhanhq(self.dhan_context)
        self.ai_config = {**AI_STUDIO_CONFIG, **(ai_config or {})}
        self.ai_studio_api_key = ai_studio_api_key or self.ai_config.get("api_key", "")
        self.ai_config["api_key"] = self.ai_studio_api_key
        self.ai_studio_url = self.ai_config.get(
            "base_url", "https://generativelanguage.googleapis.com/v1beta/models"
        )
        self.trading_config = {**TRADING_CONFIG, **(trading_config or {})}
        
        # Trading state
        self.active_positions: Dict[str, Dict] = {}
        self.pending_orders = {}
        self.market_data_cache: Dict[str, Dict] = {}
        self.market_history: Dict[str, Deque[Dict]] = defaultdict(
            lambda: deque(maxlen=self.trading_config.get("lookback_ticks", 120))
        )
        self.daily_trade_counts = defaultdict(int)
        self.last_trade_day = datetime.now().date()
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.funds_cache = {"timestamp": 0.0, "amount": None}
        self.option_strategy_analyzer = OptionStrategyAnalyzer(
            self.dhan,
            self.logger,
            exchange_segment=self.trading_config.get(
                "option_strategy_exchange_segment", getattr(self.dhan, "NSE_FNO", "NSE_FNO")
            ),
            instrument_type=self.trading_config.get("option_strategy_instrument_type", "EQUITY"),
        )
        self.current_option_strategies: Dict[str, StrategyRecommendation] = {}
    
    def get_ai_analysis(self, market_data: Dict) -> TradeRecommendation:
        """
        Get AI analysis from Google AI Studio
        
        Args:
            market_data: Real-time market data from DhanHQ
            
        Returns:
            AI analysis and trading recommendations
        """
        try:
            # Prepare prompt for AI Studio
            prompt = self._create_analysis_prompt(market_data)
            
            # Call Google AI Studio API
            response = requests.post(
                f"{self.ai_studio_url}/{self.ai_config.get('model', 'gemini-pro')}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.ai_studio_api_key}"
                },
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": self.ai_config.get("temperature", 0.1),
                        "topK": self.ai_config.get("top_k", 40),
                        "topP": self.ai_config.get("top_p", 0.95),
                        "maxOutputTokens": self.ai_config.get("max_tokens", 1024),
                    },
                }
            )
            
            if response.status_code == 200:
                ai_response = response.json()
                parsed = self._parse_ai_response(ai_response)
                return self._normalize_recommendation(parsed)
            else:
                self.logger.error(f"AI Studio API error: {response.status_code}")
                return TradeRecommendation()
                
        except Exception as e:
            self.logger.error(f"Error getting AI analysis: {e}")
            return TradeRecommendation()
    
    def _create_analysis_prompt(self, market_data: Dict) -> str:
        """
        Create analysis prompt for AI Studio
        
        Args:
            market_data: Market data from DhanHQ
            
        Returns:
            Formatted prompt for AI analysis
        """
        security_id = str(market_data.get("security_id", ""))
        symbol = market_data.get("symbol") or self._resolve_symbol(security_id)
        features = self._calculate_market_features(security_id, market_data)
        feature_summary = self._format_features(features)
        position_summary = self._format_position_summary(security_id)
        risk_summary = self._format_risk_summary()

        prompt = f"""
        You are an expert trading AI analyzing Indian stock market data and must follow disciplined risk management rules.
        
        Current Market Data:
        - Symbol: {symbol or 'N/A'} (Security ID: {security_id or 'N/A'})
        - Last Price: {market_data.get('last_price', 0)}
        - Volume: {market_data.get('volume', 0)}
        - High: {market_data.get('high', 0)}
        - Low: {market_data.get('low', 0)}
        - Open: {market_data.get('open', 0)}
        - Change: {market_data.get('change', 0)}
        - Change %: {market_data.get('change_percent', 0)}

        Computed Market Features:
        {feature_summary}

        Current Position:
        {position_summary}

        Risk Profile:
        {risk_summary}
        
        Provide a disciplined trade plan in JSON format with the following keys:
        {{
            "action": "BUY|SELL|HOLD",
            "confidence": 0.0-1.0,
            "quantity": integer number of shares (respect risk rules),
            "reasoning": "brief explanation focusing on evidence",
            "stop_loss": price level (optional but recommended),
            "take_profit": price level (optional but recommended)
        }}
        
        Only issue a BUY or SELL signal if confidence >= {self.trading_config.get('min_confidence', 0.7)} and the risk profile allows it.
        """
        return prompt
    
    def _calculate_market_features(self, security_id: str, market_data: Dict) -> Dict[str, float]:
        """
        Build lightweight quantitative features for the prompt and risk checks.
        """
        if not security_id:
            return {}
        
        history = self.market_history[security_id]
        closes = [tick.get("last_price") for tick in history if tick.get("last_price") is not None]
        volumes = [tick.get("volume") for tick in history if tick.get("volume") is not None]
        features: Dict[str, float] = {}
        last_price = market_data.get("last_price")
        
        if closes:
            short_window = closes[-min(5, len(closes)) :]
            long_window = closes[-min(20, len(closes)) :]
            features["short_ma"] = statistics.mean(short_window)
            features["long_ma"] = statistics.mean(long_window)
            if long_window and long_window[0]:
                features["momentum_pct"] = (
                    (short_window[-1] - long_window[0]) / long_window[0]
                )
            if len(long_window) > 1:
                volatility_base = max((abs(value) for value in long_window if value), default=0)
                if volatility_base:
                    features["volatility_pct"] = statistics.pstdev(long_window) / volatility_base
        
        if last_price and market_data.get("open"):
            open_price = market_data["open"]
            if open_price:
                features["intraday_return_pct"] = (last_price - open_price) / open_price
        
        if last_price and market_data.get("high") and market_data.get("low"):
            high = market_data["high"]
            low = market_data["low"]
            if high != low:
                features["range_position"] = (last_price - low) / (high - low)
        
        if volumes:
            avg_volume = statistics.mean(volumes[-min(10, len(volumes)) :])
            features["avg_volume"] = avg_volume
            if market_data.get("volume"):
                current_volume = market_data["volume"]
                if avg_volume:
                    features["relative_volume"] = current_volume / avg_volume
        
        features["history_depth"] = float(len(history))
        return {k: float(v) for k, v in features.items()}
    
    def _format_features(self, features: Dict[str, float]) -> str:
        if not features:
            return "- Not enough historical data collected yet."
        lines = [
            f"- {name.replace('_', ' ').title()}: {round(value, 4)}"
            for name, value in features.items()
        ]
        return "\n        ".join(lines)
    
    def _format_position_summary(self, security_id: str) -> str:
        position = self.active_positions.get(security_id)
        if not position:
            return "- No open position for this security."
        
        if isinstance(position, dict):
            keys_of_interest = [
                "netQuantity",
                "netQty",
                "productType",
                "averagePrice",
                "pnl",
            ]
            summary = {k: position.get(k) for k in keys_of_interest if k in position}
            if not summary:
                summary = position
        else:
            summary = position
        
        try:
            return f"- {json.dumps(summary, default=str)}"
        except TypeError:
            return f"- {summary}"
    
    def _format_risk_summary(self) -> str:
        keys = [
            "min_confidence",
            "risk_per_trade",
            "max_position_size",
            "stop_loss_percent",
            "take_profit_percent",
            "max_daily_trades",
        ]
        summary = {k: self.trading_config.get(k) for k in keys if k in self.trading_config}
        return json.dumps(summary)
    
    def _resolve_symbol(self, security_id: str) -> Optional[str]:
        if not security_id:
            return None
        for exchange_map in SECURITY_MAPPINGS.values():
            if security_id in exchange_map:
                return exchange_map[security_id]
        return None
    
    def _evaluate_option_strategy(self, security_id: str, market_snapshot: Dict) -> Optional[StrategyRecommendation]:
        """Evaluate option strategies for the given security."""
        if not self.trading_config.get("enable_option_strategy_ai", True):
            return None
        try:
            history = list(self.market_history.get(security_id, []))
            position = self.active_positions.get(security_id)
            recommendation = self.option_strategy_analyzer.select_best_strategy(
                security_id,
                market_snapshot,
                market_history=history,
                position=position,
            )
            self.current_option_strategies[security_id] = recommendation
            self.logger.info(
                "Option strategy for %s: %s (score=%.2f, confidence=%.2f)",
                security_id,
                recommendation.name,
                recommendation.score,
                recommendation.confidence,
            )
            if self.trading_config.get("auto_deploy_option_strategies", False):
                self._deploy_option_strategy(security_id, recommendation)
            return recommendation
        except Exception as exc:
            self.logger.error("Option strategy evaluation failed for %s: %s", security_id, exc)
            return None
    
    def _deploy_option_strategy(self, security_id: str, recommendation: StrategyRecommendation) -> None:
        """
        Deploy the provided option strategy.
        
        For safety, the default implementation only logs the execution plan.
        Advanced users can extend this method to place multi-leg orders through DhanHQ.
        """
        if not recommendation or recommendation.score <= 0:
            self.logger.info("Skipping option strategy deployment for %s due to low score.", security_id)
            return
        self.logger.info(
            "Auto-deploying option strategy %s for %s (risk: %s, confidence: %.2f)",
            recommendation.name,
            security_id,
            recommendation.risk_profile,
            recommendation.confidence,
        )
        for idx, leg in enumerate(recommendation.legs, start=1):
            self.logger.info(
                "  Leg %d: %s %s %s qty=%s | %s",
                idx,
                leg.action,
                leg.option_type,
                leg.moneyness,
                leg.quantity,
                leg.notes or "No additional notes",
            )
        self.logger.info(
            "Option strategy deployment for %s completed (no live orders were placed by default).",
            security_id,
        )
    
    def get_option_strategy_plan(self, security_id: str) -> Optional[Dict]:
        """Return the latest option strategy plan for the specified security."""
        recommendation = self.current_option_strategies.get(security_id)
        if not recommendation:
            return None
        return recommendation.as_dict()
    
    def _get_available_funds(self) -> Optional[float]:
        """Fetch available funds with lightweight caching to limit API calls."""
        now = time.time()
        cache_ttl = max(30, int(self.trading_config.get("funds_cache_ttl", 60)))
        if (
            self.funds_cache["amount"] is not None
            and now - self.funds_cache["timestamp"] < cache_ttl
        ):
            return self.funds_cache["amount"]
        
        try:
            funds = self.dhan.get_fund_limits()
            if funds.get("status") != "success":
                return None
            data = funds.get("data") or {}
            preferred_keys = [
                "availabelBalance",
                "withdrawableBalance",
                "sodLimit",
                "collateralAmount",
            ]
            available = None
            for key in preferred_keys:
                value = data.get(key)
                if isinstance(value, (int, float)):
                    available = float(value)
                    break
            if available is not None:
                self.funds_cache = {"timestamp": now, "amount": max(0.0, available)}
            return self.funds_cache["amount"]
        except Exception as exc:
            self.logger.error(f"Unable to fetch available funds: {exc}")
            return None
    
    def _update_market_history(self, security_id: str, market_snapshot: Dict):
        history = self.market_history[security_id]
        history.append(
            {
                "last_price": market_snapshot.get("last_price"),
                "volume": market_snapshot.get("volume"),
            }
        )
    
    def _calculate_risk_based_quantity(
        self, market_snapshot: Dict, stop_loss_input: Optional[float]
    ) -> int:
        last_price = market_snapshot.get("last_price")
        if not last_price:
            return 0
        available_funds = self._get_available_funds()
        if not available_funds:
            return 0
        
        risk_per_trade = self.trading_config.get("risk_per_trade", 0.02)
        if risk_per_trade <= 0:
            return 0
        
        stop_loss_pct = None
        if stop_loss_input is not None:
            try:
                stop_loss_input = float(stop_loss_input)
                if stop_loss_input <= 1:
                    stop_loss_pct = stop_loss_input
                else:
                    # Treat as absolute price level
                    price_diff = abs(last_price - stop_loss_input)
                    if last_price:
                        stop_loss_pct = price_diff / last_price
            except (TypeError, ValueError):
                stop_loss_pct = None
        
        if stop_loss_pct is None or stop_loss_pct <= 0:
            stop_loss_pct = self.trading_config.get("stop_loss_percent", 0.05)
        
        stop_loss_pct = max(stop_loss_pct, 0.0001)
        
        max_loss = available_funds * risk_per_trade
        per_share_risk = last_price * stop_loss_pct
        if per_share_risk <= 0:
            return 0
        return max(0, int(max_loss / per_share_risk))
    
    def _extract_net_quantity(self, position: Optional[Dict]) -> float:
        if not position or not isinstance(position, dict):
            return 0.0
        for key in ("netQuantity", "netQty", "quantity", "qty"):
            if key in position and position[key] is not None:
                try:
                    return float(position[key])
                except (TypeError, ValueError):
                    continue
        return 0.0
    
    def _determine_order_quantity(
        self,
        recommendation: TradeRecommendation,
        security_id: str,
        market_snapshot: Dict,
    ) -> int:
        quantity = recommendation.quantity
        if quantity <= 0:
            quantity = self._calculate_risk_based_quantity(
                market_snapshot, recommendation.stop_loss
            )
        position = self.active_positions.get(security_id)
        net_qty = self._extract_net_quantity(position)
        max_position_size = self.trading_config.get("max_position_size")
        
        if recommendation.action == "BUY":
            if max_position_size is not None:
                allowable = max(0, max_position_size - net_qty)
                quantity = min(quantity, int(allowable))
        elif recommendation.action == "SELL":
            if net_qty > 0:
                quantity = min(quantity, int(net_qty))
            else:
                allow_short = self.trading_config.get("allow_short_selling", False)
                if not allow_short:
                    quantity = 0
        
        return max(0, int(quantity))
    
    def _reset_daily_trade_counters(self):
        today = datetime.now().date()
        if today != self.last_trade_day:
            self.daily_trade_counts.clear()
            self.last_trade_day = today
    
    def _record_trade(self, security_id: str):
        self.daily_trade_counts[security_id] += 1
        self.daily_trade_counts["__TOTAL__"] += 1
    
    @staticmethod
    def _parse_time(value: Optional[str]) -> Optional[dt_time]:
        if not value:
            return None
        try:
            hours, minutes = value.split(":")
            return dt_time(hour=int(hours), minute=int(minutes))
        except (ValueError, TypeError):
            return None
    
    def _within_trading_hours(self) -> bool:
        trading_hours = self.trading_config.get("trading_hours", {})
        start = self._parse_time(trading_hours.get("start"))
        end = self._parse_time(trading_hours.get("end"))
        if not start or not end:
            return True
        now = datetime.now().time()
        return start <= now <= end
    
    def _should_execute_trade(
        self,
        recommendation: TradeRecommendation,
        security_id: str,
        quantity: int,
    ) -> bool:
        if not recommendation.is_actionable():
            return False
        
        if recommendation.confidence < self.trading_config.get("min_confidence", 0.7):
            self.logger.info(
                "Skipping trade due to low confidence: %.2f",
                recommendation.confidence,
            )
            return False
        
        if not self._within_trading_hours():
            self.logger.info("Skipping trade - outside configured trading hours")
            return False
        
        self._reset_daily_trade_counters()
        max_daily = self.trading_config.get("max_daily_trades")
        max_per_symbol = self.trading_config.get(
            "max_trades_per_symbol", max_daily
        )
        total_trades = self.daily_trade_counts["__TOTAL__"]
        symbol_trades = self.daily_trade_counts[security_id]
        
        if max_daily and total_trades >= max_daily:
            self.logger.info("Skipping trade - daily trade limit reached")
            return False
        if max_per_symbol and symbol_trades >= max_per_symbol:
            self.logger.info(
                "Skipping trade - symbol trade limit reached for %s", security_id
            )
            return False
        
        if quantity <= 0:
            self.logger.info("Skipping trade - calculated quantity is zero")
            return False
        
        position = self.active_positions.get(security_id)
        net_qty = self._extract_net_quantity(position)
        if recommendation.action == "SELL" and net_qty <= 0:
            allow_short = self.trading_config.get("allow_short_selling", False)
            if not allow_short:
                self.logger.info(
                    "Skipping SELL - no holdings and short selling disabled."
                )
                return False
        
        return True
    
    def _resolve_dhan_constant(self, name: Optional[str], fallback):
        if not name:
            return fallback
        return getattr(self.dhan, name, fallback)
    
    def _parse_ai_response(self, ai_response: Dict) -> Dict:
        """
        Parse AI Studio response
        
        Args:
            ai_response: Raw response from AI Studio
            
        Returns:
            Parsed trading recommendation
        """
        try:
            content = ai_response["candidates"][0]["content"]["parts"][0]["text"]
            # Extract JSON from response
            if "```" in content:
                # Remove potential code fences
                content = content.replace("```json", "").replace("```", "")
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found in AI response")
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return {"action": "HOLD", "confidence": 0.0}
    
    def _normalize_recommendation(self, recommendation: Dict) -> TradeRecommendation:
        """Convert raw AI response into a structured recommendation object."""
        try:
            action = str(recommendation.get("action", "HOLD")).upper().strip()
            if action not in {"BUY", "SELL", "HOLD"}:
                action = "HOLD"
            confidence = float(recommendation.get("confidence", 0.0))
            quantity = int(float(recommendation.get("quantity", 0)))
            reasoning = str(recommendation.get("reasoning", "")).strip()

            stop_loss = recommendation.get("stop_loss")
            take_profit = recommendation.get("take_profit")
            stop_loss = float(stop_loss) if stop_loss not in (None, "") else None
            take_profit = float(take_profit) if take_profit not in (None, "") else None

            return TradeRecommendation(
                action=action,
                confidence=max(0.0, min(1.0, confidence)),
                quantity=max(0, quantity),
                reasoning=reasoning,
                stop_loss=stop_loss,
                take_profit=take_profit,
            )
        except Exception as exc:
            self.logger.error(f"Failed to normalize recommendation: {exc}")
            return TradeRecommendation()
    
    def execute_trade(
        self,
        recommendation: TradeRecommendation,
        security_id: str,
        market_snapshot: Dict,
        quantity: int,
    ) -> bool:
        """
        Execute trade based on AI recommendation
        
        Args:
            recommendation: AI trading recommendation
            security_id: Security ID to trade
            market_snapshot: Latest market data used for sizing
            quantity: Final quantity after risk checks
            
        Returns:
            True if trade executed successfully
        """
        try:
            exchange_segment = self._resolve_dhan_constant(
                self.trading_config.get("exchange_segment"), self.dhan.NSE
            )
            product_type = self._resolve_dhan_constant(
                self.trading_config.get("product_type"), self.dhan.INTRA
            )
            order_type = self._resolve_dhan_constant(
                self.trading_config.get("order_type"), self.dhan.MARKET
            )
            transaction_type = (
                self.dhan.BUY if recommendation.action == "BUY" else self.dhan.SELL
            )
            
            self.logger.info(
                "Executing %s order for %s | quantity=%s | confidence=%.2f | reason=%s",
                recommendation.action,
                security_id,
                quantity,
                recommendation.confidence,
                recommendation.reasoning or "n/a",
            )
            
            result = self.dhan.place_order(
                security_id=security_id,
                exchange_segment=exchange_segment,
                transaction_type=transaction_type,
                quantity=quantity,
                order_type=order_type,
                product_type=product_type,
                price=0,
            )
            
            status = result.get("status") if isinstance(result, dict) else None
            if status and status.lower() != "success":
                self.logger.error("Order rejected: %s", result)
                return False
            
            if recommendation.stop_loss:
                self.logger.info(
                    "Recommended stop loss at %.2f for %s", recommendation.stop_loss, security_id
                )
            if recommendation.take_profit:
                self.logger.info(
                    "Recommended take profit at %.2f for %s",
                    recommendation.take_profit,
                    security_id,
                )
            
            self._record_trade(security_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return False
    
    def run_ai_trading_loop(self, security_ids: List[str]):
        """
        Main trading loop with AI integration
        
        Args:
            security_ids: List of security IDs to monitor
        """
        self.logger.info("Starting AI Trading Bot...")
        
        # Setup market feed
        instruments = []
        for security_id in security_ids:
            instruments.append((MarketFeed.NSE, security_id, MarketFeed.Ticker))
        
        market_feed = MarketFeed(self.dhan_context, instruments, "v2")
        update_interval = self.trading_config.get("update_interval", 5)
        
        try:
            while True:
                self._reset_daily_trade_counters()
                self._update_positions()
                # Get market data
                market_data = market_feed.get_data()
                
                if market_data:
                    for data in market_data:
                        security_id = str(data.get("security_id", ""))
                        if not security_id:
                            continue
                        
                        data.setdefault("symbol", self._resolve_symbol(security_id))
                        self.market_data_cache[security_id] = data
                        self._update_market_history(security_id, data)
                        
                        # Get AI analysis
                        ai_recommendation = self.get_ai_analysis(data)
                        self.logger.debug(
                            "AI recommendation for %s: %s",
                            security_id,
                            ai_recommendation,
                        )
                        
                        # Evaluate option strategies in parallel
                        self._evaluate_option_strategy(security_id, data)
                        
                        quantity = self._determine_order_quantity(
                            ai_recommendation, security_id, data
                        )
                        
                        if self._should_execute_trade(
                            ai_recommendation, security_id, quantity
                        ):
                            executed = self.execute_trade(
                                ai_recommendation, security_id, data, quantity
                            )
                            if executed:
                                self.logger.info(
                                    "Trade executed successfully for %s", security_id
                                )
                
                # Wait before next iteration
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped by user")
        except Exception as e:
            self.logger.error(f"Error in trading loop: {e}")
        finally:
            market_feed.disconnect()
    
    def _update_positions(self):
        """Update current positions from DhanHQ"""
        try:
            positions = self.dhan.get_positions()
            if positions.get("status") != "success":
                return
            data = positions.get("data") or {}
            if isinstance(data, list):
                structured = {}
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    security_id = item.get("securityId") or item.get("security_id")
                    if security_id is None:
                        continue
                    structured[str(security_id)] = item
                self.active_positions = structured
            elif isinstance(data, dict):
                # Assume already keyed by security id
                self.active_positions = {str(k): v for k, v in data.items()}
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get comprehensive portfolio summary
        
        Returns:
            Portfolio summary with positions, holdings, and funds
        """
        try:
            portfolio = {
                'positions': self.dhan.get_positions(),
                'holdings': self.dhan.get_holdings(),
                'funds': self.dhan.get_fund_limits(),
                'orders': self.dhan.get_order_list()
            }
            return portfolio
        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return {}


class AITradingStrategy:
    """
    Advanced AI Trading Strategy with multiple AI models
    """
    
    def __init__(self, dhan_context: DhanContext, ai_config: Dict):
        self.dhan_context = dhan_context
        self.dhan = dhanhq(dhan_context)
        self.ai_config = ai_config
        
    def technical_analysis_ai(self, market_data: Dict) -> Dict:
        """
        AI-powered technical analysis
        
        Args:
            market_data: Market data for analysis
            
        Returns:
            Technical analysis results
        """
        # This would integrate with your AI Studio technical analysis model
        pass
    
    def sentiment_analysis_ai(self, news_data: List[str]) -> Dict:
        """
        AI-powered sentiment analysis
        
        Args:
            news_data: News articles and social media data
            
        Returns:
            Sentiment analysis results
        """
        # This would integrate with your AI Studio sentiment analysis model
        pass
    
    def risk_management_ai(self, portfolio_data: Dict) -> Dict:
        """
        AI-powered risk management
        
        Args:
            portfolio_data: Current portfolio state
            
        Returns:
            Risk management recommendations
        """
        # This would integrate with your AI Studio risk management model
        pass


# Example usage
if __name__ == "__main__":
    # Initialize AI Trading Bot
    bot = AITradingBot(
        client_id="your_client_id",
        access_token="your_access_token",
        ai_studio_api_key="your_ai_studio_api_key"
    )
    
    # Run trading bot for specific securities
    securities = ["1333", "11536", "288"]  # HDFC Bank, Reliance, TCS
    bot.run_ai_trading_loop(securities)



