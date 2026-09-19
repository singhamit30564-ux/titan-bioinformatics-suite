import streamlit as st
from Bio import pairwise2
from Bio.pairwise2 import format_alignment
import plotly.graph_objects as go
import numpy as np

st.title("🔄 Module 4.03: Needleman-Wunsch Global Alignment")
st.markdown("End-to-end sequence alignment using dynamic programming.")
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    seq1 = st.text_area("Sequence 1", "AGTCCTA", height=150)
with c2:
    seq2 = st.text_area("Sequence 2", "AGTCTA", height=150)

match = st.number_input("Match Score", value=2)
mismatch = st.number_input("Mismatch Penalty", value=-1)
gap = st.number_input("Gap Penalty", value=-2)

if st.button("🔄 Run Global Alignment", type="primary", use_container_width=True):
    seq1 = seq1.replace(" ", "").upper()
    seq2 = seq2.replace(" ", "").upper()
    
    alignments = pairwise2.align.globalms(seq1, seq2, match, mismatch, gap, gap)
    best = alignments[0]
    
    st.markdown("### 📊 Alignment Result")
    st.success(f"**Optimal Global Score:** {best.score}")
    st.code(format_alignment(*best), language="text")
    
    # Create alignment visualization
    aligned1 = best[0]
    aligned2 = best[1]
    
    matches = sum(1 for a, b in zip(aligned1, aligned2) if a == b and a != '-')
    mismatches = sum(1 for a, b in zip(aligned1, aligned2) if a != b and a != '-' and b != '-')
    gaps = sum(1 for a in aligned1 + aligned2 if a == '-')
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Matches", matches)
    c2.metric("Mismatches", mismatches)
    c3.metric("Gaps", gaps)
    
    identity = (matches / len(aligned1)) * 100 if len(aligned1) > 0 else 0
    st.metric("Sequence Identity", f"{identity:.1f}%")
    
    st.info("💡 **Dr. Titan's Tip:** Global alignment forces the ENTIRE sequences to align, even if they're very different. Best for comparing sequences of similar length and overall similarity!")