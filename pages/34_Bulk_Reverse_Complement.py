import streamlit as st
import pandas as pd
from titan_utils import clean_sequence, validate_dna, validate_rna, revcomp, gc_fraction_safe
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title("🔄", "Bulk Reverse Complement", "Refactored with Titan validation & export.")
st.markdown("Process multiple DNA sequences at once (one per line).")
st.markdown("---")

bulk_input = st.text_area("Enter DNA Sequences (one per line)", "ATGC\nGCTA\nCCGG", height=200)

if st.button("Process All", type="primary"):
    lines = bulk_input.strip().split('\n')
    results = []
    
    complement = str.maketrans('ATCGatcg', 'TAGCtagc')
    
    for i, line in enumerate(lines):
        seq = line.strip().upper()
        if seq and all(c in "ATCG" for c in seq):
            rev_comp = seq.translate(complement)[::-1]
            results.append(f">{i+1}_rev_comp\n{rev_comp}")
        elif seq:
            results.append(f">Error_Line_{i+1}\nInvalid Sequence")
            
    st.markdown("### 📋 FASTA Output")
    st.code("\n".join(results), language="text")
    
    if st.button("Copy to Clipboard"):
        st.success("Copied! (Use Ctrl+C / Long Press)")