"""Electronic Lab Notebook (ELN) & GLP Audit Trail.

Session run tracking with SHA-256 sequence digests, GLP/ALCOA+ audit tables,
1-click Markdown/PDF compliance exports, and the Zero Data Retention
session memory sanitizer.
"""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from titan_utils.eln import (
    GLP_PRINCIPLES,
    export_markdown,
    export_pdf,
    get_session_log,
    sequence_digest,
)
from titan_utils.mol3d import embed_html
from titan_utils.privacy import (
    ZDR_POLICY,
    memory_snapshot,
    provenance_record,
    sanitize_session_memory,
)
from titan_utils.ui import titan_title
from titan_utils.voice_assistant import narration_html, summarize_for_speech

titan_title(
    "📓",
    "Electronic Lab Notebook & GLP Audit Trail",
    "Attributable, contemporaneous, verifiable — every run recorded with SHA-256 digests and exportable as GLP compliance reports.",
)

log = get_session_log()

# ── Study header ────────────────────────────────────────────────────────────
st.markdown("#### 🧪 Active Study Record")
c1, c2, c3 = st.columns(3)
c1.metric("Runs Recorded", str(len(log)))
c2.metric("Operator", str(log.study.get("operator", "Titan User")))
c3.metric("Facilities", "In-RAM Compute")

st.caption(f"**Study:** {log.study.get('study_title', '')} — {log.study.get('objective', '')}")

# ── New entry controls ──────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### ✍️ Log a New Run Entry")
c_mod, c_seq = st.columns([1, 2])
with c_mod:
    module = st.selectbox(
        "Analysis Module:",
        [
            "Titan Flow Pipeline Builder",
            "Bio-Olympiad Practice Arena",
            "High-Throughput Batch Processor",
            "3D Molecular Viewer",
            "Manual Bench Observation",
        ],
        key="eln_module",
    )
with c_seq:
    sequence_payload = st.text_area(
        "Sequence payload to fingerprint (SHA-256; payload itself is never stored):",
        value="ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG",
        height=68,
        key="eln_sequence_payload",
    )

note = st.text_input("Run notes / observations:", value="Automated in-silico analysis run.", key="eln_notes")

c_log, c_quick, c_sanitize = st.columns(3)
log_clicked = c_log.button("📓 Record Run to Notebook", type="primary", use_container_width=True, key="eln_log_btn")
quick_clicked = c_quick.button("⚡ Log Session Snapshot", use_container_width=True, key="eln_snapshot_btn")
sanitize_clicked = c_sanitize.button("🧽 Sanitize Session Memory (ZDR)", use_container_width=True, key="eln_sanitize_btn")

if log_clicked:
    rec = log.log_run(
        module=module,
        input_data=sequence_payload,
        output_data=f"digest:{sequence_digest(sequence_payload)}",
        summary=f"Manual run via ELN console — {module}",
        parameters={"widget": "eln_console", "payload_len": len(sequence_payload or "")},
        notes=note,
    )
    st.success(f"✅ Run **{rec.run_id}** recorded — input SHA-256 `{rec.input_digest[:16]}…`.")

if quick_clicked:
    snap = memory_snapshot()
    rec = log.log_run(
        module="Session Snapshot",
        input_data="",
        output_data=json.dumps(snap, sort_keys=True),
        summary=f"Session snapshot — {snap['live_vaults']} live ephemeral vault(s), {snap['bytes_in_ram']} bytes in RAM.",
        parameters={"snapshot": "memory_snapshot"},
        notes="Contemporaneous session-state checkpoint (GLP).",
    )
    st.success(f"✅ Session snapshot recorded as **{rec.run_id}**.")

if sanitize_clicked:
    report = sanitize_session_memory(st.session_state)
    st.success(f"🧽 {report.summary()}")
    st.json(report.as_dict())

# ── Audit trail ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📜 GLP Audit Trail")

if log.records:
    audit_df = pd.DataFrame(log.audit_table())
    st.dataframe(audit_df, use_container_width=True, hide_index=True)

    latest = log.records[-1]
    st.markdown("##### Latest Entry — Full SHA-256 Digests")
    st.code(
        f"run_id        : {latest.run_id}\n"
        f"timestamp_utc : {latest.timestamp_utc}\n"
        f"module        : {latest.module}\n"
        f"input_sha256  : {latest.input_digest}\n"
        f"output_sha256 : {latest.output_digest}\n"
        f"status        : {latest.status}",
        language="text",
    )
else:
    st.info("ℹ️ No runs recorded yet — press **Record Run to Notebook** to open the audit trail.")

# ── GLP compliance exports ──────────────────────────────────────────────────
st.markdown("---")
st.subheader("📤 1-Click GLP Compliance Exports")

md_bytes = export_markdown(log).encode("utf-8")
pdf_bytes = export_pdf(log)

c_md, c_pdf, c_json = st.columns(3)
with c_md:
    st.download_button(
        "⬇️ Markdown GLP Report (.md)",
        data=md_bytes,
        file_name="titan_eln_glp_report.md",
        mime="text/markdown",
        use_container_width=True,
        key="eln_md_download",
    )
with c_pdf:
    st.download_button(
        "⬇️ PDF GLP Report (.pdf)",
        data=pdf_bytes,
        file_name="titan_eln_glp_report.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="eln_pdf_download",
    )
with c_json:
    st.download_button(
        "⬇️ Audit Trail JSON (.json)",
        data=log.to_json().encode("utf-8"),
        file_name="titan_eln_audit_trail.json",
        mime="application/json",
        use_container_width=True,
        key="eln_json_download",
    )

with st.expander("📄 Markdown Report Preview", expanded=False):
    st.code(export_markdown(log)[:4000], language="markdown")

# ── GLP principles + provenance ─────────────────────────────────────────────
with st.expander("🏛 GLP / ALCOA+ Principles", expanded=True):
    for principle in GLP_PRINCIPLES:
        st.markdown(f"- {principle}")
    st.caption(ZDR_POLICY)

if sequence_payload:
    prov = provenance_record(sequence_payload, kind="sequence", label="eln_fingerprint_demo")
    st.caption(f"Current payload fingerprint (retention-free): **SHA-256** `{prov.digest}`")

# ── Voice narration ────────────────────────────────────────────────────────
st.markdown("#### 🔊 Voice of Dr. Titan")
embed_html(
    narration_html(
        summarize_for_speech(
            f"Electronic lab notebook status. {len(log)} runs recorded in the current "
            f"study. All sequence data is fingerprinted with SHA-256 and processed in "
            f"ephemeral memory under the zero data retention policy. "
            f"GLP compliance exports are ready in Markdown and PDF formats."
        ),
        autoplay=False,
    ),
    height=210,
)
