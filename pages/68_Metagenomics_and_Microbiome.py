"""Metagenomics & Microbiome Console (Tools 113-132)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "🦠",
    "Metagenomics & Microbiome Console",
    "Microbial community profiling, 16S in-silico PCR, alpha/beta diversity, antibiotic resistomes, and wastewater surveillance (Tools 113–132).",
)

tools = get_tools_by_category("metagenomics")
tool_map = {f"#{t.id} · {t.name}": t for t in tools}

selected_label = st.selectbox(
    "Select Metagenomics Tool:",
    options=list(tool_map.keys()),
    key="meta_console_tool_select"
)

spec = tool_map[selected_label]
render_tool_runner(spec, auto_run=True, key_prefix="meta_console")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 🎓 Student Guide to the Microbiome")
    st.markdown(
        "Trillions of microbes inhabit our bodies, soils, and oceans. Metagenomics bypasses the need to culture microbes in petri dishes "
        "by sequencing total community DNA directly. Understand alpha diversity (species richness within a sample) vs beta diversity "
        "(compositional divergence between habitats) and trace antimicrobial resistance genes across ecosystems."
    )
