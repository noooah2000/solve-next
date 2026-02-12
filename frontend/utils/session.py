import streamlit as st


def init_session_state() -> None:
    """Initialize core session state variables."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "last_visited_page" not in st.session_state:
        st.session_state.last_visited_page = None
