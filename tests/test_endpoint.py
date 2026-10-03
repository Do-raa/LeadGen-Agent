import requests

url = "http://127.0.0.1:8000/api/listen_linkedin"
payload = {"identifier": "vyaspratik"}
response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print("Response:", response.json())
