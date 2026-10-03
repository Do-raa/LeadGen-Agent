# test_unipile_exact.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_exact_unipile():
    API_KEY = os.getenv("UNIPILE_API_KEY")
    BASE_URL = "https://api23.unipile.com:15364/api/v1"
    
    headers = {
        "X-API-KEY": API_KEY,
        "accept": "application/json"
    }
    
    print("🔧 Testing exact Unipile configuration...")
    
    try:
        # This is exactly your curl command in Python
        url = f"{BASE_URL}/accounts"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            accounts = response.json()
            print("✅ SUCCESS! Unipile connection working!")
            print(f"📊 Response: {accounts}")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_exact_unipile()