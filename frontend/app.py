import streamlit as st
from api_client import check_backend_connection
from utils.session import init_session_state
from components.auth import show_login_page
from views import diary, history, trash, coach


st.set_page_config(
    page_title="SolveNext",
    page_icon="🎯",
    layout="wide"
)


def logout():
    """Logout user"""
    st.session_state.user_id = None
    st.session_state.username = None
    st.rerun()


def render_sidebar() -> str:
    with st.sidebar:
        st.header("Navigation")

        page = st.radio(
            "Select a page:",
            ["📝 Write Diary", "📊 History", "🗑️ Trash Bin", "🤖 AI Coach"],
            label_visibility="collapsed"
        )

        if st.session_state.last_visited_page is None:
            st.session_state.last_visited_page = page
        elif st.session_state.last_visited_page != page:
            st.session_state.last_visited_page = page
            if page == "📝 Write Diary":
                diary.reset_diary_form()

        st.markdown("---")
        st.write(f"**User:** {st.session_state.username}")
        st.write(f"**User ID:** {st.session_state.user_id}")

        if st.button("Logout", type="secondary", use_container_width=True):
            logout()

    return page


def main() -> None:
    init_session_state()

    # Check backend connection
    if not check_backend_connection():
        st.error("⚠️ Cannot connect to backend server. Please ensure the FastAPI backend is running at http://127.0.0.1:8000")
        st.info("Run the backend with: `cd backend && uvicorn main:app --reload`")
        return

    # If not logged in, show login/signup page
    if st.session_state.user_id is None:
        show_login_page()
        return

    # Logged in - Show main app
    st.title(f"🎯 SolveNext - Welcome, {st.session_state.username}!")

    page = render_sidebar()

    # Page routing
    if page == "📝 Write Diary":
        diary.show_write_diary()
        return
    if page == "📊 History":
        history.show_history()
        return
    if page == "🗑️ Trash Bin":
        trash.show_trash_bin()
        return
    if page == "🤖 AI Coach":
        coach.show_ai_coach()
        return


if __name__ == "__main__":
    main()