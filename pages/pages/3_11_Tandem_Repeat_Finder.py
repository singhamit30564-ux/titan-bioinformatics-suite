import streamlit as st

st.title("🔁 Module 23: Tandem Repeat Finder (STRs)")
st.markdown("Find Short Tandem Repeats (Microsatellites) in your DNA sequence.")
st.markdown("---")

dna_seq = st.text_area("Enter DNA Sequence", 
    "ATGATGATGATGCGCGCGCGCGCGATCGATCGATCG", height=150)

c1, c2 = st.columns(2)
with c1:
    min_unit = st.slider("Min Repeat Unit Length", 2, 6, 2)
with c2:
    min_repeats = st.slider("Min Number of Repeats", 3, 10, 3)

if st.button("🔍 Find Repeats", use_container_width=True, type="primary"):
    seq = dna_seq.replace(" ", "").upper()
    found = []
    
    # Simple sliding window approach
    for unit_len in range(min_unit, 7):
        for i in range(len(seq) - (unit_len * min_repeats) + 1):
            unit = seq[i:i+unit_len]
            # Check if this unit repeats
            count = 1
            j = i + unit_len
            while j + unit_len <= len(seq) and seq[j:j+unit_len] == unit:
                count += 1
                j += unit_len
            
            if count >= min_repeats:
                # Avoid duplicates/overlaps roughly
                if not any(f['start'] <= i < f['end'] for f in found):
                    found.append({
                        'start': i,
                        'end': j,
                        'unit': unit,
                        'count': count,
                        'length': (j - i)
                    })
    
    if found:
        st.success(f"✅ Found **{len(found)}** Tandem Repeat Regions!")
        for f in found:
            st.info(f"**Unit:** `{f['unit']}` | **Repeats:** {f['count']}x | **Pos:** {f['start']}-{f['end']} | **Total Len:** {f['length']}bp")
            st.code(seq[f['start']:f['end']])
    else:
        st.warning("❌ No significant tandem repeats found with current settings.")

    st.info("💡 **Dr. Titan's Tip:** Tandem repeats (STRs) are used in DNA profiling and forensics! The number of repeats varies between individuals, making them unique 'genetic fingerprints'.")