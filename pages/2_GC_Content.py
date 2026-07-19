import streamlit as st
from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction, MeltingTemp
import pandas as pd
import plotly.express as px

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 TITAN TOOL 2: GC CONTENT & MELTING TEMPERATURE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("📊 Module 2: GC Content & Melting Temp")
st.markdown("Calculate the Guanine-Cytosine percentage and the exact Melting Temperature (Tm) of your DNA sequence.")
st.markdown("---")

# --- INPUT SECTION ---
col1, col2 = st.columns([3, 1])
with col1:
    dna_input = st.text_area("Enter DNA Sequence (5' to 3'):", "ATGCGCTAGCTAGCTAGCTAGCTAGCATCGATCG", height=150, key="gc_input")

with col2:
    st.markdown("<br>", unsafe_allow_html=True) # Spacer
    calculate_btn = st.button(" Analyze Sequence", use_container_width=True, type="primary")

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    # Clean the input
    clean_dna = dna_input.replace(" ", "").replace("\n", "").upper()
    
    if not clean_dna:
        st.error("❌ Please enter a valid DNA sequence.")
    elif any(char not in "ATCG" for char in clean_dna):
        st.error("❌ Invalid DNA! Only A, T, C, G are allowed.")
    else:
        try:
            seq = Seq(clean_dna)
            
            # 1. Calculate GC Content
            gc_content = gc_fraction(seq) * 100
            
            # 2. Calculate Melting Temperature (Using Wallace Rule for short/medium sequences)
            tm = MeltingTemp.Tm_Wallace(seq)
            
            # 3. Calculate AT Content
            at_content = 100 - gc_content
            
            # --- DISPLAY METRICS ---
            st.markdown("### 📈 Analysis Results")
            met_col1, met_col2, met_col3 = st.columns(3)
            met_col1.metric(label="🧬 GC Content", value=f"{gc_content:.2f}%", delta="Ideal: 40-60%")
            met_col2.metric(label="🌡️ Melting Temp (Tm)", value=f"{tm:.2f} °C")
            met_col3.metric(label="📏 Sequence Length", value=f"{len(seq)} bp")
            
            st.markdown("---")
            
            # --- INTERACTIVE PLOTLY CHART ---
            st.markdown("### 🥧 Nucleotide Distribution")
            
            # Create data for pie chart
            df_chart = pd.DataFrame({
                'Nucleotide Group': ['GC Content (Guanine-Cytosine)', 'AT Content (Adenine-Thymine)'],
                'Percentage': [gc_content, at_content]
            })
            
            # Create Plotly Pie Chart
            fig = px.pie(
                df_chart, 
                values='Percentage', 
                names='Nucleotide Group',
                color_discrete_map={
                    'GC Content (Guanine-Cytosine)': '#d4af37', # Gold
                    'AT Content (Adenine-Thymine)': '#66fcf1'  # Cyan
                },
                hole=0.4 # Donut chart style
            )
            
            fig.update_layout(
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#0a0e17',
                font=dict(color='#e0e0e0'),
                margin=dict(t=0, b=0, l=0, r=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # --- THE "SMART LOCK" (CSV GATING) ---
            st.markdown("---")
            st.markdown("### 📥 Export Data")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📄 Download PDF Report (Free)", use_container_width=True):
                    st.info("📄 Generating PDF report... (Feature coming in v1.1)")
                    
            with col_btn2:
                if st.button("📊 Download CSV Data (🔒 Explorer Plan)", use_container_width=True):
                    st.warning("🔒 **Titan Explorer Plan Required.**\n\nUpgrade to unlock CSV exports, batch processing, and advanced analytics.")
                    
        except Exception as e:
            st.error(f"⚠️ Calculation Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** A GC content between **40% and 60%** is generally ideal for PCR primers. High GC content increases the melting temperature, making the DNA strand harder to separate!")