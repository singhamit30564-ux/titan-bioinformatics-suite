import streamlit as st
import plotly.graph_objects as go
import numpy as np
from collections import Counter

st.title("🎨 Module 4.09: Sequence Logo Generator")
st.markdown("Visualize position-specific sequence conservation as a sequence logo.")
st.markdown("---")

fasta_input = st.text_area("Enter Aligned Sequences in FASTA format", 
    """>Seq1
ATGCGTACG
>Seq2
ATGCGTACG
>Seq3
ATGCATACG
>Seq4
ATGCGTACA
>Seq5
ATGCGTACG""", height=200)

if st.button("🎨 Generate Sequence Logo", type="primary", use_container_width=True):
    try:
        # Parse sequences
        sequences = []
        for line in fasta_input.strip().split('\n'):
            if not line.startswith('>'):
                sequences.append(line.strip().upper())
        
        if not sequences:
            st.error("❌ No sequences found!")
        else:
            seq_length = len(sequences[0])
            
            # Calculate position-specific frequencies
            positions = list(range(seq_length))
            bases = ['A', 'T', 'C', 'G']
            
            logo_data = {base: [] for base in bases}
            total_info_content = []
            
            for pos in range(seq_length):
                pos_bases = [seq[pos] for seq in sequences if pos < len(seq)]
                counts = Counter(pos_bases)
                total = len(pos_bases)
                
                # Calculate information content (simplified)
                frequencies = {base: counts.get(base, 0) / total for base in bases}
                
                # Shannon entropy (simplified)
                entropy = 0
                for base in bases:
                    if frequencies[base] > 0:
                        import math
                        entropy -= frequencies[base] * math.log2(frequencies[base])
                
                info_content = 2 - entropy  # Max 2 bits for DNA
                total_info_content.append(info_content)
                
                for base in bases:
                    logo_data[base].append(frequencies[base] * info_content)
            
            # Create stacked bar chart (Sequence Logo)
            fig = go.Figure()
            
            colors = {'A': '#00CC00', 'T': '#FF0000', 'C': '#0000CC', 'G': '#FFA500'}
            
            for base in bases:
                fig.add_trace(go.Bar(
                    x=positions,
                    y=logo_data[base],
                    name=base,
                    marker_color=colors[base],
                    stackgroup='one'
                ))
            
            fig.update_layout(
                title="Sequence Logo - Position-Specific Conservation",
                xaxis_title="Position",
                yaxis_title="Information Content (bits)",
                barmode='stack',
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### 📊 Interpretation")
            st.info("💡 **Dr. Titan's Tip:** Taller stacks = higher conservation. The relative height of each letter shows its frequency at that position. Tall single letters indicate highly conserved positions!")
            
    except Exception as e:
        st.error(f"❌ Logo Generation Error: {e}")
        import traceback
        st.code(traceback.format_exc())