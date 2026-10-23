#!/usr/bin/env bash
# Devcontainer post-create: Python + R + Rust + Node bootstrapping.
set -euo pipefail

echo "[devcontainer] Python core dependencies"
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-optional.txt || echo "[devcontainer] optional heavy stacks unavailable — fallbacks active"

echo "[devcontainer] Python dev tooling"
pip install pytest pyflakes maturin httpx

echo "[devcontainer] R packages for the DE bridge (best effort)"
Rscript -e 'install.packages(c("jsonlite","testthat","DESeq2","edgeR","limma"), repos="https://cloud.r-project.org", quiet=TRUE)' \
  || echo "[devcontainer] R packages unavailable — r_bridge reports RBridgeError and fallbacks activate"

echo "[devcontainer] Build titan_core (Rust) — best effort"
(maturin develop --release -m titan_core/Cargo.toml) \
  || echo "[devcontainer] titan_core build failed — pure-Python engine fallback active"

echo "[devcontainer] Web dashboard dependencies"
(cd web && npm install)

echo "[devcontainer] ready — streamlit run Home.py / uvicorn titan_utils.api:app / node web/server/index.js"
