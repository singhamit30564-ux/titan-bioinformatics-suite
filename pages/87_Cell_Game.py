"""🎮 Cell Survival Game — Dodge viruses, collect nutrients, survive 60 seconds.

Simulated in Streamlit (no actual game engine). Player controls a cell,
dodges viruses, collects nutrients. Facts pop between waves. Score + share.
"""
from __future__ import annotations

import random
import time

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🎮",
    "Cell Survival Game",
    "You are a cell! Dodge viruses, collect nutrients, and survive for 60 seconds. Learn biology facts between waves!",
)

# ── Biology facts between waves ──────────────────────────────────────────────
FACTS = [
    "🧬 Mitochondria have their own DNA — inherited only from your mother!",
    "🦠 A single sneeze can release 40,000 virus-laden droplets.",
    "💪 Your body makes about 3.8 million red blood cells every second.",
    "🧪 The human genome contains roughly 3 billion base pairs.",
    "🔬 A human cell contains about 42 million protein molecules.",
    "🌿 Chloroplasts were once free-living cyanobacteria that were absorbed by a plant ancestor!",
    "🧬 DNA in all your cells, stretched end to end, would reach the Sun and back ~600 times.",
    "🦠 Bacteria in your body outnumber your own cells by roughly 1.3:1.",
    "⚡ Neurons can fire electrical signals at speeds up to 120 m/s!",
    "🧪 CRISPR was discovered in bacteria as a defence against viruses.",
    "🔬 Your body replaces about 330 billion cells per day.",
    "🧬 Telomeres shorten every time a cell divides — they're like a countdown clock.",
]

# ── Session state ────────────────────────────────────────────────────────────
if "cell_game_state" not in st.session_state:
    st.session_state["cell_game_state"] = "menu"  # menu, playing, gameover, fact
if "cell_game_score" not in st.session_state:
    st.session_state["cell_game_score"] = 0
if "cell_game_health" not in st.session_state:
    st.session_state["cell_game_health"] = 100
if "cell_game_wave" not in st.session_state:
    st.session_state["cell_game_wave"] = 0
if "cell_game_timer" not in st.session_state:
    st.session_state["cell_game_timer"] = 60
if "cell_game_high_score" not in st.session_state:
    st.session_state["cell_game_high_score"] = 0
if "cell_game_fact" not in st.session_state:
    st.session_state["cell_game_fact"] = ""

state = st.session_state["cell_game_state"]

# ── GAME MENU ────────────────────────────────────────────────────────────────
if state == "menu":
    st.markdown("### 🎮 Welcome, brave cell!")
    with st.container(border=True):
        st.markdown(t("""
**How to play:**
- You are a **cell** floating in the bloodstream 🧫
- **Viruses** 🦠 try to infect you — dodge them!
- **Nutrients** 🍎 heal you and give points
- Survive for **60 seconds** to win!
- Every 15 seconds, a new wave of viruses appears
        """))
        st.caption(t("⚠️ This is a **simulated** text-based game — not a real-time video game."))

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("🎮 Start Game"), type="primary", use_container_width=True):
            st.session_state["cell_game_state"] = "playing"
            st.session_state["cell_game_score"] = 0
            st.session_state["cell_game_health"] = 100
            st.session_state["cell_game_wave"] = 1
            st.session_state["cell_game_timer"] = 60
            st.rerun()
    with col2:
        hs = st.session_state["cell_game_high_score"]
        st.metric(t("🏆 High Score"), hs)

    dr_titan_tip(
        "Cells face threats every day! Your immune system has T-cells, B-cells, and "
        "NK cells patrolling your body 24/7 — they're the real cell survival game champions!"
    )

