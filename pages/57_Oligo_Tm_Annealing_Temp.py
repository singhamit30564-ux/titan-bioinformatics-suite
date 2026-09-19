import streamlit as st
import math

st.title("🌡️ Module 5.04: Oligo Tm & Annealing Temperature Calculator")
st.markdown("Calculate Melting Temperature (Tm) using 3 different scientific formulas and find the perfect Annealing Temp.")
st.markdown("---")

oligo_seq = st.text_input("Enter Primer/Oligo Sequence", "ATGCGTACGTAGCTAGCTAG").replace(" ", "").upper()
na_conc = st.slider("Na+ Concentration (mM)", 10, 200, 50)
oligo_conc = st.slider("Oligo Concentration (µM)", 0.1, 1.0, 0.2, 0.1)

if st.button(" Calculate Tm", type="primary", use_container_width=True):
    if not oligo_seq or any(c not in "ATCG" for c in oligo_seq):
        st.error("❌ Please enter a valid DNA sequence (A, T, C, G only)!")
    else:
        length = len(oligo_seq)
        gc = oligo_seq.count('G') + oligo_seq.count('C')
        at = length - gc
        
        # 1. Wallace Rule (For short oligos < 14bp)
        tm_wallace = 2 * at + 4 * gc if length < 14 else None
        
        # 2. Basic GC% Rule (For long oligos > 13bp)
        tm_basic = 64.9 + 41 * (gc - 16.4) / length if length > 13 else None
        
        # 3. Salt-Adjusted Formula (Most accurate for standard PCR)
        tm_salt = 81.5 + 16.6 * math.log10(na_conc / 1000) + 41 * (gc / length) - (600 / length)
        
        # Annealing Temp (Usually Tm - 5°C)
        tm_to_use = tm_salt if tm_salt else (tm_basic if tm_basic else tm_wallace)
        annealing_temp = tm_to_use - 5.0
        
        st.markdown("### 📊 Tm Calculation Results")
        c1, c2, c3 = st.columns(3)
        
        if tm_wallace: c1.metric("Wallace Rule (Short)", f"{tm_wallace:.2f} °C")
        else: c1.metric("Wallace Rule", "N/A (Too long)")
        
        if tm_basic: c2.metric("Basic GC% Rule (Long)", f"{tm_basic:.2f} °C")
        else: c2.metric("Basic GC% Rule", "N/A (Too short)")
        
        c3.metric("Salt-Adjusted (Best)", f"{tm_salt:.2f} °C")
        
        st.markdown("---")
        st.success(f" **Recommended Annealing Temperature for PCR: {annealing_temp:.1f} °C**")
        
        st.info("💡 **Dr. Titan's Tip:** Always start your PCR gradient with the Annealing Temp 5°C below the calculated Tm. If you get non-specific bands, increase the temp by 1-2°C!")