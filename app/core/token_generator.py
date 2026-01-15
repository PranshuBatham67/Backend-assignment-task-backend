"""
OTP Generator for Password Reset

Generates 6-digit OTP codes for password reset.
"""

import secrets
import hashlib
import random
from typing import Tuple


def generate_reset_otp() -> Tuple[str, str]:
    """
    Generate a 6-digit OTP for password reset
    
    Returns:
        Tuple of (plain_otp, hashed_otp)
        - plain_otp: Send to user via email (6 digits)
        - hashed_otp: Store in database
    """
    # Generate a cryptographically secure 6-digit OTP
    plain_otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # Hash the OTP for storage
    hashed_otp = hash_token(plain_otp)
    
    return plain_otp, hashed_otp


def hash_token(token: str) -> str:
    """
    Hash a token using SHA-256
    
    Args:
        token: Plain text token/OTP
    
    Returns:
        Hexadecimal hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(plain_token: str, hashed_token: str) -> bool:
    """
    Verify a plain token/OTP against its hash
    
    Args:
        plain_token: The plain text token/OTP from user
        hashed_token: The stored hash
    
    Returns:
        True if tokens match, False otherwise
    """
    return hash_token(plain_token) == hashed_token
