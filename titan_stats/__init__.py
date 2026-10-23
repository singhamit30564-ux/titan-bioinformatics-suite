"""titan_stats — statistical & data-modeling layer (Layer B).

* :mod:`titan_stats.de` — differential expression (PyDESeq2 default, R bridge
  for DESeq2/edgeR/limma-voom via ``Rscript`` + JSON, pure-NumPy fallback).
* :mod:`titan_stats.plots` — plot-ready JSON for volcano / MA / PCA / sample
  distance / clustered heatmaps / enrichment input lists.
* :mod:`titan_stats.ml_variants` — variant pathogenicity classifier
  (scikit-learn + optional XGBoost/SHAP; synthetic training data is labeled
  SYNTHETIC in code, UI and exports).
* :mod:`titan_stats.dimred` — PCA / UMAP / k-means / hierarchical clustering.
* :mod:`titan_stats.r_bridge` — safe ``Rscript`` subprocess bridge (JSON
  in/out, no ``shell=True``).
* :mod:`titan_stats.provenance` — run provenance records compatible with
  :mod:`titan_utils.privacy` and the ELN audit trail.

Every run returns provenance (input hashes, package versions, params, seed).
No module writes genomic data to disk: matrices travel as bytes/JSON in RAM.
"""
from __future__ import annotations

from titan_stats.provenance import stats_provenance  # noqa: F401

__all__ = ["stats_provenance"]
