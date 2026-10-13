"""🏆 Full Gamification — Achievement engine with badges, streaks, and XP.

Badges for actions: first tool run, 10 tools used, quiz perfect score,
7-day streak (localStorage date tracking). Badge gallery + progress.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🏆",
    "Achievements & Badges",
    "Track your progress, earn badges, and build streaks — gamify your bioinformatics learning journey!",
)

# ── Achievement definitions ──────────────────────────────────────────────────
ACHIEVEMENTS = [
    {
        "id": "first_tool",
        "name": "🧬 First Steps",
        "description": "Run your first bioinformatics tool",
        "icon": "🧬",
        "condition": "Use any tool in the Titan suite",
        "xp": 10,
    },
    {
        "id": "ten_tools",
        "name": "🔬 Tool Master",
        "description": "Use 10 different tools",
        "icon": "🔬",
        "condition": "Use 10 unique tools",
        "xp": 50,
    },
    {
        "id": "quiz_ace",
        "name": "🎯 Quiz Ace",
        "description": "Get a perfect score on any quiz",
        "icon": "🎯",
        "condition": "Score 5/5 on any quiz page",
        "xp": 30,
    },
    {
        "id": "streak_7",
        "name": "🔥 Week Warrior",
        "description": "Maintain a 7-day login streak",
        "icon": "🔥",
        "condition": "Visit Titan 7 days in a row",
        "xp": 100,
    },
    {
        "id": "streak_30",
        "name": "💪 Monthly Master",
        "description": "Maintain a 30-day login streak",
        "icon": "💪",
        "condition": "Visit Titan 30 days in a row",
        "xp": 500,
    },
    {
        "id": "explorer",
        "name": "🧭 Explorer",
        "description": "Visit every category in the suite",
        "icon": "🧭",
        "condition": "Open at least 1 page from each category",
        "xp": 40,
    },
    {
        "id": "flashcard_pro",
        "name": "🎴 Flashcard Pro",
        "description": "Review 50 flashcards",
        "icon": "🎴",
        "condition": "Complete 50 flashcard reviews",
        "xp": 60,
    },
    {
        "id": "lab_complete",
        "name": "🧪 Lab Rat",
        "description": "Complete all 3 virtual lab experiments",
        "icon": "🧪",
        "condition": "Finish DNA Extraction, Gel Electrophoresis, and PCR",
        "xp": 80,
    },
    {
        "id": "game_high",
        "name": "🎮 Cell Champion",
        "description": "Score 100+ in the Cell Survival Game",
        "icon": "🎮",
        "condition": "Achieve a score of 100 or more",
        "xp": 25,
    },
    {
        "id": "paper_reader",
        "name": "📄 Paper Reader",
        "description": "Look up 3 papers using Ask a Paper",
        "icon": "📄",
        "condition": "Fetch and read 3 different paper abstracts",
        "xp": 35,
    },
    {
        "id": "career_explorer",
        "name": "🚀 Career Curious",
        "description": "Explore 5 career profiles",
        "icon": "🚀",
        "condition": "Open 5 different career cards",
        "xp": 15,
    },
    {
        "id": "neet_streak",
        "name": "🎯 NEET Warrior",
        "description": "Get a 10-question streak in NEET Prep",
        "icon": "🎯",
        "condition": "Answer 10 questions correctly in a row",
        "xp": 75,
    },
]

# ── Session state ────────────────────────────────────────────────────────────
if "achievements" not in st.session_state:
    st.session_state["achievements"] = set()
if "achievement_xp" not in st.session_state:
    st.session_state["achievement_xp"] = 0
if "visit_dates" not in st.session_state:
    st.session_state["visit_dates"] = []
if "tools_used" not in st.session_state:
    st.session_state["tools_used"] = set()

# ── Record today's visit ─────────────────────────────────────────────────────
today_str = date.today().isoformat()
if today_str not in st.session_state["visit_dates"]:
    st.session_state["visit_dates"].append(today_str)

# ── Calculate streak ─────────────────────────────────────────────────────────
def _calculate_streak(dates: list[str]) -> int:
    """Calculate consecutive-day streak from list of ISO date strings."""
    if not dates:
        return 0
    sorted_dates = sorted(set(dates), reverse=True)
    try:
        latest = date.fromisoformat(sorted_dates[0])
    except ValueError:
        return 0
    if (date.today() - latest).days > 1:
        return 0
    streak = 1
    for i in range(1, len(sorted_dates)):
        try:
            current = date.fromisoformat(sorted_dates[i])
            previous = date.fromisoformat(sorted_dates[i - 1])
            if (previous - current).days == 1:
                streak += 1
            else:
                break
        except ValueError:
            break
    return streak


streak = _calculate_streak(st.session_state["visit_dates"])

# ── Auto-award streak achievements ───────────────────────────────────────────
if streak >= 7 and "streak_7" not in st.session_state["achievements"]:
    st.session_state["achievements"].add("streak_7")
    st.session_state["achievement_xp"] += 100
    st.balloons()
    st.success(t("🏆 Achievement Unlocked: **Week Warrior** (+100 XP)!"))

if streak >= 30 and "streak_30" not in st.session_state["achievements"]:
    st.session_state["achievements"].add("streak_30")
    st.session_state["achievement_xp"] += 500
    st.balloons()
    st.success(t("🏆 Achievement Unlocked: **Monthly Master** (+500 XP)!"))

# ── Sidebar stats ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(t("### 🏆 Your Achievements"))
    st.metric(t("Total XP"), st.session_state["achievement_xp"])
    st.metric(t("Badges Earned"), f"{len(st.session_state['achievements'])}/{len(ACHIEVEMENTS)}")
    st.metric(t("Current Streak"), f"🔥 {streak} days")
    st.metric(t("Tools Used"), len(st.session_state["tools_used"]))

# ── Badge gallery ────────────────────────────────────────────────────────────
st.subheader(t("🎖️ Badge Gallery"))

earned = st.session_state["achievements"]
locked_count = len(ACHIEVEMENTS) - len(earned)
st.progress(len(earned) / len(ACHIEVEMENTS), text=t("{earned} of {total} badges unlocked", earned=len(earned), total=len(ACHIEVEMENTS)))

for ach in ACHIEVEMENTS:
    is_unlocked = ach["id"] in earned
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            if is_unlocked:
                st.markdown(f"### {ach['icon']}")
            else:
                st.markdown("### 🔒")
        with col2:
            st.markdown(f"**{ach['name']}**")
            st.caption(t(ach["description"]))
            st.caption(t("Condition: {cond}", cond=ach["condition"]))
        with col3:
            if is_unlocked:
                st.success(t("✅ Unlocked"))
                st.caption(f"+{ach['xp']} XP")
            else:
                st.caption(t("🔒 Locked"))
                st.caption(f"+{ach['xp']} XP")

# ── Unlock buttons for testing/demo ──────────────────────────────────────────
st.markdown("---")
with st.expander(t("🛠️ Manual Badge Unlock (demo/testing)")):
    st.caption(t("Use these buttons to manually unlock badges for demonstration purposes."))
    for ach in ACHIEVEMENTS:
        if ach["id"] not in earned:
            if st.button(t("Unlock: {name}", name=ach["name"]), key=f"unlock_{ach['id']}"):
                st.session_state["achievements"].add(ach["id"])
                st.session_state["achievement_xp"] += ach["xp"]
                st.rerun()

# ── Reset ────────────────────────────────────────────────────────────────────
if st.button(t("🔄 Reset All Achievements"), type="secondary"):
    st.session_state["achievements"] = set()
    st.session_state["achievement_xp"] = 0
    st.rerun()

dr_titan_tip(
    "Gamification makes learning addictive in the best way! Each badge represents real knowledge "
    "you've gained. Keep exploring — the more tools you try, the more badges you'll earn!"
)