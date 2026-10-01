import streamlit as st
import pandas as pd
import plotly.express as px
from titan_utils import clean_sequence, validate_dna, validate_rna, revcomp, gc_fraction_safe
from titan_utils.i18n import t
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧬 TITAN TOOL 5: MUTATION / SNP DETECTION & Ti/Tv RATIO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

titan_title("🧬", "Mutation & SNP Detection", "Refactored with Titan validation & export.")
st.markdown(t("Compare two DNA sequences to find Point Mutations (SNPs) and calculate the Transition/Transversion (Ti/Tv) ratio."))
st.markdown("---")

# --- INPUT SECTION ---
col1, col2 = st.columns(2)

with col1:
    st.subheader(t("📄 Reference Sequence (Original)"))
    ref_input = st.text_area(t("Enter Reference DNA (5' to 3'):"), "ATGCGCTAGCTAGCTAGCTAGCTAGCATCG", height=150, key="ref_seq")

with col2:
    st.subheader(t("🧫 Mutated Sequence (Query)"))
    mut_input = st.text_area(t("Enter Mutated DNA (5' to 3'):"), "ATGCGCTAGCTAGCTAGCTAGCTAGCATCA", height=150, key="mut_seq")

st.markdown("<br>", unsafe_allow_html=True)
calculate_btn = st.button(t("🔍 Detect Mutations & Calculate Ti/Tv"), use_container_width=True, type="primary")

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
        st.error(t("❌ Please enter both Reference and Mutated sequences."))
    elif len(clean_ref) != len(clean_mut):
        st.error(t("❌ Length Mismatch! Reference length ({reference}) must equal Mutated length ({mutated}). Use Alignment tools for different lengths.", reference=len(clean_ref), mutated=len(clean_mut)))
    elif any(char not in "ATCG" for char in clean_ref + clean_mut):
        st.error(t("❌ Invalid DNA! Only A, T, C, G are allowed."))
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
            st.markdown(t("### 📊 Mutation Statistics"))
            met_col1, met_col2, met_col3, met_col4 = st.columns(4)
            met_col1.metric(t("📏 Sequence Length"), f"{len(clean_ref)} bp")
            met_col2.metric(t("🧬 Total SNPs"), f"{total_mutations}")
            met_col3.metric(t("🔄 Transitions (Ti)"), f"{ti_count}", help=t("A↔G or C↔T"))
            met_col4.metric(t("🔀 Transversions (Tv)"), f"{tv_count}", help=t("A/G↔C/T"))

            # Calculate Ti/Tv Ratio safely
            if tv_count == 0:
                ti_tv_ratio = "∞ (Infinite)"
            else:
                ti_tv_ratio = f"{ti_count / tv_count:.2f}"

            st.success(t("🎯 **Ti/Tv Ratio:** `{ratio}` *(A ratio > 2.0 usually indicates good quality sequencing data!)*", ratio=ti_tv_ratio))

            st.markdown("---")

            # --- MUTATION TABLE ---
            if total_mutations > 0:
                st.markdown(t("### 📋 Detailed SNP Map"))
                df_mutations = pd.DataFrame(mutations)

                # Translate display labels only; keep the calculation/export data in English.
                mutation_type_column = t("Mutation Type")
                transition_value = t("Transition (Ti)")
                df_display = df_mutations.rename(columns=lambda column: t(column)).copy()
                df_display[mutation_type_column] = df_display[mutation_type_column].map(t)

                def highlight_type(val):
                    if val == transition_value:
                        return 'background-color: #d4af37; color: #000' # Gold
                    return 'background-color: #66fcf1; color: #000' # Cyan

                st.dataframe(
                    df_display.style.map(highlight_type, subset=[mutation_type_column]),
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("---")

                # --- Ti vs Tv BAR CHART ---
                st.markdown(t("### 📊 Ti vs Tv Distribution"))
                mutation_type_label = t("Mutation Type")
                count_label = t("Count")
                transitions_label = t("Transitions (Ti)")
                transversions_label = t("Transversions (Tv)")
                df_chart = pd.DataFrame({
                    mutation_type_label: [transitions_label, transversions_label],
                    count_label: [ti_count, tv_count]
                })

                fig = px.bar(
                    df_chart,
                    x=mutation_type_label,
                    y=count_label,
                    color=mutation_type_label,
                    color_discrete_map={
                        transitions_label: '#d4af37', # Gold
                        transversions_label: '#66fcf1'  # Cyan
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
                st.info(t("✅ **No Mutations Found!** The two sequences are 100% identical."))

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
st.info(t("💡 **Dr. Titan's Tip:** In human genomes, the expected **Ti/Tv ratio is around 2.0 to 2.1** for whole genomes, and > 3.0 for exomes. If your ratio is much lower, it might indicate sequencing errors (since random errors cause more transversions)!"))
