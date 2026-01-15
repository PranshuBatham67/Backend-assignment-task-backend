from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.task import (
    TaskCreate, 
    TaskUpdate, 
    TaskResponse, 
    TaskList,
    TaskStatsResponse
)
from app.schemas.common import SuccessResponse
from app.services.task_service import TaskService
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.task import TaskStatus, TaskPriority
from app.core.rate_limiter import limiter, get_user_rate_limit

router = APIRouter()

@router.post(
    "/",
    response_model=TaskResponse,
    status_code=201,
    summary="Create a new task",
    description="Create a new task for the authenticated user"
)
@limiter.limit(get_user_rate_limit())
async def create_task(
    request: Request,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new task.
    
    The task will be automatically assigned to the current user.
    
    Request body:
    - **title**: Task title (required, max 255 chars)
    - **description**: Detailed description (optional)
    - **status**: Task status (default: TODO)
    - **priority**: Task priority (default: MEDIUM)
    - **due_date**: Optional deadline
    """
    task = TaskService.create_task(
        db=db,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date,
        owner_id=current_user.id
    )
    
    return task

@router.get(
    "/",
    response_model=TaskList,
    summary="List tasks",
    description="Get a paginated list of tasks with filtering and search"
)
@limiter.limit(get_user_rate_limit())
async def list_tasks(
    request: Request,
    status: Optional[TaskStatus] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List tasks for the current user with advanced filtering.
    
    Features:
    - Filtering: By status and priority
    - Search : Search in title and description
    - Sorting: Sort by any field (created_at, title, priority, etc.)
    - Pagination: Control page size and offset
    
    Returns paginated results with total count.
    """
    result = TaskService.list_tasks(
        db=db,
        owner_id=current_user.id,
        status=status,
        priority=priority,
        search=search,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    return result

@router.get(
    "/stats",
    response_model=TaskStatsResponse,
    summary="Get task statistics",
    description="Get task count breakdown by status"
)
async def get_task_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics about the current user's tasks.
    
    Returns counts for:
    - Total tasks
    - Tasks by status (TODO, IN_PROGRESS, COMPLETED, CANCELLED)
    """
    stats = TaskService.get_user_task_stats(db, current_user.id)
    return stats

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID",
    description="Retrieve a specific task by its ID"
)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific task.
    
    Users can only access their own tasks (unless admin).
    """
    from app.core.exceptions import ResourceNotFoundException, InsufficientPermissionsException
    
    task = TaskService.get_task_by_id(db, task_id)
    if not task:
        raise ResourceNotFoundException("Task")
    
    # Check ownership
    if task.owner_id != current_user.id and not current_user.is_admin:
        raise InsufficientPermissionsException()
    
    return task

@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update a task with optimistic locking (prevents concurrent modifications)"
)
@limiter.limit(get_user_rate_limit())
async def update_task(
    request: Request,
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing task.
    """
    # Build update dictionary (only include fields that are set)
    update_data = {}
    if task_data.title is not None:
        update_data["title"] = task_data.title
    if task_data.description is not None:
        update_data["description"] = task_data.description
    if task_data.status is not None:
        update_data["status"] = task_data.status
    if task_data.priority is not None:
        update_data["priority"] = task_data.priority
    if task_data.due_date is not None:
        update_data["due_date"] = task_data.due_date
    
    task = TaskService.update_task(
        db=db,
        task_id=task_id,
        current_user=current_user,
        version=task_data.version,
        **update_data
    )
    
    return task

@router.delete(
    "/{task_id}",
    response_model=SuccessResponse,
    summary="Delete task",
    description="Soft delete a task (can be recovered)"
)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a task (soft delete).
    """
    TaskService.delete_task(db, task_id, current_user, hard_delete=False)
    return {"message": "Task deleted successfully"}
