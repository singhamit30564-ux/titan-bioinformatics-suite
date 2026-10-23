"""Tests for titan_utils.engine — dispatcher, schemas, and the pure-Python
fallback path (with ``titan_core`` mocked as missing).

The fallback MUST produce the same schema keys as the Rust engine so pages can
switch engines without code changes.
"""
from __future__ import annotations

import gzip
import io
import sys

import pytest

from titan_utils import engine


FASTQ = b"""@read1 desc
ACGTACGTACGTACGTACGT
+
IIIIIIIIIIIIIIIIIIII
@read2
GCGCGCGCGCGCGCGCGCGC
+
55555555555555555555
"""

# read2 has 7 quality bytes for 8 bases → malformed (dropped + counted).
MALFORMED_FASTQ = b"""@ok
ACGTACGT
+
IIIIIIII
@bad
ACGTACGT
+
IIIIIII
"""

SAM = b"""@HD\tVN:1.6
@SQ\tSN:chr1\tLN:1000
r1\t0\tchr1\t100\t60\t10M\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII
r2\t4\t*\t0\t0\t*\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII
r3\t0\tchr1\t500\t30\t5M5M\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII
"""

VCF = b"""##fileformat=VCFv4.2
##INFO=<ID=DP,Number=1,Type=Integer,Description="d">
##INFO=<ID=AF,Number=A,Type=Float,Description="af">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t100\trs1\tA\tG\t50\tPASS\tDP=30;AF=0.25
chr1\t150\trs2\tC\tT\t45\tPASS\tDP=25;AF=0.01
chr2\t50\trs3\tG\tGAT\t60\tLowQual\tDP=40;AF=0.9
"""

PARSE_KEYS = {
    "engine", "n_reads", "names", "seq_concat", "seq_offsets", "qual_concat",
    "qual_offsets", "lengths", "phred_encoding", "truncated", "warnings", "bytes_total",
}
QC_KEYS = {
    "engine", "n_reads", "total_bases", "length_min", "length_max", "length_mean",
    "length_histogram", "gc_percent", "n_content_percent", "per_base_mean_quality",
    "q20_percent", "q30_percent", "phred_encoding", "duplication",
    "overrepresented_kmers", "adapter_hits", "empty_reads", "warnings",
}
ALIGN_KEYS = {
    "engine", "score", "cigar", "q_start", "q_end", "t_start", "t_end", "matches",
    "aln_columns", "identity_percent", "aligned_query", "aligned_target",
    "display_capped", "mode", "simd_extension",
}
BAM_KEYS = {
    "engine", "format", "header_text", "references", "flagstat", "mapq_histogram",
    "coverage", "records_sample", "n_records_scanned", "n_records_in_region",
    "region", "warnings",
}
VCF_KEYS = {
    "engine", "format", "chrom", "pos", "id", "ref", "alt", "qual", "filter",
    "info_raw", "info_af", "info_dp", "n_rows_kept", "n_rows_seen",
    "n_filtered_out", "truncated", "samples", "header_lines", "warnings",
}
KMER_KEYS = {
    "engine", "k", "total_kmers", "unique_kmers", "distinct_estimate", "truncated",
    "top_kmers",
}


@pytest.fixture()
def python_only(monkeypatch):
    """Force the pure-Python fallback (titan_core mocked as missing)."""
    monkeypatch.setitem(sys.modules, "titan_core", None)
    monkeypatch.setattr(engine, "_RUST", None, raising=False)
    monkeypatch.setattr(engine, "_RUST_TRIED", False, raising=False)
    monkeypatch.setattr(engine, "_POLICY", "auto")
    yield
    engine.refresh_engine()


@pytest.fixture()
def any_engine():
    yield
    engine.refresh_engine()


def test_engine_status_shape(any_engine):
    status = engine.engine_status()
    assert status["python_fallback"] is True
    assert status["active"] in {"rust", "python"}
    assert isinstance(status["rust_available"], bool)


