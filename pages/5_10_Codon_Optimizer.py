import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from Bio.Seq import Seq
from Bio.Data import CodonTable
import math
from datetime import datetime
import io

# --- PAGE CONFIG ---
st.set_page_config(page_title="Codon Optimizer", page_icon="", layout="wide")

# --- CODON FREQUENCY TABLES (Relative per amino acid, sum=1.0) ---
# Adapted from NCBI Codon Usage Database (Standard Genetic Code)
CODON_FREQS = {
    "E. coli (K12)": {
        'TTT':0.40,'TTC':0.60,'TTA':0.14,'TTG':0.13,'CTT':0.12,'CTC':0.10,'CTA':0.04,'CTG':0.47,
        'ATT':0.49,'ATC':0.39,'ATA':0.12,'ATG':1.00,
        'GTT':0.28,'GTC':0.20,'GTA':0.17,'GTG':0.35,
        'TCT':0.18,'TCC':0.15,'TCA':0.14,'TCG':0.09,'AGT':0.23,'AGC':0.21,
        'CCT':0.18,'CCC':0.14,'CCA':0.19,'CCG':0.49,
        'ACT':0.21,'ACC':0.28,'ACA':0.19,'ACG':0.32,
        'GCT':0.22,'GCC':0.24,'GCA':0.18,'GCG':0.36,
        'TAT':0.58,'TAC':0.42,'TAA':0.61,'TAG':0.09,'TGA':0.30,
        'CAT':0.57,'CAC':0.43,'CAA':0.66,'CAG':0.34,
        'AAT':0.49,'AAC':0.51,'AAA':0.74,'AAG':0.26,
        'GAT':0.63,'GAC':0.37,'GAA':0.68,'GAG':0.32,
        'TGT':0.46,'TGC':0.54,'TGG':1.00,
        'CGT':0.36,'CGC':0.36,'CGA':0.07,'CGG':0.11,'AGA':0.07,'AGG':0.03,
        'GGT':0.34,'GGC':0.37,'GGA':0.13,'GGG':0.16
    },
    "Homo sapiens": {
        'TTT':0.45,'TTC':0.55,'TTA':0.07,'TTG':0.13,'CTT':0.13,'CTC':0.20,'CTA':0.07,'CTG':0.40,
        'ATT':0.40,'ATC':0.37,'ATA':0.23,'ATG':1.00,
        'GTT':0.18,'GTC':0.24,'GTA':0.11,'GTG':0.47,
        'TCT':0.16,'TCC':0.22,'TCA':0.15,'TCG':0.06,'AGT':0.16,'AGC':0.25,
        'CCT':0.25,'CCC':0.32,'CCA':0.27,'CCG':0.16,
        'ACT':0.24,'ACC':0.36,'ACA':0.17,'ACG':0.23,
        'GCT':0.26,'GCC':0.40,'GCA':0.23,'GCG':0.11,
        'TAT':0.43,'TAC':0.57,'TAA':0.27,'TAG':0.20,'TGA':0.53,
        'CAT':0.41,'CAC':0.59,'CAA':0.25,'CAG':0.75,
        'AAT':0.46,'AAC':0.54,'AAA':0.42,'AAG':0.58,
        'GAT':0.45,'GAC':0.55,'GAA':0.42,'GAG':0.58,
        'TGT':0.45,'TGC':0.55,'TGG':1.00,
        'CGT':0.08,'CGC':0.18,'CGA':0.11,'CGG':0.21,'AGA':0.20,'AGG':0.22,
        'GGT':0.25,'GGC':0.37,'GGA':0.13,'GGG':0.25
    },
    "S. cerevisiae": {
        'TTT':0.43,'TTC':0.57,'TTA':0.14,'TTG':0.41,'CTT':0.12,'CTC':0.09,'CTA':0.29,'CTG':0.10,
        'ATT':0.45,'ATC':0.35,'ATA':0.20,'ATG':1.00,
        'GTT':0.23,'GTC':0.20,'GTA':0.15,'GTG':0.42,
        'TCT':0.17,'TCC':0.18,'TCA':0.25,'TCG':0.05,'AGT':0.20,'AGC':0.15,
        'CCT':0.25,'CCC':0.15,'CCA':0.25,'CCG':0.35,
        'ACT':0.20,'ACC':0.30,'ACA':0.20,'ACG':0.30,
        'GCT':0.25,'GCC':0.25,'GCA':0.20,'GCG':0.30,
        'TAT':0.45,'TAC':0.55,'TAA':0.30,'TAG':0.15,'TGA':0.55,
        'CAT':0.50,'CAC':0.50,'CAA':0.25,'CAG':0.75,
        'AAT':0.55,'AAC':0.45,'AAA':0.70,'AAG':0.30,
        'GAT':0.60,'GAC':0.40,'GAA':0.65,'GAG':0.35,
        'TGT':0.50,'TGC':0.50,'TGG':1.00,
        'CGT':0.15,'CGC':0.15,'CGA':0.15,'CGG':0.15,'AGA':0.20,'AGG':0.20,
        'GGT':0.25,'GGC':0.25,'GGA':0.25,'GGG':0.25
    }
}

