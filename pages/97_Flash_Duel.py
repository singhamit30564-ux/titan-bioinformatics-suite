"""🧠 Bio-Flash Duel — 2-player hotseat flashcard duel on the same screen.

10 cards, alternating players, +10/-5 scoring. Winner screen with a
taunt line from Dr. Titan. Uses existing flashcards data.
"""
from __future__ import annotations

import json
import pathlib
import random

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🧠",
    "Bio-Flash Duel",
    "Two players, one screen, 10 flashcards — who knows biology better? Take turns, score points, and see who wins!",
)

# ── Load flashcards ──────────────────────────────────────────────────────────
DATA_PATH = pathlib.Path(__file__).resolve().parents[1] / "data" / "flashcards.json"
with open(DATA_PATH, encoding="utf-8") as fh:
    ALL_CARDS: list[dict] = json.load(fh)

# ── Dr. Titan taunt lines ────────────────────────────────────────────────────
TAUNTS_WINNER = [
    "🏆 Dr. Titan says: 'Impressive! But can you handle the advanced cards next time?'",
    "🏆 Dr. Titan says: 'You've got the genes for greatness! (pun intended)'",
    "🏆 Dr. Titan says: 'That was CRISPR-precise knowledge! Well done!'",
    "🏆 Dr. Titan says: 'Your brain is firing on all neurons! Champion!'",
]
TAUNTS_LOSER = [
    "😅 Dr. Titan says: 'Don't worry — even Watson and Crick made mistakes. Study and rematch!'",
    "😅 Dr. Titan says: 'Time to review those flashcards! Knowledge compounds like PCR cycles.'",
    "😅 Dr. Titan says: 'Every great scientist failed first. Come back stronger!'",
    "😅 Dr. Titan says: 'Your opponent had a selective advantage today. Evolve and retry!'",
]
TAUNTS_DRAW = [
    "🤝 Dr. Titan says: 'A perfect equilibrium — like Hardy-Weinberg! Rematch?'",
    "🤝 Dr. Titan says: 'Neither of you blinked! Truly co-dominant performance.'",
]

# ── Session state ────────────────────────────────────────────────────────────
if "duel_state" not in st.session_state:
    st.session_state["duel_state"] = "setup"  # setup, playing, result
if "duel_players" not in st.session_state:
    st.session_state["duel_players"] = ("Player 1", "Player 2")
if "duel_scores" not in st.session_state:
    st.session_state["duel_scores"] = [0, 0]
if "duel_current" not in st.session_state:
    st.session_state["duel_current"] = 0
if "duel_turn" not in st.session_state:
    st.session_state["duel_turn"] = 0  # 0 or 1
if "duel_cards" not in st.session_state:
    st.session_state["duel_cards"] = []
if "duel_answered" not in st.session_state:
    st.session_state["duel_answered"] = False
if "duel_last_correct" not in st.session_state:
    st.session_state["duel_last_correct"] = None

NUM_CARDS = 10

# ── SETUP ────────────────────────────────────────────────────────────────────
if st.session_state["duel_state"] == "setup":
    st.subheader(t("👥 Player Setup"))
    col1, col2 = st.columns(2)
    with col1:
        p1 = st.text_input(t("Player 1 Name:"), value="Player 1", key="p1_name")
    with col2:
        p2 = st.text_input(t("Player 2 Name:"), value="Player 2", key="p2_name")

    st.markdown(t("""
    **Rules:**
    - 10 flashcards — players take turns
    - **Correct answer:** +10 points
    - **Wrong answer:** −5 points
    - You see the **term** — guess the **definition**
    - Player with the most points wins!
    """))

    if st.button(t("🎮 Start Duel!"), type="primary", use_container_width=True):
        cards = random.sample(ALL_CARDS, min(NUM_CARDS, len(ALL_CARDS)))
        st.session_state["duel_players"] = (p1 or "Player 1", p2 or "Player 2")
        st.session_state["duel_scores"] = [0, 0]
        st.session_state["duel_current"] = 0
        st.session_state["duel_turn"] = 0
        st.session_state["duel_cards"] = cards
        st.session_state["duel_answered"] = False
        st.session_state["duel_state"] = "playing"
        st.rerun()

