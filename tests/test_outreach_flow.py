import time
import requests
import json

BASE = "http://127.0.0.1:8000/api"

# ---------------------------------------
#  CONFIGURATION
# ---------------------------------------
TEST_LEAD_ID = 4003   # change for your DB
WAIT_TIME = 150       # 2m30s -> followup worker delay


# ---------------------------------------
# 1️⃣ Start Outreach
# ---------------------------------------
def test_outreach():
    url = f"{BASE}/outreach/{TEST_LEAD_ID}"
    print("\n⚡ Sending Outreach request...")

    resp = requests.post(url)
    print("STATUS:", resp.status_code)
    print(json.dumps(resp.json(), indent=2))


# ---------------------------------------
# 2️⃣ Wait for followup worker thread
# ---------------------------------------
def wait_for_followup():
    print(f"\n⏳ Waiting {WAIT_TIME} seconds for follow-up logic...")
    time.sleep(WAIT_TIME)
    print("⏱️ Done waiting.")


# ---------------------------------------
# 3️⃣ Check warm leads
# ---------------------------------------
def check_warm():
    url = f"{BASE}/leads/warm"
    print("\n🔥 /leads/warm")
    resp = requests.get(url)
    print(json.dumps(resp.json(), indent=2))


# ---------------------------------------
# 4️⃣ Check cold leads
# ---------------------------------------
def check_cold():
    url = f"{BASE}/leads/cold"
    print("\n🥶 /leads/cold")
    resp = requests.get(url)
    print(json.dumps(resp.json(), indent=2))


# ---------------------------------------
# 5️⃣ Check neutral leads
# ---------------------------------------
def check_neutral():
    url = f"{BASE}/leads/neutral"
    print("\n😐 /leads/neutral")
    resp = requests.get(url)
    print(json.dumps(resp.json(), indent=2))


# ---------------------------------------
# 6️⃣ Check this lead interactions
# ---------------------------------------
def check_interactions():
    url = f"{BASE}/lead/{TEST_LEAD_ID}/interactions"
    print(f"\n📬 Interactions for lead {TEST_LEAD_ID}")
    resp = requests.get(url)
    print(json.dumps(resp.json(), indent=2))


# ---------------------------------------
# MAIN TEST EXECUTION
# ---------------------------------------
if __name__ == "__main__":

    print("\n==============================")
    print("🚀 TEST: Outreach → Followup → Warm/Cold")
    print("==============================")

    # 1. Send initial outreach
    test_outreach()

    # 2. Wait for the thread to run
    wait_for_followup()

    # 3. Inspect database via API
    check_interactions()
    check_warm()
    check_cold()
    check_neutral()

    print("\n==============================")
    print("🧪 TEST COMPLETE")
    print("==============================\n")
