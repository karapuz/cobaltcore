from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.data.config import get_settings
from app.data.database import engine, Base
from app.routers import users
from app.profile import portfolio, scenarios, scenario_surface
from app.generators import credit_score, index_analysis

# ─────────────────────────────────────
# App setup
# ─────────────────────────────────────
settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Investment Platform API",
    description="Backend API for Private Credit Investment Platform",
    version="1.0.0"
)

# Origins come from CORS_ORIGINS in the environment. In production the
# React build is served from the same domain as the API, so the browser
# makes same-origin requests and this middleware is effectively unused.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
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
app.include_router(index_analysis.router, prefix="/api", tags=["Index Analysis"])

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
    return JSONResponse(status_code=404, content={"error": "Endpoint not found"})

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

if __name__ == "__main__":
    import uvicorn
    # Local development only. In production systemd runs uvicorn bound to
    # 127.0.0.1 with a single worker; nginx is the only public listener.
    uvicorn.run(app, host="127.0.0.1", port=8000)

"""
Local:
    uvicorn app.main:app --reload --port 8000

Production (single worker — the JSON model store is not multi-process safe):
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1

    curl http://localhost:8000/api/health

    
(base) root@localhost:/srv/compass-app/frontend# HOST=0.0.0.0 npm start

    """
