"""Population Genetics & Evolutionary Dynamics Console (Tools 193-212)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "👥",
    "Population Genetics & Evolutionary Dynamics Console",
    "Allele frequency trajectories, Hardy-Weinberg equilibrium, Wright-Fisher drift, Fst subdivision, Tajima's D, and archaic admixture (Tools 193–212).",
)

tools = get_tools_by_category("population")
tool_map = {f"#{t.id} · {t.name}": t for t in tools}

selected_label = st.selectbox(
    "Select Population Genetics Tool:",
    options=list(tool_map.keys()),
    key="pop_console_tool_select"
)

spec = tool_map[selected_label]
render_tool_runner(spec, auto_run=True, key_prefix="pop_console")

st.markdown("---")
with st.container(border=True):
    st.markdown("### 🎓 Student Guide to Evolutionary Genetics")
    st.markdown(
        "Evolution is the change in allele frequencies over generations. The four fundamental evolutionary forces are: "
        "mutation (creates new variation), genetic drift (random sampling in finite populations), gene flow / migration, "
        "and natural selection. Use these tools to test neutrality with Tajima's D, measure population divergence with Fst, "
        "and detect ancient Neanderthal/Denisovan gene flow with Patterson's D (ABBA-BABA) test."
    )
