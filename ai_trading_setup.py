"""
AI Trading Bot Setup and Deployment Guide
This module provides setup instructions and deployment scripts for AI-powered trading
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List
import asyncio

from dhanhq import DhanContext, dhanhq, MarketFeed, OrderUpdate
try:
    from ai_config import AI_STUDIO_CONFIG, TRADING_CONFIG
except ImportError:
    # Fallback configuration if ai_config.py doesn't exist
    AI_STUDIO_CONFIG = {
        "api_key": "",
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
        "take_profit_percent": 0.10,
        "max_daily_trades": 10,
        "trading_hours": {
            "start": "09:15",
            "end": "15:30"
        },
        "update_interval": 5
    }

class AITradingSetup:
    """
    Setup and deployment utilities for AI Trading Bot
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ai_trading_bot.log'),
                logging.StreamHandler()
            ]
        )
    
    def validate_credentials(self, client_id: str, access_token: str, ai_api_key: str) -> bool:
        """
        Validate all required credentials
        
        Args:
            client_id: DhanHQ client ID
            access_token: DhanHQ access token
            ai_api_key: Google AI Studio API key
            
        Returns:
            True if all credentials are valid
        """
        try:
            # Test DhanHQ connection
            dhan_context = DhanContext(client_id, access_token)
            dhan = dhanhq(dhan_context)
            
            # Test basic API call
            funds = dhan.get_fund_limits()
            if funds.get('status') != 'success':
                self.logger.error("Invalid DhanHQ credentials")
                return False
            
            # Test AI Studio connection (would need actual API call)
            if not ai_api_key or len(ai_api_key) < 10:
                self.logger.error("Invalid AI Studio API key")
                return False
            
            self.logger.info("All credentials validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Credential validation failed: {e}")
            return False
    
    def create_environment_file(self, credentials: Dict):
        """
        Create environment file with credentials
        
        Args:
            credentials: Dictionary containing all credentials
        """
        env_content = f"""
# DhanHQ Credentials
DHAN_CLIENT_ID={credentials.get('client_id', '')}
DHAN_ACCESS_TOKEN={credentials.get('access_token', '')}

# Google AI Studio Credentials
AI_STUDIO_API_KEY={credentials.get('ai_api_key', '')}

# Trading Configuration
MIN_CONFIDENCE={TRADING_CONFIG['min_confidence']}
MAX_POSITION_SIZE={TRADING_CONFIG['max_position_size']}
RISK_PER_TRADE={TRADING_CONFIG['risk_per_trade']}
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        self.logger.info("Environment file created successfully")
    
    def setup_database(self):
        """Setup database for storing trading data"""
        # This would setup SQLite or other database for storing:
        # - Trade history
        # - Performance metrics
        # - Market data
        # - AI analysis results
        pass
    
    def create_trading_schedule(self, trading_hours: Dict):
        """
        Create trading schedule configuration
        
        Args:
            trading_hours: Trading hours configuration
        """
        schedule_config = {
            "trading_hours": trading_hours,
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
            json.dump(schedule_config, f, indent=2)
        
        self.logger.info("Trading schedule created successfully")
    
    def setup_monitoring(self):
        """Setup monitoring and alerting"""
        monitoring_config = {
            "alerts": {
                "email": {
                    "enabled": True,
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
        
        self.logger.info("Monitoring configuration created successfully")


class AITradingDeployment:
    """
    Deployment utilities for AI Trading Bot
    """
    
    def __init__(self, bot_config: Dict):
        self.bot_config = bot_config
        self.logger = logging.getLogger(__name__)
    
    def create_dockerfile(self):
        """Create Dockerfile for containerized deployment"""
        dockerfile_content = """
FROM python:3.9-slim

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
        
        self.logger.info("Dockerfile created successfully")
    
    def create_docker_compose(self):
        """Create docker-compose.yml for multi-service deployment"""
        compose_content = """
version: '3.8'

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
      - postgres

  redis:
    image: redis:alpine
    container_name: ai-trading-redis
    ports:
      - "6379:6379"
    restart: unless-stopped

  postgres:
    image: postgres:13
    container_name: ai-trading-postgres
    environment:
      - POSTGRES_DB=ai_trading
      - POSTGRES_USER=trading_user
      - POSTGRES_PASSWORD=trading_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: ai-trading-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - ai-trading-bot
    restart: unless-stopped

volumes:
  postgres_data:
"""
        
        with open('docker-compose.yml', 'w') as f:
            f.write(compose_content)
        
        self.logger.info("Docker Compose file created successfully")
    
    def create_requirements(self):
        """Create requirements.txt for dependencies"""
        requirements = """
# DhanHQ SDK
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
        
        self.logger.info("Requirements file created successfully")
    
    def create_kubernetes_config(self):
        """Create Kubernetes deployment configuration"""
        k8s_config = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-trading-bot
  labels:
    app: ai-trading-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ai-trading-bot
  template:
    metadata:
      labels:
        app: ai-trading-bot
    spec:
      containers:
      - name: ai-trading-bot
        image: ai-trading-bot:latest
        ports:
        - containerPort: 8000
        env:
        - name: DHAN_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: dhan-client-id
        - name: DHAN_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: dhan-access-token
        - name: AI_STUDIO_API_KEY
          valueFrom:
            secretKeyRef:
              name: trading-secrets
              key: ai-studio-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ai-trading-bot-service
spec:
  selector:
    app: ai-trading-bot
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
"""
        
        with open('k8s-deployment.yaml', 'w') as f:
            f.write(k8s_config)
        
        self.logger.info("Kubernetes configuration created successfully")


def main():
    """Main setup function"""
    print("🤖 AI Trading Bot Setup")
    print("=" * 50)
    
    # Get credentials from user
    credentials = {
        'client_id': input("Enter DhanHQ Client ID: "),
        'access_token': input("Enter DhanHQ Access Token: "),
        'ai_api_key': input("Enter Google AI Studio API Key: ")
    }
    
    # Initialize setup
    setup = AITradingSetup()
    
    # Validate credentials
    if not setup.validate_credentials(
        credentials['client_id'],
        credentials['access_token'],
        credentials['ai_api_key']
    ):
        print("❌ Credential validation failed. Please check your credentials.")
        return
    
    # Create environment file
    setup.create_environment_file(credentials)
    
    # Create trading schedule
    setup.create_trading_schedule(TRADING_CONFIG['trading_hours'])
    
    # Setup monitoring
    setup.setup_monitoring()
    
    # Create deployment files
    deployment = AITradingDeployment({})
    deployment.create_requirements()
    deployment.create_dockerfile()
    deployment.create_docker_compose()
    deployment.create_kubernetes_config()
    
    print("✅ AI Trading Bot setup completed successfully!")
    print("\nNext steps:")
    print("1. Review and update configuration files")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the bot: python ai_trading_bot.py")
    print("4. For production: docker-compose up -d")


if __name__ == "__main__":
    main()
