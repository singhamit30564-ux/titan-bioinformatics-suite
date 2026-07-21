import streamlit as st
from Bio import AlignIO
from Bio.Align import MultipleSeqAlignment
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import pandas as pd

st.title(" Module 4.06: MSA ClustalW Style Output")
st.markdown("Format Multiple Sequence Alignment in the classic ClustalW style with conservation stars.")
st.markdown("---")

fasta_input = st.text_area("Enter Sequences in FASTA format", 
    """>Seq1
ATGCGTACGTAGCTAG
>Seq2
ATGCGTACGAAGCTAG
>Seq3
ATGCGTGCCTAGCTAG""", height=200)

if st.button("📋 Generate ClustalW Format", type="primary", use_container_width=True):
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
            # Pad to max length for simple visual
            max_len = max(len(rec.seq) for rec in records)
            aligned_seqs = [str(rec.seq).ljust(max_len, '-') for rec in records]
            
            st.markdown("###  Clustal W Output")
            st.code("CLUSTAL W (1.82) multiple sequence alignment\n", language="text")
            
            # Print in chunks of 60
            chunk_size = 60
            for i in range(0, max_len, chunk_size):
                chunk_end = min(i + chunk_size, max_len)
                for rec, seq in zip(records, aligned_seqs):
                    st.text(f"{rec.id:<15} {seq[i:chunk_end]}")
                
                # Conservation line
                conservation = ""
                for pos in range(i, chunk_end):
                    bases = [seq[pos] for seq in aligned_seqs]
                    if len(set(bases)) == 1 and bases[0] != '-':
                        conservation += "*"
                    elif len(set(bases)) <= 2 and '-' not in bases:
                        conservation += ":"
                    else:
                        conservation += " "
                st.text(f"{'':<15} {conservation}\n")
                
            st.info("💡 **Dr. Titan's Tip:** In Clustal format, `*` means fully conserved, `:` means strong similarity, and `.` means weak similarity. This is the standard format for publishing alignments!")
            
    except Exception as e:
        st.error(f"❌ Error: {e}")