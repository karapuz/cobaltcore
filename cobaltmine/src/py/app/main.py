from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base
from app.models import User
from app.schemas import (
    UserCreate, UserLogin, UserResponse, UserUpdate,
    LoginResponse, SignupResponse, MessageResponse, RefreshToken
)
from .auth import (
    get_password_hash, authenticate_user, create_access_token,
    create_refresh_token, get_current_user, verify_token
)
from .config import get_settings

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Compass Analytics API",
    description="Compass Analytics Platform Backend API",
    version="1.0.0"
)

settings = get_settings()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Backend is running"}

# Signup endpoint
@app.post("/api/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # import pdb; pdb.set_trace()

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email.lower(),
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    
    return SignupResponse(
        message="User created successfully",
        user=new_user,
        access_token=access_token,
        refresh_token=refresh_token
    )

# Login endpoint
@app.post("/api/login", response_model=LoginResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return tokens"""
    
    user = authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return LoginResponse(
        message="Login successful",
        user=user,
        access_token=access_token,
        refresh_token=refresh_token
    )

# Refresh token endpoint
@app.post("/api/refresh")
async def refresh_token(refresh_data: RefreshToken, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    
    try:
        token_data = verify_token(refresh_data.refresh_token, token_type="refresh")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify user still exists
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user
@app.get("/api/user", response_model=UserResponse)
async def get_user(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user

# Update user profile
@app.put("/api/user/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    if user_update.name is not None:
        current_user.name = user_update.name
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

# Logout endpoint
@app.post("/api/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint (client should delete tokens)"""
    return MessageResponse(message="Logout successful")

# Error handlers
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