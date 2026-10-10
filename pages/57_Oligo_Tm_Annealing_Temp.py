import streamlit as st
import pandas as pd
import math
from titan_utils import clean_sequence, validate_dna, validate_rna, revcomp, gc_fraction_safe
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title
from titan_utils import thermo

titan_title("🌡", "🌡️ Module 5.04: Oligo Tm & Annealing Temperature Calculator", "Refactored with Titan validation & export.")
st.markdown("Calculate Melting Temperature (Tm) with three published estimators — Wallace, salt-adjusted GC% (Marmur–Doty) and nearest-neighbor thermodynamics — and derive the PCR annealing temperature.")
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
        
        # 2. Marmur-Doty style GC% formula, salt-adjusted (81.5 + 16.6·log10[Na+] + 0.41·%GC − 600/L)
        tm_basic, salt_applied = thermo.gc_formula_tm(oligo_seq, Na_mm=na_conc)
        if length < 14:
            tm_basic = None
        
        # 3. Nearest-neighbor Tm (SantaLucia/Breslauer via Biopython), salt-corrected,
        #    oligo-concentration aware — the most accurate estimate shown here.
        tm_nn = thermo.nn_tm(oligo_seq, Na_mm=na_conc, dnac1_nm=oligo_conc * 1000.0, dnac2_nm=oligo_conc * 1000.0)
        
        # Annealing Temp (Usually Tm - 5°C)
        tm_to_use = tm_nn if tm_nn else (tm_basic if tm_basic is not None else tm_wallace)
        annealing_temp = tm_to_use - 5.0
        
        st.markdown("### 📊 Tm Calculation Results")
        c1, c2, c3 = st.columns(3)
        
        if tm_wallace: c1.metric("Wallace Rule (Short)", f"{tm_wallace:.2f} °C")
        else: c1.metric("Wallace Rule", "N/A (Too long)")
        
        if tm_basic is not None: c2.metric("GC% Formula (salt-adjusted)", f"{tm_basic:.2f} °C")
        else: c2.metric("GC% Formula", "N/A (Too short)")
        
        c3.metric("Nearest-Neighbor (Best)", f"{tm_nn:.2f} °C", delta="SantaLucia NN, [oligo] aware", delta_color="off")
        
        st.markdown("---")
        st.success(f" **Recommended Annealing Temperature for PCR: {annealing_temp:.1f} °C**")
        
        st.info("💡 **Dr. Titan's Tip:** Always start your PCR gradient with the Annealing Temp 5°C below the calculated Tm. If you get non-specific bands, increase the temp by 1-2°C!")