import streamlit as st

st.title("🧬 Module 22: In Silico Mutagenesis Simulator")
st.markdown("Simulate point mutations to see if they are Silent, Missense, or Nonsense.")
st.markdown("---")

dna_seq = st.text_area("Enter Coding DNA Sequence (CDS)", 
    "ATGCGCTACGTAATCGATCG", height=150)

c1, c2 = st.columns(2)
with c1:
    pos = st.number_input("Mutation Position (1-based)", min_value=1, max_value=len(dna_seq.replace(" ","")), value=5)
with c2:
    new_base = st.selectbox("New Base", ["A", "T", "C", "G"])

if st.button("⚡ Simulate Mutation", use_container_width=True, type="primary"):
    seq = dna_seq.replace(" ", "").upper()
    
    codon_table = {
        'ATA':'I', 'ATC':'I', 'ATT':'I', 'ATG':'M', 'ACA':'T', 'ACC':'T', 'ACG':'T', 'ACT':'T',
        'AAC':'N', 'AAT':'N', 'AAA':'K', 'AAG':'K', 'AGC':'S', 'AGT':'S', 'AGA':'R', 'AGG':'R',
        'CTA':'L', 'CTC':'L', 'CTG':'L', 'CTT':'L', 'CCA':'P', 'CCC':'P', 'CCG':'P', 'CCT':'P',
        'CAC':'H', 'CAT':'H', 'CAA':'Q', 'CAG':'Q', 'CGA':'R', 'CGC':'R', 'CGG':'R', 'CGT':'R',
        'GTA':'V', 'GTC':'V', 'GTG':'V', 'GTT':'V', 'GCA':'A', 'GCC':'A', 'GCG':'A', 'GCT':'A',
        'GAC':'D', 'GAT':'D', 'GAA':'E', 'GAG':'E', 'GGA':'G', 'GGC':'G', 'GGG':'G', 'GGT':'G',
        'TCA':'S', 'TCC':'S', 'TCG':'S', 'TCT':'S', 'TTC':'F', 'TTT':'F', 'TTA':'L', 'TTG':'L',
        'TAC':'Y', 'TAT':'Y', 'TAA':'*', 'TAG':'*', 'TGC':'C', 'TGT':'C', 'TGA':'*', 'TGG':'W',
    }
    
    def translate(s):
        return "".join([codon_table.get(s[i:i+3], 'X') for i in range(0, len(s)-2, 3)])

    # Original
    orig_prot = translate(seq)
    
    # Mutated
    idx = pos - 1
    if idx < len(seq):
        old_base = seq[idx]
        mut_seq = seq[:idx] + new_base + seq[idx+1:]
        mut_prot = translate(mut_seq)
        
        # Determine effect
        codon_idx = idx // 3
        orig_aa = orig_prot[codon_idx] if codon_idx < len(orig_prot) else "?"
        mut_aa = mut_prot[codon_idx] if codon_idx < len(mut_prot) else "?"
        
        if orig_aa == mut_aa:
            effect = "🟢 SILENT MUTATION (No change in protein)"
            color = "green"
        elif mut_aa == "*":
            effect = "🔴 NONSENSE MUTATION (Premature Stop Codon!)"
            color = "red"
        else:
            effect = f"🟠 MISSENSE MUTATION ({orig_aa} → {mut_aa})"
            color = "orange"
            
        st.markdown(f"### ⚡ Mutation: {old_base} → {new_base} at pos {pos}")
        st.markdown(f"**Original Codon:** `{seq[codon_idx*3:(codon_idx*3)+3]}` ({orig_aa})")
        st.markdown(f"**Mutated Codon:** `{mut_seq[codon_idx*3:(codon_idx*3)+3]}` ({mut_aa})")
        st.markdown(f"**Effect:** {effect}")
        
        st.code(f"Original Protein: {orig_prot}\nMutated Protein:  {mut_prot}")
    else:
        st.error("Position out of bounds!")

    st.info("💡 **Dr. Titan's Tip:** Silent mutations don't change the amino acid. Missense changes it (can be good or bad). Nonsense creates a STOP signal, cutting the protein short (usually bad)!")