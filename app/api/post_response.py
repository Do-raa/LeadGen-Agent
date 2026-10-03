# app/api/post_response.py
from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session
import json

from ..db.database import SessionLocal
from ..db.models import LinkedInPost, PostResponse
from ..clients.unipile_client import UnipileClient

router = APIRouter()
unipile = UnipileClient()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/post_response")
def handle_slack_interaction(payload: str = Form(...), db: Session = Depends(get_db)):
    """
    Receives Slack interaction payload via n8n as:
        form-data: payload="<JSON string>"
    """
    # -----------------------------
    # 1) Parse payload
    # -----------------------------
    try:
        data = json.loads(payload)
    except Exception:
        return {"ok": False, "error": "invalid_payload"}

    # -----------------------------
    # 2) Extract button action
    # -----------------------------
    actions = data.get("actions", [])
    if not actions:
        return {"ok": True, "ignored": True, "reason": "no_action"}

    button = actions[0]
    raw_value = button.get("value", "")
    if "_" not in raw_value:
        return {"ok": True, "ignored": True, "reason": "invalid_button_format"}

    action, post_id_str = raw_value.split("_", 1)

    try:
        post_id = int(post_id_str)
    except ValueError:
        return {"ok": True, "ignored": True, "reason": "invalid_post_id"}

    action = action.lower().strip()
    if action not in ["approve", "decline"]:
        return {"ok": True, "ignored": True, "reason": "unknown_action"}

    # -----------------------------
    # 3) Extract comment & reaction from state
    # -----------------------------
    state_values = data.get("state", {}).get("values", {})

    # Comment radio: block_id "wTF4f", action_id "comment_choice"
    comment_choice = None
    try:
        comment_obj = (
            state_values.get("wTF4f", {})
            .get("comment_choice", {})
            .get("selected_option")
        )
        if comment_obj:
            comment_choice = int(comment_obj.get("value"))
    except Exception:
        comment_choice = None

    # Reaction radio: block_id "ELF6X", action_id "reaction_choice"
    # NOW value is direct LinkedIn code: CELEBRATE / INSIGHTFUL / LIKE / SUPPORT ...
    reaction_code = None
    try:
        reaction_obj = (
            state_values.get("ELF6X", {})
            .get("reaction_choice", {})
            .get("selected_option")
        )
        if reaction_obj:
            reaction_code = reaction_obj.get("value")
    except Exception:
        reaction_code = None

    # -----------------------------
    # 4) DB fetch
    # -----------------------------
    post = db.query(LinkedInPost).filter_by(id=post_id).first()
    if not post:
        return {"ok": True, "ignored": True, "reason": "post_not_found"}

    post_response = (
        db.query(PostResponse)
        .filter_by(post_id=post_id)
        .order_by(PostResponse.id.desc())
        .first()
    )
    if not post_response:
        return {"ok": True, "ignored": True, "reason": "response_not_found"}

    comments = json.loads(post_response.comment_options)
    reactions = json.loads(post_response.reactions_options)  # [{emoji, code}, ...]

    # -----------------------------
    # 5) DECLINE
    # -----------------------------
    if action == "decline":
        post_response.action = "declined"
        post_response.selected_comment = None
        post_response.selected_reaction = None
        db.commit()
        return {"ok": True, "status": "declined"}

    # -----------------------------
    # 6) APPROVE
    # -----------------------------
    if action == "approve":
        if comment_choice is None:
            return {
                "ok": True,
                "ignored": True,
                "reason": "approve_without_comment",
            }

        selected_comment = comments[comment_choice - 1]
        post_response.action = "approved"
        post_response.selected_comment = selected_comment

        # reaction_code is already LinkedIn-compatible (INSIGHTFUL, SUPPORT, ...)
        selected_reaction_code = None
        if reaction_code:
            selected_reaction_code = reaction_code.upper()
            post_response.selected_reaction = selected_reaction_code
        else:
            post_response.selected_reaction = None

        db.commit()

        # Send to LinkedIn via Unipile
        try:
            unipile.post_linkedin_comment(post.social_id, selected_comment)
            if selected_reaction_code:
                unipile.post_linkedin_reaction(post.social_id, selected_reaction_code)
        except Exception as e:
            return {"ok": False, "error": str(e)}

        return {
            "ok": True,
            "status": "approved",
            "comment": selected_comment,
            "reaction": selected_reaction_code,
        }

    return {"ok": True, "ignored": True, "reason": "unhandled"}
