"""
Users router for fetching user-specific logs and trash management.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, delete
from ..database import get_session, Log
from ..schemas import LogResponse


router = APIRouter()


@router.get("/users/{user_id}/logs", response_model=List[LogResponse])
def get_user_logs(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Get all active (non-deleted) logs for a specific user.
    
    Args:
        user_id: User ID
        session: Database session
    
    Returns:
        List of active log entries ordered by practice_date descending
    """
    # Query all active logs for the user (is_deleted == False)
    statement = (
        select(Log)
        .where(Log.user_id == user_id, Log.is_deleted == False)
        .order_by(Log.practice_date.desc())
    )
    logs = session.exec(statement).all()
    
    return logs


@router.get("/users/{user_id}/logs/trash", response_model=List[LogResponse])
def get_trash_logs(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Get all soft-deleted (trashed) logs for a specific user.
    
    Args:
        user_id: User ID
        session: Database session
    
    Returns:
        List of deleted log entries ordered by practice_date descending
    """
    # Query all deleted logs for the user (is_deleted == True)
    statement = (
        select(Log)
        .where(Log.user_id == user_id, Log.is_deleted == True)
        .order_by(Log.practice_date.desc())
    )
    logs = session.exec(statement).all()
    
    return logs


@router.delete("/users/{user_id}/logs/trash/empty")
def empty_trash(
    user_id: int,
    session: Session = Depends(get_session)
):
    """
    Permanently delete all soft-deleted logs for a specific user.
    
    Args:
        user_id: User ID
        session: Database session
    
    Returns:
        Success confirmation with count of deleted logs
    """
    # Count how many logs will be deleted
    count_statement = select(Log).where(Log.user_id == user_id, Log.is_deleted == True)
    logs_to_delete = session.exec(count_statement).all()
    count = len(logs_to_delete)
    
    # Permanently delete all soft-deleted logs for this user
    delete_statement = delete(Log).where(Log.user_id == user_id, Log.is_deleted == True)
    session.exec(delete_statement)
    session.commit()
    
    return {"ok": True, "message": f"Trash emptied: {count} log(s) permanently deleted"}
