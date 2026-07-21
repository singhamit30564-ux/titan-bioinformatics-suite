import streamlit as st

st.title(" Module 5.03: PCR Product & Amplicon Length Calculator")
st.markdown("Calculate the exact size of your PCR product based on Forward and Reverse primer positions.")
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    f_pos = st.number_input("Forward Primer Start Position (1-based)", min_value=1, value=10)
    f_len = st.number_input("Forward Primer Length (bp)", min_value=15, max_value=30, value=20)
with c2:
    r_pos = st.number_input("Reverse Primer Start Position (1-based)", min_value=1, value=500)
    r_len = st.number_input("Reverse Primer Length (bp)", min_value=15, max_value=30, value=20)

if st.button("🧮 Calculate Amplicon Size", type="primary", use_container_width=True):
    if r_pos < f_pos:
        st.error("❌ Reverse primer position must be greater than Forward primer position!")
    else:
        # Amplicon size = (Reverse End) - (Forward Start) + 1
        # Reverse End = r_pos + r_len - 1 (if r_pos is the 5' end of the reverse complement)
        # Simplified: Distance between 5' ends + length of one primer
        amplicon_size = (r_pos - f_pos) + r_len 
        
        st.markdown("### 📊 PCR Product Details")
        col1, col2, col3 = st.columns(3)
        col1.metric("Forward Primer End", f"{f_pos + f_len - 1} bp")
        col2.metric("Reverse Primer End", f"{r_pos + r_len - 1} bp")
        col3.metric("Total Amplicon Size", f"{amplicon_size} bp", delta="Expected Band Size")
        
        st.info(f"💡 **Dr. Titan's Tip:** When you run this on an Agarose Gel, you will see a bright band at exactly **{amplicon_size} base pairs**. Always add a 100bp DNA Ladder to verify!")