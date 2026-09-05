from fastapi import APIRouter, Depends, HTTPException, status

from app.data.models import User
from app.auth import get_current_user
import app.data.json_store as json_store

router = APIRouter()


@router.get("/scenarios")
async def get_scenarios(current_user: User = Depends(get_current_user)):
    """Get all scenarios for the current user"""
    scenarios = json_store.get_scenarios(current_user.id)
    return {"total": len(scenarios), "items": scenarios}


@router.get("/scenarios/{computation_id}")
async def get_scenario(
    computation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a single scenario by computation ID"""
    scenario = json_store.get_scenario_by_id(current_user.id, computation_id)
    if not scenario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return scenario


@router.put("/scenarios/{computation_id}")
async def update_scenario(
    computation_id: str,
    updated_fields: dict,
    current_user: User = Depends(get_current_user)
):
    """Update an existing scenario (called on Submit)"""
    updated = json_store.update_scenario(current_user.id, computation_id, updated_fields)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scenario not found")
    return updated
