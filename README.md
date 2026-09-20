# 🧬 Titan Bioinformatics Suite

![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen)
![Version](https://img.shields.io/badge/Version-2.0.0-blue)
![Built By](https://img.shields.io/badge/Built_By-Shivay_Singh-red)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-≥1.37-ff4b4b)

### 🚀 Next-Generation Bioinformatics Platform for Everyone
**Built by a 12-year-old Founder. Designed to make bioinformatics accessible on any device.**

---

## 🌍 About Titan Bioinformatics

**Titan Bioinformatics** is a modern, mobile-first, and open-source bioinformatics platform built entirely in Python + Streamlit. It packages **50+ professional-grade tools** — DNA/RNA basics, protein analysis, genomics QC, alignment & phylogeny, and a molecular-biology lab pipeline — into a single zero-install web app.

While legacy tools are often desktop-bound, laggy, or expensive, Titan is designed to run anywhere: in your browser, on a phone, in GitHub Codespaces, or deployed for free on Streamlit Community Cloud.

---

## ✨ Highlights

- 📱 **Mobile-first UI** with a consistent dark "Titan" theme
- 🧬 **50+ validated tools** spanning DNA, RNA, protein, alignment, phylogeny and the lab bench
- 🔬 **Real algorithms** — Biopython-backed pairwise/MSA, UPGMA/NJ trees, Nearest-Neighbour Tm, codon adaptation index (CAI), CRISPR PAM scanning for SpCas9/SaCas9/Cas12a, BLAST-style seed-and-extend, Shannon entropy, Chaos Game Representation, etc.
- 📊 **Interactive Plotly charts** everywhere (pie, bar, heatmap, scatter, dendrograms)
- 📥 **Working CSV/FASTA downloads** on analysis pages
- 🏗️ **Clean architecture** — shared `titan_utils/` package for sequences, validation, I/O and UI
- 🧪 **Fully tested** — every one of the 52 pages is rendered *and every button is clicked* in CI (`streamlit.testing`), so a broken tool fails the build instead of failing in front of a user
- 🆓 **Free & open source** (see LICENSE)

> ⚠️ Educational note: the **GO Enrichment** and **KEGG Pathway Mapper** pages currently ship with *curated demo data* to illustrate the visualisations; they do not yet call live external APIs (QuickGO, KEGG REST, Ensembl). Calling out to these services is on the roadmap.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit (multi-page app via `st.navigation`) |
| Bio core | [Biopython](https://biopython.org/) (`Bio.Align`, `Bio.Phylo`, `Bio.SeqUtils`, `Bio.Restriction`, etc.) |
| Data | Pandas, NumPy |
| Charts | Plotly, Matplotlib (phylogenetic trees) |
| Shared code | `titan_utils/` package (validation, translation, UI, I/O, theme) |

---

## 📂 Project Layout

```
titan-bioinformatics-suite/
├── Home.py                      # Landing page + grouped sidebar nav
├── conftest.py                  # Puts the repo root on sys.path for pytest/AppTest
├── requirements.txt             # Runtime deps
├── .streamlit/config.toml       # Theme & server defaults
├── .devcontainer/               # GitHub Codespaces / VS Code dev container
├── titan_utils/                 # Shared library
│   ├── sequence.py              # Cleaning, validation, translation, revcomp, codons
│   ├── theme.py                 # Titan dark theme CSS & palette
│   ├── ui.py                    # titan_title, smart_lock, dr_titan_tip
│   └── io.py                    # CSV/FASTA download helpers
├── tests/
│   ├── test_titan_suite.py      # Pure-logic tests (validation, translation, ORFs…)
│   ├── test_ui_helpers.py       # Shared-helper + page regressions
│   └── test_page_interactions.py# Renders & clicks every page (the safety net)
└── pages/                       # 52 tool pages (NN_Name.py)
    ├── 01–11  DNA/RNA Basics
    ├── 12–17  Protein Analysis
    ├── 20–35  Genomics & QC
    ├── 40–50  Alignment & Phylogeny
    └── 55–62  Lab & Pipeline
```

---

## 🚀 Getting Started

```bash
git clone https://github.com/singhamit30564-ux/titan-bioinformatics-suite.git
cd titan-bioinformatics-suite
pip install -r requirements.txt
streamlit run Home.py
```

Then open the URL printed by Streamlit (defaults to `http://localhost:8501`).
The app will also work instantly inside GitHub Codespaces — just open the repo in a Codespace and port-forward 8501.

---

## 📦 Deploying

- **Streamlit Community Cloud**: point it at this repo, set `Home.py` as the entrypoint.
- **Docker / self-hosted**: any container with Python 3.10+ works; `docker run -p 8501:8501 ...`.

---

## 🗺️ Roadmap

- [x] Phase 1 — Core UI & 50+ sequence tools (✅ v2.0 complete)
- [x] Phase 1b — Shared library, codon-table correctness, grouped navigation
- [ ] Phase 2 — Live NCBI/ENTREZ, QuickGO, KEGG REST integrations
- [ ] Phase 3 — Real multiple-sequence alignment (MUSCLE/Clustal Omega via Bio.Align)
- [ ] Phase 4 — Dr. Titan multilingual LLM assistant
- [ ] Phase 5 — Session history, PDF report generation
- [ ] Phase 6 — Agriculture & Marine extensions from the MASTERPLAN

---

## 👑 Founder's Note

> *"I'm building Titan because I believe every student, regardless of location or language, deserves access to world-class bioinformatics tools. The giants ignored the mobile generation and non-English speakers — Titan is built for them. This is just the beginning."*
>
> — **Shivay Singh**, Founder & CEO (age 12)

---

## 📄 License

This project is released under the **GNU AGPLv3** (see `LICENSE`). If you deploy a modified version over a network you must share your changes.

© 2026 Titan Bioinformatics.

---

## 🐛 Recent Fixes — Tools That Broke When You Clicked Them (2026-09)

The test suite used to only *compile* each page, so pages that broke the moment you
pressed their button stayed broken. New interaction tests now render every page and
click every button, and they caught these:

| Page | Symptom | Cause |
|---|---|---|
| 04 · Mutation/SNP | Red "Calculation Error", no SNP table | `Styler.applymap` (removed in pandas 2.1 → use `.map`) |
| 07 · Restriction Cutter | Red "Calculation Error", no cut-site table | same `applymap` removal |
| 09 · Hamming/Edit | lint warning only | f-string with no placeholder |
| 16 · Protein pI | Claimed a pI but never calculated one | replaced the acid/basic residue count with a real Henderson-Hasselbalch bisection (`ProtParam`) |
| 24 · CpG Islands | Crashed: *Invalid property `yaxis` for Shape* | `add_hline(..., yaxis="y2")` → `yref="y2"` (was broken on plotly 5.x **and** 7.x) |
| 27 · VCF Viewer | "Parsing Error: 'CHROM'", chromosome chart missing | header sliced with `line[2:]`, renaming the column to `HROM` |
| 32 · KEGG Mapper | Crashed: *Invalid property `titlefont_size`* | removed in plotly 6 → nest the font in `title=dict(font=…)` |
| 33 · Advanced Tm | Crashed: *name `math` is not defined* | missing `import math` — only reachable after clicking |
| 48 · Sequence Logo | "Logo Generation Error", no logo | `stackgroup` is a scatter-only property, not valid on `go.Bar` |
| 59 · InDel Detection | Crashed: *'Styler' object has no attribute `applymap`* | same pandas 2.1 removal |
| 62 · Codon Optimizer | "Sequence is empty" on first use | shipped no default CDS |
| `titan_utils/ui.py` | Metric tooltips showed stray characters (`"0"`, `"."`) | tuple unpacking read `value[2]` from the already-rebound `value` |
| `titan_utils/ui.py` | Export widget keys derived from `id()` | CPython recycles `id()` after GC → use a content hash |

Verification:

```bash
python -m py_compile pages/*.py Home.py titan_utils/*.py
pytest -q          # 127 passed, 1 skipped — includes clicking every button
```

Each fix was confirmed by re-introducing the original bug: the new tests fail
(10 failures) while the old compile-only suite still passed 12/12.

---

## 🔧 Recent Refactor — Titan Utils Unification (2026-09)

**PR #2 — `refactor: unify 49 pages on titan_utils`**

This PR removes the last hollow duplication in the codebase:

- **49/62 pages now import `titan_utils`** (was 3/62) — `clean_sequence`, `validate_dna/rna`, `revcomp`, `gc_fraction_safe`, `titan_title`, `smart_lock`, `dr_titan_tip`, `df_to_csv_bytes`.
- **Paywall removed** — the fake "🔒 Explorer Plan Required" gating on every tool is now a free `smart_lock` CSV download. `titan_utils/ui.py:smart_lock` now shows a caption instead of a gated button when no data is ready.
- **Centralized sequence helpers** — new `titan_utils/sequence.py` functions: `gc_content_percent`, `at_content_percent`, `nucleotide_counts`, `find_orfs_simple`, `bulk_revcomp` (shared by ORF Finder, Bulk RC, GC pages).
- **Theme & export unified** — `titan_title` + `apply_theme` + `sequence_metrics_row` used consistently; Plotly dark theme stays intact.
- **Tests & CI** — new `tests/test_titan_suite.py` (11 tests: validation, revcomp, ORF, compile, navigation coverage, paywall absence) + `.github/workflows/ci.yml` + `pytest.ini`.

Validation:

```bash
python -m py_compile pages/*.py Home.py titan_utils/*.py
pytest tests/test_titan_suite.py -v   # 11 passed
```

See `titan_utils/__init__.py` for the public API.
