import streamlit as st
import math
from collections import Counter
import plotly.express as px

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 TITAN TOOL 11: NUCLEOTIDE FREQUENCY & SHANNON ENTROPY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("📊 Module 11: Frequency & Shannon Entropy")
st.markdown("Analyze base composition and calculate the Shannon Entropy to measure sequence complexity.")
st.markdown("---")

# --- INPUT SECTION ---
dna_input = st.text_area(
    "Enter DNA Sequence (5' to 3'):", 
    "ATGCGCTAGCTAGCTAGCTAGCTAGCATCGATCGATCGATCGATCGATCG", 
    height=150, 
    key="entropy_input"
)

calculate_btn = st.button("🧮 Calculate Entropy", use_container_width=True, type="primary")

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    clean_dna = dna_input.replace(" ", "").replace("\n", "").upper()
    
    if not clean_dna:
        st.error("❌ Please enter a valid DNA sequence.")
    elif any(char not in "ATCG" for char in clean_dna):
        st.error("❌ Invalid DNA! Only A, T, C, G are allowed.")
    else:
        length = len(clean_dna)
        counts = Counter(clean_dna)
        
        # Calculate Shannon Entropy: H = - Σ (p_i * log2(p_i))
        entropy = 0.0
        for base in ['A', 'T', 'C', 'G']:
            p = counts.get(base, 0) / length
            if p > 0:
                entropy -= p * math.log2(p)
                
        max_entropy = 2.0 # Maximum possible entropy for 4 bases (log2(4))
        complexity_pct = (entropy / max_entropy) * 100
        
        # --- DISPLAY METRICS ---
        st.markdown("### 📊 Complexity Statistics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📏 Sequence Length", f"{length} bp")
        c2.metric("🔢 Unique Bases", f"{len(counts)} / 4")
        c3.metric("🌡️ Shannon Entropy", f"{entropy:.3f} bits")
        c4.metric("📈 Complexity", f"{complexity_pct:.1f}%", help="Max is 100% (perfectly random sequence)")
        
        st.markdown("---")
        
        # --- PIE CHART ---
        st.markdown("### 🥧 Nucleotide Composition")
        
        # Ensure all 4 bases are in the chart even if count is 0
        chart_data = {
            'Nucleotide': ['Adenine (A)', 'Thymine (T)', 'Cytosine (C)', 'Guanine (G)'],
            'Count': [counts.get('A', 0), counts.get('T', 0), counts.get('C', 0), counts.get('G', 0)]
        }
        
        fig = px.pie(
            names=chart_data['Nucleotide'], 
            values=chart_data['Count'],
            color_discrete_map={
                'Adenine (A)': '#ff6b6b',
                'Thymine (T)': '#feca57',
                'Cytosine (C)': '#48dbfb',
                'Guanine (G)': '#1dd1a1'
            },
            hole=0.4
        )
        
        fig.update_layout(
            paper_bgcolor='#0a0e17',
            plot_bgcolor='#0a0e17',
            font=dict(color='#e0e0e0'),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- THE "SMART LOCK" ---
        st.markdown("---")
        st.markdown("### 📥 Export Data")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Download PDF Report (Free)", use_container_width=True):
                st.info("📄 Generating PDF report... (Feature coming in v1.1)")
        with c2:
            if st.button("📊 Download CSV Data (🔒 Explorer Plan)", use_container_width=True):
                st.warning("🔒 **Titan Explorer Plan Required.**\n\nUpgrade to unlock CSV exports and advanced analytics.")
                
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** A Shannon Entropy of **2.0 bits** means the sequence is perfectly random (all 4 bases are equally likely). Lower entropy indicates repetitive regions or low-complexity DNA, which is common in non-coding regions!")