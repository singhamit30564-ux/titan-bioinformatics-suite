import streamlit as st

st.title("🦠 Module 30: Codon Optimizer (E. coli)")
st.markdown("Translate protein to DNA using E. coli preferred codons for high expression.")
st.markdown("---")

prot_seq = st.text_area("Enter Protein Sequence", "MRSLLILVLCFLPAALG").replace(" ", "").upper()

if st.button("Optimize for E. coli", type="primary"):
    # E. coli highly preferred codons
    eco_codons = {
        'F': 'TTT', 'L': 'CTG', 'I': 'ATT', 'M': 'ATG', 'V': 'GTG',
        'S': 'AGC', 'P': 'CCG', 'T': 'ACC', 'A': 'GCG', 'Y': 'TAT',
        '*': 'TAA', 'H': 'CAC', 'Q': 'CAG', 'N': 'AAC', 'K': 'AAA',
        'D': 'GAT', 'E': 'GAA', 'C': 'TGC', 'W': 'TGG', 'R': 'CGC',
        'G': 'GGT'
    }
    
    optimized_dna = []
    for aa in prot_seq:
        if aa in eco_codons:
            optimized_dna.append(eco_codons[aa])
        else:
            optimized_dna.append("NNN")
            
    final_seq = "".join(optimized_dna)
    
    st.markdown("### 🧬 Optimized DNA Sequence")
    st.code(final_seq, language="text")
    
    gc_pct = ((final_seq.count('G') + final_seq.count('C')) / len(final_seq)) * 100 if len(final_seq) > 0 else 0
    st.metric("Optimized GC Content", f"{gc_pct:.2f}%")
    st.info("💡 **Dr. Titan's Tip:** E. coli prefers specific codons (e.g., Proline = CCG, not CCA). Using this table maximizes protein yield in bacterial expression!")