# --- HELPER FUNCTIONS ---
def validate_dna(seq):
    seq = seq.upper().replace(" ", "").replace("\n", "")
    valid_chars = set("ATCG")
    if not seq:
        return None, " Sequence is empty."
    if len(seq) % 3 != 0:
        return None, f"❌ Length ({len(seq)}) is not a multiple of 3. Incomplete codons detected."
    invalid = set(seq) - valid_chars
    if invalid:
        return None, f"❌ Invalid characters found: {invalid}. Use only A, T, C, G."
    return seq, None

def calculate_cai(seq, freq_table):
    codons = [seq[i:i+3] for i in range(0, len(seq), 3)]
    table = CodonTable.unambiguous_dna_by_id[1]
    valid_codons = [c for c in codons if c not in ["ATG", "TAA", "TAG", "TGA"] and c in table.forward_table]
    if not valid_codons:
        return 0.0
    
    log_sum = 0.0
    for codon in valid_codons:
        aa = table.forward_table[codon]
        synonyms = [c for c, a in table.forward_table.items() if a == aa]
        max_freq = max(freq_table.get(s, 0) for s in synonyms)
        codon_freq = freq_table.get(codon, 0)
        w = codon_freq / max_freq if max_freq > 0 else 0
        log_sum += math.log(w + 1e-9)
    return math.exp(log_sum / len(valid_codons))

def optimize_sequence(seq, freq_table):
    codons = [seq[i:i+3] for i in range(0, len(seq), 3)]
    table = CodonTable.unambiguous_dna_by_id[1]
    optimized = []
    for codon in codons:
        aa = table.forward_table.get(codon)
        if aa:
            synonyms = [c for c, a in table.forward_table.items() if a == aa]
            best = max(synonyms, key=lambda c: freq_table.get(c, 0))
            optimized.append(best)
        else:
            optimized.append(codon)
    return "".join(optimized)

# --- UI ---
st.title("🧬 Module 5.10: Codon Usage Optimizer")
st.markdown("Optimize DNA sequences for maximum heterologous expression using organism-specific codon bias.")
st.markdown("---")

# INPUTS
dna_input = st.text_area("Enter Coding DNA Sequence (CDS, 5'→3')", height=120, placeholder="e.g., ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG")
organism = st.selectbox("🌍 Target Organism", list(CODON_FREQS.keys()))
show_advanced = st.checkbox("📊 Show Detailed Codon Comparison")

