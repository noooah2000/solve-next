import streamlit as st
import requests
from datetime import datetime

# Backend API base URL
API_BASE_URL = "http://127.0.0.1:8000"

# Page configuration
st.set_page_config(
    page_title="SolveNext",
    page_icon="🎯",
    layout="wide"
)

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None


def check_backend_connection():
    """Check if backend server is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def login(username: str):
    """Login user via backend API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            params={"username": username},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            st.session_state.user_id = data["user_id"]
            st.session_state.username = data["username"]
            return True, "Login successful!"
        else:
            return False, f"Login failed: {response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


def logout():
    """Logout user"""
    st.session_state.user_id = None
    st.session_state.username = None
    st.rerun()


def create_log(username: str, problem_slug: str, status: str, note: str):
    """Create a new practice log"""
    try:
        payload = {
            "username": username,
            "problem_slug": problem_slug,
            "status": status,
            "note": note if note else None
        }
        response = requests.post(
            f"{API_BASE_URL}/logs",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return True, "Log saved successfully!"
        else:
            error_detail = response.json().get("detail", response.text)
            return False, f"Error: {error_detail}"
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


def get_user_logs(user_id: int):
    """Get user's practice history"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/users/{user_id}/logs",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return []


def get_recommendations(username: str, tags: list, difficulty: str, count: int):
    """Get AI-powered recommendations"""
    try:
        payload = {
            "username": username,
            "tags": tags,
            "difficulty": difficulty,
            "count": count
        }
        response = requests.post(
            f"{API_BASE_URL}/recommendations",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            return True, response.json()
        else:
            error_detail = response.json().get("detail", response.text)
            return False, error_detail
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"


# Main App Logic
def main():
    # Check backend connection
    if not check_backend_connection():
        st.error("⚠️ Cannot connect to backend server. Please ensure the FastAPI backend is running at http://127.0.0.1:8000")
        st.info("Run the backend with: `cd backend && uvicorn main:app --reload`")
        return
    
    # If not logged in, show login page
    if st.session_state.user_id is None:
        st.title("🎯 Welcome to SolveNext")
        st.markdown("### Your AI-Powered LeetCode Practice Companion")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("Login")
            username = st.text_input("Username", placeholder="Enter your username")
            
            if st.button("Login", type="primary", use_container_width=True):
                if username.strip():
                    success, message = login(username.strip())
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter a username")
        
        return
    
    # Logged in - Show main app
    st.title(f"🎯 SolveNext - Welcome, {st.session_state.username}!")
    
    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        
        page = st.radio(
            "Select a page:",
            ["📝 Write Diary", "📊 History", "🤖 AI Coach"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.write(f"**User:** {st.session_state.username}")
        st.write(f"**User ID:** {st.session_state.user_id}")
        
        if st.button("Logout", type="secondary", use_container_width=True):
            logout()
    
    # Page routing
    if page == "📝 Write Diary":
        show_write_diary()
    elif page == "📊 History":
        show_history()
    elif page == "🤖 AI Coach":
        show_ai_coach()


def show_write_diary():
    """Write Diary page"""
    st.header("📝 New Practice Log")
    st.markdown("Record your LeetCode practice session")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        problem_slug = st.text_input(
            "Problem Slug",
            placeholder="e.g., two-sum, best-time-to-buy-and-sell-stock",
            help="The URL slug from LeetCode problem URL"
        )
    
    with col2:
        status = st.selectbox(
            "Status",
            ["INDEPENDENT", "WITH_HINT", "STUCK"],
            help="How did you solve this problem?"
        )
    
    note = st.text_area(
        "Notes (Optional)",
        placeholder="Add any notes about your practice session, challenges faced, or insights gained...",
        height=150
    )
    
    if st.button("Save Log", type="primary", use_container_width=True):
        if problem_slug.strip():
            with st.spinner("Saving log..."):
                success, message = create_log(
                    st.session_state.username,
                    problem_slug.strip(),
                    status,
                    note.strip()
                )
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
        else:
            st.warning("Please enter a problem slug")


def show_history():
    """History page"""
    st.header("📊 Practice History")
    
    with st.spinner("Loading your practice history..."):
        logs = get_user_logs(st.session_state.user_id)
    
    if not logs:
        st.info("No practice logs found. Start logging your practice sessions!")
        return
    
    st.success(f"Found {len(logs)} practice logs")
    
    # Display logs
    for log in logs:
        # Difficulty color coding
        diff_color = {
            "Easy": "🟢",
            "Medium": "🟡",
            "Hard": "🔴"
        }.get(log["difficulty"], "⚪")
        
        # Status emoji
        status_emoji = {
            "INDEPENDENT": "✅",
            "WITH_HINT": "💡",
            "STUCK": "❌"
        }.get(log["status"], "📝")
        
        with st.expander(
            f"{diff_color} {log['problem_title']} - Attempt #{log['attempt_count']} {status_emoji}",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Difficulty", log["difficulty"])
            with col2:
                st.metric("Status", log["status"])
            with col3:
                practice_date = datetime.fromisoformat(log["practice_date"].replace("Z", "+00:00"))
                st.metric("Date", practice_date.strftime("%Y-%m-%d"))
            
            st.write(f"**Problem ID:** {log['problem_id']}")
            st.write(f"**Tags:** {log['tags']}")
            
            if log.get("note"):
                st.markdown("**Notes:**")
                st.info(log["note"])


def show_ai_coach():
    """AI Coach page"""
    st.header("🤖 AI Problem Recommender")
    st.markdown("Get personalized problem recommendations based on your practice history")
    
    # Topic tags matching backend enum
    available_tags = [
        "Array", "String", "Hash Table", "Dynamic Programming", "Math",
        "Sorting", "Greedy", "Depth-First Search", "Breadth-First Search",
        "Binary Search", "Tree", "Graph", "Backtracking", "Linked List",
        "Stack", "Queue", "Heap", "Trie", "Sliding Window", "Two Pointers"
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_tags = st.multiselect(
            "Topic Tags",
            available_tags,
            default=["Array"],
            help="Select topics you want to practice"
        )
    
    with col2:
        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"],
            index=1,
            help="Select problem difficulty"
        )
    
    count = st.number_input(
        "Number of Problems",
        min_value=1,
        max_value=10,
        value=3,
        help="How many problems do you want?"
    )
    
    if st.button("Get Advice", type="primary", use_container_width=True):
        if not selected_tags:
            st.warning("Please select at least one topic tag")
            return
        
        with st.spinner("AI is analyzing your practice history and generating recommendations..."):
            success, result = get_recommendations(
                st.session_state.username,
                selected_tags,
                difficulty,
                count
            )
        
        if success:
            # Display advice
            st.markdown("### 💡 Personalized Advice")
            st.info(result["advice"])
            
            # Display recommended problems
            st.markdown("### 📚 Recommended Problems")
            
            if result["problems"]:
                for idx, problem in enumerate(result["problems"], 1):
                    with st.container():
                        st.markdown(f"#### {idx}. {problem['problem_title']}")
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Reason:** {problem['reason']}")
                            st.write(f"**Difficulty:** {problem['difficulty']}")
                        with col2:
                            st.link_button(
                                "Solve on LeetCode →",
                                problem['leetcode_url'],
                                use_container_width=True
                            )
                        
                        st.markdown("---")
            else:
                st.warning("No problems recommended. Try adjusting your filters.")
        else:
            st.error(f"Failed to get recommendations: {result}")


if __name__ == "__main__":
    main()