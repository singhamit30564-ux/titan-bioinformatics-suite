"""High-throughput multi-FASTA batch processor & consolidated ZIP archive.

Parses multi-FASTA payloads in RAM, runs the same battery of analyses across
every record, and packages everything into one downloadable archive:

* ``batch_results.csv`` / ``batch_results.tsv`` — per-record metrics table
* ``batch_summary.json``  — aggregate statistics
* ``records.fasta``       — normalised copy of the processed records
* ``manifest.json``       — SHA-256 provenance (input + every file)

Zero Data Retention: sequences live only in ephemeral buffers during
processing and are never written to disk by the engine itself.
"""
from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Sequence, Tuple

import pandas as pd

from titan_utils.export import to_csv_bytes, to_fasta_bytes, to_tsv_bytes
from titan_utils.privacy import provenance_manifest, provenance_record, sha256_of_text
from titan_utils.sequence import (
    clean_sequence,
    gc_content_percent,
    nucleotide_counts,
)

__all__ = [
    "FastaRecord",
    "BatchResult",
    "parse_multi_fasta",
    "BATCH_ANALYSES",
    "run_batch",
    "build_batch_zip",
    "DEFAULT_BATCH_FASTA",
]

DEFAULT_BATCH_FASTA = """>sample_1 drought_tolerant_line
ATGCGATCGATCGGCTAATGCGATCGATCGGCTAATGCGATCGATCGGCTAATGCGGCTAAT
>sample_2 susceptible_line
GCGGCTAATGCGATCGATCGGCTAATGCGATCGATCGGCTAATGCGATCGATCGGCTAATGC
>sample_3 hybrid_F1
ATATCGCGATATCGCGATATCGCGATATCGCGATATCGCGATATCGCGATATCGCGATATCGCG
>sample_4 wild_type
GGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAA
>sample_5 mutant_line
ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAGATGGCCATTGTAATGGGCCGCTGA
"""


# ─────────────────────────────────────────────────────────────────────────────
# Records + parsing
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FastaRecord:
    """One in-RAM FASTA record."""

    header: str
    sequence: str

    @property
    def name(self) -> str:
        return self.header.split()[0] if self.header.split() else self.header

    @property
    def length(self) -> int:
        return len(self.sequence)

    @property
    def gc_percent(self) -> float:
        return gc_content_percent(self.sequence)

    @property
    def digest(self) -> str:
        return sha256_of_text(self.sequence)

    def to_fasta(self) -> str:
        from titan_utils.export import records_to_fasta

        return records_to_fasta({self.header: self.sequence})