def test_policy_forces_python(python_only):
    assert engine.active_engine() == "python"
    result = engine.parse_fastq(data=FASTQ)
    assert result["engine"] == "python"


def test_python_parse_fastq_schema(python_only):
    result = engine.parse_fastq(data=FASTQ)
    assert PARSE_KEYS <= set(result)
    assert result["n_reads"] == 2
    assert result["lengths"] == [20, 20]
    assert result["seq_offsets"] == [0, 20, 40]
    assert result["phred_encoding"] == "phred33"
    assert result["warnings"]["malformed_records"] == 0


def test_malformed_fastq_is_counted_not_fatal(python_only):
    result = engine.parse_fastq(data=MALFORMED_FASTQ)
    assert result["n_reads"] == 1
    # A short trailing quality line at EOF is reported as a truncated record;
    # mid-stream mismatches report as malformed. Either way, never fatal.
    warnings = result["warnings"]
    assert warnings["malformed_records"] + warnings["truncated_records"] >= 1


def test_parse_fastq_from_path(tmp_path, python_only):
    path = tmp_path / "x.fastq"
    path.write_bytes(FASTQ)
    result = engine.parse_fastq(path=str(path))
    assert result["n_reads"] == 2


def test_parse_fastq_gzip_roundtrip(python_only):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write(FASTQ)
    result = engine.parse_fastq(data=buf.getvalue())
    assert result["n_reads"] == 2


def test_python_qc_schema_and_numbers(python_only):
    result = engine.qc_fastq(data=FASTQ)
    assert QC_KEYS <= set(result)
    assert result["n_reads"] == 2
    assert result["total_bases"] == 40
    assert result["length_min"] == 20
    assert abs(result["gc_percent"] - 75.0) < 1e-6  # 30 GC of 40 bases
    assert result["q20_percent"] > 50.0
    assert result["duplication"]["duplication_rate_percent"] >= 0.0
    assert isinstance(result["length_histogram"], list)


def test_python_align_schema(python_only):
    result = engine.align("ACGTACGT", "TTACGTACGTAA", mode="local")
    assert ALIGN_KEYS <= set(result)
    assert result["score"] >= 16
    assert result["matches"] == 8
    global_result = engine.align("ACGTACGT", "ACGTACGT", mode="global")
    assert global_result["cigar"] == "8M"
    assert global_result["score"] == 16


def test_python_kmer_count(python_only):
    result = engine.kmer_count(data=b"ACGTACGTACGT", k=3)
    assert KMER_KEYS <= set(result)
    assert result["total_kmers"] == 10
    assert result["unique_kmers"] >= 2


def test_python_read_alignment_sam(python_only):
    result = engine.read_alignment(data=SAM)
    assert BAM_KEYS <= set(result)
    assert result["format"] == "sam"
    assert result["flagstat"]["total"] == 3
    assert result["flagstat"]["mapped"] == 2
    assert result["n_records_in_region"] == 3  # no region → all rows pass
    regioned = engine.read_alignment(data=SAM, region="chr1:1-200")
    assert regioned["n_records_in_region"] == 1


def test_python_parse_vcf_schema_and_pushdown(python_only):
    result = engine.parse_vcf(data=VCF)
    assert VCF_KEYS <= set(result)
    assert result["n_rows_kept"] == 3
    filtered = engine.parse_vcf(data=VCF, chrom="chr2", af_min=0.5)
    assert filtered["n_rows_kept"] == 1
    assert filtered["n_filtered_out"] == 2


def test_python_map_reads(python_only):
    reference = "ACGTTGCAAGGCTTACGATCGATCGGATCCTTAGGCATCAGTCAAGTTACCGGAT"
    read = reference[10:30]
    result = engine.map_reads([read], reference, k=12)
    assert result["n_placed"] == 1
    assert result["placements"][0]["pos_0based"] == 10
    assert result["placements"][0]["strand"] == "+"


def test_cancel_token_stops_parse(python_only):
    token = engine.PythonCancelToken()
    token.cancel()
    with pytest.raises(engine._Cancelled):
        engine.parse_fastq(data=FASTQ, cancel=token)


