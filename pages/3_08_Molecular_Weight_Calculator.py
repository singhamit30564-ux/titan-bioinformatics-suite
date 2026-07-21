import streamlit as st

st.title("⚖️ Module 20: Molecular Weight Calculator")
st.markdown("Calculate molecular weight of DNA, RNA, or Protein sequences.")
st.markdown("---")

seq_type = st.radio("Molecule Type", ["DNA", "RNA", "Protein"], horizontal=True)

if seq_type == "DNA":
    seq_input = st.text_area("Enter DNA Sequence", "ATGCGCTAGCTAG", height=150)
    valid_chars = "ATCG"
    mw_table = {'A': 313.21, 'T': 304.2, 'G': 329.21, 'C': 289.18}
elif seq_type == "RNA":
    seq_input = st.text_area("Enter RNA Sequence", "AUGCGCUAGCUAG", height=150)
    valid_chars = "AUCG"
    mw_table = {'A': 329.2, 'U': 306.2, 'G': 345.2, 'C': 305.2}
else:
    seq_input = st.text_area("Enter Protein Sequence (1-letter codes)", "MRSLLILVLCFLPAALG", height=150)
    valid_chars = "ACDEFGHIKLMNPQRSTVWY"
    mw_table = {
        'A': 89.09, 'R': 174.20, 'N': 132.12, 'D': 133.10, 'C': 121.16,
        'E': 147.13, 'Q': 146.15, 'G': 75.07, 'H': 155.16, 'I': 131.17,
        'L': 131.17, 'K': 146.19, 'M': 149.21, 'F': 165.19, 'P': 115.13,
        'S': 105.09, 'T': 119.12, 'W': 204.23, 'Y': 181.19, 'V': 117.15
    }

if st.button("⚖️ Calculate Molecular Weight", use_container_width=True, type="primary"):
    seq = seq_input.replace(" ", "").upper()
    
    if any(c not in valid_chars for c in seq):
        st.error(f"❌ Invalid {seq_type} sequence!")
    else:
        total_mw = sum(mw_table.get(base, 0) for base in seq)
        
        # Subtract water molecules for polymerization
        if seq_type in ["DNA", "RNA"]:
            total_mw -= (len(seq) - 1) * 18.02  # Phosphodiester bonds
            total_mw += 17.01  # 5' phosphate
        else:
            total_mw -= (len(seq) - 1) * 18.02  # Peptide bonds
        
        st.markdown("### 📊 Results")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sequence Length", f"{len(seq)} {'bp' if seq_type in ['DNA', 'RNA'] else 'aa'}")
        c2.metric("Molecular Weight", f"{total_mw:.2f} Da")
        c3.metric("In kDa", f"{total_mw/1000:.2f} kDa")
        
        # Composition breakdown
        st.markdown("### 🔢 Composition Breakdown")
        composition = {}
        for base in seq:
            composition[base] = composition.get(base, 0) + 1
        
        comp_data = []
        for base, count in sorted(composition.items()):
            mw = mw_table.get(base, 0)
            comp_data.append({
                'Base/AA': base,
                'Count': count,
                'MW Contribution (Da)': f"{count * mw:.2f}"
            })
        
        import pandas as pd
        df = pd.DataFrame(comp_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.info("💡 **Dr. Titan's Tip:** DNA/RNA MW includes phosphate backbone. Protein MW is sum of amino acid residues minus water from peptide bonds. 1 kDa = 1000 Daltons!")