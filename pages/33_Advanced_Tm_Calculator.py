import streamlit as st

st.title("🌡️ Module 25: Advanced Tm Calculator")
st.markdown("Calculate Melting Temperature with Salt Correction (Schildkraut & Lifson, 1965).")
st.markdown("---")

seq = st.text_input("Enter DNA Sequence", "ATGCGCTAGCTAGCTAGCTA").replace(" ", "").upper()
na_conc = st.slider("Na+ Concentration (mM)", 10, 1000, 50)

if st.button("Calculate Tm", type="primary"):
    if any(c not in "ATCG" for c in seq):
        st.error("Invalid DNA!")
    else:
        length = len(seq)
        gc = seq.count('G') + seq.count('C')
        at = length - gc
        
        # Basic Wallace Rule
        tm_wallace = 2 * at + 4 * gc if length < 14 else 64.9 + 41 * (gc - 16.4) / length
        
        # Salt Correction Formula
        salt_correction = 16.6 * (math.log10(na_conc / 1000) if na_conc > 0 else 0)
        tm_corrected = tm_wallace + salt_correction
        
        c1, c2 = st.columns(2)
        c1.metric("Basic Tm (Wallace)", f"{tm_wallace:.2f} °C")
        c2.metric("Salt-Corrected Tm", f"{tm_corrected:.2f} °C", delta=f"{salt_correction:+.2f} °C")
        st.info("💡 **Dr. Titan's Tip:** Salt (Na+) stabilizes the DNA duplex, increasing the Tm. Always use salt-corrected Tm for PCR primer design!")