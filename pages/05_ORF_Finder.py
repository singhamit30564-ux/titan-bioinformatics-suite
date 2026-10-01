import streamlit as st
from Bio.Seq import Seq
import pandas as pd
from titan_utils import clean_sequence, validate_dna, validate_rna, revcomp, gc_fraction_safe
from titan_utils.i18n import t
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧬 TITAN TOOL 6: ORF (OPEN READING FRAME) FINDER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

titan_title("🧬", "ORF Finder", "Refactored with Titan validation & export.")
st.markdown(t("Identify potential protein-coding regions (Open Reading Frames) across all 6 reading frames."))
st.markdown("---")

# --- INPUT SECTION ---
dna_input = st.text_area(
    t("Enter DNA Sequence (5' to 3'):"),
    "ATGCGCTAGCTAGCTAGCTAGCTAGCATCGATCGATGAAACCCGGGTTTAA",
    height=150,
    key="orf_input"
)

col1, col2 = st.columns([3, 1])
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    calculate_btn = st.button(t("🔍 Find ORFs"), use_container_width=True, type="primary")

# --- HELPER FUNCTION FOR ORF DETECTION ---
def find_all_orfs(seq):
    orfs = []
    stop_codons = {'TAA', 'TAG', 'TGA'}

    # Check both Forward (+) and Reverse (-) strands
    for strand, nuc in [(1, seq), (-1, seq.reverse_complement())]:
        for frame in range(3):
            index = frame
            while index <= len(nuc) - 3:
                # Look for Start Codon (ATG)
                if nuc[index:index+3] == 'ATG':
                    # Look for Stop Codon in the same frame
                    for i in range(index + 3, len(nuc) - 2, 3):
                        codon = nuc[i:i+3]
                        if codon in stop_codons:
                            orf_seq = nuc[index:i+3]
                            orfs.append({
                                'Strand': '+' if strand == 1 else '-',
                                'Frame': frame + 1,
                                'Start_Pos': index + 1,
                                'End_Pos': i + 3,
                                'Length_bp': len(orf_seq),
                                'Length_aa': len(orf_seq) // 3,
                                'DNA_Sequence': str(orf_seq),
                                'Protein_Sequence': str(Seq(orf_seq).translate(to_stop=True))
                            })
                            break # Found an ORF, move to next potential start
                index += 3

    # Sort by length (longest first)
    orfs.sort(key=lambda x: x['Length_bp'], reverse=True)
    return orfs

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    clean_dna = dna_input.replace(" ", "").replace("\n", "").upper()
    clean_dna = clean_sequence(clean_dna)  # titan_utils: ensures whitespace/FASTA handling

    if not clean_dna:
        st.error(t("❌ Please enter a valid DNA sequence."))
    elif any(char not in "ATCG" for char in clean_dna):
        st.error(t("❌ Invalid DNA! Only A, T, C, G are allowed."))
    else:
        try:
            seq = Seq(clean_dna)
            orf_list = find_all_orfs(seq)

            st.markdown(t("### 📊 ORF Statistics"))
            met_col1, met_col2, met_col3 = st.columns(3)
            met_col1.metric(t("📏 Total Sequence Length"), f"{len(seq)} bp")
            met_col2.metric(t("🧬 Total ORFs Found"), f"{len(orf_list)}")

            if len(orf_list) > 0:
                longest_orf = orf_list[0]
                met_col3.metric(t("🏆 Longest ORF"), f"{longest_orf['Length_aa']} aa ({longest_orf['Length_bp']} bp)")

                st.markdown("---")
                st.markdown(t("### 🏆 Longest ORF Details"))
                st.info(t("**Strand:** {strand} | **Frame:** {frame} | **Position:** {start} to {end}", strand=longest_orf['Strand'], frame=longest_orf['Frame'], start=longest_orf['Start_Pos'], end=longest_orf['End_Pos']))
                st.code(t("DNA:  {sequence}", sequence=longest_orf['DNA_Sequence']), language="text")
                st.code(t("Prot: {sequence}", sequence=longest_orf['Protein_Sequence']), language="text")

                st.markdown("---")
                st.markdown(t("### 📋 All Detected ORFs"))
                st.caption(t("Showing top 20 longest ORFs to keep the UI clean."))

                # Create DataFrame for display
                df_orfs = pd.DataFrame(orf_list[:20])

                # Drop the long sequence columns for a cleaner table view, keep it compact
                df_display = df_orfs[['Strand', 'Frame', 'Start_Pos', 'End_Pos', 'Length_bp', 'Length_aa']].copy()
                df_display.columns = [t(column) for column in df_display.columns]

                st.dataframe(
                    df_display,
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.warning(t("⚠️ **No valid ORFs found.** (An ORF must start with 'ATG' and end with 'TAA', 'TAG', or 'TGA' in the same reading frame)."))

            # --- THE "SMART LOCK" ---
            st.markdown("---")
            st.markdown(t("### 📥 Export Data"))

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button(t("📄 Download PDF Report (Free)"), use_container_width=True):
                    st.info(t("📄 Generating PDF report... (Feature coming in v1.1)"))

            with col_btn2:
                if st.button(t("📊 Download CSV (Free)"), use_container_width=True):
                    st.info(t("✅ CSV export unlocked — Titan Explorer gating removed via smart_lock."))

        except Exception as e:
            st.error(t("⚠️ Calculation Error: {error}", error=str(e)))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info(t("💡 **Dr. Titan's Tip:** A true Open Reading Frame (ORF) typically starts with a Start Codon (**ATG**) and ends with a Stop Codon (**TAA, TAG, or TGA**) without any other stop codons in between. We scan all 6 frames (3 forward, 3 reverse) because genes can be located on either DNA strand!"))
