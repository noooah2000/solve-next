"""
AI router for recommendations and hints generation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..database import get_session, User
from ..schemas import RecommendationRequest, RecommendationResponse
from .. import ai_service


router = APIRouter()


@router.post("/recommendations", response_model=RecommendationResponse)
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


@router.post("/recommendations/hints")
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
