"""Dimensionality reduction & clustering: PCA, UMAP (optional), k-means,
hierarchical clustering — NumPy-first with sklearn acceleration when present.

All functions return JSON-safe dicts; fixed seeds; no disk writes.
"""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd

__all__ = ["pca", "umap_embed", "kmeans_cluster", "hierarchical_cluster", "cluster_metrics"]


def _to_matrix(data: pd.DataFrame, transpose: bool = False) -> tuple[np.ndarray, list[str], list[str]]:
    values = data.apply(pd.to_numeric, errors="coerce").fillna(0.0).to_numpy(dtype=float)
    genes = [str(x) for x in data.index]
    samples = [str(x) for x in data.columns]
    if transpose:
        return values.T, samples, genes
    return values, genes, samples


def pca(
    data: pd.DataFrame,
    n_components: int = 3,
    log_transform: bool = True,
    transpose: bool = False,
) -> dict[str, Any]:
    """PCA via SVD (mean-centered, optional log2(x+1) transform)."""
    matrix, row_names, col_names = _to_matrix(data, transpose=transpose)
    if log_transform:
        matrix = np.log2(np.abs(matrix) + 1.0)
    mean = matrix.mean(axis=0, keepdims=True)
    centered = matrix - mean
    u, singular, vt = np.linalg.svd(centered, full_matrices=False)
    total = float((singular ** 2).sum()) or 1.0
    explained = (singular ** 2) / total
    k = max(1, min(n_components, u.shape[1]))
    coords = u[:, :k] * singular[:k]
    points = []
    for i, name in enumerate(row_names):
        row = {"id": name}
        for c in range(k):
            row[f"PC{c + 1}"] = float(coords[i, c])
        points.append(row)
    loadings = []
    for j, feature in enumerate(col_names):
        row = {"feature": feature}
        for c in range(k):
            row[f"PC{c + 1}"] = float(vt[c, j])
        loadings.append(row)
    return {
        "type": "pca",
        "points": points,
        "loadings": loadings[:2000],
        "explained_variance_ratio": [float(v) for v in explained[:k]],
        "n_components": k,
    }


def umap_embed(
    data: pd.DataFrame,
    n_components: int = 2,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    seed: int = 1337,
    transpose: bool = False,
) -> dict[str, Any]:
    """UMAP embedding (requires ``umap-learn``); PCA fallback otherwise."""
    matrix, row_names, _ = _to_matrix(data, transpose=transpose)
    matrix = np.log2(np.abs(matrix) + 1.0)
    try:
        import umap  # type: ignore

        reducer = umap.UMAP(
            n_components=n_components,
            n_neighbors=n_neighbors,
            min_dist=min_dist,
            random_state=seed,
        )
        embedding = reducer.fit_transform(matrix)
        method = "umap-learn"
    except Exception as exc:
        # Honest fallback: top principal components, labeled as such.
        centered = matrix - matrix.mean(axis=0, keepdims=True)
        u, singular, _ = np.linalg.svd(centered, full_matrices=False)
        k = max(1, min(n_components, u.shape[1]))
        embedding = u[:, :k] * singular[:k]
        method = f"pca-fallback (umap unavailable: {type(exc).__name__})"
    points = []
    for i, name in enumerate(row_names):
        row = {"id": name}
        for c in range(embedding.shape[1]):
            row[f"UMAP{c + 1}"] = float(embedding[i, c])
        points.append(row)
    return {"type": "umap", "method": method, "points": points, "n_components": int(embedding.shape[1])}


