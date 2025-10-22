# 🤖 AI-Powered Trading Bot with DhanHQ SDK

This repository now includes comprehensive AI integration capabilities using Google AI Studio and the DhanHQ Python SDK for building sophisticated trading bots.

## 🚀 Features

### **AI-Powered Trading Capabilities**
- **Multi-Model AI Analysis**: Technical, sentiment, and risk analysis using Google AI Studio
- **Real-time Decision Making**: AI-driven buy/sell/hold recommendations
- **Advanced Risk Management**: AI-powered position sizing and risk assessment
- **Portfolio Optimization**: Intelligent portfolio rebalancing based on AI insights

### **Trading Infrastructure**
- **Real-time Market Data**: Live market feeds with 20-level depth
- **Order Management**: Automated order placement, modification, and cancellation
- **Multi-Exchange Support**: NSE, BSE, MCX, Currency markets
- **WebSocket Integration**: Real-time order updates and market data

### **AI Integration Points**
- **Google AI Studio**: Advanced language models for market analysis
- **Technical Analysis**: AI-powered chart pattern recognition
- **Sentiment Analysis**: News and social media sentiment processing
- **Risk Management**: AI-driven portfolio risk assessment

## 📁 Project Structure

```
DhanHQ-py/
├── src/dhanhq/                 # Original DhanHQ SDK
├── ai_trading_bot.py          # Main AI trading bot
├── ai_trading_examples.py    # Advanced AI examples
├── ai_trading_setup.py       # Setup and deployment
├── ai_config.py              # AI configuration
├── AI_TRADING_README.md      # This file
└── requirements.txt           # Dependencies
```

## 🛠️ Setup Instructions

### **1. Prerequisites**
- Python 3.9+
- DhanHQ account with API access
- Google AI Studio API key
- Required Python packages

### **2. Installation**
```bash
# Clone the repository
git clone https://github.com/dhan-oss/DhanHQ-py.git
cd DhanHQ-py

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e '.[dev]'
```

### **3. Configuration**
```bash
# Run setup script
python ai_trading_setup.py

# Or manually create .env file
cp .env.example .env
# Edit .env with your credentials
```

### **4. Environment Variables**
```bash
# DhanHQ Credentials
DHAN_CLIENT_ID=your_client_id
DHAN_ACCESS_TOKEN=your_access_token

# Google AI Studio
AI_STUDIO_API_KEY=your_ai_studio_api_key

# Trading Configuration
MIN_CONFIDENCE=0.7
MAX_POSITION_SIZE=1000
RISK_PER_TRADE=0.02
```

## 🤖 AI Trading Bot Usage

### **Basic AI Trading Bot**
```python
from ai_trading_bot import AITradingBot

# Initialize bot
bot = AITradingBot(
    client_id="your_client_id",
    access_token="your_access_token",
    ai_studio_api_key="your_ai_studio_api_key"
)

# Run trading bot
securities = ["1333", "11536", "288"]  # HDFC, Reliance, TCS
bot.run_ai_trading_loop(securities)
```

### **Advanced Multi-Model AI Trading**
```python
from ai_trading_examples import AdvancedAITradingBot
import asyncio

# Initialize advanced bot
bot = AdvancedAITradingBot(
    client_id="your_client_id",
    access_token="your_access_token",
    ai_studio_api_key="your_ai_studio_api_key"
)

# Run advanced strategy
securities = ["1333", "11536", "288", "1594", "1660"]
asyncio.run(bot.run_advanced_trading_strategy(securities))
```

## 🧠 AI Models Integration

### **1. Technical Analysis AI**
```python
# AI-powered technical analysis
technical_analysis = await bot._get_technical_analysis(market_data)
# Returns: {"action": "BUY", "confidence": 0.85, "reasoning": "..."}
```

### **2. Sentiment Analysis AI**
```python
# AI-powered sentiment analysis
sentiment_analysis = await bot._get_sentiment_analysis(market_data)
# Returns: {"sentiment": "BULLISH", "confidence": 0.78, "key_factors": [...]}
```