def parse_multi_fasta(text: str) -> List[FastaRecord]:
    """Parse multi-FASTA text (tolerates bare sequences → synthetic headers)."""
    records: List[FastaRecord] = []
    header = None
    chunks: List[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                seq = clean_sequence("".join(chunks))
                if seq:
                    records.append(FastaRecord(header, seq))
            header = line[1:].strip() or f"record_{len(records) + 1}"
            chunks = []
        else:
            if header is None:
                header = "record_1"
            chunks.append(line)
    if header is not None:
        seq = clean_sequence("".join(chunks))
        if seq:
            records.append(FastaRecord(header, seq))
    return records


# ─────────────────────────────────────────────────────────────────────────────
# Analyses
# ─────────────────────────────────────────────────────────────────────────────

def _tm_wallace(seq: str) -> float:
    return float(2 * (seq.count("A") + seq.count("T")) + 4 * (seq.count("G") + seq.count("C")))


def _tm_salt(seq: str) -> float:
    if not seq:
        return 0.0
    gc = gc_content_percent(seq)
    return round(64.9 + 41.0 * (sum(seq.count(b) for b in "GC") - 16.4) / max(len(seq), 1), 2)


def _orf_count(seq: str) -> int:
    from titan_utils.sequence import find_orfs_simple

    return len(find_orfs_simple(seq, min_len=30))


def _mw_kda(seq: str) -> float:
    """Rough dsDNA molecular weight (Da → kDa): 650 Da per bp average."""
    return round(len(seq) * 650.0 / 1000.0, 2)


def _revcomp(seq: str) -> str:
    from titan_utils.sequence import revcomp

    return revcomp(seq)


# id -> (label, callable, output column name)
BATCH_ANALYSES: Dict[str, Tuple[str, Callable[[FastaRecord], Any], str]] = {
    "length": ("Length (bp)", lambda r: r.length, "Length_bp"),
    "gc": ("GC content (%)", lambda r: round(r.gc_percent, 2), "GC_Percent"),
    "tm_salt": ("Tm salt-adjusted (°C)", lambda r: _tm_salt(r.sequence), "Tm_Salt_C"),
    "tm_wallace": ("Tm Wallace (°C)", lambda r: _tm_wallace(r.sequence), "Tm_Wallace_C"),
    "mw": ("Molecular weight (kDa)", lambda r: _mw_kda(r.sequence), "MW_kDa"),
    "orfs": ("ORF count (≥30 bp)", lambda r: _orf_count(r.sequence), "ORF_Count"),
    "n_count": ("Ambiguous bases (N)", lambda r: r.sequence.upper().count("N"), "N_Count"),
    "revcomp": ("Reverse complement", lambda r: _revcomp(r.sequence), "Reverse_Complement"),
    "digest": ("SHA-256 digest", lambda r: r.digest, "SHA256"),
}

DEFAULT_ANALYSES: Tuple[str, ...] = ("length", "gc", "tm_salt", "mw", "orfs", "n_count", "digest")


@dataclass
class BatchResult:
    """Consolidated batch-run outcome."""

    records: List[FastaRecord] = field(default_factory=list)
    analyses: List[str] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    input_digest: str = ""
    input_size: int = 0
    started_utc: str = ""

    def to_frame(self) -> pd.DataFrame:
        if not self.rows:
            return pd.DataFrame()
        return pd.DataFrame(self.rows)

    @property
    def record_count(self) -> int:
        return len(self.records)

    def summary(self) -> Dict[str, Any]:
        df = self.to_frame()
        summary: Dict[str, Any] = {
            "records": len(self.records),
            "analyses": list(self.analyses),
            "input_sha256": self.input_digest,
            "generated_utc": self.started_utc,
            "zero_data_retention": True,
        }
        if not df.empty and "Length_bp" in df.columns:
            summary["total_bp"] = int(df["Length_bp"].sum())
            summary["mean_length_bp"] = round(float(df["Length_bp"].mean()), 2)
            summary["max_length_bp"] = int(df["Length_bp"].max())
            summary["min_length_bp"] = int(df["Length_bp"].min())
        if not df.empty and "GC_Percent" in df.columns:
            summary["mean_gc_percent"] = round(float(df["GC_Percent"].mean()), 2)
        return summary


def run_batch(
    payload: str,
    analyses: Sequence[str] | None = None,
) -> BatchResult:
    """Run the selected analyses across every record in ``payload``."""
    from datetime import datetime, timezone

    records = parse_multi_fasta(payload)
    chosen = [a for a in (analyses or DEFAULT_ANALYSES) if a in BATCH_ANALYSES]
    rec = provenance_record(payload, kind="fastq/fasta batch", label="batch_input")
    result = BatchResult(
        records=records,
        analyses=chosen,
        input_digest=rec.digest,
        input_size=rec.size_bytes,
        started_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )
    for i, fasta_rec in enumerate(records, start=1):
        row: Dict[str, Any] = {"Index": i, "Record_ID": fasta_rec.name}
        for analysis_id in chosen:
            label, fn, column = BATCH_ANALYSES[analysis_id]
            row[column] = fn(fasta_rec)
        result.rows.append(row)
    return result


def build_batch_zip(result: BatchResult) -> bytes:
    """Consolidated ZIP archive for a batch run (built entirely in RAM)."""
    df = result.to_frame()
    csv_bytes = to_csv_bytes(df)
    tsv_bytes = to_tsv_bytes(df)
    fasta_bytes = to_fasta_bytes({r.header: r.sequence for r in result.records})
    summary_bytes = json.dumps(result.summary(), indent=2).encode("utf-8")
    readme_bytes = (
        "TITAN BATCH PROCESSOR — consolidated archive\n"
        f"Records processed: {result.record_count}\n"
        f"Generated: {result.started_utc}\n\n"
        "Files: batch_results.csv, batch_results.tsv, batch_summary.json,\n"
        "records.fasta, manifest.json (SHA-256 provenance).\n"
        "Zero Data Retention: processed in 100% ephemeral in-RAM buffers and\n"
        "streamed to your browser on request — the Titan servers retain no\n"
        "sequences, VCFs or FASTQ reads on disk.\n"
    ).encode("utf-8")

    files: List[Tuple[str, bytes]] = [
        ("batch_results.csv", csv_bytes),
        ("batch_results.tsv", tsv_bytes),
        ("batch_summary.json", summary_bytes),
        ("records.fasta", fasta_bytes),
        ("README.txt", readme_bytes),
    ]
    manifest = provenance_manifest(
        [("batch_input", result.input_digest)]
        + [(name, data, "artifact") for name, data in files]
    )
    manifest["tool"] = "Titan High-Throughput Batch Processor"
    manifest["record_count_files"] = len(files)
    manifest["input_sha256"] = result.input_digest
    manifest["files"] = [
        {"name": name, "sha256": provenance_record(data, kind="artifact", label=name).digest,
         "size_bytes": len(data)}
        for name, data in files
    ]
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files:
            zf.writestr(name, data)
        zf.writestr("manifest.json", manifest_bytes)
    return buffer.getvalue()