if st.button("🚀 Optimize & Analyze", type="primary", use_container_width=True):
    seq, error = validate_dna(dna_input)
    if error:
        st.error(error)
    else:
        with st.spinner("🧮 Calculating CAI, GC%, and optimizing codons..."):
            org_data = CODON_FREQS[organism]
            
            # Metrics
            gc_orig = (seq.count('G') + seq.count('C')) / len(seq) * 100
            optimized_seq = optimize_sequence(seq, org_data)
            gc_opt = (optimized_seq.count('G') + optimized_seq.count('C')) / len(optimized_seq) * 100
            cai_orig = calculate_cai(seq, org_data)
            cai_opt = calculate_cai(optimized_seq, org_data)
            
            # Codon Frequency Analysis
            orig_codons = [seq[i:i+3] for i in range(0, len(seq), 3)]
            opt_codons = [optimized_seq[i:i+3] for i in range(0, len(optimized_seq), 3)]
            
            df_orig = pd.Series(orig_codons).value_counts().reset_index()
            df_orig.columns = ['Codon', 'Original Count']
            df_opt = pd.Series(opt_codons).value_counts().reset_index()
            df_opt.columns = ['Codon', 'Optimized Count']
            
            comp_df = pd.merge(df_orig, df_opt, on='Codon', how='outer').fillna(0)
            comp_df['Change'] = comp_df['Optimized Count'] - comp_df['Original Count']
            comp_df = comp_df.sort_values('Original Count', ascending=False)
            
            # DISPLAY
            st.markdown("### 📈 Optimization Results")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Original CAI", f"{cai_orig:.3f}")
            m2.metric("Optimized CAI", f"{cai_opt:.3f}", delta=f"+{cai_opt-cai_orig:.3f}")
            m3.metric("Original GC%", f"{gc_orig:.1f}%")
            m4.metric("Optimized GC%", f"{gc_opt:.1f}%")
            
            st.success(f"✅ CAI improved by **{((cai_opt-cai_orig)/cai_orig)*100:.1f}%** for {organism}")
            
            # VISUALIZATION
            if show_advanced:
                st.markdown("### 📊 Codon Usage Shift")
                fig = px.bar(comp_df, x='Codon', y=['Original Count', 'Optimized Count'],
                             barmode='group', title="Original vs Optimized Codon Frequencies",
                             color_discrete_sequence=['#66fcf1', '#d4af37'])
                fig.update_layout(template="plotly_dark", paper_bgcolor='#0a0e17', plot_bgcolor='#1a1f2e',
                                  font=dict(color='#e0e0e0'), xaxis_title="Codon", yaxis_title="Frequency")
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(comp_df.style.highlight_max(subset=['Optimized Count'], color='#66fcf133'), use_container_width=True)
            
            # SEQUENCE OUTPUT
            st.markdown("### 🧬 Optimized Sequence")
            st.code(optimized_seq, language="dna")
            
            # EXPORT
            st.markdown("---")
            st.markdown("### 📥 Export Results")
            col1, col2 = st.columns(2)
            
            csv = comp_df.to_csv(index=False).encode('utf-8')
            col1.download_button("📄 Download Codon Table (CSV)", data=csv, file_name="codon_optimization.csv", mime="text/csv", use_container_width=True)
            
            fasta = f">Optimized_CDS_{organism.replace(' ','_')}\n{optimized_seq}\n"
            col2.download_button("🧬 Download Optimized FASTA", data=fasta, file_name="optimized_sequence.fasta", mime="text/plain", use_container_width=True)
            
            st.info("💡 **Dr. Titan's Tip:** CAI > 0.8 indicates excellent adaptation to the host's tRNA pool. Avoid optimizing regulatory motifs (Kozak, Shine-Dalgarno) or restriction sites unless explicitly required!")

# SIDEBAR
with st.sidebar:
    st.markdown("### ℹ️ How It Works")
    st.markdown("""
    1. **Paste CDS** (must be multiple of 3)
    2. **Select organism** to load its codon bias table
    3. **Algorithm** replaces rare codons with host-preferred synonyms
    4. **CAI** (Codon Adaptation Index) measures adaptation quality
    5. **Export** CSV/FASTA for cloning or synthesis
    """)
    st.markdown("### 🎯 Target CAI Values")
    st.markdown("""
    - **< 0.5**: Poor adaptation
    - **0.5–0.8**: Moderate
    - **> 0.8**: Excellent for high expression
    """)