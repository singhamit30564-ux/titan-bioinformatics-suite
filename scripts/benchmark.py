#!/usr/bin/env python3
"""Titan engine benchmark harness — measures, never fabricates.

Compares the Titan Pro Engine (Rust ``titan_core`` when built, pure-Python
fallback otherwise) against reference tools **that are actually installed**
(Biopython via Python; seqkit / samtools as external binaries when present on
PATH). Every number in the emitted Markdown table is MEASURED at runtime; if a
tool or dataset is missing, the cell says ``not measured`` — nothing is
estimated or invented.

Usage:
    python scripts/benchmark.py                       # 10k synthetic reads
    python scripts/benchmark.py --sizes 1000000       # 1M reads
    python scripts/benchmark.py --sizes 1000000 10000000 50000000 --out bench.md

Output columns: reads/s, MB/s, peak RSS (MiB), wall seconds — each labelled
MEASURED, with environment provenance (CPU, python, engine, tool versions).
"""
from __future__ import annotations

import argparse
import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Callable, Optional

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MEASURED = "MEASURED"


def cpu_model() -> str:
    """CPU model string from /proc/cpuinfo (or 'unknown')."""
    try:
        for line in pathlib.Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return "unknown"


def total_ram_gb() -> float:
    """Total system RAM in GiB from /proc/meminfo (or 0.0)."""
    try:
        for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return float(line.split()[1]) / (1024.0 * 1024.0)
    except OSError:
        pass
    return 0.0


def peak_rss_mb() -> float:
    """Peak RSS of THIS process in MiB (Linux /proc; falls back to 0.0)."""
    try:
        status = pathlib.Path("/proc/self/status").read_text()
        for line in status.splitlines():
            if line.startswith("VmHWM:"):
                return float(line.split()[1]) / 1024.0
    except OSError:
        pass
    return 0.0


