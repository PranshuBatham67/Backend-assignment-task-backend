from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    """Base task schema"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.TODO
    priority: Optional[TaskPriority] = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    """Schema for creating a task"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Complete project documentation",
                "description": "Write comprehensive docs for the API",
                "status": "TODO",
                "priority": "HIGH",
                "due_date": "2024-12-31T23:59:59"
            }
        }

class TaskUpdate(BaseModel):
    """Schema for updating a task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    version: int = Field(..., description="Current version for optimistic locking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated task title",
                "status": "IN_PROGRESS",
                "priority": "URGENT",
                "version": 0
            }
        }

class TaskResponse(TaskBase):
    """Schema for task response"""
    id: int
    owner_id: int
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Complete project documentation",
                "description": "Write comprehensive docs for the API",
                "status": "TODO",
                "priority": "HIGH",
                "due_date": "2024-12-31T23:59:59",
                "owner_id": 1,
                "version": 0,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": None
            }
        }

class TaskList(BaseModel):
    """Schema for paginated task list"""
    items: List[TaskResponse]
    total: int
    page: int
    pages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 1,
                        "title": "Task 1",
                        "description": "Description",
                        "status": "TODO",
                        "priority": "MEDIUM",
                        "owner_id": 1,
                        "version": 0,
                        "created_at": "2024-01-01T00:00:00"
                    }
                ],
                "total": 1,
                "page": 1,
                "pages": 1
            }
        }

class TaskStatsResponse(BaseModel):
    """Task statistics for a user"""
    total: int
    todo: int
    in_progress: int
    completed: int
    cancelled: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 10,
                "todo": 3,
                "in_progress": 5,
                "completed": 2,
                "cancelled": 0
            }
        }
