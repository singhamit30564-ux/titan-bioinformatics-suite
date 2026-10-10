"""Titan compute layer — pure, unit-testable biology used by pages, the Hub
registry handlers, and the FastAPI. No Streamlit imports live here.

Every function returns a plain dict with the shape::

    {
      "title":   str,          # short result title
      "summary": str,          # 1-3 sentence, input-specific finding
      "metrics": [(label, value, help_or_None), ...],
      "rows":    [dict, ...],  # tabular payload (DataFrame-ready)
      "columns": [str, ...]    # optional stable column order
      "fig":     {"kind": ...} # optional declarative figure spec (built by UI)
      "fasta":   str | None,   # optional FASTA text export
      "notes":   [str, ...],   # method notes / caveats (honesty layer)
    }

Honesty contract (enforced by tests): functions must derive their numbers
from the provided inputs; where a model is a documented simplification, the
"notes" list must say so.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple


class ComputeError(ValueError):
    """User-facing computation error with a clear remediation message."""


MAX_SEQ_LEN = 200_000          # linear-time tools accept up to a small bacterial genome
MAX_ALIGN_LEN = 3_000          # DP quadratic tools
MAX_PAIRWISE_LEN = 5_000       # Biopython C-aligner tools
MAX_LEV_LEN = 1_500            # pure-python DP tools
MAX_MSALN_RECORDS = 40
MAX_Fasta_TEXT = 2_000_000


def guard_len(seq: str, limit: int = MAX_SEQ_LEN, name: str = "sequence") -> None:
    if len(seq) > limit:
        raise ComputeError(
            f"{name} of {len(seq):,} characters exceeds the {limit:,} limit for this "
            "tool. Split the input or use the batch processor for large archives."
        )


def out(
    title: str,
    summary: str,
    metrics: Sequence[Tuple[str, str, Optional[str]]] = (),
    rows: Optional[List[Dict[str, Any]]] = None,
    *,
    columns: Optional[List[str]] = None,
    fig: Optional[Dict[str, Any]] = None,
    fasta: Optional[str] = None,
    notes: Sequence[str] = (),
    text: Optional[str] = None,
    newick: Optional[str] = None,
) -> Dict[str, Any]:
    """Canonical result-builder so every tool returns the same shape."""
    res = {
        "title": title,
        "summary": summary,
        "metrics": list(metrics),
        "rows": rows or [],
        "columns": columns or (list(rows[0].keys()) if rows else []),
        "fig": fig,
        "fasta": fasta,
        "notes": list(notes),
    }
    if text:
        res["text"] = text
    if newick:
        res["newick"] = newick
    return res


def free_end_gaps(aligner) -> None:
    """Score terminal gaps 0 (for overlap-style alignment).

    Uses the unified ``end_gap_score`` setter; falls back to the pre-1.84
    per-query/target attributes. Never *read* these properties: their getter
    raises when insertion/deletion scores differ.
    """
    try:
        aligner.end_gap_score = 0.0
    except AttributeError:  # pragma: no cover - biopython < 1.84
        aligner.target_end_gap_score = 0.0
        aligner.query_end_gap_score = 0.0


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:,.4g}".rstrip("0").rstrip(".") if abs(v) < 1e6 else f"{v:,.1f}"
    return str(v)


def prepare_dna(text: str, *, allow_iupac: bool = False, strip_fasta: bool = True) -> str:
    """Clean a DNA/RNA input; reject FASTA headers or keep just the sequence.

    Raises ComputeError with an actionable message (never silently repairs).
    """
    s = text or ""
    if strip_fasta:
        lines = s.replace("\r", "\n").split("\n")
        if any(l.strip().startswith(">") for l in lines):
            s = "".join(l for l in lines if not l.strip().startswith((">", ";")))
    s = "".join(s.upper().split()).replace("-", "").replace(".", "")
    if not s:
        raise ComputeError("Input is empty after cleaning — paste a raw sequence.")
    allowed = set("ATCGURYSWKMBDHVN") if allow_iupac else set("ATCGU")
    bad = sorted({c for c in s if c not in allowed})
    if bad:
        raise ComputeError(
            f"Unexpected character(s) {bad}. Expected DNA letters A,T,G,C"
            + (" or RNA U." if not allow_iupac else ", U, or IUPAC codes.")
        )
    return s.replace("U", "T")  # callers work in DNA space


def prepare_protein(text: str, *, allow_stop: bool = True) -> str:
    s = text or ""
    if any(l.strip().startswith(">") for l in s.splitlines()):
        s = "".join(l for l in s.splitlines() if not l.strip().startswith((">", ";")))
    s = "".join(s.upper().split()).replace("-", "").replace(".", "").replace("*", "X" if not allow_stop else "*")
    if not s:
        raise ComputeError("Protein input is empty.")
    allowed = set("ACDEFGHIKLMNPQRSTVWYX*")
    bad = sorted({c for c in s if c not in allowed})
    if bad:
        raise ComputeError(f"Invalid amino-acid code(s) {bad} — use one-letter IUPAC protein codes.")
    return s


from .basic import BASIC_TOOLS  # noqa: E402
from .genomics import GENOMICS_TOOLS  # noqa: E402
from .align import ALIGN_TOOLS  # noqa: E402
from .lab import LAB_TOOLS  # noqa: E402

#: tool id -> compute function (ids 1..52; the Hub legacy range)
COMPUTE_BY_ID = {**BASIC_TOOLS, **GENOMICS_TOOLS, **ALIGN_TOOLS, **LAB_TOOLS}

__all__ = [
    "ComputeError",
    "COMPUTE_BY_ID",
    "MAX_SEQ_LEN",
    "MAX_ALIGN_LEN",
    "out",
    "prepare_dna",
    "prepare_protein",
    "guard_len",
]
