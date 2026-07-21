import streamlit as st
from Bio.Align import MultipleSeqAlignment
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Phylo.TreeConstruction import DistanceCalculator
import plotly.figure_factory as ff
import numpy as np

st.title("📊 Module 4.08: Distance Matrix Calculator")
st.markdown("Calculate p-distance between sequences and visualize as a heatmap.")
st.markdown("---")

fasta_input = st.text_area("Enter Sequences in FASTA format", 
    """>Human
ATGCGTACGT
>Chimp
ATGCGTACGA
>Gorilla
ATGCGTACCT
>Orangutan
ATGCGTACGG""", height=200)

if st.button(" Calculate Distance Matrix", type="primary", use_container_width=True):
    try:
        records = []
        current_id = ""
        current_seq = ""
        for line in fasta_input.strip().split('\n'):
            if line.startswith('>'):
                if current_id:
                    records.append(SeqRecord(Seq(current_seq), id=current_id))
                current_id = line[1:].strip()
                current_seq = ""
            else:
                current_seq += line.strip()
        if current_id:
            records.append(SeqRecord(Seq(current_seq), id=current_id))
            
        if len(records) < 2:
            st.error("❌ Need at least 2 sequences!")
        else:
            alignment = MultipleSeqAlignment(records)
            calculator = DistanceCalculator('identity')
            dm = calculator.get_distance(alignment)
            
            # Convert to numpy array for heatmap
            labels = dm.names
            matrix = np.array(dm.matrix)
            
            st.markdown("### 🔥 Genetic Distance Heatmap")
            fig = ff.create_annotated_heatmap(
                z=matrix, x=labels, y=labels,
                colorscale='Viridis',
                annotation_text=np.round(matrix, 3).tolist(),
                showscale=True
            )
            fig.update_layout(
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                font=dict(color='#e0e0e0')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### 📋 Raw Distance Matrix")
            st.dataframe(pd.DataFrame(matrix, columns=labels, index=labels))
            
            st.info("💡 **Dr. Titan's Tip:** A distance matrix shows how genetically different species are. 0.0 means identical, 1.0 means completely different. This matrix is the input for building Phylogenetic Trees!")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")