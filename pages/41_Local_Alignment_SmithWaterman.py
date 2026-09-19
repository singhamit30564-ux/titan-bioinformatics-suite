import streamlit as st
from Bio import pairwise2
from Bio.pairwise2 import format_alignment

st.title(" Module 4.02: Smith-Waterman Local Alignment")
st.markdown("Find the most similar sub-regions between sequences using dynamic programming.")
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    seq1 = st.text_area("Sequence 1 (Long)", "TTCCGGTTTAAAGGGGCCCC", height=150)
with c2:
    seq2 = st.text_area("Sequence 2 (Query)", "TTTAAA", height=150)

match = st.slider("Match Score", 1, 5, 2)
mismatch = st.slider("Mismatch Penalty", -5, 0, -1)
gap_open = st.slider("Gap Open Penalty", -10, 0, -2)
gap_extend = st.slider("Gap Extend Penalty", -5, 0, -1)

if st.button("🔍 Find Best Local Alignment", type="primary", use_container_width=True):
    seq1 = seq1.replace(" ", "").upper()
    seq2 = seq2.replace(" ", "").upper()
    
    alignments = pairwise2.align.localms(seq1, seq2, match, mismatch, gap_open, gap_extend)
    
    if alignments:
        st.markdown(f"### 📊 Top {min(5, len(alignments))} Local Alignments")
        
        for i, align in enumerate(alignments[:5], 1):
            with st.expander(f"Alignment #{i} (Score: {align.score})", expanded=(i==1)):
                st.code(format_alignment(*align), language="text")
                
                # Highlight matched region
                start = align.start
                end = align.end
                st.info(f"**Matched Region in Seq1:** Position {start} to {end}")
                st.code(f"{'-'*start}{seq1[start:end]}{'-'*(len(seq1)-end)}")
        
        st.success(f"✅ Found {len(alignments)} possible local alignments!")
    else:
        st.warning("❌ No alignment found.")

st.info("💡 **Dr. Titan's Tip:** Smith-Waterman finds the BEST matching region, ignoring the rest. Perfect for finding conserved domains or motifs within larger sequences!")