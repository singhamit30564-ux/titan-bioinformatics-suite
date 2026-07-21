import streamlit as st
import math

st.title("🧪 Module 5.02: Advanced Primer Design (Tm, GC & Hairpin)")
st.markdown("Design optimal PCR primers with strict checks for Melting Temp, GC%, and Self-Complementarity (Hairpins).")
st.markdown("---")

seq_input = st.text_area("Enter Template DNA Sequence", "ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCG", height=150)
target_tm = st.slider("Target Tm (°C)", 55, 65, 60)
min_gc = st.slider("Min GC %", 40, 50, 45)
max_gc = st.slider("Max GC %", 55, 65, 60)
primer_len = st.slider("Primer Length (bp)", 18, 24, 20)

def calc_tm(seq):
    # Nearest Neighbor simplified (SantaLucia)
    gc = seq.count('G') + seq.count('C')
    return 64.9 + 41 * (gc - 16.4) / len(seq)

def check_hairpin(seq):
    rev_comp = seq.translate(str.maketrans('ATCG', 'TAGC'))[::-1]
    for i in range(len(seq) - 3):
        if seq[i:i+4] in rev_comp:
            return "⚠️ High Risk"
    return "✅ Low Risk"

if st.button(" Design Primers", type="primary", use_container_width=True):
    seq = seq_input.replace(" ", "").upper()
    if len(seq) < 50: st.error("❌ Sequence too short!")
    else:
        st.markdown("### 📌 Top Primer Candidates")
        candidates = []
        
        for i in range(len(seq) - primer_len + 1):
            f_primer = seq[i:i+primer_len]
            gc = ((f_primer.count('G') + f_primer.count('C')) / primer_len) * 100
            
            if min_gc <= gc <= max_gc:
                tm = calc_tm(f_primer)
                if abs(tm - target_tm) <= 3:
                    candidates.append({
                        'Pos': i+1, 'Seq': f_primer, 'Tm': round(tm, 1), 'GC': round(gc, 1), 
                        'Hairpin': check_hairpin(f_primer)
                    })
        
        if not candidates: st.warning("️ No primers found matching strict criteria. Try relaxing GC% or Tm.")
        else:
            import pandas as pd
            df = pd.DataFrame(candidates[:10]) # Show top 10
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info("💡 **Dr. Titan's Tip:** A good primer has Tm between 55-65°C, GC% between 45-60%, and NO hairpins (self-binding) at the 3' end!")