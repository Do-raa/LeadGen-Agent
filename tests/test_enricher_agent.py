from app.db.database import SessionLocal
from app.agents.enricher_agent import EnricherAgent

def test_enrichment():
    print("🚀 Running enrichment test...")
    db = SessionLocal()
    agent = EnricherAgent()
    results = agent.enrich_leads(db, limit=5)
    print(f"\n✅ Enrichment results: {results}")

if __name__ == "__main__":
    test_enrichment()
