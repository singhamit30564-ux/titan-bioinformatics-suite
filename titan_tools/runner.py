"""Titan Tools Interactive Runner & Student Tutor UI.

Renders any registered tool (1-260) with:
- Dynamic input widgets with bio-realistic defaults
- 1-click execution button + safe auto-run on initial render
- Key metric cards and badges
- Interactive Plotly visualizations
- Tabular data preview with column sorting and search
- CSV and JSON file exports
- Advanced Export Center (CSV/TSV/JSON/FASTA/PDF) with ZDR provenance
- ELN (GLP) run logging + Voice of Dr. Titan narration
- Dr. Titan Student Learning Corner with ELI5 explanations and concept quizzes
"""
from __future__ import annotations

from typing import Any, Dict
import streamlit as st

from titan_utils.eln import get_session_log, sequence_digest
from titan_utils.export import EXPORT_FORMATS, build_export, export_filename, export_mime
from titan_utils.mol3d import embed_html
from titan_utils.pdf_generator import PdfReportSpec, PdfSection, build_pdf_report
from titan_utils.privacy import provenance_record
from titan_utils.ui import _widget_key, sequence_metrics_row
from titan_utils.voice_assistant import narration_html, summarize_for_speech


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

        # ── Advanced Export Center · ZDR Provenance · ELN · PDF ────────────
        _render_export_center(spec, inputs_dict, res, prefix)

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


def _render_export_center(spec: Any, inputs_dict: Dict[str, Any], res: Any, prefix: str) -> None:
    """Advanced Export Center — multi-format downloads, ZDR provenance, ELN, PDF, voice."""
    st.markdown("---")
    with st.container(border=True):
        st.markdown("### 🧾 Advanced Export Center · ZDR Provenance · GLP")
        st.caption(
            "Multi-format exports (CSV · TSV · JSON · FASTA · PDF) with SHA-256 "
            "provenance hashing and 1-click Electronic Lab Notebook logging. "
            "All data processed in 100% ephemeral in-RAM buffers — Zero Data Retention."
        )

        # Canonical input payload for fingerprinting (in-RAM only).
        input_payload = "; ".join(f"{k}={v}" for k, v in (inputs_dict or {}).items()) or f"tool:{spec.id}"
        in_prov = provenance_record(input_payload, kind="tool_input", label=f"tool_{spec.id}_input")
        out_blob = res.summary + "|" + (res.dataframe.to_csv(index=False) if res.dataframe is not None and not res.dataframe.empty else "")
        out_prov = provenance_record(out_blob, kind="tool_output", label=f"tool_{spec.id}_output")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**🔐 Input SHA-256:** `{in_prov.short}…`")
            st.caption(f"{in_prov.size_bytes} bytes fingerprinted in RAM · kind: {in_prov.kind}")
        with c2:
            st.markdown(f"**🔐 Output SHA-256:** `{out_prov.short}…`")
            st.caption(f"{out_prov.size_bytes} bytes fingerprinted in RAM · kind: {out_prov.kind}")

        # Tabular payload for exports.
        export_payload = res.dataframe if res.dataframe is not None and not res.dataframe.empty else None
        export_rows = (
            [{"Metric": k, "Value": str(v)} for k, v in (res.metrics and [m[:2] for m in res.metrics] or [])]
            or [{"Summary": res.summary}]
        )

        c_a, c_b, c_c = st.columns(3)
        with c_a:
            tsv_bytes = build_export("tsv", export_payload if export_payload is not None else export_rows)
            st.download_button(
                "📄 Download TSV",
                data=tsv_bytes,
                file_name=export_filename(f"titan_tool_{spec.id}_{spec.name}", "tsv"),
                mime=export_mime("tsv"),
                key=f"{prefix}_exp_tsv",
                use_container_width=True,
            )
        with c_b:
            json_bytes = build_export("json", export_payload if export_payload is not None else export_rows)
            st.download_button(
                "🧬 Download JSON + Provenance",
                data=json_bytes,
                file_name=export_filename(f"titan_tool_{spec.id}_{spec.name}", "json"),
                mime=export_mime("json"),
                key=f"{prefix}_exp_json",
                use_container_width=True,
            )
        with c_c:
            fasta_records = None
            if getattr(res, "fasta", None):
                fasta_records = {"tool_result": res.fasta}
            elif "sequence" in (inputs_dict or {}):
                fasta_records = {f"tool_{spec.id}_input": str(inputs_dict["sequence"])}
            if fasta_records:
                fasta_bytes = build_export("fasta", fasta_records)
                st.download_button(
                    "🧫 Download FASTA",
                    data=fasta_bytes,
                    file_name=export_filename(f"titan_tool_{spec.id}_{spec.name}", "fasta"),
                    mime=export_mime("fasta"),
                    key=f"{prefix}_exp_fasta",
                    use_container_width=True,
                )
            else:
                st.caption("ℹ️ FASTA export unlocks when the tool has sequence input/output.")

        # PDF scientific report — generated in RAM, content-addressed widget keys.
        pdf_bytes = build_pdf_report(
            PdfReportSpec(
                title=f"Titan Tool #{spec.id} — {spec.name}",
                subtitle=f"{spec.domain} · {spec.category_name}",
                sections=[
                    PdfSection(heading="Summary", paragraphs=[res.summary]),
                    PdfSection(
                        heading="Key Metrics",
                        bullets=[f"{m[0]}: {m[1]}" for m in (res.metrics or [])],
                    ),
                    PdfSection(
                        heading="Provenance (SHA-256)",
                        paragraphs=[
                            f"Input digest: {in_prov.digest}",
                            f"Output digest: {out_prov.digest}",
                            "Computed in 100% ephemeral RAM under the Titan ZDR policy.",
                        ],
                    ),
                    PdfSection(heading="Scientific Context", bullets=list(res.notes or [])),
                ],
            )
        )
        st.download_button(
            "📑 Download PDF Scientific Report",
            data=pdf_bytes,
            file_name=f"titan_tool_{spec.id}_{spec.name.lower().replace(' ', '_')}_report.pdf",
            mime="application/pdf",
            key=_widget_key("report_pdf", pdf_bytes, prefix),
            use_container_width=True,
        )

        # 1-click ELN (GLP) logging.
        if st.button(
            "📓 Log this run to ELN (GLP audit trail)",
            key=f"{prefix}_eln_log_btn",
            use_container_width=True,
        ):
            log = get_session_log()
            rec = log.log_run(
                module=f"Tool #{spec.id}: {spec.name}",
                input_data=input_payload,
                output_data=out_blob,
                summary=res.summary,
                parameters={k: str(v) for k, v in (inputs_dict or {}).items()},
                input_kind="tool_input",
            )
            st.success(
                f"✅ Run **{rec.run_id}** logged to the Electronic Lab Notebook — "
                f"input digest `{sequence_digest(input_payload)[:16]}…` (GLP contemporaneous record)."
            )

        # Voice of Dr. Titan — client-side narration.
        with st.expander("🔊 Voice of Dr. Titan — narrate this result", expanded=False):
            embed_html(
                narration_html(
                    summarize_for_speech(
                        f"Tool {spec.id}, {spec.name}. {res.summary} "
                        + " ".join(
                            f"{m[0]} is {m[1]}." for m in (res.metrics or [])[:4]
                        )
                    ),
                    autoplay=False,
                ),
                height=200,
            )
