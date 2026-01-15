from pydantic import BaseModel
from typing import Optional

class PaginationParams(BaseModel):
    """Common pagination parameters"""
    skip: int = 0
    limit: int = 20
    
    class Config:
        json_schema_extra = {
            "example": {
                "skip": 0,
                "limit": 20
            }
        }

class ErrorResponse(BaseModel):
    """Standard error response format"""
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "An error occurred"
            }
        }

class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }
