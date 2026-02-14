"""
Logs router for creating, updating, and managing practice logs.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..database import get_session, User, Log
from ..schemas import CreateLogRequest, UpdateLogRequest, LogResponse
from .. import scraper


router = APIRouter()


@router.post("/logs", response_model=LogResponse)
def create_log(
    request: CreateLogRequest,
    session: Session = Depends(get_session)
):
    """
    Create a new practice log entry.
    
    Args:
        request: CreateLogRequest with username, problem_slug, status, note
        session: Database session
    
    Returns:
        Created log entry
    """
    # Find user by username
    statement = select(User).where(User.username == request.username)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User '{request.username}' not found"
        )
    
    # Get problem info from LeetCode
    problem_slug = request.problem_slug
    if problem_slug.isdigit():
        slug_from_id = scraper.get_slug_from_id(problem_slug)
        if not slug_from_id:
            raise HTTPException(
                status_code=404,
                detail=f"Problem ID '{problem_slug}' not found on LeetCode"
            )
        problem_slug = slug_from_id

    problem_info = scraper.get_problem_info(problem_slug)
    
    if not problem_info:
        raise HTTPException(
            status_code=404,
            detail=f"Problem '{problem_slug}' not found on LeetCode"
        )
    
    # Calculate attempt_count: count existing logs for this user and problem
    statement = select(Log).where(
        Log.user_id == user.id,
        Log.problem_id == problem_info["problem_id"]
    )
    existing_logs = session.exec(statement).all()
    attempt_count = len(existing_logs) + 1
    
    # Create new log entry
    new_log = Log(
        user_id=user.id,
        problem_id=problem_info["problem_id"],
        problem_title=problem_info["title"],
        difficulty=problem_info["difficulty"],
        tags=problem_info["tags"],
        attempt_count=attempt_count,
        status=request.status,
        note=request.note
    )
    
    # Save to database
    session.add(new_log)
    session.commit()
    session.refresh(new_log)
    
    return new_log


@router.patch("/logs/{log_id}", response_model=LogResponse)
def update_log(
    log_id: int,
    request: UpdateLogRequest,
    session: Session = Depends(get_session)
):
    """
    Update a specific practice log entry (partial update).
    
    Args:
        log_id: ID of the log to update
        request: UpdateLogRequest with optional fields to update
        session: Database session
    
    Returns:
        Updated log entry
    
    Raises:
        HTTPException: 404 if log not found
    """
    # Find the log by ID
    log = session.get(Log, log_id)
    
    if not log:
        raise HTTPException(
            status_code=404,
            detail=f"Log with ID {log_id} not found"
        )
    
    # Update only provided fields
    if request.status is not None:
        log.status = request.status
    if request.note is not None:
        log.note = request.note
    if request.practice_date is not None:
        log.practice_date = request.practice_date
    
    # Save changes
    session.add(log)
    session.commit()
    session.refresh(log)
    
    return log


@router.delete("/logs/{log_id}")
def delete_log(
    log_id: int,
    session: Session = Depends(get_session)
):
    """
    Soft delete a specific practice log entry.
    
    Args:
        log_id: ID of the log to delete
        session: Database session
    
    Returns:
        Success confirmation
    
    Raises:
        HTTPException: 404 if log not found
    """
    # Find the log by ID
    log = session.get(Log, log_id)
    
    if not log:
        raise HTTPException(
            status_code=404,
            detail=f"Log with ID {log_id} not found"
        )
    
    # Soft delete: set is_deleted flag to True
    log.is_deleted = True
    session.add(log)
    session.commit()
    
    return {"ok": True, "message": "Log moved to trash"}


@router.post("/logs/{log_id}/restore")
def restore_log(
    log_id: int,
    session: Session = Depends(get_session)
):
    """
    Restore a soft-deleted log entry.
    
    Args:
        log_id: ID of the log to restore
        session: Database session
    
    Returns:
        Success confirmation
    
    Raises:
        HTTPException: 404 if log not found
    """
    # Find the log by ID (including deleted ones)
    log = session.get(Log, log_id)
    
    if not log:
        raise HTTPException(
            status_code=404,
            detail=f"Log with ID {log_id} not found"
        )
    
    # Restore: set is_deleted flag to False
    log.is_deleted = False
    session.add(log)
    session.commit()
    
    return {"ok": True, "message": "Log restored successfully"}
