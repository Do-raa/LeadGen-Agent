from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..db.models import PotentialCustomer, LinkedInPost, SentMessage
from ..clients.unipile_client import UnipileClient
from ..agents.outreach_agent import OutreachAgent
from ..api.outreach_followup import followup_worker

router = APIRouter()
unipile = UnipileClient()
agent = OutreachAgent()

# -----------------------------------------------------------
# DB Session
# -----------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------------
# Request bodies
# -----------------------------------------------------------
class OutreachRequest(BaseModel):
    max_leads: int = 10
    only_new: bool = True

class BatchOutreachRequest(BaseModel):
    lead_ids: list[int]

# -----------------------------------------------------------
# SINGLE outreach logic
# -----------------------------------------------------------
def outreach_single_lead(db: Session, lead: PotentialCustomer):

    actions = {
        "lead_id": lead.id,
        "email_sent": False,
        "linkedin_sent": False,
        "errors": [],
    }

    # load post context
    post = db.query(LinkedInPost).filter_by(id=lead.source_post_id).first() if lead.source_post_id else None

    # 1) AI message →
    dm_text, followups = agent.generate_dm(lead, post)

    # -------------------------------------------------------
    # 2) LinkedIn invite (optional)
    # -------------------------------------------------------
    if lead.linkedin_url:
        try:
            public_id = lead.linkedin_url.rstrip("/").split("/")[-1].split("?")[0]
            note = agent.generate_linkedin_note(lead, post)

            r = unipile.send_linkedin_invitation(public_id, note)

            actions["linkedin_sent"] = True

            db.add(SentMessage(
                lead_id=lead.id,
                channel="linkedin",
                message_type="initial",
                content=note,
                provider_message_id=r.get("invitation_id"),
                unipile_tracking_id=r.get("tracking_id"),
            ))
        except Exception as e:
            actions["errors"].append(f"LinkedIn error: {str(e)}")

    # -------------------------------------------------------
    # 3) SEND EMAIL OUTREACH
    # -------------------------------------------------------
    if lead.email:
        try:
            subject = f"Quick idea for {lead.company or 'your team'}"

            r = unipile.send_email(
                to_email=lead.email,
                subject=subject,
                body=dm_text
            )

            provider_id = r.get("provider_id")
            details = unipile.get_email(provider_id) if provider_id else {}

            unipile_email_id = details.get("id")
            message_id = details.get("message_id")

            db.add(SentMessage(
                lead_id=lead.id,
                channel="email",
                message_type="initial",
                subject=subject,
                content=dm_text,
                provider_message_id=provider_id,
                unipile_tracking_id=r.get("tracking_id"),
                unipile_email_id=unipile_email_id,
                message_id=message_id,
            ))

            actions["email_sent"] = True

        except Exception as e:
            actions["errors"].append(f"Email error: {str(e)}")

    # -------------------------------------------------------
    # 4) Save lead status
    # -------------------------------------------------------
    lead.status = "contacted" if actions["email_sent"] or actions["linkedin_sent"] else "skipped"
    db.add(lead)
    db.commit()

    # -------------------------------------------------------
    # 5) Start background follow-up worker
    # -------------------------------------------------------
    if actions["email_sent"]:
        from threading import Thread
        t = Thread(target=followup_worker, args=(lead.id, dm_text))
        t.daemon = True
        t.start()

    return actions

# -----------------------------------------------------------
# Bulk outreach
# -----------------------------------------------------------
def run_outreach(db: Session, max_leads: int, only_new: bool):

    q = db.query(PotentialCustomer)
    if only_new:
        q = q.filter(PotentialCustomer.status == "new")

    leads = q.order_by(PotentialCustomer.id.asc()).limit(max_leads).all()

    summary = {
        "total": len(leads),
        "processed": 0,
        "contacted": 0,
       "skipped": 0,
        "details": [],
    }

    for lead in leads:
        result = outreach_single_lead(db, lead)
        summary["details"].append(result)
        summary["processed"] += 1

        if result["linkedin_sent"] or result["email_sent"]:
            summary["contacted"] += 1
        else:
            summary["skipped"] += 1

    return summary

# -----------------------------------------------------------
# Endpoints
# -----------------------------------------------------------
@router.post("/outreach")
def trigger_outreach(req: OutreachRequest, background: BackgroundTasks, db: Session = Depends(get_db)):
    background.add_task(run_outreach, db, req.max_leads, req.only_new)
    return {"ok": True, "message": "Bulk outreach started."}

@router.post("/outreach/{lead_id}")
def outreach_one(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(PotentialCustomer).filter_by(id=lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"ok": True, "details": outreach_single_lead(db, lead)}

@router.post("/outreach/batch")
def outreach_batch(req: BatchOutreachRequest, db: Session = Depends(get_db)):
    results = []
    for lead_id in req.lead_ids:
        lead = db.query(PotentialCustomer).filter_by(id=lead_id).first()
        if not lead:
            results.append({"lead_id": lead_id, "error": "Lead not found"})
            continue
        results.append(outreach_single_lead(db, lead))
    return {"ok": True, "count": len(req.lead_ids), "results": results}