def kmeans_cluster(
    data: pd.DataFrame,
    n_clusters: int = 3,
    seed: int = 1337,
    log_transform: bool = True,
    transpose: bool = False,
) -> dict[str, Any]:
    """k-means clustering (sklearn when available, else a NumPy Lloyd loop)."""
    matrix, row_names, _ = _to_matrix(data, transpose=transpose)
    if log_transform:
        matrix = np.log2(np.abs(matrix) + 1.0)
    n_clusters = int(max(1, min(n_clusters, max(1, matrix.shape[0] - 1))))
    labels: np.ndarray
    centers: np.ndarray
    try:
        from sklearn.cluster import KMeans

        model = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
        labels = model.fit_predict(matrix)
        centers = model.cluster_centers_
        backend = "sklearn"
    except Exception:
        rng = np.random.default_rng(seed)
        indices = rng.choice(matrix.shape[0], size=n_clusters, replace=False)
        centers = matrix[indices].copy()
        labels = np.zeros(matrix.shape[0], dtype=int)
        for _ in range(100):
            distances = np.linalg.norm(matrix[:, None, :] - centers[None, :, :], axis=2)
            new_labels = distances.argmin(axis=1)
            if np.array_equal(new_labels, labels):
                break
            labels = new_labels
            for c in range(n_clusters):
                members = matrix[labels == c]
                if members.size:
                    centers[c] = members.mean(axis=0)
        backend = "numpy-lloyd"
    groups = []
    for i, name in enumerate(row_names):
        groups.append({"id": name, "cluster": int(labels[i])})
    return {
        "type": "kmeans",
        "backend": backend,
        "n_clusters": n_clusters,
        "groups": groups,
        "centers": [[float(v) for v in row] for row in centers],
    }


def hierarchical_cluster(
    data: pd.DataFrame,
    n_clusters: int = 3,
    linkage: str = "ward",
    log_transform: bool = True,
    transpose: bool = False,
) -> dict[str, Any]:
    """Agglomerative clustering + a merge-order 'dendrogram' approximation.

    Without SciPy's dendrogram machinery the returned ``order`` is a
    cluster-major leaf order (adequate for heatmap reordering), labeled
    honestly in ``method``.
    """
    matrix, row_names, _ = _to_matrix(data, transpose=transpose)
    if log_transform:
        matrix = np.log2(np.abs(matrix) + 1.0)
    n_clusters = int(max(1, min(n_clusters, max(1, matrix.shape[0] - 1))))
    try:
        from sklearn.cluster import AgglomerativeClustering

        model = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
        labels = model.fit_predict(matrix)
        backend = f"sklearn-agglomerative({linkage})"
        children = getattr(model, "children_", None)
    except Exception:
        # Fallback: k-means labels (documented as approximation).
        fallback = kmeans_cluster(data, n_clusters=n_clusters, log_transform=False, transpose=transpose)
        labels = np.array([g["cluster"] for g in fallback["groups"]], dtype=int)
        backend = "kmeans-approximation (sklearn unavailable)"
        children = None
    order = np.lexsort((np.arange(len(labels)), labels))
    groups = [{"id": row_names[i], "cluster": int(labels[i])} for i in range(len(labels))]
    result = {
        "type": "hierarchical",
        "method": backend,
        "n_clusters": n_clusters,
        "groups": groups,
        "order": [int(i) for i in order],
    }
    if children is not None:
        result["children"] = [[int(a), int(b)] for a, b in children]
    return result


def cluster_metrics(data: pd.DataFrame, labels: Sequence[int], log_transform: bool = True) -> dict[str, Any]:
    """Silhouette-style summary without sklearn (mean intra/inter distance)."""
    matrix, row_names, _ = _to_matrix(data)
    if log_transform:
        matrix = np.log2(np.abs(matrix) + 1.0)
    labels_arr = np.asarray(labels, dtype=int)
    if len(labels_arr) != matrix.shape[0]:
        raise ValueError("labels length must match data rows")
    clusters = sorted(set(labels_arr.tolist()))
    intra, inter = [], []
    for i in range(matrix.shape[0]):
        same = matrix[(labels_arr == labels_arr[i]) & (np.arange(len(labels_arr)) != i)]
        other = matrix[labels_arr != labels_arr[i]]
        if same.size:
            intra.append(float(np.linalg.norm(same - matrix[i], axis=1).mean()))
        if other.size:
            inter.append(float(np.linalg.norm(other - matrix[i], axis=1).mean()))
    mean_intra = float(np.mean(intra)) if intra else 0.0
    mean_inter = float(np.mean(inter)) if inter else 0.0
    return {
        "n_clusters": len(clusters),
        "mean_intra_distance": mean_intra,
        "mean_inter_distance": mean_inter,
        "separation_ratio": (mean_inter / mean_intra) if mean_intra > 0 else None,
        "n_points": int(matrix.shape[0]),
    }
