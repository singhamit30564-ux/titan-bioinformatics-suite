import streamlit as st
from Bio import AlignIO
from Bio.Align import MultipleSeqAlignment
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from collections import Counter
import plotly.graph_objects as go

st.title(" Module 4.12: Consensus Sequence Generator")
st.markdown("Generate consensus sequence from multiple aligned sequences using majority rule.")
st.markdown("---")

fasta_input = st.text_area("Enter Aligned Sequences in FASTA format", 
    """>Seq1
ATGCGTACGTAGCTAG
>Seq2
ATGCGTACGAAGCTAG
>Seq3
ATGCGTGCCTAGCTAG
>Seq4
ATGCA_TACGTAGCTAG
>Seq5
ATGCGTACGTAGCTAG""", height=250)

threshold = st.slider("Consensus Threshold (%)", 50, 100, 50, 
    help="Minimum percentage for a base to be included in consensus")

if st.button("🔬 Generate Consensus", type="primary", use_container_width=True):
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
        
        if len(records) < 2:
            st.error("❌ Need at least 2 sequences!")
        else:
            # Align to max length
            max_len = max(len(rec.seq) for rec in records)
            aligned_seqs = [str(rec.seq).ljust(max_len, '-') for rec in records]
            
            # Generate consensus
            consensus_seq = []
            consensus_confidence = []
            position_data = []
            
            for pos in range(max_len):
                bases = [seq[pos] for seq in aligned_seqs if pos < len(seq)]
                counts = Counter(bases)
                total = len(bases)
                
                # Find most common base
                most_common_base, most_common_count = counts.most_common(1)[0]
                percentage = (most_common_count / total) * 100
                
                if percentage >= threshold and most_common_base != '-':
                    consensus_seq.append(most_common_base)
                    consensus_confidence.append(percentage)
                else:
                    consensus_seq.append('N')  # Ambiguous
                    consensus_confidence.append(0)
                
                position_data.append({
                    'Position': pos + 1,
                    'Base': most_common_base,
                    'Count': most_common_count,
                    'Percentage': f"{percentage:.1f}%"
                })
            
            final_consensus = ''.join(consensus_seq)
            
            st.markdown("### 🧬 Consensus Sequence")
            st.success(f"**Length:** {len(final_consensus)} bp")
            st.code(final_consensus, language="text")
            
            # Download button
            st.download_button(
                label="⬇️ Download Consensus (FASTA)",
                data=f">Consensus_Sequence\n{final_consensus}",
                file_name="consensus_sequence.fasta",
                mime="text/plain"
            )
            
            # Confidence visualization
            st.markdown("### 📊 Position-wise Confidence")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(1, len(consensus_confidence) + 1)),
                y=consensus_confidence,
                mode='lines+markers',
                line=dict(color='#d4af37', width=2),
                marker=dict(size=4, color='#66fcf1'),
                name='Confidence %'
            ))
            
            fig.add_hline(y=threshold, line_dash="dash", line_color="#ff0055", 
                         annotation_text=f"Threshold ({threshold}%)")
            
            fig.update_layout(
                title="Consensus Sequence Confidence by Position",
                xaxis_title="Position",
                yaxis_title="Confidence (%)",
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                yaxis=dict(range=[0, 100])
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Position table
            st.markdown("### 📋 Detailed Position Analysis")
            import pandas as pd
            df = pd.DataFrame(position_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Statistics
            valid_bases = sum(1 for base in consensus_seq if base != 'N')
            st.markdown("### 📈 Summary Statistics")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Length", f"{len(final_consensus)} bp")
            c2.metric("Valid Bases", f"{valid_bases} ({(valid_bases/len(final_consensus))*100:.1f}%)")
            c3.metric("Ambiguous (N)", f"{len(final_consensus) - valid_bases}")
            
            st.info("💡 **Dr. Titan's Tip:** Consensus sequences are used to represent a group of related sequences (like viral strains or gene families). 'N' indicates positions where no base meets the threshold, showing high variability!")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.code(traceback.format_exc())