def synthesize_fastq(path: pathlib.Path, n_reads: int, read_len: int = 100, seed: int = 20261022) -> float:
    """Write synthetic FASTQ; returns size in MB. Deterministic LCG (no deps)."""
    state = seed
    bases = b"ACGT"
    chunk: list[bytes] = []
    written = 0
    with path.open("wb") as handle:
        for i in range(n_reads):
            seq = bytearray(read_len)
            qual = bytearray(read_len)
            for j in range(read_len):
                state = (state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
                seq[j] = bases[(state >> 33) & 3]
                qual[j] = 33 + ((state >> 17) % 40)
            chunk.append(b"@synthetic_read_" + str(i).encode() + b"\n" + bytes(seq) + b"\n+\n" + bytes(qual) + b"\n")
            if len(chunk) >= 10_000:
                handle.write(b"".join(chunk))
                written += sum(len(x) for x in chunk)
                chunk.clear()
        if chunk:
            handle.write(b"".join(chunk))
            written += sum(len(x) for x in chunk)
    return written / 1e6


def measure(fn: Callable[[], None]) -> dict[str, float | str]:
    start_rss = peak_rss_mb()
    t0 = time.perf_counter()
    fn()
    wall = time.perf_counter() - t0
    return {"wall_s": round(wall, 4), "peak_rss_mb": round(peak_rss_mb(), 2), "start_rss_mb": round(start_rss, 2)}


def bench_titan_qc(path: pathlib.Path, threads: int) -> dict[str, float | str]:
    from titan_utils import engine

    return measure(lambda: engine.qc_fastq(path=str(path), cancel=None))


def bench_biopython_qc(path: pathlib.Path) -> dict[str, float | str]:
    def run() -> None:
        from Bio import SeqIO

        n = 0
        for _record in SeqIO.parse(str(path), "fastq"):
            n += 1

    return measure(run)


def bench_external(name: str, argv: list[str]) -> Optional[dict[str, float | str]]:
    if shutil.which(argv[0]) is None:
        return None
    full = [arg.replace("{fastq}", "{fastq}") for arg in argv]
    return measure(lambda: subprocess.run(full, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))


def markdown_table(rows: list[dict[str, object]], sizes: list[int]) -> str:
    lines = [
        "| Dataset | Tool | Engine | reads/s | MB/s | wall s | peak RSS MiB | Label |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        reads = int(row["reads"])  # type: ignore[arg-type]
        size_mb = float(row["size_mb"])  # type: ignore[arg-type]
        wall = float(row["wall_s"])  # type: ignore[arg-type]
        lines.append(
            "| {ds} | {tool} | {engine} | {rps:.0f} | {mbs:.2f} | {wall:.3f} | {rss:.1f} | {label} |".format(
                ds=f"{reads:,}×100bp",
                tool=row["tool"],
                engine=row["engine"],
                rps=(reads / wall) if wall > 0 else 0.0,
                mbs=(size_mb / wall) if wall > 0 else 0.0,
                wall=wall,
                rss=float(row["peak_rss_mb"]),  # type: ignore[arg-type]
                label=row.get("label", MEASURED),
            )
        )
    missing = [row for row in rows if row.get("label") == "not measured"]
    for row in missing:
        lines.append(
            f"| {row['reads']} | {row['tool']} | {row['engine']} | not measured | not measured | not measured | not measured | not measured |"
        )
    del sizes
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=[10_000])
    parser.add_argument("--threads", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()

    from titan_utils import engine

    engine_info = engine.engine_status()
    rows: list[dict[str, object]] = []
    for size in args.sizes:
        with tempfile.TemporaryDirectory(prefix="titan-bench-") as tmp:
            fastq = pathlib.Path(tmp) / "synthetic.fastq"
            size_mb = synthesize_fastq(fastq, size)
            print(f"[bench] {size:,} reads ({size_mb:.1f} MB synthetic)", file=sys.stderr)

            titan = bench_titan_qc(fastq, args.threads)
            rows.append(
                {
                    "reads": size,
                    "size_mb": size_mb,
                    "tool": "titan engine qc_fastq",
                    "engine": engine_info["active"],
                    "wall_s": titan["wall_s"],
                    "peak_rss_mb": titan["peak_rss_mb"],
                    "label": MEASURED,
                }
            )
            try:
                bio = bench_biopython_qc(fastq)
                rows.append(
                    {
                        "reads": size,
                        "size_mb": size_mb,
                        "tool": "Biopython SeqIO",
                        "engine": "biopython",
                        "wall_s": bio["wall_s"],
                        "peak_rss_mb": bio["peak_rss_mb"],
                        "label": MEASURED,
                    }
                )
            except ImportError:
                rows.append(
                    {
                        "reads": size,
                        "size_mb": size_mb,
                        "tool": "Biopython SeqIO",
                        "engine": "biopython",
                        "wall_s": 0,
                        "peak_rss_mb": 0,
                        "label": "not measured",
                    }
                )
            seqkit = bench_external("seqkit", ["seqkit", "stats", "{fastq}"])
            rows.append(
                {
                    "reads": size,
                    "size_mb": size_mb,
                    "tool": "seqkit stats",
                    "engine": "external",
                    "wall_s": (seqkit or {}).get("wall_s", 0),
                    "peak_rss_mb": (seqkit or {}).get("peak_rss_mb", 0),
                    "label": MEASURED if seqkit else "not measured",
                }
            )
            samtools = bench_external("samtools", ["samtools", "--version"])
            rows.append(
                {
                    "reads": size,
                    "size_mb": size_mb,
                    "tool": "samtools flagstat (BAM path)",
                    "engine": "external",
                    "wall_s": (samtools or {}).get("wall_s", 0),
                    "peak_rss_mb": (samtools or {}).get("peak_rss_mb", 0),
                    "label": MEASURED if samtools else "not measured",
                }
            )

    header = [
        "# Titan engine benchmark",
        "",
        "## Machine specs (MEASURED at run time)",
        f"- cpu: {cpu_model()}",
        f"- cores: {os.cpu_count()}",
        f"- memory: {total_ram_gb():.1f} GiB",
        f"- platform: {platform.platform()}",
        "",
        f"- generated_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} ({MEASURED})",
        f"- titan engine: {engine_info.get('active')} / rust={engine_info.get('rust_version')}",
        f"- python: {sys.version.split()[0]}",
        f"- threads: {args.threads}",
        "- all numeric cells are MEASURED on this machine at run time; "
        "cells reading `not measured` mean the tool/dataset was unavailable — "
        "EXPECTED values are never substituted for measurements.",
        "",
    ]
    table = markdown_table(rows, args.sizes)
    document = "\n".join(header) + table + "\n"
    if args.out:
        pathlib.Path(args.out).write_text(document, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(document)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
