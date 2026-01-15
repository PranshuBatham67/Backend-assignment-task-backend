from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    
    # When the token expires (we can clean up old entries)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # When it was blacklisted
    blacklisted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<BlacklistedToken {self.id}>"
