#!/usr/bin/env bash
# Complete AI Trading Bot Deployment Script with All Credentials Pre-filled
# For Mumbai Lightsail VPS with Google AI Platform Integration
set -euo pipefail

########################################
# -------- Pre-filled Configuration -------- #
########################################
DHAN_CLIENT_ID="1105009139"
INITIAL_ACCESS_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzYxMTIyMjE5LCJpYXQiOjE3NjEwMzU4MTksInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA1MDA5MTM5In0.AKCuUDd0XLU5rNzv4Aiod64RX2QQ4CRpm_s9Om6k7M-6Oa_js1wS0M5l0ZW15pLR76ZLWT6ceEXUp7QI9iWaTQ"
SYMBOLS="BANKNIFTY,NIFTY"
POSITION_SIZE="1"
PROJECT_DIR="/home/ubuntu/tradingbot"
PYTHON_BIN="python3.11"
VENVDIR="$PROJECT_DIR/.venv"
SERVICE_NAME="tradingbot"
TOKEN_FILE="/etc/dhan_access_token.txt"
ENV_FILE="/etc/tradingbot.env"
TOKEN_HELPER="/usr/local/bin/dhan_token_update"

# Google AI Platform Integration - PRE-FILLED
GOOGLE_AI_PLATFORM_URL="https://enterprise-live-trading-platform-368435418141.us-west1.run.app"
AI_API_KEY="AIzaSyBn3cecYCygxvPNZDm9MgUHr25Id2zzVa4"
AI_ENABLED="true"

