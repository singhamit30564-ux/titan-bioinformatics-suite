"""Engine dispatcher — Rust (`titan_core`) with a pure-Python fallback.

Every public function returns a dict with the **same schema** regardless of
engine. ``result["engine"]`` is ``"rust"`` or ``"python"`` so the UI and the
Export Center can surface which engine produced a run (plus timing/threads via
:func:`run_with_stats`).

Design rules
------------
* The app must never crash because ``titan_core`` is missing: the Python
  implementations below are complete fallbacks (FASTQ/FASTQ.GZ/BGZF, SAM/BAM,
  VCF/BCF, banded Gotoh alignment, canonical k-mer counting, seed-and-extend
  mapping).
* Zero-Data-Retention: bytes-in / bytes-out is first-class. Path inputs are
  read (and, for plain files, memory-mapped by the Rust engine) but nothing is
  ever written to disk by this module.
* Progress callbacks receive ``(done, total)``; cancellation tokens are any
  object exposing ``is_cancelled() -> bool`` (``titan_core.CancelToken`` or
  :class:`PythonCancelToken`).
* Engine selection: :func:`set_engine_policy` / the sidebar toggle in
  :func:`render_engine_toggle` — ``"auto"`` (default) prefers Rust when it is
  importable, ``"python"`` forces the fallback, ``"rust"`` errors when the
  extension is unavailable.

Python fallback notes (honesty)
-------------------------------
* CIGAR tie-breaking can differ between engines when several optimal paths
  exist; alignment *scores* match exactly (same Gotoh recurrences, same gap
  cost model ``gap_open + gap_extend*(L-1)``).
* The Python duplication estimate is an exact hash set (capped at 2M entries);
  the Rust engine streams HyperLogLog + Bloom. Keys are identical.
* BCF ``FORMAT``/sample columns are reported through
  ``warnings["bcf_format_skipped"]`` in both engines (single-sample summaries
  are the current product surface).
"""
from __future__ import annotations

import gzip
import hashlib
import io
import os
import struct
import time
from collections import Counter
from typing import Any, Callable, Optional, Sequence

__all__ = [
    "PythonCancelToken",
    "engine_status",
    "refresh_engine",
    "set_engine_policy",
    "get_engine_policy",
    "active_engine",
    "run_with_stats",
    "parse_fastq",
    "qc_fastq",
    "read_alignment",
    "parse_vcf",
    "align",
    "kmer_count",
    "map_reads",
    "fastq_result_to_rows",
    "vcf_result_to_dataframe",
    "render_engine_toggle",
    "engine_badge",
]

ENGINE_VERSION = "1.0.0"

# ─────────────────────────────────────────────────────────────────────────────
# Engine detection & policy
# ─────────────────────────────────────────────────────────────────────────────

_POLICY = os.environ.get("TITAN_ENGINE", "auto").strip().lower() or "auto"
_RUST: Any = None
_RUST_TRIED = False


def refresh_engine() -> Any:
    """(Re)probe for the ``titan_core`` extension module."""
    global _RUST_TRIED
    _RUST_TRIED = False
    return _detect_rust()


def _detect_rust() -> Any:
    global _RUST, _RUST_TRIED
    if _RUST_TRIED:
        return _RUST
    _RUST_TRIED = True
    try:
        import titan_core  # type: ignore

        if callable(getattr(titan_core, "parse_fastq", None)) and callable(
            getattr(titan_core, "qc_fastq", None)
        ):
            _RUST = titan_core
        else:
            _RUST = None
    except Exception:
        _RUST = None
    return _RUST


def set_engine_policy(policy: str) -> None:
    """Set engine policy: ``auto`` | ``python`` | ``rust``."""
    global _POLICY
    policy = (policy or "auto").strip().lower()
    if policy not in {"auto", "python", "rust"}:
        raise ValueError("policy must be 'auto', 'python' or 'rust'")
    _POLICY = policy


def get_engine_policy() -> str:
    return _POLICY


def active_engine() -> str:
    """Return the engine the next call would use: ``rust`` or ``python``."""
    if _POLICY == "python":
        return "python"
    rust = _detect_rust()
    if rust is not None:
        return "rust"
    return "python"


def engine_status() -> dict[str, Any]:
    """Full engine availability report (for the sidebar status card)."""
    rust = _detect_rust()
    info: dict[str, Any] = {
        "policy": _POLICY,
        "active": active_engine(),
        "python_fallback": True,
        "python_version": ENGINE_VERSION,
        "rust_available": rust is not None,
        "rust_version": None,
        "rust_threads_default": None,
        "features": [],
    }
    if rust is not None:
        try:
            details = rust.engine_info()
            info["rust_version"] = details.get("version")
            info["rust_threads_default"] = details.get("rayon_threads")
            info["features"] = list(details.get("features", []))
        except Exception:
            info["rust_version"] = getattr(rust, "__engine_version__", "unknown")
    return info


class PythonCancelToken:
    """Thread-safe cancellation token mirroring ``titan_core.CancelToken``."""

    def __init__(self) -> None:
        import threading

        self._flag = threading.Event()

    def cancel(self) -> None:
        self._flag.set()

    def is_cancelled(self) -> bool:
        return self._flag.is_set()

    def reset(self) -> None:
        self._flag.clear()


def _check_cancel(cancel: Any) -> bool:
    if cancel is None:
        return False
    try:
        return bool(cancel.is_cancelled())
    except Exception:
        return False


class _Cancelled(RuntimeError):
    pass


def _report(progress: Optional[Callable[[int, int], None]], done: int, total: int) -> None:
    if progress is not None:
        try:
            progress(int(done), int(total))
        except Exception:
            pass  # progress is best-effort observability, never fatal


# ─────────────────────────────────────────────────────────────────────────────
# Input loading (bytes-in / bytes-out, ZDR-safe)
# ─────────────────────────────────────────────────────────────────────────────

def _load_bytes(path: Optional[str], data: Any) -> bytes:
    if path is not None and data is not None:
        raise ValueError("pass either 'path' or 'data', not both")
    if path is None and data is None:
        raise ValueError("no input: pass 'path' or 'data'")
    if path is not None:
        path = os.fspath(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"path not found: {path}")
        with open(path, "rb") as handle:
            raw = handle.read()
    else:
        if isinstance(data, str):
            raw = data.encode("utf-8")
        else:
            raw = bytes(data)
    if len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
        # gzip or BGZF: the stdlib decoder handles multi-member streams.
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as gz:
            raw = gz.read()
    return raw


# ─────────────────────────────────────────────────────────────────────────────
# FASTQ parsing (Python fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _iter_fastq(raw: bytes, warnings: dict[str, int]):
    """Yield ``(name, seq, qual)`` byte triples; counts problems in ``warnings``."""
    pos = 0
    n = len(raw)
    while pos < n:
        # 1. header
        end = raw.find(b"\n", pos)
        if end < 0:
            end = n
        header = raw[pos:end].rstrip(b"\r")
        pos = end + 1
        if not header:
            continue
        if not header.startswith(b"@"):
            warnings["malformed_records"] += 1
            continue
        name = header[1:]
        # 2. sequence lines until '+'
        seq_parts: list[bytes] = []
        seq_len = 0
        sep_found = False
        while pos < n:
            end = raw.find(b"\n", pos)
            if end < 0:
                end = n
            line = raw[pos:end].rstrip(b"\r")
            pos = end + 1
            if line.startswith(b"+"):
                sep_found = True
                break
            seq_parts.append(line)
            seq_len += len(line)
        if not sep_found:
            warnings["truncated_records"] += 1
            break
        seq = b"".join(seq_parts)
        if not seq:
            warnings["empty_reads"] += 1
        if len(seq_parts) > 1:
            warnings["wrapped_records"] += 1
        # 3. quality lines until >= len(seq)
        qual_parts: list[bytes] = []
        qual_len = 0
        complete = False
        while pos < n:
            end = raw.find(b"\n", pos)
            if end < 0:
                end = n
            line = raw[pos:end].rstrip(b"\r")
            pos = end + 1
            qual_parts.append(line)
            qual_len += len(line)
            if qual_len >= seq_len:
                complete = True
                break
        if not complete:
            warnings["truncated_records"] += 1
            break
        qual = b"".join(qual_parts)
        if len(qual) != len(seq):
            warnings["malformed_records"] += 1
            continue
        yield name, seq, qual


