"""Epigenetics & Epitranscriptomics Console (Tools 153-172)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "🧬",
    "Epigenetics & Epitranscriptomics Console",
    "Chromatin accessibility, DNA bisulfite methylation, m6A RNA modifications, alternative splicing PSI, and volcano plots (Tools 153–172).",
)

tools = get_tools_by_category("epigenetics")
tool_map = {f"#{t.id} · {t.name}": t for t in tools}

selected_label = st.selectbox(
    "Select Epigenetics & RNA Tool:",
    options=list(tool_map.keys()),
    key="epi_console_tool_select"
)

spec = tool_map[selected_label]
render_tool_runner(spec, auto_run=True, key_prefix="epi_console")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 🎓 Student Guide to Beyond-the-DNA Genetics")
    st.markdown(
        "Epigenetics explains how cells with identical DNA (like a neuron and a skin cell) develop different phenotypes. "
        "Chemical tags on DNA (CpG methylation) and histones regulate gene expression without altering the sequence. "
        "Epitranscriptomics further studies mRNA modifications like m6A that dictate transcript stability and translation."
    )
