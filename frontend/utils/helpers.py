def extract_slug_from_input(user_input: str) -> str:
    """
    Extract problem slug from user input.

    Handles three cases:
    1. Full LeetCode URL: https://leetcode.com/problems/two-sum/description/ → two-sum
    2. Slug only: two-sum → two-sum
    3. Numeric ID: 2911 → 2911 (warning shown)

    Args:
        user_input: Raw user input (URL or slug)

    Returns:
        Extracted slug or original input
    """
    user_input = user_input.strip()

    # Check if it's a LeetCode URL
    if "leetcode.com/problems/" in user_input.lower():
        # Extract slug between /problems/ and the next /
        try:
            start_idx = user_input.lower().index("leetcode.com/problems/") + len("leetcode.com/problems/")
            remaining = user_input[start_idx:]
            # Get everything up to the next / or end of string
            end_idx = remaining.find("/")
            if end_idx != -1:
                slug = remaining[:end_idx]
            else:
                slug = remaining
            return slug.strip()
        except (ValueError, IndexError):
            return user_input

    # Check if input is purely numeric (problem ID)
    if user_input.isdigit():
        return user_input

    # Otherwise treat as slug
    return user_input


def extract_slug_from_url(url: str) -> str:
    """
    Extract problem slug from a LeetCode URL.

    Args:
        url: Full LeetCode problem URL

    Returns:
        Extracted slug or empty string if not found
    """
    url = url.strip()
    if "leetcode.com/problems/" not in url.lower():
        return ""
    try:
        start_idx = url.lower().index("leetcode.com/problems/") + len("leetcode.com/problems/")
        remaining = url[start_idx:]
        end_idx = remaining.find("/")
        if end_idx != -1:
            return remaining[:end_idx].strip()
        return remaining.strip()
    except (ValueError, IndexError):
        return ""
