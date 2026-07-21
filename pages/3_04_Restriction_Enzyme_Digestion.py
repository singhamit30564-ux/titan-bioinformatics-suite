import streamlit as st

st.title("✂️ Module 16: Restriction Enzyme Digestion")
st.markdown("Simulate how specific restriction enzymes will cut your DNA sequence.")
st.markdown("---")

dna_seq = st.text_area("Enter DNA Sequence", "GAATTCGCGGCCGCTCTAGAACTAGT", height=150)

enzymes = {
    "EcoRI": "GAATTC",
    "BamHI": "GGATCC",
    "HindIII": "AAGCTT",
    "NotI": "GCGGCCGC",
    "XbaI": "TCTAGA"
}

selected_enzymes = st.multiselect("Select Enzymes to Test", list(enzymes.keys()), default=["EcoRI", "NotI"])

if st.button("✂️ Simulate Digestion", use_container_width=True, type="primary"):
    seq = dna_seq.replace(" ", "").upper()
    st.markdown("### 🧬 Digestion Results")
    
    found_any = False
    for enz_name, enz_seq in enzymes.items():
        if enz_name in selected_enzymes:
            count = seq.count(enz_seq)
            if count > 0:
                found_any = True
                # Find positions
                positions = [i for i in range(len(seq)) if seq.startswith(enz_seq, i)]
                st.success(f"✅ **{enz_name}** (`{enz_seq}`): Found **{count}** cut site(s) at positions: {positions}")
            else:
                st.warning(f"❌ **{enz_name}** (`{enz_seq}`): No cut sites found.")
                
    if not found_any:
        st.info("ℹ️ No selected enzymes matched the sequence. Try a different sequence or enzyme.")

    st.info("💡 **Dr. Titan's Tip:** Restriction enzymes are molecular scissors. EcoRI cuts at GAATTC, creating 'sticky ends' perfect for cloning!")