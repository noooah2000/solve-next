import requests
from typing import Optional, Dict


def get_problem_info(title_slug: str) -> Optional[Dict[str, str]]:
    """
    Fetch problem information from LeetCode GraphQL API.
    
    Args:
        title_slug: The URL slug of the LeetCode problem (e.g., "two-sum")
    
    Returns:
        Dictionary with problem_id, title, difficulty, and tags (comma-separated)
        Returns None if the request fails
    """
    url = "https://leetcode.com/graphql"
    
    # GraphQL query to fetch problem details
    query = """
    query getProblemInfo($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionFrontendId
            title
            difficulty
            topicTags {
                name
            }
        }
    }
    """
    
    # Request payload
    payload = {
        "query": query,
        "variables": {"titleSlug": title_slug}
    }
    
    # Headers to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com/"
    }
    
    try:
        # Make the POST request
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the response
        data = response.json()
        question = data.get("data", {}).get("question", {})
        
        if not question:
            print(f"Problem not found: {title_slug}")
            return None
        
        # Extract tags and join them as comma-separated string
        topic_tags = question.get("topicTags", [])
        tags_str = ", ".join([tag["name"] for tag in topic_tags])
        
        # Return the structured data
        return {
            "problem_id": question.get("questionFrontendId", ""),
            "title": question.get("title", ""),
            "difficulty": question.get("difficulty", ""),
            "tags": tags_str
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching problem info for '{title_slug}': {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Error parsing response for '{title_slug}': {e}")
        return None


def get_slug_from_id(problem_id: str) -> Optional[str]:
    """
    Fetch the title slug from a LeetCode problem ID using the GraphQL API.

    Args:
        problem_id: Frontend question ID as string (e.g., "1", "54")

    Returns:
        The titleSlug if found, otherwise None
    """
    url = "https://leetcode.com/graphql"

    query = """
    query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList: questionList(
        categorySlug: $categorySlug
        limit: $limit
        skip: $skip
        filters: $filters
      ) {
        data {
          titleSlug
          questionFrontendId
        }
      }
    }
    """

    variables = {
        "categorySlug": "",
        "limit": 1,
        "skip": 0,
        "filters": {
            "searchKeywords": str(problem_id)
        }
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://leetcode.com/"
    }

    try:
        response = requests.post(
            url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        items = data.get("data", {}).get("problemsetQuestionList", {}).get("data", [])
        for item in items:
            if item.get("questionFrontendId") == str(problem_id):
                return item.get("titleSlug")

        print(f"Problem ID not found: {problem_id}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching slug for problem ID '{problem_id}': {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Error parsing response for problem ID '{problem_id}': {e}")
        return None