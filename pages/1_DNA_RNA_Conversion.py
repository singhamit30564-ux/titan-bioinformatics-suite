import streamlit as st
from Bio.Seq import Seq
import pandas as pd

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧬 TITAN TOOL 1: DNA ↔ RNA CONVERSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("🧬 Module 1: DNA ↔ RNA Conversion")
st.markdown("Transcribe DNA to RNA or back-transcribe RNA to DNA instantly using Biopython.")
st.markdown("---")

col1, col2 = st.columns(2)

# --- DNA TO RNA SECTION ---
with col1:
    st.subheader("🧬 DNA ➡️ RNA (Transcription)")
    dna_input = st.text_area("Enter DNA Sequence (5' to 3'):", "ATGCATGCATGC", height=150, key="dna_input")
    
    if st.button("Transcribe to RNA", use_container_width=True):
        # Clean the input (remove spaces and newlines)
        clean_dna = dna_input.replace(" ", "").replace("\n", "").upper()
        
        if not clean_dna:
            st.error("❌ Please enter a valid DNA sequence.")
        elif any(char not in "ATCG" for char in clean_dna):
            st.error("❌ Invalid DNA! Only A, T, C, G are allowed.")
        else:
            try:
                seq = Seq(clean_dna)
                rna_output = str(seq.transcribe())
                st.success(f"✅ **RNA Sequence:**\n\n`{rna_output}`")
                
                # 📊 THE "SMART LOCK" (CSV GATING)
                st.markdown("---")
                st.markdown("### 📥 Export Results")
                
                # Free PDF Button
                if st.button("📄 Download PDF (Free)", use_container_width=True):
                    st.info("📄 Generating PDF report... (Feature coming in v1.1)")
                    
                # Locked CSV Button
                if st.button(" Download CSV (🔒 Explorer Plan)", use_container_width=True):
                    st.warning("🔒 **Titan Explorer Plan Required.**\n\nUpgrade to unlock CSV exports, advanced data manipulation, and batch processing.")
                    
            except Exception as e:
                st.error(f"⚠️ Conversion Error: {e}")

# --- RNA TO DNA SECTION ---
with col2:
    st.subheader("🧫 RNA ➡️ DNA (Back-Transcription)")
    rna_input = st.text_area("Enter RNA Sequence (5' to 3'):", "AUGCAUGCAUGC", height=150, key="rna_input")
    
    if st.button("Back-Transcribe to DNA", use_container_width=True):
        clean_rna = rna_input.replace(" ", "").replace("\n", "").upper()
        
        if not clean_rna:
            st.error("❌ Please enter a valid RNA sequence.")
        elif any(char not in "AUCG" for char in clean_rna):
            st.error("❌ Invalid RNA! Only A, U, C, G are allowed.")
        else:
            try:
                seq = Seq(clean_rna)
                dna_output = str(seq.back_transcribe())
                st.success(f"✅ **DNA Sequence:**\n\n`{dna_output}`")
                
            except Exception as e:
                st.error(f"⚠️ Conversion Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip (Future Integration Placeholder)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** Remember, in RNA, Thymine (T) is replaced by Uracil (U). This is crucial for protein translation!")