from sqlalchemy.orm import Session
from datetime import datetime
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token,
    decode_token,
    get_token_expiry
)
from app.core.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    InactiveUserException
)
from app.services.user_service import UserService
from typing import Dict
import re

class AuthService:
    """Service for authentication and authorization operations"""
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validate password meets minimum security requirements:
        - At least 8 characters
        - Contains uppercase and lowercase
        - Contains at least one number
        """
        if len(password) < 8:
            return False
        
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        
        return has_upper and has_lower and has_digit
    
    @staticmethod
    def register(
        db: Session,
        email: str,
        password: str,
        full_name: str = None
    ) -> Dict[str, any]:
        """
        Register a new user and return access tokens.
        """
        # Validate email format (basic check)
        if '@' not in email or '.' not in email.split('@')[1]:
            raise InvalidCredentialsException()
        
        # Validate password strength
        if not AuthService.validate_password_strength(password):
            from app.core.exceptions import ValidationException
            raise ValidationException(
                "Password must be at least 8 characters with uppercase, lowercase, and number"
            )
        
        # Create the user
        user = UserService.create_user(db, email, password, full_name)
        
        # Generate tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }
    
    @staticmethod
    def login(db: Session, email: str, password: str) -> Dict[str, any]:
        """
        Authenticate user and return access tokens.
        """
        # Get user by email
        user = UserService.get_by_email(db, email)
        if not user:
            raise InvalidCredentialsException()
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        
        # Check if user is active
        if not user.is_active:
            raise InactiveUserException()
        
        # Generate tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }
    
    @staticmethod
    def refresh_access_token(db: Session, refresh_token: str) -> Dict[str, str]:
        """
        Generate a new access token using a refresh token.
        """
        # Decode refresh token
        payload = decode_token(refresh_token)
        if not payload:
            raise InvalidTokenException()
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise InvalidTokenException()
        
        # Check if token is blacklisted
        if AuthService.is_token_blacklisted(db, refresh_token):
            raise InvalidTokenException()
        
        # Get user
        user_id = payload.get("sub")
        user = UserService.get_by_id(db, int(user_id))
        if not user or not user.is_active:
            raise InvalidTokenException()
        
        # Create new access token
        access_token = create_access_token({"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    def logout(db: Session, token: str) -> bool:
        """
        Logout by blacklisting the token.
        """
        # Get token expiry
        expires_at = get_token_expiry(token)
        if not expires_at:
            return False
        
        # Add to blacklist
        blacklisted = TokenBlacklist(
            token=token,
            expires_at=expires_at
        )
        db.add(blacklisted)
        db.commit()
        
        return True
    
    @staticmethod
    def is_token_blacklisted(db: Session, token: str) -> bool:
        """Check if a token is blacklisted"""
        result = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
        return result is not None
    
    @staticmethod
    def cleanup_expired_tokens(db: Session):
        """Remove expired tokens from blacklist (run periodically)"""
        db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