def test_run_with_stats_reports_engine(python_only):
    result, stats = engine.run_with_stats(lambda: engine.parse_fastq(data=FASTQ), threads=4)
    assert stats["engine"] == "python"
    assert stats["threads"] == 4
    assert stats["wall_seconds"] >= 0.0


def test_bytes_and_path_are_mutually_exclusive(python_only):
    with pytest.raises(ValueError):
        engine.parse_fastq(path="x", data=b"@a\nA\n+\nI\n")


def test_rust_engine_used_when_available(monkeypatch):
    """When titan_core imports, the dispatcher must route to it."""

    class FakeRust:
        @staticmethod
        def parse_fastq(**kwargs):
            return {"engine": "rust", "n_reads": 0}

        @staticmethod
        def qc_fastq(**kwargs):
            return {"engine": "rust", "n_reads": 0}

        @staticmethod
        def engine_info():
            return {"version": "0.0-test", "rayon_threads": 4, "features": []}

    monkeypatch.setitem(sys.modules, "titan_core", FakeRust)
    monkeypatch.setattr(engine, "_RUST", None, raising=False)
    monkeypatch.setattr(engine, "_RUST_TRIED", False, raising=False)
    monkeypatch.setattr(engine, "_POLICY", "auto")
    assert engine.active_engine() == "rust"
    result = engine.parse_fastq(data=FASTQ)
    assert result["engine"] == "rust"
    status = engine.engine_status()
    assert status["rust_version"] == "0.0-test"
    engine.refresh_engine()


def test_schemas_match_across_engines_when_rust_present():
    """If the real extension is installed, compare schema keys across engines."""
    status = engine.engine_status()
    if not status["rust_available"]:
        pytest.skip("titan_core extension not installed in this environment")
    rust_result = engine.parse_fastq(data=FASTQ)
    engine.set_engine_policy("python")
    try:
        py_result = engine.parse_fastq(data=FASTQ)
    finally:
        engine.set_engine_policy("auto")
    assert set(rust_result) == set(py_result)
    assert rust_result["n_reads"] == py_result["n_reads"]
    assert rust_result["lengths"] == py_result["lengths"]
    assert rust_result["seq_concat"] == py_result["seq_concat"]


def test_fastq_numpy_views_are_zero_copy():
    """np.frombuffer views over the concatenated buffers — no copies made."""
    import numpy as np

    fastq = "@r1\nACGTACGTAC\n+\nIIIIIIIIII\n@r2\nTTTTGGGGCC\n+\nAAAAAAAAAA\n"
    parsed = engine.parse_fastq(data=fastq)
    views = engine.fastq_numpy_views(parsed)
    assert views["n_reads"] == 2
    assert isinstance(views["seq_bases"], np.ndarray)
    assert views["seq_bases"].dtype == np.uint8
    # zero-copy: the view shares memory with the underlying buffer
    assert views["seq_bases"].base is not None or views["seq_bases"].flags["OWNDATA"] is False
    # offsets slice per read
    s0, s1 = views["seq_offsets"][0], views["seq_offsets"][1]
    assert bytes(views["seq_bases"][s0:s1]).decode() == parsed["seqs"][0]
    assert list(views["lengths"]) == [10, 10]


def test_log_redaction_strips_sequence_tokens():
    from titan_utils.api import _redact_sequence_tokens, _TitanLogFilter
    import logging

    seq = "ACGT" * 20  # 80 nt — sequence-like
    message = f"user pasted {seq} into input"
    redacted = _redact_sequence_tokens(message)
    assert seq not in redacted
    assert "<sequence-redacted>" in redacted
    short = "ACGT"  # not sequence-like at 4 nt
    assert _redact_sequence_tokens(short) == short

    record = logging.LogRecord("titan.test", logging.INFO, __file__, 1, message, (), None)
    assert _TitanLogFilter().filter(record) is True
    assert seq not in record.getMessage()
