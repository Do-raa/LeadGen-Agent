import requests
import json
from ..utils.config import TRYKITT_API_KEY

BASE_URL = "https://api.trykitt.ai"

class TrykittClient:
    def __init__(self, api_key=TRYKITT_API_KEY):
        if not api_key:
            raise ValueError("❌ Missing TRYKITT_API_KEY in environment variables.")
        self.api_key = api_key
        self.headers = {
            "x-api-key": self.api_key,
            "accept": "application/json",
            "content-type": "application/json"
        }

    def find_email(self, full_name: str, domain: str, linkedin_url: str = None):
        """
        Find and enrich contact info (email, role, company) for a person.
        """
        url = f"{BASE_URL}/job/find_email"
        
        payload = {
            "fullName": full_name,
            "website": domain,
            "realtime": True,
            "strictNameMatches": False
        }
        
        if linkedin_url:
            payload["linkedinStandardProfileURL"] = linkedin_url

        print(f"🔍 Sending payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            print(f"📡 API Response Status: {response.status_code}")
            
            if response.status_code == 402:
                print("💳 Payment required - check your credits or subscription")
            elif response.status_code == 403:
                print("🔐 Forbidden - check your API key permissions")
            elif response.status_code == 429:
                print("🚦 Rate limited - too many requests")
            
            if not response.ok:
                print(f"❌ API Error: {response.text}")
                return None

            data = response.json() if response.text else {}
            
            # Debug the response structure
            print(f"📊 Response keys: {list(data.keys()) if data else 'Empty'}")
            
            return data

        except Exception as e:
            print(f"⚠️ Trykitt enrichment failed for {full_name}: {e}")
            return None