from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.config import settings
import hashlib

# Password hashing context - using bcrypt with cost factor 12
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    Returns True if they match, False otherwise.
    """
    # Pre-hash with SHA-256 to handle any password length
    prehashed = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(prehashed, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password using SHA-256 + bcrypt.
    SHA-256 pre-hashing ensures passwords of any length can be hashed.
    This is a standard approach recommended for bcrypt with long passwords.
    """
    # Pre-hash with SHA-256 to handle passwords longer than 72 bytes
    prehashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(prehashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing the claims to encode
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token as string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.
    
    Returns:
        Dictionary with token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Extract the expiration time from a token.
    Useful for blacklisting tokens on logout.
    """
    payload = decode_token(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None
