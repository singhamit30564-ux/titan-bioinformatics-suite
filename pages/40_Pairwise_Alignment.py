import streamlit as st
from Bio import pairwise2
from Bio.pairwise2 import format_alignment
import plotly.graph_objects as go

st.title("🧬 Module 4.01: Advanced Pairwise Aligner")
st.markdown("Compare two sequences using Needleman-Wunsch (Global) or Smith-Waterman (Local) algorithms.")
st.markdown("---")

# --- INPUTS ---
c1, c2 = st.columns(2)
with c1:
    seq1 = st.text_area("Sequence 1 (Target)", "HEAGAWGHEE", height=150)
with c2:
    seq2 = st.text_area("Sequence 2 (Query)", "PAWHEAE", height=150)

algo = st.radio("Select Algorithm", ["Global (Needleman-Wunsch)", "Local (Smith-Waterman)"], horizontal=True)

# Scoring Parameters
c3, c4, c5 = st.columns(3)
with c3: match_score = st.number_input("Match Score", value=2)
with c4: mismatch_score = st.number_input("Mismatch Penalty", value=-1)
with c5: gap_penalty = st.number_input("Gap Penalty", value=-2)

if st.button("🚀 Run Alignment", type="primary", use_container_width=True):
    seq1 = seq1.replace(" ", "").upper()
    seq2 = seq2.replace(" ", "").upper()
    
    if not seq1 or not seq2:
        st.error("Please enter both sequences!")
    else:
        with st.spinner(" Running Dynamic Programming Matrix..."):
            try:
                # Biopython Alignment
                if "Global" in algo:
                    alignments = pairwise2.align.globalms(seq1, seq2, match_score, mismatch_score, gap_penalty, gap_penalty)
                else:
                    alignments = pairwise2.align.localms(seq1, seq2, match_score, mismatch_score, gap_penalty, gap_penalty)
                
                best_align = alignments[0]
                
                # --- DISPLAY RESULTS ---
                st.markdown("###  Optimal Alignment")
                st.success(f"**Maximum Score:** {best_align.score}")
                st.code(format_alignment(*best_align), language="text")
                
                # --- VISUALIZATION (Match/Mismatch Plot) ---
                st.markdown("### 📊 Alignment Visualization")
                
                aligned_seq1 = best_align[0]
                aligned_seq2 = best_align[1]
                
                match_colors = ['#66fcf1' if a == b else '#ff0055' for a, b in zip(aligned_seq1, aligned_seq2)]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(len(aligned_seq1))),
                    y=[1]*len(aligned_seq1),
                    mode='markers+text',
                    marker=dict(size=20, color=match_colors),
                    text=list(aligned_seq1),
                    textposition="middle center",
                    name="Sequence 1"
                ))
                fig.add_trace(go.Scatter(
                    x=list(range(len(aligned_seq2))),
                    y=[0]*len(aligned_seq2),
                    mode='markers+text',
                    marker=dict(size=20, color=match_colors),
                    text=list(aligned_seq2),
                    textposition="middle center",
                    name="Sequence 2"
                ))
                
                fig.update_layout(
                    yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                    xaxis=dict(showgrid=False, zeroline=False),
                    template="plotly_dark",
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#1a1f2e',
                    height=200
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.info("💡 **Dr. Titan's Tip:** Cyan = Perfect Match. Red = Mismatch/Gap. Global alignment forces end-to-end matching, while Local finds the best matching sub-region!")
                
            except Exception as e:
                st.error(f"Alignment Error: {e}")