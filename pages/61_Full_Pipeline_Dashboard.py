"""Full Central Dogma Pipeline Dashboard: DNA → RNA → Protein with analytics."""
import plotly.graph_objects as go
import streamlit as st

from titan_utils import (
    clean_sequence,
    CODON_TABLE_STANDARD,
    gc_fraction_safe,
    translate,
    validate_dna,
)
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🧬",
    "Full Central Dogma Pipeline Dashboard",
    "Visualize the complete DNA → RNA → Protein pipeline with real-time "
    "analytics and charts.",
)

dna_input = st.text_area(
    "Enter DNA Sequence (coding strand 5' → 3')",
    "ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG",
    height=150,
)

if st.button("▶️ Run Full Pipeline", type="primary", use_container_width=True):
    seq, err = validate_dna(dna_input)
    if err:
        st.error(err)
    else:
        # 1. Transcription (coding DNA → mRNA: T → U)
        rna_seq = seq.replace("T", "U")

        # 2. Translation using the verified standard codon table (DNA codons)
        protein_seq = translate(seq)

        length = len(seq)
        gc_pct = gc_fraction_safe(seq) * 100

        # Molecular weights (approximate, commonly used averages)
        # ≈ 303.7 Da per base (sodium salt avg), minus H2O per phosphodiester
        mw_dna = length * 303.7 - (length - 1) * 18.02
        # ≈ 110 Da per amino acid residue average
        mw_protein = sum(110 for aa in protein_seq if aa != "*")

        # ---- Row 1 : sequences ----
        st.markdown("### 📊 Sequence Dashboard")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**🧬 DNA**")
            st.code(seq, language="text")
            st.metric("Length", f"{length} bp")
        with c2:
            st.markdown("**🧫 mRNA**")
            st.code(rna_seq, language="text")
            st.metric("Length", f"{len(rna_seq)} nt")
        with c3:
            st.markdown("**🥩 Protein**")
            st.code(protein_seq, language="text")
            st.metric("Length", f"{len(protein_seq)} aa")

        st.markdown("---")

        # ---- Row 2 : metrics ----
        m1, m2, m3 = st.columns(3)
        m1.metric("GC Content", f"{gc_pct:.1f}%")
        m2.metric("DNA Mol. Weight", f"{mw_dna/1000:.2f} kDa")
        m3.metric("Protein Mol. Weight", f"{mw_protein/1000:.2f} kDa")

        st.markdown("### 📈 Nucleotide Composition")
        fig = go.Figure(data=[go.Pie(
            labels=["Adenine (A)", "Thymine (T)", "Cytosine (C)", "Guanine (G)"],
            values=[seq.count("A"), seq.count("T"), seq.count("C"), seq.count("G")],
            marker=dict(colors=["#ff0055", "#d4af37", "#66fcf1", "#ffffff"]),
            hole=0.4,
        )])
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0a0e17",
            font=dict(color="#e0e0e0"),
            showlegend=True,
            legend=dict(x=0.5, y=-0.2, orientation="h"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Report codon-table size for sanity
        st.caption(f"Standard genetic code: {len(CODON_TABLE_STANDARD)} codons loaded.")

dr_titan_tip(
    "This dashboard represents the Central Dogma of Molecular Biology. "
    "GC content and molecular weight are critical parameters for primer "
    "design and for predicting protein behaviour in the lab."
)
