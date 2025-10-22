"""
Live dashboard server for the Liquid F&O Trading System.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from ..config import config
from ..utils.timezone import ISTTimezone

# Initialize FastAPI app
app = FastAPI(title="Liquid F&O Trading Dashboard", version="1.0.0")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.logger = logging.getLogger(__name__)
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                self.logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

# Dashboard data
dashboard_data = {
    "system_status": {
        "timestamp": ISTTimezone.now().isoformat(),
        "market_status": "Open" if ISTTimezone.is_market_hours() else "Closed",
        "live_trading": config.is_live_trading_enabled,
        "options_enabled": config.is_options_enabled
    },
    "portfolio": {
        "total_pnl": 0.0,
        "daily_pnl": 0.0,
        "max_drawdown": 0.0,
        "total_trades": 0,
        "win_rate": 0.0
    },
    "positions": [],
    "orders": [],
    "risk_metrics": {
        "portfolio_delta": 0.0,
        "portfolio_gamma": 0.0,
        "portfolio_theta": 0.0,
        "portfolio_vega": 0.0,
        "margin_used": 0.0,
        "margin_available": 1000000.0
    },
    "strategies": [
        {
            "name": "Donchian Breakout",
            "status": "Active",
            "pnl": 0.0,
            "trades": 0,
            "win_rate": 0.0
        },
        {
            "name": "Iron Butterfly",
            "status": "Active",
            "pnl": 0.0,
            "trades": 0,
            "win_rate": 0.0
        }
    ]
}

@app.get("/")
async def get_dashboard():
    """Serve the main dashboard page."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Liquid F&O Trading Dashboard</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            .dashboard {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }
            .card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .card h3 {
                margin-top: 0;
                color: #333;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            .metric {
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 5px;
            }
            .metric .label {
                font-weight: bold;
                color: #666;
            }
            .metric .value {
                color: #333;
                font-weight: bold;
            }
            .positive { color: #28a745; }
            .negative { color: #dc3545; }
            .status-active { color: #28a745; }
            .status-inactive { color: #dc3545; }
            .status-paper { color: #ffc107; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Liquid F&O Trading Dashboard</h1>
            <p>Real-time monitoring and control</p>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <h3>📊 System Status</h3>
                <div class="metric">
                    <span class="label">Market Status:</span>
                    <span class="value" id="market-status">Loading...</span>
                </div>
                <div class="metric">
                    <span class="label">Trading Mode:</span>
                    <span class="value" id="trading-mode">Loading...</span>
                </div>
                <div class="metric">
                    <span class="label">Last Update:</span>
                    <span class="value" id="last-update">Loading...</span>
                </div>
            </div>
            
            <div class="card">
                <h3>💰 Portfolio</h3>
                <div class="metric">
                    <span class="label">Total P&L:</span>
                    <span class="value" id="total-pnl">₹0.00</span>
                </div>
                <div class="metric">
                    <span class="label">Daily P&L:</span>
                    <span class="value" id="daily-pnl">₹0.00</span>
                </div>
                <div class="metric">
                    <span class="label">Max Drawdown:</span>
                    <span class="value" id="max-dd">0.00%</span>
                </div>
                <div class="metric">
                    <span class="label">Total Trades:</span>
                    <span class="value" id="total-trades">0</span>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Strategies</h3>
                <div id="strategies-list">
                    <div class="metric">
                        <span class="label">Donchian Breakout:</span>
                        <span class="value status-active">Active</span>
                    </div>
                    <div class="metric">
                        <span class="label">Iron Butterfly:</span>
                        <span class="value status-active">Active</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🛡️ Risk Metrics</h3>
                <div class="metric">
                    <span class="label">Portfolio Delta:</span>
                    <span class="value" id="portfolio-delta">0.00</span>
                </div>
                <div class="metric">
                    <span class="label">Portfolio Gamma:</span>
                    <span class="value" id="portfolio-gamma">0.00</span>
                </div>
                <div class="metric">
                    <span class="label">Portfolio Theta:</span>
                    <span class="value" id="portfolio-theta">0.00</span>
                </div>
                <div class="metric">
                    <span class="label">Margin Used:</span>
                    <span class="value" id="margin-used">₹0.00</span>
                </div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket("ws://localhost:8787/ws");
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            function updateDashboard(data) {
                // Update system status
                document.getElementById('market-status').textContent = data.system_status.market_status;
                document.getElementById('trading-mode').textContent = data.system_status.live_trading ? 'Live' : 'Paper';
                document.getElementById('last-update').textContent = new Date(data.system_status.timestamp).toLocaleTimeString();
                
                // Update portfolio
                document.getElementById('total-pnl').textContent = '₹' + data.portfolio.total_pnl.toFixed(2);
                document.getElementById('daily-pnl').textContent = '₹' + data.portfolio.daily_pnl.toFixed(2);
                document.getElementById('max-dd').textContent = (data.portfolio.max_drawdown * 100).toFixed(2) + '%';
                document.getElementById('total-trades').textContent = data.portfolio.total_trades;
                
                // Update risk metrics
                document.getElementById('portfolio-delta').textContent = data.risk_metrics.portfolio_delta.toFixed(2);
                document.getElementById('portfolio-gamma').textContent = data.risk_metrics.portfolio_gamma.toFixed(2);
                document.getElementById('portfolio-theta').textContent = data.risk_metrics.portfolio_theta.toFixed(2);
                document.getElementById('margin-used').textContent = '₹' + data.risk_metrics.margin_used.toFixed(2);
                
                // Add color coding
                const totalPnl = document.getElementById('total-pnl');
                const dailyPnl = document.getElementById('daily-pnl');
                
                if (data.portfolio.total_pnl >= 0) {
                    totalPnl.className = 'value positive';
                } else {
                    totalPnl.className = 'value negative';
                }
                
                if (data.portfolio.daily_pnl >= 0) {
                    dailyPnl.className = 'value positive';
                } else {
                    dailyPnl.className = 'value negative';
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Send current dashboard data
            await manager.send_personal_message(
                json.dumps(dashboard_data, default=str), 
                websocket
            )
            await asyncio.sleep(5)  # Update every 5 seconds
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/status")
async def get_status():
    """Get current system status."""
    return dashboard_data

@app.get("/api/portfolio")
async def get_portfolio():
    """Get portfolio data."""
    return dashboard_data["portfolio"]

@app.get("/api/positions")
async def get_positions():
    """Get current positions."""
    return dashboard_data["positions"]

@app.get("/api/orders")
async def get_orders():
    """Get current orders."""
    return dashboard_data["orders"]

@app.get("/api/risk")
async def get_risk_metrics():
    """Get risk metrics."""
    return dashboard_data["risk_metrics"]

@app.get("/api/strategies")
async def get_strategies():
    """Get strategy status."""
    return dashboard_data["strategies"]

async def update_dashboard_data():
    """Update dashboard data periodically."""
    while True:
        try:
            # Update timestamp
            dashboard_data["system_status"]["timestamp"] = ISTTimezone.now().isoformat()
            dashboard_data["system_status"]["market_status"] = "Open" if ISTTimezone.is_market_hours() else "Closed"
            
            # Simulate some data updates
            dashboard_data["portfolio"]["total_pnl"] += 100.0  # Simulate P&L change
            dashboard_data["portfolio"]["daily_pnl"] += 50.0
            
            # Broadcast update to all connected clients
            await manager.broadcast(json.dumps(dashboard_data, default=str))
            
            await asyncio.sleep(10)  # Update every 10 seconds
            
        except Exception as e:
            logging.error(f"Failed to update dashboard data: {e}")
            await asyncio.sleep(10)

def start_dashboard_server(host: str = "localhost", port: int = 8787):
    """Start the dashboard server."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting dashboard server on {host}:{port}")
    logger.info(f"Dashboard available at: http://{host}:{port}")
    
    # Start the update task
    asyncio.create_task(update_dashboard_data())
    
    # Run the server
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_dashboard_server()
