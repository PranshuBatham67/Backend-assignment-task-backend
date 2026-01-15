from fastapi import APIRouter
from app.api.v2 import tasks

# Create the main v2 router
api_router = APIRouter()

# Include v2 routers
# V2 has enhanced task features (demonstration of API evolution)
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks V2"])
