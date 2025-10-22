"""
Non-interactive AI Trading Bot Setup
This script sets up the AI trading environment without requiring user input
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List

def setup_ai_trading_environment():
    """
    Setup AI trading environment with default configurations
    """
    print("🤖 AI Trading Bot Setup (Non-Interactive)")
    print("=" * 50)
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    # Create environment file template
    env_content = """# DhanHQ Credentials
DHAN_CLIENT_ID=your_client_id_here
DHAN_ACCESS_TOKEN=your_access_token_here

# Google AI Studio Credentials
AI_STUDIO_API_KEY=your_ai_studio_api_key_here

# Trading Configuration
MIN_CONFIDENCE=0.7
MAX_POSITION_SIZE=1000
RISK_PER_TRADE=0.02
STOP_LOSS_PERCENT=0.05
TAKE_PROFIT_PERCENT=0.10
MAX_DAILY_TRADES=10

# Market Data Configuration
UPDATE_INTERVAL=5
MAX_INSTRUMENTS=50

# AI Configuration
AI_MODEL=gemini-pro
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=1024
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    print("✅ Environment file created: .env")
    
    # Create AI configuration
    ai_config = {
        "AI_STUDIO_CONFIG": {
            "api_key": "your_ai_studio_api_key_here",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
            "model": "gemini-pro",
            "temperature": 0.1,
            "max_tokens": 1024,
            "top_k": 40,
            "top_p": 0.95
        },
        "TRADING_CONFIG": {
            "min_confidence": 0.7,
            "max_position_size": 1000,
            "risk_per_trade": 0.02,
            "stop_loss_percent": 0.05,
            "take_profit_percent": 0.10,
            "max_daily_trades": 10,
            "trading_hours": {
                "start": "09:15",
                "end": "15:30"
            },
            "update_interval": 5
        },
        "MARKET_DATA_CONFIG": {
            "update_interval": 5,
            "max_instruments": 50,
            "data_types": ["ticker", "quote", "depth"],
            "exchanges": ["NSE_EQ", "BSE_EQ", "NSE_FNO"]
        },
        "AI_PROMPTS": {
            "technical_analysis": """
            Analyze the following market data and provide technical analysis:
            
            Market Data: {market_data}
            
            Consider:
            1. Price action and trends
            2. Volume analysis
            3. Support and resistance levels
            4. Technical indicators (RSI, MACD, etc.)
            5. Market sentiment
            
            Provide recommendation in JSON format:
            {{
                "action": "BUY|SELL|HOLD",
                "confidence": 0.0-1.0,
                "quantity": number,
                "reasoning": "explanation",
                "stop_loss": price,
                "take_profit": price
            }}
            """,
            "sentiment_analysis": """
            Analyze market sentiment based on news and social media:
            
            News Data: {news_data}
            Social Media: {social_data}
            Market Events: {events}
            
            Consider:
            1. News sentiment
            2. Social media sentiment
            3. Market events impact
            4. Sector performance
            5. Global market conditions
            
            Provide sentiment analysis in JSON format:
            {{
                "sentiment": "BULLISH|BEARISH|NEUTRAL",
                "confidence": 0.0-1.0,
                "key_factors": ["factor1", "factor2"],
                "impact_score": 0.0-1.0,
                "recommendation": "explanation"
            }}
            """,
            "risk_management": """
            Analyze portfolio risk and provide risk management recommendations:
            
            Portfolio Data: {portfolio_data}
            Current Positions: {positions}
            Market Conditions: {market_conditions}
            
            Consider:
            1. Portfolio diversification
            2. Position sizing
            3. Risk exposure
            4. Market volatility
            5. Correlation between positions
            
            Provide risk assessment in JSON format:
            {{
                "risk_level": "LOW|MEDIUM|HIGH",
                "recommended_actions": ["action1", "action2"],
                "position_adjustments": {{"symbol": "adjustment"}},
                "reasoning": "explanation"
            }}
            """
        },
        "SECURITY_MAPPINGS": {
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
    }
    
    with open('ai_config.py', 'w') as f:
        f.write("""# AI Trading Bot Configuration
# This file contains all configuration settings for the AI trading bot

""")
        f.write("AI_STUDIO_CONFIG = " + json.dumps(ai_config["AI_STUDIO_CONFIG"], indent=4) + "\n\n")
        f.write("TRADING_CONFIG = " + json.dumps(ai_config["TRADING_CONFIG"], indent=4) + "\n\n")
        f.write("MARKET_DATA_CONFIG = " + json.dumps(ai_config["MARKET_DATA_CONFIG"], indent=4) + "\n\n")
        f.write("AI_PROMPTS = " + json.dumps(ai_config["AI_PROMPTS"], indent=4) + "\n\n")
        f.write("SECURITY_MAPPINGS = " + json.dumps(ai_config["SECURITY_MAPPINGS"], indent=4) + "\n")
    
    print("✅ AI configuration created: ai_config.py")
    
    # Create trading schedule
    trading_schedule = {
        "trading_hours": {
            "start": "09:15",
            "end": "15:30"
        },
        "market_holidays": [
            "2024-01-26",  # Republic Day
            "2024-03-08",  # Holi
            "2024-03-29",  # Good Friday
            "2024-04-11",  # Eid
            "2024-08-15",  # Independence Day
            "2024-10-02",  # Gandhi Jayanti
            "2024-11-01",  # Diwali
            "2024-12-25"   # Christmas
        ],
        "pre_market_analysis": "09:00",
        "post_market_analysis": "15:45"
    }
    
    with open('trading_schedule.json', 'w') as f:
        json.dump(trading_schedule, f, indent=2)
    print("✅ Trading schedule created: trading_schedule.json")
    
    # Create monitoring configuration
    monitoring_config = {
        "alerts": {
            "email": {
                "enabled": False,
                "recipients": ["trader@example.com"],
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587
            },
            "slack": {
                "enabled": False,
                "webhook_url": ""
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            }
        },
        "monitoring": {
            "performance_tracking": True,
            "error_alerting": True,
            "trade_logging": True,
            "ai_confidence_tracking": True
        }
    }
    
    with open('monitoring_config.json', 'w') as f:
        json.dump(monitoring_config, f, indent=2)
    print("✅ Monitoring configuration created: monitoring_config.json")
    
    # Create requirements.txt
    requirements = """# DhanHQ SDK
dhanhq>=2.1.0

# AI and ML libraries
google-generativeai>=0.3.0
openai>=1.0.0
transformers>=4.30.0
torch>=2.0.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0

# Web and API libraries
aiohttp>=3.8.0
requests>=2.31.0
websockets>=12.0.0
fastapi>=0.100.0
uvicorn>=0.23.0

# Database libraries
sqlalchemy>=2.0.0
alembic>=1.11.0
psycopg2-binary>=2.9.0
redis>=4.6.0

# Monitoring and logging
prometheus-client>=0.17.0
grafana-api>=1.0.3
python-telegram-bot>=20.0

# Development and testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0

# Utilities
python-dotenv>=1.0.0
schedule>=1.2.0
croniter>=1.4.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("✅ Requirements file created: requirements.txt")
    
    # Create Dockerfile
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "ai_trading_bot.py"]
"""
    
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    print("✅ Dockerfile created")
    
    # Create docker-compose.yml
    compose_content = """version: '3.8'

services:
  ai-trading-bot:
    build: .
    container_name: ai-trading-bot
    environment:
      - DHAN_CLIENT_ID=${DHAN_CLIENT_ID}
      - DHAN_ACCESS_TOKEN=${DHAN_ACCESS_TOKEN}
      - AI_STUDIO_API_KEY=${AI_STUDIO_API_KEY}
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    depends_on:
      - redis

  redis:
    image: redis:alpine
    container_name: ai-trading-redis
    ports:
      - "6379:6379"
    restart: unless-stopped
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(compose_content)
    print("✅ Docker Compose file created: docker-compose.yml")
    
    # Create example usage script
    example_script = """#!/usr/bin/env python3
\"\"\"
Example AI Trading Bot Usage
This script demonstrates how to use the AI trading bot
\"\"\"

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
        print("\\n🛑 Trading bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
"""
    
    with open('run_ai_trading.py', 'w') as f:
        f.write(example_script)
    print("✅ Example script created: run_ai_trading.py")
    
    # Make example script executable
    os.chmod('run_ai_trading.py', 0o755)
    
    print("\n🎉 AI Trading Bot setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your credentials:")
    print("   - DHAN_CLIENT_ID")
    print("   - DHAN_ACCESS_TOKEN")
    print("   - AI_STUDIO_API_KEY")
    print("\n2. Install additional dependencies:")
    print("   pip install -r requirements.txt")
    print("\n3. Run the example:")
    print("   python run_ai_trading.py")
    print("\n4. For production deployment:")
    print("   docker-compose up -d")
    print("\n📚 Documentation: AI_TRADING_README.md")

if __name__ == "__main__":
    setup_ai_trading_environment()

