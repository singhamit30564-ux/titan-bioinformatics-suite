"""Dr. Titan AI & Bio-Copilot Console (Tools 233-260)."""
from __future__ import annotations

import streamlit as st

from titan_tools.runner import render_tool_runner
from titan_tools.student_tutor import tool_dr_titan_ai_student_tutor
from titan_utils.registry import get_tools_by_category
from titan_utils.ui import titan_title

titan_title(
    "🤖",
    "Dr. Titan AI & Bio-Copilot Console",
    "Next-generation conversational AI reasoning, wet-lab troubleshooting, multilingual sequence explanation, and student tutoring (Tools 233–260).",
)

tab_copilot, tab_student_tutor = st.tabs(["🤖 AI Copilot Tools (233-260)", "🎓 Dr. Titan Student Tutor & Practice"])

with tab_copilot:
    tools = get_tools_by_category("dr_titan")
    tool_map = {f"#{t.id} · {t.name}": t for t in tools}

    selected_label = st.selectbox(
        "Select AI Copilot Assistant:",
        options=list(tool_map.keys()),
        key="drtitan_console_tool_select"
    )

    spec = tool_map[selected_label]
    render_tool_runner(spec, auto_run=True, key_prefix="drtitan_console")

with tab_student_tutor:
    st.markdown("### 🎓 Interactive AI Student Tutor")
    st.write(
        "Learn core biology & bioinformatics topics step-by-step with real-world analogies, "
        "practice questions, and multilingual support in English, Hindi, and Hinglish."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st_topic = st.selectbox(
            "Topic to Learn:",
            ["Central Dogma", "DNA vs RNA", "CRISPR-Cas9", "PCR & Primer Design", "BLAST & Alignment", "Protein Structure & AlphaFold"],
            key="console_tutor_topic"
        )
    with c2:
        st_mode = st.selectbox(
            "Teaching Mode:",
            ["Teach Concept (ELI5 + Story)", "Generate Student Quiz & Practice", "Bioinformatics Career & Study Plan"],
            key="console_tutor_mode"
        )
    with c3:
        st_lang = st.selectbox(
            "Instruction Language:",
            ["English", "Hindi", "Hinglish"],
            key="console_tutor_lang"
        )

    st_question = st.text_input(
        "Ask Dr. Titan AI Tutor Any Question:",
        value="Explain this simply with an analogy",
        key="console_tutor_question"
    )

    st_btn = st.button("🚀 Learn with Dr. Titan", type="primary", key="console_tutor_btn", use_container_width=True)

    if st_btn or True:  # Auto-run for immediate educational feedback
        tutor_res = tool_dr_titan_ai_student_tutor(
            topic=st_topic,
            mode=st_mode,
            language=st_lang,
            custom_question=st_question
        )

        st.success(f"### {tutor_res.title}")
        st.write(tutor_res.summary)

        if tutor_res.figure:
            st.plotly_chart(tutor_res.figure, use_container_width=True)

        if tutor_res.dataframe is not None and not tutor_res.dataframe.empty:
            st.markdown("#### 📝 Concept Knowledge Check & Quiz")
            st.dataframe(tutor_res.dataframe, use_container_width=True)

        with st.expander("📖 Concept Breakdown & Insights", expanded=True):
            for note in tutor_res.notes:
                st.markdown(note)
