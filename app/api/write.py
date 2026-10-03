# app/api/write.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import json
import concurrent.futures

from ..db.database import SessionLocal
from ..db.models import LinkedInPost, PostResponse
from ..agents.writer_agent import HumanLikeWriter

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class WriteRequest(BaseModel):
    limit: int = 3      # number of posts to process
    persona: str = "friendly"   # persona override (optional)


@router.post("/write")
def generate_comments_for_posts(
    request: WriteRequest, 
    db: Session = Depends(get_db)
):
    """
    Generate comment options + reaction options for recent LinkedIn posts.
    Fully upgraded for the new writer agent:
    - Thread-aware comment generation
    - Persona styles
    - Intent & sentiment modeling
    - Reddit-based writing patterns
    """
    try:
        # Fetch most recent posts
        posts = (
            db.query(LinkedInPost)
            .order_by(LinkedInPost.timestamp.desc())
            .limit(request.limit)
            .all()
        )

        if not posts:
            raise HTTPException(status_code=404, detail="No posts found in database.")

        writer = HumanLikeWriter(db)
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_map = {
                executor.submit(
                    process_single_post, writer, db, post, request.persona
                ): post.id
                for post in posts
            }

            for future in concurrent.futures.as_completed(future_map):
                try:
                    results.append(future.result(timeout=40))
                except Exception as e:
                    print(f"⚠️ Post processing failed: {e}")

        return {
            "ok": True,
            "processed": len([r for r in results if r]),
            "results": [r for r in results if r],
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Writer agent failed: {str(e)}"
        )


def process_single_post(writer, db, post, persona: str):
    """
    Handles generation + DB insert for ONE post.
    Uses upgraded agent method:
      writer.generate_comment_options(post, persona)
    """
    # Avoid generating twice
    existing = db.query(PostResponse).filter_by(post_id=post.id).first()
    if existing:
        print(f"⚠️ Skipping post {post.id} — already processed.")
        return None

    # NEW: Thread-aware, persona-aware comment generation
    output = writer.generate_comment_options(post, persona)

    # Save in DB
    response = PostResponse(
        post_id=post.id,
        comment_options=json.dumps(output["comment_options"], ensure_ascii=False),
        reactions_options=json.dumps(output["reactions"], ensure_ascii=False),
        created_at=datetime.utcnow(),
    )

    db.add(response)
    db.commit()
    db.refresh(response)

    return {
        "post_id": post.id,
        "post_url": post.post_url,
        "author": post.author_name,
        "post_text": post.post_text[:200],
        "comment_options": output["comment_options"],
        "reactions": output["reactions"],
        "created_at": response.created_at.isoformat(),
        "meta": output["meta"],
    }
