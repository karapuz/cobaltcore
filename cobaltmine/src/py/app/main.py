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
# Index Analysis endpoints
# ─────────────────────────────────────

MOCK_INDICES = [
    {"index_name": "Dow Jones Industrial Average", "index_id": "DJIA"},
    {"index_name": "S&P 500", "index_id": "SPX"},
    {"index_name": "NASDAQ 100", "index_id": "NDX"},
]

MOCK_TICKERS = {
    "DJIA": [
        {"ticker_name": "Apple Inc.", "ticker_id": "AAPL"},
        {"ticker_name": "Microsoft Corporation", "ticker_id": "MSFT"},
        {"ticker_name": "JPMorgan Chase & Co.", "ticker_id": "JPM"},
        {"ticker_name": "Visa Inc.", "ticker_id": "V"},
        {"ticker_name": "Johnson & Johnson", "ticker_id": "JNJ"},
        {"ticker_name": "Walmart Inc.", "ticker_id": "WMT"},
        {"ticker_name": "Procter & Gamble Co.", "ticker_id": "PG"},
        {"ticker_name": "UnitedHealth Group Inc.", "ticker_id": "UNH"},
        {"ticker_name": "Home Depot Inc.", "ticker_id": "HD"},
        {"ticker_name": "Chevron Corporation", "ticker_id": "CVX"},
    ],
    "SPX": [
        {"ticker_name": "Apple Inc.", "ticker_id": "AAPL"},
        {"ticker_name": "Microsoft Corporation", "ticker_id": "MSFT"},
        {"ticker_name": "Amazon.com Inc.", "ticker_id": "AMZN"},
        {"ticker_name": "NVIDIA Corporation", "ticker_id": "NVDA"},
        {"ticker_name": "Alphabet Inc.", "ticker_id": "GOOGL"},
    ],
    "NDX": [
        {"ticker_name": "Apple Inc.", "ticker_id": "AAPL"},
        {"ticker_name": "Microsoft Corporation", "ticker_id": "MSFT"},
        {"ticker_name": "NVIDIA Corporation", "ticker_id": "NVDA"},
        {"ticker_name": "Meta Platforms Inc.", "ticker_id": "META"},
    ],
}

# Mock basic values per ticker (in billions, ratios as decimals)
MOCK_BASIC_VALUES = {
    "AAPL": {"revenue": 394.3, "ebitda": 130.5, "free_cash_flow": 99.6, "debt": 111.1, "total_debt": 111.1, "net_debt": 49.0, "interest": 3.9, "operating_cash_flow": 110.5, "short_term_debt": 15.0},
    "MSFT": {"revenue": 211.9, "ebitda": 98.1, "free_cash_flow": 59.5, "debt": 78.4, "total_debt": 78.4, "net_debt": -28.0, "interest": 2.1, "operating_cash_flow": 87.7, "short_term_debt": 5.0},
    "JPM":  {"revenue": 154.8, "ebitda": 65.2, "free_cash_flow": 35.0, "debt": 450.0, "total_debt": 450.0, "net_debt": 350.0, "interest": 18.5, "operating_cash_flow": 45.0, "short_term_debt": 50.0},
    "V":    {"revenue": 32.7, "ebitda": 21.3, "free_cash_flow": 18.5, "debt": 20.5, "total_debt": 20.5, "net_debt": 5.2, "interest": 0.6, "operating_cash_flow": 19.8, "short_term_debt": 3.0},
    "JNJ":  {"revenue": 85.2, "ebitda": 28.5, "free_cash_flow": 17.8, "debt": 35.5, "total_debt": 35.5, "net_debt": 12.3, "interest": 0.9, "operating_cash_flow": 22.1, "short_term_debt": 5.5},
    "WMT":  {"revenue": 611.3, "ebitda": 36.2, "free_cash_flow": 12.5, "debt": 55.8, "total_debt": 55.8, "net_debt": 42.1, "interest": 2.1, "operating_cash_flow": 28.8, "short_term_debt": 8.2},
    "PG":   {"revenue": 82.0, "ebitda": 20.5, "free_cash_flow": 14.2, "debt": 33.1, "total_debt": 33.1, "net_debt": 22.5, "interest": 0.8, "operating_cash_flow": 17.5, "short_term_debt": 4.8},
    "UNH":  {"revenue": 324.2, "ebitda": 32.8, "free_cash_flow": 22.1, "debt": 58.2, "total_debt": 58.2, "net_debt": 35.6, "interest": 2.8, "operating_cash_flow": 28.5, "short_term_debt": 6.5},
    "HD":   {"revenue": 152.7, "ebitda": 24.8, "free_cash_flow": 14.5, "debt": 42.5, "total_debt": 42.5, "net_debt": 38.2, "interest": 1.8, "operating_cash_flow": 18.2, "short_term_debt": 2.8},
    "CVX":  {"revenue": 200.5, "ebitda": 45.2, "free_cash_flow": 21.5, "debt": 25.8, "total_debt": 25.8, "net_debt": 8.5, "interest": 0.7, "operating_cash_flow": 35.2, "short_term_debt": 3.2},
    "AMZN": {"revenue": 574.8, "ebitda": 85.5, "free_cash_flow": 32.2, "debt": 67.2, "total_debt": 67.2, "net_debt": -18.5, "interest": 2.1, "operating_cash_flow": 84.5, "short_term_debt": 8.5},
    "NVDA": {"revenue": 60.9, "ebitda": 33.8, "free_cash_flow": 27.2, "debt": 11.2, "total_debt": 11.2, "net_debt": -15.8, "interest": 0.3, "operating_cash_flow": 28.5, "short_term_debt": 1.2},
    "GOOGL": {"revenue": 307.4, "ebitda": 97.5, "free_cash_flow": 60.2, "debt": 28.5, "total_debt": 28.5, "net_debt": -90.5, "interest": 0.5, "operating_cash_flow": 91.5, "short_term_debt": 3.5},
    "META": {"revenue": 134.9, "ebitda": 52.5, "free_cash_flow": 43.0, "debt": 18.4, "total_debt": 18.4, "net_debt": -23.5, "interest": 0.4, "operating_cash_flow": 71.1, "short_term_debt": 2.1},
}

