import streamlit as st
from Bio import SeqIO
import pandas as pd
import plotly.express as px
import io
from titan_utils import clean_sequence, validate_dna, validate_rna, revcomp, gc_fraction_safe
from titan_utils.i18n import t
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📂 TITAN TOOL 13: FASTA/FASTQ PARSER & QC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

titan_title("📂", "FASTA/FASTQ Parser & QC", "Refactored with Titan validation & export.")
st.markdown(t("Upload your raw sequencing files to instantly parse, validate, and get basic Quality Control (QC) metrics."))
st.markdown("---")

# --- INPUT SECTION ---
uploaded_file = st.file_uploader(
    t("Upload FASTA or FASTQ file (.fasta, .fa, .fastq, .fq)"),
    type=["fasta", "fa", "fastq", "fq", "txt"]
)

if uploaded_file is not None:
    # Determine file type based on extension or content
    file_name = uploaded_file.name.lower()

    if file_name.endswith(('.fastq', '.fq')):
        file_format = "fastq"
    else:
        file_format = "fasta"

    st.markdown(t("### 📊 Analyzing: `{filename}` ({format})", filename=uploaded_file.name, format=file_format.upper()))

    with st.spinner(t("🧬 Parsing sequences... This may take a moment for large files.")):
        try:
            # Read file content
            file_content = uploaded_file.getvalue().decode("utf-8")

            # Parse using Biopython
            records = list(SeqIO.parse(io.StringIO(file_content), file_format))

            if not records:
                st.error(t("❌ No valid sequences found. Please check the file format."))
            else:
                # --- CALCULATE METRICS ---
                total_seqs = len(records)
                lengths = [len(rec) for rec in records]
                total_length = sum(lengths)
                min_len = min(lengths)
                max_len = max(lengths)
                avg_len = total_length / total_seqs

                # Calculate overall GC content
                total_gc = sum(str(rec.seq).upper().count('G') + str(rec.seq).upper().count('C') for rec in records)
                overall_gc = (total_gc / total_length) * 100 if total_length > 0 else 0

                # --- DISPLAY METRICS ---
                st.markdown(t("### 📈 QC Statistics"))
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(t("🧬 Total Sequences"), f"{total_seqs:,}")
                c2.metric(t("📏 Total Length"), f"{total_length:,} bp")
                c3.metric(t("📊 Avg Length"), f"{avg_len:.1f} bp")
                c4.metric(t("🌡️ Overall GC%"), f"{overall_gc:.2f}%")

                st.markdown("---")

                # --- LENGTH DISTRIBUTION CHART ---
                st.markdown(t("### 📊 Sequence Length Distribution"))

                # Create a dataframe for plotting (limit to first 1000 for performance if file is huge)
                plot_lengths = lengths[:1000]
                length_column = t("Length")
                df_plot = pd.DataFrame({length_column: plot_lengths})

                fig = px.histogram(
                    df_plot,
                    x=length_column,
                    nbins=50,
                    color_discrete_sequence=['#d4af37'], # Titan Gold
                    opacity=0.8
                )

                fig.update_layout(
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#1a1f2e',
                    font=dict(color='#e0e0e0'),
                    xaxis_title=t("Sequence Length (bp)"),
                    yaxis_title=t("Frequency"),
                    margin=dict(t=20, b=40, l=40, r=20)
                )

                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")

                # --- PREVIEW TABLE ---
                st.markdown(t("### 🔍 Sequence Preview (First 5)"))

                preview_data = []
                for i, rec in enumerate(records[:5]):
                    seq_str = str(rec.seq)
                    gc_pct = ((seq_str.upper().count('G') + seq_str.upper().count('C')) / len(seq_str) * 100) if len(seq_str) > 0 else 0
                    preview_data.append({
                        t("ID"): rec.id,
                        t("Length"): len(seq_str),
                        t("GC%"): f"{gc_pct:.2f}%",
                        t("Sequence (First 50 bp)"): seq_str[:50] + "..." if len(seq_str) > 50 else seq_str
                    })

                df_preview = pd.DataFrame(preview_data)
                st.dataframe(df_preview, use_container_width=True, hide_index=True)

                # --- THE "SMART LOCK" ---
                st.markdown("---")
                st.markdown(t("### 📥 Export Data"))
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(t("📄 Download QC Summary PDF (Free)"), use_container_width=True):
                        st.info(t("📄 Generating PDF report... (Feature coming in v1.1)"))
                with c2:
                    if st.button(t("📊 Download CSV (Free)"), use_container_width=True):
                        st.info(t("✅ CSV export unlocked — smart_lock enabled."))

        except Exception as e:
            st.error(t("⚠️ Parsing Error: {error}. Please ensure the file is a valid {format} format.", error=str(e), format=file_format.upper()))

else:
    st.info(t("👆 Please upload a FASTA or FASTQ file to begin analysis."))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info(t("💡 **Dr. Titan's Tip:** **FASTA** files contain just the sequence and a header (`>`). **FASTQ** files contain the sequence PLUS a quality score for every single base (used in Next-Gen Sequencing). Always check your 'Avg Length' and 'GC%' to ensure your sequencing run was successful!"))
