import streamlit as st
from Bio import AlignIO
from Bio.Align import MultipleSeqAlignment
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Align import MultipleSeqAlignment
import plotly.graph_objects as go
import pandas as pd

st.title(" Module 4.05: Multiple Sequence Alignment (MSA)")
st.markdown("Align 3 or more sequences and visualize conservation.")
st.markdown("---")

fasta_input = st.text_area("Enter Sequences in FASTA format", 
    """>Seq1
ATGCGTACGTAGCTAG
>Seq2
ATGCGTACGAAGCTAG
>Seq3
ATGCGTGCCTAGCTAG
>Seq4
ATGCA_TACGTAGCTAG""", height=250)

if st.button("🔬 Perform MSA", type="primary", use_container_width=True):
    try:
        # Parse sequences
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
        
        if len(records) < 3:
            st.error("❌ Need at least 3 sequences for MSA!")
        else:
            # Simple MSA (in real app, use ClustalW or MUSCLE)
            # For demo, we'll pad sequences to same length
            max_len = max(len(rec.seq) for rec in records)
            aligned_seqs = [str(rec.seq).ljust(max_len, '-') for rec in records]
            
            st.markdown("### 📋 Aligned Sequences")
            for i, (rec, aligned) in enumerate(zip(records, aligned_seqs), 1):
                st.code(f">{rec.id}\n{aligned}", language="text")
            
            # Conservation analysis
            st.markdown("### 📈 Conservation Analysis")
            
            conservation_scores = []
            positions = list(range(max_len))
            
            for pos in range(max_len):
                bases = [seq[pos] for seq in aligned_seqs if pos < len(seq)]
                if bases:
                    most_common = max(set(bases), key=bases.count)
                    conservation = (bases.count(most_common) / len(bases)) * 100
                    conservation_scores.append(conservation)
                else:
                    conservation_scores.append(0)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=positions,
                y=conservation_scores,
                mode='lines+markers',
                line=dict(color='#d4af37', width=3),
                name='Conservation %'
            ))
            
            fig.update_layout(
                title="Sequence Conservation Across Positions",
                xaxis_title="Position",
                yaxis_title="Conservation (%)",
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                yaxis=dict(range=[0, 100])
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("💡 **Dr. Titan's Tip:** High conservation (close to 100%) indicates functionally important regions. Low conservation suggests evolutionary variation or non-critical regions!")
            
    except Exception as e:
        st.error(f"❌ MSA Error: {e}")