from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


# 1️⃣ PROVIDERS (e.g., LinkedIn authors or known B2B influencers)
class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    linkedin_url = Column(String(500), unique=True)
    provider_id = Column(String(200), unique=True, index=True, nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship("LinkedInPost", back_populates="author", cascade="all, delete-orphan")



# 2️⃣ POTENTIAL CUSTOMERS (leads)
class PotentialCustomer(Base):
    __tablename__ = "potential_customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    role = Column(String(255))
    company = Column(String(255))
    email = Column(String(255))
    public_identifier = Column(String(255), nullable=True, index=True)
    linkedin_url = Column(String(500), nullable=True)  
    source_post_id = Column(Integer, ForeignKey("linkedin_posts.id"), nullable=True)
    engagement_source = Column(String(50), default="comment")  # "comment" or "reaction"
    engagement_type = Column(String(50), nullable=True)  # "LIKE", "CELEBRATE", etc.
    enriched_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="new")  # new, enriched, contacted, converted

    # Relationship to posts
    post = relationship("LinkedInPost", back_populates="leads", foreign_keys=[source_post_id])
    interactions = relationship("LeadInteraction", back_populates="lead")
    sent_messages = relationship("SentMessage", back_populates="lead", cascade="all, delete-orphan")

# 3️⃣ LINKEDIN POSTS (core for social listening)
class LinkedInPost(Base):
    __tablename__ = "linkedin_posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    author_name = Column(String(255))
    post_text = Column(Text)
    post_comments = Column(Integer, default=0)
    post_reactions = Column(Integer, default=0)
    post_url = Column(String(1000))
    share_url = Column(String(1000))
    social_id = Column(String(200), unique=True, index=True, nullable=True)
    provider = Column(String(50), default="LINKEDIN")
    timestamp = Column(DateTime, default=datetime.utcnow)
    can_post_comments = Column(Boolean, default=True)

    # Relationships
    author = relationship("Provider", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    leads = relationship("PotentialCustomer", back_populates="post")
    post_responses = relationship("PostResponse", back_populates="post", cascade="all, delete-orphan")


# 4️⃣ COMMENTS (to track engagement by me or others)
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("linkedin_posts.id"))
    author_name = Column(String(255))
    comment_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    post = relationship("LinkedInPost", back_populates="comments", foreign_keys=[post_id])
    
# 4️⃣ POST RESPONSE (Generated comments & reactions per post)
class PostResponse(Base):
    __tablename__ = "post_response"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("linkedin_posts.id"))
    comment_options = Column(String, nullable=False)      # JSON stringified list of 3 comments
    reactions_options = Column(String, nullable=False)    # JSON stringified list of 3 reactions
    action = Column(String, nullable=True)               # "approved" or "declined"
    selected_comment = Column(String, nullable=True)
    selected_reaction = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    post = relationship("LinkedInPost", back_populates="post_responses", foreign_keys=[post_id])
    
class SentMessage(Base):
    __tablename__ = "sent_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), nullable=True)
    unipile_email_id = Column(String(255), nullable=True)
    lead_id = Column(Integer, ForeignKey("potential_customers.id"), nullable=False)

    lead = relationship("PotentialCustomer", back_populates="sent_messages")

    channel = Column(String(50))          # "email" | "linkedin"
    message_type = Column(String(50))     # "initial" | "followup" | "calendly"
    subject = Column(String(255), nullable=True)
    content = Column(Text)

    provider_message_id = Column(String(255), nullable=True)
    unipile_tracking_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

class LeadInteraction(Base):
    __tablename__ = "lead_interactions"

    id = Column(Integer, primary_key=True, index=True)
    
    lead_id = Column(Integer, ForeignKey("potential_customers.id"))
    lead = relationship("PotentialCustomer", back_populates="interactions")

    source = Column(String(50))           # "email" or "linkedin"
    content = Column(Text)                # full reply text
    sentiment_score = Column(Float)       # 0.00 - 1.00
    warm_score = Column(Integer)          # 0 - 100
    label = Column(String(50))            # cold / neutral / warm / hot
    
    created_at = Column(DateTime, default=datetime.utcnow)
      
# class Log(Base):
#     __tablename__ = "logs"
#     id = Column(Integer, primary_key=True, index=True)
#     agent_name = Column(String(255))
#     message = Column(Text)
#     timestamp = Column(DateTime, default=datetime.utcnow)
    
# class Task(Base):
#     __tablename__ = "tasks"
#     id = Column(Integer, primary_key=True, index=True)
#     type = Column(String(100))
#     timestamp = Column(DateTime, default=datetime.utcnow)
#     result = Column(JSON)
#     status = Column(String(50), default="pending")

# class SocialPatterns(Base):
#     __tablename__ = "social_patterns"
#     id = Column(Integer, primary_key=True, index=True)
#     patterns = Column(JSON)
#     created_at = Column(DateTime, default=datetime.utcnow)

# class ApprovalTask(Base):
#     __tablename__ = "approval_tasks"
#     id = Column(Integer, primary_key=True, index=True)
#     task_type = Column(String(50))  # 'comment', 'email', 'dm'
#     content = Column(Text)
#     lead_id = Column(Integer)
#     post_id = Column(Integer)
#     status = Column(String(20), default="pending")  # pending, approved, denied
#     created_at = Column(DateTime, default=datetime.utcnow)
#     resolved_at = Column(DateTime, nullable=True)