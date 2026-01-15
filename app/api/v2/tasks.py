from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.schemas.task import TaskResponse, TaskList
from app.services.task_service import TaskService
from app.dependencies import get_current_active_user
from app.models.user import User
from app.models.task import TaskStatus, TaskPriority
from app.core.rate_limiter import limiter, get_user_rate_limit

router = APIRouter()

@router.get(
    "/",
    response_model=TaskList,
    summary="List tasks (V2 - Enhanced)",
    description="Enhanced version with additional query capabilities"
)
@limiter.limit(get_user_rate_limit())
async def list_tasks_v2(
    request: Request,
    status: Optional[List[TaskStatus]] = Query(None, description="Filter by multiple statuses"),
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
    **V2 Enhancement**: This version supports filtering by multiple statuses.
    
    Example: /api/v2/tasks?status=TODO&status=IN_PROGRESS
    
    This demonstrates API evolution while maintaining v1 compatibility.
    """
    # V2 feature: If multiple statuses provided, we fetch all and filter in memory
    
    if status and len(status) > 1:
        # Fetch all tasks and filter by multiple statuses
        all_results = TaskService.list_tasks(
            db=db,
            owner_id=current_user.id,
            status=None,  # Don't filter by status in service
            priority=priority,
            search=search,
            skip=skip,
            limit=limit * len(status),  # Get more to account for filtering
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Filter by multiple statuses
        filtered_items = [
            task for task in all_results["items"] 
            if task.status in status
        ]
        
        return {
            "items": filtered_items[:limit],
            "total": len(filtered_items),
            "page": all_results["page"],
            "pages": (len(filtered_items) + limit - 1) // limit if limit > 0 else 1
        }
    else:
        # Single status or no status - use v1 logic
        single_status = status[0] if status and len(status) > 0 else None
        return TaskService.list_tasks(
            db=db,
            owner_id=current_user.id,
            status=single_status,
            priority=priority,
            search=search,
            skip=skip,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order
        )

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task by ID (V2)",
    description="Get task with same functionality as V1"
)
async def get_task_v2(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    V2 version of get task - maintains compatibility with V1.
    Future enhancements could include additional fields in response.
    """
    from app.core.exceptions import ResourceNotFoundException, InsufficientPermissionsException
    
    task = TaskService.get_task_by_id(db, task_id)
    if not task:
        raise ResourceNotFoundException("Task")
    
    # Check ownership
    if task.owner_id != current_user.id and not current_user.is_admin:
        raise InsufficientPermissionsException()
    
    return task
