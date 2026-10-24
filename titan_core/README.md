# titan_core — native processing core (Layer A)

Rust (PyO3 + maturin) acceleration for the Titan Bioinformatics Suite.

## What lives here

| Module        | Responsibility                                                                    |
|---------------|-----------------------------------------------------------------------------------|
| `bgzf.rs`     | gzip / BGZF (multi-member) decompression; multithreaded over independent BGZF blocks |
| `fastq.rs`    | mmap + chunked parallel FASTQ/FASTQ.GZ/BGZF parsing, CRLF / truncated / malformed-tolerant |
| `qc.rs`       | one-pass streaming QC (per-base quality, GC%, length histogram, N-content, adapters, over-represented k-mers, duplication estimate) |
| `hll.rs`      | HyperLogLog (14-bit) cardinality estimation for duplication / distinct k-mers     |
| `bloom.rs`    | Bloom filter used for streaming duplicate detection                                |
| `bam.rs`      | SAM text + BAM binary decode, region queries, coverage tracks, MAPQ / flagstat    |
| `vcf.rs`      | streaming VCF / BCF parser with typed INFO/FORMAT and filter pushdown, columnar out |
| `align.rs`    | banded Smith-Waterman / Needleman-Wunsch with affine gaps (SIMD-friendly inner loop, AVX2 fast path), k-mer seed-and-extend short-read mapper |
| `kmer.rs`     | canonical 2-bit packed k-mer counting                                              |
| `lib.rs`      | PyO3 bindings: `parse_fastq`, `qc_fastq`, `read_bam`, `parse_vcf`, `align`, `kmer_count`, `engine_info`, `CancelToken` |

## Design rules

1. **ZDR-safe**: every entry point accepts `bytes` as well as `path`. Bytes-in /
   bytes-out means no temp files ever touch the disk.
2. **GIL released** for the whole compute phase (`Python::allow_threads`).
3. **Configurable threads** (`threads = 0` → rayon default pool).
4. **Progress + cancellation**: chunked work checks an `Arc<AtomicBool>` cancel
   token and reports progress via a Python callback between chunks (callback is
   invoked with the GIL held, never from worker threads).
5. **Deterministic output**: chunk results are merged in input order.
6. **Python fallback is mandatory**: `titan_utils/engine.py` reimplements every
   schema in pure Python and is used automatically when this extension is not
   installed. The app must never crash because `titan_core` is missing.

## Why a self-contained BAM/BCF decoder (not noodles / rust-htslib)

* `rust-htslib` needs a C toolchain + libclang + htslib at build time, which
  breaks the single-`cargo build` story and the Android/WASM cross targets.
* `noodles` is excellent but pulls a large dependency tree and its API moves
  quickly; pinning it blind (without a lockfile checked in) risks breaking CI.
* The BGZF + BAM record layout and the VCF/BCF codecs are small, stable and
  fully specified; a compact decoder here keeps the wheel small and makes the
  bytes-in/bytes-out ZDR path trivial.

The decode surface exposed to Python matches the fallback schemas exactly, so
this is an internal implementation choice, not a compatibility surface.

## Build

```bash
pip install maturin
maturin develop --release          # installs the `titan_core` module into the active venv
cargo test --no-default-features   # unit + proptest fuzz tests (links rlib, no libpython)
cargo bench --no-default-features  # criterion benches (see benches/)
```

`--no-default-features` disables `pyo3/extension-module` so test and bench
binaries can link; the wheel built by `maturin` uses the default features.

## Status honesty

This crate is complete source. Whether it has been compiled / benched in a given
environment is reported by `scripts/benchmark.py` (rows are marked MEASURED or
EXPECTED/NOT MEASURED — numbers are never invented).
