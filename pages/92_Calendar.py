"""📅 Science Calendar — Real events with countdown badges and Google Calendar links.

Data from data/events.json — includes exams, olympiads, science fairs, and
key science dates. Each event has a "Add to Google Calendar" link.
"""
from __future__ import annotations

import json
import pathlib
from datetime import date, datetime

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "📅",
    "Science Calendar",
    "Never miss an important science event, exam, or olympiad — with countdown badges and Google Calendar links!",
)

# ── Load events ──────────────────────────────────────────────────────────────
DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "events.json"
with open(DATA_PATH, encoding="utf-8") as fh:
    EVENTS: list[dict] = json.load(fh)

today = date.today()

# ── Category filter ──────────────────────────────────────────────────────────
CATEGORIES = sorted(set(e["category"] for e in EVENTS))
cat_emojis = {"exam": "📝", "olympiad": "🏆", "science_fair": "🔬"}
selected_cats = st.multiselect(
    t("Filter by category:"),
    options=CATEGORIES,
    default=CATEGORIES,
)

filtered = [e for e in EVENTS if e["category"] in selected_cats]


def _countdown(event_date_str: str) -> tuple[int, str]:
    """Return (days_remaining, label) — negative means past."""
    try:
        event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
    except ValueError:
        return 0, "Unknown"
    delta = (event_date - today).days
    return delta, f"{delta}d"


def _gcal_link(event: dict) -> str:
    """Generate a Google Calendar add-event URL."""
    try:
        dt = datetime.strptime(event["date"], "%Y-%m-%d")
    except ValueError:
        return "#"
    start = dt.strftime("%Y%m%d")
    end = dt.strftime("%Y%m%d")
    title = event["name"].replace(" ", "+")
    details = event.get("description", "").replace(" ", "+")
    return (
        f"https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={title}&dates={start}/{end}"
        f"&details={details}&sf=true"
    )


# ── Display events ───────────────────────────────────────────────────────────
if not filtered:
    st.warning(t("No events match the selected categories."))
else:
    # Sort by date
    filtered_sorted = sorted(filtered, key=lambda e: e["date"])

    for event in filtered_sorted:
        emoji = cat_emojis.get(event["category"], "📅")
        days, countdown_label = _countdown(event["date"])

        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                st.markdown(f"### {emoji} {event['name']}")
                st.caption(f"📅 {event['date']} · 🏷️ {event['category']}")
                st.write(t(event.get("description", "")))
            with col2:
                if days > 0:
                    st.markdown(f"### 🔥 {countdown_label}")
                    st.caption(t("until event"))
                elif days == 0:
                    st.markdown("### 🎉 TODAY!")
                else:
                    st.markdown(f"### ⏪ {-days}d ago")
                    st.caption(t("past event"))
            with col3:
                gcal = _gcal_link(event)
                st.link_button(t("📅 Add to GCal"), gcal, use_container_width=True)

st.markdown("---")
st.caption(t(
    "ℹ️ Event dates are based on recurring patterns and official announcements. "
    "Always verify exact dates on the official website before making plans."
))

dr_titan_tip(
    "Planning is key for competitive exams! Mark important dates early, "
    "set reminders, and work backwards from the exam date to create a study schedule."
)