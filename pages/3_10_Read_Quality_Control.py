import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.title("📉 Module 3.10: Read Quality Control (FastQC Style)")
st.markdown("Analyze per-base sequence quality from FASTQ data, just like the industry-standard FastQC tool.")
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
    lines = fastq_input.strip().split('\n')
    
    # Parse FASTQ (every 4th line is quality)
    quality_lines = [lines[i] for i in range(3, len(lines), 4)]
    
    if not quality_lines:
        st.error("❌ No valid FASTQ quality lines found! Ensure format is: Header, Seq, +, Quality")
    else:
        with st.spinner("🧮 Calculating Phred Scores..."):
            # Convert ASCII to Phred scores (Sanger format: ASCII - 33)
            max_len = max(len(q) for q in quality_lines)
            quality_matrix = np.zeros((len(quality_lines), max_len))
            
            for i, q_line in enumerate(quality_lines):
                for j, char in enumerate(q_line):
                    if j < max_len:
                        quality_matrix[i, j] = max(0, ord(char) - 33) # Phred+33
            
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