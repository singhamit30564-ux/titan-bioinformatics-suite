import streamlit as st
from Bio.Seq import Seq

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔄 TITAN TOOL 12: CENTRAL DOGMA VISUALIZER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("🔄 Module 12: Central Dogma Visualizer")
st.markdown("Visualize the flow of genetic information: DNA → (Transcription) → RNA → (Translation) → Protein.")
st.markdown("---")

# --- INPUT SECTION ---
dna_input = st.text_area(
    "Enter DNA Sequence (Coding Strand 5' to 3'):", 
    "ATGGCGTACGTAATCGATCGATCGATCTAA", 
    height=150, 
    key="dogma_input"
)

calculate_btn = st.button("🧬 Process Central Dogma", use_container_width=True, type="primary")

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    clean_dna = dna_input.replace(" ", "").replace("\n", "").upper()
    
    if not clean_dna:
        st.error("❌ Please enter a valid DNA sequence.")
    elif any(char not in "ATCG" for char in clean_dna):
        st.error("❌ Invalid DNA! Only A, T, C, G are allowed.")
    else:
        try:
            dna_seq = Seq(clean_dna)
            
            # Step 1: Transcription (DNA -> RNA)
            rna_seq = dna_seq.transcribe()
            
            # Step 2: Translation (RNA -> Protein)
            protein_seq = rna_seq.translate()
            
            # --- VISUAL PIPELINE UI ---
            st.markdown("### 🏭 The Biological Pipeline")
            
            # Row 1: DNA
            st.markdown("#### 🧬 1. DNA (Template / Coding Strand)")
            st.code(clean_dna, language="text")
            
            st.markdown("<div style='text-align:center; font-size:24px; margin:10px 0;'>⬇️ <b>Transcription (RNA Polymerase)</b> ⬇️</div>", unsafe_allow_html=True)
            
            # Row 2: RNA
            st.markdown("#### 🧫 2. mRNA (Messenger RNA)")
            st.code(str(rna_seq), language="text")
            
            st.markdown("<div style='text-align:center; font-size:24px; margin:10px 0;'>⬇️ <b>Translation (Ribosome)</b> ⬇️</div>", unsafe_allow_html=True)
            
            # Row 3: Protein
            st.markdown("#### 🥩 3. Polypeptide (Protein Chain)")
            st.code(str(protein_seq), language="text")
            
            st.markdown("---")
            
            # --- SUMMARY METRICS ---
            st.markdown("### 📊 Translation Statistics")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("DNA Length", f"{len(dna_seq)} bp")
            c2.metric("mRNA Length", f"{len(rna_seq)} bases")
            c3.metric("Protein Length", f"{len(protein_seq)} amino acids")
            
            # Check for Stop Codon
            stop_count = str(protein_seq).count('*')
            c4.metric("Stop Codons (*)", f"{stop_count}", help="Indicates end of translation")
            
            if stop_count > 0 and str(protein_seq)[-1] == '*':
                st.success("✅ **Valid Open Reading Frame detected!** The sequence ends with a proper Stop Codon.")
            elif stop_count > 0:
                st.warning("⚠️ **Internal Stop Codons detected.** This might result in a truncated (short) protein.")
            else:
                st.info("ℹ️ **No Stop Codon found.** The ribosome would continue translating until the end of the mRNA.")
            
            # --- THE "SMART LOCK" ---
            st.markdown("---")
            st.markdown("### 📥 Export Data")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📄 Download PDF Report (Free)", use_container_width=True):
                    st.info("📄 Generating PDF report... (Feature coming in v1.1)")
            with c2:
                if st.button("📊 Download CSV Data (🔒 Explorer Plan)", use_container_width=True):
                    st.warning("🔒 **Titan Explorer Plan Required.**\n\nUpgrade to unlock CSV exports and advanced analytics.")
                    
        except Exception as e:
            st.error(f"⚠️ Processing Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** The **Central Dogma of Molecular Biology** (proposed by Francis Crick) states that genetic information flows only in one direction: from DNA, to RNA, to protein. Reverse transcription (RNA to DNA) happens in retroviruses like HIV, but it's an exception!")