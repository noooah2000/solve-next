import streamlit as st
from datetime import datetime
from api_client import get_user_logs, delete_log
from components.dialogs import edit_log_dialog


def _group_logs_by_problem(logs: list[dict]) -> dict[str, list[dict]]:
    from collections import defaultdict
    grouped_logs: dict[str, list[dict]] = defaultdict(list)
    for log in logs:
        grouped_logs[log['problem_id']].append(log)
    return grouped_logs


def _sorted_attempts(problem_logs: list[dict]) -> list[dict]:
    return sorted(
        problem_logs,
        key=lambda x: datetime.fromisoformat(x["practice_date"].replace("Z", "+00:00")),
        reverse=True
    )


def _render_attempt_row(log: dict) -> None:
    status_emoji = {
        "INDEPENDENT": "✅",
        "WITH_HINT": "💡",
        "STUCK": "❌"
    }.get(log["status"], "📝")

    practice_date = datetime.fromisoformat(log["practice_date"].replace("Z", "+00:00"))

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


def _render_problem_group(problem_logs_sorted: list[dict]) -> None:
    if not problem_logs_sorted:
        return

    first_log = problem_logs_sorted[0]
    diff_color = {
        "Easy": "🟢",
        "Medium": "🟡",
        "Hard": "🔴"
    }.get(first_log["difficulty"], "⚪")
    total_attempts = len(problem_logs_sorted)

    with st.expander(
        f"{diff_color} {first_log['problem_id']}. **{first_log['problem_title']}**",
        expanded=False
    ):
        col1, col2, _ = st.columns([1, 1, 3])
        with col1:
            st.metric("Total Attempts", total_attempts)
        with col2:
            st.metric("Difficulty", first_log["difficulty"])

        st.write(f"**Tags:** {first_log['tags']}")

        st.markdown("---")
        st.markdown("### 📜 Attempt History")

        for idx, log in enumerate(problem_logs_sorted, 1):
            _render_attempt_row(log)
            if idx < len(problem_logs_sorted):
                st.markdown("---")


def show_history() -> None:
    """History page"""
    st.header("📊 Practice History")

    with st.spinner("Loading your practice history..."):
        logs = get_user_logs(st.session_state.user_id)

    if not logs:
        st.info("No practice logs found. Start logging your practice sessions!")
        return

    st.success(f"Found {len(logs)} practice logs across {len(set(log['problem_id'] for log in logs))} unique problems")

    grouped_logs = _group_logs_by_problem(logs)
    for problem_logs in grouped_logs.values():
        problem_logs_sorted = _sorted_attempts(problem_logs)
        _render_problem_group(problem_logs_sorted)
