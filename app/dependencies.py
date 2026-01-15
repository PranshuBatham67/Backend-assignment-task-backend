from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.core.security import decode_token
from app.core.exceptions import (
    InvalidTokenException,
    InactiveUserException,
    InsufficientPermissionsException
)
from app.services.user_service import UserService
from app.services.auth_service import AuthService

# HTTP Bearer token scheme
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Validates the token and returns the user object.
    """
    token = credentials.credentials
    
    # Check if token is blacklisted (logged out)
    if AuthService.is_token_blacklisted(db, token):
        raise InvalidTokenException()
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise InvalidTokenException()
    
    # Verify token type
    if payload.get("type") != "access":
        raise InvalidTokenException()
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenException()
    
    # Get user from database
    user = UserService.get_by_id(db, int(user_id))
    if not user:
        raise InvalidTokenException()
    
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure the current user is active.
    """
    if not current_user.is_active:
        raise InactiveUserException()
    
    return current_user

def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to require admin role.
    Only allows superusers or users with ADMIN role.
    """
    if not current_user.is_admin:
        raise InsufficientPermissionsException()
    
    return current_user

def require_role(role_name: str):
    """
    Factory function to create role-based dependency.
    Usage: current_user = Depends(require_role("ADMIN"))
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.has_role(role_name) and not current_user.is_superuser:
            raise InsufficientPermissionsException()
        return current_user
    
    return role_checker

# Optional authentication - doesn't fail if no token provided
def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Optional authentication dependency.
    Returns user if valid token provided, None otherwise.
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = UserService.get_by_id(db, int(user_id))
        if user and user.is_active and not AuthService.is_token_blacklisted(db, token):
            return user
    except:
        pass
    
    return None
