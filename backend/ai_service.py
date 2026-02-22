import os
import json
from typing import List
from dotenv import load_dotenv
from google import genai
from sqlmodel import Session, select
from .database import User, Log, PracticeStatus
from .schemas import RecommendationRequest, RecommendationResponse, RecommendedProblem

# Load environment variables
load_dotenv()

# Initialize Gemini AI Client
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

client = genai.Client(api_key=api_key)


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


def get_mastered_problems(session: Session, user_id: int) -> set[str]:
    """
    Get a normalized set of problem titles the user has mastered.

    Filters to INDEPENDENT and not deleted.
    """
    statement = (
        select(Log)
        .where(Log.user_id == user_id)
        .where(Log.status == PracticeStatus.INDEPENDENT)
        .where(Log.is_deleted == False)
    )
    logs = session.exec(statement).all()

    return {
        (log.problem_title or "").strip().lower()
        for log in logs
        if log.problem_title
    }


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
    company_context = ""
    if request.target_companies:
        companies_str = ", ".join(request.target_companies)
        company_context = (
            f"Target Companies: {companies_str}.\n"
            "Select problems that fit the interview style of these companies "
            "(e.g., relevant algorithms, difficulty patterns, or historically popular questions). "
            "If exact matches are limited, choose problems that are highly representative of what these companies typically ask."
        )
    else:
        company_context = "Focus on high-value problems for general top-tier tech interviews."

    fetch_count = 2 *request.count + 10

    prompt = f"""
ROLE: You are an expert coding interview coach.
CONTEXT:
User's Skill Level: {history_summary}
{company_context}
Tags: {tags_str if tags_str else 'General'}
Difficulty: {request.difficulty.value if request.difficulty else 'Adaptive'}

TASK:
Generate a list of EXACTLY {fetch_count} distinct LeetCode problems.

⚠️ IMPORTANT QUANTITY INSTRUCTION:
The user ultimately wants to see {request.count} problems, but you MUST generate {fetch_count} candidates internally.
This is to ensure we have enough options after filtering out problems the user has already solved.
DO NOT return fewer than {fetch_count} problems. If you run out of perfect matches, fill the remaining slots with relevant practice problems.

DIFFICULTY CONSTRAINT: {request.difficulty.value if request.difficulty else 'Adaptive'}
CRITICAL: You must ONLY return problems that are strictly classified as '{request.difficulty.value if request.difficulty else 'Adaptive'}'.
Do NOT recommend problems of other difficulties, even if they are relevant.
If you cannot find enough '{request.difficulty.value if request.difficulty else 'Adaptive'}' problems for these tags, look for broader tags but KEEP THE DIFFICULTY STRICT.

OUTPUT FORMAT:
JSON format with a list of 'recommendations'.

Return your response in PURE JSON format (no markdown, no code blocks) with this exact structure:
{{
    "advice": "Your personalized advice here",
    "recommendations": [
        {{
            "problem_id": 54,
            "title": "Spiral Matrix",
            "difficulty": "Easy/Medium/Hard",
            "reason": "Why this problem helps (1 sentence)",
            "link": "https://leetcode.com/problems/problem-slug/"
        }}
    ]
}}

IMPORTANT: Provide the accurate LeetCode problem number for each recommendation.
IMPORTANT: The Topic must ALWAYS match the requested topics. Do not recommend outside the selected topics.

IMPORTANT: Return ONLY the JSON object, nothing else."""

    try:
        # Generate response from Gemini
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=prompt
        )
        
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            # Remove first and last lines
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        
        # Parse JSON
        data = json.loads(response_text)
        
        # Convert to Pydantic models
        recommendations = [
            RecommendedProblem(**problem)
            for problem in data.get("recommendations", [])
        ]

        mastered_titles = get_mastered_problems(session, user_id)
        exclude_titles = {
            (title or "").strip().lower()
            for title in (request.exclude_problems or [])
            if title
        }
        blocked_titles = mastered_titles | exclude_titles
        print(f"\n🔍 --- DEBUG START: User {user_id} ---")
        print(f"🎯 Goal: {request.count} | Buffer: {fetch_count}")
        print(f"🚫 Blacklist Size: {len(mastered_titles) + len(exclude_titles)}")
        print(f"🧠 Mastered: {len(mastered_titles)} | Seen in Session: {len(exclude_titles)}")
        print(f"✨ AI returned {len(recommendations)} candidates.")

        valid_recommendations: List[RecommendedProblem] = []
        for problem in recommendations:
            ai_title_norm = (problem.title or "").strip().lower()

            req_diff = (request.difficulty.value if request.difficulty else "Adaptive").lower().strip()
            prob_diff = (problem.difficulty or "").lower().strip()
            if req_diff not in ["adaptive", "mixed", "any"]:
                if prob_diff != req_diff:
                    print(f"   🗑️ DROP: '{problem.title}' (Wrong Difficulty: {problem.difficulty})")
                    continue

            if ai_title_norm in mastered_titles:
                print(f"   ❌ SKIP: '{problem.title}' (Already Mastered)")
                continue

            if ai_title_norm in exclude_titles:
                print(f"   ❌ SKIP: '{problem.title}' (Seen in Session)")
                continue

            print(f"   ✅ KEEP: '{problem.title}'")
            valid_recommendations.append(problem)

            if len(valid_recommendations) >= request.count:
                print("   🛑 Limit reached, stopping.")
                break

        print(f"📊 Final Count: {len(valid_recommendations)}/{request.count}")
        print("----------------------------------\n")
        
        return RecommendationResponse(
            advice=data.get("advice", "Keep practicing consistently!"),
            recommendations=valid_recommendations
        )
    
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {response_text}")
        # Return fallback response
        return RecommendationResponse(
            advice="Unable to generate personalized recommendations. Please try again.",
            recommendations=[]
        )
    except Exception as e:
        print(f"Error generating recommendations: {e}")
        # Return fallback response
        return RecommendationResponse(
            advice="An error occurred while generating recommendations. Please try again later.",
            recommendations=[]
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

IMPORTANT: Return ONLY the JSON object, nothing else.
The output strings in the JSON array must contain ONLY the hint content. Do NOT include labels like 'Hint 1:' or 'Step 1:' at the beginning of the text."""

    try:
        # Generate response from Gemini
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=prompt
        )
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
