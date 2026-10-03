import requests
import json

BASE = "http://127.0.0.1:8000"  

def test_enrich(lead_id: int):
    print(f"\n🔍 Testing enrichment for Lead ID {lead_id}...")

    url = f"{BASE}/api/enrich/{lead_id}"

    response = requests.post(url)
    
    print("\n🔹 Response Status:", response.status_code)

    if response.status_code != 200:
        print("❌ Error:", response.text)
        return
    
    data = response.json()
    
    print("✅ Enrichment Successful!")
    print(json.dumps(data, indent=4))


if __name__ == "__main__":
    # Test first 10 leads automatically
    for i in range(1, 11):
        test_enrich(i)
