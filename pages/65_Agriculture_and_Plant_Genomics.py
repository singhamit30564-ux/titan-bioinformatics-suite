"""Agriculture & Plant Genomics Console (Tools 53-72)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "🌾",
    "Agriculture & Plant Genomics Console",
    "Comprehensive analytical suite for crop breeding, disease resistance, stress tolerance, and plant biotechnology (Tools 53–72).",
)

tools = get_tools_by_category("agri")
tool_map = {f"#{t.id} · {t.name}": t for t in tools}

selected_label = st.selectbox(
    "Select Plant Genomics Tool:",
    options=list(tool_map.keys()),
    key="agri_console_tool_select"
)

spec = tool_map[selected_label]
render_tool_runner(spec, auto_run=True, key_prefix="agri_console")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 🎓 Student Guide to Plant Genomics")
    st.markdown(
        "Plants have unique evolutionary adaptations: polyploid genomes, chloroplast plastids with inverted repeats, "
        "and extensive secondary metabolite clusters. Tools in this console help researchers and students track genetic "
        "markers for drought resistance, screen for disease resistance genes (NBS-LRR), and optimize photosynthetic efficiency."
    )
