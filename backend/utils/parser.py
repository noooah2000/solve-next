"""
Utility functions for parsing user input.
"""
from fastapi import HTTPException
from .. import scraper


def parse_problem_input(user_input: str) -> str:
    """
    Parse problem input and extract the slug.
    
    Handles three cases:
    1. Full LeetCode URL: https://leetcode.com/problems/two-sum/ → two-sum
    2. Numeric ID: 1 → converts to slug via scraper
    3. Invalid input → raises HTTPException
    
    Args:
        user_input: Raw user input (URL or ID)
    
    Returns:
        Extracted slug
        
    Raises:
        HTTPException: 400 for invalid format, 404 if problem not found
    """
    problem_input = user_input.strip()
    
    if not problem_input:
        raise HTTPException(status_code=400, detail="problem_input is required")
    
    # Case 1: Full LeetCode URL
    if "leetcode.com/problems/" in problem_input.lower():
        try:
            start_idx = problem_input.lower().index("leetcode.com/problems/") + len("leetcode.com/problems/")
            remaining = problem_input[start_idx:]
            end_idx = remaining.find("/")
            if end_idx != -1:
                slug = remaining[:end_idx].strip()
            else:
                slug = remaining.strip()
            return slug
        except (ValueError, IndexError):
            raise HTTPException(status_code=400, detail="Invalid LeetCode URL format")
    
    # Case 2: Numeric ID
    elif problem_input.isdigit():
        slug = scraper.get_slug_from_id(problem_input)
        if not slug:
            raise HTTPException(
                status_code=404, 
                detail=f"Problem ID '{problem_input}' not found on LeetCode"
            )
        return slug
    
    # Case 3: Invalid format
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid format. Please enter a numeric ID (e.g., 1) or full LeetCode URL."
        )
