"""Classroom Quiz Mode — a lightweight, educational, login-free quiz page."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from titan_utils.classroom_quiz import (
    MAX_STUDENTS_PER_ROOM,
    close_classroom,
    create_classroom,
    get_classroom,
    get_leaderboard,
    get_student_progress,
    join_classroom,
    resolve_topic,
    submit_answer,
)
from titan_utils.classroom_storage import sync_classroom_profile
from titan_utils.olympiad import GradeResult, TIER_XP
from titan_utils.ui import titan_title


titan_title(
    "🎓",
    "Classroom Quiz Mode",
    "Teacher-hosted five-question MCQs from built-in biology content — no student login required.",
)
st.info(
    "Educational practice only — not for clinical or diagnostic decisions. "
    "Quiz content is built in and works offline."
)


def _query_code() -> str:
    """Read an optional shared link parameter, without requiring it."""
    try:
        return str(st.query_params.get("classroom", "")).strip().upper()[:4]
    except Exception:  # pragma: no cover - older Streamlit compatibility
        try:
            values = st.experimental_get_query_params().get("classroom", [""])
            return str(values[0] if values else "").strip().upper()[:4]
        except Exception:
            return ""


def _sync_arena_xp(room_code: str, participant: dict, answers: dict, topic: str) -> None:
    """Mirror new classroom points into the existing Bio-Olympiad XP state."""
    st.session_state.setdefault("olympiad_xp", 0)
    st.session_state.setdefault("olympiad_results", [])
    synced = st.session_state.setdefault("classroom_xp_by_room", {})
    previous = int(synced.get(room_code, 0))
    current = int(participant.get("xp", 0))
    if current <= previous:
        return

    # Points are awarded by the quiz engine at the existing Foundational Arena
    # rate. Results also appear in page 76's existing tier-progress summary.
    st.session_state["olympiad_xp"] += current - previous
    recorded = st.session_state.setdefault("classroom_grade_ids", set())
    for question_index, answer in sorted(answers.items()):
        marker = f"{room_code}:{question_index}"
        if answer.get("correct") and marker not in recorded:
            st.session_state["olympiad_results"].append(
                GradeResult(
                    challenge_id=f"classroom-{room_code}-{question_index}",
                    title=f"Classroom Quiz: {topic} · Q{question_index + 1}",
                    tier="Foundational",
                    correct=True,
                    xp_earned=TIER_XP["Foundational"],
                    expected="Correct MCQ option",
                    submitted="Correct MCQ option",
                    feedback="Correct classroom quiz answer.",
                )
            )
            recorded.add(marker)
    synced[room_code] = current


def _render_live_leaderboard(room_code: str) -> None:
    """Render a two-second live leaderboard when Streamlit fragments exist."""
    def draw() -> None:
        room = get_classroom(room_code)
        if not room:
            st.warning("This room has expired. Create a new classroom code.")
            return
        st.markdown("#### 🏆 Live classroom leaderboard")
        st.caption(
            f"{room['joined_count']} / {room['student_limit']} students joined · "
            f"Room status: {room['status']} · {room['question_count']} questions"
        )
        leaderboard = get_leaderboard(room_code)
        if leaderboard:
            st.dataframe(
                pd.DataFrame(leaderboard),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Waiting for students to join on their phones.")

    fragment = getattr(st, "fragment", None)
    if fragment:
        fragment(run_every=2.0)(draw)()
    else:  # Streamlit versions without fragments get a manual-refresh page rerun.
        draw()


def _teacher_view() -> None:
    st.markdown("### 🧑‍🏫 Teacher / host")
    with st.form("classroom_create_form"):
        topic = st.text_input(
            "Quiz topic",
            value="CRISPR",
            max_chars=80,
            help="Built-in topics include CRISPR, DNA, GC content, PCR, and Central Dogma.",
        )
        student_limit = st.number_input(
            "Expected student count",
            min_value=1,
            max_value=MAX_STUDENTS_PER_ROOM,
            value=25,
            step=1,
        )
        create_clicked = st.form_submit_button(
            "Create five-question quiz",
            type="primary",
            use_container_width=True,
        )

    if create_clicked:
        try:
            _resolved_topic, has_builtin_topic = resolve_topic(topic)
            room = create_classroom(topic, int(student_limit))
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))
        else:
            if not has_builtin_topic:
                st.warning(
                    f"No exact question bank for that topic; using the built-in "
                    f"{room['topic']} questions instead."
                )
            st.session_state["classroom_teacher_code"] = room["code"]
            st.session_state["classroom_teacher_topic"] = room["topic"]

    room_code = st.session_state.get("classroom_teacher_code", "")
    if not room_code:
        st.caption("Create a room, share its four-character code and app URL, then watch the leaderboard update live.")
        return

    room = get_classroom(room_code)
    if not room:
        st.warning("This classroom has expired. Create a new code to start another session.")
        st.session_state.pop("classroom_teacher_code", None)
        return

    st.success(f"Quiz ready for **{room['topic']}** — session code: **{room_code}**")
    st.code(f"{room_code}    ·    ?classroom={room_code}", language="text")
    st.caption(
        "Students open this app on a phone, choose Student / Join, and enter the code. "
        "The code is a room locator, not a password."
    )
    if room["status"] == "active":
        if st.button("End this classroom", key="classroom_close_button"):
            close_classroom(room_code)
            st.rerun()
    else:
        st.info("This classroom is closed. Its leaderboard remains visible until the room expires.")
    _render_live_leaderboard(room_code)


def _student_view() -> None:
    st.markdown("### 📱 Student / join")
    query_code = _query_code()
    current_code = st.session_state.get("classroom_join_code", query_code)
    current_name = st.session_state.get("classroom_join_name", "")
    saved_profile = sync_classroom_profile(
        {"name": current_name, "code": current_code},
        key="classroom_local_profile_storage",
    )
    if "classroom_join_name" not in st.session_state:
        st.session_state["classroom_join_name"] = (saved_profile or {}).get("name", "")
    if "classroom_join_code" not in st.session_state:
        st.session_state["classroom_join_code"] = query_code or (saved_profile or {}).get("code", "")

    with st.form("classroom_join_form"):
        code = st.text_input(
            "Four-character classroom code",
            max_chars=4,
            key="classroom_join_code",
            help="Enter the code shared by your teacher. No email or account is needed.",
        )
        name = st.text_input(
            "Student name or nickname",
            max_chars=32,
            key="classroom_join_name",
        )
        join_clicked = st.form_submit_button(
            "Join quiz",
            type="primary",
            use_container_width=True,
        )

    if join_clicked:
        try:
            joined = join_classroom(code, name)
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.session_state["classroom_joined_code"] = joined["room"]["code"]
            st.session_state["classroom_joined_name"] = joined["student"]["name"]
            st.rerun()

    room_code = st.session_state.get("classroom_joined_code", "")
    participant_name = st.session_state.get("classroom_joined_name", "")
    if not room_code or not participant_name:
        st.caption("Enter the shared code and a classroom nickname to join — no login required.")
        return

    progress = get_student_progress(room_code, participant_name)
    if not progress:
        st.warning("This room is no longer available. Ask your teacher for a new code.")
        st.session_state.pop("classroom_joined_code", None)
        return

    room = progress["room"]
    participant = progress["student"]
    _sync_arena_xp(room_code, participant, progress["student"]["answers"], room["topic"])
    st.success(f"Joined **{room['topic']}** as **{participant_name}** · **{participant['xp']} XP**")

    feedback = st.session_state.get("classroom_last_feedback", {})
    if feedback.get("code") == room_code and feedback.get("name") == participant_name:
        if feedback.get("correct"):
            st.success(f"Correct — +{feedback['xp_earned']} XP. {feedback['explanation']}")
        else:
            st.info(f"Not quite. {feedback['explanation']}")

    next_index = participant["answered"]
    if room["status"] == "closed":
        st.info("The teacher has ended this quiz. Your score remains on the leaderboard.")
    elif next_index < room["question_count"]:
        question = room["questions"][next_index]
        st.markdown(f"#### Question {next_index + 1} of {room['question_count']}")
        st.markdown(question["question"])
        selected_option = st.radio(
            "Choose one answer",
            question["options"],
            key=f"classroom_answer_{room_code}_{next_index}",
        )
        if st.button("Submit answer", type="primary", key=f"classroom_submit_{room_code}_{next_index}"):
            try:
                result = submit_answer(
                    room_code,
                    participant_name,
                    next_index,
                    question["options"].index(selected_option),
                )
            except ValueError as exc:
                st.error(str(exc))
            else:
                if result["accepted"]:
                    st.session_state["classroom_last_feedback"] = {
                        "code": room_code,
                        "name": participant_name,
                        "question_index": next_index,
                        **result,
                    }
                st.rerun()
    else:
        st.success("Quiz complete — thanks for participating!")

    _render_live_leaderboard(room_code)


role = st.radio(
    "Choose your classroom role",
    ("Teacher / Host", "Student / Join"),
    horizontal=True,
    key="classroom_role",
)
if role == "Teacher / Host":
    _teacher_view()
else:
    _student_view()
