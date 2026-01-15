from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.tasks import router as tasks_router

__all__ = ["auth_router", "users_router", "tasks_router"]
