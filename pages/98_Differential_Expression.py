"""⚡ Pro Engine console — Differential Expression (Layer B).

Runs DE through titan_stats: PyDESeq2 when installed, the R bridge (DESeq2 /
edgeR / limma-voom via Rscript + JSON) when requested and available, else an
honest pure-NumPy fallback (labeled ``fallback-ttest`` — not DESeq2). Every run
carries a provenance record (SHA-256 input hashes, package versions, seed).
"""
from __future__ import annotations

import io
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from titan_stats import plots as titan_plots
from titan_stats.de import result_records, run_differential_expression
from titan_stats.provenance import provenance_to_eln_parameters
from titan_utils import engine
from titan_utils.eln import get_session_log
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title(
    "⚡",
    "Differential Expression",
    "Counts matrix + metadata → log2FC, p-values, FDR · PyDESeq2 / R (DESeq2·edgeR·limma) / honest fallback.",
)
st.markdown(
    "Paste a raw counts matrix (genes × samples, CSV) and a sample metadata table "
    "(CSV with `sample` + design columns). Everything runs in RAM (ZDR)."
)
st.markdown("---")

engine.render_engine_toggle(key="de_engine_toggle")

DEFAULT_COUNTS = """gene,s1,s2,s3,s4
geneA,100,120,400,420
geneB,200,210,50,60
geneC,80,90,85,95
geneD,5,4,300,280
geneE,15,18,14,16
geneF,500,480,510,490
"""
DEFAULT_META = """sample,condition,batch
s1,control,b1
s2,control,b2
s3,treated,b1
s4,treated,b2
"""

c1, c2 = st.columns(2)
with c1:
    counts_text = st.text_area("📊 Counts matrix (CSV, genes × samples)", DEFAULT_COUNTS, height=220)
with c2:
    meta_text = st.text_area("📋 Sample metadata (CSV)", DEFAULT_META, height=220)

o1, o2, o3 = st.columns(3)
with o1:
    method = st.selectbox(
        "Engine / method",
        options=["auto", "fallback", "pydeseq2", "r-deseq2", "r-edger", "r-limma"],
        index=0,
        help="auto → R bridge (if requested via r-*) / PyDESeq2 (if installed) / labeled fallback-ttest.",
    )
with o2:
    min_count = st.number_input("Min count per gene", min_value=0, max_value=10_000, value=10, step=1)
with o3:
    fdr_threshold = st.number_input("FDR threshold", min_value=0.001, max_value=0.5, value=0.05, step=0.01)

run_clicked = st.button("🧬 Run Differential Expression", type="primary", use_container_width=True)
export_volcano = st.button("📈 Export Volcano JSON", use_container_width=True)
log_eln = st.button("📓 Log run to ELN (GLP)", use_container_width=True)


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    counts = pd.read_csv(io.StringIO(counts_text))
    counts = counts.rename(columns={counts.columns[0]: "gene"})
    counts = counts.set_index("gene")
    meta = pd.read_csv(io.StringIO(meta_text))
    first = meta.columns[0]
    meta = meta.rename(columns={first: "sample"})
    meta = meta.set_index("sample")
    return counts, meta


if run_clicked:
    try:
        counts_df, meta_df = _load_inputs()
        with st.spinner("Computing differential expression…"):
            result = run_differential_expression(
                counts_df,
                meta_df,
                design="~ condition",
                contrast=("condition", "treated", "control"),
                method=method,
                min_count=int(min_count),
            )
        st.session_state["de_result"] = {
            "records": result_records(result),
            "normalized": result["normalized_counts"].reset_index().rename(columns={"index": "gene"}).to_dict(orient="list"),
            "method": result["method"],
            "warnings": result["warnings"],
            "contrast": result["contrast"],
            "counts": int(result["n_genes_tested"]),
            "sig": int(result["n_genes_significant_fdr05"]),
            "provenance": result["provenance"],
        }
    except Exception as exc:  # controlled degradation, never a crash
        st.warning(
            f"Requested engine could not run ({type(exc).__name__}: {exc}). "
            "Falling back to the labeled fallback-ttest path."
        )
        try:
            counts_df, meta_df = _load_inputs()
            result = run_differential_expression(
                counts_df,
                meta_df,
                design="~ condition",
                contrast=("condition", "treated", "control"),
                method="fallback",
                min_count=int(min_count),
            )
            st.session_state["de_result"] = {
                "records": result_records(result),
                "normalized": result["normalized_counts"].reset_index().rename(columns={"index": "gene"}).to_dict(orient="list"),
                "method": result["method"],
                "warnings": result["warnings"] + [f"engine fallback triggered: {exc}"],
                "contrast": result["contrast"],
                "counts": int(result["n_genes_tested"]),
                "sig": int(result["n_genes_significant_fdr05"]),
                "provenance": result["provenance"],
            }
        except Exception as exc2:
            st.session_state["de_result"] = None
            st.warning(f"Could not analyze the provided matrices: {exc2}")

