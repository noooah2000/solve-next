import re
import streamlit as st
from api_client import get_recommendations, get_ai_hints


TARGET_COMPANIES = [
    "Google", "Meta", "Amazon", "Microsoft", "Apple", "Netflix",
    "Uber", "Bloomberg", "TikTok"
]

AVAILABLE_TAGS = [
    "Array", "String", "Hash Table", "Dynamic Programming", "Math",
    "Sorting", "Greedy", "Depth-First Search", "Breadth-First Search",
    "Binary Search", "Tree", "Graph", "Backtracking", "Linked List",
    "Stack", "Queue", "Heap", "Trie", "Sliding Window", "Two Pointers"
]


def clean_hint_text(hint_text: str) -> str:
    return re.sub(
        r"^(?:\*\*|)?Hint \d+[:.]\s*(?:\*\*|)?",
        "",
        hint_text
    ).strip()


def normalize_title(title: str) -> str:
    return title.strip().lower()


def render_ai_hints(problem_title: str, idx: int) -> None:
    hints_key = f"hints_{idx}_{problem_title.replace(' ', '_')}"
    has_hints = hints_key in st.session_state and st.session_state[hints_key]

    hint_col1, hint_col2 = st.columns([2, 2])
    with hint_col1:
        button_label = "🔄 Ask AI Again" if has_hints else "✨ Ask AI for Hints"
        if st.button(button_label, key=f"hint_btn_{idx}_{problem_title.replace(' ', '_')}", use_container_width=True):
            with st.spinner("Generating AI hints..."):
                success, hints, message = get_ai_hints(problem_title)
                if success:
                    st.session_state[hints_key] = hints
                    st.rerun()
                else:
                    st.error(message)

    if has_hints:
        hints = st.session_state[hints_key]
        st.markdown("**✨ AI-Generated Hints:**")

        hint_labels = [
            ("✨ AI Hint 1: High-level Concept", "Conceptual approach and strategy"),
            ("✨ AI Hint 2: Strategic Approach", "Data structure or algorithm suggestion"),
            ("✨ AI Hint 3: Implementation Detail", "Key logic step or pseudo-code")
        ]

        for hint_idx, (label, description) in enumerate(hint_labels):
            if hint_idx < len(hints):
                with st.expander(label, expanded=False):
                    hint_content = hints[hint_idx]
                    st.write(clean_hint_text(hint_content))
                    st.caption(description)

        st.caption("💡 AI-generated hints may be imperfect. Use them as a guide.")


def render_problem_card(idx: int, problem: dict) -> None:
    problem_id = problem.get("problem_id")
    title = problem.get("title", "Untitled")
    display_prefix = f"{problem_id}." if problem_id else f"{idx}."
    st.markdown(f"#### {display_prefix} {title}")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"**Reason:** {problem.get('reason', '')}")
        st.write(f"**Difficulty:** {problem.get('difficulty', '')}")
    with col2:
        st.link_button(
            "Solve on LeetCode →",
            problem.get('link', ""),
            use_container_width=True
        )

    render_ai_hints(title, idx)
    st.markdown("---")


def render_filters_section() -> tuple[list[str], str, int, list[str]]:
    col1, col2 = st.columns([3, 1])

    with col1:
        selected_options = st.multiselect(
            "Topic Tags",
            AVAILABLE_TAGS,
            default=[],
            placeholder="Select topics (Leave empty for all)",
            help="Filter problems by specific algorithms or data structures."
        )

    final_tags = AVAILABLE_TAGS if not selected_options else selected_options

    with col2:
        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"],
            index=1,
            help="Choose the difficulty level."
        )

    col3, col4 = st.columns([3, 1])
    with col3:
        target_companies = st.multiselect(
            "Target Company",
            TARGET_COMPANIES,
            default=[],
            placeholder="Choose companies (Leave empty for any)",
            help="Choose specific companies to simulate their interview style."
        )

    with col4:
        count = st.number_input(
            "Number of Problems",
            min_value=1,
            max_value=5,
            value=3,
            help="How many problems do you want to practice?"
        )

    return final_tags, difficulty, count, target_companies


def render_recommendations_section(result: dict) -> None:
    st.markdown("### 💡 Personalized Advice")
    st.info(result["advice"])

    st.markdown("### 📚 Recommended Problems")
    st.caption("💡 Note: If exact matches aren't found, the system automatically relaxes criteria to find the next best problems for you.")

    recommendations = result.get("recommendations", [])
    if not recommendations:
        st.warning("No problems recommended. Try adjusting your filters.")
        return

    for idx, problem in enumerate(recommendations, 1):
        with st.container():
            render_problem_card(idx, problem)


def show_ai_coach() -> None:
    """AI Coach page"""
    st.header("🎯 Personal AI Coach")
    st.markdown("Get personalized problem recommendations based on your practice history")

    if "recommendations" not in st.session_state:
        st.session_state.recommendations = None
    if "seen_problems" not in st.session_state:
        # Only track problems shown in current session, backend handles mastered filtering
        st.session_state.seen_problems = set()
    final_tags, difficulty, count, target_companies = render_filters_section()

    if st.button("Get Advice", type="primary", use_container_width=True):
        if not final_tags:
            st.warning("Please select at least one topic tag")
            return

        keys_to_clear = [key for key in st.session_state.keys() if key.startswith("hints_")]
        for key in keys_to_clear:
            del st.session_state[key]

        with st.status("AI is analyzing your practice history and generating recommendations..."):
            success, result = get_recommendations(
                st.session_state.username,
                final_tags,
                difficulty,
                count,
                target_companies,
                list(st.session_state.seen_problems)
            )

        if not success:
            st.error(f"Failed to get recommendations: {result}")
            st.session_state.recommendations = None
            return

        st.session_state.recommendations = result
        new_titles = {
            normalize_title(problem.get("title", ""))
            for problem in result.get("recommendations", [])
            if problem.get("title")
        }
        st.session_state.seen_problems.update(new_titles)

    if not st.session_state.recommendations:
        return

    render_recommendations_section(st.session_state.recommendations)
