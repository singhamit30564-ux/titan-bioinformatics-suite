import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.title("📉 Module 24: GC Skew & Cumulative GC Skew")
st.markdown("Analyze strand asymmetry to find the Origin of Replication (OriC) in bacterial genomes.")
st.markdown("---")

dna_seq = st.text_area("Enter Bacterial DNA Sequence", 
    "ATGCGCTAGCTAGCTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCG" * 10, height=150)

window_size = st.slider("Window Size (bp)", 100, 1000, 500)

if st.button("📊 Calculate GC Skew", use_container_width=True, type="primary"):
    seq = dna_seq.replace(" ", "").upper()
    
    if len(seq) < window_size:
        st.error("Sequence too short for this window size!")
    else:
        skews = []
        cum_skew = 0
        cum_skews = []
        positions = []
        
        for i in range(0, len(seq) - window_size + 1, window_size):
            window = seq[i:i+window_size]
            g = window.count('G')
            c = window.count('C')
            
            # Formula: (G - C) / (G + C)
            skew = (g - c) / (g + c) if (g + c) > 0 else 0
            skews.append(skew)
            
            cum_skew += (g - c)
            cum_skews.append(cum_skew)
            positions.append(i)
            
        # Plotting
        fig = go.Figure()
        
        # GC Skew Bar Chart
        fig.add_trace(go.Bar(
            x=positions, y=skews, name='GC Skew (Window)',
            marker_color=['#d4af37' if s > 0 else '#66fcf1' for s in skews]
        ))
        
        # Cumulative Skew Line
        fig.add_trace(go.Scatter(
            x=positions, y=cum_skews, name='Cumulative GC Skew',
            line=dict(color='#ff0055', width=3), yaxis='y2'
        ))
        
        fig.update_layout(
            title='GC Skew Analysis (Leading vs Lagging Strand)',
            xaxis_title='Genome Position (bp)',
            yaxis_title='GC Skew (G-C)/(G+C)',
            yaxis2=dict(title='Cumulative Skew', overlaying='y', side='right'),
            template='plotly_dark',
            paper_bgcolor='#0a0e17',
            plot_bgcolor='#1a1f2e'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 **Dr. Titan's Tip:** In bacteria, the **Origin of Replication (OriC)** is usually where the Cumulative GC Skew shifts from negative to positive (minimum), and the **Terminus (Ter)** is at the maximum shift! This helps in genome assembly.")