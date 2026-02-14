"""
Authentication router for user signup and login.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..database import get_session, User


router = APIRouter()


@router.post("/auth/signup")
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


@router.post("/auth/login")
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
