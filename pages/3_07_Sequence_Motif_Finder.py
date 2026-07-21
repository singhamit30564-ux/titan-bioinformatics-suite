import streamlit as st
import re

st.title("🔍 Module 19: Sequence Pattern/Motif Finder")
st.markdown("Find specific patterns or motifs in your DNA/Protein sequence using regex.")
st.markdown("---")

seq_type = st.radio("Sequence Type", ["DNA", "Protein"], horizontal=True)

if seq_type == "DNA":
    seq_input = st.text_area("Enter DNA Sequence", 
        "ATGCGCTAGCTAGCTAGCTAGCTAGCATCGATCGATCG", height=150)
    valid_chars = "ATCG"
else:
    seq_input = st.text_area("Enter Protein Sequence", 
        "MRSLLILVLCFLPAALGKVRQKISSFKGK", height=150)
    valid_chars = "ACDEFGHIKLMNPQRSTVWY"

pattern = st.text_input("Enter Pattern (Regex)", "ATG[CG]T")

common_patterns = {
    "Start Codon (ATG)": "ATG",
    "Stop Codons (TAA/TAG/TGA)": "TAA|TAG|TGA",
    "TATA Box (TATAAA)": "TATAAA",
    "Kozak Sequence (GCCACC)": "GCCACC",
    "N-glycosylation (N{P}[ST]{P})": "N[^P][ST][^P]",
    "Zinc Finger (C2H2)": "C.{2,4}C.{12}H.{3,5}H"
}

selected_preset = st.selectbox("Or Select Common Pattern", ["Custom"] + list(common_patterns.keys()))

if selected_preset != "Custom":
    pattern = common_patterns[selected_preset]
    st.info(f"📌 Using preset: `{pattern}`")

if st.button("🔍 Find Pattern", use_container_width=True, type="primary"):
    seq = seq_input.replace(" ", "").upper()
    
    if any(c not in valid_chars for c in seq):
        st.error(f"❌ Invalid {seq_type} sequence!")
    else:
        try:
            matches = [(m.start(), m.end(), m.group()) for m in re.finditer(pattern, seq)]
            
            if matches:
                st.success(f"✅ Found **{len(matches)}** match(es)!")
                
                for i, (start, end, match) in enumerate(matches, 1):
                    st.info(f"**Match #{i}:** Position {start}-{end} | `{match}`")
                
                # Highlight in sequence
                highlighted = seq
                for start, end, match in reversed(matches):
                    highlighted = highlighted[:start] + f"**[{match}]**" + highlighted[end:]
                
                st.markdown("### 📍 Highlighted Sequence")
                st.markdown(highlighted)
            else:
                st.warning("❌ No matches found.")
                
        except re.error as e:
            st.error(f"❌ Invalid regex pattern: {e}")

    st.info("💡 **Dr. Titan's Tip:** Use regex patterns like `[AT]` for A or T, `.{3}` for any 3 characters, `*` for 0+ repeats. Common motifs help identify regulatory elements or protein domains!")