from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

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

@app.get("/api/portfolio/{computation_id}/pdf")
async def get_credit_rating_pdf(
    computation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get PDF report for a credit rating"""
    import os
    from fastapi.responses import FileResponse
    
    # Sanitize filename to prevent directory traversal
    safe_id = os.path.basename(computation_id)
    pdf_path = f"data/pdfs/{safe_id}.pdf"
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{safe_id}.pdf"
    )

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
# Scenario Surface endpoints
# ─────────────────────────────────────
import hashlib
import json
from pathlib import Path

SCENARIO_SURFACES_FILE = Path(__file__).parent.parent / "data" / "scenario_surfaces.json"

def load_scenario_surfaces():
    """Load scenario surfaces from JSON file"""
    if not SCENARIO_SURFACES_FILE.exists():
        return {"scenario_surfaces": {}}
    with open(SCENARIO_SURFACES_FILE, 'r') as f:
        return json.load(f)

def save_scenario_surfaces(data):
    """Save scenario surfaces to JSON file"""
    SCENARIO_SURFACES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCENARIO_SURFACES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.post("/api/scenario-surface/request")
async def scenario_surface_request(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Submit a scenario surface request.
    Returns a ScenarioSurfaceResponseID for polling.
    """
    # Generate hash from all parameters for idempotent requests
    params_str = json.dumps(request_data, sort_keys=True)
    request_id = hashlib.sha256(params_str.encode()).hexdigest()[:16]
    
    # Load existing data
    data = load_scenario_surfaces()
    
    # Check if this request already exists and is completed
    if request_id in data["scenario_surfaces"]:
        existing = data["scenario_surfaces"][request_id]
        if existing.get("status") == "completed":
            return {"scenarioSurfaceResponseId": request_id, "status": "completed"}
    
    # Store the request as pending (in a real system, this would trigger background processing)
    # For now, we'll use mock data based on the request parameters
    data["scenario_surfaces"][request_id] = {
        "status": "pending",
        "request": request_data,
        "user_id": current_user.id
    }
    save_scenario_surfaces(data)
    
    return {"scenarioSurfaceResponseId": request_id, "status": "pending"}

@app.get("/api/scenario-surface/response/{response_id}")
async def scenario_surface_response(
    response_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Poll for scenario surface response.
    Returns empty/pending status until computation is complete.
    """
    data = load_scenario_surfaces()
    
    if response_id not in data["scenario_surfaces"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response ID not found")
    
    surface_data = data["scenario_surfaces"][response_id]
    
    # Check if still pending
    if surface_data.get("status") == "pending":
        # In a real system, check if background job completed
        # For demo, we'll simulate completion by returning mock data based on request
        request_params = surface_data.get("request", {})
        
        # Determine plot type based on how many parameters have bounds
        params_with_bounds = sum(1 for k, v in request_params.items() 
                                if k.endswith('_lower') or k.endswith('_upper'))
        param_count = params_with_bounds // 2  # Each param has lower and upper
        
        # Generate mock response based on parameter count
        if param_count == 1:
            # Find which parameter has bounds
            param_name = None
            for key in request_params.keys():
                if key.endswith('_lower'):
                    param_name = key.replace('_lower', '')
                    break
            
            surface_data = {
                "status": "completed",
                "plot_type": "1D",
                "param_name": param_name or "revenue",
                "timeseries": generate_1d_mock_data(param_name)
            }
        elif param_count == 2:
            surface_data = {
                "status": "completed",
                "plot_type": "2D",
                "param_names": ["revenue", "ebitdaMargin"],
                "timeseries": generate_2d_mock_data()
            }
        else:
            surface_data = {
                "status": "completed",
                "plot_type": "3D",
                "param_names": ["revenue", "ebitdaMargin", "debtToEbitda"],
                "timeseries": generate_3d_mock_data()
            }
        
        # Save the completed result
        data["scenario_surfaces"][response_id] = surface_data
        save_scenario_surfaces(data)
    
    return surface_data

def generate_1d_mock_data(param_name):
    """Generate mock 1D timeseries data"""
    ratings = ["B", "B+", "BB-", "BB", "BB+", "BBB-", "BBB", "BBB+", "A-", "A"]
    timeseries = {}
    for i in range(10):
        value = 40000000 + i * 2000000  # Example: revenue from 40M to 58M
        timeseries[str(i)] = [value, ratings[i]]
    return timeseries

def generate_2d_mock_data():
    """Generate mock 2D timeseries data"""
    ratings = ["BB", "BB+", "BBB-", "BB+", "BBB-", "BBB", "BBB-", "BBB", "BBB+", "BBB", "BBB+", "A-"]
    timeseries = {}
    idx = 0
    for rev in [40000000, 45000000, 50000000, 55000000]:
        for ebitda in [18.0, 22.0, 26.0]:
            timeseries[str(idx)] = [rev, ebitda, ratings[idx % len(ratings)]]
            idx += 1
            if idx >= 12:
                break
        if idx >= 12:
            break
    return timeseries

def generate_3d_mock_data():
    """Generate mock 3D timeseries data"""
    ratings = ["B+", "BB", "BB+", "BB", "BB+", "BBB-", "BB+", "BBB-", "BBB", "BBB-", "BBB", "BBB+"]
    timeseries = {}
    idx = 0
    for rev in [40000000, 50000000]:
        for ebitda in [20.0, 25.0]:
            for debt in [4.0, 3.0, 2.0]:
                timeseries[str(idx)] = [rev, ebitda, debt, ratings[idx % len(ratings)]]
                idx += 1
                if idx >= 12:
                    break
            if idx >= 12:
                break
        if idx >= 12:
            break
    return timeseries

# ─────────────────────────────────────
# Credit Score Estimator endpoints
# ─────────────────────────────────────

# Industry weights by sector
INDUSTRY_WEIGHTS = {
    'default': {
        'revenueScale': 15.0,
        'ebitdaMargin': 15.0,
        'fcfToDebt': 25.0,
        'debtToEbitda': 25.0,
        'netDebtToEbitda': 10.0,
        'ebitdaToInterest': 10.0
    }
}

def calculate_factor_score(value, factor_type):
    """Calculate letter score based on factor value and type"""
    # Simplified scoring logic - in real implementation would be more sophisticated
    if factor_type in ['revenueScale']:
        if value >= 100: return 'AA'
        if value >= 80: return 'A'
        if value >= 60: return 'BBB'
        if value >= 40: return 'BB'
        if value >= 20: return 'B'
        return 'CCC'
    elif factor_type in ['ebitdaMargin']:
        if value >= 25: return 'AA'
        if value >= 20: return 'A'
        if value >= 15: return 'BBB'
        if value >= 10: return 'BB'
        if value >= 5: return 'B'
        return 'CCC'
    elif factor_type in ['fcfToDebt']:
        if value >= 30: return 'A'
        if value >= 20: return 'BBB-'
        if value >= 15: return 'BB+'
        if value >= 10: return 'BB'
        return 'B'
    elif factor_type in ['debtToEbitda', 'netDebtToEbitda']:
        if value <= 1.0: return 'AA'
        if value <= 2.0: return 'A'
        if value <= 3.0: return 'BBB'
        if value <= 4.0: return 'BB'
        if value <= 5.0: return 'B'
        return 'CCC'
    elif factor_type in ['ebitdaToInterest']:
        if value >= 8: return 'AA'
        if value >= 5: return 'A'
        if value >= 3: return 'BBB'
        if value >= 2: return 'BB'
        return 'B'
    return 'BB'

def calculate_compass_rating(factor_scores, weights):
    """Calculate overall Compass rating from factor scores"""
    rating_values = {
        'AAA': 21, 'AA+': 20, 'AA': 19, 'AA-': 18,
        'A+': 17, 'A': 16, 'A-': 15,
        'BBB+': 14, 'BBB': 13, 'BBB-': 12,
        'BB+': 11, 'BB': 10, 'BB-': 9,
        'B+': 8, 'B': 7, 'B-': 6,
        'CCC+': 5, 'CCC': 4, 'CCC-': 3,
        'CC': 2, 'C': 1, 'D': 0
    }
    
    value_ratings = {v: k for k, v in rating_values.items()}
    
    weighted_sum = 0
    total_weight = 0
    
    for factor, score in factor_scores.items():
        if factor in weights:
            weight = weights[factor]
            rating_val = rating_values.get(score, 10)
            weighted_sum += rating_val * weight
            total_weight += weight
    
    if total_weight > 0:
        avg_rating = weighted_sum / total_weight
        # Find closest rating
        closest_val = min(rating_values.values(), key=lambda x: abs(x - avg_rating))
        return value_ratings.get(closest_val, 'BB')
    
    return 'BB'

@app.post("/api/credit-score/compute")
async def compute_credit_score(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Compute credit score based on financial inputs.
    Returns detailed factor analysis and final Compass rating.
    """
    sector = request_data.get('sector', 'Industrials')
    industry = request_data.get('industry', 'General')
    financial_data = request_data.get('financialData', {})
    
    # Get industry weights (or use default)
    weights = INDUSTRY_WEIGHTS.get(sector, INDUSTRY_WEIGHTS['default'])
    
    # Calculate weighted metrics (average across time periods)
    def get_weighted_average(key):
        vals = []
        for period in ['trailing12', 'oneYearForward', 'twoYearsForward']:
            val = financial_data.get(f'{key}_{period}')
            if val is not None:
                # Weight: 25% trailing, 50% 1yr forward, 25% 2yr forward
                if period == 'oneYearForward':
                    vals.extend([val, val])  # Double weight for 1yr forward
                else:
                    vals.append(val)
        return sum(vals) / len(vals) if vals else 0
    
    revenue = get_weighted_average('revenueScale')
    ebitda = get_weighted_average('ebitda')
    total_debt = get_weighted_average('totalDebt')
    net_debt = get_weighted_average('netDebt')
    fcf = get_weighted_average('freeCashFlow')
    
    # Calculate derived metrics
    ebitda_margin = (ebitda / revenue * 100) if revenue > 0 else 0
    fcf_to_debt = (fcf / total_debt * 100) if total_debt > 0 else 0
    debt_to_ebitda = (total_debt / ebitda) if ebitda > 0 else 0
    net_debt_to_ebitda = (net_debt / ebitda) if ebitda > 0 else 0
    # Assume interest is 5% of total debt for demo
    interest = total_debt * 0.05
    ebitda_to_interest = (ebitda / interest) if interest > 0 else 0
    
    # Calculate factor scores
    factor_scores = {
        'revenueScale': calculate_factor_score(revenue, 'revenueScale'),
        'ebitdaMargin': calculate_factor_score(ebitda_margin, 'ebitdaMargin'),
        'fcfToDebt': calculate_factor_score(fcf_to_debt, 'fcfToDebt'),
        'debtToEbitda': calculate_factor_score(debt_to_ebitda, 'debtToEbitda'),
        'netDebtToEbitda': calculate_factor_score(net_debt_to_ebitda, 'netDebtToEbitda'),
        'ebitdaToInterest': calculate_factor_score(ebitda_to_interest, 'ebitdaToInterest'),
    }
    
    # Calculate overall Compass rating
    compass_rating = calculate_compass_rating(factor_scores, weights)
    
    # Build response
    factors = [
        {
            'name': 'Revenue Scale ($ millions)',
            'weight': f"{weights['revenueScale']:.2f}%",
            'metric': f"${revenue:.2f}M",
            'score': factor_scores['revenueScale']
        },
        {
            'name': 'EBITDA Margin',
            'weight': f"{weights['ebitdaMargin']:.2f}%",
            'metric': f"{ebitda_margin:.0f}%",
            'score': factor_scores['ebitdaMargin']
        },
        {
            'name': 'Free Cash Flow / Debt',
            'weight': f"{weights['fcfToDebt']:.2f}%",
            'metric': f"{fcf_to_debt:.0f}%",
            'score': factor_scores['fcfToDebt']
        },
        {
            'name': 'Total Debt / EBITDA',
            'weight': f"{weights['debtToEbitda']:.2f}%",
            'metric': f"{debt_to_ebitda:.1f} x",
            'score': factor_scores['debtToEbitda']
        },
        {
            'name': 'Net Debt / EBITDA',
            'weight': f"{weights['netDebtToEbitda']:.2f}%",
            'metric': f"{net_debt_to_ebitda:.1f} x",
            'score': factor_scores['netDebtToEbitda']
        },
        {
            'name': 'EBITDA / Interest',
            'weight': f"{weights['ebitdaToInterest']:.2f}%",
            'metric': f"{ebitda_to_interest:.1f} x",
            'score': factor_scores['ebitdaToInterest']
        },
    ]
    
    return {
        'sector': sector,
        'industry': industry,
        'compassRating': compass_rating,
        'factors': factors
    }

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