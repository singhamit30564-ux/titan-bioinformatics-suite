import streamlit as st
import pandas as pd
import plotly.express as px

st.title("🧬 Module 5.06: SNP Detection & Ti/Tv Ratio Analyzer")
st.markdown("Compare a reference sequence with a query sequence to detect Single Nucleotide Polymorphisms (SNPs) and calculate the Transition/Transversion ratio.")
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    ref_seq = st.text_area("Reference Sequence", "ATGCGTACGTAGCTAGCTAGCATCGATCGATCG", height=150)
with c2:
    query_seq = st.text_area("Query Sequence (Mutated)", "ATGCGTACGTAGCTAGCTAGCATCGATCGATCA", height=150)

if st.button("🔍 Detect SNPs", type="primary", use_container_width=True):
    ref = ref_seq.replace(" ", "").upper()
    query = query_seq.replace(" ", "").upper()
    
    # Align lengths for simple comparison
    min_len = min(len(ref), len(query))
    ref = ref[:min_len]
    query = query[:min_len]
    
    snps = []
    transitions = 0
    transversions = 0
    
    # Transition pairs: A<->G, C<->T
    # Transversion pairs: Purine<->Pyrimidine (A/G <-> C/T)
    
    for i in range(min_len):
        if ref[i] != query[i] and ref[i] in "ATCG" and query[i] in "ATCG":
            pair = tuple(sorted([ref[i], query[i]]))
            snp_type = ""
            
            if pair in [('A', 'G'), ('C', 'T')]:
                snp_type = "Transition (Ti)"
                transitions += 1
            else:
                snp_type = "Transversion (Tv)"
                transversions += 1
                
            snps.append({
                "Position": i + 1,
                "Ref Base": ref[i],
                "Query Base": query[i],
                "Type": snp_type
            })
            
    if not snps:
        st.success("✅ No SNPs detected! Sequences are identical in the aligned region.")
    else:
        df = pd.DataFrame(snps)
        st.markdown(f"### 📊 Detected {len(df)} SNPs")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Ti/Tv Calculation
        titv_ratio = transitions / transversions if transversions > 0 else float('inf')
        
        st.markdown("### 📈 Mutation Spectrum")
        c1, c2, c3 = st.columns(3)
        c1.metric("Transitions (Ti)", transitions)
        c2.metric("Transversions (Tv)", transversions)
        
        ratio_display = f"{titv_ratio:.2f}" if titv_ratio != float('inf') else "Infinity"
        c3.metric("Ti/Tv Ratio", ratio_display)
        
        # Pie Chart
        fig = px.pie(
            names=["Transitions (Ti)", "Transversions (Tv)"],
            values=[transitions, transversions],
            color_discrete_sequence=["#d4af37", "#ff0055"],
            hole=0.4
        )
        fig.update_layout(paper_bgcolor='#0a0e17', font=dict(color='#e0e0e0'))
        st.plotly_chart(fig, use_container_width=True)
        
        # Interpretation
        st.info(f"💡 **Dr. Titan's Tip:** A Ti/Tv ratio of ~2.0-2.1 is expected in human whole-genome data. A lower ratio (< 1.0) often indicates sequencing errors or random noise, while a higher ratio suggests true biological variation!")