from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from .database import engine, get_db, Base
from .models import User
from .schemas import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    LoginResponse, SignupResponse, MessageResponse, RefreshToken
)
from .auth import (
    get_password_hash, authenticate_user, create_access_token,
    create_refresh_token, get_current_user, verify_token
)
from .config import get_settings
from . import json_store

# ─────────────────────────────────────
# App setup
# ─────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Investment Platform API",
    description="Backend API for Private Credit Investment Platform",
    version="1.0.0"
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────
# Resolve the data/ directory relative
# to the project root (one level up from app/)
# ─────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDFS_DIR = os.path.join(BASE_DIR, "data", "pdfs")

# ─────────────────────────────────────
# Health check
# ─────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

# ─────────────────────────────────────
# Auth endpoints
# ─────────────────────────────────────
@app.post("/api/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email.lower(),
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Seed demo data for new user in both portfolio and scenarios
    json_store.seed_portfolio_data(new_user.id)
    json_store.seed_scenarios_data(new_user.id)

    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})

    return SignupResponse(
        message="User created successfully",
        user=new_user,
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.post("/api/login", response_model=LoginResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return LoginResponse(
        message="Login successful",
        user=user,
        access_token=access_token,
        refresh_token=refresh_token
    )

@app.post("/api/refresh")
async def refresh_token(refresh_data: RefreshToken, db: Session = Depends(get_db)):
    try:
        token_data = verify_token(refresh_data.refresh_token, token_type="refresh")
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/user", response_model=UserResponse)
async def get_user(current_user: User = Depends(get_current_user)):
    return current_user

@app.put("/api/user/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_update.name is not None:
        current_user.name = user_update.name
    db.commit()
    db.refresh(current_user)
    return current_user

@app.post("/api/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    return MessageResponse(message="Logout successful")

# ─────────────────────────────────────
# Portfolio endpoints (credit_ratings.json)
# ─────────────────────────────────────
@app.get("/api/portfolio")
async def get_portfolio(current_user: User = Depends(get_current_user)):
    """Get all credit ratings for the current user"""
    ratings = json_store.get_credit_ratings(current_user.id)
    return {"total": len(ratings), "items": ratings}

@app.get("/api/portfolio/{computation_id}/pdf")
async def get_credit_rating_pdf(
    computation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Serve the Credit Rating PDF report for a given computation ID.
    PDFs are expected at: data/pdfs/{computation_id}.pdf
    """
    # Sanitise: strip path separators so no directory-traversal is possible
    safe_name = os.path.basename(computation_id)
    pdf_path = os.path.join(PDFS_DIR, f"{safe_name}.pdf")

    if not os.path.isfile(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF report not found for {computation_id}"
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{safe_name}.pdf"
    )

@app.get("/api/portfolio/{computation_id}")
async def get_credit_rating(
    computation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a single credit rating by computation ID"""
    rating = json_store.get_credit_rating_by_id(current_user.id, computation_id)
    if not rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit rating not found")
    return rating

@app.post("/api/portfolio", status_code=status.HTTP_201_CREATED)
async def add_credit_rating(
    rating: dict,
    current_user: User = Depends(get_current_user)
):
    """Add a new credit rating"""
    try:
        created = json_store.add_credit_rating(current_user.id, rating)
        return created
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

@app.put("/api/portfolio/{computation_id}")
async def update_credit_rating(
    computation_id: str,
    updated_fields: dict,
    current_user: User = Depends(get_current_user)
):
    """Update an existing credit rating"""
    updated = json_store.update_credit_rating(current_user.id, computation_id, updated_fields)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit rating not found")
    return updated

@app.delete("/api/portfolio/{computation_id}", response_model=MessageResponse)
async def delete_credit_rating(
    computation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a credit rating"""
    deleted = json_store.delete_credit_rating(current_user.id, computation_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit rating not found")
    return MessageResponse(message="Credit rating deleted successfully")

# ─────────────────────────────────────
# Scenarios endpoints (scenarios.json)
# ─────────────────────────────────────
@app.get("/api/scenarios")
async def get_scenarios(current_user: User = Depends(get_current_user)):
    """Get all scenarios for the current user"""
    scenarios = json_store.get_scenarios(current_user.id)
    return {"total": len(scenarios), "items": scenarios}

@app.get("/api/scenarios/{computation_id}")
async def get_scenario(
    computation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a single scenario by computation ID"""
    scenario = json_store.get_scenario_by_id(current_user.id, computation_id)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return scenario

@app.put("/api/scenarios/{computation_id}")
async def update_scenario(
    computation_id: str,
    updated_fields: dict,
    current_user: User = Depends(get_current_user)
):
    """Update an existing scenario (called on Submit)"""
    updated = json_store.update_scenario(current_user.id, computation_id, updated_fields)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    print("updated_fields ->", current_user, computation_id, updated_fields)
    return updated

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