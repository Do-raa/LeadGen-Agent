# test_outreach_agent.py

from pprint import pprint

from app.db.database import SessionLocal
from app.db.models import PotentialCustomer, LinkedInPost
from app.agents.outreach_agent import OutreachAgent


# 🔧 Change this to an existing lead ID in your DB
TEST_LEAD_ID = 4003


def main():
    print("\n==============================")
    print("🔎 TEST: OutreachAgent messaging")
    print("==============================")

    db = SessionLocal()

    try:
        # 1️⃣ Load lead
        lead = db.query(PotentialCustomer).filter_by(id=TEST_LEAD_ID).first()
        if not lead:
            print(f"❌ Lead with id {TEST_LEAD_ID} not found in DB.")
            return

        print("\n👤 LEAD")
        pprint(
            {
                "id": lead.id,
                "name": lead.name,
                "role": lead.role,
                "company": lead.company,
                "email": lead.email,
                "linkedin_url": lead.linkedin_url,
                "source_post_id": lead.source_post_id,
            },
            sort_dicts=False,
        )

        # 2️⃣ Load post (if any)
        post = None
        if lead.source_post_id:
            post = db.query(LinkedInPost).filter_by(id=lead.source_post_id).first()

        if post:
            print("\n📝 POST CONTEXT")
            pprint(
                {
                    "id": post.id,
                    "author_name": post.author_name,
                    "social_id": post.social_id,
                    "snippet": (post.post_text or "")[:200],
                },
                sort_dicts=False,
            )
        else:
            print("\n⚠️ No source post found for this lead (post is None).")

        agent = OutreachAgent()

        # 3️⃣ Generate DM + followups
        print("\n==============================")
        print("✉️  generate_dm()")
        print("==============================")

        dm_text, followups = agent.generate_dm(lead, post)
        print("\nDM TEXT:\n")
        print(dm_text)
        print("\n------------------------------")
        print("FOLLOWUPS:")
        for idx, fu in enumerate(followups, start=1):
            print(f"{idx}. {fu}")

        # 4️⃣ LinkedIn note
        print("\n==============================")
        print("🔗 generate_linkedin_note()")
        print("==============================")

        li_note = agent.generate_linkedin_note(lead, post)
        print("NOTE:")
        print(li_note)
        print(f"(length = {len(li_note)} chars)")

        # 5️⃣ Calendly followup text
        print("\n==============================")
        print("📅 generate_calendly_followup()")
        print("==============================")

        calendly_text = agent.generate_calendly_followup(lead)
        print(calendly_text)

        print("\n==============================")
        print("✅ OutreachAgent test complete")
        print("==============================\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
