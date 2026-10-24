# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧬 TITAN BIOINFORMATICS SUITE — full stack image
# Rust (titan_core) + Python 3.11 + R (DESeq2/edgeR/limma) + Node 20 (web)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FROM python:3.11-slim-bookworm AS python-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps: R (DESeq2/edgeR/limma), Rust toolchain, Node 20, build tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl ca-certificates git \
        r-base r-base-dev \
        libxml2-dev libcurl4-openssl-dev libssl-dev libfontconfig1-dev libharfbuzz-dev libfribidi-dev \
        libfreetype6-dev libpng-dev libtiff5-dev libjpeg-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Rust toolchain (rustup, minimal profile)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app

# Python core + optional heavy stacks (install is best-effort: app must not
# require them; fallbacks are covered by tests).
COPY requirements.txt requirements-optional.txt ./
RUN pip install -r requirements.txt && \
    (pip install -r requirements-optional.txt || echo "optional stacks unavailable — Python fallbacks active")

# R packages for the DE bridge (best effort; bridge degrades to PyDESeq2/fallback)
RUN Rscript -e 'install.packages(c("jsonlite","DESeq2","edgeR","limma"), repos="https://cloud.r-project.org", quiet=TRUE)' \
    || echo "R packages unavailable — de_runner.R will report RBridgeError and fallbacks activate"

# Build the Rust extension (optional at runtime)
COPY titan_core ./titan_core
RUN pip install maturin && (maturin build --release -m titan_core/Cargo.toml --out /app/wheels && pip install /app/wheels/*.whl) \
    || echo "titan_core build failed — pure-Python engine fallback active"

# App + web dashboard
COPY . .
RUN cd web && npm ci && npm run build

EXPOSE 8501 8000 4173

# Default: Streamlit classic app. The API (`uvicorn titan_utils.api:app`) and
# the web gateway (`node web/server/index.js`) can be started from the same
# image with `docker compose` or `docker run ... <command>`.
CMD ["streamlit", "run", "Home.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
