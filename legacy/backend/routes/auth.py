from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from models.user import UserCreate, UserLogin, TokenResponse, UserResponse
from services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()

class ResetPasswordRequest(BaseModel):
    identifier: str  # email or phone
    new_password: str
    confirm_password: str

class ResetPasswordResponse(BaseModel):
    success: bool
    message: str

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await auth_service.register(user_data)
        _, token = await auth_service.login(user_data.phone, user_data.password)
        return TokenResponse(access_token=token, user=user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login user"""
    try:
        user, token = await auth_service.login(login_data.identifier, login_data.password)
        return TokenResponse(access_token=token, user=user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(reset_data: ResetPasswordRequest):
    """Reset user password"""
    # Validate passwords match
    if reset_data.new_password != reset_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Validate password length
    if len(reset_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    try:
        await auth_service.reset_password(reset_data.identifier, reset_data.new_password)
        return ResetPasswordResponse(
            success=True,
            message="Password reset successfully. You can now login with your new password."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = None):
    """Get current user profile"""
    from utils.auth import get_current_user
    from fastapi import Depends
    # This endpoint needs the dependency injected at router level
    pass
