import streamlit as st
from datetime import datetime
from api_client import get_trash_logs, restore_log, empty_trash


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


def _render_trash_attempt(log: dict) -> None:
    status_emoji = {
        "INDEPENDENT": "✅",
        "WITH HINT": "💡",
        "STUCK": "❌"
    }.get(log["status"], "📝")

    practice_date = datetime.fromisoformat(log["practice_date"].replace("Z", "+00:00"))

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


def _render_trash_group(problem_logs_sorted: list[dict]) -> None:
    if not problem_logs_sorted:
        return

    first_log = problem_logs_sorted[0]
    diff_color = {
        "Easy": "🟢",
        "Medium": "🟡",
        "Hard": "🔴"
    }.get(first_log["difficulty"], "⚪")

    with st.expander(
        f"{diff_color} {first_log['problem_id']}. **{first_log['problem_title']}**",
        expanded=False
    ):
        st.write(f"**Tags:** {first_log['tags']}")

        st.markdown("---")
        st.markdown("### 📜 Deleted Attempts")

        for idx, log in enumerate(problem_logs_sorted, 1):
            _render_trash_attempt(log)
            if idx < len(problem_logs_sorted):
                st.markdown("---")


def show_trash_bin() -> None:
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

    grouped_trash = _group_logs_by_problem(trash_logs)
    for problem_logs in grouped_trash.values():
        problem_logs_sorted = _sorted_attempts(problem_logs)
        _render_trash_group(problem_logs_sorted)
