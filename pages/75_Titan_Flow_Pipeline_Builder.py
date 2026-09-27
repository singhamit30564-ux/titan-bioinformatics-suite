"""Titan Flow — Multi-Tool Automated Workflow Builder.

Chain multi-step bioinformatics pipelines (Central Dogma, Crop Resilience,
Clinical Oncology, Metagenomics) and download one consolidated .ZIP package
with a PDF report, CSV/TSV tables and a SHA-256 manifest.json.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from titan_utils.mol3d import embed_html
from titan_utils.privacy import ZDR_POLICY, provenance_record
from titan_utils.titan_flow import (
    TITAN_FLOWS,
    build_flow_zip,
    get_flow,
    run_flow,
)
from titan_utils.ui import titan_title
from titan_utils.voice_assistant import narration_html, summarize_for_speech

titan_title(
    "🚀",
    "Titan Flow Pipeline Builder",
    "Automated multi-tool workflows with consolidated ZIP deliverables — PDF report + CSV/TSV + `manifest.json` SHA-256 provenance.",
)

# ── Flow selector ───────────────────────────────────────────────────────────
flow_options = [f"{f.emoji} {f.name}" for f in TITAN_FLOWS.values()]
label_to_id = {f"{f.emoji} {f.name}": fid for fid, f in TITAN_FLOWS.items()}

c_pick, c_info = st.columns([2, 1])
with c_pick:
    selected_label = st.selectbox("Select a Titan Flow:", options=flow_options, key="flow_selector")
flow_id = label_to_id[selected_label]
flow = get_flow(flow_id)

with c_info:
    st.metric("Chained Tools", str(len(flow.steps)), help="Steps executed automatically")
    st.metric("Payload Type", flow.payload_kind)

st.info(f"ℹ️ {flow.description}")

# ── Payload input ───────────────────────────────────────────────────────────
st.markdown("#### 📥 Input Payload (ephemeral in-RAM)")
c_run, c_demo = st.columns([2, 1])
run_clicked = c_run.button("🚀 Run Titan Flow Pipeline", type="primary", use_container_width=True, key="flow_run_btn")
if c_demo.button("🧪 Reset Demo Payload", use_container_width=True, key="flow_reset_btn"):
    # Must be set before the widget instantiates (it is created below).
    st.session_state["flow_payload_input"] = flow.default_payload

payload = st.text_area(
    f"Input — {flow.payload_kind}:",
    value=flow.default_payload,
    height=140,
    key="flow_payload_input",
    help="All payload data is processed in 100% ephemeral RAM buffers (Zero Data Retention).",
)

# Always run in RAM (fast, deterministic) so exports stay in sync.
result = run_flow(flow_id, payload)
prov = provenance_record(payload, kind=flow.payload_kind, label=f"flow_input:{flow.id}")

if run_clicked:
    st.success(f"✅ **{result.title}** completed — {len(result.steps)} tools chained, input fingerprint `{prov.short}…`.")

# ── Results ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Pipeline Results")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Tools Chained", str(len(result.steps)))
m2.metric("Result Rows", str(len(result.consolidated_rows())))
m3.metric("Input SHA-256", prov.short + "…", help=prov.digest)
m4.metric("Input Size", f"{prov.size_bytes} B")

for idx, step in enumerate(result.steps, start=1):
    with st.expander(f"Step {idx} · {step.title}", expanded=(idx == 1)):
        st.markdown(f"**{step.summary}**")
        if step.metrics:
            cols = st.columns(min(len(step.metrics), 4))
            for col, (k, v) in zip(cols, list(step.metrics.items())):
                col.metric(k, str(v))
        if step.rows:
            st.dataframe(pd.DataFrame(step.rows, columns=step.columns or None), use_container_width=True)
        for note in step.notes:
            st.caption(f"🔬 {note}")

# ── Consolidated package ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📦 Consolidated ZIP Package")
zip_bytes = build_flow_zip(result)
manifest_preview = {
    "flow_id": result.flow_id,
    "input_sha256": result.input_digest,
    "steps": len(result.steps),
    "package_files": ["report.pdf", "results.csv", "results.tsv", "manifest.json", "steps/…"],
    "zero_data_retention": True,
}
c_zip, c_json = st.columns([1, 1])
with c_zip:
    st.download_button(
        "⬇️ Download Consolidated .ZIP (PDF + CSV/TSV + manifest.json)",
        data=zip_bytes,
        file_name=f"titan_flow_{flow.id}.zip",
        mime="application/zip",
        use_container_width=True,
        key="flow_zip_download",
    )
    st.caption(f"Package size: {len(zip_bytes):,} bytes — built entirely in RAM.")
with c_json:
    st.json(manifest_preview)

# ── Voice + privacy ─────────────────────────────────────────────────────────
st.markdown("#### 🔊 Voice of Dr. Titan")
embed_html(
    narration_html(
        summarize_for_speech(
            f"Titan Flow complete. {result.title}. {len(result.steps)} tools chained "
            f"and {len(result.consolidated_rows())} result rows generated. "
            f"{result.verdict}"
        ),
        autoplay=False,
    ),
    height=210,
)

with st.expander("🛡️ Zero Data Retention — policy & provenance", expanded=False):
    st.markdown(f"`SHA-256 input digest:` `{prov.digest}`")
    st.caption(ZDR_POLICY)
    st.json(prov.as_dict())
