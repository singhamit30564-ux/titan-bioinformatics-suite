"""DNA ↔ RNA Conversion — refactored to use titan_utils."""

import streamlit as st
from Bio.Seq import Seq

from titan_utils import clean_sequence, validate_dna, validate_rna
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title
import pandas as pd

titan_title(
    "🧬",
    "DNA ↔ RNA Conversion",
    "Transcribe DNA to RNA or back-transcribe RNA to DNA instantly using Biopython + Titan validation.",
)

col1, col2 = st.columns(2)

# --- DNA TO RNA SECTION ---
with col1:
    st.subheader("🧬 DNA ➡️ RNA (Transcription)")
    dna_input = st.text_area("Enter DNA Sequence (5' to 3'):", "ATGCATGCATGC", height=150, key="dna_input")

    if st.button("Transcribe to RNA", use_container_width=True, type="primary"):
        seq, err = validate_dna(dna_input)
        if err:
            st.error(err)
        else:
            try:
                rna_output = str(Seq(seq).transcribe())
                st.success(f"✅ **RNA Sequence:**\n\n`{rna_output}`")
                # Export via shared smart_lock (real CSV download, no fake paywall)
                df = pd.DataFrame([{"input_DNA": seq, "output_RNA": rna_output}])
                smart_lock(csv_data=df_to_csv_bytes(df), csv_filename="dna_to_rna.csv")
            except Exception as e:
                st.error(f"⚠️ Conversion Error: {e}")

# --- RNA TO DNA SECTION ---
with col2:
    st.subheader("🧫 RNA ➡️ DNA (Back-Transcription)")
    rna_input = st.text_area("Enter RNA Sequence (5' to 3'):", "AUGCAUGCAUGC", height=150, key="rna_input")

    if st.button("Back-Transcribe to DNA", use_container_width=True):
        seq, err = validate_rna(rna_input)
        if err:
            st.error(err)
        else:
            try:
                dna_output = str(Seq(seq).back_transcribe())
                st.success(f"✅ **DNA Sequence:**\n\n`{dna_output}`")
                df2 = pd.DataFrame([{"input_RNA": seq, "output_DNA": dna_output}])
                smart_lock(csv_data=df_to_csv_bytes(df2), csv_filename="rna_to_dna.csv")
            except Exception as e:
                st.error(f"⚠️ Conversion Error: {e}")

dr_titan_tip("In RNA, Thymine (T) is replaced by Uracil (U). Transcription is the first step of the Central Dogma — DNA → RNA — carried out by RNA polymerase in the cell.")
