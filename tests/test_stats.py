"""Tests for titan_stats (Layer B): DE fallback, plot JSON, ML, dimred,
provenance, and the R bridge's safe failure modes."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from titan_stats import dimred, plots
from titan_stats.de import (
    benjamini_hochberg,
    filter_low_counts,
    normalize_median_of_ratios,
    run_differential_expression,
)
from titan_stats.ml_variants import (
    SYNTHETIC_LABEL,
    extract_features,
    make_synthetic_dataset,
    model_card,
    train_pathogenicity_model,
)
from titan_stats.provenance import provenance_to_eln_parameters, stats_provenance

COUNTS = pd.DataFrame(
    {
        "s1": [100, 200, 80, 5, 15, 500],
        "s2": [120, 210, 90, 4, 18, 480],
        "s3": [400, 50, 85, 300, 14, 510],
        "s4": [420, 60, 95, 280, 16, 490],
    },
    index=["geneA", "geneB", "geneC", "geneD", "geneE", "geneF"],
)
META = pd.DataFrame(
    {"condition": ["control", "control", "treated", "treated"], "batch": ["b1", "b2", "b1", "b2"]},
    index=["s1", "s2", "s3", "s4"],
)


def test_filter_low_counts():
    filtered, removed = filter_low_counts(COUNTS, min_count=10, min_samples=2)
    assert removed == 0  # every gene has >=10 in >=2 samples
    assert filtered.shape == COUNTS.shape
    strict, removed_strict = filter_low_counts(COUNTS, min_count=1000, min_samples=1)
    assert strict.empty or removed_strict > 0


def test_median_of_ratios_normalization():
    normalized, size = normalize_median_of_ratios(COUNTS)
    assert normalized.shape == COUNTS.shape
    assert np.all(np.isfinite(size.values))
    assert np.all(size.values > 0)


def test_benjamini_hochberg_bounds():
    q = benjamini_hochberg([0.001, 0.01, 0.05, 0.5, 1.0])
    assert np.all((q >= 0) & (q <= 1))
    assert np.all(np.diff(q) >= -1e-12)  # monotone in rank order of input sort


def test_fallback_de_direction_and_schema():
    result = run_differential_expression(COUNTS, META, method="fallback")
    assert result["method"] == "fallback-ttest"
    for key in (
        "results",
        "normalized_counts",
        "size_factors",
        "dispersion",
        "n_genes_input",
        "n_genes_filtered",
        "n_genes_tested",
        "n_genes_significant_fdr05",
        "contrast",
        "warnings",
        "provenance",
    ):
        assert key in result
    frame = result["results"].set_index("gene")
    assert frame.loc["geneA", "log2FC"] > 1  # up in treated
    assert frame.loc["geneB", "log2FC"] < -1  # down in treated
    assert {"baseMean", "log2FC", "stat", "pvalue", "padj"} <= set(frame.columns)
    prov = result["provenance"]
    assert prov["inputs"]["counts_matrix"]["digest"]
    assert prov["seed"] == 1337
    flat = provenance_to_eln_parameters(prov)
    assert "input:counts_matrix:sha256" in flat


def test_de_orientation_samples_as_rows():
    transposed = COUNTS.T
    result = run_differential_expression(transposed, META, method="fallback")
    assert result["n_genes_tested"] == 6


def test_de_rejects_mismatched_samples():
    bad_meta = META.copy()
    bad_meta.index = ["a", "b", "c", "d"]
    with pytest.raises(ValueError):
        run_differential_expression(COUNTS, bad_meta, method="fallback")


def test_r_bridge_absent_is_a_clean_error():
    from titan_stats.r_bridge import RBridgeError, r_available, run_r_de

    if r_available():
        pytest.skip("Rscript present in this environment — absence path not applicable")
    with pytest.raises(RBridgeError):
        run_r_de(COUNTS, META, "~ condition", ("condition", "treated", "control"), "deseq2", 10, None, 1337)


def test_volcano_and_ma_json_serializable():
    result = run_differential_expression(COUNTS, META, method="fallback")
    volcano = plots.volcano_json(result["results"], fdr_threshold=0.05)
    ma = plots.ma_json(result["results"])
    assert volcano["type"] == "volcano"
    assert len(volcano["points"]) == 6
    json.dumps(volcano)
    json.dumps(ma)


def test_pca_sample_distance_heatmap_enrichment():
    normalized = pd.DataFrame(
        np.abs(COUNTS.values) + 1.0, index=COUNTS.index, columns=COUNTS.columns
    )
    pca = plots.pca_json(normalized, META)
    assert len(pca["samples"]) == 4
    assert abs(sum(pca["explained_variance_ratio"]) - 1.0) < 0.5
    distance = plots.sample_distance_json(normalized)
    assert distance["matrix"][0][0] == 0.0
    heat = plots.top_heatmap_json(normalized, pd.DataFrame({"gene": list(normalized.index), "padj": [0.001] * 6}), top_n=3)
    assert len(heat["rows"]) == 3
    result = run_differential_expression(COUNTS, META, method="fallback")
    enrichment = plots.enrichment_lists(result["results"], fdr_threshold=1.0, lfc_threshold=0.0)
    assert set(enrichment) == {"up", "down", "ranked_all"}
    json.dumps({"pca": pca, "distance": distance, "heat": heat, "enrichment": enrichment}, default=str)


def test_synthetic_dataset_is_labelled():
    features, labels = make_synthetic_dataset(n_samples=400, seed=1)
    assert features.shape[0] == 400
    assert set(np.unique(labels)) == {0, 1}
    assert all(str(name).startswith("SYNTHETIC:") for name in features["variant"][:5])
    assert "SYNTHETIC" in SYNTHETIC_LABEL


def test_variant_ml_training_and_card():
    features, labels = make_synthetic_dataset(n_samples=600, seed=7)
    model = train_pathogenicity_model(features, labels, model_type="logreg", n_folds=3, seed=7)
    card = model_card(model)
    assert card["synthetic_training_data"] is True
    assert "SYNTHETIC" in card["training_data"]
    assert card["backend"] in {"sklearn", "xgboost", "numpy-gnb"}
    assert card["cross_validation"]["folds"] == 3
    proba = model.predict_proba(features.head(10))
    assert proba.shape == (10, 2)
    assert np.all((proba >= 0) & (proba <= 1))
    json.dumps(card, default=str)


def test_variant_ml_numpy_fallback():
    features, labels = make_synthetic_dataset(n_samples=300, seed=3)
    model = train_pathogenicity_model(features, labels, model_type="numpy-gnb", n_folds=3, seed=3)
    assert model.backend == "numpy-gnb"
    predictions = model.predict(features.head(20))
    assert predictions.shape == (20,)


def test_extract_features_from_vcf_result():
    vcf_result = {
        "chrom": ["chr1", "chr1"],
        "pos": [100, 200],
        "ref": ["A", "C"],
        "alt": ["G", "T"],
        "info_raw": [
            "AF=0.001;CADD=30;SIFT=0.05;PolyPhen=0.9;Conservation=0.9;Consequence=frameshift_variant",
            "AF=0.4;Consequence=synonymous_variant",
        ],
        "info_af": [0.001, 0.4],
    }
    features = extract_features(vcf_result)
    assert features.shape[0] == 2
    assert features.loc[0, "is_lof"] == 1.0
    assert features.loc[0, "impact"] == 3.0


def test_dimred_pca_kmeans_hierarchical():
    matrix = pd.DataFrame(
        np.abs(np.random.default_rng(0).normal(50, 5, size=(10, 6))) + 1.0,
        index=[f"g{i}" for i in range(10)],
        columns=[f"s{i}" for i in range(6)],
    )
    pca = dimred.pca(matrix, n_components=2, transpose=True)
    assert len(pca["points"]) == 6
    kmeans = dimred.kmeans_cluster(matrix, n_clusters=2, transpose=True)
    assert {g["cluster"] for g in kmeans["groups"]} <= {0, 1}
    hierarchical = dimred.hierarchical_cluster(matrix, n_clusters=2, transpose=True)
    assert len(hierarchical["order"]) == 6
    gene_kmeans = dimred.kmeans_cluster(matrix, n_clusters=2, transpose=False)
    metrics = dimred.cluster_metrics(matrix, [g["cluster"] for g in gene_kmeans["groups"]])
    assert metrics["n_points"] == 10
    json.dumps({"pca": pca, "kmeans": kmeans, "h": hierarchical, "m": metrics}, default=str)


def test_umap_fallback_is_labelled():
    matrix = pd.DataFrame(np.abs(np.random.default_rng(1).normal(20, 2, size=(8, 5))) + 1.0)
    result = dimred.umap_embed(matrix, n_components=2, transpose=True)
    assert result["type"] == "umap"
    assert "method" in result
    json.dumps(result, default=str)


def test_stats_provenance_shape():
    prov = stats_provenance(
        analysis="unit-test",
        inputs={"counts": b"1,2;3,4"},
        params={"alpha": 0.05},
        seed=42,
        engine="python",
    )
    assert prov["inputs"]["counts"]["digest"]
    assert prov["params"]["alpha"] == 0.05
    assert prov["seed"] == 42
    assert prov["zero_data_retention"] is True
    assert prov["python"]
    assert "numpy" in prov["package_versions"]
    json.dumps(prov, default=str)


def test_de_results_include_outlier_flags():
    result = run_differential_expression(COUNTS, META, method="fallback")
    assert "outliers" in result
    outliers = result["outliers"]
    assert outliers["engine"] == "robust-MAD"
    assert isinstance(outliers["flagged_genes"], dict)
    assert outliers["notes"]
    assert "outlier_samples" in result["results"].columns


def test_go_kegg_json_shape():
    result = run_differential_expression(COUNTS, META, method="fallback")
    payload = plots.go_kegg_json(result["results"], fdr_threshold=1.0, lfc_threshold=0.0)
    assert payload["type"] == "go_kegg"
    assert set(payload["go_kegg"]) == {"up_candidates", "down_candidates", "ranked_all"}
    assert payload["counts"]["up"] + payload["counts"]["down"] >= 1
    json.dumps(payload, default=str)


def test_mad_outlier_detection_flags_injected_outlier():
    from titan_stats.de import _mad_outlier_flags

    frame = pd.DataFrame(
        [[10.0, 10.2, 10.1, 100.0]] * 30,  # 4th sample is a huge outlier
        columns=["s1", "s2", "s3", "s4"],
        index=[f"g{i}" for i in range(30)],
    )
    flags = _mad_outlier_flags(frame)
    assert flags["engine"] == "robust-MAD"
    flagged_count = sum(1 for hits in flags["flagged_genes"].values() if hits == ["s4"])
    assert flagged_count == 30