INDEX_DEFAULT_RANGES = {
    "revenue_scale": [100, 50, 25, 12.5, 6, 3, 1.5, 1],
    "ebitda_margin": [0.35, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05, 0.02],
    "fcf_debt": [1.0, 0.5, 0.3, 0.2, 0.15, 0.10, 0.05, 0.02],
    "td_ebitda": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    "nd_ebitda": [0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0],
    "ebitda_interest": [15, 10, 8, 6, 4, 3, 2, 1.5],
    "dscr": [3.0, 2.5, 2.0, 1.5, 1.2, 1.0, 0.8, 0.5],
}

INDEX_DEFAULT_WEIGHTS = {
    "revenue_scale": 0.15,
    "ebitda_margin": 0.15,
    "fcf_debt": 0.15,
    "td_ebitda": 0.15,
    "nd_ebitda": 0.10,
    "ebitda_interest": 0.15,
    "dscr": 0.15,
}

# Increasing = True means higher value = better (lower rank)
PILLAR_DIRECTION = {
    "revenue_scale": True,
    "ebitda_margin": True,
    "fcf_debt": True,
    "td_ebitda": False,
    "nd_ebitda": False,
    "ebitda_interest": True,
    "dscr": True,
}

PILLAR_NAMES = {
    "revenue_scale": "Revenue Scale",
    "ebitda_margin": "EBITDA Margin",
    "fcf_debt": "Free Cash Flow / Debt",
    "td_ebitda": "Total Debt / EBITDA",
    "nd_ebitda": "Net Debt / EBITDA",
    "ebitda_interest": "EBITDA / Interest",
    "dscr": "Debt Service Coverage Ratio",
}

INDEX_RATING_SCALE = [
    ("AAA",   0.0,  1.5),
    ("AA+",   1.5,  2.5),
    ("AA",    2.5,  3.5),
    ("AA-",   3.5,  4.5),
    ("A+",    4.5,  5.5),
    ("A",     5.5,  6.5),
    ("A-",    6.5,  7.5),
    ("BBB+",  7.5,  8.5),
    ("BBB",   8.5,  9.5),
    ("BBB-",  9.5, 10.5),
    ("BB+",  10.5, 11.5),
    ("BB",   11.5, 12.5),
    ("BB-",  12.5, 13.5),
    ("B+",   13.5, 14.5),
    ("B",    14.5, 15.5),
    ("B-",   15.5, 16.5),
    ("CCC+", 16.5, 17.5),
    ("CCC",  17.5, 18.5),
    ("CCC-", 18.5, 19.5),
    ("CC",   19.5, 25.0),
]

