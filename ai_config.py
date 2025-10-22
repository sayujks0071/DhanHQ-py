# AI Trading Bot Configuration
# This file contains all configuration settings for the AI trading bot

AI_STUDIO_CONFIG = {
    "api_key": "your_ai_studio_api_key_here",
    "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
    "model": "gemini-pro",
    "temperature": 0.1,
    "max_tokens": 1024,
    "top_k": 40,
    "top_p": 0.95
}

TRADING_CONFIG = {
    "min_confidence": 0.7,
    "max_position_size": 1000,
    "risk_per_trade": 0.02,
    "stop_loss_percent": 0.05,
    "take_profit_percent": 0.1,
    "max_daily_trades": 10,
    "trading_hours": {
        "start": "09:15",
        "end": "15:30"
    },
    "update_interval": 5,
    "enable_option_strategy_ai": True,
    "auto_deploy_option_strategies": True,  # Enable auto-deploy for live trading
    "option_strategy_exchange_segment": "NSE_FNO",
    "option_strategy_instrument_type": "OPTIDX",  # Changed to OPTIDX for index options
    # High probability options settings
    "min_option_confidence": 0.7,
    "max_option_risk_per_trade": 0.005,
    "option_strategy_timeout": 300,
    "paper_trading_mode": False,
    "paper_position_size": 1,
    "live_safeguards": True,
    "enhanced_logging": True
}

MARKET_DATA_CONFIG = {
    "update_interval": 5,
    "max_instruments": 50,
    "data_types": [
        "ticker",
        "quote",
        "depth"
    ],
    "exchanges": [
        "NSE_EQ",
        "BSE_EQ",
        "NSE_FNO"
    ]
}

AI_PROMPTS = {
    "technical_analysis": "\n            Analyze the following market data and provide technical analysis:\n            \n            Market Data: {market_data}\n            \n            Consider:\n            1. Price action and trends\n            2. Volume analysis\n            3. Support and resistance levels\n            4. Technical indicators (RSI, MACD, etc.)\n            5. Market sentiment\n            \n            Provide recommendation in JSON format:\n            {{\n                \"action\": \"BUY|SELL|HOLD\",\n                \"confidence\": 0.0-1.0,\n                \"quantity\": number,\n                \"reasoning\": \"explanation\",\n                \"stop_loss\": price,\n                \"take_profit\": price\n            }}\n            ",
    "sentiment_analysis": "\n            Analyze market sentiment based on news and social media:\n            \n            News Data: {news_data}\n            Social Media: {social_data}\n            Market Events: {events}\n            \n            Consider:\n            1. News sentiment\n            2. Social media sentiment\n            3. Market events impact\n            4. Sector performance\n            5. Global market conditions\n            \n            Provide sentiment analysis in JSON format:\n            {{\n                \"sentiment\": \"BULLISH|BEARISH|NEUTRAL\",\n                \"confidence\": 0.0-1.0,\n                \"key_factors\": [\"factor1\", \"factor2\"],\n                \"impact_score\": 0.0-1.0,\n                \"recommendation\": \"explanation\"\n            }}\n            ",
    "risk_management": "\n            Analyze portfolio risk and provide risk management recommendations:\n            \n            Portfolio Data: {portfolio_data}\n            Current Positions: {positions}\n            Market Conditions: {market_conditions}\n            \n            Consider:\n            1. Portfolio diversification\n            2. Position sizing\n            3. Risk exposure\n            4. Market volatility\n            5. Correlation between positions\n            \n            Provide risk assessment in JSON format:\n            {{\n                \"risk_level\": \"LOW|MEDIUM|HIGH\",\n                \"recommended_actions\": [\"action1\", \"action2\"],\n                \"position_adjustments\": {{\"symbol\": \"adjustment\"}},\n                \"reasoning\": \"explanation\"\n            }}\n            "
}

SECURITY_MAPPINGS = {
    "NSE": {
        "1333": "HDFC Bank",
        "11536": "Reliance Industries",
        "288": "TCS",
        "1594": "Infosys",
        "1660": "ITC"
    },
    "BSE": {
        "500180": "HDFC Bank",
        "500325": "Reliance Industries",
        "532540": "TCS",
        "500209": "Infosys",
        "500875": "ITC"
    }
}

