"""Pro Engine tool handlers (registry tools 261–265).

Each handler runs through :mod:`titan_utils.engine` (Rust when available,
pure-Python fallback otherwise) and returns a standard :class:`ToolResult`
whose ``extra_data["engine_stats"]`` surfaces engine / timing / threads for
the Advanced Export Center.
"""
from __future__ import annotations

import time
from typing import Any

import pandas as pd
import plotly.express as px

from titan_tools.common import ToolResult, titan_plot_layout
from titan_utils import engine

_DEFAULT_FASTQ = (
    "@read1\nACGTACGTACGTACGTACGT\n+\nIIIIIIIIIIIIIIIIIIII\n"
    "@read2\nGCGCGCGCGCGCGCGCGCGC\n+\n55555555555555555555\n"
    "@read3\nAAATTTCCCGGGAAATTTCC\n+\nIIIIIIIIIIIIIIIIIIII\n"
)

_DEFAULT_VCF = (
    "##fileformat=VCFv4.2\n"
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
    "chr1\t100\trs1\tA\tG\t50\tPASS\tAF=0.25;DP=30\n"
    "chr1\t150\trs2\tC\tT\t45\tPASS\tAF=0.01;DP=25\n"
    "chr2\t50\trs3\tG\tGAT\t60\tLowQual\tAF=0.9;DP=40\n"
)

_DEFAULT_SAM = (
    "@HD\tVN:1.6\n@SQ\tSN:chr1\tLN:1000\n"
    "r1\t0\tchr1\t100\t60\t10M\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII\n"
    "r2\t4\t*\t0\t0\t*\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII\n"
    "r3\t0\tchr1\t500\t30\t10M\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII\n"
)

_DEFAULT_COUNTS = """gene,s1,s2,s3,s4
geneA,100,120,400,420
geneB,200,210,50,60
geneC,80,90,85,95
geneD,5,4,300,280
"""
_DEFAULT_META = """sample,condition
s1,control
s2,control
s3,treated
s4,treated
"""


def _stats(started: float, threads: int = 0) -> dict[str, Any]:
    status = engine.engine_status()
    effective = threads or (
        status.get("rust_threads_default") or 1 if status["active"] == "rust" else 1
    )
    return {
        "engine": engine.active_engine(),
        "engine_version": status.get("rust_version") if status["active"] == "rust" else status.get("python_version"),
        "wall_seconds": round(time.perf_counter() - started, 6),
        "threads": int(effective),
    }


def tool_pro_fast_qc(fastq_data: str = _DEFAULT_FASTQ, k: int = 8) -> ToolResult:
    """Tool 261: streaming FASTQ QC via the Pro Engine (Rust) or fallback."""
    started = time.perf_counter()
    report = engine.qc_fastq(data=fastq_data.encode("utf-8"), k=int(k))
    stats = _stats(started)
    df = pd.DataFrame(report["length_histogram"])
    fig = px.bar(df, x="length", y="count", title="Read length distribution")
    fig.update_layout(**titan_plot_layout("Read Length Distribution", height=280))
    dup = report["duplication"]
    return ToolResult(
        title="Pro Fast QC (streaming)",
        summary=(
            f"{report['n_reads']} reads · {report['total_bases']} bases · "
            f"GC {report['gc_percent']:.1f}% · Q30 {report['q30_percent']:.1f}% "
            f"(engine: {report['engine']})"
        ),
        metrics=[
            ("Reads", str(report["n_reads"]), None),
            ("GC %", f"{report['gc_percent']:.1f}", None),
            ("Q30 %", f"{report['q30_percent']:.1f}", None),
            ("Duplication %", f"{dup['duplication_rate_percent']:.1f}", None),
        ],
        dataframe=df,
        figure=fig,
        notes=[
            "One-pass streaming QC: per-base quality, GC%, N-content, adapters, over-represented k-mers.",
            f"Phred encoding autodetected: {report['phred_encoding']}.",
            f"Duplication method: {dup['method']}.",
        ],
        extra_data={"engine_stats": stats, "qc_report": report},
    )


def tool_pro_fast_vcf(vcf_data: str = _DEFAULT_VCF, chrom: str = "") -> ToolResult:
    """Tool 262: streaming VCF parse with filter pushdown via the Pro Engine."""
    started = time.perf_counter()
    parsed = engine.parse_vcf(
        data=vcf_data.encode("utf-8"),
        chrom=chrom.strip() or None,
        max_rows=10_000,
    )
    stats = _stats(started)
    frame = engine.vcf_result_to_dataframe(parsed)
    fig = px.histogram(frame, x="CHROM", color="FILTER", title="Variants per chromosome")
    fig.update_layout(**titan_plot_layout("VCF Snapshot", height=280))
    return ToolResult(
        title="Pro Fast VCF (streaming + pushdown)",
        summary=(
            f"{parsed['n_rows_kept']} rows kept / {parsed['n_rows_seen']} seen "
            f"({parsed['n_filtered_out']} filtered out · engine: {parsed['engine']})"
        ),
        metrics=[
            ("Rows kept", str(parsed["n_rows_kept"]), None),
            ("Rows seen", str(parsed["n_rows_seen"]), None),
            ("Filtered out", str(parsed["n_filtered_out"]), None),
        ],
        dataframe=frame,
        figure=fig,
        notes=[
            "Filter pushdown (chrom / position / QUAL / AF / FILTER) runs before rows are materialized.",
            "INFO/FORMAT typed decoding; BCF sample columns are summarized via warnings['bcf_format_skipped'].",
        ],
        extra_data={"engine_stats": stats},
    )


