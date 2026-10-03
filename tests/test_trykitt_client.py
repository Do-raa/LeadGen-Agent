# test_trykitt_final.py
import requests
import os
import json

def test_basic_functionality():
    """Test the most basic possible case"""
    api_key = "nwvDuxbTV3pQFG3YYmF77cjUtxWCvF"
    
    if not api_key:
        print("❌ No API key found")
        return
    
    headers = {
        "x-api-key": api_key,
        "accept": "application/json",
        "content-type": "application/json"
    }
    
    # Test case from their documentation exactly
    payload = {
        "fullName": "Tadeusz Twardzik, MBA.", 
        "domain": "trykitt.ai", 
        "linkedinStandardProfileURL": "https://www.linkedin.com/in/tadeusz-twardzik/",
        "realtime": True,
        "strictNameMatches": False
    }
    
    print("🔍 Testing with EXACT documentation example...")
    response = requests.post("https://api.trykitt.ai/job/find_email", 
                           headers=headers, json=payload, timeout=30)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Email result: {data.get('email', 'NOT FOUND')}")

def check_account_status():
    """Try to get any account information"""
    api_key = "nwvDuxbTV3pQFG3YYmF77cjUtxWCvF"
    
    headers = {
        "x-api-key": api_key,
        "accept": "application/json"
    }
    
    # Try different endpoints that might exist
    endpoints = [
        "/user",
        "/account",
        "/profile",
        "/usage",
        "/subscription"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"https://api.trykitt.ai{endpoint}", headers=headers, timeout=10)
            print(f"\n🔍 {endpoint}: Status {response.status_code}")
            if response.text:
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

if __name__ == "__main__":
    print("🚀 Final Trykitt Diagnostics")
    test_basic_functionality()
    check_account_status()