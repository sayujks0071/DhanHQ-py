"""
Advanced AI Trading Examples using DhanHQ SDK with Google AI Studio
This module provides comprehensive examples for building AI-powered trading systems
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from dhanhq import DhanContext, dhanhq, MarketFeed, OrderUpdate
from ai_config import AI_STUDIO_CONFIG, TRADING_CONFIG, AI_PROMPTS, SECURITY_MAPPINGS

class AdvancedAITradingBot:
    """
    Advanced AI Trading Bot with multiple AI models and strategies
    """
    
    def __init__(self, client_id: str, access_token: str, ai_studio_api_key: str):
        self.dhan_context = DhanContext(client_id, access_token)
        self.dhan = dhanhq(self.dhan_context)
        self.ai_studio_api_key = ai_studio_api_key
        
        # Trading state
        self.portfolio = {}
        self.positions = {}
        self.orders = {}
        self.market_data = {}
        self.ai_models = {}
        
        # Performance tracking
        self.trade_history = []
        self.performance_metrics = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def multi_model_analysis(self, market_data: Dict) -> Dict:
        """
        Use multiple AI models for comprehensive analysis
        
        Args:
            market_data: Real-time market data
            
        Returns:
            Combined AI analysis from multiple models
        """
        try:
            # Technical Analysis AI
            technical_analysis = await self._get_technical_analysis(market_data)
            
            # Sentiment Analysis AI
            sentiment_analysis = await self._get_sentiment_analysis(market_data)
            
            # Risk Management AI
            risk_analysis = await self._get_risk_analysis(market_data)
            
            # Combine all analyses
            combined_analysis = self._combine_ai_analyses(
                technical_analysis, sentiment_analysis, risk_analysis
            )
            
            return combined_analysis
            
        except Exception as e:
            self.logger.error(f"Error in multi-model analysis: {e}")
            return {"action": "HOLD", "confidence": 0.0}
    
    async def _get_technical_analysis(self, market_data: Dict) -> Dict:
        """Get technical analysis from AI Studio"""
        prompt = AI_PROMPTS["technical_analysis"].format(market_data=market_data)
        return await self._call_ai_studio(prompt, "technical_analysis")
    
    async def _get_sentiment_analysis(self, market_data: Dict) -> Dict:
        """Get sentiment analysis from AI Studio"""
        # This would integrate with news and social media data
        news_data = self._get_news_data(market_data.get('symbol', ''))
        prompt = AI_PROMPTS["sentiment_analysis"].format(
            news_data=news_data,
            social_data=[],
            events=[]
        )
        return await self._call_ai_studio(prompt, "sentiment_analysis")
    
    async def _get_risk_analysis(self, market_data: Dict) -> Dict:
        """Get risk analysis from AI Studio"""
        portfolio_data = self._get_portfolio_data()
        prompt = AI_PROMPTS["risk_management"].format(
            portfolio_data=portfolio_data,
            positions=self.positions,
            market_conditions=market_data
        )
        return await self._call_ai_studio(prompt, "risk_management")
    
    async def _call_ai_studio(self, prompt: str, model_type: str) -> Dict:
        """Call Google AI Studio API"""
        try:
            import aiohttp
            
            model_config = AI_MODELS.get(model_type, AI_MODELS["technical_analysis"])
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{AI_STUDIO_CONFIG['base_url']}/{model_config['model']}:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.ai_studio_api_key}"
                    },
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": model_config["temperature"],
                            "maxOutputTokens": model_config["max_tokens"],
                            "topK": AI_STUDIO_CONFIG["top_k"],
                            "topP": AI_STUDIO_CONFIG["top_p"]
                        }
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_ai_response(result)
                    else:
                        self.logger.error(f"AI Studio API error: {response.status}")
                        return {"action": "HOLD", "confidence": 0.0}
                        
        except Exception as e:
            self.logger.error(f"Error calling AI Studio: {e}")
            return {"action": "HOLD", "confidence": 0.0}
    
    def _combine_ai_analyses(self, technical: Dict, sentiment: Dict, risk: Dict) -> Dict:
        """
        Combine multiple AI analyses into final trading decision
        
        Args:
            technical: Technical analysis results
            sentiment: Sentiment analysis results
            risk: Risk analysis results
            
        Returns:
            Combined trading recommendation
        """
        # Weighted scoring system
        weights = {
            "technical": 0.4,
            "sentiment": 0.3,
            "risk": 0.3
        }
        
        # Calculate weighted scores
        technical_score = self._score_analysis(technical) * weights["technical"]
        sentiment_score = self._score_analysis(sentiment) * weights["sentiment"]
        risk_score = self._score_analysis(risk) * weights["risk"]
        
        total_score = technical_score + sentiment_score + risk_score
        
        # Determine final action
        if total_score > 0.6:
            action = "BUY"
        elif total_score < -0.6:
            action = "SELL"
        else:
            action = "HOLD"
        
        return {
            "action": action,
            "confidence": abs(total_score),
            "technical_score": technical_score,
            "sentiment_score": sentiment_score,
            "risk_score": risk_score,
            "total_score": total_score,
            "reasoning": f"Technical: {technical.get('reasoning', '')}, "
                        f"Sentiment: {sentiment.get('reasoning', '')}, "
                        f"Risk: {risk.get('reasoning', '')}"
        }
    
    def _score_analysis(self, analysis: Dict) -> float:
        """Convert analysis to numerical score"""
        action = analysis.get("action", "HOLD")
        confidence = analysis.get("confidence", 0.0)
        
        if action == "BUY":
            return confidence
        elif action == "SELL":
            return -confidence
        else:
            return 0.0
    
    def _parse_ai_response(self, response: Dict) -> Dict:
        """Parse AI Studio response"""
        try:
            content = response['candidates'][0]['content']['parts'][0]['text']
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
            else:
                return {"action": "HOLD", "confidence": 0.0}
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return {"action": "HOLD", "confidence": 0.0}
    
    def _get_news_data(self, symbol: str) -> List[str]:
        """Get news data for sentiment analysis"""
        # This would integrate with news APIs
        return []
    
    def _get_portfolio_data(self) -> Dict:
        """Get current portfolio data"""
        try:
            return {
                "positions": self.dhan.get_positions(),
                "holdings": self.dhan.get_holdings(),
                "funds": self.dhan.get_fund_limits()
            }
        except Exception as e:
            self.logger.error(f"Error getting portfolio data: {e}")
            return {}
    
    async def run_advanced_trading_strategy(self, securities: List[str]):
        """
        Run advanced AI trading strategy
        
        Args:
            securities: List of security IDs to trade
        """
        self.logger.info("Starting Advanced AI Trading Strategy...")
        
        # Setup market feed
        instruments = []
        for security_id in securities:
            instruments.append((MarketFeed.NSE, security_id, MarketFeed.Ticker))
        
        market_feed = MarketFeed(self.dhan_context, instruments, "v2")
        
        try:
            while True:
                # Get market data
                market_data = market_feed.get_data()
                
                if market_data:
                    for data in market_data:
                        # Multi-model AI analysis
                        ai_analysis = await self.multi_model_analysis(data)
                        
                        # Execute trades based on AI recommendations
                        if ai_analysis['confidence'] > TRADING_CONFIG['min_confidence']:
                            await self._execute_ai_trade(ai_analysis, data.get('security_id'))
                        
                        # Update portfolio state
                        await self._update_portfolio_state()
                
                # Wait before next iteration
                await asyncio.sleep(TRADING_CONFIG['update_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("Trading strategy stopped by user")
        except Exception as e:
            self.logger.error(f"Error in trading strategy: {e}")
        finally:
            market_feed.disconnect()
    
    async def _execute_ai_trade(self, analysis: Dict, security_id: str):
        """Execute trade based on AI analysis"""
        try:
            action = analysis['action']
            confidence = analysis['confidence']
            
            if confidence < TRADING_CONFIG['min_confidence']:
                return
            
            # Calculate position size based on risk management
            position_size = self._calculate_position_size(security_id, confidence)
            
            if action == 'BUY' and position_size > 0:
                result = self.dhan.place_order(
                    security_id=security_id,
                    exchange_segment=self.dhan.NSE,
                    transaction_type=self.dhan.BUY,
                    quantity=position_size,
                    order_type=self.dhan.MARKET,
                    product_type=self.dhan.INTRA,
                    price=0
                )
                self._log_trade("BUY", security_id, position_size, analysis)
                
            elif action == 'SELL' and position_size > 0:
                result = self.dhan.place_order(
                    security_id=security_id,
                    exchange_segment=self.dhan.NSE,
                    transaction_type=self.dhan.SELL,
                    quantity=position_size,
                    order_type=self.dhan.MARKET,
                    product_type=self.dhan.INTRA,
                    price=0
                )
                self._log_trade("SELL", security_id, position_size, analysis)
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
    
    def _calculate_position_size(self, security_id: str, confidence: float) -> int:
        """Calculate position size based on risk management"""
        try:
            # Get current portfolio value
            funds = self.dhan.get_fund_limits()
            available_cash = funds.get('data', {}).get('available_cash', 0)
            
            # Calculate position size based on risk per trade
            risk_amount = available_cash * TRADING_CONFIG['risk_per_trade']
            position_size = int(risk_amount * confidence)
            
            # Apply maximum position size limit
            max_size = TRADING_CONFIG['max_position_size']
            return min(position_size, max_size)
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0
    
    def _log_trade(self, action: str, security_id: str, quantity: int, analysis: Dict):
        """Log trade execution"""
        trade_log = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "security_id": security_id,
            "quantity": quantity,
            "analysis": analysis
        }
        self.trade_history.append(trade_log)
        self.logger.info(f"Trade executed: {trade_log}")
    
    async def _update_portfolio_state(self):
        """Update portfolio state"""
        try:
            self.positions = self.dhan.get_positions()
            self.portfolio = self.dhan.get_holdings()
            self.orders = self.dhan.get_order_list()
        except Exception as e:
            self.logger.error(f"Error updating portfolio state: {e}")
    
    def get_performance_report(self) -> Dict:
        """Generate performance report"""
        try:
            total_trades = len(self.trade_history)
            buy_trades = len([t for t in self.trade_history if t['action'] == 'BUY'])
            sell_trades = len([t for t in self.trade_history if t['action'] == 'SELL'])
            
            return {
                "total_trades": total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "trade_history": self.trade_history,
                "portfolio": self.portfolio,
                "positions": self.positions
            }
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {}


class AITradingStrategies:
    """
    Collection of AI-powered trading strategies
    """
    
    def __init__(self, dhan_context: DhanContext, ai_studio_api_key: str):
        self.dhan_context = dhan_context
        self.dhan = dhanhq(dhan_context)
        self.ai_studio_api_key = ai_studio_api_key
    
    async def momentum_strategy(self, securities: List[str]) -> Dict:
        """
        AI-powered momentum trading strategy
        
        Args:
            securities: List of securities to analyze
            
        Returns:
            Momentum strategy recommendations
        """
        # This would implement momentum-based AI trading
        pass
    
    async def mean_reversion_strategy(self, securities: List[str]) -> Dict:
        """
        AI-powered mean reversion strategy
        
        Args:
            securities: List of securities to analyze
            
        Returns:
            Mean reversion strategy recommendations
        """
        # This would implement mean reversion AI trading
        pass
    
    async def arbitrage_strategy(self, securities: List[str]) -> Dict:
        """
        AI-powered arbitrage strategy
        
        Args:
            securities: List of securities to analyze
            
        Returns:
            Arbitrage strategy recommendations
        """
        # This would implement arbitrage AI trading
        pass


# Example usage and testing
if __name__ == "__main__":
    # Initialize Advanced AI Trading Bot
    bot = AdvancedAITradingBot(
        client_id="your_client_id",
        access_token="your_access_token",
        ai_studio_api_key="your_ai_studio_api_key"
    )
    
    # Run advanced trading strategy
    securities = ["1333", "11536", "288", "1594", "1660"]  # Multiple stocks
    asyncio.run(bot.run_advanced_trading_strategy(securities))

