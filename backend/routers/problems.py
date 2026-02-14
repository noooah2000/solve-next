"""
Problems router for problem preview functionality.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..utils.parser import parse_problem_input
from .. import scraper


router = APIRouter()


class ProblemPreviewRequest(BaseModel):
    problem_input: str


@router.post("/problems/preview")
def preview_problem(request: ProblemPreviewRequest):
    """
    Preview problem details (title, difficulty) for a slug or ID.
    Accepts raw input and parses it internally using parse_problem_input.
    
    Args:
        request: ProblemPreviewRequest with raw problem_input
    
    Returns:
        Dictionary with slug, title, difficulty, problem_id
        
    Raises:
        HTTPException: 400 for invalid format, 404 if problem not found
    """
    # Parse input to extract slug (handles URLs and IDs)
    slug = parse_problem_input(request.problem_input)

    # Fetch problem info from LeetCode
    problem_info = scraper.get_problem_info(slug)
    if not problem_info:
        raise HTTPException(
            status_code=404, 
            detail=f"Problem '{slug}' not found on LeetCode"
        )

    return {
        "slug": slug,
        "title": problem_info.get("title", ""),
        "difficulty": problem_info.get("difficulty", ""),
        "problem_id": problem_info.get("problem_id", "")
    }
