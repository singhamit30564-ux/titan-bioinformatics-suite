import streamlit as st

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📏 TITAN TOOL 10: HAMMING & EDIT (LEVENSHTEIN) DISTANCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("📏 Module 10: Hamming & Edit Distance")
st.markdown("Calculate the exact number of mutations (Hamming) or edit operations (Levenshtein) between two sequences.")
st.markdown("---")

# --- INPUT SECTION ---
c1, c2 = st.columns(2)
with c1:
    seq1 = st.text_area("Sequence 1 (DNA):", "ATGCGCTAG", height=150, key="dist_seq1")
with c2:
    seq2 = st.text_area("Sequence 2 (DNA):", "ATGCACTAGC", height=150, key="dist_seq2")

calculate_btn = st.button("📏 Calculate Distances", use_container_width=True, type="primary")

# --- HELPER FUNCTION FOR LEVENSHTEIN ---
def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    s1 = seq1.replace(" ", "").replace("\n", "").upper()
    s2 = seq2.replace(" ", "").replace("\n", "").upper()
    
    if not s1 or not s2:
        st.error("❌ Please enter both sequences.")
    elif any(char not in "ATCG" for char in s1+s2):
        st.error("❌ Invalid DNA! Only A, T, C, G are allowed.")
    else:
        # 1. Hamming Distance (only if lengths are equal)
        hamming_dist = None
        if len(s1) == len(s2):
            hamming_dist = sum(c1 != c2 for c1, c2 in zip(s1, s2))
        
        # 2. Levenshtein Distance (Dynamic Programming)
        lev_dist = levenshtein(s1, s2)
        
        # --- DISPLAY METRICS ---
        st.markdown("### 📊 Distance Metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sequence 1 Length", f"{len(s1)} bp")
        c2.metric("Sequence 2 Length", f"{len(s2)} bp")
        c3.metric("Edit Distance (Levenshtein)", lev_dist)
        
        st.markdown("---")
        
        if hamming_dist is not None:
            st.success(f"✅ **Hamming Distance:** `{hamming_dist}` *(Sequences are of equal length)*")
        else:
            st.warning(f"⚠️ **Hamming Distance:** `N/A` *(Sequences must be of equal length to calculate Hamming distance. Use Edit Distance instead.)*")
            
        # --- THE "SMART LOCK" ---
        st.markdown("---")
        st.markdown("### 📥 Export Data")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Download PDF (Free)", use_container_width=True):
                st.info("📄 Generating PDF... (Coming in v1.1)")
        with c2:
            if st.button("📊 Download CSV (🔒 Explorer)", use_container_width=True):
                st.warning("🔒 **Titan Explorer Plan Required.**")