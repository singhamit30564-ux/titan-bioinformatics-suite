"""Synthetic Biology & Metabolic Engineering Console (Tools 173-192)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "⚙️",
    "Synthetic Biology & Metabolic Engineering Console",
    "In-silico genetic circuit design, Gibson & Golden Gate assembly, genetic toggle switches, cell-free TX-TL, and FBA (Tools 173–192).",
)

tools = get_tools_by_category("synthetic")
tool_map = {f"#{t.id} · {t.name}": t for t in tools}

selected_label = st.selectbox(
    "Select Synthetic Biology Tool:",
    options=list(tool_map.keys()),
    key="syn_console_tool_select"
)

spec = tool_map[selected_label]
render_tool_runner(spec, auto_run=True, key_prefix="syn_console")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 🎓 Student Guide to Engineering Living Systems")
    st.markdown(
        "Synthetic biology treats biology as an engineering discipline with standardized genetic parts (BioBricks, MoClo). "
        "Learn how genetic toggle switches store cellular memory, how repressilators mimic circadian biological clocks, "
        "and how Flux Balance Analysis (FBA) optimizes cellular factories to produce sustainable biofuels and pharmaceuticals."
    )
