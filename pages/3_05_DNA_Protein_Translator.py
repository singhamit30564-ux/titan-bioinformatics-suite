import streamlit as st

st.title("🧬 Module 17: DNA to Protein Translator")
st.markdown("Translate DNA sequences to protein with all 6 reading frames.")
st.markdown("---")

dna_seq = st.text_area("Enter DNA Sequence (5' to 3')", 
    "ATGGCGTACGTAATCGATCGATCGATCTAA", height=150)

if st.button("🔄 Translate All Frames", use_container_width=True, type="primary"):
    seq = dna_seq.replace(" ", "").upper()
    
    if any(c not in "ATCG" for c in seq):
        st.error("❌ Invalid DNA! Only A, T, C, G allowed.")
    else:
        codon_table = {
            'ATA':'I', 'ATC':'I', 'ATT':'I', 'ATG':'M',
            'ACA':'T', 'ACC':'T', 'ACG':'T', 'ACT':'T',
            'AAC':'N', 'AAT':'N', 'AAA':'K', 'AAG':'K',
            'AGC':'S', 'AGT':'S', 'AGA':'R', 'AGG':'R',
            'CTA':'L', 'CTC':'L', 'CTG':'L', 'CTT':'L',
            'CCA':'P', 'CCC':'P', 'CCG':'P', 'CCT':'P',
            'CAC':'H', 'CAT':'H', 'CAA':'Q', 'CAG':'Q',
            'CGA':'R', 'CGC':'R', 'CGG':'R', 'CGT':'R',
            'GTA':'V', 'GTC':'V', 'GTG':'V', 'GTT':'V',
            'GCA':'A', 'GCC':'A', 'GCG':'A', 'GCT':'A',
            'GAC':'D', 'GAT':'D', 'GAA':'E', 'GAG':'E',
            'GGA':'G', 'GGC':'G', 'GGG':'G', 'GGT':'G',
            'TCA':'S', 'TCC':'S', 'TCG':'S', 'TCT':'S',
            'TTC':'F', 'TTT':'F', 'TTA':'L', 'TTG':'L',
            'TAC':'Y', 'TAT':'Y', 'TAA':'*', 'TAG':'*',
            'TGC':'C', 'TGT':'C', 'TGA':'*', 'TGG':'W',
        }
        
        def translate(seq, frame):
            protein = ""
            for i in range(frame, len(seq) - 2, 3):
                codon = seq[i:i+3]
                protein += codon_table.get(codon, 'X')
            return protein
        
        st.markdown("### 📊 All 6 Reading Frames")
        
        # Forward frames
        for frame in range(3):
            protein = translate(seq, frame)
            st.success(f"**Frame +{frame+1}:** `{protein}`")
        
        # Reverse complement
        complement = str.maketrans('ATCG', 'TAGC')
        rev_seq = seq.translate(complement)[::-1]
        
        for frame in range(3):
            protein = translate(rev_seq, frame)
            st.warning(f"**Frame -{frame+1}:** `{protein}`")
        
        st.info("💡 **Dr. Titan's Tip:** Frame +1 starts at position 0, +2 at position 1, +3 at position 2. Negative frames are on the reverse complement strand. Look for the longest ORF without stop codons (*)!")