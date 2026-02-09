from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select, delete
from .database import (
    create_db_and_tables,
    get_session,
    User,
    Log,
    PracticeStatus
)
from .schemas import (
    CreateLogRequest,
    UpdateLogRequest,
    LogResponse,
    RecommendationRequest,
    RecommendationResponse
)
from . import scraper, ai_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup logic
    create_db_and_tables()
    yield
    # Shutdown logic (pass for now)


# Initialize FastAPI app
app = FastAPI(title="SolveNext API", lifespan=lifespan)


@app.get("/")
def read_root():
    """Root endpoint - welcome message"""
    return {
        "message": "Welcome to SolveNext API",
        "version": "1.0.0",
        "endpoints": {
            "signup": "POST /auth/signup",
            "login": "POST /auth/login",
            "create_log": "POST /logs",
            "get_user_logs": "GET /users/{user_id}/logs",
            "update_log": "PATCH /logs/{log_id}",
            "delete_log": "DELETE /logs/{log_id}",
            "get_trash": "GET /users/{user_id}/logs/trash",
            "restore_log": "POST /logs/{log_id}/restore",
            "empty_trash": "DELETE /users/{user_id}/logs/trash/empty",
            "get_recommendations": "POST /recommendations"
        }
    }


@app.post("/auth/signup")
def signup(username: str, session: Session = Depends(get_session)):
    """
    Create a new user account.
    
    Args:
        username: Username for the new account
        session: Database session
    
    Returns:
        Dictionary with user_id and username
    
    Raises:
        HTTPException: 400 if user already exists
    """
    # Check if user already exists
    statement = select(User).where(User.username == username)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail=f"User '{username}' already exists"
        )
    
    # Create new user
    user = User(username=username)
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return {
        "user_id": user.id,
        "username": user.username
    }


@app.post("/auth/login")
def login(username: str, session: Session = Depends(get_session)):
    """
    Login an existing user.
    
    Args:
        username: Username to login
        session: Database session
    
    Returns:
        Dictionary with user_id and username
    
    Raises:
        HTTPException: 404 if user not found
    """
    # Check if user exists
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User '{username}' not found"
        )
    
    return {
        "user_id": user.id,
        "username": user.username
    }


@app.post("/logs", response_model=LogResponse)
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
    problem_info = scraper.get_problem_info(request.problem_slug)
    
    if not problem_info:
        raise HTTPException(
            status_code=404,
            detail=f"Problem '{request.problem_slug}' not found on LeetCode"
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


@app.get("/users/{user_id}/logs", response_model=List[LogResponse])
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


@app.patch("/logs/{log_id}", response_model=LogResponse)
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


@app.delete("/logs/{log_id}")
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


@app.get("/users/{user_id}/logs/trash", response_model=List[LogResponse])
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


@app.post("/logs/{log_id}/restore")
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


@app.delete("/users/{user_id}/logs/trash/empty")
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


@app.post("/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    request: RecommendationRequest,
    session: Session = Depends(get_session)
):
    """
    Get AI-powered problem recommendations based on user history.
    
    Args:
        request: RecommendationRequest with username, tags, difficulty, count
        session: Database session
    
    Returns:
        RecommendationResponse with advice and recommended problems
    """
    # Find user by username
    statement = select(User).where(User.username == request.username)
    user = session.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"User '{request.username}' not found"
        )
    
    # Generate recommendations using AI service
    recommendations = ai_service.generate_recommendations(
        session=session,
        request=request,
        user_id=user.id
    )
    
    return recommendations

@app.post("/recommendations/hints")
def get_problem_hints(
    request: dict,
    session: Session = Depends(get_session)
):
    """
    Get AI-generated hints for a specific LeetCode problem.
    
    Args:
        request: Dictionary with problem_title
        session: Database session
    
    Returns:
        Dictionary with list of 3 progressive hints
    """
    problem_title = request.get("problem_title")
    
    if not problem_title:
        raise HTTPException(
            status_code=400,
            detail="problem_title is required"
        )
    
    # Generate hints using AI service
    hints = ai_service.get_problem_hints(problem_title)
    
    return hints
