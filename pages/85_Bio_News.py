"""📰 Bio-News Feed — 30 curated bioinformatics headlines with Dr. Titan summaries.

Data sourced from static JSON (no live API). Category filter and Dr. Titan
Hinglish summaries included.
"""
from __future__ import annotations

import json
import pathlib
import random

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "📰",
    "Bio-News Feed",
    "Stay updated with the latest in genomics, proteins, and AI-in-biology — curated for students.",
)

# ── Load data ────────────────────────────────────────────────────────────────
DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "bionews.json"
with open(DATA_PATH, encoding="utf-8") as fh:
    NEWS: list[dict] = json.load(fh)

CATEGORIES = sorted(set(item["category"] for item in NEWS))

# ── Hinglish summary generator (template-based, offline) ─────────────────────
_HINGLISH_TEMPLATES = [
    "Yaar, ye research bahut cool hai — {title}. Matlab basically scientists ne ek bada kadam uthaya hai {category} mein! 🔬",
    "Sun sun! 🧬 {title}. Iska matlab hai ki hum ab {category} mein pehle se zyada samajhdaar ho gaye hain, bhai!",
    "Bhai log, ek mast news hai: {title}. Ye discovery students ke liye bahut important hai — {category} ke field mein game changer! 🚀",
    "Dr. Titan bolta hai: {title}. Ye padho aur samjho — {category} ka future badal raha hai! 💡",
]


def _hinglish_summary(item: dict) -> str:
    """Produce a 2-line Hinglish summary from the news item."""
    template = random.choice(_HINGLISH_TEMPLATES)
    return template.format(title=item["title"][:80], category=item["category"])


# ── Filter UI ────────────────────────────────────────────────────────────────
col_filter, col_refresh = st.columns([3, 1])
with col_filter:
    selected_cat = st.multiselect(
        t("Filter by category:"),
        options=CATEGORIES,
        default=CATEGORIES,
    )
with col_refresh:
    st.markdown("<br>", unsafe_allow_html=True)
    refresh = st.button(t("🔄 Refresh"), use_container_width=True)

if refresh:
    random.shuffle(NEWS)

# ── Display news cards ───────────────────────────────────────────────────────
filtered = [item for item in NEWS if item["category"] in selected_cat]
if not filtered:
    st.warning(t("No news items match the selected categories."))
else:
    for item in filtered:
        with st.container(border=True):
            cat_emoji = {"genomics": "🧬", "proteins": "🥩", "AI-in-bio": "🤖"}.get(item["category"], "📰")
            st.markdown(f"### {cat_emoji} {item['title']}")
            st.caption(f"📰 **{item['source']}** · 📅 {item['date']} · 🏷️ {item['category']}")
            st.write(t(item["summary"]))
            with st.expander(t("🗣️ Dr. Titan ka Hinglish Summary")):
                st.info(_hinglish_summary(item))

st.markdown("---")
st.caption(t(
    "ℹ️ News data is **statically curated** (manually collected headlines). "
    "No live API calls are made. Last curated set covers 2024 bioinformatics highlights."
))

dr_titan_tip(
    "Reading scientific news regularly is one of the best habits for a young scientist. "
    "Follow Nature, Science, and bioRxiv on social media to stay current!"
)