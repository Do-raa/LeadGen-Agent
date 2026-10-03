"""
TEST: Unipile Email Sending + Reply Threading
"""

import json
import time
from app.clients.unipile_client import UnipileClient


u = UnipileClient()

TEST_EMAIL = "dorraelkahla@yahoo.fr"
SUBJECT = "🔥 Test Email via Unipile"
BODY = "Hello, this is a test email sent using the Unipile API."

print("\n==============================")
print("🔹 TEST 1 — Send EMAIL")
print("==============================")

try:
    resp = u.send_email(TEST_EMAIL, SUBJECT, BODY)
    print("✅ Email sent!")
    print(json.dumps(resp, indent=2))
    provider_id = resp.get("provider_id")
    tracking_id = resp.get("tracking_id")
    print("🌐 provider_id:", provider_id)
    print("🔍 tracking_id:", tracking_id)
except Exception as e:
    print("❌ ERROR:", e)
    exit()


# ------------------------------------------
# Wait for Unipile to register the message
# ------------------------------------------
time.sleep(3)


print("\n==============================")
print("🔹 TEST 2 — List Recent Emails")
print("==============================")

emails = []

try:
    emails = u.list_emails(limit=5)
    print(f"📬 Returned {len(emails)} emails")

    for e in emails:
        print(
            f"- id: {e.get('id')} | "
            f"subject: {e.get('subject')} | "
            f"from: {e.get('from_attendee',{}).get('identifier')}"
        )

except Exception as e:
    print("❌ ERROR listing emails:", e)
    exit()


# ------------------------------------------
# Fetch one specific email
# ------------------------------------------
print("\n==============================")
print("🔹 TEST 3 — Fetch Single Email")
print("==============================")

if not emails:
    print("⚠️ No emails available to fetch details.")
    exit()

email_id = emails[0].get("id")

try:
    details = u.get_email(email_id)
    print("📨 Email Details:")
    print(json.dumps({
        "id": details.get("id"),
        "from": details.get("from_attendee",{}).get("identifier"),
        "subject": details.get("subject"),
        "body_plain": (details.get("body_plain") or "")[:200]
    }, indent=2))

    # 👇 Save provider ID for reply test
    original_provider_id = details.get("provider_id")
    print("💾 original provider_id:", original_provider_id)

except Exception as e:
    print("❌ ERROR fetching email:", e)
    exit()


# ------------------------------------------
# TEST threaded reply using `reply_to`
# ------------------------------------------
print("\n==============================")
print("🔹 TEST 4 — Threaded Reply (reply_to)")
print("==============================")

if not original_provider_id:
    print("⚠️ No provider_id from original email! Cannot test reply threading.")
    exit()

reply_body = "This is a threaded reply message. It should appear in the same conversation."

try:
    reply_resp = u.send_email(
        to_email=TEST_EMAIL,
        subject="Re: " + SUBJECT,
        body=reply_body,
        reply_to_provider_id=original_provider_id,
    )

    print("📨 Threaded reply sent!")
    print(json.dumps(reply_resp, indent=2))

except Exception as e:
    print("❌ ERROR sending threaded reply:", e)


print("\n==============================")
print("🧪 TEST COMPLETE")
print("==============================\n")
