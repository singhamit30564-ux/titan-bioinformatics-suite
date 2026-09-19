import streamlit as st
from Bio import SeqIO
import pandas as pd
import plotly.express as px
import io

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📂 TITAN TOOL 13: FASTA/FASTQ PARSER & QC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("📂 Module 13: FASTA/FASTQ Parser & QC")
st.markdown("Upload your raw sequencing files to instantly parse, validate, and get basic Quality Control (QC) metrics.")
st.markdown("---")

# --- INPUT SECTION ---
uploaded_file = st.file_uploader(
    "Upload FASTA or FASTQ file (.fasta, .fa, .fastq, .fq)", 
    type=["fasta", "fa", "fastq", "fq", "txt"]
)

if uploaded_file is not None:
    # Determine file type based on extension or content
    file_name = uploaded_file.name.lower()
    
    if file_name.endswith(('.fastq', '.fq')):
        file_format = "fastq"
    else:
        file_format = "fasta"
        
    st.markdown(f"### 📊 Analyzing: `{uploaded_file.name}` ({file_format.upper()})")
    
    with st.spinner("🧬 Parsing sequences... This may take a moment for large files."):
        try:
            # Read file content
            file_content = uploaded_file.getvalue().decode("utf-8")
            
            # Parse using Biopython
            records = list(SeqIO.parse(io.StringIO(file_content), file_format))
            
            if not records:
                st.error("❌ No valid sequences found. Please check the file format.")
            else:
                # --- CALCULATE METRICS ---
                total_seqs = len(records)
                lengths = [len(rec) for rec in records]
                total_length = sum(lengths)
                min_len = min(lengths)
                max_len = max(lengths)
                avg_len = total_length / total_seqs
                
                # Calculate overall GC content
                total_gc = sum(str(rec.seq).upper().count('G') + str(rec.seq).upper().count('C') for rec in records)
                overall_gc = (total_gc / total_length) * 100 if total_length > 0 else 0
                
                # --- DISPLAY METRICS ---
                st.markdown("### 📈 QC Statistics")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("🧬 Total Sequences", f"{total_seqs:,}")
                c2.metric("📏 Total Length", f"{total_length:,} bp")
                c3.metric("📊 Avg Length", f"{avg_len:.1f} bp")
                c4.metric("🌡️ Overall GC%", f"{overall_gc:.2f}%")
                
                st.markdown("---")
                
                # --- LENGTH DISTRIBUTION CHART ---
                st.markdown("### 📊 Sequence Length Distribution")
                
                # Create a dataframe for plotting (limit to first 1000 for performance if file is huge)
                plot_lengths = lengths[:1000] 
                df_plot = pd.DataFrame({'Length': plot_lengths})
                
                fig = px.histogram(
                    df_plot, 
                    x='Length', 
                    nbins=50,
                    color_discrete_sequence=['#d4af37'], # Titan Gold
                    opacity=0.8
                )
                
                fig.update_layout(
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#1a1f2e',
                    font=dict(color='#e0e0e0'),
                    xaxis_title="Sequence Length (bp)",
                    yaxis_title="Frequency",
                    margin=dict(t=20, b=40, l=40, r=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")
                
                # --- PREVIEW TABLE ---
                st.markdown("### 🔍 Sequence Preview (First 5)")
                
                preview_data = []
                for i, rec in enumerate(records[:5]):
                    seq_str = str(rec.seq)
                    gc_pct = ((seq_str.upper().count('G') + seq_str.upper().count('C')) / len(seq_str) * 100) if len(seq_str) > 0 else 0
                    preview_data.append({
                        "ID": rec.id,
                        "Length": len(seq_str),
                        "GC%": f"{gc_pct:.2f}%",
                        "Sequence (First 50 bp)": seq_str[:50] + "..." if len(seq_str) > 50 else seq_str
                    })
                    
                df_preview = pd.DataFrame(preview_data)
                st.dataframe(df_preview, use_container_width=True, hide_index=True)
                
                # --- THE "SMART LOCK" ---
                st.markdown("---")
                st.markdown("### 📥 Export Data")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📄 Download QC Summary PDF (Free)", use_container_width=True):
                        st.info("📄 Generating PDF report... (Feature coming in v1.1)")
                with c2:
                    if st.button("📊 Download Full CSV Data (🔒 Explorer Plan)", use_container_width=True):
                        st.warning("🔒 **Titan Explorer Plan Required.**\n\nUpgrade to unlock full sequence data exports and advanced analytics.")
                        
        except Exception as e:
            st.error(f"⚠️ Parsing Error: {e}. Please ensure the file is a valid {file_format.upper()} format.")

else:
    st.info("👆 Please upload a FASTA or FASTQ file to begin analysis.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** **FASTA** files contain just the sequence and a header (`>`). **FASTQ** files contain the sequence PLUS a quality score for every single base (used in Next-Gen Sequencing). Always check your 'Avg Length' and 'GC%' to ensure your sequencing run was successful!")