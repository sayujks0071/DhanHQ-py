#!/usr/bin/env python3
"""
Trading Configuration Tuning Script
This script helps you optimize TRADING_CONFIG parameters for your capital and risk tolerance
"""

import json
from typing import Dict, List

def calculate_optimal_config(capital: float, risk_tolerance: str = "moderate") -> Dict:
    """
    Calculate optimal trading configuration based on capital and risk tolerance
    
    Args:
        capital: Available trading capital
        risk_tolerance: "conservative", "moderate", or "aggressive"
    
    Returns:
        Optimized trading configuration
    """
    
    # Risk tolerance multipliers
    risk_multipliers = {
        "conservative": {
            "risk_per_trade": 0.005,  # 0.5%
            "max_position_size": 0.1,  # 10% of capital
            "min_confidence": 0.8,     # 80% confidence
            "max_daily_trades": 5,
            "stop_loss_percent": 0.03,  # 3%
            "take_profit_percent": 0.06  # 6%
        },
        "moderate": {
            "risk_per_trade": 0.01,   # 1%
            "max_position_size": 0.2,  # 20% of capital
            "min_confidence": 0.7,     # 70% confidence
            "max_daily_trades": 10,
            "stop_loss_percent": 0.05,  # 5%
            "take_profit_percent": 0.10  # 10%
        },
        "aggressive": {
            "risk_per_trade": 0.02,   # 2%
            "max_position_size": 0.3,  # 30% of capital
            "min_confidence": 0.6,     # 60% confidence
            "max_daily_trades": 20,
            "stop_loss_percent": 0.08,  # 8%
            "take_profit_percent": 0.15  # 15%
        }
    }
    
    config = risk_multipliers.get(risk_tolerance, risk_multipliers["moderate"])
    
    # Calculate position size based on capital
    max_position_value = capital * config["max_position_size"]
    max_position_size = int(max_position_value / 1000)  # Assuming average stock price of ₹1000
    
    return {
        "min_confidence": config["min_confidence"],
        "max_position_size": max_position_size,
        "risk_per_trade": config["risk_per_trade"],
        "stop_loss_percent": config["stop_loss_percent"],
        "take_profit_percent": config["take_profit_percent"],
        "max_daily_trades": config["max_daily_trades"],
        "trading_hours": {
            "start": "09:15",
            "end": "15:30"
        },
        "update_interval": 5,
        "funds_cache_ttl": 60,
        "lookback_ticks": 120,
        "allow_short_selling": False
    }

def analyze_current_config(config: Dict, capital: float) -> Dict:
    """
    Analyze current configuration and provide recommendations
    
    Args:
        config: Current trading configuration
        capital: Available trading capital
    
    Returns:
        Analysis and recommendations
    """
    analysis = {
        "current_config": config,
        "capital": capital,
        "recommendations": [],
        "risk_assessment": {},
        "optimization_suggestions": []
    }
    
    # Risk assessment
    risk_per_trade = config.get("risk_per_trade", 0.02)
    max_position_size = config.get("max_position_size", 1000)
    min_confidence = config.get("min_confidence", 0.7)
    
    # Calculate risk metrics
    max_risk_per_trade = capital * risk_per_trade
    max_position_value = max_position_size * 1000  # Assuming average price
    
    analysis["risk_assessment"] = {
        "max_risk_per_trade": max_risk_per_trade,
        "max_position_value": max_position_value,
        "risk_percentage": (max_risk_per_trade / capital) * 100,
        "position_percentage": (max_position_value / capital) * 100
    }
    
    # Generate recommendations
    if risk_per_trade > 0.02:
        analysis["recommendations"].append("⚠️  Risk per trade is high (>2%). Consider reducing to 1-2%")
    
    if min_confidence < 0.7:
        analysis["recommendations"].append("⚠️  Minimum confidence is low (<70%). Consider increasing to 70-80%")
    
    if max_position_size > capital * 0.3:
        analysis["recommendations"].append("⚠️  Maximum position size is large (>30% of capital). Consider reducing")
    
    if max_position_size < capital * 0.05:
        analysis["recommendations"].append("💡 Maximum position size is small (<5% of capital). You might be too conservative")
    
    # Optimization suggestions
    if capital < 50000:
        analysis["optimization_suggestions"].append("💡 With capital < ₹50k, consider conservative settings")
    elif capital > 500000:
        analysis["optimization_suggestions"].append("💡 With capital > ₹5L, you can afford moderate risk settings")
    
    return analysis