########################################
# ------------- Helpers --------------- #
########################################
log() { printf "\n[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

ensure_pkg() {
  if ! dpkg -s "$1" >/dev/null 2>&1; then
    sudo apt-get -y install "$1"
  fi
}

write_if_missing() {
  local path="$1" owner="$2" perms="$3" payload="$4"
  if [[ -f "$path" ]]; then
    log "$path already exists, leaving in place."
    return
  fi
  log "Creating $path"
  printf '%s\n' "$payload" | sudo tee "$path" >/dev/null
  sudo chown "$owner" "$path"
  sudo chmod "$perms" "$path"
}

########################################
# -------- System preparation -------- #
########################################
log "🚀 Starting AI Trading Bot Deployment..."
log "Dhan Client ID: $DHAN_CLIENT_ID"
log "AI Platform: $GOOGLE_AI_PLATFORM_URL"
log "AI API Key: ${AI_API_KEY:0:10}..."

log "Updating apt cache and upgrading base system…"
sudo apt-get update -y
sudo apt-get upgrade -y

log "Installing essential packages…"
ensure_pkg "build-essential"
ensure_pkg "git"
ensure_pkg "python3.11"
ensure_pkg "python3.11-venv"
ensure_pkg "python3-pip"
ensure_pkg "unzip"
ensure_pkg "curl"
ensure_pkg "fail2ban"
ensure_pkg "ufw"

log "Setting timezone to Asia/Kolkata…"
sudo timedatectl set-timezone Asia/Kolkata

log "Configuring firewall…"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw --force enable

########################################
# -------- Project setup -------- #
########################################
log "Creating project directory…"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

log "Setting up Python virtual environment…"
"$PYTHON_BIN" -m venv "$VENVDIR"
source "$VENVDIR/bin/activate"

log "Upgrading pip…"
pip install --upgrade pip

log "Installing Python dependencies…"
pip install pandas numpy pytz requests websockets python-dotenv

# Try to install dhanhq SDK, fall back gracefully if not available
log "Installing DhanHQ SDK…"
pip install dhanhq || log "DhanHQ SDK not available, will use REST fallback"

########################################
# -------- Secrets setup -------- #
########################################
log "Setting up secrets and configuration…"

# Create environment file with AI integration
write_if_missing "$ENV_FILE" "root:root" "600" "DHAN_CLIENT_ID=$DHAN_CLIENT_ID
DHAN_ACCESS_TOKEN_FILE=$TOKEN_FILE
SYMBOLS=$SYMBOLS
POSITION_SIZE=$POSITION_SIZE
GOOGLE_AI_PLATFORM_URL=$GOOGLE_AI_PLATFORM_URL
AI_API_KEY=$AI_API_KEY
AI_ENABLED=$AI_ENABLED"

# Create token file
write_if_missing "$TOKEN_FILE" "root:root" "600" "$INITIAL_ACCESS_TOKEN"

# Create token update helper
write_if_missing "$TOKEN_HELPER" "root:root" "755" "#!/usr/bin/env bash
set -euo pipefail
TOKFILE=\"$TOKEN_FILE\"

if [[ \$# -ge 1 ]]; then
  NEWTOK=\"\$1\"
else
  echo \"Usage: dhan_token_update <NEW_ACCESS_TOKEN>\"
  exit 1
fi

TMP=\"\$(mktemp)\"
printf \"%s\" \"\$NEWTOK\" > \"\$TMP\"
chmod 600 \"\$TMP\"
chown root:root \"\$TMP\"
mv -f \"\$TMP\" \"\$TOKFILE\"
echo \"Dhan access token updated at \$(date).\"
"

########################################
# -------- Enhanced Bot deployment -------- #
########################################
log "Deploying enhanced trading bot with AI integration…"

# Create enhanced broker.py with AI integration
write_if_missing "$PROJECT_DIR/broker.py" "ubuntu:ubuntu" "644" "from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

import requests


class TokenFile:
    \"\"\"Helper that returns the latest token value when the backing file changes.\"\"\"

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self._token: Optional[str] = None
        self._mtime: Optional[float] = None

    def read(self) -> str:
        \"\"\"Return the current token, reloading when the file timestamp changes.\"\"\"
        try:
            stat = self.path.stat()
            if self._mtime is None or stat.st_mtime > self._mtime:
                self._token = self.path.read_text().strip()
                self._mtime = stat.st_mtime
            return self._token
        except (OSError, IOError) as e:
            raise RuntimeError(f\"Failed to read token file {self.path}: {e}\") from e


@dataclass
class DhanConfig:
    client_id: str
    access_token_file: str
    base_url: str = \"https://api.dhan.co\"


class AIPlatform:
    \"\"\"Google AI Platform integration.\"\"\"
    
    def __init__(self, platform_url: str, api_key: str):
        self.platform_url = platform_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            \"Authorization\": f\"Bearer {api_key}\",
            \"Content-Type\": \"application/json\"
        })
    
    def get_ai_signals(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Get AI-generated trading signals.\"\"\"
        try:
            response = self.session.post(
                f\"{self.platform_url}/api/signals\",
                json=market_data,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f\"AI Platform error: {e}\")
            return {}
    
    def send_trade_data(self, trade_data: Dict[str, Any]) -> bool:
        \"\"\"Send trade data to AI platform for analysis.\"\"\"
        try:
            response = self.session.post(
                f\"{self.platform_url}/api/trades\",
                json=trade_data,
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_market_analysis(self, symbols: list[str]) -> Dict[str, Any]:
        \"\"\"Get AI market analysis for symbols.\"\"\"
        try:
            response = self.session.post(
                f\"{self.platform_url}/api/analysis\",
                json={\"symbols\": symbols},
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            print(f\"AI Analysis error: {e}\")
            return {}


class DhanBroker:
    \"\"\"Enhanced DhanHQ broker with AI integration.\"\"\"

    def __init__(self, config: DhanConfig, ai_platform: Optional[AIPlatform] = None) -> None:
        self.config = config
        self.token_file = TokenFile(config.access_token_file)
        self.ai_platform = ai_platform
        self.session = requests.Session()
        self.session.headers.update({
            \"Content-Type\": \"application/json\"
        })

    def _get_headers(self) -> Dict[str, str]:
        \"\"\"Get headers with current access token.\"\"\"
        return {
            \"Authorization\": f\"Bearer {self.token_file.read()}\",
            \"Content-Type\": \"application/json\"
        }

    def test_connection(self) -> bool:
        \"\"\"Test connection to DhanHQ.\"\"\"
        try:
            response = self.session.get(
                f\"{self.config.base_url}/api/v1/profile\",
                headers=self._get_headers(),
                timeout=10
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_account_info(self) -> Dict[str, Any]:
        \"\"\"Get account information.\"\"\"
        try:
            response = self.session.get(
                f\"{self.config.base_url}/api/v1/profile\",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception:
            return {}

    def get_positions(self) -> Dict[str, Any]:
        \"\"\"Get current positions.\"\"\"
        try:
            response = self.session.get(
                f\"{self.config.base_url}/api/v1/positions\",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception:
            return {}

    def get_orders(self) -> Dict[str, Any]:
        \"\"\"Get current orders.\"\"\"
        try:
            response = self.session.get(
                f\"{self.config.base_url}/api/v1/orders\",
                headers=self._get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception:
            return {}

    def place_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        order_type: str = \"MARKET\",
        product_type: str = \"INTRADAY\",
        validity: str = \"DAY\"
    ) -> Dict[str, Any]:
        \"\"\"Place an order with AI integration.\"\"\"
        try:
            order_data = {
                \"dhanClientId\": self.config.client_id,
                \"transactionType\": side,
                \"exchangeSegment\": \"NSE\",
                \"productType\": product_type,
                \"orderType\": order_type,
                \"validity\": validity,
                \"tradingSymbol\": symbol,
                \"securityId\": symbol,
                \"quantity\": quantity,
                \"price\": price,
                \"disclosedQuantity\": 0,
                \"offMarketFlag\": False,
                \"stopPrice\": 0,
                \"squareOff\": 0,
                \"trailingStop\": 0,
                \"boProfitValue\": 0,
                \"boStopLossValue\": 0,
                \"boTrailingStop\": 0
            }

            response = self.session.post(
                f\"{self.config.base_url}/api/v1/orders\",
                json=order_data,
                headers=self._get_headers(),
                timeout=15
            )

            result = {}
            if response.status_code == 200:
                result = response.json()
            else:
                result = {\"success\": False, \"error\": response.text}

            # Send trade data to AI platform for analysis
            if self.ai_platform and result.get(\"success\", False):
                trade_data = {
                    \"symbol\": symbol,
                    \"side\": side,
                    \"quantity\": quantity,
                    \"price\": price,
                    \"timestamp\": str(datetime.now()),
                    \"order_id\": result.get(\"orderId\", \"\")
                }
                self.ai_platform.send_trade_data(trade_data)

            return result
        except Exception as e:
            return {\"success\": False, \"error\": str(e)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        \"\"\"Cancel an order.\"\"\"
        try:
            response = self.session.delete(
                f\"{self.config.base_url}/api/v1/orders/{order_id}\",
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {\"success\": False, \"error\": response.text}
        except Exception as e:
            return {\"success\": False, \"error\": str(e)}

    def get_quotes(self, symbols: list[str]) -> Dict[str, Any]:
        \"\"\"Get quotes for symbols.\"\"\"
        try:
            quote_data = {
                \"IDX_I\": symbols
            }

            response = self.session.post(
                f\"{self.config.base_url}/api/v1/quotes\",
                json=quote_data,
                headers=self._get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception:
            return {}

    def get_ai_signals(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Get AI-generated trading signals.\"\"\"
        if self.ai_platform:
            return self.ai_platform.get_ai_signals(market_data)
        return {}

    def get_market_analysis(self, symbols: list[str]) -> Dict[str, Any]:
        \"\"\"Get AI market analysis.\"\"\"
        if self.ai_platform:
            return self.ai_platform.get_market_analysis(symbols)
        return {}


def main():
    \"\"\"Main function for testing.\"\"\"
    config = DhanConfig(
        client_id=os.environ.get(\"DHAN_CLIENT_ID\", \"\"),
        access_token_file=os.environ.get(\"DHAN_ACCESS_TOKEN_FILE\", \"/etc/dhan_access_token.txt\")
    )

    # Initialize AI platform if enabled
    ai_platform = None
    if os.environ.get(\"AI_ENABLED\", \"false\").lower() == \"true\":
        ai_platform = AIPlatform(
            platform_url=os.environ.get(\"GOOGLE_AI_PLATFORM_URL\", \"\"),
            api_key=os.environ.get(\"AI_API_KEY\", \"\")
        )

    broker = DhanBroker(config, ai_platform)

    if broker.test_connection():
        print(\"Connection successful\")
        print(\"Account info:\", broker.get_account_info())
        
        if ai_platform:
            print(\"AI Platform connected\")
            # Test AI integration
            test_data = {\"symbols\": [\"BANKNIFTY\", \"NIFTY\"]}
            ai_signals = broker.get_ai_signals(test_data)
            print(\"AI Signals:\", ai_signals)
    else:
        print(\"Connection failed\")
        sys.exit(1)


if __name__ == \"__main__\":
    main()
"

# Create enhanced run_bot.py with AI integration
write_if_missing "$PROJECT_DIR/run_bot.py" "ubuntu:ubuntu" "644" "#!/usr/bin/env python3
\"\"\"Enhanced bot runner script with AI integration.\"\"\"

import os
import sys
import time
import signal
import logging
from datetime import datetime
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

from broker import DhanBroker, DhanConfig, AIPlatform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/tradingbot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class TradingBot:
    \"\"\"Enhanced trading bot with AI integration.\"\"\"

    def __init__(self):
        self.config = DhanConfig(
            client_id=os.environ.get('DHAN_CLIENT_ID', ''),
            access_token_file=os.environ.get('DHAN_ACCESS_TOKEN_FILE', '/etc/dhan_access_token.txt')
        )
        
        # Initialize AI platform if enabled
        self.ai_platform = None
        if os.environ.get('AI_ENABLED', 'false').lower() == 'true':
            self.ai_platform = AIPlatform(
                platform_url=os.environ.get('GOOGLE_AI_PLATFORM_URL', ''),
                api_key=os.environ.get('AI_API_KEY', '')
            )
            logger.info(f\"AI Platform initialized: {os.environ.get('GOOGLE_AI_PLATFORM_URL', '')}\")
        
        self.broker = DhanBroker(self.config, self.ai_platform)
        self.running = False

        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        \"\"\"Handle shutdown signals.\"\"\"
        logger.info(f\"Received signal {signum}, shutting down...\")
        self.running = False

    def start(self):
        \"\"\"Start the enhanced trading bot.\"\"\"
        try:
            logger.info(\"🚀 Starting enhanced trading bot with AI integration...\")

            # Test connection
            if not self.broker.test_connection():
                logger.error(\"❌ Failed to connect to DhanHQ\")
                return

            logger.info(\"✅ Connected to DhanHQ successfully\")

            # Test AI platform connection
            if self.ai_platform:
                logger.info(\"🤖 Testing AI platform connection...\")
                test_data = {\"symbols\": [\"BANKNIFTY\", \"NIFTY\"]}
                ai_signals = self.broker.get_ai_signals(test_data)
                if ai_signals:
                    logger.info(\"✅ AI Platform connected successfully\")
                else:
                    logger.warning(\"⚠️ AI Platform connection failed, continuing without AI\")

            # Get account info
            account_info = self.broker.get_account_info()
            logger.info(f\"📊 Account info: {account_info}\")

            # Start main loop
            self.running = True
            loop_count = 0
            
            while self.running:
                loop_count += 1
                
                # Get current positions
                positions = self.broker.get_positions()
                logger.info(f\"📈 Current positions: {positions}\")

                # Get current orders
                orders = self.broker.get_orders()
                logger.info(f\"📋 Current orders: {orders}\")

                # Get AI signals every 10 loops (50 seconds)
                if self.ai_platform and loop_count % 10 == 0:
                    logger.info(\"🤖 Getting AI signals...\")
                    market_data = {
                        \"symbols\": [\"BANKNIFTY\", \"NIFTY\"],
                        \"positions\": positions,
                        \"orders\": orders,
                        \"timestamp\": datetime.now().isoformat()
                    }
                    ai_signals = self.broker.get_ai_signals(market_data)
                    if ai_signals:
                        logger.info(f\"🎯 AI Signals: {ai_signals}\")
                        
                        # Process AI signals (implement your logic here)
                        self._process_ai_signals(ai_signals)

                # Heartbeat
                logger.info(\"💓 heartbeat ok | decision={}\")

                # Sleep for 5 seconds
                time.sleep(5)

        except Exception as e:
            logger.error(f\"❌ Error in trading bot: {e}\")
        finally:
            logger.info(\"🛑 Trading bot stopped\")

    def _process_ai_signals(self, ai_signals: dict):
        \"\"\"Process AI-generated signals.\"\"\"
        try:
            # Implement your AI signal processing logic here
            # This is where you would analyze AI signals and make trading decisions
            logger.info(f\"🧠 Processing AI signals: {ai_signals}\")
            
            # Example: Check for buy/sell signals
            if \"signals\" in ai_signals:
                for signal in ai_signals[\"signals\"]:
                    symbol = signal.get(\"symbol\", \"\")
                    action = signal.get(\"action\", \"\")
                    confidence = signal.get(\"confidence\", 0.0)
                    
                    if confidence > 0.7:  # Only act on high-confidence signals
                        logger.info(f\"🎯 High confidence AI signal: {symbol} {action} (confidence: {confidence})\")
                        # Implement your trading logic here
                        
        except Exception as e:
            logger.error(f\"❌ Error processing AI signals: {e}\")

    def stop(self):
        \"\"\"Stop the trading bot.\"\"\"
        logger.info(\"🛑 Stopping trading bot...\")
        self.running = False


def main():
    \"\"\"Main function.\"\"\"
    bot = TradingBot()
    try:
        bot.start()
    except KeyboardInterrupt:
        logger.info(\"Received keyboard interrupt\")
    except Exception as e:
        logger.error(f\"Unexpected error: {e}\")
    finally:
        bot.stop()


if __name__ == \"__main__\":
    main()
"

# Create enhanced strategy.py with AI integration
write_if_missing "$PROJECT_DIR/strategy.py" "ubuntu:ubuntu" "644" "from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class Signal:
    \"\"\"Enhanced trading signal with AI confidence.\"\"\"
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    strategy: str
    timestamp: datetime
    confidence: float = 0.0
    ai_generated: bool = False


class BaseStrategy(ABC):
    \"\"\"Base strategy class with AI integration.\"\"\"

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.positions = {}
        self.orders = {}
        self.ai_signals = {}

    @abstractmethod
    def generate_signals(
        self,
        timestamp: datetime,
        market_data: Dict[str, Any],
        positions: Dict[str, Any],
        ai_signals: Optional[Dict[str, Any]] = None
    ) -> List[Signal]:
        \"\"\"Generate trading signals with optional AI input.\"\"\"
        pass

    def initialize(self, universe: List[str], config: Dict[str, Any]):
        \"\"\"Initialize the strategy.\"\"\"
        self.universe = universe
        self.config = config

    def update_ai_signals(self, ai_signals: Dict[str, Any]):
        \"\"\"Update AI signals for strategy use.\"\"\"
        self.ai_signals = ai_signals

    def get_strategy_info(self) -> Dict[str, Any]:
        \"\"\"Get strategy information.\"\"\"
        return {
            \"strategy_name\": self.__class__.__name__,
            \"universe\": getattr(self, 'universe', []),
            \"positions\": self.positions,
            \"orders\": self.orders,
            \"ai_signals_count\": len(self.ai_signals)
        }


class AISimpleStrategy(BaseStrategy):
    \"\"\"AI-enhanced simple strategy.\"\"\"

    def generate_signals(
        self,
        timestamp: datetime,
        market_data: Dict[str, Any],
        positions: Dict[str, Any],
        ai_signals: Optional[Dict[str, Any]] = None
    ) -> List[Signal]:
        \"\"\"Generate AI-enhanced signals.\"\"\"
        signals = []

        # Process AI signals if available
        if ai_signals and \"signals\" in ai_signals:
            for ai_signal in ai_signals[\"signals\"]:
                symbol = ai_signal.get(\"symbol\", \"\")
                action = ai_signal.get(\"action\", \"\")
                confidence = ai_signal.get(\"confidence\", 0.0)
                
                if confidence > 0.7:  # Only use high-confidence AI signals
                    signals.append(Signal(
                        symbol=symbol,
                        side=action.upper(),
                        quantity=1,
                        price=100.0,  # Placeholder price
                        strategy='ai_enhanced',
                        timestamp=timestamp,
                        confidence=confidence,
                        ai_generated=True
                    ))

        # Fallback to simple logic if no AI signals
        if not signals:
            for symbol in self.universe:
                if symbol not in positions:
                    signals.append(Signal(
                        symbol=symbol,
                        side='BUY',
                        quantity=1,
                        price=100.0,
                        strategy='simple_fallback',
                        timestamp=timestamp,
                        confidence=0.5,
                        ai_generated=False
                    ))

        return signals
"

########################################
# -------- Systemd service -------- #
########################################
log "Creating systemd service…"

write_if_missing "/etc/systemd/system/$SERVICE_NAME.service" "root:root" "644" "[Unit]
Description=Enhanced AI Trading Bot (Dhan + Google AI)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$PROJECT_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$VENVDIR/bin/python $PROJECT_DIR/run_bot.py
Restart=always
RestartSec=3
KillSignal=SIGTERM
StandardOutput=append:/var/log/tradingbot.log
StandardError=append:/var/log/tradingbot.log

[Install]
WantedBy=multi-user.target
"

########################################
# -------- Final setup -------- #
########################################
log "Enabling and starting enhanced service…"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

log "Checking service status…"
sudo systemctl status "$SERVICE_NAME" --no-pager

log "🎉 Enhanced AI Trading Bot deployment completed successfully!"
log "📊 Bot logs: sudo tail -f /var/log/tradingbot.log"
log "🔧 Service control: sudo systemctl start/stop/restart $SERVICE_NAME"
log "🔄 Token update: sudo $TOKEN_HELPER <NEW_TOKEN>"
log "🤖 AI Platform: $GOOGLE_AI_PLATFORM_URL"
log "🔑 AI API Key: ${AI_API_KEY:0:10}..."
log "📈 Dhan Client: $DHAN_CLIENT_ID"
log "🌍 Mumbai VPS: Ready for low-latency trading!"
"
