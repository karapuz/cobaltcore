import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.data.models import User
from app.data.schemas import MessageResponse
from app.auth import get_current_user
import app.data.json_store as json_store

router = APIRouter()


@router.get("/portfolio")
async def get_portfolio(current_user: User = Depends(get_current_user)):
    """Get all credit ratings for the current user"""
    ratings = json_store.get_credit_ratings(current_user.id)
    return {"total": len(ratings), "items": ratings}


@router.get("/portfolio/{computation_id}")
async def get_credit_rating(
    computation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a single credit rating by computation ID"""
    rating = json_store.get_credit_rating_by_id(current_user.id, computation_id)
    if not rating:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit rating not found")
    return rating


@router.get("/portfolio/{computation_id}/pdf")
async def get_credit_rating_pdf(
    computation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get PDF report for a credit rating"""
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


@router.post("/portfolio", status_code=status.HTTP_201_CREATED)
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


@router.put("/portfolio/{computation_id}")
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


@router.delete("/portfolio/{computation_id}", response_model=MessageResponse)
async def delete_credit_rating(
    computation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a credit rating"""
    deleted = json_store.delete_credit_rating(current_user.id, computation_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit rating not found")
    return MessageResponse(message="Credit rating deleted successfully")
