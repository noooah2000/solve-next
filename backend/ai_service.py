import os
import json
from typing import List
from dotenv import load_dotenv
import google.generativeai as genai
from sqlmodel import Session, select
from .database import User, Log, PracticeStatus
from .schemas import RecommendationRequest, RecommendationResponse, RecommendedProblem

# Load environment variables
load_dotenv()

# Initialize Gemini AI
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-flash-latest')


def get_user_history_summary(session: Session, user_id: int) -> str:
    """
    Get a summary of the user's practice history.
    
    Args:
        session: Database session
        user_id: User ID
    
    Returns:
        String summary of recent practice logs, focusing on struggles
    """
    # Query the last 20 logs for the user
    statement = (
        select(Log)
        .where(Log.user_id == user_id)
        .order_by(Log.practice_date.desc())
        .limit(20)
    )
    logs = session.exec(statement).all()
    
    if not logs:
        return "No practice history available."
    
    # Focus on problematic logs (WITH_HINT or STUCK)
    struggled_logs = [
        log for log in logs 
        if log.status != PracticeStatus.INDEPENDENT
    ]
    
    summary_parts = []
    summary_parts.append(f"Total recent attempts: {len(logs)}")
    summary_parts.append(f"Problems with difficulty: {len(struggled_logs)}")
    
    if struggled_logs:
        summary_parts.append("\nStruggled with:")
        for log in struggled_logs[:10]:  # Top 10 struggles
            status_label = "Needed hints" if log.status == PracticeStatus.WITH_HINT else "Got stuck"
            summary_parts.append(
                f"- {log.problem_title} ({log.difficulty}) [{log.tags}] - {status_label}"
            )
            if log.note:
                summary_parts.append(f"  Note: {log.note}")
    
    # Add topics that appear frequently in struggles
    if struggled_logs:
        all_tags = []
        for log in struggled_logs:
            all_tags.extend([tag.strip() for tag in log.tags.split(",")])
        
        from collections import Counter
        tag_counts = Counter(all_tags)
        if tag_counts:
            summary_parts.append("\nMost challenging topics:")
            for tag, count in tag_counts.most_common(5):
                summary_parts.append(f"- {tag}: {count} times")
    
    return "\n".join(summary_parts)


def generate_recommendations(
    session: Session, 
    request: RecommendationRequest, 
    user_id: int
) -> RecommendationResponse:
    """
    Generate AI-powered problem recommendations based on user history.
    
    Args:
        session: Database session
        request: Recommendation request with tags, difficulty, and count
        user_id: User ID
    
    Returns:
        RecommendationResponse with advice and recommended problems
    """
    # Get user history summary
    history_summary = get_user_history_summary(session, user_id)
    
    # Convert tags to string list
    tags_str = ", ".join([tag.value for tag in request.tags])
    
    # Construct the AI prompt
    curriculum_instruction = ""
    if request.source_list == "Blind 75":
        curriculum_instruction = "\nStrictly recommend problems ONLY from the famous 'Blind 75' list."
    elif request.source_list == "NeetCode 150":
        curriculum_instruction = "\nStrictly recommend problems ONLY from the 'NeetCode 150' list."

    company_instruction = ""
    if request.target_companies:
        companies_str = ", ".join(request.target_companies)
        company_instruction = (
            f"\nPrioritize problems that are frequently asked in interviews at the following companies: {companies_str}. "
            "Use your internal knowledge of company question banks."
        )

    prompt = f"""You are an expert LeetCode coach. Based on the user's practice history, recommend {request.count} LeetCode problems.
{f"You are a specialized coach helping the user complete the {request.source_list} challenge." if request.source_list and request.source_list != "All Problems" else ""}

User Practice History:
{history_summary}

Requested Topics: {tags_str}
Requested Difficulty: {request.difficulty.value}
{curriculum_instruction}
{company_instruction}

Please provide:
1. Personalized advice (2-3 sentences) based on their struggle patterns
2. {request.count} recommended LeetCode problems that:
   - Match the requested difficulty and topics
   - Help strengthen their weak areas
   - Are varied and build upon each other

Return your response in PURE JSON format (no markdown, no code blocks) with this exact structure:
{{
    "advice": "Your personalized advice here",
    "problems": [
        {{
            "problem_title": "Problem name",
            "difficulty": "Easy/Medium/Hard",
            "reason": "Why this problem helps (1 sentence)",
            "leetcode_url": "https://leetcode.com/problems/problem-slug/"
        }}
    ]
}}

IMPORTANT: Return ONLY the JSON object, nothing else."""

    try:
        # Generate response from Gemini
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            # Remove first and last lines
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        
        # Parse JSON
        data = json.loads(response_text)
        
        # Convert to Pydantic models
        problems = [
            RecommendedProblem(**problem) 
            for problem in data.get("problems", [])
        ]
        
        return RecommendationResponse(
            advice=data.get("advice", "Keep practicing consistently!"),
            problems=problems
        )
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {response_text}")
        # Return fallback response
        return RecommendationResponse(
            advice="Unable to generate personalized recommendations. Please try again.",
            problems=[]
        )
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        # Return fallback response
        return RecommendationResponse(
            advice="An error occurred while generating recommendations. Please try again later.",
            problems=[]
        )

def get_problem_hints(problem_title: str) -> dict:
    """
    Generate 3 progressive hints for a LeetCode problem.
    
    Args:
        problem_title: Title of the LeetCode problem
    
    Returns:
        Dictionary with list of 3 hints
    """
    prompt = f"""You are an expert LeetCode coach. Provide 3 progressive hints for solving this LeetCode problem: "{problem_title}"

The hints should be:
1. Hint 1: High-level conceptual approach (no code, just the general strategy)
2. Hint 2: Specific data structure or algorithm to use
3. Hint 3: Key logic step or pseudo-code guidance

Return your response in PURE JSON format (no markdown, no code blocks) with this exact structure:
{{
    "hints": [
        "Hint 1: [conceptual approach]",
        "Hint 2: [data structure/algorithm]",
        "Hint 3: [key logic step]"
    ]
}}

IMPORTANT: Return ONLY the JSON object, nothing else."""

    try:
        # Generate response from Gemini
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        
        # Parse JSON
        data = json.loads(response_text)
        
        return {
            "hints": data.get("hints", [
                "Try breaking down the problem into smaller steps.",
                "Consider what data structure would help you track information efficiently.",
                "Think about the time complexity of your approach."
            ])
        }
    
    except Exception as e:
        print(f"Error generating hints: {e}")
        # Return fallback hints
        return {
            "hints": [
                "Start by understanding the input and output requirements clearly.",
                "Think about which data structure (array, hash map, stack, etc.) fits this problem.",
                "Consider edge cases and how your solution handles them."
            ]
        }