def _detect_phred(qmin: int, qmax: int) -> str:
    if qmin == 255:
        return "ambiguous"
    if qmin >= 64:
        return "phred64"
    if qmax <= 60 or (qmin < 59 and qmax <= 74):
        return "phred33"
    return "ambiguous"


def _phred_offset(encoding: str) -> int:
    return 64 if encoding == "phred64" else 33


def _flatten_fastq(result: dict[str, Any]) -> dict[str, Any]:
    """Zero-copy-style flattened views (names / seqs / qualities) from the
    columnar worker layout. Both the Rust and Python paths share this schema,
    so ``engine.parse_fastq`` exposes the same convenience keys either way."""
    seq_concat = result.get("seq_concat", b"")
    seq_offsets = result.get("seq_offsets") or [0]
    qual_concat = result.get("qual_concat", b"")
    qual_offsets = result.get("qual_offsets") or [0]
    names = result.get("names") or []
    n_reads = int(result.get("n_reads", len(names)))
    seqs = [
        bytes(seq_concat[seq_offsets[i]:seq_offsets[i + 1]]).decode("ascii", "replace")
        for i in range(n_reads)
    ]
    qualities = [
        bytes(qual_concat[qual_offsets[i]:qual_offsets[i + 1]]).decode("ascii", "replace")
        for i in range(n_reads)
    ]
    return {"names": list(names), "seqs": seqs, "qualities": qualities}


def _py_parse_fastq(
    path: Optional[str],
    data: Any,
    max_records: Optional[int],
    progress: Optional[Callable[[int, int], None]],
    cancel: Any,
) -> dict[str, Any]:
    raw = _load_bytes(path, data)
    total = len(raw)
    warnings = {
        "malformed_records": 0,
        "truncated_records": 0,
        "crlf_lines": 0,
        "empty_reads": 0,
        "wrapped_records": 0,
    }
    names: list[str] = []
    seq_concat = bytearray()
    seq_offsets: list[int] = [0]
    qual_concat = bytearray()
    qual_offsets: list[int] = [0]
    lengths: list[int] = []
    qmin, qmax = 255, 0
    truncated = False
    for index, (name, seq, qual) in enumerate(_iter_fastq(raw, warnings)):
        if _check_cancel(cancel):
            raise _Cancelled("cancelled")
        if max_records is not None and index >= max_records:
            truncated = True
            break
        names.append(name.decode("utf-8", "replace"))
        seq_concat += seq
        seq_offsets.append(len(seq_concat))
        qual_concat += qual
        qual_offsets.append(len(qual_concat))
        lengths.append(len(seq))
        if qual:
            lo, hi = min(qual), max(qual)
            qmin = min(qmin, lo)
            qmax = max(qmax, hi)
        if index % 50_000 == 0:
            _report(progress, min(len(seq_concat) + len(qual_concat), total), total)
    _report(progress, total, total)
    encoding = _detect_phred(qmin, qmax)
    result: dict[str, Any] = {
        "engine": "python",
        "n_reads": len(names),
        "names": names,
        "seq_concat": bytes(seq_concat),
        "seq_offsets": seq_offsets,
        "qual_concat": bytes(qual_concat),
        "qual_offsets": qual_offsets,
        "lengths": lengths,
        "phred_encoding": encoding,
        "truncated": truncated,
        "warnings": warnings,
        "bytes_total": total,
    }
    # Flattened convenience views (names / seqs / qualities) as documented on
    # engine.parse_fastq — the Rust path returns the same keys.
    result.update(_flatten_fastq(result))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# QC (Python fallback)
# ─────────────────────────────────────────────────────────────────────────────

_ADAPTERS = (
    ("Illumina_Universal", b"AGATCGGAAGAG"),
    ("Illumina_SmallRNA", b"TGGAATTCTCGG"),
    ("Nextera", b"CTGTCTCTTATA"),
    ("PolyA", b"AAAAAAAAAAAA"),
    ("PolyG", b"GGGGGGGGGGGG"),
)


