#!/usr/bin/env python3
"""
Interactive credential configuration for AI Trading Bot
This script helps you configure your credentials securely
"""

import os
import getpass
from pathlib import Path

def configure_credentials():
    """
    Interactive credential configuration
    """
    print("🔐 AI Trading Bot Credential Configuration")
    print("=" * 50)
    print("This script will help you configure your trading bot credentials.")
    print("Your credentials will be stored in the .env file.\n")
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found. Please run setup_ai_trading.py first.")
        return
    
    # Read current .env content
    with open(".env", "r") as f:
        current_content = f.read()
    
    print("📋 Current .env file content:")
    print("-" * 30)
    print(current_content)
    print("-" * 30)
    print()
    
    # Get credentials from user
    print("Please enter your credentials:")
    print("(Press Enter to keep current value, or type 'skip' to skip)")
    print()
    
    # DhanHQ Credentials
    print("🏦 DhanHQ Credentials:")
    dhan_client_id = input("DhanHQ Client ID: ").strip()
    if dhan_client_id.lower() == 'skip':
        dhan_client_id = "your_client_id_here"
    
    dhan_access_token = getpass.getpass("DhanHQ Access Token: ").strip()
    if dhan_access_token.lower() == 'skip':
        dhan_access_token = "your_access_token_here"
    
    print()
    
    # Google AI Studio Credentials
    print("🤖 Google AI Studio Credentials:")
    ai_studio_api_key = getpass.getpass("Google AI Studio API Key: ").strip()
    if ai_studio_api_key.lower() == 'skip':
        ai_studio_api_key = "your_ai_studio_api_key_here"
    
    print()
    
    # Trading Configuration
    print("⚙️  Trading Configuration (optional - press Enter for defaults):")
    
    min_confidence = input("Minimum AI Confidence (0.0-1.0) [0.7]: ").strip() or "0.7"
    max_position_size = input("Max Position Size [1000]: ").strip() or "1000"
    risk_per_trade = input("Risk per Trade (0.0-1.0) [0.02]: ").strip() or "0.02"
    
    print()
    
    # Create new .env content
    new_content = f"""# DhanHQ Credentials
DHAN_CLIENT_ID={dhan_client_id}
DHAN_ACCESS_TOKEN={dhan_access_token}

# Google AI Studio Credentials
AI_STUDIO_API_KEY={ai_studio_api_key}

# Trading Configuration
MIN_CONFIDENCE={min_confidence}
MAX_POSITION_SIZE={max_position_size}
RISK_PER_TRADE={risk_per_trade}
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
    
    # Show preview
    print("📝 New .env file content:")
    print("-" * 30)
    print(new_content)
    print("-" * 30)
    print()
    
    # Confirm save
    confirm = input("Save these credentials? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        # Backup original file
        backup_file = ".env.backup"
        with open(backup_file, "w") as f:
            f.write(current_content)
        print(f"✅ Original .env backed up to {backup_file}")
        
        # Save new content
        with open(".env", "w") as f:
            f.write(new_content)
        print("✅ Credentials saved to .env file")
        
        # Set secure permissions
        os.chmod(".env", 0o600)
        print("✅ File permissions set to secure mode")
        
        print("\n🎉 Configuration complete!")
        print("\n📋 Next steps:")
        print("1. Test your credentials: python test_credentials.py")
        print("2. Run the AI trading bot: python run_ai_trading.py")
        print("3. For production: docker-compose up -d")
        
    else:
        print("❌ Configuration cancelled. No changes made.")
    
    print("\n🔒 Security Note:")
    print("- Your .env file contains sensitive credentials")
    print("- Never commit this file to version control")
    print("- Keep your credentials secure and private")

def test_credentials():
    """
    Test the configured credentials
    """
    print("🧪 Testing AI Trading Bot Credentials")
    print("=" * 40)
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        client_id = os.getenv('DHAN_CLIENT_ID')
        access_token = os.getenv('DHAN_ACCESS_TOKEN')
        ai_api_key = os.getenv('AI_STUDIO_API_KEY')
        
        if not client_id or client_id == "your_client_id_here":
            print("❌ DhanHQ Client ID not configured")
            return False
            
        if not access_token or access_token == "your_access_token_here":
            print("❌ DhanHQ Access Token not configured")
            return False
            
        if not ai_api_key or ai_api_key == "your_ai_studio_api_key_here":
            print("❌ Google AI Studio API Key not configured")
            return False
        
        print("✅ All credentials are configured")
        
        # Test DhanHQ connection
        try:
            from dhanhq import DhanContext, dhanhq
            dhan_context = DhanContext(client_id, access_token)
            dhan = dhanhq(dhan_context)
            
            # Test basic API call
            funds = dhan.get_fund_limits()
            if funds.get('status') == 'success':
                print("✅ DhanHQ connection successful")
            else:
                print("❌ DhanHQ connection failed")
                return False
                
        except Exception as e:
            print(f"❌ DhanHQ connection error: {e}")
            return False
        
        print("✅ All credentials are valid and working!")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error testing credentials: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_credentials()
    else:
        configure_credentials()

