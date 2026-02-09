import streamlit as st
from datetime import datetime
from api_client import (
    check_backend_connection,
    signup,
    login,
    create_log,
    get_user_logs,
    delete_log,
    get_trash_logs,
    restore_log,
    empty_trash,
    update_log,
    get_recommendations
)

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


def logout():
    """Logout user"""
    st.session_state.user_id = None
    st.session_state.username = None
    st.rerun()


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


# Dialog for editing logs
@st.dialog("✏️ Edit Log")
def edit_log_dialog(log: dict):
    """Dialog to edit a log entry"""
    with st.form("edit_log_form"):
        st.write(f"**Problem:** {log['problem_title']}")
        st.caption(f"Difficulty: {log.get('difficulty', 'Unknown')}")
        
        # Parse current date from ISO string
        current_date_str = log.get("practice_date", "")
        try:
            current_datetime = datetime.fromisoformat(current_date_str.replace("Z", "+00:00"))
            current_date = current_datetime.date()
        except:
            current_date = datetime.now().date()
        
        # Date picker
        practice_date = st.date_input(
            "Date",
            value=current_date,
            help="When did you practice this problem?"
        )
        
        # Status selectbox
        current_status = log.get("status", "INDEPENDENT")
        status = st.selectbox(
            "Status",
            ["INDEPENDENT", "WITH_HINT", "STUCK"],
            index=["INDEPENDENT", "WITH_HINT", "STUCK"].index(current_status),
            help="How did you solve this problem?"
        )
        
        # Note textarea
        note = st.text_area(
            "Notes (Optional)",
            value=log.get("note", ""),
            placeholder="Add any notes about this attempt...",
            height=120
        )
        
        # Submit button
        if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
            # Convert date to ISO 8601 datetime string
            practice_datetime = datetime.combine(practice_date, datetime.min.time())
            practice_datetime_str = practice_datetime.isoformat() + "Z"
            
            success, message = update_log(
                log['id'],
                status,
                practice_datetime_str,
                note
            )
            if success:
                st.toast("Log updated successfully!", icon="✅")
                st.rerun()
            else:
                st.error(message)


# Main App Logic
def main():
    # Check backend connection
    if not check_backend_connection():
        st.error("⚠️ Cannot connect to backend server. Please ensure the FastAPI backend is running at http://127.0.0.1:8000")
        st.info("Run the backend with: `cd backend && uvicorn main:app --reload`")
        return
    
    # If not logged in, show login/signup page
    if st.session_state.user_id is None:
        st.title("🎯 Welcome to SolveNext")
        st.markdown("### Your AI-Powered LeetCode Practice Companion")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Toggle between Login and Sign Up
            auth_mode = st.radio(
                "Choose an option:",
                ["Login", "Sign Up"],
                horizontal=True
            )
            
            username = st.text_input("Username", placeholder="Enter your username")
            
            if auth_mode == "Login":
                if st.button("Login", type="primary", use_container_width=True):
                    if username.strip():
                        success, user_data, message = login(username.strip())
                        if success:
                            st.session_state.user_id = user_data["user_id"]
                            st.session_state.username = user_data["username"]
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Please enter a username")
            
            else:  # Sign Up
                if st.button("Create Account", type="primary", use_container_width=True):
                    if username.strip():
                        success, user_data, message = signup(username.strip())
                        if success:
                            st.success(message)
                            # Auto-login after successful signup
                            st.session_state.user_id = user_data["user_id"]
                            st.session_state.username = user_data["username"]
                            st.success("You are now logged in!")
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
            ["📝 Write Diary", "📊 History", "🗑️ Trash Bin", "🤖 AI Coach"],
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
    elif page == "🗑️ Trash Bin":
        show_trash_bin()
    elif page == "🤖 AI Coach":
        show_ai_coach()


def show_write_diary():
    """Write Diary page"""
    st.header("📝 New Practice Log")
    st.markdown("Record your LeetCode practice session")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        problem_input = st.text_input(
            "Problem Link",
            placeholder="e.g., https://leetcode.com/problems/two-sum/",
            help="Paste the full URL of the LeetCode problem"
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
        if problem_input.strip():
            # Extract slug from input
            slug = extract_slug_from_input(problem_input)
            st.caption(f"🔍 Detected Slug: `{slug}`")
            
            with st.spinner("Saving log..."):
                success, message = create_log(
                    st.session_state.username,
                    slug,
                    status,
                    note.strip()
                )
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)
        else:
            st.warning("Please enter a problem link or slug")