def create_configuration_presets() -> Dict[str, Dict]:
    """Create predefined configuration presets for different scenarios"""
    
    presets = {
        "beginner": {
            "description": "For beginners with small capital",
            "capital_range": "₹10k - ₹50k",
            "config": {
                "min_confidence": 0.8,
                "max_position_size": 5,
                "risk_per_trade": 0.005,
                "stop_loss_percent": 0.03,
                "take_profit_percent": 0.06,
                "max_daily_trades": 3,
                "trading_hours": {"start": "09:15", "end": "15:30"},
                "update_interval": 10,
                "allow_short_selling": False
            }
        },
        "conservative": {
            "description": "Conservative approach for capital preservation",
            "capital_range": "₹50k - ₹2L",
            "config": {
                "min_confidence": 0.75,
                "max_position_size": 20,
                "risk_per_trade": 0.01,
                "stop_loss_percent": 0.04,
                "take_profit_percent": 0.08,
                "max_daily_trades": 5,
                "trading_hours": {"start": "09:15", "end": "15:30"},
                "update_interval": 5,
                "allow_short_selling": False
            }
        },
        "moderate": {
            "description": "Balanced approach for steady growth",
            "capital_range": "₹2L - ₹10L",
            "config": {
                "min_confidence": 0.7,
                "max_position_size": 50,
                "risk_per_trade": 0.015,
                "stop_loss_percent": 0.05,
                "take_profit_percent": 0.10,
                "max_daily_trades": 10,
                "trading_hours": {"start": "09:15", "end": "15:30"},
                "update_interval": 5,
                "allow_short_selling": False
            }
        },
        "aggressive": {
            "description": "Aggressive approach for experienced traders",
            "capital_range": "₹10L+",
            "config": {
                "min_confidence": 0.65,
                "max_position_size": 100,
                "risk_per_trade": 0.02,
                "stop_loss_percent": 0.06,
                "take_profit_percent": 0.12,
                "max_daily_trades": 15,
                "trading_hours": {"start": "09:15", "end": "15:30"},
                "update_interval": 3,
                "allow_short_selling": True
            }
        }
    }
    
    return presets

def main():
    """Main configuration tuning interface"""
    print("⚙️  AI Trading Bot Configuration Tuner")
    print("=" * 50)
    
    # Get user input
    try:
        capital = float(input("Enter your available trading capital (₹): "))
        risk_tolerance = input("Enter risk tolerance (conservative/moderate/aggressive) [moderate]: ").strip().lower()
        if not risk_tolerance:
            risk_tolerance = "moderate"
    except (ValueError, KeyboardInterrupt):
        print("❌ Invalid input. Using default values.")
        capital = 100000
        risk_tolerance = "moderate"
    
    print(f"\n💰 Capital: ₹{capital:,.2f}")
    print(f"🎯 Risk Tolerance: {risk_tolerance}")
    print()
    
    # Calculate optimal configuration
    optimal_config = calculate_optimal_config(capital, risk_tolerance)
    
    print("📊 OPTIMAL CONFIGURATION")
    print("-" * 30)
    print(json.dumps(optimal_config, indent=2))
    print()
    
    # Show presets
    presets = create_configuration_presets()
    print("📋 CONFIGURATION PRESETS")
    print("-" * 30)
    
    for name, preset in presets.items():
        print(f"\n{name.upper()}: {preset['description']}")
        print(f"Capital Range: {preset['capital_range']}")
        print(f"Key Settings:")
        config = preset['config']
        print(f"  - Min Confidence: {config['min_confidence']}")
        print(f"  - Max Position Size: {config['max_position_size']}")
        print(f"  - Risk Per Trade: {config['risk_per_trade']}")
        print(f"  - Max Daily Trades: {config['max_daily_trades']}")
    
    # Analysis of current config
    print(f"\n🔍 CONFIGURATION ANALYSIS")
    print("-" * 30)
    
    analysis = analyze_current_config(optimal_config, capital)
    
    print(f"Risk Assessment:")
    risk = analysis['risk_assessment']
    print(f"  - Max Risk Per Trade: ₹{risk['max_risk_per_trade']:,.2f}")
    print(f"  - Max Position Value: ₹{risk['max_position_value']:,.2f}")
    print(f"  - Risk Percentage: {risk['risk_percentage']:.2f}%")
    print(f"  - Position Percentage: {risk['position_percentage']:.2f}%")
    
    if analysis['recommendations']:
        print(f"\nRecommendations:")
        for rec in analysis['recommendations']:
            print(f"  {rec}")
    
    if analysis['optimization_suggestions']:
        print(f"\nOptimization Suggestions:")
        for suggestion in analysis['optimization_suggestions']:
            print(f"  {suggestion}")
    
    # Generate configuration file
    print(f"\n💾 GENERATING CONFIGURATION FILE")
    print("-" * 30)
    
    config_content = f"""# AI Trading Bot Configuration
# Generated for capital: ₹{capital:,.2f}
# Risk tolerance: {risk_tolerance}

TRADING_CONFIG = {json.dumps(optimal_config, indent=4)}

# Usage in your bot:
# bot = AITradingBot(
#     client_id="your_client_id",
#     access_token="your_access_token", 
#     ai_studio_api_key="your_ai_studio_api_key",
#     trading_config=TRADING_CONFIG
# )
"""
    
    with open('optimized_trading_config.py', 'w') as f:
        f.write(config_content)
    
    print("✅ Configuration saved to: optimized_trading_config.py")
    print("\n📋 Next Steps:")
    print("1. Review the optimized configuration above")
    print("2. Test with paper trading using the optimized settings")
    print("3. Adjust parameters based on your specific needs")
    print("4. Deploy with real credentials when ready")

if __name__ == "__main__":
    main()