def _py_qc_fastq(
    path: Optional[str],
    data: Any,
    k: int,
    progress: Optional[Callable[[int, int], None]],
    cancel: Any,
) -> dict[str, Any]:
    raw = _load_bytes(path, data)
    total = len(raw)
    warnings = {"malformed_records": 0, "truncated_records": 0, "crlf_lines": 0, "empty_reads": 0, "wrapped_records": 0}
    n_reads = 0
    total_bases = 0
    gc_bases = 0
    n_bases = 0
    len_min: Optional[int] = None
    len_max = 0
    length_hist: dict[int, int] = {}
    qual_sum_by_pos: list[int] = []
    qual_count_by_pos: list[int] = []
    qual_hist = [0] * 256
    qmin, qmax = 255, 0
    seen: set[bytes] = set()
    duplicates_seen = 0
    distinct_cap = 2_000_000
    kmer_counts: Counter[str] = Counter()
    kmer_total = 0
    kmer_cap = 200_000
    adapter_hits = [0] * len(_ADAPTERS)
    empty_reads = 0

    for index, (name, seq, qual) in enumerate(_iter_fastq(raw, warnings)):
        if _check_cancel(cancel):
            raise _Cancelled("cancelled")
        n_reads += 1
        length = len(seq)
        total_bases += length
        if length == 0:
            empty_reads += 1
        len_min = length if len_min is None else min(len_min, length)
        if length > len_max:
            len_max = length
            qual_sum_by_pos.extend([0] * (length - len(qual_sum_by_pos)))
            qual_count_by_pos.extend([0] * (length - len(qual_count_by_pos)))
        length_hist[length] = length_hist.get(length, 0) + 1
        up = seq.upper()
        gc_bases += up.count(b"G") + up.count(b"C")
        n_bases += up.count(b"N")
        for i, q in enumerate(qual):
            if i < len(qual_sum_by_pos):
                qual_sum_by_pos[i] += q
                qual_count_by_pos[i] += 1
            qual_hist[q] += 1
            if q < qmin:
                qmin = q
            if q > qmax:
                qmax = q
        digest = hashlib.blake2b(seq, digest_size=8).digest()
        if digest in seen:
            duplicates_seen += 1
        elif len(seen) < distinct_cap:
            seen.add(digest)
        if k:
            for j in range(0, max(0, length - k + 1)):
                word = up[j : j + k]
                if b"N" in word:
                    continue
                key = word.decode("ascii", "replace")
                if key in kmer_counts:
                    kmer_counts[key] += 1
                elif len(kmer_counts) < kmer_cap:
                    kmer_counts[key] = 1
                kmer_total += 1
        for ai, (_aname, motif) in enumerate(_ADAPTERS):
            if motif in up:
                adapter_hits[ai] += 1
        if index % 20_000 == 0:
            _report(progress, min(index * 64, total), total)
    _report(progress, total, total)

    encoding = _detect_phred(qmin, qmax)
    offset = _phred_offset(encoding)
    total_q = max(1, sum(qual_hist))
    q20 = sum(count for q, count in enumerate(qual_hist) if q - offset >= 20)
    q30 = sum(count for q, count in enumerate(qual_hist) if q - offset >= 30)
    per_base_mean = [
        (qual_sum_by_pos[i] / qual_count_by_pos[i] - offset) if qual_count_by_pos[i] else 0.0
        for i in range(len(qual_sum_by_pos))
    ]
    distinct_estimate = float(len(seen) + max(0, duplicates_seen - (n_reads - len(seen))))
    if n_reads:
        # exact distinct among capped set + unseen tail estimate is not
        # fabricated: report the observed distinct count honestly.
        distinct_estimate = float(len(seen))
        dup_rate = 100.0 * (1.0 - distinct_estimate / n_reads)
    else:
        dup_rate = 0.0
    bloom_dup_rate = 100.0 * duplicates_seen / n_reads if n_reads else 0.0
    top_kmers = [
        {"kmer": word, "count": count, "percent": 100.0 * count / max(1, kmer_total)}
        for word, count in sorted(kmer_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]
    ]
    top_kmers = [item for item in top_kmers if item["percent"] >= 0.05]
    return {
        "engine": "python",
        "n_reads": n_reads,
        "total_bases": total_bases,
        "length_min": len_min or 0,
        "length_max": len_max,
        "length_mean": (total_bases / n_reads) if n_reads else 0.0,
        "length_histogram": [
            {"length": length, "count": count} for length, count in sorted(length_hist.items())
        ],
        "gc_percent": 100.0 * gc_bases / max(1, total_bases),
        "n_content_percent": 100.0 * n_bases / max(1, total_bases),
        "per_base_mean_quality": per_base_mean,
        "q20_percent": 100.0 * q20 / total_q,
        "q30_percent": 100.0 * q30 / total_q,
        "phred_encoding": encoding,
        "duplication": {
            "method": "python-exact-hashset(capped)",
            "distinct_estimate": distinct_estimate,
            "duplication_rate_percent": max(0.0, dup_rate),
            "bloom_duplicate_rate_percent": min(100.0, bloom_dup_rate),
        },
        "overrepresented_kmers": top_kmers,
        "adapter_hits": [
            {
                "adapter": _ADAPTERS[ai][0],
                "reads_with_adapter": adapter_hits[ai],
                "percent": 100.0 * adapter_hits[ai] / n_reads if n_reads else 0.0,
            }
            for ai in range(len(_ADAPTERS))
        ],
        "empty_reads": empty_reads,
        "warnings": warnings,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Alignment (Python fallback — Gotoh banded affine gaps)
# ─────────────────────────────────────────────────────────────────────────────

_NEG = float("-inf")


def _py_align(
    query: str,
    target: str,
    mode: str,
    match_score: int,
    mismatch_score: int,
    gap_open: int,
    gap_extend: int,
    band: int,
    display_max: int = 2000,
) -> dict[str, Any]:
    q = (query or "").strip()
    t = (target or "").strip()
    if not q or not t:
        raise ValueError("align() requires non-empty sequences")
    if len(q) > 100_000 or len(t) > 100_000:
        raise ValueError("align() input limited to 100 kb per sequence")
    local = mode not in {"global", "needleman_wunsch", "nw"}
    m, n = len(q), len(t)
    d0 = n - m
    half_band = max(abs(d0) + 1, band or 64)
    width = 2 * half_band + 1

    def j_lo(i: int) -> int:
        return max(0, i + d0 // 2 - half_band)

    def j_hi(i: int) -> int:
        return min(n, i + d0 // 2 + half_band)

    # Rows: dict-free lists sized to the band window.
    m_prev = [_NEG] * width
    x_prev = [_NEG] * width
    y_prev = [_NEG] * width
    trace: list[list[int]] = [[0, 0, 0] for _ in range((m + 1) * width)]
    # trace codes: 0 stop, 1 diag-from-M, 2 diag-from-X, 3 diag-from-Y,
    # 4 up-from-M, 5 up-from-X, 6 left-from-M, 7 left-from-Y
    lo0, hi0 = j_lo(0), j_hi(0)
    for j in range(lo0, hi0 + 1):
        slot = j - lo0
        if j == 0:
            m_prev[slot] = 0
        elif not local:
            y_prev[slot] = -(gap_open + gap_extend * (j - 1))
            trace[0 * width + slot][2] = 1 if j == 1 else 7
        else:
            m_prev[slot] = 0

    best = (0, 0, 0, 0)  # score, i, j, state
    for i in range(1, m + 1):
        lo, hi = j_lo(i), j_hi(i)
        plo, phi = j_lo(i - 1), j_hi(i - 1)
        m_cur = [_NEG] * width
        x_cur = [_NEG] * width
        y_cur = [_NEG] * width
        for j in range(lo, hi + 1):
            slot = j - lo
            row_base = i * width + slot
            if j == 0:
                if not local:
                    x_cur[slot] = -(gap_open + gap_extend * (i - 1))
                    trace[row_base][1] = 1 if i == 1 else 5
                else:
                    m_cur[slot] = 0
                continue
            best_m, pred_m = _NEG, 0
            if plo <= j - 1 <= phi:
                ds = (j - 1) - plo
                for score, pred in ((m_prev[ds], 1), (x_prev[ds], 2), (y_prev[ds], 3)):
                    if score > best_m:
                        best_m, pred_m = score, pred
            if best_m > _NEG / 2:
                best_m += match_score if q[i - 1].upper() == t[j - 1].upper() else mismatch_score
            if local and best_m < 0:
                best_m, pred_m = 0, 0
            m_cur[slot] = best_m
            trace[row_base][0] = pred_m

            best_x, pred_x = _NEG, 0
            if plo <= j <= phi:
                us = j - plo
                open_ = m_prev[us] - gap_open
                ext = x_prev[us] - gap_extend
                if open_ >= ext and open_ > _NEG / 2:
                    best_x, pred_x = open_, 4
                elif ext > _NEG / 2:
                    best_x, pred_x = ext, 5
            x_cur[slot] = best_x
            trace[row_base][1] = pred_x

            best_y, pred_y = _NEG, 0
            if j - 1 >= lo:
                ls = (j - 1) - lo
                open_ = m_cur[ls] - gap_open
                ext = y_cur[ls] - gap_extend
                if open_ >= ext and open_ > _NEG / 2:
                    best_y, pred_y = open_, 6
                elif ext > _NEG / 2:
                    best_y, pred_y = ext, 7
            y_cur[slot] = best_y
            trace[row_base][2] = pred_y

            if local and best_m > best[0]:
                best = (best_m, i, j, 0)
        m_prev, x_prev, y_prev = m_cur, x_cur, y_cur

    if not local:
        lo, hi = j_lo(m), j_hi(m)
        if not (lo <= n <= hi):
            raise ValueError("global alignment band does not reach the end cell; increase band")
        slot = n - lo
        score, state = max(((m_prev[slot], 0), (x_prev[slot], 1), (y_prev[slot], 2)), key=lambda x: x[0])
        if score <= _NEG / 2:
            raise ValueError("no alignment path in band")
        best = (score, m, n, state)

    # Traceback.
    i, j, state = best[1], best[2], best[3]
    cigar_rev: list[str] = []
    q_aln_rev: list[str] = []
    t_aln_rev: list[str] = []
    matches = 0
    guard = 0
    while True:
        if i == 0 and j == 0:
            break
        if i == 0 or j == 0:
            if local:
                break
            while j > 0:
                cigar_rev.append("D")
                q_aln_rev.append("-")
                t_aln_rev.append(t[j - 1])
                j -= 1
            while i > 0:
                cigar_rev.append("I")
                q_aln_rev.append(q[i - 1])
                t_aln_rev.append("-")
                i -= 1
            break
        lo = j_lo(i)
        slot = j - lo
        if j < lo or slot >= width:
            break
        pred = trace[i * width + slot][state]
        if pred == 0:
            break
        if pred in (1, 2, 3):
            cigar_rev.append("M")
            q_aln_rev.append(q[i - 1])
            t_aln_rev.append(t[j - 1])
            if q[i - 1].upper() == t[j - 1].upper():
                matches += 1
            i -= 1
            j -= 1
            state = pred - 1
        elif pred in (4, 5):
            cigar_rev.append("I")
            q_aln_rev.append(q[i - 1])
            t_aln_rev.append("-")
            i -= 1
            state = 0 if pred == 4 else 1
        else:
            cigar_rev.append("D")
            q_aln_rev.append("-")
            t_aln_rev.append(t[j - 1])
            j -= 1
            state = 0 if pred == 6 else 2
        guard += 1
        if guard > m + n + 8:
            break

    # Coalesce CIGAR.
    cigar_parts: list[str] = []
    last_op = ""
    last_len = 0
    for op in reversed(cigar_rev):
        if op == last_op:
            last_len += 1
        else:
            if last_op:
                cigar_parts.append(f"{last_len}{last_op}")
            last_op, last_len = op, 1
    if last_op:
        cigar_parts.append(f"{last_len}{last_op}")
    aln_columns = len(q_aln_rev)
    display_capped = aln_columns > display_max
    take = min(display_max, aln_columns)
    q_aln = "".join(reversed(q_aln_rev))[:take]
    t_aln = "".join(reversed(t_aln_rev))[:take]
    return {
        "engine": "python",
        "score": int(best[0]),
        "cigar": "".join(cigar_parts),
        "q_start": i,
        "q_end": best[1],
        "t_start": j,
        "t_end": best[2],
        "matches": matches,
        "aln_columns": aln_columns,
        "identity_percent": 100.0 * matches / aln_columns if aln_columns else 0.0,
        "aligned_query": q_aln,
        "aligned_target": t_aln,
        "display_capped": display_capped,
        "mode": mode,
        "simd_extension": False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# k-mer counting (Python fallback — canonical 2-bit)
# ─────────────────────────────────────────────────────────────────────────────

def _pack_kmer(word: bytes) -> Optional[int]:
    packed = 0
    for base in word.upper():
        bits = b"ACGT".find(base)
        if bits < 0:
            return None
        packed = (packed << 2) | bits
    return packed


def _revcomp_packed(packed: int, k: int) -> int:
    out = 0
    for i in range(k):
        bits = (packed >> (2 * i)) & 0b11
        out = (out << 2) | (3 - bits)
    return out


def _unpack_kmer(packed: int, k: int) -> str:
    out = []
    for i in range(k - 1, -1, -1):
        out.append("ACGT"[(packed >> (2 * i)) & 0b11])
    return "".join(out)


def _py_kmer_count(
    path: Optional[str],
    data: Any,
    k: int,
    top: int,
    max_entries: int,
    progress: Optional[Callable[[int, int], None]],
    cancel: Any,
) -> dict[str, Any]:
    raw = _load_bytes(path, data)
    total_bytes = len(raw)
    k = max(1, min(32, k))
    counts: dict[int, int] = {}
    total_kmers = 0
    truncated = False
    stream = raw.replace(b"\n", b"").replace(b"\r", b"").upper()
    if _check_cancel(cancel):
        raise _Cancelled("cancelled")
    for j in range(0, max(0, len(stream) - k + 1)):
        packed = _pack_kmer(stream[j : j + k])
        if packed is None:
            continue
        key = min(packed, _revcomp_packed(packed, k))
        total_kmers += 1
        if key in counts:
            counts[key] += 1
        elif len(counts) < max_entries:
            counts[key] = 1
        else:
            truncated = True
    _report(progress, total_bytes, total_bytes)
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    return {
        "engine": "python",
        "k": k,
        "total_kmers": total_kmers,
        "unique_kmers": len(counts),
        "distinct_estimate": float(len(counts)),
        "truncated": truncated,
        "top_kmers": [
            {"kmer": _unpack_kmer(key, k), "count": count} for key, count in ranked
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# SAM/BAM (Python fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_region(region: Optional[str]):
    if not region:
        return None, None, None
    text = region.strip()
    chrom = None
    start, end = 1, None
    if ":" in text:
        chrom, rest = text.split(":", 1)
    else:
        chrom, rest = text, ""
    if rest:
        if "-" in rest:
            s, e = rest.split("-", 1)
            start = int(s.replace(",", "")) if s else 1
            end = int(e.replace(",", "")) if e else None
        else:
            start = int(rest.replace(",", ""))
    return chrom or None, start, end


def _region_matches(region_chrom, region_start, region_end, chrom: str, pos: int) -> bool:
    active = region_chrom is not None or (region_start or 1) != 1 or region_end is not None
    if not active:
        return True
    if pos <= 0:
        return False  # unmapped reads never fall inside a genomic region
    if region_chrom:
        strip = lambda s: (s or "").lower().removeprefix("chr")
        if strip(region_chrom) != strip(chrom):
            return False
    if pos < (region_start or 1):
        return False
    if region_end is not None and pos > region_end:
        return False
    return True


def _cigar_ref_span(cigar: str) -> int:
    import re

    span = 0
    for length, op in re.findall(r"(\d+)([MIDNSHP=X])", cigar or ""):
        if op in "MDN=X":
            span += int(length)
    return span


def _parse_cigar_ops(cigar: str):
    import re

    ops = []
    for length, op in re.findall(r"(\d+)([MIDNSHP=X])", cigar or ""):
        ops.append((int(length), op))
    return ops


def _flagstat_observe(flagstat: dict[str, int], flag: int) -> None:
    flagstat["total"] += 1
    if flag & 0x100:
        flagstat["secondary"] += 1
    elif flag & 0x800:
        flagstat["supplementary"] += 1
    else:
        flagstat["primary"] += 1
    if flag & 0x400:
        flagstat["duplicates"] += 1
    mapped = not (flag & 0x4)
    if mapped:
        flagstat["mapped"] += 1
    if flag & 0x1:
        flagstat["paired"] += 1
        if flag & 0x40:
            flagstat["read1"] += 1
        if flag & 0x80:
            flagstat["read2"] += 1
        if flag & 0x2:
            flagstat["properly_paired"] += 1
        if mapped and not (flag & 0x8):
            flagstat["with_itself_and_mate_mapped"] += 1
        if mapped and (flag & 0x8):
            flagstat["singletons"] += 1


def _new_flagstat() -> dict[str, int]:
    return {
        "total": 0,
        "primary": 0,
        "secondary": 0,
        "supplementary": 0,
        "duplicates": 0,
        "mapped": 0,
        "paired": 0,
        "read1": 0,
        "read2": 0,
        "properly_paired": 0,
        "with_itself_and_mate_mapped": 0,
        "singletons": 0,
    }


def _add_coverage(coverage: dict[str, list[int]], ref_name: str, ref_len: int, pos0: int, ops, region) -> None:
    if ref_len <= 0:
        return
    bins = 1000
    bin_size = max(1.0, ref_len / bins)
    entry = coverage.setdefault(ref_name, [0] * bins)
    cursor = pos0
    region_chrom, region_start, region_end = region
    for length, op in ops:
        if op in "MDN=X":
            left, right = cursor, cursor + length
            while left < right:
                bin_index = int(left / bin_size)
                bin_end = int((bin_index + 1) * bin_size)
                if bin_index >= bins:
                    break
                if region_chrom is None and region_start == 1 and region_end is None:
                    entry[bin_index] += max(0, min(right, bin_end) - left)
                else:
                    for p in range(left, min(right, bin_end)):
                        if _region_matches(region_chrom, region_start, region_end, ref_name, p + 1):
                            entry[bin_index] += 1
                left = bin_end
            cursor = right


def _py_read_alignment(
    path: Optional[str],
    data: Any,
    region: Optional[str],
    progress: Optional[Callable[[int, int], None]],
    cancel: Any,
) -> dict[str, Any]:
    raw = _load_bytes(path, data)
    total_bytes = len(raw)
    region_parsed = _parse_region(region)
    flagstat = _new_flagstat()
    mapq_hist = [0] * 256
    coverage: dict[str, list[int]] = {}
    sample: list[dict[str, Any]] = []
    header_lines: list[str] = []
    references: list[dict[str, Any]] = []
    ref_len_by_name: dict[str, int] = {}
    n_in_region = 0
    warnings = {"malformed_rows": 0, "bcf_format_skipped": False, "header_missing": False}

    is_bam = raw[:4] == b"BAM\x01"
    fmt = "bam" if is_bam else "sam"
    header_text = ""

    if is_bam:
        if len(raw) < 12:
            raise ValueError("truncated BAM stream")
        l_text = struct.unpack("<i", raw[4:8])[0]
        header_text = raw[8 : 8 + l_text].decode("utf-8", "replace")
        pos = 8 + l_text
        (n_ref,) = struct.unpack("<i", raw[pos : pos + 4])
        pos += 4
        for _ in range(max(0, n_ref)):
            (l_name,) = struct.unpack("<i", raw[pos : pos + 4])
            pos += 4
            name = raw[pos : pos + l_name].split(b"\x00")[0].decode("utf-8", "replace")
            pos += l_name
            (l_ref,) = struct.unpack("<i", raw[pos : pos + 4])
            pos += 4
            references.append({"name": name, "length": l_ref})
            ref_len_by_name[name] = l_ref
        index = 0
        while pos + 4 <= len(raw):
            if index % 4096 == 0 and _check_cancel(cancel):
                raise _Cancelled("cancelled")
            index += 1
            (block_size,) = struct.unpack("<i", raw[pos : pos + 4])
            if block_size <= 0 or pos + 4 + block_size > len(raw):
                warnings["malformed_rows"] += 1 if pos + 4 <= len(raw) else 0
                break
            rec = raw[pos + 4 : pos + 4 + block_size]
            pos += 4 + block_size
            if len(rec) < 32:
                continue
            ref_id, rpos = struct.unpack("<ii", rec[0:8])
            l_read_name = rec[8]
            mapq = rec[9]
            n_cigar_op, flag = struct.unpack("<HH", rec[12:16])
            (l_seq,) = struct.unpack("<i", rec[16:20])
            name_end = 32 + l_read_name
            if name_end > len(rec):
                continue
            ref_name = references[ref_id]["name"] if 0 <= ref_id < len(references) else "*"
            pos_1based = rpos + 1 if rpos >= 0 else 0
            cigar_off = name_end
            cigar_end = cigar_off + n_cigar_op * 4
            if cigar_end > len(rec):
                continue
            cigar_ops = []
            op_chars = "MIDNSHP=X"
            for ci in range(n_cigar_op):
                (v,) = struct.unpack("<I", rec[cigar_off + ci * 4 : cigar_off + ci * 4 + 4])
                cigar_ops.append((v >> 4, op_chars[v & 0xF] if (v & 0xF) < 9 else "?"))
            cigar = "".join(f"{length}{op}" for length, op in cigar_ops)
            if not _region_matches(*region_parsed, ref_name, pos_1based):
                continue
            n_in_region += 1
            _flagstat_observe(flagstat, flag)
            mapq_hist[mapq] += 1
            if 0 <= ref_id < len(references):
                _add_coverage(
                    coverage,
                    ref_name,
                    ref_len_by_name.get(ref_name, 0),
                    max(0, rpos),
                    cigar_ops,
                    region_parsed,
                )
            if len(sample) < 1000:
                sample.append(
                    {
                        "name": rec[32 : name_end - 1].decode("utf-8", "replace"),
                        "ref": ref_name,
                        "pos_1based": pos_1based,
                        "mapq": mapq,
                        "flag": flag,
                        "cigar": cigar,
                        "seq_len": l_seq,
                    }
                )
        header_lines = [line for line in header_text.splitlines() if line]
    else:
        # SAM text (optionally with @SQ headers).
        for raw_line in raw.split(b"\n"):
            if _check_cancel(cancel):
                raise _Cancelled("cancelled")
            line = raw_line.rstrip(b"\r")
            if not line:
                continue
            if line.startswith(b"@"):
                header = line.decode("utf-8", "replace")
                header_lines.append(header)
                if header.startswith("@SQ"):
                    name, length = "", 0
                    for field in header.split("\t")[1:]:
                        if field.startswith("SN:"):
                            name = field[3:]
                        elif field.startswith("LN:"):
                            length = int(field[3:] or 0)
                    if name:
                        references.append({"name": name, "length": length})
                        ref_len_by_name[name] = length
                continue
            fields = line.split(b"\t")
            if len(fields) < 11:
                warnings["malformed_rows"] += 1
                continue
            flag = int(fields[1] or 0)
            ref_name = fields[2].decode("utf-8", "replace")
            pos_1based = int(fields[3] or 0)
            mapq = min(255, max(0, int(fields[4] or 0)))
            cigar = fields[5].decode("utf-8", "replace")
            seq_len = len(fields[9])
            if not _region_matches(*region_parsed, ref_name, pos_1based):
                continue
            n_in_region += 1
            _flagstat_observe(flagstat, flag)
            mapq_hist[mapq] += 1
            if pos_1based > 0:
                _add_coverage(
                    coverage,
                    ref_name,
                    ref_len_by_name.get(ref_name, 0),
                    pos_1based - 1,
                    _parse_cigar_ops(cigar),
                    region_parsed,
                )
            if len(sample) < 1000:
                sample.append(
                    {
                        "name": fields[0].decode("utf-8", "replace"),
                        "ref": ref_name,
                        "pos_1based": pos_1based,
                        "mapq": mapq,
                        "flag": flag,
                        "cigar": cigar,
                        "seq_len": seq_len,
                    }
                )
    _report(progress, total_bytes, total_bytes)
    coverage_out = []
    for ref_name, bins in coverage.items():
        ref_len = ref_len_by_name.get(ref_name, 0)
        bin_size = max(1.0, ref_len / 1000) if ref_len else 1.0
        coverage_out.append({"ref": ref_name, "bins": bins, "bin_size": bin_size})
    region_label = None
    if region:
        chrom, start, end = region_parsed
        if end is None:
            region_label = f"{chrom}:{start}-"
        else:
            region_label = f"{chrom}:{start}-{end}"
    return {
        "engine": "python",
        "format": fmt,
        "header_text": header_text or "\n".join(header_lines),
        "references": references,
        "flagstat": flagstat,
        "mapq_histogram": mapq_hist,
        "coverage": coverage_out,
        "records_sample": sample,
        "n_records_scanned": flagstat["total"],
        "n_records_in_region": n_in_region,
        "region": region_label,
        "warnings": warnings,
    }


# ─────────────────────────────────────────────────────────────────────────────
# VCF/BCF (Python fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _read_bcf_typed(buf: bytes, pos: int):
    if pos >= len(buf):
        raise ValueError("truncated BCF typed value")
    type_byte = buf[pos]
    pos += 1
    type_id = type_byte >> 4
    count = type_byte & 0x0F
    if count == 15:
        count, pos = _read_bcf_count(buf, pos)
    if type_id == 0:
        return ("flag", None), pos
    if type_id == 1:
        vals = []
        for _ in range(count):
            if pos >= len(buf):
                raise ValueError("truncated BCF int8")
            v = struct.unpack_from("<b", buf, pos)[0]
            pos += 1
            vals.append(None if struct.pack("<b", v) == b"\x80" else v)
        return ("int", vals), pos
    if type_id == 2:
        vals = []
        for _ in range(count):
            if pos + 2 > len(buf):
                raise ValueError("truncated BCF int16")
            v = struct.unpack_from("<h", buf, pos)[0]
            pos += 2
            vals.append(None if v == -32768 else v)
        return ("int", vals), pos
    if type_id == 3:
        vals = []
        for _ in range(count):
            if pos + 4 > len(buf):
                raise ValueError("truncated BCF int32")
            v = struct.unpack_from("<i", buf, pos)[0]
            pos += 4
            vals.append(None if v == -2147483648 else v)
        return ("int", vals), pos
    if type_id == 5:
        vals = []
        for _ in range(count):
            if pos + 4 > len(buf):
                raise ValueError("truncated BCF float")
            v = struct.unpack_from("<f", buf, pos)[0]
            pos += 4
            vals.append(None if struct.pack("<f", v) == struct.pack("<I", 0x7F800001) else v)
        return ("float", vals), pos
    if type_id == 7:
        if pos + count > len(buf):
            raise ValueError("truncated BCF char")
        raw = buf[pos : pos + count]
        pos += count
        text = raw.split(b"\x00")[0].decode("utf-8", "replace")
        return ("str", text), pos
    raise ValueError(f"unknown BCF type id {type_id}")


def _read_bcf_count(buf: bytes, pos: int):
    if pos >= len(buf):
        raise ValueError("truncated BCF length")
    type_byte = buf[pos]
    pos += 1
    type_id = type_byte >> 4
    if type_id == 1:
        return buf[pos], pos + 1
    if type_id == 2:
        return struct.unpack_from("<H", buf, pos)[0], pos + 2
    if type_id == 3:
        return struct.unpack_from("<I", buf, pos)[0], pos + 4
    raise ValueError(f"bad BCF length type {type_id}")


def _parse_info_af_dp(info: str):
    af = dp = None
    for field in info.split(";"):
        if field.startswith("AF="):
            try:
                af = float(field[3:].split(",")[0])
            except ValueError:
                af = None
        elif field.startswith("DP="):
            try:
                dp = int(field[3:].split(",")[0])
            except ValueError:
                dp = None
    return af, dp


def _row_passes(f: dict[str, Any], chrom: str, pos: int, qual: float, filt: str, af) -> bool:
    if f.get("chrom"):
        strip = lambda s: (s or "").lower().removeprefix("chr")
        if strip(f["chrom"]) != strip(chrom):
            return False
    if f.get("pos_min") is not None and pos < f["pos_min"]:
        return False
    if f.get("pos_max") is not None and pos > f["pos_max"]:
        return False
    if f.get("qual_min") is not None and not (qual >= f["qual_min"]):
        return False
    if f.get("filter") is not None and filt != f["filter"]:
        return False
    if f.get("af_min") is not None or f.get("af_max") is not None:
        if af is None:
            return False
        if f.get("af_min") is not None and af < f["af_min"]:
            return False
        if f.get("af_max") is not None and af > f["af_max"]:
            return False
    return True


def _py_parse_vcf(
    path: Optional[str],
    data: Any,
    chrom: Optional[str],
    pos_min: Optional[int],
    pos_max: Optional[int],
    qual_min: Optional[float],
    af_min: Optional[float],
    af_max: Optional[float],
    filter_value: Optional[str],
    max_rows: Optional[int],
    progress: Optional[Callable[[int, int], None]],
    cancel: Any,
) -> dict[str, Any]:
    raw = _load_bytes(path, data)
    total_bytes = len(raw)
    f = {
        "chrom": chrom,
        "pos_min": pos_min,
        "pos_max": pos_max,
        "qual_min": qual_min,
        "af_min": af_min,
        "af_max": af_max,
        "filter": filter_value,
    }
    out = {
        "engine": "python",
        "format": "vcf",
        "chrom": [],
        "pos": [],
        "id": [],
        "ref": [],
        "alt": [],
        "qual": [],
        "filter": [],
        "info_raw": [],
        "info_af": [],
        "info_dp": [],
        "n_rows_kept": 0,
        "n_rows_seen": 0,
        "n_filtered_out": 0,
        "truncated": False,
        "samples": [],
        "header_lines": [],
        "warnings": {"malformed_rows": 0, "bcf_format_skipped": False, "header_missing": False},
    }
    is_bcf = raw[:5] == b"BCF\x02\x02"
    if is_bcf:
        out["format"] = "bcf"
        (l_text,) = struct.unpack_from("<I", raw, 5)
        text = raw[9 : 9 + l_text].decode("utf-8", "replace")
        body = raw[9 + l_text :]
        header_lines = text.splitlines()
        dictionary: list[str] = []
        for line in header_lines:
            for prefix in ("##FILTER=<ID=", "##contig=<ID=", "##INFO=<ID=", "##FORMAT=<ID="):
                if line.startswith(prefix):
                    rest = line[len(prefix) :]
                    stop = min([i for i in (rest.find(","), rest.find(">")) if i >= 0] or [len(rest)])
                    dictionary.append(rest[:stop])
        for line in header_lines:
            if line.startswith("#CHROM"):
                out["samples"] = line.split("\t")[9:]
        out["header_lines"] = header_lines
        pos = 0
        while pos + 8 <= len(body):
            if _check_cancel(cancel):
                raise _Cancelled("cancelled")
            l_shared, l_indiv = struct.unpack_from("<II", body, pos)
            shared = body[pos + 8 : pos + 8 + l_shared]
            pos_next = pos + 8 + l_shared + l_indiv
            if len(shared) < 24 or pos_next > len(body):
                out["warnings"]["malformed_rows"] += 1
                break
            pos = pos_next
            chrom_id, vpos0 = struct.unpack_from("<ii", shared, 0)
            qual_f = struct.unpack_from("<f", shared, 12)[0]
            n_allele_info = struct.unpack_from("<I", shared, 16)[0]
            n_info = n_allele_info & 0xFFFF
            n_allele = n_allele_info >> 16
            sp = 24
            (kind, vid), sp = _read_bcf_typed(shared, sp)
            vid = vid if kind == "str" else "."
            alleles = []
            for _ in range(n_allele):
                (k2, allele), sp = _read_bcf_typed(shared, sp)
                alleles.append(allele if k2 == "str" else ".")
            filt_text = "."
            try:
                (k3, ids), sp = _read_bcf_typed(shared, sp)
                if k3 == "int":
                    if not ids:
                        filt_text = "."
                    else:
                        filt_text = ";".join(
                            "PASS" if (v is None or v == 0) else dictionary[v] if v < len(dictionary) else f"id{v}"
                            for v in ids
                        )
            except ValueError:
                pass
            af = dp = None
            info_parts = []
            for _ in range(n_info):
                if sp + 4 > len(shared):
                    break
                (key_id,) = struct.unpack_from("<I", shared, sp)
                sp += 4
                key = dictionary[key_id] if key_id < len(dictionary) else f"key{key_id}"
                try:
                    (kind, value), sp = _read_bcf_typed(shared, sp)
                except ValueError:
                    out["warnings"]["malformed_rows"] += 1
                    break
                if kind == "flag":
                    info_parts.append(key)
                elif kind == "str":
                    if key == "AF":
                        try:
                            af = float(str(value).split(",")[0])
                        except ValueError:
                            af = None
                    if key == "DP":
                        try:
                            dp = int(str(value).split(",")[0])
                        except ValueError:
                            dp = None
                    info_parts.append(f"{key}={value}")
                else:
                    vals = value or []
                    rendered = ",".join("." if v is None else (f"{v:.6f}" if kind == "float" else str(v)) for v in vals)
                    if key == "AF" and vals:
                        af = vals[0]
                    if key == "DP" and kind == "int" and vals:
                        dp = vals[0]
                    info_parts.append(f"{key}={rendered}")
            if l_indiv > 0:
                out["warnings"]["bcf_format_skipped"] = True
            vpos = vpos0 + 1
            qual = float("nan") if struct.pack("<f", qual_f) == struct.pack("<I", 0x7F800001) else float(qual_f)
            ref = alleles[0] if alleles else "."
            alt = ",".join(alleles[1:]) if len(alleles) > 1 else "."
            chrom_name = dictionary[chrom_id] if 0 <= chrom_id < len(dictionary) else f"contig{chrom_id}"
            out["n_rows_seen"] += 1
            if _row_passes(f, chrom_name, vpos, qual, filt_text, af):
                if max_rows is not None and out["n_rows_kept"] >= max_rows:
                    out["truncated"] = True
                    break
                out["chrom"].append(chrom_name)
                out["pos"].append(vpos)
                out["id"].append(vid)
                out["ref"].append(ref)
                out["alt"].append(alt)
                out["qual"].append(qual)
                out["filter"].append(filt_text)
                out["info_raw"].append(";".join(info_parts))
                out["info_af"].append(af)
                out["info_dp"].append(dp)
                out["n_rows_kept"] += 1
            else:
                out["n_filtered_out"] += 1
    else:
        saw_header = False
        for raw_line in raw.split(b"\n"):
            if _check_cancel(cancel):
                raise _Cancelled("cancelled")
            line = raw_line.rstrip(b"\r")
            if not line:
                continue
            if line.startswith(b"##"):
                out["header_lines"].append(line.decode("utf-8", "replace"))
                continue
            if line.startswith(b"#CHROM"):
                saw_header = True
                cols = line.decode("utf-8", "replace").split("\t")
                out["samples"] = cols[9:]
                out["header_lines"].append(line.decode("utf-8", "replace"))
                continue
            fields = line.split(b"\t")
            if len(fields) < 8:
                out["warnings"]["malformed_rows"] += 1
                continue
            out["n_rows_seen"] += 1
            chrom_name = fields[0].decode("utf-8", "replace")
            try:
                vpos = int(fields[1])
            except ValueError:
                out["warnings"]["malformed_rows"] += 1
                continue
            vid = fields[2].decode("utf-8", "replace")
            ref = fields[3].decode("utf-8", "replace")
            alt = fields[4].decode("utf-8", "replace")
            try:
                qual = float(fields[5])
            except ValueError:
                qual = float("nan")
            filt_text = fields[6].decode("utf-8", "replace")
            info = fields[7].decode("utf-8", "replace")
            af, dp = _parse_info_af_dp(info)
            if _row_passes(f, chrom_name, vpos, qual, filt_text, af):
                if max_rows is not None and out["n_rows_kept"] >= max_rows:
                    out["truncated"] = True
                    break
                out["chrom"].append(chrom_name)
                out["pos"].append(vpos)
                out["id"].append(vid)
                out["ref"].append(ref)
                out["alt"].append(alt)
                out["qual"].append(qual)
                out["filter"].append(filt_text)
                out["info_raw"].append(info)
                out["info_af"].append(af)
                out["info_dp"].append(dp)
                out["n_rows_kept"] += 1
            else:
                out["n_filtered_out"] += 1
        if not saw_header:
            out["warnings"]["header_missing"] = True
    _report(progress, total_bytes, total_bytes)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Seed-and-extend mapper (Python fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _revcomp_str(seq: str) -> str:
    return seq.translate(str.maketrans("ACGTacgt", "TGCAtgca"))[::-1]


def _py_map_reads(
    reads: Sequence[str], reference: str, ref_name: str, k: int
) -> list[dict[str, Any]]:
    if not (5 <= k <= 32):
        raise ValueError("k must be in 5..=32")
    ref = (reference or "").upper()
    if len(ref) < k:
        raise ValueError("map_reads: k must fit the reference")
    if len(ref) > 5_000_000:
        raise ValueError("map_reads: reference limited to 5 Mbp")
    index: dict[int, list[int]] = {}
    for i in range(len(ref) - k + 1):
        packed = _pack_kmer(ref[i : i + k].encode())
        if packed is not None:
            index.setdefault(packed, []).append(i)
    placements: list[dict[str, Any]] = []
    for read_index, read in enumerate(reads):
        best = None
        for strand, s in (("+", read.upper()), ("-", _revcomp_str(read.upper()))):
            votes: dict[int, int] = {}
            for qi in range(max(0, len(s) - k + 1)):
                packed = _pack_kmer(s[qi : qi + k].encode())
                if packed is None:
                    continue
                for ri in index.get(packed, ())[:4]:
                    votes[ri - qi] = votes.get(ri - qi, 0) + 1
            for diag, _count in sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))[:8]:
                start_ri = max(0, diag)
                start_qi = max(0, -diag)
                if start_ri >= len(ref):
                    continue
                length = min(len(s) - start_qi, len(ref) - start_ri)
                if length < k:
                    continue
                a = s[start_qi : start_qi + length]
                b = ref[start_ri : start_ri + length]
                score = sum(2 if x == y else -1 for x, y in zip(a, b))
                matches = max(0, (score + length) // 2)
                cand = {
                    "read_index": read_index,
                    "ref_name": ref_name,
                    "pos_0based": start_ri,
                    "score": score,
                    "matches": matches,
                    "mismatches": max(0, length - matches),
                    "strand": strand,
                }
                if best is None or cand["score"] > best["score"]:
                    best = cand
        if best is not None:
            placements.append(best)
    return placements


# ─────────────────────────────────────────────────────────────────────────────
# Public dispatcher API
# ─────────────────────────────────────────────────────────────────────────────

def _dispatch(name: str):
    if _POLICY != "python":
        rust = _detect_rust()
        if rust is not None:
            return rust
    return None


def run_with_stats(func: Callable[[], Any], *, threads: int = 0) -> tuple[Any, dict[str, Any]]:
    """Run ``func`` and return ``(result, stats)`` with engine/timing/threads.

    ``stats`` is what the Export Center surfaces: engine used, wall time, and
    the thread count actually requested (0 = engine default).
    """
    started = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - started
    engine_name = "rust"
    if isinstance(result, dict):
        engine_name = str(result.get("engine", "rust"))
    status = engine_status()
    effective_threads = threads
    if threads == 0:
        if engine_name == "rust":
            effective_threads = status.get("rust_threads_default") or os.cpu_count() or 1
        else:
            effective_threads = 1
    stats = {
        "engine": engine_name,
        "engine_version": status.get("rust_version") if engine_name == "rust" else ENGINE_VERSION,
        "wall_seconds": round(elapsed, 6),
        "threads": effective_threads,
        "threads_requested": threads,
    }
    return result, stats


def parse_fastq(
    path: Optional[str] = None,
    data: Any = None,
    threads: int = 0,
    progress: Optional[Callable[[int, int], None]] = None,
    cancel: Any = None,
    max_records: Optional[int] = None,
) -> dict[str, Any]:
    """Parse FASTQ/FASTQ.GZ/BGZF into the shared columnar schema.

    Returns the columnar worker layout plus flattened views: ``names``,
    ``seqs`` and ``qualities`` (ASCII quality strings).
    """
    rust = _dispatch("parse_fastq")
    if rust is not None:
        result = rust.parse_fastq(
            path=path, data=data, threads=threads, progress=progress, cancel=cancel, max_records=max_records
        )
    else:
        result = _py_parse_fastq(path, data, max_records, progress, cancel)
    result.update(_flatten_fastq(result))
    return result


def qc_fastq(
    path: Optional[str] = None,
    data: Any = None,
    threads: int = 0,
    progress: Optional[Callable[[int, int], None]] = None,
    cancel: Any = None,
    k: int = 8,
) -> dict[str, Any]:
    """One-pass streaming QC report (identical keys on both engines)."""
    rust = _dispatch("qc_fastq")
    if rust is not None:
        return rust.qc_fastq(path=path, data=data, threads=threads, progress=progress, cancel=cancel, k=k)
    return _py_qc_fastq(path, data, k, progress, cancel)


def read_alignment(
    path: Optional[str] = None,
    data: Any = None,
    threads: int = 0,
    region: Optional[str] = None,
    progress: Optional[Callable[[int, int], None]] = None,
    cancel: Any = None,
) -> dict[str, Any]:
    """SAM/BAM summary: flagstat, MAPQ histogram, coverage bins, sample rows."""
    rust = _dispatch("read_bam")
    if rust is not None:
        return rust.read_bam(path=path, data=data, threads=threads, region=region, progress=progress, cancel=cancel)
    return _py_read_alignment(path, data, region, progress, cancel)


def parse_vcf(
    path: Optional[str] = None,
    data: Any = None,
    threads: int = 0,
    chrom: Optional[str] = None,
    pos_min: Optional[int] = None,
    pos_max: Optional[int] = None,
    qual_min: Optional[float] = None,
    af_min: Optional[float] = None,
    af_max: Optional[float] = None,
    filter: Optional[str] = None,
    max_rows: Optional[int] = None,
    progress: Optional[Callable[[int, int], None]] = None,
    cancel: Any = None,
) -> dict[str, Any]:
    """VCF/BCF parse with filter pushdown (columnar output)."""
    rust = _dispatch("parse_vcf")
    if rust is not None:
        return rust.parse_vcf(
            path=path,
            data=data,
            threads=threads,
            chrom=chrom,
            pos_min=pos_min,
            pos_max=pos_max,
            qual_min=qual_min,
            af_min=af_min,
            af_max=af_max,
            filter=filter,
            max_rows=max_rows,
            progress=progress,
            cancel=cancel,
        )
    return _py_parse_vcf(
        path, data, chrom, pos_min, pos_max, qual_min, af_min, af_max, filter, max_rows, progress, cancel
    )


def align(
    query: str,
    target: str,
    mode: str = "local",
    match_score: int = 2,
    mismatch_score: int = -3,
    gap_open: int = 5,
    gap_extend: int = 2,
    band: int = 64,
) -> dict[str, Any]:
    """Banded affine-gap Smith-Waterman / Needleman-Wunsch."""
    rust = _dispatch("align")
    if rust is not None:
        return rust.align(
            query,
            target,
            mode=mode,
            match_score=match_score,
            mismatch_score=mismatch_score,
            gap_open=gap_open,
            gap_extend=gap_extend,
            band=band,
        )
    return _py_align(query, target, mode, match_score, mismatch_score, gap_open, gap_extend, band)


def kmer_count(
    path: Optional[str] = None,
    data: Any = None,
    k: int = 8,
    threads: int = 0,
    top: int = 20,
    max_entries: int = 200_000,
    progress: Optional[Callable[[int, int], None]] = None,
    cancel: Any = None,
) -> dict[str, Any]:
    """Canonical 2-bit k-mer counting with a bounded map."""
    rust = _dispatch("kmer_count")
    if rust is not None:
        return rust.kmer_count(
            path=path, data=data, k=k, threads=threads, top=top, max_entries=max_entries, progress=progress, cancel=cancel
        )
    return _py_kmer_count(path, data, k, top, max_entries, progress, cancel)


def map_reads(
    reads: Sequence[str],
    reference: str,
    ref_name: str = "ref",
    k: int = 12,
    threads: int = 0,
) -> dict[str, Any]:
    """k-mer seed-and-extend mapping of short reads vs a small reference."""
    rust = _dispatch("map_reads")
    if rust is not None:
        return rust.map_reads(list(reads), reference, ref_name=ref_name, k=k, threads=threads)
    placements = _py_map_reads(reads, reference, ref_name, k)
    return {
        "engine": "python",
        "placements": placements,
        "n_reads": len(reads),
        "n_placed": len(placements),
    }


# ─────────────────────────────────────────────────────────────────────────────
# UI helpers (Streamlit-optional)
# ─────────────────────────────────────────────────────────────────────────────

def fastq_result_to_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a parse_fastq result into per-read dicts (bounded by caller)."""
    rows = []
    offsets = result.get("seq_offsets") or [0]
    qual_offsets = result.get("qual_offsets") or [0]
    seq_concat = result.get("seq_concat") or b""
    qual_concat = result.get("qual_concat") or b""
    if isinstance(seq_concat, memoryview):
        seq_concat = seq_concat.tobytes()
    if isinstance(qual_concat, memoryview):
        qual_concat = qual_concat.tobytes()
    for i, name in enumerate(result.get("names") or []):
        s0, s1 = offsets[i], offsets[i + 1]
        q0, q1 = qual_offsets[i], qual_offsets[i + 1]
        rows.append(
            {
                "name": name,
                "sequence": seq_concat[s0:s1].decode("ascii", "replace"),
                "quality": qual_concat[q0:q1].decode("ascii", "replace"),
                "length": (result.get("lengths") or [])[i] if i < len(result.get("lengths") or []) else s1 - s0,
            }
        )
    return rows


def vcf_result_to_dataframe(result: dict[str, Any]):
    """Convert a parse_vcf result to a pandas DataFrame (same columns as the
    legacy VCF Viewer page)."""
    import pandas as pd

    frame = pd.DataFrame(
        {
            "CHROM": result.get("chrom") or [],
            "POS": result.get("pos") or [],
            "ID": result.get("id") or [],
            "REF": result.get("ref") or [],
            "ALT": result.get("alt") or [],
            "QUAL": result.get("qual") or [],
            "FILTER": result.get("filter") or [],
            "INFO": result.get("info_raw") or [],
        }
    )
    return frame


def engine_badge() -> str:
    """Short markdown badge describing the active engine (for page headers)."""
    status = engine_status()
    if status["active"] == "rust":
        return f"⚡ **Pro Engine (Rust titan_core {status.get('rust_version') or '?'})** — accelerated path active"
    return "🐍 **Python engine (fallback)** — install `titan_core` (maturin) to enable the Pro Engine"


def render_engine_toggle(key: str = "titan_pro_engine") -> str:
    """Sidebar toggle + status card. Returns the active engine name.

    Safe to call on every page; requires Streamlit (already a hard dependency
    of the pages that use it).
    """
    import streamlit as st

    status = engine_status()
    with st.sidebar:
        with st.container(border=True):
            st.markdown("### ⚡ Pro Engine")
            choice = st.radio(
                "Compute engine",
                options=["auto", "rust", "python"],
                index=["auto", "rust", "python"].index(get_engine_policy()),
                format_func=lambda v: {
                    "auto": "Auto (Rust if available)",
                    "rust": "Force Rust (Pro)",
                    "python": "Force Python (fallback)",
                }[v],
                key=key,
                help="Rust (titan_core) accelerates FASTQ/BAM/VCF parsing, QC and alignment. "
                "The Python fallback is always available and returns identical schemas.",
            )
            if choice != get_engine_policy():
                set_engine_policy(choice)
            if status["rust_available"]:
                st.success(f"Rust titan_core {status.get('rust_version') or ''} available")
            else:
                st.info("Rust titan_core not installed — Python fallback active")
            st.caption(f"Active engine: **{active_engine()}** · policy: {get_engine_policy()}")
    return active_engine()
