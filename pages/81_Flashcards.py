"""🎴 Flashcards + SM-2-lite spaced repetition.

Persistence design (documented, per spec): review state (interval / ease /
due date per card) and custom cards are mirrored into the browser's
``localStorage`` through the small custom-component bridge in
:mod:`titan_utils.local_storage` — the **same** pattern this suite already
uses for the Classroom Quiz's local profile
(:mod:`titan_utils.classroom_storage`). We picked this over
``st.query_params`` persistence because query params would leak review
history into a shareable URL and have tight size/character limits, while a
localStorage blob keeps the whole SM-2-lite state private to the student's
own browser. ``st.session_state`` remains the source of truth while the app
is open; the browser bridge is best-effort and never blocks the page if
components are unavailable (e.g. under automated testing).
"""
from __future__ import annotations

import uuid
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from titan_utils.flashcards import (
    CardState,
    FLIP_CARD_CSS,
    due_cards,
    flip_card_html,
    load_seed_cards,
    merge_cards,
    new_card_state,
    progress_counts,
    sm2_update,
    validate_custom_card,
)
from titan_utils.i18n import t
from titan_utils.local_storage import sync_json_blob
from titan_utils.theme import THEME
from titan_utils.ui import dr_titan_tip, titan_title

STORAGE_KEY = "titan_flashcards_v1"

titan_title(
    "🎴",
    t("Flashcards & Spaced Repetition"),
    t("Daily review queue with an SM-2-lite scheduler — study a little, every day, and it sticks."),
)
st.markdown(FLIP_CARD_CSS, unsafe_allow_html=True)

# ── Session bootstrap: load seed deck + merge any browser-local state ───────
SEED_CARDS = load_seed_cards()

if "fc_states" not in st.session_state:
    st.session_state["fc_states"] = {}
if "fc_custom_cards" not in st.session_state:
    st.session_state["fc_custom_cards"] = []
if "fc_bootstrapped" not in st.session_state:
    restored = sync_json_blob(STORAGE_KEY, write=False, key="fc_storage_read") or {}
    if isinstance(restored.get("states"), dict):
        st.session_state["fc_states"] = dict(restored["states"])
    if isinstance(restored.get("custom"), list):
        st.session_state["fc_custom_cards"] = list(restored["custom"])
    st.session_state["fc_bootstrapped"] = True
    st.session_state["fc_dirty"] = False
if "fc_dirty" not in st.session_state:
    st.session_state["fc_dirty"] = False
if "fc_queue_pos" not in st.session_state:
    st.session_state["fc_queue_pos"] = 0


def _states() -> dict:
    return {cid: CardState.from_dict(s).as_dict() for cid, s in st.session_state["fc_states"].items()}


def _state_for(card_id: str) -> CardState:
    raw = st.session_state["fc_states"].get(card_id)
    return CardState.from_dict(raw) if raw else new_card_state(card_id)


def _persist() -> None:
    st.session_state["fc_dirty"] = True


ALL_CARDS = merge_cards(SEED_CARDS, st.session_state["fc_custom_cards"])
today = date.today()
QUEUE = due_cards(ALL_CARDS, {cid: CardState.from_dict(s) for cid, s in st.session_state["fc_states"].items()}, today)

# Persist any pending change to localStorage (best-effort, one call per run).
if st.session_state["fc_dirty"]:
    sync_json_blob(
        STORAGE_KEY,
        payload={"states": _states(), "custom": st.session_state["fc_custom_cards"]},
        write=True,
        key="fc_storage_write",
    )
    st.session_state["fc_dirty"] = False

tab_review, tab_manage, tab_progress = st.tabs([
    t("📅 Daily Review"), t("➕ Add / Edit / Delete"), t("📊 Progress"),
])

# ── Daily review queue ───────────────────────────────────────────────────
with tab_review:
    st.caption(t(
        "⏰ {due} of {total} cards are due today. New cards are due immediately; "
        "graded cards come back on their SM-2-lite schedule.",
        due=len(QUEUE), total=len(ALL_CARDS),
    ))
    if not QUEUE:
        st.success(t("🎉 Nothing due right now — come back tomorrow, or add new cards below."))
    else:
        pos = st.session_state["fc_queue_pos"] % len(QUEUE)
        card = QUEUE[pos]
        st.markdown(
            flip_card_html(card["id"], card["term"], card["definition"], card.get("chapter", "")),
            unsafe_allow_html=True,
        )
        st.caption(t("Card {pos} of {total} due today", pos=pos + 1, total=len(QUEUE)))

        grade_cols = st.columns(4)
        grades = [
            (t("😵 Again"), 1), (t("😅 Hard"), 3), (t("🙂 Good"), 4), (t("😎 Easy"), 5),
        ]
        for col, (label, quality) in zip(grade_cols, grades):
            if col.button(label, use_container_width=True, key=f"fc_grade_{quality}"):
                state = _state_for(card["id"])
                next_state = sm2_update(state, quality, today)
                st.session_state["fc_states"][card["id"]] = next_state.as_dict()
                st.session_state["fc_queue_pos"] = pos  # stay in place; queue recomputes next run
                _persist()
                st.success(t(
                    "Saved — next review on {due} (interval: {interval}d).",
                    due=next_state.due_date, interval=next_state.interval,
                ))
                st.rerun()

        nav_cols = st.columns(2)
        if nav_cols[0].button(t("⬅️ Previous card"), use_container_width=True, key="fc_prev_btn"):
            st.session_state["fc_queue_pos"] = (pos - 1) % len(QUEUE)
            st.rerun()
        if nav_cols[1].button(t("➡️ Skip to next"), use_container_width=True, key="fc_next_btn"):
            st.session_state["fc_queue_pos"] = (pos + 1) % len(QUEUE)
            st.rerun()

