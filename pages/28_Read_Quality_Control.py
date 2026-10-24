import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from titan_utils import clean_sequence, validate_dna, validate_rna, revcomp, gc_fraction_safe
from titan_utils import engine as pro_engine
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title("📉", "📉 Module 3.10: Read Quality Control (FastQC Style)", "Refactored with Titan validation & export.")
st.markdown("Analyze per-base sequence quality from FASTQ data, just like the industry-standard FastQC tool.")
st.caption(pro_engine.engine_badge(), help="FASTQ parsing runs through titan_utils.engine (Rust titan_core when available, pure-Python fallback otherwise).")
st.markdown("---")

# Mock FASTQ data for demonstration
default_fastq = """@READ1
ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
@READ2
ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
@READ3
ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
+
IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII"""

fastq_input = st.text_area("Paste FASTQ Data (or use default mock data)", default_fastq, height=200)

if st.button("🔬 Run Quality Control", type="primary", use_container_width=True):
    # Parse FASTQ via the Pro Engine (Rust titan_core when available,
    # pure-Python fallback otherwise) — tolerant of CRLF/truncation.
    try:
        parsed_fastq = pro_engine.parse_fastq(data=fastq_input)
        quality_lines = parsed_fastq["qualities"]
    except ValueError:
        quality_lines = []

    if not quality_lines:
        st.error("❌ No valid FASTQ quality lines found! Ensure format is: Header, Seq, +, Quality")
    else:
        with st.spinner("🧮 Calculating Phred Scores..."):
            # Convert ASCII to Phred scores with the engine's autodetected
            # offset (Phred+33 unless the data is clearly Phred+64).
            flat_min = min((ord(c) for q in quality_lines for c in q), default=33)
            phred_offset = 33 if flat_min < 64 else 64
            max_len = max(len(q) for q in quality_lines)
            quality_matrix = np.zeros((len(quality_lines), max_len))
            
            for i, q_line in enumerate(quality_lines):
                for j, char in enumerate(q_line):
                    if j < max_len:
                        quality_matrix[i, j] = max(0, ord(char) - phred_offset)
            
            # Calculate stats per base position
            positions = list(range(1, max_len + 1))
            mean_q = np.mean(quality_matrix, axis=0)
            median_q = np.median(quality_matrix, axis=0)
            q10 = np.percentile(quality_matrix, 10, axis=0)
            q90 = np.percentile(quality_matrix, 90, axis=0)
            
            # Plotly Chart (FastQC Style)
            fig = go.Figure()
            
            # Box plot / Range area
            fig.add_trace(go.Scatter(
                x=positions, y=q90, mode='lines', line=dict(width=0), showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=positions, y=q10, mode='lines', line=dict(width=0), fill='tonexty',
                fillcolor='rgba(212, 175, 55, 0.2)', name='10th-90th Percentile'
            ))
            
            # Mean and Median lines
            fig.add_trace(go.Scatter(
                x=positions, y=mean_q, mode='lines', line=dict(color='#d4af37', width=3), name='Mean Quality'
            ))
            fig.add_trace(go.Scatter(
                x=positions, y=median_q, mode='lines', line=dict(color='#66fcf1', width=2, dash='dot'), name='Median Quality'
            ))
            
            # Threshold lines
            fig.add_hline(y=20, line_dash="dash", line_color="#ff0055", annotation_text="Q20 (99% Accuracy)")
            fig.add_hline(y=30, line_dash="dash", line_color="#00ff00", annotation_text="Q30 (99.9% Accuracy)")
            
            fig.update_layout(
                title="Per Base Sequence Quality",
                xaxis_title="Position in Read (bp)",
                yaxis_title="Phred Quality Score",
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                font=dict(color='#e0e0e0'),
                yaxis=dict(range=[0, 45])
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### 📊 QC Summary")
            avg_overall_q = np.mean(quality_matrix)
            st.metric("Overall Mean Quality Score", f"{avg_overall_q:.2f}")
            
            st.info("💡 **Dr. Titan's Tip:** In a good sequencing run, the mean quality (gold line) should stay above Q30 (green line) across the entire read. A drop at the end is normal, but a sharp drop indicates poor sequencing chemistry!")