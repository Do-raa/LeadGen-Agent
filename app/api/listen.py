from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from ..db.database import SessionLocal
from ..db.models import Provider, LinkedInPost, PotentialCustomer, Comment
from ..clients.unipile_client import UnipileClient

router = APIRouter()

# -----------------------------
# 🧱 Request schema
# -----------------------------
class LinkedInRequest(BaseModel):
    identifier: str  


# -----------------------------
# ⚙️ DB dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# 🚀 Main endpoint
# -----------------------------
unipile = UnipileClient()


@router.post("/listen_linkedin")
def listen_linkedin(request: LinkedInRequest, db: Session = Depends(get_db)):
    """
    Listens to LinkedIn posts for a given user (identifier),
    retrieves relevant posts, comments, and potential customers.
    """
    identifier = request.identifier
    try:
        # 1️⃣ Get provider_id
        provider_id = unipile.get_provider_id(identifier)
        if not provider_id:
            raise HTTPException(status_code=404, detail="Provider ID not found.")
        print(f"✅ Retrieved provider ID: {provider_id} for {identifier}")
        
        # 2️⃣ Ensure Provider record exists or create one
        provider = db.query(Provider).filter_by(provider_id=provider_id).first()
        if not provider:
            provider = Provider(
                name=identifier,
                linkedin_url=f"https://www.linkedin.com/in/{identifier}/",
                provider_id=provider_id,
                created_at=datetime.utcnow(),
            )
            db.add(provider)
            db.commit()
            db.refresh(provider)

        # 3️⃣ Retrieve relevant posts
        posts = unipile.get_user_posts(provider_id, limit=30)
        print("RAW POSTS:", posts)
        print(f"✅ Retrieved {len(posts)} posts for {identifier}")

        results = []

        for post in posts:
            social_id = post.get("social_id")
            if not social_id:
                continue

            # Check if post already exists
            existing_post = db.query(LinkedInPost).filter_by(social_id=social_id).first()
            if existing_post:
                continue

            # Parse timestamp safely
            post_timestamp = datetime.utcnow()
            if post.get("parsed_datetime"):
                try:
                    post_timestamp = datetime.fromisoformat(post.get("parsed_datetime").replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    post_timestamp = datetime.utcnow()

            new_post = LinkedInPost(
                author_id=provider.id,  
                author_name=post.get("author", {}).get("name", "Unknown"),
                post_text=post.get("text", ""),
                post_comments=post.get("comment_counter", 0),
                post_reactions=post.get("reaction_counter", 0),
                post_url=post.get("share_url") or post.get("id") or "",
                share_url=post.get("share_url"),
                social_id=social_id,
                provider=post.get("provider", "LINKEDIN"),
                timestamp=post_timestamp,
                can_post_comments=post.get("permissions", {}).get("can_post_comments", True)
            )

            db.add(new_post)
            db.commit()
            db.refresh(new_post)

            # 4️⃣ Get comments for this post
            comments = unipile.get_post_comments(social_id, limit=50)
            print(f"🗨️ Retrieved {len(comments)} comments for post {social_id}")

            # 5️⃣ Get reactions for this post
            reactions = unipile.get_post_reactions(social_id, limit=100)
            print(f"👍 Retrieved {len(reactions)} reactions for post {social_id}")

            # Save comments to database
            comment_entries = []
            for c in comments:
                author_name = c.get("author", "Unknown")  
                comment_text = c.get("text", "")

                if not comment_text.strip():
                    continue

                comment_entry = Comment(
                    post_id=new_post.id,
                    author_name=author_name,
                    comment_text=comment_text,
                    created_at=datetime.utcnow()
                )
                comment_entries.append(comment_entry)

            if comment_entries:
                db.add_all(comment_entries)
                db.commit()

            # 6️⃣ Extract and save potential customers from BOTH comments and reactions
            leads = unipile.extract_potential_customers(comments=comments, reactions=reactions)
            
            for lead_data in leads:
                name = lead_data["name"]
                identifier = lead_data.get("identifier")
                linkedin_url = lead_data.get("linkedin_url")  # This will be None for comment leads
                source = lead_data.get("source")
                engagement_type = lead_data.get("reaction_type")

                if not identifier or identifier == "Unknown":
                    continue

                # Check if potential customer already exists by name AND source_post_id
                # This prevents duplicates for the same person across different posts
                existing_customer = db.query(PotentialCustomer).filter(
                    PotentialCustomer.name == identifier,
                    PotentialCustomer.source_post_id == new_post.id
                ).first()

                if existing_customer:
                    # Update existing customer with LinkedIn URL if we have one now
                    if not existing_customer.linkedin_url and linkedin_url:
                        existing_customer.linkedin_url = linkedin_url
                        db.commit()
                        print(f"🔄 Updated LinkedIn URL for existing customer: {identifier}")
                    continue

                # Create new potential customer
                new_lead = PotentialCustomer(
                    name=name,
                    public_identifier=identifier,
                    linkedin_url=linkedin_url,  # Could be None for comment leads
                    source_post_id=new_post.id,
                    engagement_source=source,
                    engagement_type=engagement_type,
                    status="new"
                )
                
                db.add(new_lead)
                db.commit()
                print(f"✅ Added new potential customer: {identifier} from {source}")        

            results.append({
                "post_url": new_post.share_url,
                "comments": len(comments),
                "reactions": len(reactions),
                "total_leads": len(leads)
            })

        return {"ok": True, "provider": identifier, "results": results}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during LinkedIn listening: {str(e)}")