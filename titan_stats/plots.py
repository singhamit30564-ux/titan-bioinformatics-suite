"""Plot-ready JSON builders: volcano, MA, PCA, sample-distance heatmap,
clustered top-N heatmap, GO/KEGG enrichment input lists.

Every builder returns a plain JSON-serializable dict with a ``"type"`` tag and
``"points"``/``"rows"`` arrays — consumed by the Streamlit pages (which render
Plotly figures) and by the web dashboard (which renders WebGL/canvas charts).
No chart data is written to disk.
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

__all__ = [
    "volcano_json",
    "ma_json",
    "pca_json",
    "sample_distance_json",
    "top_heatmap_json",
    "enrichment_lists",
    "go_kegg_json",
]


def _clean_float(value: Any) -> Optional[float]:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f if np.isfinite(f) else None


def volcano_json(
    results: pd.DataFrame,
    fdr_threshold: float = 0.05,
    lfc_threshold: float = 1.0,
    label_top_n: int = 20,
) -> dict[str, Any]:
    frame = results.copy()
    frame["neg_log10_padj"] = [
        -np.log10(max(float(p), 1e-300)) if pd.notna(p) else None for p in frame.get("padj", [])
    ]
    points = []
    for _, row in frame.iterrows():
        padj = row.get("padj")
        lfc = row.get("log2FC")
        significant = (
            padj is not None
            and pd.notna(padj)
            and float(padj) < fdr_threshold
            and lfc is not None
            and pd.notna(lfc)
            and abs(float(lfc)) >= lfc_threshold
        )
        points.append(
            {
                "gene": str(row.get("gene", "")),
                "x": _clean_float(lfc),
                "y": _clean_float(row.get("neg_log10_padj")),
                "padj": _clean_float(padj),
                "significant": bool(significant),
            }
        )
    labeled = sorted(
        (p for p in points if p["significant"] and p["x"] is not None and p["y"] is not None),
        key=lambda p: (-(p["y"] or 0.0), -abs(p["x"] or 0.0)),
    )[:label_top_n]
    return {
        "type": "volcano",
        "x_label": "log2 fold change",
        "y_label": "-log10(FDR)",
        "thresholds": {"fdr": fdr_threshold, "lfc": lfc_threshold},
        "points": points,
        "labels": [p["gene"] for p in labeled],
    }


def ma_json(results: pd.DataFrame) -> dict[str, Any]:
    points = []
    for _, row in results.iterrows():
        base = row.get("baseMean")
        lfc = row.get("log2FC")
        padj = row.get("padj")
        points.append(
            {
                "gene": str(row.get("gene", "")),
                "x": _clean_float(np.log10(max(float(base), 1e-9))) if pd.notna(base) else None,
                "y": _clean_float(lfc),
                "padj": _clean_float(padj),
            }
        )
    return {"type": "ma", "x_label": "log10 base mean", "y_label": "log2FC", "points": points}


def pca_json(
    normalized_counts: pd.DataFrame,
    metadata: Optional[pd.DataFrame] = None,
    n_components: int = 3,
) -> dict[str, Any]:
    """PCA over samples (SVD on mean-centered log2 normalized counts)."""
    values = np.log2(normalized_counts.values.astype(float) + 1.0)
    sample_names = [str(c) for c in normalized_counts.columns]
    gene_names = [str(g) for g in normalized_counts.index]
    mean = values.mean(axis=1, keepdims=True)
    centered = values - mean
    # samples as rows for the SVD
    u, singular, vt = np.linalg.svd(centered.T, full_matrices=False)
    total_var = float((singular ** 2).sum()) or 1.0
    explained = (singular ** 2) / total_var
    pcs = u * singular
    groups = {}
    if metadata is not None and not metadata.empty:
        for column in metadata.columns:
            groups[str(column)] = [
                str(metadata.loc[s, column]) if s in metadata.index else "" for s in sample_names
            ]
    samples = []
    for i, name in enumerate(sample_names):
        row = {"sample": name}
        for c in range(min(n_components, pcs.shape[1])):
            row[f"PC{c + 1}"] = _clean_float(pcs[i, c])
        for column, values_col in groups.items():
            row[column] = values_col[i]
        samples.append(row)
    loadings = []
    for gi, gene in enumerate(gene_names[:2000]):
        row = {"gene": gene}
        for c in range(min(n_components, vt.shape[0])):
            row[f"PC{c + 1}"] = _clean_float(vt[c, gi])
        loadings.append(row)
    return {
        "type": "pca",
        "samples": samples,
        "loadings": loadings,
        "explained_variance_ratio": [_clean_float(v) for v in explained[:n_components]],
        "n_genes": len(gene_names),
    }


def sample_distance_json(normalized_counts: pd.DataFrame) -> dict[str, Any]:
    """Euclidean sample-distance matrix on log2 normalized counts."""
    values = np.log2(normalized_counts.values.astype(float) + 1.0)
    names = [str(c) for c in normalized_counts.columns]
    matrix = np.linalg.norm(values.T[:, None, :] - values.T[None, :, :], axis=2)
    return {
        "type": "sample_distance",
        "samples": names,
        "matrix": [[_clean_float(v) for v in row] for row in matrix],
        "metric": "euclidean(log2 normalized)",
    }


def top_heatmap_json(
    normalized_counts: pd.DataFrame,
    results: pd.DataFrame,
    top_n: int = 50,
    z_score: bool = True,
) -> dict[str, Any]:
    """Top-N DE genes × samples heatmap matrix (row-cluster order via mean
    linkage on z-scored rows — a dependency-free ordering)."""
    ranked = results.dropna(subset=["padj"]).sort_values("padj").head(top_n)
    genes = [str(g) for g in ranked["gene"] if str(g) in set(map(str, normalized_counts.index))]
    if not genes:
        genes = [str(g) for g in normalized_counts.index[:top_n]]
    sub = normalized_counts.loc[genes].astype(float)
    values = np.log2(sub.values + 1.0)
    if z_score:
        mean = values.mean(axis=1, keepdims=True)
        std = values.std(axis=1, keepdims=True)
        std[std == 0] = 1.0
        values = (values - mean) / std
    order = np.argsort(values.mean(axis=1))
    rows = []
    for gi in order:
        rows.append(
            {
                "gene": genes[int(gi)],
                "values": [_clean_float(v) for v in values[int(gi)]],
            }
        )
    return {
        "type": "top_heatmap",
        "samples": [str(c) for c in sub.columns],
        "rows": rows,
        "z_score": z_score,
        "top_n": top_n,
    }


def enrichment_lists(
    results: pd.DataFrame,
    fdr_threshold: float = 0.05,
    lfc_threshold: float = 1.0,
) -> dict[str, list[str]]:
    """Ranked gene lists ready for GO/KEGG enrichment tools (g:Profiler, DAVID).

    ``up`` / ``down``: significant genes by direction; ``ranked_all``: all genes
    sorted by padj (for pre-ranked GSEA).
    """
    frame = results.copy()
    significant = frame[
        (pd.to_numeric(frame.get("padj"), errors="coerce") < fdr_threshold)
        & (pd.to_numeric(frame.get("log2FC"), errors="coerce").abs() >= lfc_threshold)
    ]
    up = significant[pd.to_numeric(significant.get("log2FC"), errors="coerce") > 0]["gene"].astype(str).tolist()
    down = significant[pd.to_numeric(significant.get("log2FC"), errors="coerce") < 0]["gene"].astype(str).tolist()
    ranked_all = (
        frame.assign(_p=pd.to_numeric(frame.get("padj"), errors="coerce"))
        .sort_values("_p", na_position="last")["gene"]
        .astype(str)
        .tolist()
    )
    return {"up": up, "down": down, "ranked_all": ranked_all}


def go_kegg_json(
    results: pd.DataFrame,
    fdr_threshold: float = 0.05,
    lfc_threshold: float = 1.0,
) -> dict[str, Any]:
    """Plot-ready GO/KEGG payload: up/down candidate genes + ranked list.

    Output is the standard enrichment-tool input shape (g:Profiler, DAVID,
    clusterProfiler ``TERM2GENE`` pipelines) plus a ranking suitable for GSEA.
    """
    lists = enrichment_lists(results, fdr_threshold=fdr_threshold, lfc_threshold=lfc_threshold)
    return {
        "type": "go_kegg",
        "thresholds": {"fdr": fdr_threshold, "log2fc": lfc_threshold},
        "go_kegg": {
            "up_candidates": lists["up"],
            "down_candidates": lists["down"],
            "ranked_all": lists["ranked_all"],
        },
        "counts": {
            "up": len(lists["up"]),
            "down": len(lists["down"]),
            "ranked": len(lists["ranked_all"]),
        },
    }
