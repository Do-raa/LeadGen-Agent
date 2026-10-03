# test_write_endpoint.py
import requests
import json

API_URL = "http://127.0.0.1:8000/api/write"

def test_write_api():
    print("🚀 Testing /api/write endpoint (fast version)...")
    payload = {"limit": 5}

    try:
        response = requests.post(API_URL, json=payload, timeout=60)
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print("❌ API Error:", response.text)


if __name__ == "__main__":
    test_write_api()
