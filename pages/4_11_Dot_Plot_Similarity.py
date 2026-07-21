import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.title("🔵 Module 4.11: Dot Plot Similarity")
st.markdown("Visualize sequence similarity using a 2D Dot Plot matrix. Diagonal lines indicate matching regions!")
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    seq1 = st.text_area("Sequence 1 (X-axis)", "ATGCGTACGTAGCTAGCTAG", height=150)
with c2:
    seq2 = st.text_area("Sequence 2 (Y-axis)", "GCGTACGTAGCTAGCTAGATG", height=150)

window_size = st.slider("Window Size (Noise Filter)", 1, 10, 3)

if st.button(" Generate Dot Plot", type="primary", use_container_width=True):
    seq1 = seq1.replace(" ", "").upper()
    seq2 = seq2.replace(" ", "").upper()
    
    if not seq1 or not seq2:
        st.error("❌ Please enter both sequences!")
    else:
        with st.spinner("🧮 Calculating Matrix..."):
            len1, len2 = len(seq1), len(seq2)
            
            # Create dot plot matrix
            dot_matrix = np.zeros((len2, len1))
            
            for i in range(len1 - window_size + 1):
                for j in range(len2 - window_size + 1):
                    if seq1[i:i+window_size] == seq2[j:j+window_size]:
                        # Fill the window block
                        dot_matrix[j:j+window_size, i:i+window_size] = 1

            # Plotly Heatmap
            fig = go.Figure(data=go.Heatmap(
                z=dot_matrix,
                x=list(seq1),
                y=list(seq2),
                colorscale=[[0, '#0a0e17'], [1, '#d4af37']], # Titan Black to Gold
                showscale=False,
                hoverinfo='none'
            ))

            fig.update_layout(
                title="Dot Plot (Gold = Match, Black = Mismatch)",
                xaxis_title="Sequence 1",
                yaxis_title="Sequence 2",
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                font=dict(color='#e0e0e0'),
                xaxis=dict(tickfont=dict(size=10)),
                yaxis=dict(tickfont=dict(size=10), autorange='reversed') # Reversed to match standard dot plot
            )

            st.plotly_chart(fig, use_container_width=True)

            # Analysis
            total_matches = np.sum(dot_matrix)
            max_possible = min(len1, len2) * window_size
            similarity = (total_matches / max_possible) * 100 if max_possible > 0 else 0
            
            st.markdown("### 📈 Similarity Metrics")
            c1, c2 = st.columns(2)
            c1.metric("Total Matching Windows", f"{int(total_matches)}")
            c2.metric("Approx Similarity", f"{similarity:.2f}%")

            st.info("💡 **Dr. Titan's Tip:** Look for **diagonal lines** in the plot! A perfect diagonal from top-left to bottom-right means the sequences are identical. Breaks in the diagonal indicate insertions, deletions, or inversions!")