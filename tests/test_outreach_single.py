# test_outreach_single.py
import json
from app.db.database import SessionLocal
from app.db.models import PotentialCustomer, SentMessage
from app.api.outreach import outreach_single_lead

TEST_LEAD_ID = 4003

db = SessionLocal()

lead = db.query(PotentialCustomer).filter_by(id=TEST_LEAD_ID).first()

print("\n==============================")
print("💥 TEST: outreach_single_lead()")
print("==============================")

result = outreach_single_lead(db, lead)

print("\n📌 ACTIONS")
print(json.dumps(result, indent=2))

print("\n📤 SENT MESSAGES IN DB:")
msgs = db.query(SentMessage).filter_by(lead_id=TEST_LEAD_ID).all()

for m in msgs:
    print({
        "id": m.id,
        "type": m.message_type,
        "channel": m.channel,
        "provider_message_id": m.provider_message_id,
        "thread_id": m.thread_id,
        "created_at": str(m.created_at)
    })

db.close()
