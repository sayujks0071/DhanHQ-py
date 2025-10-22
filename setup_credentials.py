#!/usr/bin/env python3
"""
Setup Credentials for High Probability Option Strategies
Quick credential setup for live trading
"""

import os

def setup_credentials():
    """Setup credentials for live trading"""
    print("🔐 Setting up Live Trading Credentials")
    print("=" * 50)
    
    print("📋 You need to set these environment variables:")
    print()
    print("export DHAN_LIVE_CLIENT_ID='your_live_client_id'")
    print("export DHAN_LIVE_ACCESS_TOKEN='your_live_access_token'")
    print("export AI_STUDIO_API_KEY='your_ai_studio_api_key'")
    print()
    
    # Check if credentials are already set
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    ai_key = os.getenv("AI_STUDIO_API_KEY")
    
    if client_id and access_token and ai_key:
        print("✅ Credentials are already set!")
        print(f"   Client ID: {client_id[:10]}...")
        print(f"   Access Token: {access_token[:20]}...")
        print(f"   AI Key: {ai_key[:20]}...")
        return True
    else:
        print("❌ Credentials not set")
        print()
        print("🔧 To set credentials, run these commands in your terminal:")
        print()
        print("# Set DhanHQ Live Credentials")
        print("export DHAN_LIVE_CLIENT_ID='your_actual_client_id'")
        print("export DHAN_LIVE_ACCESS_TOKEN='your_actual_access_token'")
        print()
        print("# Set Google AI Studio API Key")
        print("export AI_STUDIO_API_KEY='your_actual_ai_key'")
        print()
        print("Then run: python quick_deploy_options.py")
        return False

def create_env_file():
    """Create .env file template"""
    env_content = """# Live Trading Credentials for High Probability Option Strategies
# Replace with your actual credentials

# DhanHQ Live API Credentials
DHAN_LIVE_CLIENT_ID=your_live_client_id_here
DHAN_LIVE_ACCESS_TOKEN=your_live_access_token_here

# Google AI Studio API Key
AI_STUDIO_API_KEY=your_ai_studio_api_key_here

# Optional: Sandbox credentials for testing
DHAN_SANDBOX_CLIENT_ID=your_sandbox_client_id_here
DHAN_SANDBOX_ACCESS_TOKEN=your_sandbox_access_token_here
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ .env file created")
        print("📝 Edit .env file with your actual credentials")
        return True
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

if __name__ == "__main__":
    print("🎯 High Probability Option Strategies - Credential Setup")
    print("=" * 60)
    
    # Check current credentials
    if setup_credentials():
        print("\n🚀 Ready to deploy! Run:")
        print("   python quick_deploy_options.py")
    else:
        print("\n📝 Alternative: Create .env file")
        if create_env_file():
            print("✅ .env file created - edit it with your credentials")
            print("Then run: python quick_deploy_options.py")
        else:
            print("❌ Please set environment variables manually")
