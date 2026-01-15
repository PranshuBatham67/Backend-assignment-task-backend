from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128,
        description="Password must be between 8 and 128 characters"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe"
            }
        }

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }

class UserResponse(UserBase):
    """Schema for user response (without sensitive info)"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    roles: List[str] = []
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-01-01T00:00:00",
                "roles": ["USER"]
            }
        }
    
    @classmethod
    def from_orm_with_roles(cls, user):
        """Helper to convert ORM User to response with role names"""
        user_dict = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": user.created_at,
            "roles": [role.name for role in user.roles]
        }
        return cls(**user_dict)
