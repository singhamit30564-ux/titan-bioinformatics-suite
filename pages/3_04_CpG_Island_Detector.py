import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.title("🏝️ Module 3.04: CpG Island Detector")
st.markdown("Identify CpG Islands in DNA sequences using the Observed/Expected (O/E) ratio and sliding window.")
st.markdown("---")

dna_seq = st.text_area("Enter DNA Sequence (or paste a promoter region)", 
    "GCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCGCG......", 
    height=150)

c1, c2 = st.columns(2)
with c1:
    window_size = st.slider("Window Size (bp)", 50, 500, 100)
with c2:
    step_size = st.slider("Step Size (bp)", 1, 50, 10)

oe_threshold = st.slider("O/E Ratio Threshold (Standard > 0.6)", 0.4, 1.0, 0.6, 0.05)
gc_threshold = st.slider("GC Content Threshold (%)", 40, 70, 50)

if st.button(" Detect CpG Islands", type="primary", use_container_width=True):
    seq = dna_seq.replace(" ", "").upper()
    
    if len(seq) < window_size:
        st.error(f"❌ Sequence too short! Need at least {window_size} bp for this window size.")
    else:
        with st.spinner("🧮 Calculating O/E Ratios..."):
            positions = []
            oe_ratios = []
            gc_contents = []
            
            # Sliding Window Algorithm
            for i in range(0, len(seq) - window_size + 1, step_size):
                window = seq[i:i+window_size]
                
                n_c = window.count('C')
                n_g = window.count('G')
                n_cg = sum(1 for j in range(len(window)-1) if window[j:j+2] == 'CG')
                
                # Observed/Expected Ratio Formula
                # OE = (Count(CG) * N) / (Count(C) * Count(G))
                if n_c > 0 and n_g > 0:
                    oe_ratio = (n_cg * window_size) / (n_c * n_g)
                else:
                    oe_ratio = 0
                    
                gc_pct = ((n_c + n_g) / window_size) * 100
                
                positions.append(i)
                oe_ratios.append(oe_ratio)
                gc_contents.append(gc_pct)
            
            # Plotting
            fig = go.Figure()
            
            # O/E Ratio Line
            fig.add_trace(go.Scatter(
                x=positions, y=oe_ratios, name='Obs/Exp Ratio',
                line=dict(color='#d4af37', width=2), fill='tozeroy'
            ))
            
            # GC Content Line (Secondary Y-axis)
            fig.add_trace(go.Scatter(
                x=positions, y=gc_contents, name='GC %',
                line=dict(color='#66fcf1', width=2, dash='dot'), yaxis='y2'
            ))
            
            # Threshold Lines
            fig.add_hline(y=oe_threshold, line_dash="dash", line_color="#ff0055", 
                         annotation_text=f"O/E Threshold ({oe_threshold})")
            fig.add_hline(y=gc_threshold, line_dash="dash", line_color="#ffffff", 
                         annotation_text=f"GC Threshold ({gc_threshold}%)", yaxis="y2")
            
            fig.update_layout(
                title="CpG Island Detection Analysis",
                xaxis_title="Genome Position (bp)",
                yaxis_title="Observed/Expected Ratio",
                yaxis2=dict(title="GC Content (%)", overlaying="y", side="right"),
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                font=dict(color='#e0e0e0')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary Metrics
            st.markdown("### 📊 Detection Summary")
            islands_found = sum(1 for oe, gc in zip(oe_ratios, gc_contents) if oe >= oe_threshold and gc >= gc_threshold)
            max_oe = max(oe_ratios)
            
            c1, c2 = st.columns(2)
            c1.metric("Potential CpG Islands", f"{islands_found}")
            c2.metric("Max O/E Ratio Found", f"{max_oe:.2f}")
            
            st.info("💡 **Dr. Titan's Tip:** CpG Islands are regions where Cytosine is followed by Guanine more frequently than expected. They are crucial markers for gene promoters and are often unmethylated in active genes!")