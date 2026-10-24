"""⚡ Pro Engine console — Variant ML (pathogenicity classifier).

Trains and applies the Titan variant pathogenicity classifier. Training data
generated in-app is **SYNTHETIC** (rule-based simulation) and is labeled as
such in the UI, exports and model card. Educational model — never clinical.
"""
from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from titan_stats.ml_variants import (
    explain_with_shap,
    extract_features,
    make_synthetic_dataset,
    model_card,
    train_pathogenicity_model,
)
from titan_utils import engine
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title(
    "⚡",
    "Variant ML — Pathogenicity Classifier",
    "scikit-learn / XGBoost (optional SHAP) · stratified CV · ROC/PR · calibration · model card.",
)
st.markdown(
    "Train an educational pathogenicity classifier on SYNTHETIC variants, then score "
    "variants from a VCF INFO block (consequence, AF, CADD-like, SIFT/PolyPhen-like fields)."
)
st.markdown("---")

engine.render_engine_toggle(key="vml_engine_toggle")

st.warning(
    "SYNTHETIC TRAINING DATA — labels come from a rule-based simulator. "
    "This model teaches ML-for-genomics; it is NOT a clinical predictor."
)

DEFAULT_VCF = """##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t100\trs1\tA\tG\t50\tPASS\tAF=0.0001;CADD=32;SIFT=0.01;PolyPhen=0.99;Conservation=0.95;Consequence=frameshift_variant
chr1\t200\trs2\tC\tT\t45\tPASS\tAF=0.4;CADD=1.2;SIFT=0.8;PolyPhen=0.05;Conservation=0.1;Consequence=synonymous_variant
chr2\t50\trs3\tG\tA\t60\tPASS\tAF=0.02;CADD=24;SIFT=0.1;PolyPhen=0.7;Conservation=0.6;Consequence=missense_variant
chr2\t150\trs4\tT\tC\t30\tPASS\tAF=0.25;CADD=8;SIFT=0.5;PolyPhen=0.3;Conservation=0.3;Consequence=missense_variant
"""

c1, c2, c3 = st.columns(3)
with c1:
    n_synthetic = st.number_input("SYNTHETIC training rows", min_value=200, max_value=20_000, value=2000, step=200)
with c2:
    model_type = st.selectbox("Model backend", options=["auto", "logreg", "random_forest", "xgboost", "numpy-gnb"], index=0)
with c3:
    threshold = st.number_input("Pathogenic probability threshold", min_value=0.05, max_value=0.95, value=0.5, step=0.05)

vcf_text = st.text_area("🧬 VCF content to score (INFO fields: AF, CADD, SIFT, PolyPhen, Conservation, Consequence)", DEFAULT_VCF, height=180)

train_clicked = st.button("🧪 Train on SYNTHETIC dataset", type="primary", use_container_width=True)
score_clicked = st.button("🎯 Score VCF variants", use_container_width=True)
explain_clicked = st.button("🔍 SHAP explanations (optional)", use_container_width=True)


def _parse_vcf_text(text: str) -> dict:
    return engine.parse_vcf(data=text.encode("utf-8"), max_rows=5000)


def _score_frame(features: pd.DataFrame, result_state: dict) -> pd.DataFrame:
    model = result_state["model"]
    proba = model.predict_proba(features)[:, 1]
    out = features.copy()
    out["pathogenic_probability"] = proba
    out["prediction"] = ["pathogenic-like" if p >= float(threshold) else "benign-like" for p in proba]
    return out

if "vml_model" not in st.session_state:
    st.session_state["vml_model"] = None

