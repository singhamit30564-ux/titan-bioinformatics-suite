import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.title("🎨 Module 3.06: Chaos Game Representation (CGR)")
st.markdown("Visualize DNA sequences as a 2D fractal image. Each nucleotide maps to a specific corner!")
st.markdown("---")

dna_seq = st.text_area("Enter DNA Sequence", 
    "ATGCGTACGTAGCTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG", 
    height=150)

max_points = st.slider("Max Points to Plot (Higher = More Detail, Slower)", 1000, 20000, 5000)

if st.button("🌌 Generate CGR Fractal", type="primary", use_container_width=True):
    seq = dna_seq.replace(" ", "").upper()
    
    # Filter only valid nucleotides
    valid_seq = [base for base in seq if base in 'ACGT']
    
    if len(valid_seq) == 0:
        st.error("❌ No valid DNA sequence (A, C, G, T) found!")
    else:
        with st.spinner("🧮 Calculating Fractal Coordinates..."):
            # Limit points for performance
            plot_seq = valid_seq[:max_points]
            
            # CGR Corner Coordinates
            corners = {
                'A': (0.0, 0.0),
                'C': (0.0, 1.0),
                'G': (1.0, 1.0),
                'T': (1.0, 0.0)
            }
            
            x_coords = []
            y_coords = []
            
            # Start at center
            current_x, current_y = 0.5, 0.5
            
            for base in plot_seq:
                corner_x, corner_y = corners[base]
                # Move halfway to the corner
                current_x = (current_x + corner_x) / 2.0
                current_y = (current_y + corner_y) / 2.0
                
                x_coords.append(current_x)
                y_coords.append(current_y)
            
            # Plotly Scatter Plot (Fractal)
            fig = go.Figure()
            
            fig.add_trace(go.Scattergl( # Scattergl for fast rendering of many points
                x=x_coords,
                y=y_coords,
                mode='markers',
                marker=dict(
                    size=2,
                    color='#d4af37', # Titan Gold
                    opacity=0.3      # Transparency creates the fractal density effect
                ),
                hoverinfo='skip'
            ))
            
            fig.update_layout(
                title="Chaos Game Representation (CGR) of DNA",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.05, 1.05]),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-0.05, 1.05]),
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#000000', # Pure black for maximum fractal contrast
                margin=dict(l=0, r=0, t=40, b=0),
                height=600
            )
            
            # Add corner labels
            fig.add_annotation(x=0.0, y=0.0, text="A", showarrow=False, font=dict(color='#66fcf1', size=16))
            fig.add_annotation(x=0.0, y=1.0, text="C", showarrow=False, font=dict(color='#66fcf1', size=16))
            fig.add_annotation(x=1.0, y=1.0, text="G", showarrow=False, font=dict(color='#66fcf1', size=16))
            fig.add_annotation(x=1.0, y=0.0, text="T", showarrow=False, font=dict(color='#66fcf1', size=16))
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### 📊 Sequence Stats")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total A", seq.count('A'))
            c2.metric("Total C", seq.count('C'))
            c3.metric("Total G", seq.count('G'))
            c4.metric("Total T", seq.count('T'))
            
            st.info("💡 **Dr. Titan's Tip:** CGR creates a unique 'fingerprint' for any DNA sequence. Similar sequences produce similar fractal patterns! Notice how the density of points reveals hidden repeating motifs in the genome.")