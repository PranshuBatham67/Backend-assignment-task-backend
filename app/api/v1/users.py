from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.dependencies import require_admin, get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List all users (Admin only)",
    description="Get a list of all registered users. Requires admin privileges."
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Retrieve a paginated list of users.
    
    Admin only endpoint
    
    Query parameters:
    - skip: Pagination offset (default: 0)
    - limit: Number of results (default: 20, max: 100)
    """
    users = UserService.list_users(db, skip=skip, limit=limit)
    return [UserResponse.from_orm_with_roles(user) for user in users]

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (Admin only)",
    description="Get detailed information about a specific user"
)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get a specific user by their ID.
    
    Admin only endpoint
    """
    from app.core.exceptions import ResourceNotFoundException
    user = UserService.get_by_id(db, user_id)
    if not user:
        raise ResourceNotFoundException("User")
    
    return UserResponse.from_orm_with_roles(user)

@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate user (Admin only)",
    description="Deactivate a user account"
)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account.
    Deactivated users cannot log in.
    
    Admin only endpoint
    """
    user = UserService.deactivate_user(db, user_id)
    return UserResponse.from_orm_with_roles(user)
