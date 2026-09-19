import streamlit as st

st.title("🧪 Module 26: Protein Isoelectric Point (pI) Estimator")
st.markdown("Estimate the pH at which the protein has a net zero charge.")
st.markdown("---")

prot_seq = st.text_area("Enter Protein Sequence", "MRSLLILVLCFLPAALG").replace(" ", "").upper()

if st.button("Calculate pI", type="primary"):
    if any(c not in "ACDEFGHIKLMNPQRSTVWY" for c in prot_seq):
        st.error("Invalid Protein Sequence!")
    else:
        # Simplified pKa values for N-term, C-term, and ionizable side chains
        pka = {'N_term': 9.69, 'C_term': 2.34, 'D': 3.86, 'E': 4.25, 'C': 8.33, 'Y': 10.07, 'H': 6.00, 'K': 10.53, 'R': 12.48}
        counts = {aa: prot_seq.count(aa) for aa in pka if aa != 'N_term' and aa != 'C_term'}
        counts['N_term'] = 1
        counts['C_term'] = 1
        
        # Very basic estimation (Net charge at pH 7)
        # For a real pI, we'd iterate pH from 0-14, but this gives a quick heuristic
        net_charge_7 = 0
        # Simplified logic for display
        acidic = counts.get('D', 0) + counts.get('E', 0) + counts.get('C_term', 0)
        basic = counts.get('H', 0) + counts.get('K', 0) + counts.get('R', 0) + counts.get('N_term', 0)
        
        st.markdown("### 📊 Charge Analysis at pH 7.0")
        c1, c2, c3 = st.columns(3)
        c1.metric("Acidic Residues (D, E, C-term)", acidic)
        c2.metric("Basic Residues (H, K, R, N-term)", basic)
        
        if basic > acidic:
            st.success(f"✅ **Estimated pI > 7.0 (Basic Protein)**. Net charge at pH 7 is positive.")
        elif acidic > basic:
            st.warning(f"⚠️ **Estimated pI < 7.0 (Acidic Protein)**. Net charge at pH 7 is negative.")
        else:
            st.info("ℹ️ **Estimated pI ≈ 7.0 (Neutral Protein)**.")
            
        st.info("💡 **Dr. Titan's Tip:** pI is crucial for protein purification (Isoelectric Focusing). Proteins precipitate at their pI!")