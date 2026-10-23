"""Safe R bridge — DESeq2 / edgeR / limma-voom through ``Rscript`` + JSON.

* No ``shell=True`` anywhere: ``subprocess.run([...])`` with an argv list only.
* The R program is resolved from this repository (``r/de_runner.R``) and every
  argument is validated against an allow-list before use.
* Data flows as JSON on stdin/stdout — no temp files (ZDR-safe).
* Timeout + output size caps; stderr is never echoed wholesale into logs
  (it can contain user data from R error messages — we only surface a short
  sanitized message).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from titan_stats.provenance import provenance_to_eln_parameters, stats_provenance

__all__ = ["RBridgeError", "r_available", "r_versions", "run_r_de"]

_ALLOWED_METHODS = {"deseq2", "edger", "limma"}
_R_TIMEOUT_SECONDS = int(os.environ.get("TITAN_R_TIMEOUT", "600"))
_MAX_R_STDOUT_BYTES = 256 * 1024 * 1024
_REPO_ROOT = Path(__file__).resolve().parents[1]
_R_RUNNER = _REPO_ROOT / "r" / "de_runner.R"


class RBridgeError(RuntimeError):
    """Raised when the R engine is missing, too old, or fails safely."""


def rscript_path() -> Optional[str]:
    return shutil.which("Rscript")


def r_available() -> bool:
    return rscript_path() is not None and _R_RUNNER.exists()


def r_versions() -> dict[str, str]:
    """Probe R + Bioconductor package versions (best-effort, no user data)."""
    exe = rscript_path()
    if exe is None:
        return {}
    probe = (
        "cat(R.version.string); cat('|'); "
        "for (p in c('DESeq2','edgeR','limma')) {"
        " v <- tryCatch(as.character(packageVersion(p)), error=function(e) 'absent');"
        " cat(p, '=', v, ';', sep='') }"
    )
    try:
        proc = subprocess.run(
            [exe, "--vanilla", "-e", probe],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    out = (proc.stdout or "").strip()
    versions: dict[str, str] = {}
    if out:
        parts = out.split("|", 1)
        versions["R"] = parts[0].strip()
        if len(parts) > 1:
            for item in parts[1].split(";"):
                if "=" in item:
                    name, version = item.split("=", 1)
                    versions[name.strip()] = version.strip()
    return versions


def _matrix_payload(counts: pd.DataFrame, metadata: pd.DataFrame) -> dict[str, Any]:
    genes = [str(g) for g in counts.index]
    samples = [str(s) for s in counts.columns]
    values = counts.values.astype(float).tolist()
    meta_records = []
    for sample in samples:
        row = metadata.loc[sample] if sample in metadata.index else None
        record: dict[str, Any] = {"sample": sample}
        if row is not None:
            for column in metadata.columns:
                value = row[column]
                record[str(column)] = None if pd.isna(value) else (value.item() if hasattr(value, "item") else value)
        meta_records.append(record)
    return {"genes": genes, "samples": samples, "counts": values, "metadata": meta_records}


def run_r_de(
    counts: pd.DataFrame,
    metadata: pd.DataFrame,
    design: str,
    contrast: Optional[tuple[str, str, str]],
    method: str,
    min_count: int,
    min_samples: Optional[int],
    seed: int,
) -> dict[str, Any]:
    """Run one DE method in R and normalize the output to the shared schema."""
    method_key = (method or "deseq2").strip().lower()
    if method_key not in _ALLOWED_METHODS:
        raise RBridgeError(f"method must be one of {sorted(_ALLOWED_METHODS)}")
    exe = rscript_path()
    if exe is None:
        raise RBridgeError("Rscript not found on PATH")
    if not _R_RUNNER.exists():
        raise RBridgeError(f"missing R runner script: {_R_RUNNER}")

    factor_col, treated, control = contrast if contrast else (None, None, None)
    payload = {
        "method": method_key,
        "design": design or "~ condition",
        "factor": factor_col,
        "treated": treated,
        "control": control,
        "min_count": int(min_count),
        "min_samples": None if min_samples is None else int(min_samples),
        "seed": int(seed),
        "matrix": _matrix_payload(counts, metadata),
    }
    input_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    try:
        proc = subprocess.run(
            [exe, "--vanilla", str(_R_RUNNER)],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=_R_TIMEOUT_SECONDS,
            check=False,
            shell=False,
            env={**os.environ, "TITAN_R_JSON_IN": "stdin"},
        )
    except subprocess.TimeoutExpired as exc:
        raise RBridgeError(f"R engine timed out after {_R_TIMEOUT_SECONDS}s") from exc
    except OSError as exc:
        raise RBridgeError(f"failed to launch Rscript: {exc}") from exc

    if len(proc.stdout or "") > _MAX_R_STDOUT_BYTES:
        raise RBridgeError("R engine output exceeded the size cap")
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()
        # Never forward raw stderr (may embed user data); keep only the first
        # R error tag line and a character count.
        summary = tail[0][:200] if tail else "unknown R failure"
        raise RBridgeError(f"R engine failed (exit {proc.returncode}): {summary}")
    try:
        decoded = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RBridgeError("R engine produced invalid JSON") from exc
    if not isinstance(decoded, dict) or decoded.get("ok") is not True:
        raise RBridgeError(f"R engine reported failure: {str(decoded)[:200]}")

    rows = decoded.get("results") or []
    results = pd.DataFrame(rows)
    for column in ("gene", "baseMean", "log2FC", "stat", "pvalue", "padj"):
        if column not in results.columns:
            results[column] = np.nan
    results = results[["gene", "baseMean", "log2FC", "stat", "pvalue", "padj"]]
    normalized_counts = pd.DataFrame(decoded.get("normalized_counts") or {})
    dispersion = decoded.get("dispersion")
    warnings = list(decoded.get("warnings") or [])
    versions = decoded.get("versions") or {}
    provenance = stats_provenance(
        analysis="differential_expression",
        inputs={
            "counts_matrix": counts.to_csv().encode("utf-8"),
            "metadata": metadata.to_csv().encode("utf-8"),
        },
        params={
            "method": f"r-{method_key}",
            "design": design,
            "contrast": list(contrast) if contrast else None,
            "min_count": min_count,
            "min_samples": min_samples,
        },
        seed=seed,
        engine="R",
        r_versions=versions,
    )
    return {
        "method": f"r-{method_key}",
        "results": results,
        "normalized_counts": normalized_counts,
        "size_factors": decoded.get("size_factors") or {},
        "dispersion": dispersion,
        "n_genes_input": int(counts.shape[0]),
        "n_genes_filtered": int(decoded.get("n_genes_filtered") or 0),
        "n_genes_tested": int(results.shape[0]),
        "n_genes_significant_fdr05": int((pd.to_numeric(results["padj"], errors="coerce") < 0.05).sum()),
        "contrast": decoded.get("contrast")
        or {"factor": factor_col, "treated": treated, "control": control},
        "outliers": decoded.get("outliers")
        or {"engine": f"r-{method_key}", "flagged_genes": [], "notes": ["R engine returned no outlier section."]},
        "warnings": warnings,
        "provenance": provenance,
        "eln_parameters": provenance_to_eln_parameters(provenance),
    }
