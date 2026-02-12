import streamlit as st
from api_client import login, signup


def show_login_page() -> None:
    """Render the login/signup page."""
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
