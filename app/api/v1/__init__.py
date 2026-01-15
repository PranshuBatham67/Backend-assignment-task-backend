from fastapi import APIRouter
from app.api.v1 import auth, users, tasks, password_reset

# Create the main v1 router
api_router = APIRouter()

# Include all v1 sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(password_reset.router, prefix="/auth", tags=["Password Reset"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
