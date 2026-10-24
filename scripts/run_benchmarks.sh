#!/usr/bin/env bash
# Build the Rust extension (if cargo is available) and run the benchmark
# harness at 1M / 10M / 50M reads. Numbers in the output are MEASURED only.
set -euo pipefail
cd "$(dirname "$0")/.."

if command -v cargo >/dev/null 2>&1; then
  echo "[bench] building titan_core (maturin develop --release)"
  python -m maturin develop --release -m titan_core/Cargo.toml
else
  echo "[bench] cargo not found — benchmarking the pure-Python fallback" >&2
fi

python scripts/benchmark.py --sizes 1000000 10000000 50000000 --out "docs/benchmarks-$(date -u +%Y%m%d).md"
echo "[bench] done"
