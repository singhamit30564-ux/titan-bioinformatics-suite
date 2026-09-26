"""NCBI & Global Bioinformatics APIs Console (Tools 213-232)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "🌐",
    "NCBI & Global Bioinformatics APIs Console",
    "Direct live access to NCBI Entrez, GenBank, PubMed, ClinVar, UniProt, Ensembl, PubChem, and KEGG (Tools 213–232).",
)

tools = get_tools_by_category("ncbi")
tool_map = {f"#{t.id} · {t.name}": t for t in tools}

selected_label = st.selectbox(
    "Select Database / API Tool:",
    options=list(tool_map.keys()),
    key="ncbi_console_tool_select"
)

spec = tool_map[selected_label]
render_tool_runner(spec, auto_run=True, key_prefix="ncbi_console")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 🎓 Student Guide to Global Biological Databases")
    st.markdown(
        "Modern biology relies on open international databases. The National Center for Biotechnology Information (NCBI), "
        "European Bioinformatics Institute (EMBL-EBI), and UniProt archive billions of scientific records. "
        "Learn how accession numbers work, how to query PubMed for clinical trials, and how REST APIs allow automated research."
    )
