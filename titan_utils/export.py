"""Multi-format export center — CSV, TSV, JSON, FASTA, FASTQ byte encoders.

Every exporter returns **in-memory bytes** suitable for ``st.download_button``.
Per the Zero Data Retention policy, these helpers never touch the filesystem:
payloads are encoded straight from RAM into the browser download stream.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple, Union

import pandas as pd

__all__ = [
    "EXPORT_FORMATS",
    "to_csv_bytes",
    "to_tsv_bytes",
    "to_json_bytes",
    "to_fasta_bytes",
    "to_fastq_bytes",
    "records_to_fasta",
    "records_to_fastq",
    "build_export",
    "export_mime",
    "export_filename",
    "EXPORT_CENTER_STEPS",
]

EXPORT_FORMATS: Tuple[str, ...] = ("csv", "tsv", "json", "fasta", "fastq")

# Human-readable recipe shown in the Export Center UI.
EXPORT_CENTER_STEPS: Tuple[str, ...] = (
    "1 · CSV — spreadsheet-ready table (Excel, Sheets, pandas).",
    "2 · TSV — tab-delimited table for R, awk, and genome browsers.",
    "3 · JSON — structured records with full key/value provenance.",
    "4 · FASTA — nucleotide/amino-acid sequences, 70-col wrapped.",
    "5 · FASTQ — sequences + Phred quality lines (Q40 placeholder).",
)

Records = Union[pd.DataFrame, Mapping[str, str], Sequence[Mapping[str, Any]], Sequence[Tuple[str, str]]]


# ─────────────────────────────────────────────────────────────────────────────
# Tabular
# ─────────────────────────────────────────────────────────────────────────────

def _as_dataframe(payload: Any) -> pd.DataFrame:
    if isinstance(payload, pd.DataFrame):
        return payload
    if isinstance(payload, Mapping):
        return pd.DataFrame([dict(payload)])
    if isinstance(payload, Sequence):
        return pd.DataFrame(list(payload))
    raise TypeError(f"Cannot tabularise payload of type {type(payload)!r}")


def to_csv_bytes(payload: Any) -> bytes:
    """Encode a DataFrame / record list as UTF-8 CSV bytes."""
    return _as_dataframe(payload).to_csv(index=False).encode("utf-8")


def to_tsv_bytes(payload: Any) -> bytes:
    """Encode a DataFrame / record list as UTF-8 TSV (tab-delimited) bytes."""
    return _as_dataframe(payload).to_csv(index=False, sep="\t").encode("utf-8")


def to_json_bytes(payload: Any, indent: int = 2) -> bytes:
    """Encode a DataFrame / record list / dict as pretty-printed JSON bytes."""
    if isinstance(payload, pd.DataFrame):
        text = payload.to_json(orient="records", indent=indent)
        return text.encode("utf-8")
    return json.dumps(payload, indent=indent, default=str).encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Sequence formats
# ─────────────────────────────────────────────────────────────────────────────

def _iter_records(records: Records) -> List[Tuple[str, str]]:
    """Normalise every supported record container to ``[(header, seq), …]``."""
    out: List[Tuple[str, str]] = []
    if isinstance(records, Mapping):
        out.extend((str(h), str(s)) for h, s in records.items())
    elif isinstance(records, pd.DataFrame):
        cols = {c.lower(): c for c in records.columns}
        hcol = cols.get("header") or cols.get("name") or cols.get("id") or records.columns[0]
        scol = cols.get("sequence") or cols.get("seq") or (
            records.columns[1] if len(records.columns) > 1 else records.columns[0]
        )
        out.extend((str(row[hcol]), str(row[scol])) for _, row in records.iterrows())
    else:
        for item in records:
            if isinstance(item, Mapping):
                header = item.get("header", item.get("name", item.get("id", "record")))
                seq = item.get("sequence", item.get("seq", ""))
                out.append((str(header), str(seq)))
            elif isinstance(item, (tuple, list)) and len(item) >= 2:
                out.append((str(item[0]), str(item[1])))
            else:
                out.append((f"seq_{len(out) + 1}", str(item)))
    return out


def _wrap(seq: str, width: int = 70) -> Iterable[str]:
    for i in range(0, max(len(seq), 1), width):
        yield seq[i:i + width]


def records_to_fasta(records: Records, width: int = 70) -> str:
    """Render records as a FASTA string (70-column wrapped)."""
    lines: List[str] = []
    for header, seq in _iter_records(records):
        h = header[1:] if header.startswith(">") else header
        lines.append(f">{h}")
        lines.extend(_wrap(seq, width))
    return "\n".join(lines) + "\n"


def records_to_fastq(records: Records, quality_char: str = "I", width: int = 0) -> str:
    """Render records as FASTQ. Quality defaults to ``I`` (Phred Q40).

    ``width`` wraps sequence + quality lines (0 = single-line, the common
    modern convention).
    """
    q = quality_char if quality_char else "I"
    lines: List[str] = []
    for header, seq in _iter_records(records):
        h = header[1:] if header.startswith(">") else header
        h = h.split()[0] if h.split() else h
        qual = q * len(seq)
        if width and width > 0:
            seq_chunks = list(_wrap(seq, width))
            qual_chunks = list(_wrap(qual, width))
        else:
            seq_chunks, qual_chunks = [seq], [qual]
        lines.append(f"@{h}")
        lines.extend(seq_chunks)
        lines.append("+")
        lines.extend(qual_chunks)
    return "\n".join(lines) + "\n"


def to_fasta_bytes(records: Records, width: int = 70) -> bytes:
    """Encode records as UTF-8 FASTA bytes."""
    return records_to_fasta(records, width=width).encode("utf-8")


def to_fastq_bytes(records: Records, quality_char: str = "I", width: int = 0) -> bytes:
    """Encode records as UTF-8 FASTQ bytes."""
    return records_to_fastq(records, quality_char=quality_char, width=width).encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────────────────────────────────────

_MIME = {
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
    "json": "application/json",
    "fasta": "text/plain",
    "fastq": "text/plain",
}


def export_mime(fmt: str) -> str:
    """MIME type for an export format slug."""
    return _MIME.get(fmt.lower(), "application/octet-stream")


def export_filename(stem: str, fmt: str) -> str:
    """Build ``<stem>.<ext>`` with filesystem-safe stem characters."""
    safe = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in stem.strip()) or "titan_export"
    ext = {"fasta": "fasta", "fastq": "fastq"}.get(fmt.lower(), fmt.lower())
    return f"{safe}.{ext}"


def build_export(fmt: str, payload: Any) -> bytes:
    """Encode ``payload`` in the requested format. One entry point for the UI.

    * csv / tsv / json accept DataFrames, record lists or dicts.
    * fasta / fastq accept DataFrames, ``{header: seq}`` dicts, or record lists.
    """
    fmt = (fmt or "").lower()
    if fmt == "csv":
        return to_csv_bytes(payload)
    if fmt == "tsv":
        return to_tsv_bytes(payload)
    if fmt == "json":
        return to_json_bytes(payload)
    if fmt == "fasta":
        return to_fasta_bytes(payload)
    if fmt == "fastq":
        return to_fastq_bytes(payload)
    raise ValueError(f"Unsupported export format: {fmt!r} (choose from {EXPORT_FORMATS})")


# Small helper used by io.py-level UI wiring without importing Streamlit here.
def encode_all(payload: Any, records: Records | None = None) -> Dict[str, bytes]:
    """Return every export format for a payload in one pass."""
    bundle = {
        "csv": to_csv_bytes(payload),
        "tsv": to_tsv_bytes(payload),
        "json": to_json_bytes(payload),
    }
    if records is not None:
        bundle["fasta"] = to_fasta_bytes(records)
        bundle["fastq"] = to_fastq_bytes(records)
    return bundle
