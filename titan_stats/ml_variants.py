"""Variant pathogenicity classifier (Layer B ML).

Features are derived from VCF records (consequence, allele frequency,
conservation-like scores, CADD-like fields — extracted from INFO when present).
Training data in this module is **SYNTHETIC** (rule-based simulation): the
labels, UI, exports and model card all say ``SYNTHETIC`` explicitly. The model
is educational — never a clinical claim.

Stack: scikit-learn (Logistic Regression + Random Forest) with optional
XGBoost and optional SHAP explanations. If scikit-learn is missing, a pure
NumPy Gaussian-naive-Bayes fallback still trains and predicts so the app never
crashes. Fixed seeds throughout; stratified k-fold CV; ROC/PR curves;
calibration curve; model card dict.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

__all__ = [
    "FEATURE_COLUMNS",
    "SYNTHETIC_LABEL",
    "extract_features",
    "make_synthetic_dataset",
    "train_pathogenicity_model",
    "model_card",
    "explain_with_shap",
]

SYNTHETIC_LABEL = "SYNTHETIC — rule-based simulated variants (educational model, NOT clinical)"
FEATURE_COLUMNS = (
    "af",  # allele frequency (INFO/AF) — log-scaled at model time
    "cadd",  # CADD-like deleteriousness score (INFO/CADD or PHRED-like)
    "sift",  # SIFT-like score in [0, 1]
    "polyphen",  # PolyPhen-like score in [0, 1]
    "conservation",  # conservation-like score in [0, 1]
    "impact",  # ordinal variant impact (0=synonymous … 3=high)
    "is_lof",  # loss-of-function flag (0/1)
    "in_exon",  # exon membership flag (0/1)
)
_DEFAULT_SEED = 20261022


def extract_features(vcf_result: Mapping[str, Any]) -> pd.DataFrame:
    """Derive model features from an ``engine.parse_vcf`` result dict.

    Missing INFO fields become NaN (models handle them via median imputation).
    Never raises on absent columns — partial VCFs still score.
    """
    info_raw = list(vcf_result.get("info_raw") or [])
    af = pd.to_numeric(pd.Series(vcf_result.get("info_af") or [None] * len(info_raw)), errors="coerce")
    rows = []
    for idx, info in enumerate(info_raw):
        fields = {}
        for part in str(info).split(";"):
            if "=" in part:
                key, value = part.split("=", 1)
                fields[key.strip()] = value.split(",")[0].strip()
        def _float(keys: Sequence[str]) -> float:
            for key in keys:
                if key in fields:
                    try:
                        return float(fields[key])
                    except ValueError:
                        return float("nan")
            return float("nan")

        consequence = fields.get("Consequence", fields.get("CSQ", "")).lower()
        impact_rank = 3.0 if "frameshift" in consequence or "stop_gained" in consequence else (
            2.0 if "missense" in consequence else (
                1.0 if "splice" in consequence or "intron" in consequence else (
                    0.0 if "synonymous" in consequence else float("nan")
                )
            )
        )
        rows.append(
            {
                "af": float(af.iloc[idx]) if idx < len(af) else float("nan"),
                "cadd": _float(("CADD", "CADD_PHRED", "cadd_phred")),
                "sift": _float(("SIFT", "SIFT_score")),
                "polyphen": _float(("PolyPhen", "PolyPhen_score", "PP2")),
                "conservation": _float(("Conservation", "phyloP", "GERP", "GERP_RS")),
                "impact": impact_rank,
                "is_lof": 1.0 if "frameshift" in consequence or "stop_gained" in consequence else 0.0,
                "in_exon": 1.0 if "exon" in fields.get("Region", "exon") or "missense" in consequence or "synonymous" in consequence else float("nan"),
            }
        )
    frame = pd.DataFrame(rows, columns=list(FEATURE_COLUMNS))
    frame.insert(0, "variant", [
        f"{chrom}:{pos}:{ref}>{alt}"
        for chrom, pos, ref, alt in zip(
            vcf_result.get("chrom") or [],
            vcf_result.get("pos") or [],
            vcf_result.get("ref") or [],
            vcf_result.get("alt") or [],
        )
    ][: len(frame)])
    return frame


def make_synthetic_dataset(
    n_samples: int = 4000, seed: int = _DEFAULT_SEED
) -> tuple[pd.DataFrame, pd.Series]:
    """Generate a SYNTHETIC labeled variant dataset.

    The generative rules are explicit: pathogenic-like draws get higher CADD /
    conservation, lower AF, more loss-of-function; benign-like draws the
    reverse. Labels are **simulated** and every export repeats that.
    """
    rng = np.random.default_rng(seed)
    n_path = n_samples // 2
    n_benign = n_samples - n_path

    def draw(count: int, pathogenic: bool) -> np.ndarray:
        af = rng.beta(0.3 if pathogenic else 2.0, 8.0 if pathogenic else 2.0, count)
        cadd = rng.normal(28.0 if pathogenic else 6.0, 5.0, count).clip(0, 60)
        sift = rng.beta(2.0 if pathogenic else 8.0, 8.0 if pathogenic else 2.0, count)
        polyphen = rng.beta(8.0 if pathogenic else 2.0, 2.0 if pathogenic else 8.0, count)
        conservation = rng.beta(6.0 if pathogenic else 2.0, 2.0 if pathogenic else 6.0, count)
        impact = rng.choice([0, 1, 2, 3], count, p=[0.05, 0.15, 0.35, 0.45] if pathogenic else [0.45, 0.3, 0.2, 0.05])
        is_lof = rng.binomial(1, 0.35 if pathogenic else 0.02, count)
        in_exon = rng.binomial(1, 0.85 if pathogenic else 0.6, count)
        return np.column_stack([af, cadd, sift, polyphen, conservation, impact, is_lof, in_exon])

    values = np.vstack([draw(n_path, True), draw(n_benign, False)])
    labels = np.concatenate([np.ones(n_path), np.zeros(n_benign)])
    order = rng.permutation(values.shape[0])
    frame = pd.DataFrame(values[order], columns=list(FEATURE_COLUMNS))
    frame.insert(0, "variant", [f"SYNTHETIC:var{i:06d}" for i in range(values.shape[0])])
    series = pd.Series(labels[order].astype(int), name="label")
    return frame, series


def _feature_matrix(frame: pd.DataFrame) -> np.ndarray:
    missing = [c for c in FEATURE_COLUMNS if c not in frame.columns]
    if missing:
        raise ValueError(f"feature frame missing columns: {missing}")
    values = np.array(
        frame.loc[:, list(FEATURE_COLUMNS)].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float),
        dtype=float,
        copy=True,
    )
    # Median imputation for NaNs (fitted on training data at predict time).
    medians = np.nanmedian(values, axis=0)
    medians[~np.isfinite(medians)] = 0.0
    inds = np.where(~np.isfinite(values))
    values[inds] = np.take(medians, inds[1])
    values[:, 0] = np.log10(values[:, 0] + 1e-4)  # AF is log-scaled
    return values


@dataclass
class PathogenicityModel:
    """Trained model + honest metadata. ``backend``: sklearn|xgboost|numpy-gnb."""

    backend: str
    estimator: Any
    feature_names: tuple = FEATURE_COLUMNS
    seed: int = _DEFAULT_SEED
    synthetic_training_data: bool = True
    cv: dict = field(default_factory=dict)
    roc: dict = field(default_factory=dict)
    pr: dict = field(default_factory=dict)
    calibration: dict = field(default_factory=dict)
    classes: tuple = (0, 1)

    def predict_proba(self, features: pd.DataFrame) -> np.ndarray:
        matrix = _feature_matrix(features)
        if self.backend == "numpy-gnb":
            return _gnb_predict_proba(self.estimator, matrix)
        proba = self.estimator.predict_proba(matrix)
        # Column order follows estimator.classes_; align to (benign, pathogenic).
        classes = list(getattr(self.estimator, "classes_", self.classes))
        out = np.zeros((matrix.shape[0], 2), dtype=float)
        for column, cls in enumerate(classes):
            out[:, int(cls)] = proba[:, column]
        return out

    def predict(self, features: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        return (self.predict_proba(features)[:, 1] >= threshold).astype(int)


def _fit_numpy_gnb(x: np.ndarray, y: np.ndarray) -> dict:
    classes = np.unique(y)
    params = {}
    for cls in classes:
        rows = x[y == cls]
        params[int(cls)] = {
            "mean": rows.mean(axis=0),
            "var": rows.var(axis=0) + 1e-9,
            "prior": rows.shape[0] / x.shape[0],
        }
    return params


def _gnb_predict_proba(params: Mapping[int, Mapping[str, Any]], x: np.ndarray) -> np.ndarray:
    log_likelihood = []
    classes = sorted(params)
    for cls in classes:
        p = params[cls]
        var = p["var"]
        mean = p["mean"]
        ll = -0.5 * np.sum(np.log(2 * np.pi * var) + (x - mean) ** 2 / var, axis=1)
        log_likelihood.append(ll + np.log(max(p["prior"], 1e-12)))
    stacked = np.column_stack(log_likelihood)
    stacked -= stacked.max(axis=1, keepdims=True)
    exp = np.exp(stacked)
    return exp / exp.sum(axis=1, keepdims=True)


def _stratified_cv_scores(estimator_factory, x: np.ndarray, y: np.ndarray, folds: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    classes = np.unique(y)
    per_class_indices = {cls: np.where(y == cls)[0] for cls in classes}
    for idx in per_class_indices.values():
        rng.shuffle(idx)
    fold_assignments = np.zeros(len(y), dtype=int)
    for cls, indices in per_class_indices.items():
        for position, idx in enumerate(indices):
            fold_assignments[idx] = position % folds
    aucs, aps = [], []
    try:
        from sklearn.metrics import average_precision_score, roc_auc_score
    except Exception:
        roc_auc_score = average_precision_score = None
    for fold in range(folds):
        test_mask = fold_assignments == fold
        train_mask = ~test_mask
        if test_mask.sum() == 0 or train_mask.sum() == 0:
            continue
        model = estimator_factory()
        if isinstance(model, tuple):
            model, is_numpy = model
        else:
            is_numpy = False
        if is_numpy:
            model = _fit_numpy_gnb(x[train_mask], y[train_mask])
            scores = _gnb_predict_proba(model, x[test_mask])[:, 1]
        else:
            model.fit(x[train_mask], y[train_mask])
            scores = model.predict_proba(x[test_mask])[:, 1]
        if roc_auc_score is not None and len(np.unique(y[test_mask])) == 2:
            aucs.append(float(roc_auc_score(y[test_mask], scores)))
            aps.append(float(average_precision_score(y[test_mask], scores)))
    return {
        "folds": folds,
        "roc_auc_mean": float(np.mean(aucs)) if aucs else None,
        "roc_auc_std": float(np.std(aucs)) if aucs else None,
        "pr_auc_mean": float(np.mean(aps)) if aps else None,
        "pr_auc_std": float(np.std(aps)) if aps else None,
    }


def _curve_points(y_true: np.ndarray, scores: np.ndarray, curve: str) -> dict[str, Any]:
    try:
        from sklearn.metrics import auc, precision_recall_curve, roc_curve
    except Exception:
        return {"available": False, "points": []}
    if curve == "roc":
        fpr, tpr, _ = roc_curve(y_true, scores)
        return {
            "available": True,
            "points": [{"x": float(a), "y": float(b)} for a, b in zip(fpr, tpr)],
            "auc": float(auc(fpr, tpr)),
        }
    precision, recall, _ = precision_recall_curve(y_true, scores)
    return {
        "available": True,
        "points": [{"x": float(a), "y": float(b)} for a, b in zip(recall, precision)],
        "auc": float(auc(recall, precision)),
    }


def train_pathogenicity_model(
    features: Optional[pd.DataFrame] = None,
    labels: Optional[pd.Series] = None,
    model_type: str = "auto",
    n_folds: int = 5,
    seed: int = _DEFAULT_SEED,
    calibrate: bool = True,
) -> PathogenicityModel:
    """Train the classifier. Falls back through xgboost → sklearn → NumPy GNB.

    When ``features``/``labels`` are omitted a SYNTHETIC dataset is generated
    (the model is flagged ``synthetic_training_data=True`` accordingly).
    """
    synthetic = features is None or labels is None
    if synthetic:
        features, labels = make_synthetic_dataset(seed=seed)
    elif "variant" in getattr(features, "columns", []):
        # Honor the SYNTHETIC provenance marker carried by generated frames.
        synthetic = all(str(v).startswith("SYNTHETIC:") for v in features["variant"].head(50))
    x = _feature_matrix(features)
    y = np.asarray(labels, dtype=int)
    if len(np.unique(y)) < 2:
        raise ValueError("training labels must contain both classes")

    backend = "numpy-gnb"
    estimator: Any = None
    model_type_key = (model_type or "auto").strip().lower()

    def try_sklearn(kind: str):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression

        if kind in {"auto", "logreg", "logistic"}:
            return LogisticRegression(max_iter=1000, random_state=seed)
        return RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=1)

    def try_xgboost():
        import xgboost  # type: ignore

        return xgboost.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=seed,
            eval_metric="logloss",
            n_jobs=1,
        )

    if model_type_key in {"auto", "xgboost"}:
        try:
            estimator = try_xgboost()
            backend = "xgboost"
        except Exception:
            estimator = None
    if estimator is None and model_type_key != "numpy-gnb":
        try:
            estimator = try_sklearn(model_type_key)
            backend = "sklearn"
        except Exception:
            estimator = None
    if estimator is None:
        estimator = _fit_numpy_gnb(x, y)
        backend = "numpy-gnb"

    if backend != "numpy-gnb":
        estimator.fit(x, y)

    cv = _stratified_cv_scores(
        (lambda: (estimator.__class__(**estimator.get_params()) if hasattr(estimator, "get_params") else estimator.__class__(), False))
        if backend != "numpy-gnb"
        else (lambda: ({}, True)),
        x,
        y,
        n_folds,
        seed,
    )

    model = PathogenicityModel(
        backend=backend,
        estimator=estimator,
        seed=seed,
        synthetic_training_data=bool(synthetic),
        cv=cv,
    )
    # Score the training matrix directly (x is already feature-transformed;
    # round-tripping through predict_proba would log-scale AF twice).
    if backend == "numpy-gnb":
        scores = _gnb_predict_proba(estimator, x)[:, 1]
    else:
        proba = estimator.predict_proba(x)
        classes = list(getattr(estimator, "classes_", [0, 1]))
        column = classes.index(1) if 1 in classes else proba.shape[1] - 1
        scores = proba[:, column]
    model.roc = _curve_points(y, scores, "roc")
    model.pr = _curve_points(y, scores, "pr")
    if calibrate:
        try:
            from sklearn.calibration import calibration_curve

            fraction_positive, mean_predicted = calibration_curve(y, scores, n_bins=8, strategy="quantile")
            model.calibration = {
                "available": True,
                "points": [
                    {"x": float(a), "y": float(b)} for a, b in zip(mean_predicted, fraction_positive)
                ],
            }
        except Exception:
            model.calibration = {"available": False, "points": []}
    model.classes = (0, 1)
    return model


def model_card(model: PathogenicityModel) -> dict[str, Any]:
    """Model card — includes the SYNTHETIC label wherever training was simulated."""
    return {
        "name": "Titan Variant Pathogenicity Classifier",
        "version": "1.0.0",
        "task": "binary classification of variant pathogenicity (educational)",
        "intended_use": "Teaching ML for genomics. NOT for diagnosis, triage or any clinical decision.",
        "training_data": SYNTHETIC_LABEL if model.synthetic_training_data else "user-supplied labels (verify provenance before use)",
        "synthetic_training_data": bool(model.synthetic_training_data),
        "features": list(model.feature_names),
        "backend": model.backend,
        "seed": model.seed,
        "cross_validation": model.cv,
        "roc_auc": model.roc.get("auc"),
        "pr_auc": model.pr.get("auc"),
        "calibration": model.calibration.get("available", False),
        "limitations": [
            "Synthetic labels encode the generator's assumptions — real pathogenicity is far more complex.",
            "Population-specific allele frequencies and clinical evidence are not modeled.",
            "Output probabilities are not calibrated for clinical prevalence.",
        ],
        "ethical_considerations": [
            "Do not use for reproductive, diagnostic or treatment decisions.",
            "Human variant data must stay under the Titan ZDR policy (in-RAM only).",
        ],
    }


def explain_with_shap(model: PathogenicityModel, features: pd.DataFrame, max_rows: int = 200) -> dict[str, Any]:
    """Optional SHAP explanations — gracefully reports when shap is missing."""
    try:
        import shap  # type: ignore
    except Exception as exc:
        return {"available": False, "reason": f"shap not installed: {exc}"}
    if model.backend == "numpy-gnb":
        return {"available": False, "reason": "SHAP explanations need an sklearn/xgboost backend"}
    try:
        matrix = _feature_matrix(features.head(max_rows))
        explainer = shap.Explainer(model.estimator, feature_names=list(model.feature_names))
        values = explainer(matrix)
        mean_abs = np.abs(np.asarray(values.values)).mean(axis=0)
        return {
            "available": True,
            "n_rows": int(matrix.shape[0]),
            "feature_importance": [
                {"feature": name, "mean_abs_shap": float(score)}
                for name, score in sorted(
                    zip(model.feature_names, mean_abs), key=lambda item: -item[1]
                )
            ],
            "synthetic_training_data": bool(model.synthetic_training_data),
        }
    except Exception as exc:  # pragma: no cover - shap/version drift
        return {"available": False, "reason": f"shap failed: {exc}"}
