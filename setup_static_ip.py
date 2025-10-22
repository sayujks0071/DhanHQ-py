#!/usr/bin/env python3
"""
Setup Static IP for Live Trading
Configure primary and secondary IP addresses for order placement
"""

import os
import sys
import requests
from dotenv import load_dotenv

def setup_static_ip():
    """Set up static IP addresses for live trading"""
    print("🌐 Setting up Static IP for Live Trading")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    client_id = os.getenv("DHAN_LIVE_CLIENT_ID")
    
    if not access_token or not client_id:
        print("❌ Missing credentials in .env file")
        return False
    
    # Get current IP (you'll need to replace with your actual IPs)
    primary_ip = input("Enter your Primary IP address: ").strip()
    secondary_ip = input("Enter your Secondary IP address (or press Enter to skip): ").strip()
    
    if not primary_ip:
        print("❌ Primary IP is required")
        return False
    
    # Prepare API request
    headers = {
        "access-token": access_token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "dhanClientId": client_id,
        "ip": primary_ip,
        "ipFlag": "PRIMARY"
    }
    
    if secondary_ip:
        payload["secondaryIp"] = secondary_ip
        payload["secondaryIpFlag"] = "SECONDARY"
    
    print(f"📡 Setting Primary IP: {primary_ip}")
    if secondary_ip:
        print(f"📡 Setting Secondary IP: {secondary_ip}")
    
    try:
        # Set primary IP
        response = requests.post(
            "https://api.dhan.co/v2/ip/setIP",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "SUCCESS":
                print("✅ Static IP configuration successful!")
                print(f"📋 Response: {result.get('message', 'IP set successfully')}")
                return True
            else:
                print(f"❌ API Error: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting static IP: {e}")
        return False

def get_current_ip():
    """Get current IP configuration"""
    print("\n🔍 Checking current IP configuration...")
    
    load_dotenv()
    access_token = os.getenv("DHAN_LIVE_ACCESS_TOKEN")
    
    if not access_token:
        print("❌ Missing access token")
        return False
    
    headers = {
        "access-token": access_token
    }
    
    try:
        response = requests.get(
            "https://api.dhan.co/v2/ip/getIP",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print("📊 Current IP Configuration:")
            print(f"   Primary IP: {result.get('primaryIP', 'Not set')}")
            print(f"   Secondary IP: {result.get('secondaryIP', 'Not set')}")
            print(f"   Primary IP can be modified after: {result.get('modifyDatePrimary', 'N/A')}")
            print(f"   Secondary IP can be modified after: {result.get('modifyDateSecondary', 'N/A')}")
            return True
        else:
            print(f"❌ Error getting IP config: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting IP config: {e}")
        return False

if __name__ == "__main__":
    print("🌐 DhanHQ Static IP Setup")
    print("=" * 40)
    
    # Check current IP first
    get_current_ip()
    
    print("\n" + "=" * 40)
    setup_choice = input("Do you want to set up static IP? (y/n): ").strip().lower()
    
    if setup_choice == 'y':
        success = setup_static_ip()
        if success:
            print("\n✅ Static IP setup completed!")
            print("🎯 You can now place live orders")
        else:
            print("\n❌ Static IP setup failed")
            sys.exit(1)
    else:
        print("⏭️ Skipping static IP setup")
        print("⚠️ Note: You may not be able to place live orders without static IP")
