from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.user import User
from app.core.exceptions import (
    ResourceNotFoundException,
    InsufficientPermissionsException,
    ConcurrentModificationException
)
from app.core.cache import cache

class TaskService:
    """Service for task-related operations with advanced features"""
    
    @staticmethod
    def create_task(
        db: Session,
        title: str,
        owner_id: int,
        description: Optional[str] = None,
        status: TaskStatus = TaskStatus.TODO,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date: Optional[datetime] = None
    ) -> Task:
        """Create a new task"""
        task = Task(
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            owner_id=owner_id,
            version=0
        )
        
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Invalidate user's task list cache
        cache.delete_pattern(f"tasks:user:{owner_id}:*")
        
        return task
    
    @staticmethod
    def get_task_by_id(db: Session, task_id: int, include_deleted: bool = False) -> Optional[Task]:
        """Get a single task by ID"""
        query = db.query(Task).filter(Task.id == task_id)
        
        if not include_deleted:
            query = query.filter(Task.deleted_at.is_(None))
        
        return query.first()
    
    @staticmethod
    def list_tasks(
        db: Session,
        owner_id: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """
        List tasks with filtering, searching, sorting and pagination.
        Returns dict with items and total count.
        """
        # Try to get from cache first
        cache_key = f"tasks:user:{owner_id}:status:{status}:p:{skip}:l:{limit}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build query
        query = db.query(Task).filter(Task.deleted_at.is_(None))
        
        # Filter by owner
        if owner_id:
            query = query.filter(Task.owner_id == owner_id)
        
        # Filter by status
        if status:
            query = query.filter(Task.status == status)
        
        # Filter by priority
        if priority:
            query = query.filter(Task.priority == priority)
        
        # Search in title and description
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Task.title.ilike(search_pattern),
                    Task.description.ilike(search_pattern)
                )
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Sorting
        if sort_order == "desc":
            query = query.order_by(getattr(Task, sort_by).desc())
        else:
            query = query.order_by(getattr(Task, sort_by).asc())
        
        # Pagination
        tasks = query.offset(skip).limit(limit).all()
        
        result = {
            "items": tasks,
            "total": total,
            "page": (skip // limit) + 1 if limit > 0 else 1,
            "pages": (total + limit - 1) // limit if limit > 0 else 1
        }
        
        # Cache the result for 2 minutes
        cache.set(cache_key, result, ttl=120)
        
        return result
    
    @staticmethod
    def update_task(
        db: Session,
        task_id: int,
        current_user: User,
        version: int,
        **update_data
    ) -> Task:
        """
        Update task with optimistic locking to prevent concurrent modifications.
        The version field must match the current version in DB.
        """
        # I use SELECT FOR UPDATE to lock the row (handles race conditions)
        task = db.query(Task).filter(
            and_(Task.id == task_id, Task.deleted_at.is_(None))
        ).with_for_update().first()
        
        if not task:
            raise ResourceNotFoundException("Task")
        
        # Check ownership (only owner or admin can update)
        if task.owner_id != current_user.id and not current_user.is_admin:
            raise InsufficientPermissionsException()
        
        # Check version for optimistic locking
        if task.version != version:
            raise ConcurrentModificationException()
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(task, key) and key not in ['id', 'owner_id', 'version', 'created_at']:
                setattr(task, key, value)
        
        # Increment version
        task.version += 1
        
        db.commit()
        db.refresh(task)
        
        # Invalidate cache
        cache.delete_pattern(f"tasks:user:{task.owner_id}:*")
        
        return task
    
    @staticmethod
    def delete_task(db: Session, task_id: int, current_user: User, hard_delete: bool = False) -> bool:
        """
        Delete a task (soft delete by default).
        Only owner or admin can delete.
        """
        task = db.query(Task).filter(
            and_(Task.id == task_id, Task.deleted_at.is_(None))
        ).with_for_update().first()
        
        if not task:
            raise ResourceNotFoundException("Task")
        
        # Check ownership
        if task.owner_id != current_user.id and not current_user.is_admin:
            raise InsufficientPermissionsException()
        
        if hard_delete:
            # Permanent deletion
            db.delete(task)
        else:
            # Soft delete
            task.deleted_at = datetime.utcnow()
        
        db.commit()
        
        # Invalidate cache
        cache.delete_pattern(f"tasks:user:{task.owner_id}:*")
        
        return True
    
    @staticmethod
    def get_user_task_stats(db: Session, user_id: int) -> Dict[str, int]:
        """Get task statistics for a user"""
        stats = {
            "total": 0,
            "todo": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0
        }
        
        tasks = db.query(Task).filter(
            and_(Task.owner_id == user_id, Task.deleted_at.is_(None))
        ).all()
        
        stats["total"] = len(tasks)
        for task in tasks:
            if task.status == TaskStatus.TODO:
                stats["todo"] += 1
            elif task.status == TaskStatus.IN_PROGRESS:
                stats["in_progress"] += 1
            elif task.status == TaskStatus.COMPLETED:
                stats["completed"] += 1
            elif task.status == TaskStatus.CANCELLED:
                stats["cancelled"] += 1
        
        return stats
