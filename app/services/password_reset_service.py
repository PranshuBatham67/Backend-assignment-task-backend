"""
Password Reset Service

Business logic for password reset functionality.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import logging

from ..models.password_reset import PasswordResetToken
from ..models.user import User
from ..core.token_generator import generate_reset_otp, hash_token, verify_token
from ..core.email import email_service
from ..config import settings
from ..core.security import get_password_hash

logger = logging.getLogger(__name__)


class PasswordResetService:
    """Service for handling password reset operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def request_password_reset(self, email: str) -> bool:
        """
        Create a password reset request and send OTP email
        
        Args:
            email: User's email address
        
        Returns:
            Always returns True (don't leak if email exists)
        """
        try:
            # Find user by email
            user = self.db.query(User).filter(User.email == email).first()
            
            if not user:
                # Don't reveal if user exists (security)
                logger.info(f"Password reset requested for non-existent email: {email}")
                return True
            
            # Generate secure 6-digit OTP
            plain_otp, hashed_otp = generate_reset_otp()
            
            # Set expiration
            expires_at = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
            
            # Create reset token record (storing OTP hash)
            reset_token = PasswordResetToken(
                user_id=user.id,
                token_hash=hashed_otp,
                expires_at=expires_at
            )
            
            self.db.add(reset_token)
            self.db.commit()
            
            # Send OTP email
            sent = await email_service.send_password_reset_otp(
                to_email=user.email,
                user_name=user.full_name or user.email,
                otp_code=plain_otp
            )
            
            if not sent:
                raise Exception("Failed to send email")
            
            logger.info(f"Password reset OTP sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error in password reset request: {str(e)}")
            self.db.rollback()
            
            # If email sending failed specifically, propagate the error
            if str(e) == "Failed to send email":
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send password reset email. Please try again later."
                )
                
            return True  # For other errors (or user not found logic), return True to not leak information
    
    def verify_reset_token(self, token: str) -> Optional[User]:
        """
        Verify a reset token and return the associated user
        
        Args:
            token: Plain reset token from URL
        
        Returns:
            User object if token is valid, None otherwise
        """
        try:
            # Hash the provided token
            token_hash = hash_token(token)
            
            # Find token record
            reset_token = self.db.query(PasswordResetToken)\
                .filter(PasswordResetToken.token_hash == token_hash)\
                .first()
            
            if not reset_token:
                return None
            
            # Check if token is valid
            if not reset_token.is_valid():
                return None
            
            # Return associated user
            user = self.db.query(User).filter(User.id == reset_token.user_id).first()
            return user
            
        except Exception as e:
            logger.error(f"Error verifying reset token: {str(e)}")
            return None
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset user password using valid token
        
        Args:
            token: Plain reset token from URL
            new_password: New password to set
        
        Returns:
            True if password reset successful, False otherwise
        """
        try:
            # Hash the provided token
            token_hash = hash_token(token)
            
            # Find token record
            reset_token = self.db.query(PasswordResetToken)\
                .filter(PasswordResetToken.token_hash == token_hash)\
                .first()
            
            if not reset_token or not reset_token.is_valid():
                return False
            
            # Get user
            user = self.db.query(User).filter(User.id == reset_token.user_id).first()
            if not user:
                return False
            
            # Update password
            user.hashed_password = get_password_hash(new_password)
            
            # Mark token as used
            reset_token.mark_as_used()
            
            # Invalidate all other reset tokens for this user
            self.db.query(PasswordResetToken)\
                .filter(
                    PasswordResetToken.user_id == user.id,
                    PasswordResetToken.id != reset_token.id,
                    PasswordResetToken.used == False
                )\
                .update({"used": True})
            
            self.db.commit()
            
            logger.info(f"Password reset successful for user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting password: {str(e)}")
            self.db.rollback()
            return False
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from database"""
        try:
            deleted = self.db.query(PasswordResetToken)\
                .filter(PasswordResetToken.expires_at < datetime.utcnow())\
                .delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted} expired password reset tokens")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            self.db.rollback()
