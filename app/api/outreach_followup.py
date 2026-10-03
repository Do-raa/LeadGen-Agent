import time
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..db.models import PotentialCustomer, SentMessage, LeadInteraction
from ..clients.unipile_client import UnipileClient
from ..agents.outreach_agent import OutreachAgent
from ..agents.warm_classifier import classify_warm_lead

unipile = UnipileClient()
agent = OutreachAgent()

# -----------------------------------------------------------
# Helper — clean reply subject
# -----------------------------------------------------------
def _clean_reply_subject(s: str) -> str:
    s = s or ""
    base = s.strip()
    while base.lower().startswith("re:"):
        base = base[3:].lstrip()
    return f"Re: {base}" if base else "Re:"

# -----------------------------------------------------------
# Followup email
# -----------------------------------------------------------
def send_followup(lead, dm_text, db, reply_to, original_subject):
    followup_text = agent.generate_followups(lead, {})[0]
    subject = _clean_reply_subject(original_subject)

    r = unipile.send_email(
        to_email=lead.email,
        subject=subject,
        body=followup_text,
        reply_to=reply_to
    )

    db.add(SentMessage(
        lead_id=lead.id,
        channel="email",
        message_type="followup",
        subject=subject,
        content=followup_text,
        provider_message_id=r.get("provider_id"),
        unipile_tracking_id=r.get("tracking_id"),
    ))

# -----------------------------------------------------------
# Calendly reply
# -----------------------------------------------------------
def send_calendly(lead, db, reply_to, original_subject):
    calendly_text = agent.generate_calendly_followup(lead)
    subject = _clean_reply_subject(original_subject)

    r = unipile.send_email(
        to_email=lead.email,
        subject=subject,
        body=calendly_text,
        reply_to=reply_to,
    )

    db.add(SentMessage(
        lead_id=lead.id,
        channel="email",
        message_type="calendly",
        subject=subject,
        content=calendly_text,
        provider_message_id=r.get("provider_id"),
        unipile_tracking_id=r.get("tracking_id"),
    ))

# -----------------------------------------------------------
# WORKER — runs 2 min later
# -----------------------------------------------------------
def followup_worker(lead_id: int, dm_text: str):

    db = SessionLocal()
    try:
        lead = db.query(PotentialCustomer).filter_by(id=lead_id).first()
        if not lead:
            return

        time.sleep(120)

        # 1) find last initial email
        last_initial = (
            db.query(SentMessage)
            .filter(
                SentMessage.lead_id == lead.id,
                SentMessage.channel == "email",
                SentMessage.message_type == "initial",
            )
            .order_by(SentMessage.created_at.desc())
            .first()
        )

        if not last_initial:
            return

        initial_msg = last_initial.message_id
        initial_uni = last_initial.unipile_email_id
        original_subject = last_initial.subject

        # 2) fetch all emails involving user
        emails = unipile.list_emails(limit=50, any_email=lead.email)

        reply_found = False

        for email in emails:

            in_reply = email.get("in_reply_to") or {}

            if (
                (initial_msg and in_reply.get("message_id") == initial_msg)
                or (initial_uni and in_reply.get("id") == initial_uni)
            ):
                # reply detected
                body = (email.get("body_plain") or email.get("body") or "").strip()

                result = classify_warm_lead(body)

                db.add(LeadInteraction(
                    lead_id=lead.id,
                    source="email",
                    content=body,
                    warm_score=result["score"],
                    label=result["intent"],
                    sentiment_score=result["score"] / 100,
                ))
                db.commit()

                reply_to = email.get("provider_id") or email.get("id")

                if result["score"] >= 50:
                    send_calendly(lead, db, reply_to, original_subject)
                else:
                    send_followup(lead, dm_text, db, reply_to, original_subject)

                reply_found = True
                break

        # 3) No reply → send soft followup
        if not reply_found:
            reply_to = initial_uni or last_initial.provider_message_id
            send_followup(lead, dm_text, db, reply_to, original_subject)

        db.commit()

    finally:
        db.close()
