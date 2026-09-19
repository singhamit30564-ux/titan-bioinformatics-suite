import streamlit as st
from Bio import pairwise2
from Bio.pairwise2 import format_alignment

st.title(" Module 4.04: Overlap Alignment")
st.markdown("Find the best overlap between the end of Sequence 1 and the start of Sequence 2.")
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    seq1 = st.text_area("Sequence 1 (Left)", "AAACCCCGGGG", height=150)
with c2:
    seq2 = st.text_area("Sequence 2 (Right)", "CCCCGGGGTTTT", height=150)

match = st.number_input("Match Score", value=2)
mismatch = st.number_input("Mismatch Penalty", value=-1)
gap = st.number_input("Gap Penalty", value=-2)

if st.button("🔗 Find Overlap", type="primary", use_container_width=True):
    seq1 = seq1.replace(" ", "").upper()
    seq2 = seq2.replace(" ", "").upper()
    
    # Overlap alignment: free end gaps
    alignments = pairwise2.align.globalms(seq1, seq2, match, mismatch, gap, gap, 
                                          penalize_end_gaps=(False, False))
    
    if alignments:
        best = alignments[0]
        st.success(f"**Best Overlap Score:** {best.score}")
        st.code(format_alignment(*best), language="text")
        
        # Show merged sequence
        aligned1 = best[0].replace('-', '')
        aligned2 = best[1].replace('-', '')
        st.markdown("### 🧬 Merged Sequence")
        st.info(f"`{aligned1}{aligned2[len(seq1):]}`")
    else:
        st.warning(" No overlap found.")

st.info("💡 **Dr. Titan's Tip:** Overlap alignment is used in genome assembly! It finds how two DNA reads connect at their ends to build a longer contiguous sequence (Contig).")