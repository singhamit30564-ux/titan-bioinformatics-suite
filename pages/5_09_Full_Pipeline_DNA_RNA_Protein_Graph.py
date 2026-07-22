import streamlit as st
import plotly.graph_objects as go
import math

st.title("🧬 Module 5.09: Full Central Dogma Pipeline Dashboard")
st.markdown("Visualize the complete DNA → RNA → Protein pipeline with real-time analytics and graphs.")
st.markdown("---")

# --- INPUT ---
dna_seq = st.text_area("Enter DNA Sequence (Coding Strand 5' to 3')", 
    "ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG", 
    height=150)

if st.button(" Run Full Pipeline", type="primary", use_container_width=True):
    seq = dna_seq.replace(" ", "").upper()
    
    if not seq or any(c not in "ATCG" for c in seq):
        st.error("❌ Please enter a valid DNA sequence (A, T, C, G only)!")
    else:
        # 1. TRANSCRIPTION (DNA -> RNA)
        rna_seq = seq.replace('T', 'U')
        
        # 2. TRANSLATION (RNA -> Protein)
        codon_table = {
            'AUG':'M', 'UAA':'*', 'UAG':'*', 'UGA':'*',
            'UUU':'F', 'UUC':'F', 'UUA':'L', 'UUG':'L',
            'UCU':'S', 'UCC':'S', 'UCA':'S', 'UCG':'S',
            'UAU':'Y', 'UAC':'Y', 'UAA':'*', 'UAG':'*',
            'UGU':'C', 'UGC':'C', 'UGA':'*', 'UGG':'W',
            'CUU':'L', 'CUC':'L', 'CUA':'L', 'CUG':'L',
            'CCU':'P', 'CCC':'P', 'CCA':'P', 'CCG':'P',
            'CAU':'H', 'CAC':'H', 'CAA':'Q', 'CAG':'Q',
            'CGU':'R', 'CGC':'R', 'CGA':'R', 'CGG':'R',
            'AUU':'I', 'AUC':'I', 'AUA':'I', 'AUG':'M',
            'ACU':'T', 'ACC':'T', 'ACA':'T', 'ACG':'T',
            'AAU':'N', 'AAC':'N', 'AAA':'K', 'AAG':'K',
            'AGU':'S', 'AGC':'S', 'AGA':'R', 'AGG':'R',
            'GUU':'V', 'GUC':'V', 'GUA':'V', 'GUG':'V',
            'GCU':'A', 'GCC':'A', 'GCA':'A', 'GCG':'A',
            'GAU':'D', 'GAC':'D', 'GAA':'E', 'GAG':'E',
            'GGU':'G', 'GGC':'G', 'GGA':'G', 'GGG':'G'
        }
        
        protein_seq = ""
        for i in range(0, len(rna_seq) - 2, 3):
            codon = rna_seq[i:i+3]
            protein_seq += codon_table.get(codon, '?')
            
        # 3. ANALYTICS
        length = len(seq)
        gc_count = seq.count('G') + seq.count('C')
        gc_pct = (gc_count / length) * 100
        
        # Molecular Weight (Approximate)
        mw_dna = (length * 303.7) - (length - 1) * 18.02 
        mw_protein = sum([110 for _ in protein_seq if _ != '*']) # Avg AA weight ~110 Da
        
        # --- DASHBOARD LAYOUT ---
        st.markdown("### 📊 Sequence Dashboard")
        
        # Row 1: The Sequences
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**🧬 DNA**")
            st.code(seq, language="text")
            st.metric("Length", f"{length} bp")
        with c2:
            st.markdown("** RNA**")
            st.code(rna_seq, language="text")
            st.metric("Length", f"{len(rna_seq)} nt")
        with c3:
            st.markdown("**🥩 Protein**")
            st.code(protein_seq, language="text")
            st.metric("Length", f"{len(protein_seq)} aa")
            
        st.markdown("---")
        
        # Row 2: Metrics & Graphs
        m1, m2, m3 = st.columns(3)
        m1.metric("GC Content", f"{gc_pct:.1f}%")
        m2.metric("DNA Mol. Weight", f"{mw_dna/1000:.2f} kDa")
        m3.metric("Protein Mol. Weight", f"{mw_protein/1000:.2f} kDa")
        
        st.markdown("### 📈 Nucleotide Composition")
        
        # Plotly Pie Chart
        fig = go.Figure(data=[go.Pie(
            labels=['Adenine (A)', 'Thymine (T)', 'Cytosine (C)', 'Guanine (G)'],
            values=[seq.count('A'), seq.count('T'), seq.count('C'), seq.count('G')],
            marker=dict(colors=['#ff0055', '#d4af37', '#66fcf1', '#ffffff']),
            hole=0.4
        )])
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='#0a0e17',
            font=dict(color='#e0e0e0'),
            showlegend=True,
            legend=dict(x=0.5, y=-0.2, orientation='h')
        )
        
        st.plotly_chart(fig, use_container_width=True)

        st.info("💡 **Dr. Titan's Tip:** This dashboard represents the Central Dogma of Molecular Biology. The GC content and Molecular Weight are critical parameters for designing primers and predicting protein behavior in the lab!")