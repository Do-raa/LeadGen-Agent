from fastapi import FastAPI
from app.api import listen, write, post_response, enrich, outreach, leads

app = FastAPI(title="LeadGen Agent API")

# Register routers
app.include_router(listen.router, prefix="/api", tags=["LinkedIn Listener"])
app.include_router(post_response.router, prefix="/api", tags=["Post Response"])
app.include_router(write.router, prefix="/api", tags=["Writer"]) 
app.include_router(enrich.router, prefix="/api", tags=["Enrichment"])
app.include_router(outreach.router, prefix="/api", tags=["Outreach"])
app.include_router(leads.router, prefix="/api", tags=["Leads Management"])

@app.get("/")
def root():
    return {"message": "LeadGen Agent API is running 🚀"}
