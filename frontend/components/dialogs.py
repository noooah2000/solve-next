import streamlit as st
from datetime import datetime
from api_client import update_log


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
        except Exception:
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
            ["INDEPENDENT", "WITH HINT", "STUCK"],
            index=["INDEPENDENT", "WITH HINT", "STUCK"].index(current_status),
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