# ── Add / Edit / Delete custom cards ────────────────────────────────────
with tab_manage:
    st.markdown(t("#### ➕ Add a custom card"))
    chapters = sorted({c.get("chapter", "Custom") for c in ALL_CARDS}) or ["Custom"]
    with st.form("fc_add_form", clear_on_submit=True):
        new_term = st.text_input(t("Term"), key="fc_new_term")
        new_definition = st.text_area(t("Definition"), key="fc_new_definition", height=80)
        new_chapter = st.selectbox(t("Chapter tag"), options=chapters + [t("+ New chapter")], key="fc_new_chapter")
        custom_chapter = ""
        if new_chapter == t("+ New chapter"):
            custom_chapter = st.text_input(t("New chapter name"), key="fc_new_chapter_custom")
        add_clicked = st.form_submit_button(t("Add Card"), type="primary", use_container_width=True)

    if add_clicked:
        chapter_value = custom_chapter.strip() if new_chapter == t("+ New chapter") else new_chapter
        error = validate_custom_card(new_term, new_definition, chapter_value)
        if error:
            st.warning(f"⚠️ {t(error)}")
        else:
            card_id = f"custom-{uuid.uuid4().hex[:10]}"
            st.session_state["fc_custom_cards"].append({
                "id": card_id, "term": new_term.strip(), "definition": new_definition.strip(),
                "chapter": chapter_value,
            })
            _persist()
            st.success(t("✅ Added '{term}' to your deck.", term=new_term.strip()))
            st.rerun()

    st.markdown("---")
    st.markdown(t("#### ✏️ Your custom cards"))
    custom_cards = st.session_state["fc_custom_cards"]
    if not custom_cards:
        st.caption(t("No custom cards yet — add one above. The 50-card seed deck is read-only."))
    else:
        labels = {f"{c['term']} ({c['chapter']})": c["id"] for c in custom_cards}
        selected_label = st.selectbox(t("Select a custom card to edit/delete"), options=list(labels.keys()), key="fc_edit_select")
        selected_id = labels[selected_label]
        selected_card = next(c for c in custom_cards if c["id"] == selected_id)

        edit_term = st.text_input(t("Edit term"), value=selected_card["term"], key="fc_edit_term")
        edit_definition = st.text_area(t("Edit definition"), value=selected_card["definition"], key="fc_edit_definition", height=80)

        edit_cols = st.columns(2)
        if edit_cols[0].button(t("💾 Save changes"), use_container_width=True, key="fc_save_btn"):
            error = validate_custom_card(edit_term, edit_definition, selected_card["chapter"])
            if error:
                st.warning(f"⚠️ {t(error)}")
            else:
                selected_card["term"] = edit_term.strip()
                selected_card["definition"] = edit_definition.strip()
                _persist()
                st.success(t("✅ Updated."))
                st.rerun()
        if edit_cols[1].button(t("🗑️ Delete card"), use_container_width=True, key="fc_delete_btn"):
            st.session_state["fc_custom_cards"] = [c for c in custom_cards if c["id"] != selected_id]
            st.session_state["fc_states"].pop(selected_id, None)
            _persist()
            st.success(t("🗑️ Deleted."))
            st.rerun()

# ── Progress chart ───────────────────────────────────────────────────────
with tab_progress:
    counts = progress_counts(ALL_CARDS, {cid: CardState.from_dict(s) for cid, s in st.session_state["fc_states"].items()}, today)
    metric_cols = st.columns(4)
    metric_cols[0].metric(t("Total Cards"), counts["total"])
    metric_cols[1].metric(t("Due Today"), counts["due"])
    metric_cols[2].metric(t("Reviewed"), counts["reviewed"])
    metric_cols[3].metric(t("Mastered"), counts["mastered"])

    fig = go.Figure(data=[go.Bar(
        x=[t("New"), t("Reviewed"), t("Due Today"), t("Mastered")],
        y=[counts["new"], counts["reviewed"], counts["due"], counts["mastered"]],
        marker_color=[THEME["muted"], THEME["cyan"], THEME["gold"], THEME["green"]],
    )])
    fig.update_layout(
        title=t("Flashcard Progress"),
        paper_bgcolor=THEME["bg_card"], plot_bgcolor=THEME["bg_card"],
        font_color=THEME["text"], yaxis_title=t("Cards"),
    )
    st.plotly_chart(fig, use_container_width=True)

    by_chapter = pd.DataFrame(ALL_CARDS).groupby("chapter").size().reset_index(name="cards")
    st.markdown(t("#### 📚 Cards per chapter"))
    st.dataframe(by_chapter, use_container_width=True, hide_index=True)

dr_titan_tip(
    "Spaced repetition beats cramming: SM-2-lite spaces reviews further apart "
    "every time you answer correctly, so you spend less time on cards you "
    "already know and more on the ones you don't."
)