state = st.session_state.get("de_result")
if state:
    st.success(
        f"✅ Method **{state['method']}** · {state['counts']} genes tested · "
        f"{state['sig']} significant at FDR < {fdr_threshold}"
    )
    if state["warnings"]:
        with st.expander("⚠️ Engine notes (honesty)", expanded=False):
            for note in state["warnings"]:
                st.caption(f"• {note}")

    results_df = pd.DataFrame(state["records"])
    st.markdown("### 📋 Results (sorted by FDR)")
    st.dataframe(results_df, use_container_width=True, hide_index=True)

    volcano = titan_plots.volcano_json(results_df, fdr_threshold=float(fdr_threshold))
    fig = px.scatter(
        volcano["points"],
        x="x",
        y="y",
        color="significant",
        hover_data=["gene", "padj"],
        labels={"x": volcano["x_label"], "y": volcano["y_label"]},
        title="Volcano plot (fallback renderer)",
    )
    st.plotly_chart(fig, use_container_width=True)

    norm_df = pd.DataFrame(state["normalized"])
    if "gene" in norm_df.columns and norm_df.shape[1] > 2:
        heatmap = titan_plots.top_heatmap_json(
            norm_df.set_index("gene"), results_df, top_n=25
        )
        heat_df = pd.DataFrame(
            [row["values"] for row in heatmap["rows"]],
            index=[row["gene"] for row in heatmap["rows"]],
            columns=heatmap["samples"],
        )
        st.markdown("### 🔥 Top DE genes (z-score heatmap)")
        st.plotly_chart(px.imshow(heat_df, aspect="auto", title="Top DE genes"), use_container_width=True)

    c_exp1, c_exp2 = st.columns(2)
    with c_exp1:
        st.download_button(
            "📊 Download results CSV",
            data=results_df.to_csv(index=False).encode("utf-8"),
            file_name="titan_de_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c_exp2:
        json_payload = {
            "method": state["method"],
            "contrast": state["contrast"],
            "results": state["records"],
            "provenance": state["provenance"],
        }
        st.download_button(
            "🧬 Download JSON + provenance",
            data=json.dumps(json_payload, indent=2, default=str).encode("utf-8"),
            file_name="titan_de_results.json",
            mime="application/json",
            use_container_width=True,
        )

    enrichment = titan_plots.enrichment_lists(results_df, fdr_threshold=float(fdr_threshold))
    with st.expander("🧪 GO/KEGG enrichment input lists", expanded=False):
        st.caption(f"Up-regulated: {len(enrichment['up'])} · Down-regulated: {len(enrichment['down'])} · Ranked: {len(enrichment['ranked_all'])}")
        st.code("\n".join(enrichment["ranked_all"][:50]) or "(none)")

    if export_volcano:
        st.download_button(
            "📥 Download Volcano JSON",
            data=json.dumps(volcano, indent=2).encode("utf-8"),
            file_name="titan_de_volcano.json",
            mime="application/json",
            use_container_width=True,
        )

    if log_eln:
        log = get_session_log()
        prov = state["provenance"]
        inputs = prov.get("inputs") or {}
        first_digest = next(iter(inputs.values()), {}).get("digest", "")
        rec = log.log_run(
            module="Differential Expression (Pro Stats)",
            input_data=first_digest,
            output_data=json.dumps(state["records"][:20], default=str),
            summary=f"method={state['method']} genes_tested={state['counts']} sig={state['sig']}",
            parameters=provenance_to_eln_parameters(prov),
            input_kind="stats_input",
        )
        st.success(f"✅ ELN run **{rec.run_id}** logged (GLP contemporaneous record).")
    smart_lock(
        csv_data=results_df.to_csv(index=False).encode("utf-8") if not results_df.empty else None,
        csv_filename="titan_de_results.csv",
    )
else:
    st.info("👆 Adjust the matrices if you like, then press **Run Differential Expression** — the toy dataset above is pre-loaded.")

dr_titan_tip(
    "Differential expression finds genes whose activity shifts between conditions. "
    "Real RNA-seq counts follow a negative-binomial distribution — DESeq2/edgeR model that "
    "explicitly. The labeled fallback-ttest here is a teaching approximation (Welch t-test on "
    "log-normalized counts), never a substitute for a published DE pipeline on real data."
)
