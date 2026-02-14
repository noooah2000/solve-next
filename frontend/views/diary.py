import streamlit as st
from datetime import datetime
from api_client import create_log, get_problem_preview


INVALID_INPUT_MESSAGE = "⚠️ Invalid format! Please enter a numeric ID (e.g., 1) or a full LeetCode URL."


def _init_diary_state() -> None:
    if "current_preview" not in st.session_state:
        st.session_state.current_preview = None
    if "problem_input" not in st.session_state:
        st.session_state.problem_input = ""
    if "check_problem_requested" not in st.session_state:
        st.session_state.check_problem_requested = False
    if "notes_input" not in st.session_state:
        st.session_state.notes_input = ""
    if "save_error" not in st.session_state:
        st.session_state.save_error = ""


def _apply_preview(input_val: str, preview_container) -> None:
    """Send raw input to backend for parsing and preview"""
    with st.spinner("Checking problem..."):
        ok, data, message = get_problem_preview(input_val)
        if not ok:
            st.session_state.current_preview = None
            preview_container.error(message)
            return

        st.session_state.current_preview = {
            "slug": data.get("slug", ""),
            "title": data.get("title", ""),
            "difficulty": data.get("difficulty", ""),
            "input": input_val
        }


def _render_preview(preview_container) -> None:
    preview = st.session_state.current_preview
    if not preview:
        return

    difficulty = preview.get("difficulty", "")
    diff_color = "green" if difficulty == "Easy" else "orange" if difficulty == "Medium" else "red"
    with preview_container.container(border=True):
        st.markdown(f"**Problem:** {preview.get('title', '')}")
        st.markdown(f"**Difficulty:** :{diff_color}[{difficulty}]")


def _render_input_row(request_check) -> str:
    col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
    with col1:
        problem_input = st.text_input(
            "Problem ID or Link",
            placeholder="e.g., 1 or https://leetcode.com/problems/two-sum/",
            help="Enter the numeric Problem ID or the full URL. Raw slugs (e.g., 'two-sum') are no longer supported.",
            key="problem_input",
            on_change=request_check
        )
    with col2:
        if st.button("🔍 Check Problem", type="secondary", use_container_width=True):
            st.session_state.check_problem_requested = True
    return problem_input


def _maybe_check_problem(problem_input: str, preview_container) -> None:
    if not st.session_state.check_problem_requested:
        return

    st.session_state.check_problem_requested = False
    input_val = problem_input.strip()
    if not input_val:
        preview_container.warning("Please enter a problem ID or link")
        return

    _apply_preview(input_val, preview_container)


def reset_diary_form() -> None:
    """Reset the New Practice Log form state."""
    st.session_state.problem_input = ""
    st.session_state.notes_input = ""
    st.session_state.status_input = "INDEPENDENT"
    st.session_state.current_preview = None
    st.session_state.save_error = ""
    st.session_state.check_problem_requested = False


def show_write_diary() -> None:
    """Write Diary page"""
    st.header("📝 New Practice Log")
    st.markdown("Record your LeetCode practice session")

    _init_diary_state()

    def request_check():
        st.session_state.check_problem_requested = True

    def save_log_callback():
        st.session_state.save_error = ""
        input_val = st.session_state.problem_input.strip()
        if not input_val:
            st.session_state.save_error = INVALID_INPUT_MESSAGE
            return

        needs_check = (
            not st.session_state.current_preview or
            st.session_state.current_preview.get("input") != input_val
        )

        if needs_check:
            ok, data, message = get_problem_preview(input_val)
            if not ok:
                st.session_state.save_error = message
                return

            st.session_state.current_preview = {
                "slug": data.get("slug", ""),
                "title": data.get("title", ""),
                "difficulty": data.get("difficulty", ""),
                "input": input_val
            }

        preview = st.session_state.current_preview
        success, message = create_log(
            st.session_state.username,
            preview["slug"],
            st.session_state.status_input,
            st.session_state.notes_input.strip()
        )
        if success:
            st.toast("✅ Log saved successfully!")
            st.session_state.problem_input = ""
            st.session_state.notes_input = ""
            st.session_state.current_preview = None
        else:
            st.session_state.save_error = message

    problem_input = _render_input_row(request_check)

    preview_container = st.container()
    _maybe_check_problem(problem_input, preview_container)
    _render_preview(preview_container)

    st.selectbox(
        "Status",
        ["INDEPENDENT", "WITH HINT", "STUCK"],
        help="How did you solve this problem?",
        key="status_input"
    )

    st.text_area(
        "Notes (Optional)",
        placeholder="Add any notes about your practice session, challenges faced, or insights gained...",
        height=150,
        key="notes_input"
    )

    if st.button("Save Log", type="primary", use_container_width=True, on_click=save_log_callback):
        pass

    if st.session_state.save_error:
        st.error(st.session_state.save_error)
