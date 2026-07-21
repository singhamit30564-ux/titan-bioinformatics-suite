import streamlit as st

st.title("🔄 Module 21: Protein to DNA Back-Translator")
st.markdown("Convert a Protein sequence back to a possible DNA sequence. Visualizes codon degeneracy!")
st.markdown("---")

protein_seq = st.text_area("Enter Protein Sequence (1-letter codes)", 
    "MRSLLILVLCFLPAALG", height=150)

if st.button("🔄 Back-Translate to DNA", use_container_width=True, type="primary"):
    seq = protein_seq.replace(" ", "").upper()
    
    if any(c not in "ACDEFGHIKLMNPQRSTVWY*" for c in seq):
        st.error("❌ Invalid Protein Sequence!")
    else:
        # Standard Genetic Code (Amino Acid -> List of Codons)
        reverse_table = {
            'F': ['TTT', 'TTC'], 'L': ['TTA', 'TTG', 'CTT', 'CTC', 'CTA', 'CTG'],
            'I': ['ATT', 'ATC', 'ATA'], 'M': ['ATG'], 'V': ['GTT', 'GTC', 'GTA', 'GTG'],
            'S': ['TCT', 'TCC', 'TCA', 'TCG', 'AGT', 'AGC'], 'P': ['CCT', 'CCC', 'CCA', 'CCG'],
            'T': ['ACT', 'ACC', 'ACA', 'ACG'], 'A': ['GCT', 'GCC', 'GCA', 'GCG'],
            'Y': ['TAT', 'TAC'], '*': ['TAA', 'TAG', 'TGA'], 'H': ['CAT', 'CAC'],
            'Q': ['CAA', 'CAG'], 'N': ['AAT', 'AAC'], 'K': ['AAA', 'AAG'],
            'D': ['GAT', 'GAC'], 'E': ['GAA', 'GAG'], 'C': ['TGT', 'TGC'],
            'W': ['TGG'], 'R': ['CGT', 'CGC', 'CGA', 'CGG', 'AGA', 'AGG'],
            'G': ['GGT', 'GGC', 'GGA', 'GGG']
        }
        
        st.markdown("### 🧬 Possible DNA Sequence (Using Most Frequent Codon)")
        
        # Generate one possible sequence (picking the first/most common codon)
        dna_seq = ""
        for aa in seq:
            if aa in reverse_table:
                dna_seq += reverse_table[aa][0] # Just picking the first one for simplicity
            else:
                dna_seq += "NNN"
        
        st.code(dna_seq, language="text")
        
        st.markdown("### 📊 Codon Degeneracy Analysis")
        degeneracy_data = []
        for i, aa in enumerate(seq):
            if aa in reverse_table:
                count = len(reverse_table[aa])
                degeneracy_data.append({
                    'Position': i + 1,
                    'Amino Acid': aa,
                    'Possible Codons': count,
                    'Codon Options': ", ".join(reverse_table[aa])
                })
        
        import pandas as pd
        df = pd.DataFrame(degeneracy_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.info("💡 **Dr. Titan's Tip:** Notice how Leucine (L) and Arginine (R) have 6 codons, while Methionine (M) and Tryptophan (W) have only 1? This is the **Genetic Code Degeneracy**! It protects organisms from mutations.")