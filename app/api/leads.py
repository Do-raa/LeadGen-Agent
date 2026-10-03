from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..db.models import PotentialCustomer, LeadInteraction

router = APIRouter()


# -----------------------------------------------------------
# DB Session Dependency
# -----------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------------
# Helper function: serialize interaction object
# -----------------------------------------------------------
def serialize_interaction(i: LeadInteraction) -> dict:
    return {
        "id": i.id,
        "lead_id": i.lead_id,
        "source": i.source,
        "label": i.label,
        "score": i.warm_score,
        "sentiment": i.sentiment_score,
        "content": i.content,
        "created_at": i.created_at.isoformat(),
    }


# -----------------------------------------------------------
# GET /leads/warm → last warm interactions
# -----------------------------------------------------------
@router.get("/leads/warm")
def get_warm_leads(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = (
        db.query(LeadInteraction)
        .filter(LeadInteraction.warm_score >= 75)
        .order_by(LeadInteraction.created_at.desc())
        .limit(limit)
        .all()
    )

    return [serialize_interaction(i) for i in items]


# -----------------------------------------------------------
# GET /leads/cold → cold leads below threshold
# -----------------------------------------------------------
@router.get("/leads/cold")
def get_cold_leads(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = (
        db.query(LeadInteraction)
        .filter(LeadInteraction.warm_score < 40)
        .order_by(LeadInteraction.created_at.desc())
        .limit(limit)
        .all()
    )

    return [serialize_interaction(i) for i in items]


# -----------------------------------------------------------
# GET /leads/neutral → neither cold nor warm
# -----------------------------------------------------------
@router.get("/leads/neutral")
def get_neutral_leads(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items = (
        db.query(LeadInteraction)
        .filter(LeadInteraction.warm_score >= 40)
        .filter(LeadInteraction.warm_score < 75)
        .order_by(LeadInteraction.created_at.desc())
        .limit(limit)
        .all()
    )

    return [serialize_interaction(i) for i in items]


# -----------------------------------------------------------
# GET /lead/{lead_id}/interactions → all interactions for a lead
# -----------------------------------------------------------
@router.get("/lead/{lead_id}/interactions")
def get_lead_interactions(
    lead_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    lead = db.query(PotentialCustomer).filter_by(id=lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    items = (
        db.query(LeadInteraction)
        .filter(LeadInteraction.lead_id == lead_id)
        .order_by(LeadInteraction.created_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "lead": {
            "id": lead.id,
            "name": lead.name,
            "company": lead.company,
            "email": lead.email,
            "linkedin": lead.linkedin_url,
            "status": lead.status,
        },
        "interactions": [serialize_interaction(i) for i in items],
    }


# -----------------------------------------------------------
# GET /leads/score-range?min=60&max=90 → flexible scoring filter
# -----------------------------------------------------------
@router.get("/leads/score-range")
def get_leads_by_score_range(
    min_score: int = Query(0, ge=0, le=100),
    max_score: int = Query(100, ge=0, le=100),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if min_score > max_score:
        raise HTTPException(
            status_code=400, detail="min_score cannot be greater than max_score"
        )

    items = (
        db.query(LeadInteraction)
        .filter(LeadInteraction.warm_score >= min_score)
        .filter(LeadInteraction.warm_score <= max_score)
        .order_by(LeadInteraction.created_at.desc())
        .limit(limit)
        .all()
    )

    return [serialize_interaction(i) for i in items]
