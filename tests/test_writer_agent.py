# test_writer_agent.py

import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, LinkedInPost, Comment
from app.agents.writer_agent import HumanLikeWriter


def setup_test_db():
    """
    Creates an in-memory SQLite DB for isolated testing.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def seed_fake_post(db):
    """
    Create a fake LinkedIn post + real thread comments to test the agent.
    """
    post = LinkedInPost(
        author_name="John Carter",
        post_text=(
            "AI in 2025 is evolving fast. We're seeing huge jumps in reasoning "
            "and automation. Curious how small teams are adapting to this?"
        ),
        post_url="https://linkedin.com/posts/fake-post-test"
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    # Add fake comments to train the thread tone
    comments_data = [
        ("Sarah M", "Love this thinking! We're testing small automations too 🔥"),
        ("Daniel R", "Great insights. How do you evaluate which tasks to automate first?"),
        ("Lina AI", "Interesting point — speed matters but clarity matters even more."),
    ]

    for name, text in comments_data:
        c = Comment(post_id=post.id, author_name=name, comment_text=text)
        db.add(c)

    db.commit()

    return post.id


def pretty(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def run_test():
    print("\n================= 🔥 TESTING WRITER AGENT 🔥 =================\n")

    db = setup_test_db()
    post_id = seed_fake_post(db)

    writer = HumanLikeWriter(db)

    print("🔍 Running writer agent on test post...\n")

    result = writer.generate_comment_options(post_id=post_id, persona="expert")

    print("\n================= 🧠 META DATA =================")
    pretty(result["meta"])

    print("\n================= 💬 COMMENT OPTIONS =================")
    pretty(result["comment_options"])

    print("\n================= 🎉 REACTIONS =================")
    pretty(result["reactions"])

    print("\n================= 📄 POST SNIPPET =================")
    print(result["post_text"])

    print("\n🔥 TEST COMPLETE — Writer Agent is functioning!\n")


if __name__ == "__main__":
    run_test()