# ── PLAYING ──────────────────────────────────────────────────────────────────
elif st.session_state["duel_state"] == "playing":
    cards = st.session_state["duel_cards"]
    current = st.session_state["duel_current"]
    turn = st.session_state["duel_turn"]
    p1, p2 = st.session_state["duel_players"]
    scores = st.session_state["duel_scores"]

    if current >= len(cards):
        st.session_state["duel_state"] = "result"
        st.rerun()

    card = cards[current]

    # Status bar
    col1, col2, col3 = st.columns(3)
    col1.metric(f"👤 {p1}", scores[0])
    col2.metric(t("Card"), f"{current + 1}/{len(cards)}")
    col3.metric(f"👤 {p2}", scores[1])

    current_player = p1 if turn == 0 else p2
    st.markdown(f"### 🎯 {t('It is')} **{current_player}**'s {t('turn!')}")
    st.markdown("---")

    # Show the term (question side)
    with st.container(border=True):
        st.markdown(f"## 🃏 **{card['term']}**")
        st.caption(f"📖 Chapter: {card.get('chapter', 'General')}")

    if not st.session_state["duel_answered"]:
        st.markdown(t("### Do you know the definition?"))
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t("✅ I know it!"), type="primary", use_container_width=True):
                # Show answer — player claims they know it
                scores[turn] += 10
                st.session_state["duel_scores"] = scores
                st.session_state["duel_answered"] = True
                st.session_state["duel_last_correct"] = True
                st.rerun()
        with col2:
            if st.button(t("❌ I don't know"), use_container_width=True):
                scores[turn] -= 5
                st.session_state["duel_scores"] = scores
                st.session_state["duel_answered"] = True
                st.session_state["duel_last_correct"] = False
                st.rerun()
    else:
        # Show answer
        correct = st.session_state["duel_last_correct"]
        if correct:
            st.success(t("✅ Correct! +10 points"))
        else:
            st.error(t("❌ Wrong! −5 points"))

        st.info(f"📖 **Definition:** {card['definition']}")

        if st.button(t("➡️ Next Card"), type="primary", use_container_width=True):
            st.session_state["duel_answered"] = False
            st.session_state["duel_current"] += 1
            st.session_state["duel_turn"] = 1 - turn  # alternate
            st.rerun()

# ── RESULTS ──────────────────────────────────────────────────────────────────
elif st.session_state["duel_state"] == "result":
    p1, p2 = st.session_state["duel_players"]
    s1, s2 = st.session_state["duel_scores"]

    st.markdown("---")
    st.markdown("### 🏆 Duel Results!")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.markdown(f"## 👤 {p1}")
            st.markdown(f"### ⭐ {s1} points")
    with col2:
        with st.container(border=True):
            st.markdown(f"## 👤 {p2}")
            st.markdown(f"### ⭐ {s2} points")

    if s1 > s2:
        st.balloons()
        st.success(t("🎉 **{winner} WINS!** {loser} needs to study more!", winner=p1, loser=p2))
        taunt = random.choice(TAUNTS_WINNER)
    elif s2 > s1:
        st.balloons()
        st.success(t("🎉 **{winner} WINS!** {loser} needs to study more!", winner=p2, loser=p1))
        taunt = random.choice(TAUNTS_WINNER)
    else:
        st.info(t("🤝 **It's a DRAW!** Both players are equally matched!"))
        taunt = random.choice(TAUNTS_DRAW)

    st.markdown(f"### {taunt}")

    # Share text
    share = f"🧠 {p1} ({s1}pts) vs {p2} ({s2}pts) — Bio-Flash Duel on Titan Bioinformatics Suite! Who wins next? 🧬"
    st.code(share)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("🔄 Rematch"), type="primary", use_container_width=True):
            st.session_state["duel_state"] = "setup"
            st.rerun()
    with col2:
        if st.button(t("🏠 New Game"), use_container_width=True):
            st.session_state["duel_state"] = "setup"
            st.rerun()

dr_titan_tip(
    "Spaced repetition and active recall are the two most powerful study techniques. "
    "Testing yourself (or competing with a friend!) is far more effective than re-reading notes."
)