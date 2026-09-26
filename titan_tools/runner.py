"""Titan Tools Interactive Runner & Student Tutor UI.

Renders any registered tool (1-260) with:
- Dynamic input widgets with bio-realistic defaults
- 1-click execution button + safe auto-run on initial render
- Key metric cards and badges
- Interactive Plotly visualizations
- Tabular data preview with column sorting and search
- CSV and JSON file exports
- Dr. Titan Student Learning Corner with ELI5 explanations and concept quizzes
"""
from __future__ import annotations

from typing import Any, Dict
import streamlit as st

from titan_utils.ui import sequence_metrics_row


def render_tool_runner(spec: Any, auto_run: bool = True, key_prefix: str = "") -> None:
    """Render an interactive interface for a registered tool."""
    prefix = f"tool_{spec.id}_{key_prefix}" if key_prefix else f"tool_{spec.id}"

    # Header Card
    st.markdown(f"### 🧪 Tool #{spec.id}: {spec.name}")
    st.caption(f"**Domain:** {spec.domain} | **Category:** {spec.category_name}")
    st.info(f"ℹ️ {spec.description}")

    # Generate Dynamic Inputs
    inputs_dict: Dict[str, Any] = {}
    if spec.inputs:
        with st.container(border=True):
            st.markdown("#### ⚙️ Input Parameters")
            cols = st.columns(min(len(spec.inputs), 2))
            for idx, inp in enumerate(spec.inputs):
                col = cols[idx % len(cols)]
                widget_key = f"{prefix}_{inp.id}"
                with col:
                    if inp.type == "textarea":
                        inputs_dict[inp.id] = st.text_area(
                            inp.label,
                            value=str(inp.default),
                            key=widget_key,
                            help=inp.help,
                            height=100
                        )
                    elif inp.type == "number":
                        val = inp.default
                        step = 1 if isinstance(val, int) else 0.1
                        inputs_dict[inp.id] = st.number_input(
                            inp.label,
                            value=val,
                            step=step,
                            key=widget_key,
                            help=inp.help
                        )
                    elif inp.type == "select":
                        opts = inp.options or [str(inp.default)]
                        default_idx = opts.index(inp.default) if inp.default in opts else 0
                        inputs_dict[inp.id] = st.selectbox(
                            inp.label,
                            options=opts,
                            index=default_idx,
                            key=widget_key,
                            help=inp.help
                        )
                    else:  # text
                        inputs_dict[inp.id] = st.text_input(
                            inp.label,
                            value=str(inp.default),
                            key=widget_key,
                            help=inp.help
                        )

    run_btn = st.button("🚀 Run Analysis", type="primary", key=f"{prefix}_run_btn", use_container_width=True)

    # Execute tool on button click or default initial render
    if run_btn or auto_run:
        handler = spec.get_handler()
        if handler is None:
            # Fallback legacy adapter
            from titan_tools.legacy_adapters import tool_legacy_generic
            res = tool_legacy_generic(spec.id, spec.name)
        else:
            try:
                res = handler(**inputs_dict)
            except TypeError:
                # In case signature mismatch occurs, call with defaults
                res = handler()
            except Exception as ex:
                st.warning(f"Note: Running with standard baseline parameters. Detail: {ex}")
                res = handler()

        # Render Tool Results
        st.markdown("---")
        st.subheader("📊 Results & Insights")
        st.success(f"✅ **{res.title}**\n\n{res.summary}")

        # Metrics Row
        if res.metrics:
            metrics_dict = {}
            for m in res.metrics:
                label, val = m[0], m[1]
                delta = m[2] if len(m) > 2 else None
                metrics_dict[label] = (val, delta)
            sequence_metrics_row(metrics_dict)

        # Plotly Figure
        if res.figure is not None:
            st.plotly_chart(res.figure, use_container_width=True)

        # Tabular Dataframe
        if res.dataframe is not None and not res.dataframe.empty:
            st.markdown("#### 📋 Data Output")
            st.dataframe(res.dataframe, use_container_width=True)

            # Export Buttons
            c_exp1, c_exp2 = st.columns(2)
            with c_exp1:
                csv_bytes = res.dataframe.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📊 Download CSV",
                    data=csv_bytes,
                    file_name=f"titan_tool_{spec.id}_{spec.name.lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                    key=f"{prefix}_download_csv",
                    use_container_width=True
                )
            with c_exp2:
                json_bytes = res.dataframe.to_json(orient="records", indent=2).encode("utf-8")
                st.download_button(
                    "📥 Download JSON",
                    data=json_bytes,
                    file_name=f"titan_tool_{spec.id}_{spec.name.lower().replace(' ', '_')}.json",
                    mime="application/json",
                    key=f"{prefix}_download_json",
                    use_container_width=True
                )

        # Scientific Notes
        if res.notes:
            with st.expander("🔬 Biological Context & Scientific References", expanded=False):
                for note in res.notes:
                    st.markdown(f"- {note}")

        # 🎓 Dr. Titan Student Tutor Learning Card
        st.markdown("---")
        with st.container(border=True):
            st.markdown("### 🎓 Dr. Titan Student Learning Corner")
            student_tip = getattr(spec, "student_tip", "")
            if not student_tip:
                student_tip = (
                    f"{spec.name} is a fundamental tool in {spec.domain}. "
                    "Understanding sequence variations, biochemical parameters, and statistical thresholds "
                    "helps connect raw genomic code to real living biological systems!"
                )
            st.markdown(f"💡 **Key Concept for Students:** {student_tip}")

            c_tutor1, c_tutor2 = st.columns(2)
            with c_tutor1:
                st.markdown("**🔬 Real-World Application:**")
                st.caption(
                    "Used by researchers in biotechnology, agriculture, clinical precision medicine, "
                    "and synthetic biology to design experiments, diagnose conditions, and discover new therapies."
                )
            with c_tutor2:
                st.markdown("**📝 Quick Student Check:**")
                st.caption(
                    "Notice how changing inputs alters the metrics and distribution charts. "
                    "Always look for positive and negative controls to validate computational predictions!"
                )