def show_history():
    """History page"""
    st.header("📊 Practice History")
    
    with st.spinner("Loading your practice history..."):
        logs = get_user_logs(st.session_state.user_id)
    
    if not logs:
        st.info("No practice logs found. Start logging your practice sessions!")
        return
    
    st.success(f"Found {len(logs)} practice logs across {len(set(log['problem_id'] for log in logs))} unique problems")
    
    # Group logs by problem_id
    from collections import defaultdict
    grouped_logs = defaultdict(list)
    
    for log in logs:
        grouped_logs[log['problem_id']].append(log)
    
    # Display grouped logs
    for problem_id, problem_logs in grouped_logs.items():
        # Sort attempts by date (newest first)
        problem_logs_sorted = sorted(
            problem_logs, 
            key=lambda x: datetime.fromisoformat(x["practice_date"].replace("Z", "+00:00")),
            reverse=True
        )
        
        # Get problem info from the first log
        first_log = problem_logs_sorted[0]
        
        # Difficulty color coding
        diff_color = {
            "Easy": "🟢",
            "Medium": "🟡",
            "Hard": "🔴"
        }.get(first_log["difficulty"], "⚪")
        
        # Calculate summary stats
        total_attempts = len(problem_logs_sorted)
        
        # Main expander title with summary
        with st.expander(
            f"{diff_color} {first_log['problem_id']}. **{first_log['problem_title']}**",
            expanded=False
        ):
            # Summary section
            col1, col2, col3 = st.columns([1, 1, 3])
            
            with col1:
                st.metric("Total Attempts", total_attempts)
            with col2:
                st.metric("Difficulty", first_log["difficulty"])
            
            st.write(f"**Tags:** {first_log['tags']}")
            
            st.markdown("---")
            st.markdown("### 📜 Attempt History")
            
            # Display each attempt
            for idx, log in enumerate(problem_logs_sorted, 1):
                # Status emoji
                status_emoji = {
                    "INDEPENDENT": "✅",
                    "WITH_HINT": "💡",
                    "STUCK": "❌"
                }.get(log["status"], "📝")
                
                practice_date = datetime.fromisoformat(log["practice_date"].replace("Z", "+00:00"))
                
                # Attempt details with edit and delete buttons
                attempt_header_col1, attempt_header_col2, attempt_header_col3 = st.columns([4, 1, 1])
                with attempt_header_col1:
                    st.markdown(f"**Attempt #{log['attempt_count']}** {status_emoji} · {practice_date.strftime('%Y-%m-%d %H:%M')}")
                with attempt_header_col2:
                    if st.button("✏️", key=f"edit_{log['id']}", help="Edit this log", type="secondary"):
                        edit_log_dialog(log)
                with attempt_header_col3:
                    if st.button("🗑️", key=f"delete_{log['id']}", help="Delete this log", type="secondary"):
                        success, message = delete_log(log['id'])
                        if success:
                            st.toast("Log deleted successfully!", icon="✅")
                            st.rerun()
                        else:
                            st.error(message)
                
                attempt_col1, attempt_col2 = st.columns([1, 3])
                with attempt_col1:
                    st.write(f"**Status:** {log['status']}")
                with attempt_col2:
                    if log.get("note"):
                        st.write(f"**Notes:** {log['note']}")
                    else:
                        st.write("*No notes*")
                
                if idx < len(problem_logs_sorted):
                    st.markdown("---")


def show_trash_bin():
    """Trash Bin page"""
    st.header("🗑️ Trash Bin")
    st.markdown("Deleted logs can be restored from here")
    
    with st.spinner("Loading trash..."):
        trash_logs = get_trash_logs(st.session_state.user_id)
    
    if not trash_logs:
        st.info("🎉 Trash is empty! All your logs are safe and sound.")
        return
    
    st.warning(f"Found {len(trash_logs)} deleted log(s)")
    
    # Empty Trash button
    if st.button("🗑️ Empty Trash Permanently", type="primary", help="Permanently delete all items in trash"):
        with st.spinner("Emptying trash..."):
            success, message = empty_trash(st.session_state.user_id)
            if success:
                st.toast(message, icon="✅")
                st.rerun()
            else:
                st.error(message)
    
    st.markdown("---")
    
    # Group trash logs by problem_id (similar to history page)
    from collections import defaultdict
    grouped_trash = defaultdict(list)
    
    for log in trash_logs:
        grouped_trash[log['problem_id']].append(log)
    
    # Display grouped trash logs
    for problem_id, problem_logs in grouped_trash.items():
        # Sort attempts by date (newest first)
        problem_logs_sorted = sorted(
            problem_logs, 
            key=lambda x: datetime.fromisoformat(x["practice_date"].replace("Z", "+00:00")),
            reverse=True
        )
        
        # Get problem info from the first log
        first_log = problem_logs_sorted[0]
        
        # Difficulty color coding
        diff_color = {
            "Easy": "🟢",
            "Medium": "🟡",
            "Hard": "🔴"
        }.get(first_log["difficulty"], "⚪")
        
        # Main expander for each problem
        with st.expander(
            f"{diff_color} {first_log['problem_id']}. **{first_log['problem_title']}**",
            expanded=False
        ):
            st.write(f"**Tags:** {first_log['tags']}")
            
            st.markdown("---")
            st.markdown("### 📜 Deleted Attempts")
            
            # Display each deleted attempt
            for idx, log in enumerate(problem_logs_sorted, 1):
                # Status emoji
                status_emoji = {
                    "INDEPENDENT": "✅",
                    "WITH_HINT": "💡",
                    "STUCK": "❌"
                }.get(log["status"], "📝")
                
                practice_date = datetime.fromisoformat(log["practice_date"].replace("Z", "+00:00"))
                
                # Attempt details with restore button
                attempt_header_col1, attempt_header_col2 = st.columns([5, 1])
                with attempt_header_col1:
                    st.markdown(f"**Attempt #{log['attempt_count']}** {status_emoji} · {practice_date.strftime('%Y-%m-%d %H:%M')}")
                with attempt_header_col2:
                    if st.button("♻️", key=f"restore_{log['id']}", help="Restore this log", type="primary"):
                        success, message = restore_log(log['id'])
                        if success:
                            st.toast("Log restored!", icon="♻️")
                            st.rerun()
                        else:
                            st.error(message)
                
                attempt_col1, attempt_col2 = st.columns([1, 3])
                with attempt_col1:
                    st.write(f"**Status:** {log['status']}")
                with attempt_col2:
                    if log.get("note"):
                        st.write(f"**Notes:** {log['note']}")
                    else:
                        st.write("*No notes*")
                
                if idx < len(problem_logs_sorted):
                    st.markdown("---")


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