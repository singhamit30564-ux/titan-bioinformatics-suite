"""⚡ Pro Engine console — Expression Explorer (Layer B).

PCA / UMAP (optional) / k-means / hierarchical clustering / top-gene heatmap
over a normalized expression matrix. Pure-NumPy fallbacks everywhere, so the
page always renders — even with no optional dependencies installed.
"""
from __future__ import annotations

import io
import json

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from titan_stats import dimred
from titan_stats import plots as titan_plots
from titan_utils import engine
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title(
    "⚡",
    "Expression Explorer",
    "PCA · UMAP (optional) · k-means · hierarchical clustering · interactive heatmaps.",
)
st.markdown(
    "Paste a normalized expression matrix (genes × samples, CSV). Everything runs in RAM; "
    "every export is free (CSV/JSON)."
)
st.markdown("---")

engine.render_engine_toggle(key="expr_engine_toggle")

DEFAULT_MATRIX = """gene,s1,s2,s3,s4,s5,s6
geneA,10,12,11,90,95,88
geneB,80,85,78,12,10,14
geneC,50,52,48,51,49,50
geneD,5,4,6,60,58,62
geneE,95,90,92,8,9,7
geneF,30,28,31,29,30,33
geneG,70,72,69,20,22,19
geneH,25,24,26,25,27,24
"""

matrix_text = st.text_area("📊 Expression matrix (CSV, genes × samples)", DEFAULT_MATRIX, height=240)

g1, g2, g3 = st.columns(3)
with g1:
    n_clusters = st.number_input("Clusters (k)", min_value=2, max_value=10, value=2, step=1)
with g2:
    top_n = st.number_input("Top-N genes for heatmap", min_value=5, max_value=200, value=50, step=5)
with g3:
    log_transform = st.checkbox("log2(x+1) transform", value=True)

run_pca = st.button("🧭 Run PCA & Clustering", type="primary", use_container_width=True)
run_umap = st.button("🗺️ Run UMAP (PCA fallback if missing)", use_container_width=True)
export_json = st.button("📥 Export analysis JSON", use_container_width=True)


def _load_matrix() -> pd.DataFrame:
    frame = pd.read_csv(io.StringIO(matrix_text))
    frame = frame.rename(columns={frame.columns[0]: "gene"})
    return frame.set_index("gene")


if run_pca or run_umap:
    try:
        matrix = _load_matrix()
        with st.spinner("Reducing dimensions…"):
            pca_result = dimred.pca(matrix, n_components=3, log_transform=bool(log_transform), transpose=True)
            kmeans = dimred.kmeans_cluster(matrix, n_clusters=int(n_clusters), log_transform=bool(log_transform), transpose=True)
            hierarchical = dimred.hierarchical_cluster(matrix, n_clusters=int(n_clusters), log_transform=bool(log_transform), transpose=True)
            distances = titan_plots.sample_distance_json(matrix)
            heatmap = titan_plots.top_heatmap_json(
                matrix,
                pd.DataFrame({"gene": matrix.index, "padj": np.linspace(0.001, 0.5, matrix.shape[0])}),
                top_n=int(top_n),
            )
            umap_result = None
            if run_umap:
                umap_result = dimred.umap_embed(matrix, n_components=2, log_transform=bool(log_transform), transpose=True)
        st.session_state["expr_state"] = {
            "pca": pca_result,
            "kmeans": kmeans,
            "hierarchical": hierarchical,
            "distances": distances,
            "heatmap": heatmap,
            "umap": umap_result,
        }
    except Exception as exc:
        st.warning(f"Analysis failed: {exc}")
        st.session_state["expr_state"] = None

state = st.session_state.get("expr_state")
if state:
    st.success(f"✅ PCA complete · {state['pca']['n_components']} components · k-means k={state['kmeans']['n_clusters']} ({state['kmeans']['backend']})")

    pca_df = pd.DataFrame(state["pca"]["points"])
    if {"PC1", "PC2"}.issubset(pca_df.columns):
        st.markdown("### 🧭 PCA (samples)")
        fig = px.scatter(pca_df, x="PC1", y="PC2", hover_data=["id"], title="PCA — PC1 vs PC2")
        st.plotly_chart(fig, use_container_width=True)
        explained = state["pca"]["explained_variance_ratio"]
        st.caption("Explained variance: " + ", ".join(f"PC{i+1}={v:.1%}" for i, v in enumerate(explained)))

    if state.get("umap"):
        umap_df = pd.DataFrame(state["umap"]["points"])
        cols = [c for c in umap_df.columns if c.startswith("UMAP")]
        if cols:
            st.markdown(f"### 🗺️ UMAP ({state['umap']['method']})")
            st.plotly_chart(px.scatter(umap_df, x=cols[0], y=cols[1] if len(cols) > 1 else cols[0], hover_data=["id"]), use_container_width=True)

    cluster_df = pd.DataFrame(state["kmeans"]["groups"])
    st.markdown("### 🎯 k-means cluster membership")
    st.dataframe(cluster_df, use_container_width=True, hide_index=True)

    st.markdown("### 🔥 Top-gene heatmap (row z-scores)")
    heat = state["heatmap"]
    heat_df = pd.DataFrame(
        [row["values"] for row in heat["rows"]],
        index=[row["gene"] for row in heat["rows"]],
        columns=heat["samples"],
    )
    st.plotly_chart(px.imshow(heat_df, aspect="auto", color_continuous_scale="RdBu_r"), use_container_width=True)

    st.markdown("### 📏 Sample distance matrix")
    st.dataframe(
        pd.DataFrame(state["distances"]["matrix"], index=state["distances"]["samples"], columns=state["distances"]["samples"]),
        use_container_width=True,
    )

    if export_json:
        st.download_button(
            "📥 Download analysis JSON",
            data=json.dumps(state, indent=2, default=str).encode("utf-8"),
            file_name="titan_expression_explorer.json",
            mime="application/json",
            use_container_width=True,
        )
    smart_lock(
        csv_data=pd.DataFrame(state["pca"]["points"]).to_csv(index=False).encode("utf-8"),
        csv_filename="titan_expression_pca.csv",
    )
else:
    st.info("👆 Press **Run PCA & Clustering** to explore the toy expression matrix above.")

dr_titan_tip(
    "PCA finds the axes of largest variance across samples — useful to spot batch effects and "
    "outliers. Clustering groups co-expressed genes or similar samples. For publication-grade "
    "work, validate clusters with biological replicates and adjust for known covariates first."
)
