"""🎯 NEET Adaptive Packs — 100 Class-11/12 biology MCQs with adaptive difficulty.

Adaptive engine: wrong answer → similar question; right → harder.
Session score + XP tracking. Data from data/neet.json.
"""
from __future__ import annotations

import json
import pathlib
import random

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🎯",
    "NEET Adaptive Packs",
    "100 biology MCQs (Class 11/12) with an adaptive engine — wrong answers get you similar questions, right answers unlock harder ones!",
)

# ── Load question bank ───────────────────────────────────────────────────────
DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "neet.json"
with open(DATA_PATH, encoding="utf-8") as fh:
    QUESTION_BANK: list[dict] = json.load(fh)

CHAPTERS = sorted(set(q["chapter"] for q in QUESTION_BANK))

# ── Session state ────────────────────────────────────────────────────────────
if "neet_score" not in st.session_state:
    st.session_state["neet_score"] = 0
if "neet_total" not in st.session_state:
    st.session_state["neet_total"] = 0
if "neet_xp" not in st.session_state:
    st.session_state["neet_xp"] = 0
if "neet_streak" not in st.session_state:
    st.session_state["neet_streak"] = 0
if "neet_current_q" not in st.session_state:
    st.session_state["neet_current_q"] = None
if "neet_answered" not in st.session_state:
    st.session_state["neet_answered"] = False
if "neet_selected_chapters" not in st.session_state:
    st.session_state["neet_selected_chapters"] = CHAPTERS
if "neet_difficulty" not in st.session_state:
    st.session_state["neet_difficulty"] = 1  # adaptive

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(t("### 📊 Your Stats"))
    st.metric(t("Score"), f"{st.session_state['neet_score']}/{st.session_state['neet_total']}")
    st.metric(t("XP Earned"), st.session_state["neet_xp"])
    st.metric(t("Current Streak"), f"🔥 {st.session_state['neet_streak']}")
    if st.session_state["neet_total"] > 0:
        pct = st.session_state["neet_score"] / st.session_state["neet_total"] * 100
        st.metric(t("Accuracy"), f"{pct:.0f}%")

# ── Chapter filter ───────────────────────────────────────────────────────────
selected = st.multiselect(
    t("Select chapters:"),
    options=CHAPTERS,
    default=st.session_state["neet_selected_chapters"],
)
st.session_state["neet_selected_chapters"] = selected or CHAPTERS

# ── Adaptive question selection ──────────────────────────────────────────────
def _pick_question() -> dict | None:
    """Pick the next question using adaptive difficulty."""
    chapters = st.session_state["neet_selected_chapters"]
    difficulty = st.session_state["neet_difficulty"]
    pool = [q for q in QUESTION_BANK if q["chapter"] in chapters and abs(q["difficulty"] - difficulty) <= 1]
    if not pool:
        pool = [q for q in QUESTION_BANK if q["chapter"] in chapters]
    if not pool:
        return None
    return random.choice(pool)


def _on_answer(question: dict, selected_idx: int) -> None:
    """Process the answer and update adaptive difficulty."""
    correct = question["correct"]
    st.session_state["neet_total"] += 1
    if selected_idx == correct:
        st.session_state["neet_score"] += 1
        st.session_state["neet_xp"] += 10
        st.session_state["neet_streak"] += 1
        st.session_state["neet_difficulty"] = min(3, st.session_state["neet_difficulty"] + 0.5)
    else:
        st.session_state["neet_streak"] = 0
        st.session_state["neet_difficulty"] = max(1, st.session_state["neet_difficulty"] - 0.5)
    st.session_state["neet_answered"] = True


# ── Main quiz area ───────────────────────────────────────────────────────────
if st.session_state["neet_current_q"] is None:
    if st.button(t("🎯 Start Quiz"), type="primary", use_container_width=True):
        q = _pick_question()
        if q:
            st.session_state["neet_current_q"] = q
            st.session_state["neet_answered"] = False
            st.rerun()
        else:
            st.warning(t("No questions available for the selected chapters."))
else:
    q = st.session_state["neet_current_q"]
    diff_emoji = {1: "🟢 Easy", 2: "🟡 Medium", 3: "🔴 Hard"}

    with st.container(border=True):
        st.markdown(f"**{t('Chapter')}:** {q['chapter']} | **{t('Difficulty')}:** {diff_emoji.get(q['difficulty'], '🟢')}")
        st.markdown(f"### {q['question']}")

        if not st.session_state["neet_answered"]:
            for i, option in enumerate(q["options"]):
                if st.button(option, key=f"opt_{i}", use_container_width=True):
                    _on_answer(q, i)
                    st.rerun()
        else:
            # Show result
            selected_idx = st.session_state.get("neet_last_selected", -1)
            correct = q["correct"]
            # Re-display options with color coding
            for i, option in enumerate(q["options"]):
                if i == correct:
                    st.success(f"✅ {option}")
                else:
                    st.caption(option)

            if st.session_state["neet_score"] > 0 and st.session_state["neet_total"] > 0:
                last_was_correct = st.session_state["neet_streak"] > 0
                if last_was_correct:
                    st.success(t("✅ Correct! +10 XP 🎯"))
                else:
                    st.error(t("❌ Wrong! The correct answer is: {answer}", answer=q["options"][correct]))

            st.info(f"💡 {q['explanation']}")

            if st.button(t("➡️ Next Question"), type="primary", use_container_width=True):
                next_q = _pick_question()
                st.session_state["neet_current_q"] = next_q
                st.session_state["neet_answered"] = False
                st.rerun()

    if st.button(t("🔄 Reset Quiz")):
        st.session_state["neet_current_q"] = None
        st.session_state["neet_score"] = 0
        st.session_state["neet_total"] = 0
        st.session_state["neet_xp"] = 0
        st.session_state["neet_streak"] = 0
        st.session_state["neet_difficulty"] = 1
        st.rerun()

dr_titan_tip(
    "The NEET exam tests your understanding, not just memory. Focus on WHY each answer is correct — "
    "that's what adaptive learning helps with. The more you practice, the better your concepts get!"
)