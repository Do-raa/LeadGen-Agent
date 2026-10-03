# test_db.py (in project root)
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, init_db
from sqlalchemy import text

try:
    init_db()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print("✅ Database connected:", result.scalar())
        
        # Check tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result]
        print("✅ Tables created:", tables)
except Exception as e:
    print("❌ Database error:", e)