def tool_pro_bam_stats(sam_data: str = _DEFAULT_SAM, region: str = "") -> ToolResult:
    """Tool 263: SAM/BAM flagstat + MAPQ + coverage via the Pro Engine."""
    started = time.perf_counter()
    report = engine.read_alignment(data=sam_data.encode("utf-8"), region=region.strip() or None)
    stats = _stats(started)
    flagstat = report["flagstat"]
    frame = pd.DataFrame([flagstat])
    mapq = report["mapq_histogram"]
    mapq_df = pd.DataFrame({"MAPQ": list(range(len(mapq))), "count": mapq})
    mapq_df = mapq_df[mapq_df["count"] > 0]
    fig = px.bar(mapq_df, x="MAPQ", y="count", title="MAPQ distribution")
    fig.update_layout(**titan_plot_layout("MAPQ Distribution", height=280))
    mapped_pct = 100.0 * flagstat["mapped"] / flagstat["total"] if flagstat["total"] else 0.0
    return ToolResult(
        title="Pro BAM/SAM Stats (samtools-flagstat compatible)",
        summary=(
            f"{flagstat['total']} records · {flagstat['mapped']} mapped ({mapped_pct:.1f}%) · "
            f"format {report['format']} (engine: {report['engine']})"
        ),
        metrics=[
            ("Total", str(flagstat["total"]), None),
            ("Mapped", str(flagstat["mapped"]), None),
            ("Duplicates", str(flagstat["duplicates"]), None),
            ("Properly paired", str(flagstat["properly_paired"]), None),
        ],
        dataframe=frame,
        figure=fig,
        notes=[
            "Flag semantics match samtools flagstat (total/primary/secondary/supplementary/duplicates/mapped/paired/read1/read2/singletons).",
            "Coverage depth tracks are binned per reference (1000 bins).",
        ],
        extra_data={"engine_stats": stats},
    )


def tool_pro_differential_expression(
    counts_data: str = _DEFAULT_COUNTS,
    metadata: str = _DEFAULT_META,
    min_count: int = 10,
) -> ToolResult:
    """Tool 264: differential expression (PyDESeq2 / R bridge / labeled fallback)."""
    import io as _io

    from titan_stats.de import run_differential_expression

    started = time.perf_counter()
    counts_df = pd.read_csv(_io.StringIO(counts_data)).rename(columns={"gene": "gene"}).set_index("gene")
    meta_df = pd.read_csv(_io.StringIO(metadata))
    meta_df = meta_df.rename(columns={meta_df.columns[0]: "sample"}).set_index("sample")
    result = run_differential_expression(
        counts_df,
        meta_df,
        design="~ condition",
        contrast=("condition", "treated", "control"),
        method="auto",
        min_count=int(min_count),
    )
    stats = _stats(started)
    frame = result["results"]
    fig = px.scatter(
        frame,
        x="log2FC",
        y=frame["padj"].apply(lambda p: -__import__("math").log10(max(float(p), 1e-300)) if pd.notna(p) else 0.0),
        color=frame["padj"].apply(lambda p: "significant" if pd.notna(p) and p < 0.05 else "n.s."),
        hover_data=["gene"],
        title=f"Volcano — {result['method']}",
    )
    fig.update_layout(**titan_plot_layout("Volcano", height=280))
    return ToolResult(
        title="Pro Differential Expression",
        summary=(
            f"method {result['method']} · {result['n_genes_tested']} genes tested · "
            f"{result['n_genes_significant_fdr05']} at FDR<0.05"
        ),
        metrics=[
            ("Method", result["method"], None),
            ("Genes tested", str(result["n_genes_tested"]), None),
            ("FDR<0.05", str(result["n_genes_significant_fdr05"]), None),
        ],
        dataframe=frame,
        figure=fig,
        notes=result["warnings"] + ["Every run carries a SHA-256 provenance record (see JSON export)."],
        extra_data={"engine_stats": stats, "provenance": result["provenance"]},
    )


def tool_pro_variant_ml(n_synthetic: int = 1000) -> ToolResult:
    """Tool 265: variant pathogenicity classifier on SYNTHETIC training data."""
    from titan_stats.ml_variants import make_synthetic_dataset, model_card, train_pathogenicity_model

    started = time.perf_counter()
    features, labels = make_synthetic_dataset(n_samples=int(n_synthetic))
    model = train_pathogenicity_model(features, labels, model_type="auto")
    card = model_card(model)
    stats = _stats(started)
    frame = pd.DataFrame([card["cross_validation"]])
    fig = px.bar(
        x=list(card["features"]),
        y=[0.0] * len(card["features"]),
        title="Model card feature list (see JSON for SHAP importances)",
    )
    fig.update_layout(**titan_plot_layout("Variant ML", height=280))
    return ToolResult(
        title="Pro Variant ML (SYNTHETIC training data)",
        summary=(
            f"backend {card['backend']} · CV ROC-AUC "
            f"{(card['cross_validation'].get('roc_auc_mean') or 0):.3f} · training data SYNTHETIC"
        ),
        metrics=[
            ("Backend", card["backend"], None),
            ("ROC-AUC", str(card.get("roc_auc")), None),
            ("Training data", "SYNTHETIC", None),
        ],
        dataframe=frame,
        figure=fig,
        notes=[
            "SYNTHETIC TRAINING DATA — rule-based simulation, educational model only.",
            "Not for clinical use. See the downloadable model card for limitations and ethics notes.",
        ],
        extra_data={"engine_stats": stats, "model_card": card},
    )
