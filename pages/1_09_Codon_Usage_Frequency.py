import streamlit as st
from Bio.Seq import Seq
from collections import Counter
import pandas as pd
import plotly.express as px

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧬 TITAN TOOL 9: CODON USAGE FREQUENCY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("🧬 Module 9: Codon Usage Frequency")
st.markdown("Analyze the frequency of each codon in your DNA sequence to understand codon bias.")
st.markdown("---")

# --- INPUT SECTION ---
dna_input = st.text_area(
    "Enter DNA Sequence (Length must be a multiple of 3):", 
    "ATGCGTAAAATCGCCGGGTTTAAACCCGGG", 
    height=150, 
    key="codon_input"
)

calculate_btn = st.button("📊 Analyze Codons", use_container_width=True, type="primary")

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    clean_dna = dna_input.replace(" ", "").replace("\n", "").upper()
    
    if not clean_dna:
        st.error("❌ Please enter a valid DNA sequence.")
    elif len(clean_dna) % 3 != 0:
        st.error("❌ Sequence length must be a multiple of 3 for codon analysis!")
    elif any(char not in "ATCG" for char in clean_dna):
        st.error("❌ Invalid DNA! Only A, T, C, G are allowed.")
    else:
        seq = Seq(clean_dna)
        
        # Extract codons
        codons = [str(seq[i:i+3]) for i in range(0, len(seq), 3)]
        codon_counts = Counter(codons)
        
        total_codons = len(codons)
        unique_codons = len(codon_counts)
        
        # --- DISPLAY METRICS ---
        st.markdown("### 📊 Statistics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Codons", total_codons)
        c2.metric("Unique Codons", unique_codons)
        c3.metric("Sequence Length", f"{len(seq)} bp")
        
        st.markdown("---")
        
        # --- DATA TABLE ---
        st.markdown("### 📋 Codon Frequency Table")
        df = pd.DataFrame(list(codon_counts.items()), columns=['Codon', 'Count'])
        df['Frequency (%)'] = (df['Count'] / total_codons * 100).round(2)
        df = df.sort_values(by='Count', ascending=False)
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # --- CHART ---
        st.markdown("### 📊 Top 10 Codons Chart")
        top_10 = df.head(10)
        
        fig = px.bar(
            top_10, 
            x='Codon', 
            y='Count', 
            color='Count', 
            color_continuous_scale='Sunset', 
            text_auto=True
        )
        
        fig.update_layout(
            paper_bgcolor='#0a0e17',
            plot_bgcolor='#1a1f2e',
            font=dict(color='#e0e0e0'),
            margin=dict(t=20, b=40, l=40, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- THE "SMART LOCK" ---
        st.markdown("---")
        st.markdown("### 📥 Export Data")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Download PDF (Free)", use_container_width=True):
                st.info("📄 Generating PDF... (Coming in v1.1)")
        with c2:
            if st.button("📊 Download CSV (🔒 Explorer)", use_container_width=True):
                st.warning("🔒 **Titan Explorer Plan Required.**")