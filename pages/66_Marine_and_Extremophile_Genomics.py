"""Marine & Extremophile Genomics Console (Tools 73-92)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "🌊",
    "Marine & Extremophile Genomics Console",
    "Exploration tools for ocean biodiversity, hydrothermal vents, coral reef bleaching, bioluminescence, and deep-sea barophiles (Tools 73–92).",
)

tools = get_tools_by_category("marine")
tool_map = {f"#{t.id} · {t.name}": t for t in tools}

selected_label = st.selectbox(
    "Select Marine Genomics Tool:",
    options=list(tool_map.keys()),
    key="marine_console_tool_select"
)

spec = tool_map[selected_label]
render_tool_runner(spec, auto_run=True, key_prefix="marine_console")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 🎓 Student Guide to Ocean & Extremophile Life")
    st.markdown(
        "Over 70% of Earth is ocean, harboring extremophiles that thrive at freezing temperatures (AFGP antifreeze proteins), "
        "crushing hydrostatic pressure (piezophilic desaturases), and pitch darkness (lux bioluminescent operons). "
        "Use this console to investigate marine biology, ocean acidification, and environmental DNA (eDNA) biodiversity."
    )
