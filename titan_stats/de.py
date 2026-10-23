"""Differential expression: PyDESeq2 default, R bridge optional, pure-NumPy
fallback so the app never crashes when optional engines are missing.

Engine selection order (each labeled honestly in ``result["method"]``):

1. ``r-deseq2`` / ``r-edger`` / ``r-limma`` — when ``method="r"`` (or "auto"
   with R available) and the requested Bioconductor package is installed.
2. ``pydeseq2`` — when the ``pydeseq2`` package imports and method allows it.
3. ``fallback-ttest`` — median-of-ratios normalization + Welch t-test on
   log2(normalized+1) + Benjamini–Hochberg FDR. **Not** DESeq2: no NB GLM, no
   dispersion shrinkage, no covariates beyond the primary factor. The method
   name in the result says exactly what ran.

All engines return the same schema (see :func:`run_differential_expression`).
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from titan_stats.provenance import stats_provenance

__all__ = ["run_differential_expression", "filter_low_counts", "normalize_median_of_ratios", "benjamini_hochberg"]

DEFAULT_SEED = 1337


def filter_low_counts(
    counts: pd.DataFrame,
    min_count: int = 10,
    min_samples: Optional[int] = None,
) -> tuple[pd.DataFrame, int]:
    """Keep genes with ``count >= min_count`` in at least ``min_samples``.

    Accepts genes-as-rows or samples-as-rows (auto-oriented toward
    genes-as-rows by :func:`_orient_counts`).
    """
    if min_samples is None:
        min_samples = max(2, counts.shape[1] // 2) if counts.shape[1] > 2 else 1
    keep = (counts.values >= min_count).sum(axis=1) >= min_samples
    return counts.loc[keep].copy(), int((~keep).sum())


def normalize_median_of_ratios(counts: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """DESeq2-style median-of-ratios size factors (robust to zeros)."""
    values = counts.values.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        log_values = np.log(values)
        log_values[~np.isfinite(log_values)] = np.nan
    with np.errstate(all="ignore"):
        log_geomeans = np.nanmean(log_values, axis=1)
    factors = []
    for col in range(values.shape[1]):
        ratios = np.exp(log_values[:, col] - log_geomeans)
        ratios = ratios[np.isfinite(ratios)]
        factors.append(float(np.median(ratios)) if ratios.size else 1.0)
    size = pd.Series(factors, index=counts.columns, dtype=float)
    size = size.mask(size <= 0, 1.0)
    normalized = counts.divide(size, axis=1)
    return normalized, size


def benjamini_hochberg(pvalues: Sequence[float]) -> np.ndarray:
    """BH-FDR adjusted p-values (NaN-safe)."""
    p = np.asarray(list(pvalues), dtype=float)
    n = p.size
    adjusted = np.full(n, np.nan)
    valid = np.isfinite(p)
    m = int(valid.sum())
    if m == 0:
        return adjusted
    pv = p[valid]
    order = np.argsort(pv, kind="mergesort")
    ranked = pv[order]
    q = ranked * m / (np.arange(1, m + 1))
    q = np.minimum.accumulate(q[::-1])[::-1]
    q = np.clip(q, 0.0, 1.0)
    out = np.empty(m, dtype=float)
    out[order] = q
    adjusted[valid] = out
    return adjusted


def _orient_counts(
    counts: pd.DataFrame, metadata: pd.DataFrame
) -> tuple[pd.DataFrame, list[str]]:
    """Return counts as genes × samples with sample order matching metadata."""
    meta_index = [str(x) for x in metadata.index]
    if set(map(str, counts.columns)) >= set(meta_index) and counts.shape[1] >= len(meta_index):
        oriented = counts.copy()
        oriented.columns = [str(c) for c in counts.columns]
        sample_order = [s for s in meta_index if s in set(oriented.columns)]
        return oriented[sample_order], sample_order
    if set(map(str, counts.index)) >= set(meta_index):
        oriented = counts.T.copy()
        oriented.columns = [str(c) for c in oriented.columns]
        sample_order = [s for s in meta_index if s in set(oriented.columns)]
        return oriented[sample_order], sample_order
    raise ValueError(
        "counts matrix sample names must match metadata index (checked rows and columns)"
    )


def _design_factors(design: str) -> list[str]:
    text = (design or "~ condition").strip()
    if text.startswith("~"):
        text = text[1:]
    factors = [part.strip() for part in text.split("+") if part.strip()]
    return factors or ["condition"]


def _fallback_de(
    counts: pd.DataFrame,
    metadata: pd.DataFrame,
    design: str,
    contrast: tuple[str, str, str],
    min_count: int,
    min_samples: Optional[int],
    seed: int,
) -> dict[str, Any]:
    warnings: list[str] = []
    factors = _design_factors(design)
    primary = contrast[0] if contrast and contrast[0] in metadata.columns else factors[0]
    if primary not in metadata.columns:
        raise ValueError(f"design factor '{primary}' not found in metadata columns")
    if len(factors) > 1:
        warnings.append(
            "fallback-ttest ignores covariates beyond the primary factor "
            f"({', '.join(factors[1:])}); use pydeseq2 or the R bridge for full models."
        )
    factor_col, treated_level, control_level = (
        (primary, contrast[1], contrast[2]) if contrast and len(contrast) == 3 else (primary, None, None)
    )
    levels = sorted(metadata[factor_col].astype(str).unique())
    if treated_level is None:
        if len(levels) != 2:
            raise ValueError(
                f"fallback-ttest needs exactly 2 levels in '{factor_col}' (found {levels}); "
                "pass contrast=(factor, treated, control)"
            )
        control_level, treated_level = levels[0], levels[1]
    labels = metadata[factor_col].astype(str)
    treated_samples = [s for s in counts.columns if labels.get(s) == str(treated_level)]
    control_samples = [s for s in counts.columns if labels.get(s) == str(control_level)]
    if not treated_samples or not control_samples:
        raise ValueError("contrast levels must each contain at least one sample")

    filtered, n_filtered = filter_low_counts(counts, min_count=min_count, min_samples=min_samples)
    if filtered.empty:
        raise ValueError("all genes were filtered out; lower min_count/min_samples")
    normalized, size_factors = normalize_median_of_ratios(filtered)
    lognorm = np.log2(normalized.values.astype(float) + 1.0)

    treated_idx = [list(normalized.columns).index(s) for s in treated_samples]
    control_idx = [list(normalized.columns).index(s) for s in control_samples]
    treated = lognorm[:, treated_idx]
    control = lognorm[:, control_idx]
    with np.errstate(all="ignore"):
        mean_t = treated.mean(axis=1)
        mean_c = control.mean(axis=1)
        var_t = treated.var(axis=1, ddof=1) if treated.shape[1] > 1 else np.zeros_like(mean_t)
        var_c = control.var(axis=1, ddof=1) if control.shape[1] > 1 else np.zeros_like(mean_c)
        n_t = max(1, treated.shape[1])
        n_c = max(1, control.shape[1])
        se = np.sqrt(var_t / n_t + var_c / n_c)
        with np.errstate(divide="ignore", invalid="ignore"):
            t_stat = np.where(se > 0, (mean_t - mean_c) / se, 0.0)
    # Welch–Satterthwaite degrees of freedom.
    with np.errstate(divide="ignore", invalid="ignore"):
        num = (var_t / n_t + var_c / n_c) ** 2
        den = (var_t / n_t) ** 2 / max(1, n_t - 1) + (var_c / n_c) ** 2 / max(1, n_c - 1)
        dof = np.where(den > 0, num / den, float(n_t + n_c - 2))
    pvalues = _t_sf_two_sided(t_stat, dof)

    base_mean = normalized.values.astype(float).mean(axis=1)
    results = pd.DataFrame(
        {
            "gene": filtered.index.astype(str),
            "baseMean": base_mean,
            "log2FC": mean_t - mean_c,
            "stat": t_stat,
            "pvalue": pvalues,
        }
    )
    results["padj"] = benjamini_hochberg(results["pvalue"].tolist())
    results = results.sort_values("padj", na_position="last").reset_index(drop=True)

    normalized_out = pd.DataFrame(
        lognorm, index=filtered.index.astype(str), columns=normalized.columns
    )
    provenance = stats_provenance(
        analysis="differential_expression",
        inputs={
            "counts_matrix": counts.to_csv().encode("utf-8"),
            "metadata": metadata.to_csv().encode("utf-8"),
        },
        params={
            "method": "fallback-ttest",
            "design": design,
            "factor": factor_col,
            "contrast": [factor_col, treated_level, control_level],
            "min_count": min_count,
            "min_samples": min_samples,
        },
        seed=seed,
        engine="python",
    )
    return {
        "method": "fallback-ttest",
        "results": results,
        "normalized_counts": normalized_out,
        "size_factors": size_factors.to_dict(),
        "dispersion": None,
        "n_genes_input": int(counts.shape[0]),
        "n_genes_filtered": n_filtered,
        "n_genes_tested": int(results.shape[0]),
        "n_genes_significant_fdr05": int((results["padj"] < 0.05).sum()),
        "contrast": {"factor": factor_col, "treated": treated_level, "control": control_level},
        "warnings": warnings
        + ["fallback-ttest: no negative-binomial GLM, no dispersion shrinkage — labelled honestly."],
        "provenance": provenance,
    }


def _t_sf_two_sided(t_stat: np.ndarray, dof: np.ndarray) -> np.ndarray:
    """Two-sided p-values for a t statistic; SciPy when available."""
    t_stat = np.asarray(t_stat, dtype=float)
    dof = np.asarray(dof, dtype=float)
    try:
        from scipy import stats

        return np.asarray(2.0 * stats.t.sf(np.abs(t_stat), dof), dtype=float)
    except Exception:
        # Normal approximation fallback (documented): erfc-based.
        z = np.abs(t_stat)
        return np.asarray([math.erfc(v / math.sqrt(2.0)) for v in z], dtype=float)


def _pydeseq2_de(
    counts: pd.DataFrame,
    metadata: pd.DataFrame,
    design: str,
    contrast: tuple[str, str, str],
    min_count: int,
    min_samples: Optional[int],
    seed: int,
) -> dict[str, Any]:
    from pydeseq2.dds import DeseqDataSet  # type: ignore
    from pydeseq2.ds import DeseqStats  # type: ignore

    factors = _design_factors(design)
    filtered, n_filtered = filter_low_counts(counts, min_count=min_count, min_samples=min_samples)
    if filtered.empty:
        raise ValueError("all genes were filtered out; lower min_count/min_samples")
    factor_col = contrast[0] if contrast else factors[0]
    treated_level = contrast[1] if contrast and len(contrast) == 3 else None
    control_level = contrast[2] if contrast and len(contrast) == 3 else None
    meta = metadata.copy()
    meta.index = [str(x) for x in meta.index]
    # pydeseq2 expects samples × genes.
    sample_by_gene = filtered.T
    sample_by_gene.index = [str(x) for x in sample_by_gene.index]
    np.random.seed(seed)
    design_factors = factors if len(factors) > 1 else factors[0]
    dds = DeseqDataSet(
        counts=sample_by_gene,
        metadata=meta.loc[sample_by_gene.index],
        design_factors=design_factors,
        refit_cooks=True,
    )
    dds.deseq2()
    if treated_level is None:
        levels = sorted(meta[factor_col].astype(str).unique())
        control_level, treated_level = levels[0], levels[1]
    stats = DeseqStats(
        dds, contrast=[factor_col, str(treated_level), str(control_level)]
    )
    stats.summary()
    res = stats.results_df.copy().reset_index()
    res = res.rename(
        columns={
            res.columns[0]: "gene",
            "baseMean": "baseMean",
            "log2FoldChange": "log2FC",
            "pvalue": "pvalue",
            "padj": "padj",
        }
    )
    for column in ("baseMean", "log2FC", "pvalue", "padj"):
        if column not in res.columns:
            res[column] = np.nan
    res["stat"] = res.get("stat", pd.Series(np.nan, index=res.index))
    normalized = pd.DataFrame(
        dds.layers["normed_counts"].T
        if hasattr(dds, "layers") and "normed_counts" in getattr(dds, "layers", {})
        else filtered.values,
        index=filtered.index.astype(str),
        columns=filtered.columns,
    )
    provenance = stats_provenance(
        analysis="differential_expression",
        inputs={
            "counts_matrix": counts.to_csv().encode("utf-8"),
            "metadata": metadata.to_csv().encode("utf-8"),
        },
        params={
            "method": "pydeseq2",
            "design": design,
            "contrast": [factor_col, treated_level, control_level],
            "min_count": min_count,
            "min_samples": min_samples,
        },
        seed=seed,
        engine="python",
    )
    return {
        "method": "pydeseq2",
        "results": res,
        "normalized_counts": normalized,
        "size_factors": {},
        "dispersion": None,
        "n_genes_input": int(counts.shape[0]),
        "n_genes_filtered": n_filtered,
        "n_genes_tested": int(res.shape[0]),
        "n_genes_significant_fdr05": int((pd.to_numeric(res["padj"], errors="coerce") < 0.05).sum()),
        "contrast": {"factor": factor_col, "treated": treated_level, "control": control_level},
        "warnings": [],
        "provenance": provenance,
    }


def run_differential_expression(
    counts: pd.DataFrame,
    metadata: pd.DataFrame,
    design: str = "~ condition",
    contrast: Optional[tuple[str, str, str]] = None,
    method: str = "auto",
    min_count: int = 10,
    min_samples: Optional[int] = None,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Run differential expression and return the shared result schema.

    ``counts``: genes × samples (or samples × genes — auto-detected) raw counts.
    ``metadata``: sample annotation indexed by sample id (must contain the
    design factors).
    ``contrast``: ``(factor, treated_level, control_level)``.
    ``method``: ``auto`` | ``pydeseq2`` | ``r`` | ``r-deseq2`` | ``r-edger`` |
    ``r-limma`` | ``fallback``.

    Returns dict with keys: ``method``, ``results`` (DataFrame: gene, baseMean,
    log2FC, stat, pvalue, padj), ``normalized_counts``, ``size_factors``,
    ``dispersion``, ``n_genes_*`` counters, ``contrast``, ``warnings``,
    ``provenance``.
    """
    if not isinstance(counts, pd.DataFrame) or not isinstance(metadata, pd.DataFrame):
        raise TypeError("counts and metadata must be pandas DataFrames")
    if metadata.empty:
        raise ValueError("metadata must contain at least one sample")
    method_key = (method or "auto").strip().lower()
    oriented, sample_order = _orient_counts(counts, metadata)
    if oriented.shape[1] != len(sample_order):
        raise ValueError("counts/metadata sample mismatch after orientation")
    numeric = oriented.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    if (numeric.values < 0).any():
        raise ValueError("counts must be non-negative")

    errors: list[str] = []
    if method_key in {"r", "r-deseq2", "r-edger", "r-limma"}:
        from titan_stats.r_bridge import RBridgeError, run_r_de

        r_method = {
            "r": "deseq2",
            "r-deseq2": "deseq2",
            "r-edger": "edger",
            "r-limma": "limma",
        }[method_key]
        try:
            return run_r_de(
                numeric, metadata.loc[sample_order], design, contrast, r_method, min_count, min_samples, seed
            )
        except (RBridgeError, FileNotFoundError) as exc:
            if method_key != "r":
                raise
            errors.append(f"R bridge unavailable: {exc}")

    if method_key in {"auto", "pydeseq2"}:
        try:
            __import__("pydeseq2")  # presence probe only

            return _pydeseq2_de(numeric, metadata.loc[sample_order], design, contrast, min_count, min_samples, seed)
        except ImportError as exc:
            if method_key == "pydeseq2":
                raise RuntimeError(
                    "pydeseq2 is not installed; pip install pydeseq2 or use method='fallback'"
                ) from exc
            errors.append(f"pydeseq2 unavailable: {exc}")
        except Exception as exc:  # pragma: no cover - version drift guard
            if method_key == "pydeseq2":
                raise
            errors.append(f"pydeseq2 failed: {exc}")

    result = _fallback_de(numeric, metadata.loc[sample_order], design, contrast, min_count, min_samples, seed)
    result["warnings"] = errors + result["warnings"]
    return result


def result_records(result: Mapping[str, Any]) -> list[dict[str, Any]]:
    """JSON-safe row dicts for the results table (NaN → None)."""
    frame: pd.DataFrame = result["results"]
    rows = frame.replace({np.nan: None}).to_dict(orient="records")
    return rows
