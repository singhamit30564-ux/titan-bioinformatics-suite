"""High-Throughput Batch Processor & Consolidated Archive.

Run the same analytical battery across an entire multi-FASTA batch and
download one consolidated ZIP archive (CSV + TSV + summary JSON + normalised
FASTA + SHA-256 manifest.json). All processing is ephemeral in-RAM.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from titan_utils.batch_processor import (
    BATCH_ANALYSES,
    DEFAULT_ANALYSES,
    DEFAULT_BATCH_FASTA,
    build_batch_zip,
    run_batch,
)
from titan_utils.mol3d import embed_html
from titan_utils.privacy import ZDR_POLICY, provenance_record
from titan_utils.ui import titan_title
from titan_utils.voice_assistant import narration_html, summarize_for_speech

titan_title(
    "🧬",
    "High-Throughput Batch Processor & Archive",
    "Multi-FASTA batch analysis with consolidated ZIP archive downloads — powered by 100% ephemeral in-RAM execution.",
)

# ── Input ───────────────────────────────────────────────────────────────────
st.markdown("#### 📥 Multi-FASTA Batch Input")
c_load, c_clear = st.columns([1, 1])
if c_load.button("🧪 Load Demo Batch (5 samples)", use_container_width=True, key="batch_load_btn"):
    st.session_state["batch_input"] = DEFAULT_BATCH_FASTA
if c_clear.button("🧹 Clear Input", use_container_width=True, key="batch_clear_btn"):
    st.session_state["batch_input"] = ""

payload = st.text_area(
    "Paste multi-FASTA (or raw sequences):",
    value=DEFAULT_BATCH_FASTA,
    height=180,
    key="batch_input",
    help="Sequences are parsed in RAM — nothing is written to disk (Zero Data Retention).",
)

uploaded = st.file_uploader(
    "…or upload a .fasta / .fa / .txt file (processed in RAM only):",
    type=["fasta", "fa", "fna", "txt"],
    key="batch_uploader",
)
if uploaded is not None:
    payload = uploaded.getvalue().decode("utf-8", errors="replace")

# ── Analysis selection ──────────────────────────────────────────────────────
st.markdown("#### ⚙️ Batch Analyses")
analysis_labels = {f"{label} [{aid}]": aid for aid, (label, _fn, _col) in BATCH_ANALYSES.items()}
chosen_labels = st.multiselect(
    "Select analyses to run across every record:",
    options=list(analysis_labels.keys()),
    default=[f"{BATCH_ANALYSES[a][0]} [{a}]" for a in DEFAULT_ANALYSES if a in BATCH_ANALYSES],
    key="batch_analyses",
)
chosen = [analysis_labels[l] for l in chosen_labels]

run_clicked = st.button("🚀 Run Batch Processing", type="primary", use_container_width=True, key="batch_run_btn")

# Run in RAM on every render so tables/exports stay in sync.
result = run_batch(payload, chosen)
prov = provenance_record(payload, kind="multi-FASTA batch", label="batch_input")

if run_clicked:
    st.success(
        f"✅ Batch complete — **{result.record_count} records** × "
        f"**{len(result.analyses)} analyses** in one ephemeral pass "
        f"(input fingerprint `{prov.short}…`)."
    )

# ── Results ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📊 Batch Results")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Records", str(result.record_count))
summary = result.summary()
m2.metric("Total bp", str(summary.get("total_bp", 0)))
m3.metric("Mean Length", f"{summary.get('mean_length_bp', 0)} bp")
m4.metric("Mean GC", f"{summary.get('mean_gc_percent', 0)} %")
m5.metric("Input SHA-256", prov.short + "…", help=prov.digest)

if result.rows:
    df = result.to_frame()
    # Keep ultra-wide columns readable.
    st.dataframe(df, use_container_width=True)

    st.markdown("#### 📈 Per-Record GC Content")
    if "GC_Percent" in df.columns:
        st.bar_chart(df.set_index("Record_ID")["GC_Percent"], height=240, use_container_width=True)

    with st.expander("🔍 Per-Record SHA-256 Provenance Digests", expanded=False):
        digest_df = df[["Record_ID", "SHA256"]].copy() if "SHA256" in df.columns else pd.DataFrame(
            {"Note": ["Enable the 'SHA-256 digest' analysis to fingerprint each record."]})
        st.dataframe(digest_df, use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ No records detected — paste multi-FASTA sequences above and press **Run Batch Processing**.")

# ── Consolidated archive ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📦 Consolidated ZIP Archive")
zip_bytes = build_batch_zip(result)
c_zip, c_manifest = st.columns([1, 1])
with c_zip:
    st.download_button(
        "⬇️ Download Consolidated .ZIP (CSV + TSV + JSON + FASTA + manifest)",
        data=zip_bytes,
        file_name="titan_batch_archive.zip",
        mime="application/zip",
        use_container_width=True,
        key="batch_zip_download",
    )
    st.caption(
        f"Archive size: {len(zip_bytes):,} bytes — batch_results.csv · batch_results.tsv · "
        "batch_summary.json · records.fasta · manifest.json"
    )
with c_manifest:
    st.json(summary)

# ── Voice + ZDR ─────────────────────────────────────────────────────────────
st.markdown("#### 🔊 Voice of Dr. Titan")
embed_html(
    narration_html(
        summarize_for_speech(
            f"Batch processing complete. {result.record_count} records analysed with "
            f"{len(result.analyses)} metrics per record. "
            f"Total batch length {summary.get('total_bp', 0)} base pairs, "
            f"mean GC content {summary.get('mean_gc_percent', 0)} percent. "
            "The consolidated archive is ready for download."
        ),
        autoplay=False,
    ),
    height=210,
)

with st.expander("🛡️ Zero Data Retention — policy & provenance", expanded=False):
    st.markdown(f"`SHA-256 batch digest:` `{prov.digest}`")
    st.caption(ZDR_POLICY)
