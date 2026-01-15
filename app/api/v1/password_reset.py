"""
Password Reset API Endpoints

Handles forgot password and reset password functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
import re

from ...database import get_db
from ...services.password_reset_service import PasswordResetService
from ...core.rate_limiter import limiter

router = APIRouter()


# Pydantic Models
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    
    @validator('otp')
    def otp_format(cls, v):
        """Validate OTP format"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError('OTP must be exactly 6 digits')
        return v
    
    @validator('new_password')
    def password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class VerifyTokenRequest(BaseModel):
    token: str


class MessageResponse(BaseModel):
    message: str


class TokenValidResponse(BaseModel):
    valid: bool
    email: str = None


@router.post("/forgot-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
# @limiter.limit("3/15minutes")  # Temporarily disabled for debugging
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email
    
    Security: Always returns success even if email doesn't exist
    to prevent email enumeration attacks.
    """
    service = PasswordResetService(db)
    await service.request_password_reset(request.email)
    
    return MessageResponse(
        message="If an account exists with that email, a password reset link has been sent."
    )


@router.post("/verify-reset-token", response_model=TokenValidResponse)
async def verify_reset_token(
    request: VerifyTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Verify if a reset token is valid
    
    Returns user email if token is valid.
    """
    service = PasswordResetService(db)
    user = service.verify_reset_token(request.token)
    
    if not user:
        return TokenValidResponse(valid=False)
    
    return TokenValidResponse(
        valid=True,
        email=user.email
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using OTP code
    """
    service = PasswordResetService(db)
    
    # Find user by email first
    from ...models.user import User
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or OTP"
        )
    
    # Find valid OTP for this user
    from ...models.password_reset import PasswordResetToken
    from ...core.token_generator import hash_token
    from datetime import datetime
    
    otp_hash = hash_token(request.otp)
    reset_token = db.query(PasswordResetToken)\
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.token_hash == otp_hash,
            PasswordResetToken.used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        )\
        .first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    
    # Reset password
    success = service.reset_password(request.otp, request.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password"
        )
    
    return MessageResponse(
        message="Password has been reset successfully"
    )
