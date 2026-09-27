"""Gamified Bio-Olympiad & Rosalind Practice Arena.

Multi-tier challenges (Foundational → Intermediate → Olympiad), instant
algorithmic grading, XP points, and Groq Llama-8B hints (with a rich local
hint fallback so the arena works fully offline).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from titan_utils.mol3d import embed_html
from titan_utils.olympiad import (
    CHALLENGES,
    TIERS,
    grade_attempt,
    get_challenge,
    get_hint,
    list_challenges,
    tier_progress,
    total_xp,
)
from titan_utils.ui import titan_title
from titan_utils.voice_assistant import narration_html, summarize_for_speech

titan_title(
    "🏆",
    "Bio-Olympiad & Rosalind Practice Arena",
    "Train like a champion — multi-tier bioinformatics challenges, instant grading, XP progression, and AI coaching hints.",
)

# ── Session progress state ──────────────────────────────────────────────────
if "olympiad_xp" not in st.session_state:
    st.session_state["olympiad_xp"] = 0
if "olympiad_results" not in st.session_state:
    st.session_state["olympiad_results"] = []

progress = tier_progress(st.session_state["olympiad_results"])

# ── Leaderboard header ──────────────────────────────────────────────────────
c_xp, c_solved, c_tier, c_badge = st.columns(4)
solved_total = sum(t["solved"] for t in progress.values())
c_xp.metric("Total XP", str(st.session_state["olympiad_xp"]))
c_solved.metric("Challenges Solved", f"{solved_total}/{len(CHALLENGES)}")
level = (
    "🥇 Olympiad Master" if st.session_state["olympiad_xp"] >= 600
    else "🥈 Intermediate Researcher" if st.session_state["olympiad_xp"] >= 200
    else "🥉 Foundational Explorer" if st.session_state["olympiad_xp"] > 0
    else "🎓 Newcomer"
)
c_tier.metric("Current Rank", level)
c_badge.metric("Attempts Logged", str(len(st.session_state["olympiad_results"])))

with st.expander("📈 Tier Progress", expanded=False):
    st.dataframe(
        pd.DataFrame([
            {"Tier": t, "Solved": p["solved"], "of": p["total_challenges"],
             "XP": p["xp"], "Attempts": p["attempted"]}
            for t, p in progress.items()
        ]),
        use_container_width=True,
        hide_index=True,
    )

# ── Challenge picker ────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("🎯 Select Your Challenge")
c_tier_sel, c_chal = st.columns([1, 2])
with c_tier_sel:
    tier = st.selectbox("Difficulty Tier:", options=list(TIERS), key="olympiad_tier")
with c_chal:
    challenges = list_challenges(tier)
    ch_map = {f"{c.id} · {c.title} (+{c.xp} XP)": c.id for c in challenges}
    ch_label = st.selectbox("Challenge:", options=list(ch_map.keys()), key="olympiad_challenge")

challenge = get_challenge(ch_map[ch_label])

with st.container(border=True):
    st.markdown(f"#### 🧩 {challenge.title}")
    st.caption(f"**Tier:** {challenge.tier} | **Topic:** {challenge.topic} | **Reward:** {challenge.xp} XP")
    st.markdown(challenge.prompt)

# ── Workspace ───────────────────────────────────────────────────────────────
c_load, c_grade, c_hint, c_solution = st.columns(4)
load_clicked = c_load.button("🧪 Load Sample Dataset", use_container_width=True, key="olympiad_load_btn")
grade_clicked = c_grade.button("⚡ Grade My Answer", type="primary", use_container_width=True, key="olympiad_grade_btn")
hint_clicked = c_hint.button("💡 Get Hint (Groq Llama-8B)", use_container_width=True, key="olympiad_hint_btn")
solution_clicked = c_solution.button("📖 Solution Walkthrough", use_container_width=True, key="olympiad_solution_btn")

if load_clicked:
    st.session_state["olympiad_input"] = challenge.sample_input

input_text = st.text_area(
    "Dataset / Input:",
    value=challenge.sample_input,
    height=110,
    key="olympiad_input",
    help="This is the raw dataset your algorithm must solve (kept in RAM only).",
)
answer_text = st.text_area(
    "Your Answer (what you would submit):",
    value="",
    height=90,
    key="olympiad_answer",
    help="The grader normalises whitespace and case before comparing.",
)

if grade_clicked:
    grade = grade_attempt(challenge.id, input_text, answer_text)
    if grade.correct:
        st.session_state["olympiad_xp"] += grade.xp_earned
        st.session_state["olympiad_results"].append(grade)
        st.success(f"✅ Correct! **+{grade.xp_earned} XP** — total: **{st.session_state['olympiad_xp']} XP**")
        st.balloons()
    elif not (answer_text or "").strip():
        st.info(grade.feedback)
    else:
        st.session_state["olympiad_results"].append(grade)
        st.warning(grade.feedback)

if hint_clicked:
    hint_text, hint_source = get_hint(challenge.id)
    st.info(f"💡 **Hint ({hint_source}):** {hint_text}")
    st.caption("Groq Llama-8B is consulted when GROQ_API_KEY is configured; otherwise the local Titan hint library keeps the arena offline-capable.")

if solution_clicked:
    st.markdown("##### 📖 Official Solution Walkthrough")
    for i, step in enumerate(challenge.solution_steps, start=1):
        st.markdown(f"**Step {i}.** {step}")
    st.code(f"Reference output for the sample dataset:\n\n{challenge.sample_output}", language="text")
    st.caption(challenge.explanation)

# ── Challenge bank overview ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("🗂 Full Challenge Bank")
bank_df = pd.DataFrame([
    {"ID": c.id, "Title": c.title, "Tier": c.tier, "Topic": c.topic, "XP": c.xp}
    for c in CHALLENGES
])
st.dataframe(bank_df, use_container_width=True, hide_index=True)

# ── Coach narration + footer ────────────────────────────────────────────────
st.markdown("#### 🔊 Coach Narration")
embed_html(
    narration_html(
        summarize_for_speech(
            f"Welcome to the Titan Practice Arena. Current rank: {level} with "
            f"{st.session_state['olympiad_xp']} experience points. "
            f"You are working on {challenge.title}, a {challenge.tier} challenge "
            f"worth {challenge.xp} XP. {challenge.explanation}"
        ),
        autoplay=False,
    ),
    height=210,
)

st.caption(
    "🛡️ Zero Data Retention — attempt data is graded in ephemeral RAM; only XP counters and score summaries are kept in session state."
)
