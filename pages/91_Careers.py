"""🚀 Career Explorer — 12 bioinformatics careers with details, skills, and paths.

Data from data/careers.json — covers what they do, required skills, India
colleges, entrance exams, salary ranges (approx, labelled), and day-in-the-life.
"""
from __future__ import annotations

import json
import pathlib

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🚀",
    "Career Explorer",
    "Explore 12 exciting careers in bioinformatics and life sciences — what they do, skills needed, colleges, and salary ranges.",
)

st.caption(t("ℹ️ Salary ranges are **approximate** (indicative, not guaranteed). Actual pay varies by company, location, and experience."))

# ── Load data ────────────────────────────────────────────────────────────────
DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "careers.json"
with open(DATA_PATH, encoding="utf-8") as fh:
    CAREERS: list[dict] = json.load(fh)

# ── Search / Filter ──────────────────────────────────────────────────────────
search = st.text_input(t("🔍 Search careers:"), placeholder="e.g. genomics, AI, clinical...")

filtered = CAREERS
if search.strip():
    search_lower = search.lower()
    filtered = [
        c for c in CAREERS
        if search_lower in c["title"].lower()
        or search_lower in c["what_they_do"].lower()
        or any(search_lower in s.lower() for s in c["skills"])
    ]

if not filtered:
    st.info(t("No careers match your search. Try different keywords!"))
else:
    for career in filtered:
        with st.expander(f"{career['icon']} **{career['title']}**", expanded=False):
            st.markdown(f"### {career['icon']} {career['title']}")

            st.markdown(f"**🎯 What they do:**")
            st.write(t(career["what_they_do"]))

            st.markdown(f"**🛠️ Key Skills:**")
            skills_html = " ".join(f"`{s}`" for s in career["skills"])
            st.markdown(skills_html)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**🏫 Top India Colleges/Institutes:**")
                for college in career["india_colleges"]:
                    st.markdown(f"- {college}")

                st.markdown(f"**📝 Entrance Exams:**")
                for exam in career["entrance_exams"]:
                    st.markdown(f"- {exam}")

            with col2:
                st.markdown(f"**💰 Salary Range (approximate):**")
                st.info(career["salary_range"])

                st.markdown(f"**📅 A Day in the Life:**")
                st.write(t(career["day_in_life"]))

    st.markdown("---")
    st.caption(t(f"Showing {len(filtered)} of {len(CAREERS)} careers."))

# ── Career quiz teaser ───────────────────────────────────────────────────────
st.markdown("---")
with st.container(border=True):
    st.markdown(t("### 🧭 Which career suits you?"))
    st.write(t("Answer a few questions to get a personalised career suggestion!"))
    col1, col2 = st.columns(2)
    with col1:
        pref = st.radio(t("I prefer:"), [t("Working with data & code"), t("Working with patients & people"), t("Working in a wet lab"), t("Teaching & communication")], label_visibility="visible")
    with col2:
        subject = st.radio(t("Favourite subject:"), [t("Computer Science"), t("Biology"), t("Chemistry"), t("Mathematics")], label_visibility="visible")

    if st.button(t("🔮 Suggest My Career"), type="primary"):
        suggestion = "Bioinformatician"
        if "patients" in pref or "लोग" in pref:
            suggestion = "Genetic Counselor"
        elif "wet lab" in pref or "प्रयोगशाला" in pref:
            suggestion = "Structural Biologist"
        elif "Teaching" in pref or "शिक्षण" in pref:
            suggestion = "Science Communicator / Educator"
        elif "Mathematics" in subject or "गणित" in subject:
            suggestion = "Biostatistician"
        elif "Computer" in subject or "कंप्यूटर" in subject:
            suggestion = "Biomedical Data Scientist"
        st.success(t("🎯 Based on your preferences, consider: **{career}**", career=suggestion))
        st.caption(t("This is a simple suggestion — explore all careers above for more details!"))

dr_titan_tip(
    "Bioinformatics is one of the fastest-growing fields! You don't need to choose just one path — "
    "many professionals combine skills from multiple careers. Start learning Python and biology today!"
)