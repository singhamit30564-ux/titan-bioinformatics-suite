import streamlit as st
from Bio.Seq import Seq
from Bio.SeqUtils import gc_fraction, MeltingTemp
import pandas as pd
import plotly.graph_objects as go

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 TITAN TOOL 4: GC CONTENT, MELTING TEMP & SLIDING WINDOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title(" Module 4: GC Content, Tm & Sliding Window")
st.markdown("Advanced analysis: Nearest Neighbor Tm calculation and GC% distribution across your sequence.")
st.markdown("---")

# --- INPUT SECTION ---
dna_input = st.text_area("Enter DNA Sequence (5' to 3'):", "ATGCGCTAGCTAGCTAGCTAGCTAGCATCGATCGATCGATCGATCGATCG", height=150, key="gc_melting_input")

col1, col2 = st.columns([3, 1])
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    calculate_btn = st.button("📈 Analyze Sequence", use_container_width=True, type="primary")

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
            length = len(seq)
            
            # 1. Overall GC Content
            gc_content = gc_fraction(seq) * 100
            
            # 2. Melting Temperature (Advanced: Nearest Neighbor Method)
            # We use Tm_NN for high accuracy, falling back to Wallace if sequence is too short/complex
            try:
                tm_nn = MeltingTemp.Tm_NN(seq)
                tm_method = "Nearest Neighbor (High Accuracy)"
            except Exception:
                tm_nn = MeltingTemp.Tm_Wallace(seq)
                tm_method = "Wallace Rule (Basic)"

            # --- DISPLAY METRICS ---
            st.markdown("### 📈 Analysis Results")
            met_col1, met_col2, met_col3 = st.columns(3)
            met_col1.metric(label="🧬 Overall GC Content", value=f"{gc_content:.2f}%")
            met_col2.metric(label="🌡️ Melting Temp (Tm)", value=f"{tm_nn:.2f} °C", delta=tm_method)
            met_col3.metric(label="📏 Sequence Length", value=f"{length} bp")
            
            st.markdown("---")
            
            # 3. SLIDING WINDOW PLOT (The Pro Feature)
            st.markdown("### 🌊 GC% Sliding Window Analysis")
            st.caption("Shows how GC content varies across different regions of your sequence.")
            
            if length >= 20:
                window_size = 20
                step = 5
                positions = []
                gc_values = []
                
                for i in range(0, length - window_size + 1, step):
                    window_seq = seq[i:i+window_size]
                    positions.append(i + window_size//2) # Center of window
                    gc_values.append(gc_fraction(window_seq) * 100)
                
                # Create Plotly Line Chart
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=positions, 
                    y=gc_values,
                    mode='lines+markers',
                    name='GC%',
                    line=dict(color='#d4af37', width=3), # Gold line
                    marker=dict(color='#66fcf1', size=6)  # Cyan dots
                ))
                
                # Add a reference line at 50%
                fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50% Reference")
                
                fig.update_layout(
                    title="GC% Distribution (Window: 20bp, Step: 5bp)",
                    xaxis_title="Position (bp)",
                    yaxis_title="GC Content (%)",
                    yaxis=dict(range=[0, 100]),
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#1a1f2e',
                    font=dict(color='#e0e0e0'),
                    margin=dict(t=40, b=40, l=40, r=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Sequence is too short (< 20bp) for Sliding Window analysis. Try a longer sequence!")
            
            # --- THE "SMART LOCK" ---
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
            st.error(f"️ Calculation Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** The **Nearest Neighbor (NN)** method calculates Tm by looking at how adjacent base pairs stack together. It's much more accurate than the simple Wallace rule, especially for sequences longer than 14bp!")