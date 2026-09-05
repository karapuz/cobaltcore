import hashlib
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from app.data.models import User
from app.auth import get_current_user

router = APIRouter()

SCENARIO_SURFACES_FILE = Path(__file__).parent.parent.parent / "data" / "scenario_surfaces.json"


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


def generate_1d_mock_data(param_name):
    """Generate mock 1D timeseries data"""
    ratings = ["B", "B+", "BB-", "BB", "BB+", "BBB-", "BBB", "BBB+", "A-", "A"]
    timeseries = {}
    for i in range(10):
        value = 40000000 + i * 2000000
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


@router.post("/scenario-surface/request")
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
    
    # Store the request as pending
    data["scenario_surfaces"][request_id] = {
        "status": "pending",
        "request": request_data,
        "user_id": current_user.id
    }
    save_scenario_surfaces(data)
    
    return {"scenarioSurfaceResponseId": request_id, "status": "pending"}


@router.get("/scenario-surface/response/{response_id}")
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
        request_params = surface_data.get("request", {})
        
        # Determine plot type based on how many parameters have bounds
        params_with_bounds = sum(1 for k, v in request_params.items() 
                                if k.endswith('_lower') or k.endswith('_upper'))
        param_count = params_with_bounds // 2
        
        # Generate mock response based on parameter count
        if param_count == 1:
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
