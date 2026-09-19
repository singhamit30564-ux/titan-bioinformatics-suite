"""GO Enrichment Analyzer (demo with curated mock database).

NOTE: This is an educational demo using a small, curated in-memory
database of common cancer-related GO terms. It does NOT call the real
Gene Ontology / Ensembl API; a real implementation would query
`goatools`, `mygene.info`, or EMBL-EBI QuickGO.
"""
import math
import random

import pandas as pd
import plotly.express as px
import streamlit as st

from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title(
    "🧬", "GO Enrichment Analyzer",
    "Analyze and visualize enriched Biological Processes, Molecular "
    "Functions, and Cellular Components for a gene list.",
)
st.caption(
    "⚠️ **Demo mode** — this page ships with a curated mock GO database to "
    "illustrate enrichment-plotting mechanics. It does not yet call the "
    "real GO/QuickGO API."
)

# Curated mock database (demo only)
GO_DATABASE = {
    "GO:0006915": {"term": "Apoptotic process", "category": "Biological Process", "p_value": 0.001},
    "GO:0005524": {"term": "ATP binding", "category": "Molecular Function", "p_value": 0.005},
    "GO:0005634": {"term": "Nucleus", "category": "Cellular Component", "p_value": 0.010},
    "GO:0006955": {"term": "Immune response", "category": "Biological Process", "p_value": 0.0001},
    "GO:0004672": {"term": "Protein kinase activity", "category": "Molecular Function", "p_value": 0.020},
    "GO:0016020": {"term": "Membrane", "category": "Cellular Component", "p_value": 0.030},
    "GO:0006351": {"term": "Transcription, DNA-templated", "category": "Biological Process", "p_value": 0.004},
    "GO:0003677": {"term": "DNA binding", "category": "Molecular Function", "p_value": 0.008},
}

st.markdown("### 📥 Input Gene List")
gene_input = st.text_area(
    "Enter Gene IDs or names (comma- or newline-separated)",
    "TP53, BRCA1, EGFR, MYC, AKT1, MTOR, PTEN, KRAS",
    height=100,
)

if st.button("🔬 Run GO Enrichment Analysis", type="primary", use_container_width=True):
    genes = [g.strip().upper() for g in gene_input.replace(",", "\n").split("\n") if g.strip()]
    if len(genes) < 2:
        st.error("❌ Please enter at least 2 genes!")
    else:
        with st.spinner("🧮 Computing enrichment scores..."):
            # Deterministic demo mapping: each gene deterministically maps to a
            # subset of GO terms via a stable hash so results don't change on
            # every re-run (the original code used random.sample which changed
            # every click).
            results = []
            for go_id, data in GO_DATABASE.items():
                # Pseudo-mapping: pick genes deterministically from the list
                # using hash modulo to illustrate the visualisation.
                mapped = [g for i, g in enumerate(genes) if (hash(g + go_id) % 3) == 0]
                if not mapped:
                    mapped = genes[:2]
                results.append({
                    "GO ID": go_id,
                    "Term": data["term"],
                    "Category": data["category"],
                    "Gene Count": len(mapped),
                    "P-Value": data["p_value"],
                    "-log10(P)": round(-math.log10(data["p_value"]), 3),
                    "Mapped Genes": ", ".join(mapped),
                })
            df = pd.DataFrame(results).sort_values(by="P-Value")

            st.markdown("### 📊 Enrichment Results")
            fig = px.bar(
                df,
                x="Term",
                y="-log10(P)",
                color="Category",
                color_discrete_map={
                    "Biological Process": "#d4af37",
                    "Molecular Function": "#66fcf1",
                    "Cellular Component": "#ff0055",
                },
                hover_data=["GO ID", "Gene Count", "Mapped Genes"],
                title="GO Enrichment Significance (-log10 P-value)",
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0a0e17",
                plot_bgcolor="#1a1f2e",
                font=dict(color="#e0e0e0"),
                xaxis_title="Gene Ontology Term",
                yaxis_title="-log10(P) (higher = more significant)",
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📋 Detailed GO Terms Table")
            st.dataframe(df, use_container_width=True, hide_index=True)

            smart_lock(csv_data=df_to_csv_bytes(df), csv_filename="go_enrichment.csv")

dr_titan_tip(
    "A low P-value (< 0.05) and high -log10(P) means the term is significantly "
    "enriched in your gene list, suggesting a common biological theme (e.g., "
    "many of your genes participate in 'Apoptotic process')."
)
