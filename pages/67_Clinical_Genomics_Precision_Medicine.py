"""Clinical Genomics & Precision Medicine Console (Tools 93-112)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "🩺",
    "Clinical Genomics & Precision Medicine Console",
    "Diagnostic intelligence for ACMG variant classification, cancer driver hotspots, pharmacogenomics (PGx), and liquid biopsy (Tools 93–112).",
)

tools = get_tools_by_category("clinical")
tool_map = {f"#{t.id} · {t.name}": t for t in tools}

selected_label = st.selectbox(
    "Select Clinical Genomics Tool:",
    options=list(tool_map.keys()),
    key="clinical_console_tool_select"
)

spec = tool_map[selected_label]
render_tool_runner(spec, auto_run=True, key_prefix="clinical_console")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 🎓 Student Guide to Medical Genetics")
    st.markdown(
        "Precision medicine personalizes healthcare by analyzing patients' individual DNA profiles. "
        "Learn how ACMG rules guide variant classification, how CYP enzyme star-alleles alter drug metabolism, "
        "and how circulating tumor DNA (ctDNA) in liquid biopsies tracks cancer recurrence non-invasively."
    )