### **3. Risk Management AI**
```python
# AI-powered risk management
risk_analysis = await bot._get_risk_analysis(market_data)
# Returns: {"risk_level": "MEDIUM", "recommended_actions": [...]}
```

## 📊 Trading Strategies

### **1. Momentum Strategy**
```python
# AI-powered momentum trading
momentum_recommendations = await strategies.momentum_strategy(securities)
```

### **2. Mean Reversion Strategy**
```python
# AI-powered mean reversion
mean_reversion_recommendations = await strategies.mean_reversion_strategy(securities)
```

### **3. Arbitrage Strategy**
```python
# AI-powered arbitrage
arbitrage_recommendations = await strategies.arbitrage_strategy(securities)
```

## 🚀 Deployment Options

### **1. Docker Deployment**
```bash
# Build and run with Docker
docker build -t ai-trading-bot .
docker run -d --name ai-trading-bot ai-trading-bot
```

### **2. Docker Compose**
```bash
# Multi-service deployment
docker-compose up -d
```

### **3. Kubernetes Deployment**
```bash
# Deploy to Kubernetes
kubectl apply -f k8s-deployment.yaml
```

## 📈 Performance Monitoring

### **Real-time Monitoring**
- Trade execution logs
- AI confidence tracking
- Portfolio performance metrics
- Risk exposure monitoring

### **Alerting System**
- Email notifications for trades
- Slack/Telegram integration
- Performance alerts
- Error notifications

## 🔧 Configuration Options

### **AI Studio Configuration**
```python
AI_STUDIO_CONFIG = {
    "api_key": "your_api_key",
    "model": "gemini-pro",
    "temperature": 0.1,
    "max_tokens": 1024
}
```

### **Trading Configuration**
```python
TRADING_CONFIG = {
    "min_confidence": 0.7,
    "max_position_size": 1000,
    "risk_per_trade": 0.02,
    "stop_loss_percent": 0.05,
    "take_profit_percent": 0.10
}
```

## 🧪 Testing

### **Unit Tests**
```bash
# Run unit tests
pytest tests/unit -v
```

### **Integration Tests**
```bash
# Run integration tests
pytest tests/integration -v
```

### **AI Model Tests**
```bash
# Test AI integration
pytest tests/ai_integration -v
```

## 📚 API Documentation

### **DhanHQ SDK Methods**
- `place_order()`: Place buy/sell orders
- `get_positions()`: Get current positions
- `get_holdings()`: Get portfolio holdings
- `get_fund_limits()`: Get available funds
- `intraday_minute_data()`: Get historical data
- `option_chain()`: Get options data

### **AI Trading Bot Methods**
- `run_ai_trading_loop()`: Main trading loop
- `multi_model_analysis()`: AI analysis
- `execute_trade()`: Execute AI recommendations
- `get_performance_report()`: Performance metrics

## 🛡️ Risk Management

### **Built-in Risk Controls**
- Position size limits
- Daily trade limits
- Stop-loss automation
- Portfolio risk assessment
- AI confidence thresholds

### **Safety Features**
- Credential validation
- Connection monitoring
- Error handling and recovery
- Trade logging and audit trail

## 📞 Support

### **Documentation**
- [DhanHQ Python Documentation](https://dhanhq.co/docs/DhanHQ-py/)
- [DhanHQ API Documentation](https://dhanhq.co/docs/v2/)
- [Google AI Studio Documentation](https://ai.google.dev/docs)

### **Community**
- GitHub Issues: [Report bugs and feature requests](https://github.com/dhan-oss/DhanHQ-py/issues)
- Discord: [Join the trading community](https://discord.gg/dhanhq)

## ⚠️ Disclaimer

This software is for educational and research purposes only. Trading involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. Always test thoroughly in a paper trading environment before using real money.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ using DhanHQ SDK and Google AI Studio**

