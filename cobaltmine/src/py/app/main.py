from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data.database import engine, Base
from app.routers import users
from app.profile import portfolio, scenarios, scenario_surface
from app.generators import credit_score, index_analysis

# ─────────────────────────────────────
# App setup
# ─────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Investment Platform API",
    description="Backend API for Private Credit Investment Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────
# Include routers
# ─────────────────────────────────────
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"])
app.include_router(scenarios.router, prefix="/api", tags=["Scenarios"])
app.include_router(scenario_surface.router, prefix="/api", tags=["Scenario Surface"])
app.include_router(credit_score.router, prefix="/api", tags=["Credit Score"])
app.include_router(index_analysis.router, prefix="/api/v0", tags=["Index Analysis"])

# ─────────────────────────────────────
# Health check
# ─────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

# ─────────────────────────────────────
# Error handlers
# ─────────────────────────────────────
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found"}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return {"error": "Internal server error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
uvicorn app.main:app --reload --port 8000

uvicorn app:main --reload --port 8000

curl http://localhost:8000/api/health

"""