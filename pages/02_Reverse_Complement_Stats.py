import streamlit as st
from Bio.Seq import Seq
import pandas as pd
import plotly.express as px

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧬 TITAN TOOL 3: REVERSE COMPLEMENT & SEQUENCE STATS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("🧬 Module 3: Reverse Complement & Stats")
st.markdown("Generate the reverse complement of your DNA sequence and get a full statistical breakdown.")
st.markdown("---")

# --- INPUT SECTION ---
dna_input = st.text_area("Enter DNA Sequence (5' to 3'):", "ATGCGCTAGCTAGCTAGCTAGCTAGCATCGATCG", height=150, key="rev_comp_input")

col1, col2 = st.columns([3, 1])
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    calculate_btn = st.button("🔄 Analyze Sequence", use_container_width=True, type="primary")

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    clean_dna = dna_input.replace(" ", "").replace("\n", "").upper()
    
    if not clean_dna:
        st.error("❌ Please enter a valid DNA sequence.")
    elif any(char not in "ATCG" for char in clean_dna):
        st.error("❌ Invalid DNA! Only A, T, C, G are allowed.")
    else:
        try:
            seq = Seq(clean_dna)
            rev_comp = str(seq.reverse_complement())
            
            # Calculate Stats
            length = len(seq)
            count_a = seq.count('A')
            count_t = seq.count('T')
            count_c = seq.count('C')
            count_g = seq.count('G')
            gc_percent = ((count_c + count_g) / length) * 100
            
            # --- DISPLAY RESULTS ---
            st.markdown("### 📊 Sequence Statistics")
            met_col1, met_col2, met_col3, met_col4 = st.columns(4)
            met_col1.metric("📏 Length", f"{length} bp")
            met_col2.metric(" GC Content", f"{gc_percent:.2f}%")
            met_col3.metric(" AT Content", f"{100 - gc_percent:.2f}%")
            met_col4.metric("⚖️ AT/GC Ratio", f"{(count_a + count_t) / (count_c + count_g):.2f}" if (count_c + count_g) > 0 else "N/A")
            
            st.markdown("---")
            
            st.markdown("### 🔄 Reverse Complement")
            st.code(rev_comp, language="text")
            
            st.markdown("---")
            
            # --- INTERACTIVE PIE CHART ---
            st.markdown("### 🥧 Nucleotide Composition")
            
            df_chart = pd.DataFrame({
                'Nucleotide': ['Adenine (A)', 'Thymine (T)', 'Cytosine (C)', 'Guanine (G)'],
                'Count': [count_a, count_t, count_c, count_g]
            })
            
            fig = px.pie(
                df_chart, 
                values='Count', 
                names='Nucleotide',
                color_discrete_map={
                    'Adenine (A)': '#ff6b6b',   # Red
                    'Thymine (T)': '#feca57',   # Yellow
                    'Cytosine (C)': '#48dbfb',  # Cyan
                    'Guanine (G)': '#1dd1a1'    # Green
                },
                hole=0.4
            )
            
            fig.update_layout(
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#0a0e17',
                font=dict(color='#e0e0e0'),
                margin=dict(t=0, b=0, l=0, r=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # --- THE "SMART LOCK" ---
            st.markdown("---")
            st.markdown("###  Export Data")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📄 Download PDF Report (Free)", use_container_width=True):
                    st.info("📄 Generating PDF report... (Feature coming in v1.1)")
                    
            with col_btn2:
                if st.button("📊 Download CSV Data (🔒 Explorer Plan)", use_container_width=True):
                    st.warning(" **Titan Explorer Plan Required.**\n\nUpgrade to unlock CSV exports, batch processing, and advanced analytics.")
                    
        except Exception as e:
            st.error(f"⚠️ Calculation Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** The reverse complement is crucial for understanding the opposite strand of DNA. In a double helix, the two strands run in opposite directions (anti-parallel), so the 5' to 3' strand is the reverse complement of the 3' to 5' strand!")