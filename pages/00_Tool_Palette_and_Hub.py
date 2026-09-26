"""Titan Master Tool Palette & Interactive Hub — 260 Tools Suite.

Search, filter, inspect, and execute any of the 260 bioinformatics tools
with live interactive execution, Plotly figures, CSV/JSON exports, and
Dr. Titan's AI Student Tutor & Learning Lab.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from titan_tools.common import titan_plot_layout, TITAN_TEAL, TITAN_GOLD, TITAN_CORAL, TITAN_BLUE
from titan_tools.runner import render_tool_runner
from titan_tools.student_tutor import tool_dr_titan_ai_student_tutor
from titan_utils.registry import (
    CATEGORIES,
    get_all_tools,
    get_tool_by_id,
    search_tools,
)
from titan_utils.ui import titan_title

titan_title(
    "🎛️",
    "Titan Master Tool Palette & Hub",
    "Unified interactive search and execution engine across all 260 specialized bioinformatics tools.",
)

tab_hub, tab_tutor, tab_stats = st.tabs(["🔍 Search & Execute Tools", "🎓 Dr. Titan AI Student Tutor", "📈 Suite Analytics"])

with tab_hub:
    c_search, c_cat = st.columns([2, 1])
    with c_search:
        query = st.text_input("🔍 Search 260 Tools (by name, keyword, gene, or method):", value="", key="hub_search_q")
    with c_cat:
        cat_options = [("all", "All Domains (15 Categories)")] + [(c[0], c[1]) for c in CATEGORIES]
        selected_cat = st.selectbox(
            "Filter by Domain:",
            options=[c[0] for c in cat_options],
            format_func=lambda cid: next(label for val, label in cat_options if val == cid),
            key="hub_cat_filter"
        )

    matching_tools = search_tools(query=query, category_id=selected_cat)
    st.caption(f"Found **{len(matching_tools)}** matching tools in the master suite.")

    if not matching_tools:
        st.info("No tools found matching your search. Try another keyword like 'CRISPR', 'BLAST', 'RNA', or 'Coral'.")
        matching_tools = get_all_tools()[:5]

    # Tool Selector
    tool_map = {f"#{t.id} · {t.name} ({t.domain})": t.id for t in matching_tools}
    selected_label = st.selectbox("Select Tool to Launch & Run:", options=list(tool_map.keys()), key="hub_selected_tool")
    chosen_tool_id = tool_map[selected_label]
    spec = get_tool_by_id(chosen_tool_id)

    if spec:
        render_tool_runner(spec, auto_run=True, key_prefix="hub")

with tab_tutor:
    st.markdown("### 🎓 Dr. Titan AI Student Teaching Assistant & Concept Lab")
    st.write(
        "Welcome to the student learning lab! Here, students of all ages can learn "
        "fundamental and advanced bioinformatics concepts with real-world analogies, "
        "step-by-step guides, interactive quizzes, and multilingual explanations."
    )

    c_top, c_mode, c_lang = st.columns(3)
    with c_top:
        t_topic = st.selectbox(
            "Learning Topic:",
            ["Central Dogma", "DNA vs RNA", "CRISPR-Cas9", "PCR & Primer Design", "BLAST & Alignment", "Protein Structure & AlphaFold"],
            key="tutor_topic"
        )
    with c_mode:
        t_mode = st.selectbox(
            "Explanation Mode:",
            ["Teach Concept (ELI5 + Story)", "Generate Student Quiz & Practice", "Bioinformatics Career & Study Plan"],
            key="tutor_mode"
        )
    with c_lang:
        t_lang = st.selectbox(
            "Language:",
            ["English", "Hindi", "Hinglish"],
            key="tutor_lang"
        )

    t_custom = st.text_input(
        "Ask Dr. Titan AI Tutor a Custom Question:",
        value="Explain this with an easy analogy and step-by-step example",
        key="tutor_custom_q"
    )

    tutor_run_btn = st.button("🚀 Ask Dr. Titan AI Tutor", type="primary", key="tutor_submit_btn", use_container_width=True)

    if tutor_run_btn or True:  # Auto-run for immediate educational feedback
        tutor_result = tool_dr_titan_ai_student_tutor(
            topic=t_topic,
            mode=t_mode,
            language=t_lang,
            custom_question=t_custom
        )

        st.success(f"### {tutor_result.title}")
        st.write(tutor_result.summary)

        if tutor_result.figure:
            st.plotly_chart(tutor_result.figure, use_container_width=True)

        if tutor_result.dataframe is not None and not tutor_result.dataframe.empty:
            st.markdown("#### 📝 Interactive Concept Check & Quiz")
            st.dataframe(tutor_result.dataframe, use_container_width=True)

        with st.expander("📖 Detailed Teaching Notes & Dr. Titan Insights", expanded=True):
            for note in tutor_result.notes:
                st.markdown(note)

with tab_stats:
    st.markdown("### 📈 Titan Bioinformatics Suite Composition (260 Tools)")
    all_suite = get_all_tools()
    counts = {}
    for t in all_suite:
        counts[t.domain] = counts.get(t.domain, 0) + 1
    stats_df = pd.DataFrame(list(counts.items()), columns=["Domain", "Tool_Count"]).sort_values("Tool_Count", ascending=False)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Total Tools", "260", "Complete Suite")
    col_m2.metric("Biological Domains", "15", "All Life Sciences")
    col_m3.metric("Interactive AI Copilots", "28", "Dr. Titan Suite")
    col_m4.metric("Free & Open Source", "100%", "No Paywalls")

    fig_stats = px.bar(
        stats_df,
        x="Domain",
        y="Tool_Count",
        color="Tool_Count",
        color_continuous_scale=[TITAN_TEAL, TITAN_GOLD, TITAN_CORAL, TITAN_BLUE],
        text="Tool_Count"
    )
    fig_stats.update_layout(**titan_plot_layout("Tool Distribution Across 15 Biological Domains", height=350))
    st.plotly_chart(fig_stats, use_container_width=True)
