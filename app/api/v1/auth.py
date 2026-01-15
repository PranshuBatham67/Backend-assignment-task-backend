from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.auth import Token, TokenRefresh, AccessTokenResponse
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.dependencies import get_current_active_user
from app.models.user import User
from app.core.rate_limiter import limiter

router = APIRouter()

@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password. Returns JWT tokens for immediate authentication."
)
@limiter.limit("5/minute")  # Prevent registration spam
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user with the following:
    - **email**: Valid email address (must be unique)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, number)
    - **full_name**: Optional full name
    
    Returns JWT access token and refresh token.
    """
    try:
        result = AuthService.register(
            db=db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name
        )
        
        # Convert user to response format
        user_response = UserResponse.from_orm_with_roles(result["user"])
        
        return {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "user": user_response
        }
    except Exception as e:
        raise e

@router.post(
    "/login",
    response_model=Token,
    summary="Login to get access tokens",
    description="Authenticate with email and password to receive JWT tokens"
)
@limiter.limit("10/minute")  # Prevent brute force attacks
async def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns:
    - Access token (expires in 30 minutes)
    - Refresh token (expires in 7 days)
    - User information
    """
    result = AuthService.login(
        db=db,
        email=credentials.email,
        password=credentials.password
    )
    
    user_response = UserResponse.from_orm_with_roles(result["user"])
    
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
        "user": user_response
    }

@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
    description="Get a new access token using a refresh token"
)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    Use a refresh token to get a new access token.
    Useful when the access token expires but you want to keep the user logged in.
    """
    result = AuthService.refresh_access_token(
        db=db,
        refresh_token=token_data.refresh_token
    )
    
    return result

@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="Logout user",
    description="Invalidate the current access token (adds it to blacklist)"
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout the current user by blacklisting their token.
    The token will no longer be valid after this call.
    """
    # Extract token from Authorization header
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix
        # Blacklist the token
        AuthService.logout(db, token)
    
    return {"message": "Successfully logged out"}

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user info",
    description="Get information about the currently authenticated user"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of the currently logged-in user.
    Requires valid JWT token in Authorization header.
    """
    return UserResponse.from_orm_with_roles(current_user)