# ── GAME PLAYING ─────────────────────────────────────────────────────────────
elif state == "playing":
    health = st.session_state["cell_game_health"]
    score = st.session_state["cell_game_score"]
    wave = st.session_state["cell_game_wave"]
    timer = st.session_state["cell_game_timer"]

    # Status bar
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("❤️ Health"), f"{health}%")
    col2.metric(t("⭐ Score"), score)
    col3.metric(t("🌊 Wave"), wave)
    col4.metric(t("⏱️ Timer"), f"{timer}s")

    # Health bar
    bar_color = "normal" if health > 50 else ("off" if health > 20 else None)
    st.progress(health / 100)

    st.markdown("---")

    # Game grid (simplified text-based)
    grid_size = 5
    grid = [["⬜" for _ in range(grid_size)] for _ in range(grid_size)]

    # Place player cell
    player_pos = st.session_state.get("cell_player_pos", (2, 2))
    grid[player_pos[0]][player_pos[1]] = "🧫"

    # Place viruses (more in later waves)
    num_viruses = min(wave + 1, 6)
    virus_positions = st.session_state.get("cell_virus_positions", [])
    for vr, vc in virus_positions:
        if 0 <= vr < grid_size and 0 <= vc < grid_size:
            grid[vr][vc] = "🦠"

    # Place nutrients
    num_nutrients = max(1, 3 - wave // 2)
    nutrient_positions = st.session_state.get("cell_nutrient_positions", [])
    for nr, nc in nutrient_positions:
        if 0 <= nr < grid_size and 0 <= nc < grid_size and grid[nr][nc] == "⬜":
            grid[nr][nc] = "🍎"

    # Render grid
    grid_str = "\n".join(" ".join(row) for row in grid)
    st.code(grid_str, language=None)

    st.markdown(t("### Move your cell:"))
    cols = st.columns(5)

    def _move(dr: int, dc: int) -> None:
        r, c = player_pos
        nr, nc = max(0, min(grid_size - 1, r + dr)), max(0, min(grid_size - 1, c + dc))
        st.session_state["cell_player_pos"] = (nr, nc)
        _resolve_move(nr, nc)

    def _resolve_move(nr: int, nc: int) -> None:
        # Check virus hit
        viruses = st.session_state.get("cell_virus_positions", [])
        if (nr, nc) in viruses:
            st.session_state["cell_game_health"] = max(0, st.session_state["cell_game_health"] - 25)
            viruses.remove((nr, nc))
            st.session_state["cell_virus_positions"] = viruses
        # Check nutrient
        nutrients = st.session_state.get("cell_nutrient_positions", [])
        if (nr, nc) in nutrients:
            st.session_state["cell_game_health"] = min(100, st.session_state["cell_game_health"] + 15)
            st.session_state["cell_game_score"] += 10
            nutrients.remove((nr, nc))
            st.session_state["cell_nutrient_positions"] = nutrients
        # Check health
        if st.session_state["cell_game_health"] <= 0:
            st.session_state["cell_game_state"] = "gameover"
        # Advance timer
        st.session_state["cell_game_timer"] = max(0, st.session_state["cell_game_timer"] - 5)
        if st.session_state["cell_game_timer"] <= 0:
            st.session_state["cell_game_state"] = "gameover"
        # Advance wave
        if st.session_state["cell_game_timer"] % 15 == 0:
            st.session_state["cell_game_wave"] += 1
            _spawn_entities()
        st.rerun()

    with cols[0]:
        if st.button("⬅️", use_container_width=True):
            _move(0, -1)
    with cols[1]:
        if st.button("⬆️", use_container_width=True):
            _move(-1, 0)
    with cols[2]:
        if st.button("⬇️", use_container_width=True):
            _move(1, 0)
    with cols[3]:
        if st.button("➡️", use_container_width=True):
            _move(0, 1)
    with cols[4]:
        if st.button(t("⏸️ Wait"), use_container_width=True):
            _resolve_move(player_pos[0], player_pos[1])

    if st.button(t("🛑 End Game")):
        st.session_state["cell_game_state"] = "gameover"
        st.rerun()

# ── GAME OVER ────────────────────────────────────────────────────────────────
elif state == "gameover":
    score = st.session_state["cell_game_score"]
    if score > st.session_state["cell_game_high_score"]:
        st.session_state["cell_game_high_score"] = score
        st.balloons()
        st.success(t("🏆 NEW HIGH SCORE: {score}!", score=score))
    else:
        st.markdown(f"### 🎮 Game Over! Score: {score}")

    fact = random.choice(FACTS)
    st.session_state["cell_game_fact"] = fact

    with st.container(border=True):
        st.markdown(t("### 🧠 Did you know?"))
        st.info(fact)

    # Share text
    share_text = f"🎮 I scored {score} in Titan's Cell Survival Game! Can you beat me? Play at Titan Bioinformatics Suite 🧬"
    st.code(share_text)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("🔄 Play Again"), type="primary", use_container_width=True):
            st.session_state["cell_game_state"] = "menu"
            st.rerun()
    with col2:
        if st.button(t("🏠 Back to Menu"), use_container_width=True):
            st.session_state["cell_game_state"] = "menu"
            st.rerun()


def _spawn_entities() -> None:
    """Spawn new viruses and nutrients on the grid."""
    wave = st.session_state["cell_game_wave"]
    grid_size = 5
    viruses = []
    for _ in range(min(wave + 1, 6)):
        r, c = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)
        viruses.append((r, c))
    nutrients = []
    for _ in range(max(1, 3 - wave // 2)):
        r, c = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)
        nutrients.append((r, c))
    st.session_state["cell_virus_positions"] = viruses
    st.session_state["cell_nutrient_positions"] = nutrients