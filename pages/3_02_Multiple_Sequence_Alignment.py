import streamlit as st

st.title("🧬 Module 14: Multiple Sequence Alignment (Basic)")
st.markdown("Compare 2 or 3 DNA/Protein sequences side-by-side to identify mutations and conserved regions.")
st.markdown("---")

c1, c2, c3 = st.columns(3)
with c1:
    seq1 = st.text_area("Sequence 1", "ATGCGCTAGCTAG", height=150)
with c2:
    seq2 = st.text_area("Sequence 2", "ATGCACTAGCTAG", height=150)
with c3:
    seq3 = st.text_area("Sequence 3 (Optional)", "ATGCGCTAGCTAA", height=150)

if st.button("🔍 Align & Compare", use_container_width=True, type="primary"):
    s1, s2, s3 = seq1.replace(" ", "").upper(), seq2.replace(" ", "").upper(), seq3.replace(" ", "").upper()
    
    # Simple visual alignment logic (padding to max length)
    max_len = max(len(s1), len(s2), len(s3) if s3 else 0)
    s1, s2, s3 = s1.ljust(max_len, '-'), s2.ljust(max_len, '-'), s3.ljust(max_len, '-')
    
    st.markdown("### 📊 Visual Alignment")
    
    # Generate match/mismatch indicators
    matches_1_2 = "".join(["🟢" if a == b else "🔴" for a, b in zip(s1, s2)])
    
    st.markdown(f"**Seq 1:** `{s1}`")
    st.markdown(f"**Seq 2:** `{s2}`")
    st.markdown(f"**Match:**  {matches_1_2}")
    
    if s3:
        matches_1_3 = "".join(["🟢" if a == b else "🔴" for a, b in zip(s1, s3)])
        st.markdown(f"**Seq 3:** `{s3}`")
        st.markdown(f"**Match:**  {matches_1_3}")

    st.info("💡 **Dr. Titan's Tip:** 🟢 = Match (Conserved), 🔴 = Mismatch (Mutation/Indel). Real MSA uses algorithms like ClustalW, but this visualizer is perfect for quick, short sequence checks!")