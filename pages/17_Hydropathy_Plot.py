import streamlit as st
import plotly.graph_objects as go

st.title("📉 Module 29: Protein Hydropathy Plot")
st.markdown("Identify hydrophobic (transmembrane) and hydrophilic regions.")
st.markdown("---")

prot_seq = st.text_area("Enter Protein Sequence", "MRSLLILVLCFLPAALGKVR").replace(" ", "").upper()
window = st.slider("Window Size", 5, 15, 9)

if st.button("Plot Hydropathy", type="primary"):
    # Kyte-Doolittle scale
    kd_scale = {'I': 4.5, 'V': 4.2, 'L': 3.8, 'F': 2.8, 'C': 2.5, 'M': 1.9, 'A': 1.8, 'G': -0.4, 'T': -0.7, 'S': -0.8, 'W': -0.9, 'Y': -1.3, 'P': -1.6, 'H': -3.2, 'E': -3.5, 'Q': -3.5, 'D': -3.5, 'N': -3.5, 'K': -3.9, 'R': -4.5}
    
    scores = []
    positions = []
    
    for i in range(len(prot_seq) - window + 1):
        window_seq = prot_seq[i:i+window]
        avg_score = sum(kd_scale.get(aa, 0) for aa in window_seq) / window
        scores.append(avg_score)
        positions.append(i + window // 2)
        
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=positions, y=scores, mode='lines+markers', line=dict(color='#66fcf1', width=2), name='Hydropathy'))
    fig.add_hline(y=0, line_dash="dash", line_color="white")
    fig.add_hrect(y0=1.6, y1=5, fillcolor="rgba(212, 175, 55, 0.2)", line_width=0, annotation_text="Hydrophobic (Potential Transmembrane)")
    
    fig.update_layout(title="Kyte-Doolittle Hydropathy Plot", xaxis_title="Amino Acid Position", yaxis_title="Hydropathy Score", template="plotly_dark", paper_bgcolor='#0a0e17', plot_bgcolor='#1a1f2e')
    st.plotly_chart(fig, use_container_width=True)
    st.info("💡 **Dr. Titan's Tip:** Scores > 1.6 indicate hydrophobic regions, often representing transmembrane alpha-helices!")