def calculate_pillar_values(basic):
    """Calculate pillar values from basic financials"""
    revenue = basic.get("revenue", 0)
    ebitda = basic.get("ebitda", 0)
    fcf = basic.get("free_cash_flow", 0)
    debt = basic.get("debt", 1)
    total_debt = basic.get("total_debt", 1)
    net_debt = basic.get("net_debt", 0)
    interest = basic.get("interest", 1)
    ocf = basic.get("operating_cash_flow", 0)
    std = basic.get("short_term_debt", 0)
    
    return {
        "revenue_scale": revenue,
        "ebitda_margin": ebitda / revenue if revenue else 0,
        "fcf_debt": fcf / debt if debt else 0,
        "td_ebitda": total_debt / ebitda if ebitda else 0,
        "nd_ebitda": net_debt / ebitda if ebitda else 0,
        "ebitda_interest": ebitda / interest if interest else 0,
        "dscr": ocf / (std + debt) if (std + debt) else 0,
    }

def calculate_rank(value, breakpoints, is_increasing):
    """Calculate rank based on value and breakpoints"""
    if is_increasing:
        for i, bp in enumerate(breakpoints):
            if value >= bp:
                return i
        return len(breakpoints)
    else:
        for i, bp in enumerate(breakpoints):
            if value <= bp:
                return i
        return len(breakpoints)

def get_range_display(rank, breakpoints, is_increasing):
    """Get display string for the range"""
    if is_increasing:
        if rank == 0:
            return f"≥{breakpoints[0]}"
        elif rank < len(breakpoints):
            return f"{breakpoints[rank]}-{breakpoints[rank-1]}"
        else:
            return f"<{breakpoints[-1]}"
    else:
        if rank == 0:
            return f"≤{breakpoints[0]}"
        elif rank < len(breakpoints):
            return f"{breakpoints[rank-1]}-{breakpoints[rank]}"
        else:
            return f">{breakpoints[-1]}"

def format_pillar_value(pillar_id, value):
    """Format pillar value for display"""
    if pillar_id == "revenue_scale":
        return f"${value:.1f}B"
    elif pillar_id in ["ebitda_margin", "fcf_debt"]:
        return f"{value*100:.1f}%"
    else:
        return f"{value:.2f}x"

def index_score_to_rating(score):
    """Convert total score to rating"""
    for rating, low, high in INDEX_RATING_SCALE:
        if low <= score < high:
            return rating
    return "CC"

def build_pillar_response(ticker_id, weights=None, ranges=None):
    """Build full pillar response for a ticker"""
    weights = weights or INDEX_DEFAULT_WEIGHTS
    ranges = ranges or INDEX_DEFAULT_RANGES
    
    basic = MOCK_BASIC_VALUES.get(ticker_id, MOCK_BASIC_VALUES["AAPL"])
    pillar_values = calculate_pillar_values(basic)
    
    pillars = []
    total_score = 0
    
    for pillar_id in ["revenue_scale", "ebitda_margin", "fcf_debt", "td_ebitda", "nd_ebitda", "ebitda_interest", "dscr"]:
        value = pillar_values[pillar_id]
        is_increasing = PILLAR_DIRECTION[pillar_id]
        breakpoints = ranges.get(pillar_id, INDEX_DEFAULT_RANGES[pillar_id])
        weight = weights.get(pillar_id, INDEX_DEFAULT_WEIGHTS[pillar_id])
        
        rank = calculate_rank(value, breakpoints, is_increasing)
        score = rank * weight
        total_score += score
        
        pillars.append({
            "name": PILLAR_NAMES[pillar_id],
            "id": pillar_id,
            "value": value,
            "formatted_value": format_pillar_value(pillar_id, value),
            "rank": rank,
            "range_display": get_range_display(rank, breakpoints, is_increasing),
            "range_breakpoints": breakpoints,
            "weight": weight,
            "is_increasing": is_increasing,
        })
    
    return {
        "pillars": pillars,
        "total_score": total_score,
        "compass_rating": index_score_to_rating(total_score),
    }


@app.get("/api/v0/index/name/historical")
async def get_indices(
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get list of available indices"""
    return {"indices": MOCK_INDICES}


@app.get("/api/v0/index/value/historical")
async def get_index_tickers(
    index_id: str,
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get tickers for a specific index"""
    tickers = MOCK_TICKERS.get(index_id, [])
    return {"tickers": tickers}


@app.get("/api/v0/pillar/values/historical")
async def get_pillar_values(
    ticker_id: str,
    effective_date: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get pillar values for a specific ticker"""
    return build_pillar_response(ticker_id)


@app.post("/api/v0/pillar/recalculate")
async def recalculate_pillars(
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Recalculate pillars with custom weights and ranges"""
    ticker_id = request_data.get("ticker_id", "AAPL")
    weights = request_data.get("weights")
    ranges = request_data.get("ranges")
    return build_pillar_response(ticker_id, weights, ranges)

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