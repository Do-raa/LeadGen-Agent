# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from .models import Base
# from ..utils.config import DATABASE_URL

# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(bind=engine)

# def init_db():
#     Base.metadata.create_all(bind=engine)
# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from ..utils.config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def reset_db():
    """Drops all tables and recreates them - WARNING: DELETES ALL DATA"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database reset complete - all tables recreated")
