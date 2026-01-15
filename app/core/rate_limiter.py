from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

# Create rate limiter instance
# Use memory storage for testing/development
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE_IP}/minute"],
    storage_uri="memory://",
    swallow_errors=True
)
print("Rate limiter: Using in-memory storage")

def get_user_rate_limit():
    """Rate limit per authenticated user"""
    return f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
