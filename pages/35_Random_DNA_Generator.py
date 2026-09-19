import streamlit as st
import pandas as pd
import random
from titan_utils import clean_sequence, validate_dna, validate_rna, revcomp, gc_fraction_safe
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title("🎲", "Random DNA Sequence Generator", "Refactored with Titan validation & export.")
st.markdown("Generate synthetic DNA with specific length and GC content.")
st.markdown("---")

length = st.slider("Sequence Length (bp)", 50, 5000, 500)
target_gc = st.slider("Target GC Content (%)", 0, 100, 50)

if st.button("Generate Sequence", type="primary"):
    gc_prob = target_gc / 100.0
    at_prob = 1.0 - gc_prob
    
    seq = []
    for _ in range(length):
        if random.random() < gc_prob:
            seq.append(random.choice(['G', 'C']))
        else:
            seq.append(random.choice(['A', 'T']))
            
    final_seq = "".join(seq)
    actual_gc = ((final_seq.count('G') + final_seq.count('C')) / length) * 100
    
    st.markdown("### 🧬 Generated Sequence")
    st.code(final_seq, language="text")
    
    c1, c2 = st.columns(2)
    c1.metric("Length", f"{length} bp")
    c2.metric("Actual GC%", f"{actual_gc:.2f}%")