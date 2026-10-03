
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from ..db.database import SessionLocal
from ..db.models import PotentialCustomer
from ..clients.unipile_client import UnipileClient

router = APIRouter()
unipile = UnipileClient()

# ----------------------------------------------------
# DB Dependency
# ----------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------------------------------------
# Helper: Extract fields
# ----------------------------------------------------
def extract_enrichment_fields(raw: dict):
    email = None
    role = None
    company = None

    # Email
    try:
        emails = raw.get("contact_info", {}).get("emails", [])
        if emails:
            email = emails[0]
    except:
        pass

    # Work experience (current job)
    try:
        exp = raw.get("work_experience", [])
        if exp:
            current = next((x for x in exp if x.get("current")), None) or exp[0]
            role = current.get("position")
            company = current.get("company")
    except:
        pass

    return email, role, company


# ----------------------------------------------------
# NEW: Auto-enrich ALL leads without passing lead_id
# ----------------------------------------------------
@router.post("/enrich")
def auto_enrich_all_leads(db: Session = Depends(get_db)):
    """
    Automatically enrich the FIRST 50 leads that:
    - have no email, OR
    - have no role, OR
    - have no company
    
    Runs Unipile enrichment on each of them.
    """

    # Fetch only the FIRST 50 leads needing enrichment
    leads = (
        db.query(PotentialCustomer)
        .filter(
            (PotentialCustomer.email.is_(None)) |
            (PotentialCustomer.role.is_(None)) |
            (PotentialCustomer.company.is_(None))
        )
        .order_by(PotentialCustomer.id.asc())   # ensure stable ordering
        .limit(60)
        .all()
    )

    if not leads:
        return {"ok": True, "message": "No leads need enrichment."}

    enriched_summary = []

    for lead in leads:
        public_identifier = None

        # Extract username from linkedin_url
        if lead.linkedin_url:
            public_identifier = lead.linkedin_url.rstrip("/").split("/")[-1]

        if not public_identifier:
            enriched_summary.append({
                "lead_id": lead.id,
                "status": "skipped",
                "reason": "Invalid LinkedIn URL"
            })
            continue

        # ---- Call Unipile ----
        raw_profile = unipile.enrich_profile(
            linkedin_url=lead.linkedin_url,
            public_identifier=public_identifier
        )

        if not raw_profile:
            enriched_summary.append({
                "lead_id": lead.id,
                "status": "failed",
                "reason": "Unipile returned no data"
            })
            continue

        # Extract values
        email, role, company = extract_enrichment_fields(raw_profile)

        updated = False
        if email and email != lead.email:
            lead.email = email
            updated = True
        if role and role != lead.role:
            lead.role = role
            updated = True
        if company and company != lead.company:
            lead.company = company
            updated = True

        if updated:
            lead.enriched_at = datetime.utcnow()
            lead.status = "enriched"
            db.add(lead)
            db.commit()

        enriched_summary.append({
            "lead_id": lead.id,
            "updated": updated,
            "email": email,
            "role": role,
            "company": company
        })

    return {
        "ok": True,
        "processed": len(enriched_summary),
        "details": enriched_summary
    }
