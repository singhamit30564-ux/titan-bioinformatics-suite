import streamlit as st
import pandas as pd
import plotly.express as px

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧬 TITAN TOOL 5: MUTATION / SNP DETECTION & Ti/Tv RATIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("🧬 Module 5: Mutation & SNP Detection")
st.markdown("Compare two DNA sequences to find Point Mutations (SNPs) and calculate the Transition/Transversion (Ti/Tv) ratio.")
st.markdown("---")

# --- INPUT SECTION ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 Reference Sequence (Original)")
    ref_input = st.text_area("Enter Reference DNA (5' to 3'):", "ATGCGCTAGCTAGCTAGCTAGCTAGCATCG", height=150, key="ref_seq")

with col2:
    st.subheader("🧫 Mutated Sequence (Query)")
    mut_input = st.text_area("Enter Mutated DNA (5' to 3'):", "ATGCGCTAGCTAGCTAGCTAGCTAGCATCA", height=150, key="mut_seq")

st.markdown("<br>", unsafe_allow_html=True)
calculate_btn = st.button("🔍 Detect Mutations & Calculate Ti/Tv", use_container_width=True, type="primary")

# --- HELPER FUNCTION FOR Ti/Tv LOGIC ---
def classify_mutation(ref_base, mut_base):
    purines = {'A', 'G'}
    pyrimidines = {'C', 'T'}
    
    # Transition: Purine <-> Purine OR Pyrimidine <-> Pyrimidine
    if (ref_base in purines and mut_base in purines) or (ref_base in pyrimidines and mut_base in pyrimidines):
        return 'Transition (Ti)'
    # Transversion: Purine <-> Pyrimidine
    else:
        return 'Transversion (Tv)'

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    clean_ref = ref_input.replace(" ", "").replace("\n", "").upper()
    clean_mut = mut_input.replace(" ", "").replace("\n", "").upper()
    
    # Validation
    if not clean_ref or not clean_mut:
        st.error("❌ Please enter both Reference and Mutated sequences.")
    elif len(clean_ref) != len(clean_mut):
        st.error(f"❌ Length Mismatch! Reference length ({len(clean_ref)}) must equal Mutated length ({len(clean_mut)}). Use Alignment tools for different lengths.")
    elif any(char not in "ATCG" for char in clean_ref + clean_mut):
        st.error("❌ Invalid DNA! Only A, T, C, G are allowed.")
    else:
        try:
            mutations = []
            ti_count = 0
            tv_count = 0
            
            # Base-by-base comparison
            for i, (b1, b2) in enumerate(zip(clean_ref, clean_mut)):
                if b1 != b2:
                    mut_type = classify_mutation(b1, b2)
                    if mut_type == 'Transition (Ti)':
                        ti_count += 1
                    else:
                        tv_count += 1
                    
                    mutations.append({
                        'Position (bp)': i + 1,
                        'Reference Base': b1,
                        'Mutated Base': b2,
                        'Mutation Type': mut_type
                    })
            
            total_mutations = len(mutations)
            
            # --- DISPLAY METRICS ---
            st.markdown("### 📊 Mutation Statistics")
            met_col1, met_col2, met_col3, met_col4 = st.columns(4)
            met_col1.metric("📏 Sequence Length", f"{len(clean_ref)} bp")
            met_col2.metric("🧬 Total SNPs", f"{total_mutations}")
            met_col3.metric("🔄 Transitions (Ti)", f"{ti_count}", help="A↔G or C↔T")
            met_col4.metric("🔀 Transversions (Tv)", f"{tv_count}", help="A/G↔C/T")
            
            # Calculate Ti/Tv Ratio safely
            if tv_count == 0:
                ti_tv_ratio = "∞ (Infinite)"
            else:
                ti_tv_ratio = f"{ti_count / tv_count:.2f}"
                
            st.success(f"🎯 **Ti/Tv Ratio:** `{ti_tv_ratio}` *(A ratio > 2.0 usually indicates good quality sequencing data!)*")
            
            st.markdown("---")
            
            # --- MUTATION TABLE ---
            if total_mutations > 0:
                st.markdown("### 📋 Detailed SNP Map")
                df_mutations = pd.DataFrame(mutations)
                
                # Color code the types
                def highlight_type(val):
                    if val == 'Transition (Ti)':
                        return 'background-color: #d4af37; color: #000' # Gold
                    else:
                        return 'background-color: #66fcf1; color: #000' # Cyan
                        
                st.dataframe(
                    df_mutations.style.applymap(highlight_type, subset=['Mutation Type']),
                    use_container_width=True,
                    hide_index=True
                )
                
                st.markdown("---")
                
                # --- Ti vs Tv BAR CHART ---
                st.markdown("### 📊 Ti vs Tv Distribution")
                df_chart = pd.DataFrame({
                    'Mutation Type': ['Transitions (Ti)', 'Transversions (Tv)'],
                    'Count': [ti_count, tv_count]
                })
                
                fig = px.bar(
                    df_chart, 
                    x='Mutation Type', 
                    y='Count',
                    color='Mutation Type',
                    color_discrete_map={
                        'Transitions (Ti)': '#d4af37', # Gold
                        'Transversions (Tv)': '#66fcf1'  # Cyan
                    },
                    text_auto=True
                )
                
                fig.update_layout(
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#1a1f2e',
                    font=dict(color='#e0e0e0'),
                    showlegend=False,
                    margin=dict(t=20, b=40, l=40, r=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("✅ **No Mutations Found!** The two sequences are 100% identical.")
            
            # --- THE "SMART LOCK" ---
            st.markdown("---")
            st.markdown("### 📥 Export Data")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📄 Download PDF Report (Free)", use_container_width=True):
                    st.info("📄 Generating PDF report... (Feature coming in v1.1)")
                    
            with col_btn2:
                if st.button("📊 Download CSV Data (🔒 Explorer Plan)", use_container_width=True):
                    st.warning("🔒 **Titan Explorer Plan Required.**\n\nUpgrade to unlock CSV exports, batch processing, and advanced analytics.")
                    
        except Exception as e:
            st.error(f"⚠️ Calculation Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** In human genomes, the expected **Ti/Tv ratio is around 2.0 to 2.1** for whole genomes, and > 3.0 for exomes. If your ratio is much lower, it might indicate sequencing errors (since random errors cause more transversions)!")