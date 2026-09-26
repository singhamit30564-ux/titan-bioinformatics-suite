"""Structural Biology & Biophysics Console (Tools 133-152)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "📐",
    "Structural Biology & Biophysics Console",
    "Macromolecular structure validation, Ramachandran dihedrals, AlphaFold pLDDT, docking energetics, and SASA (Tools 133–152).",
)

tools = get_tools_by_category("structural")
tool_map = {f"#{t.id} · {t.name}": t for t in tools}

selected_label = st.selectbox(
    "Select Structural Biology Tool:",
    options=list(tool_map.keys()),
    key="struct_console_tool_select"
)

spec = tool_map[selected_label]
render_tool_runner(spec, auto_run=True, key_prefix="struct_console")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 🎓 Student Guide to 3D Macromolecular Structure")
    st.markdown(
        "Proteins are 3D molecular machines whose function depends strictly on their 3D fold. "
        "Explore how backbone dihedral angles (phi and psi) determine secondary structures in Ramachandran space, "
        "how AlphaFold revolutionized structure prediction, and how ligand-binding pockets are targeted in rational drug design."
    )
