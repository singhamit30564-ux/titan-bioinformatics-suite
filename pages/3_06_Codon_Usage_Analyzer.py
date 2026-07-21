import streamlit as st
import pandas as pd

st.title("📊 Module 18: Codon Usage Analyzer")
st.markdown("Analyze codon frequency and GC content at 3rd codon position.")
st.markdown("---")

dna_seq = st.text_area("Enter Coding DNA Sequence (CDS)", 
    "ATGGCGTACGTAATCGATCGATCGATCTAA", height=150)

if st.button("🔍 Analyze Codon Usage", use_container_width=True, type="primary"):
    seq = dna_seq.replace(" ", "").upper()
    
    if len(seq) % 3 != 0:
        st.warning("⚠️ Sequence length not divisible by 3. Incomplete codons will be ignored.")
    
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
        
        codon_counts = {}
        aa_counts = {}
        gc3_count = 0
        total_codons = 0
        
        for i in range(0, len(seq) - 2, 3):
            codon = seq[i:i+3]
            if codon in codon_table:
                total_codons += 1
                codon_counts[codon] = codon_counts.get(codon, 0) + 1
                aa = codon_table[codon]
                aa_counts[aa] = aa_counts.get(aa, 0) + 1
                if codon[2] in 'GC':
                    gc3_count += 1
        
        gc3_pct = (gc3_count / total_codons * 100) if total_codons > 0 else 0
        
        st.markdown("### 📈 Summary Statistics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Codons", f"{total_codons}")
        c2.metric("Unique Codons", f"{len(codon_counts)}")
        c3.metric("GC3 Content", f"{gc3_pct:.1f}%")
        
        st.markdown("### 🔢 Codon Frequency Table")
        df_data = []
        for codon, count in sorted(codon_counts.items(), key=lambda x: x[1], reverse=True):
            aa = codon_table[codon]
            freq = (count / aa_counts[aa] * 100) if aa_counts[aa] > 0 else 0
            df_data.append({
                'Codon': codon,
                'Amino Acid': aa,
                'Count': count,
                'Frequency %': f"{freq:.1f}%"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.info("💡 **Dr. Titan's Tip:** GC3 content indicates codon bias. High GC3 (>60%) suggests GC-rich organism. Frequency % shows how often a codon is used for that amino acid!")