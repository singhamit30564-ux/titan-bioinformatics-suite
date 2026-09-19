"""Reverse Complement & Sequence Stats — refactored to use titan_utils."""

import pandas as pd
import plotly.express as px
import streamlit as st
from Bio.Seq import Seq

from titan_utils import revcomp, validate_dna, gc_fraction_safe
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title, sequence_metrics_row

titan_title(
    "🧬",
    "Reverse Complement & Stats",
    "Generate the reverse complement and get a full statistical breakdown using validated Titan utilities.",
)

dna_input = st.text_area("Enter DNA Sequence (5' to 3'):", "ATGCGCTAGCTAGCTAGCTAGCTAGCATCGATCG", height=150, key="rev_comp_input")

col1, col2 = st.columns([3, 1])
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    calculate_btn = st.button("🔄 Analyze Sequence", use_container_width=True, type="primary")

if calculate_btn:
    seq, err = validate_dna(dna_input)
    if err:
        st.error(err)
    else:
        try:
            # Use titan_utils revcomp (handles IUPAC correctly) + Biopython for display
            rev_comp = revcomp(seq)
            # Biopython cross-check
            # rev_comp = str(Seq(seq).reverse_complement())

            length = len(seq)
            count_a = seq.count('A')
            count_t = seq.count('T')
            count_c = seq.count('C')
            count_g = seq.count('G')
            gc_percent = gc_fraction_safe(seq) * 100

            st.markdown("### 📊 Sequence Statistics")
            sequence_metrics_row({
                "📏 Length": f"{length} bp",
                "🧬 GC Content": f"{gc_percent:.2f}%",
                "🧫 AT Content": f"{100 - gc_percent:.2f}%",
                "⚖️ AT/GC Ratio": f"{(count_a + count_t) / (count_c + count_g):.2f}" if (count_c + count_g) > 0 else "N/A",
            })

            st.markdown("---")
            st.markdown("### 🔄 Reverse Complement")
            st.code(rev_comp, language="text")

            st.markdown("---")
            st.markdown("### 🥧 Nucleotide Composition")

            df_chart = pd.DataFrame({
                'Nucleotide': ['Adenine (A)', 'Thymine (T)', 'Cytosine (C)', 'Guanine (G)'],
                'Count': [count_a, count_t, count_c, count_g]
            })

            fig = px.pie(
                df_chart,
                values='Count',
                names='Nucleotide',
                color_discrete_map={
                    'Adenine (A)': '#ff6b6b',
                    'Thymine (T)': '#feca57',
                    'Cytosine (C)': '#48dbfb',
                    'Guanine (G)': '#1dd1a1'
                },
                hole=0.4
            )
            fig.update_layout(
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#0a0e17',
                font=dict(color='#e0e0e0'),
                margin=dict(t=0, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)

            # Real export via titan_utils smart_lock
            df_export = pd.DataFrame([{
                "input": seq,
                "reverse_complement": rev_comp,
                "length": length,
                "GC_percent": round(gc_percent, 2),
                "A": count_a, "T": count_t, "C": count_c, "G": count_g
            }])
            smart_lock(csv_data=df_to_csv_bytes(df_export), csv_filename="revcomp_stats.csv")

        except Exception as e:
            st.error(f"⚠️ Calculation Error: {e}")

dr_titan_tip("The reverse complement is crucial for the opposite strand — DNA is anti-parallel. A 5'→3' strand's reverse complement gives you the correct 3'→5' strand, handling IUPAC ambiguity codes via titan_utils.revcomp.")