if train_clicked:
    try:
        with st.spinner("Training classifier…"):
            features, labels = make_synthetic_dataset(n_samples=int(n_synthetic))
            model = train_pathogenicity_model(features, labels, model_type=model_type)
        card = model_card(model)
        st.session_state["vml_model"] = {
            "model": model,
            "card": card,
            "n_rows": int(n_synthetic),
        }
    except Exception as exc:
        st.warning(f"Training failed ({exc}); falling back to the NumPy Gaussian-naive-Bayes backend.")
        features, labels = make_synthetic_dataset(n_samples=int(n_synthetic))
        model = train_pathogenicity_model(features, labels, model_type="numpy-gnb")
        st.session_state["vml_model"] = {"model": model, "card": model_card(model), "n_rows": int(n_synthetic)}

state = st.session_state.get("vml_model")
if state:
    card = state["card"]
    st.success(
        f"✅ Model trained on **{state['n_rows']} SYNTHETIC variants** · backend **{card['backend']}** · "
        f"ROC-AUC {card.get('roc_auc')} · PR-AUC {card.get('pr_auc')}"
    )
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Backend", card["backend"])
    with m2:
        st.metric("CV ROC-AUC (mean ± std)", f"{(card['cross_validation'].get('roc_auc_mean') or 0):.3f} ± {(card['cross_validation'].get('roc_auc_std') or 0):.3f}")
    with m3:
        st.metric("Training data", "SYNTHETIC" if card["synthetic_training_data"] else "user")

    if state["model"].roc.get("available"):
        roc_df = pd.DataFrame(state["model"].roc["points"])
        st.plotly_chart(
            px.line(roc_df, x="x", y="y", title=f"ROC curve (AUC={state['model'].roc.get('auc', 0):.3f})"),
            use_container_width=True,
        )

    with st.expander("📇 Model card (downloadable, honest)", expanded=False):
        st.json(card)
        st.download_button(
            "📥 Download model card JSON",
            data=json.dumps(card, indent=2).encode("utf-8"),
            file_name="titan_variant_model_card.json",
            mime="application/json",
            use_container_width=True,
        )

    if score_clicked:
        try:
            parsed = _parse_vcf_text(vcf_text)
            features = extract_features(parsed)
            if features.empty:
                st.warning("No variants found in the pasted VCF.")
            else:
                scored = _score_frame(features, state)
                st.session_state["vml_scored"] = scored
        except Exception as exc:
            st.warning(f"Scoring failed: {exc}")

    scored = st.session_state.get("vml_scored")
    if scored is not None:
        st.markdown("### 🎯 Scored variants")
        st.dataframe(scored, use_container_width=True, hide_index=True)
        st.plotly_chart(
            px.scatter(
                scored,
                x=scored.columns[1],
                y="pathogenic_probability",
                color="prediction",
                hover_data=[scored.columns[0]],
                title="Pathogenic probability per variant",
            ),
            use_container_width=True,
        )
        st.download_button(
            "📊 Download scored variants CSV",
            data=scored.to_csv(index=False).encode("utf-8"),
            file_name="titan_variant_scores.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if explain_clicked:
        try:
            parsed = _parse_vcf_text(vcf_text)
            features = extract_features(parsed)
            explanation = explain_with_shap(state["model"], features)
            if explanation.get("available"):
                shap_df = pd.DataFrame(explanation["feature_importance"])
                st.plotly_chart(
                    px.bar(shap_df, x="feature", y="mean_abs_shap", title="Mean |SHAP| per feature"),
                    use_container_width=True,
                )
            else:
                st.info(f"SHAP explanations unavailable: {explanation.get('reason')}")
        except Exception as exc:
            st.info(f"SHAP explanations unavailable: {exc}")
    smart_lock(
        csv_data=json.dumps(state["card"], indent=2).encode("utf-8"),
        csv_filename="titan_variant_model_card.json",
    )
else:
    st.info("👆 Press **Train on SYNTHETIC dataset** to build the educational classifier.")

dr_titan_tip(
    "Pathogenicity prediction blends allele frequency, conservation and functional impact. "
    "Clinical labs use ACMG/AMP evidence frameworks — a machine-learning score alone never "
    "establishes pathogenicity. This page trains on SYNTHETIC labels so you can explore the "
    "mechanics safely."
)
