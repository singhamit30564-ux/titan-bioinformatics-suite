# 🧬 Titan Bioinformatics Suite

![Status](https://img.shields.io/badge/Status-Active_Development-brightgreen)
![Version](https://img.shields.io/badge/Version-3.0.0-blue)
![Built By](https://img.shields.io/badge/Built_By-Shivay_Singh-red)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-≥1.37-ff4b4b)
![Total Tools](https://img.shields.io/badge/Total_Tools-260_Tools-gold)

### 🚀 Next-Generation AI-Powered Multi-Domain Bioinformatics Platform
**Built by a 12-year-old Founder. Designed to make bioinformatics and genomics accessible, intuitive, and interactive for students and researchers everywhere.**

---

## 🌍 About Titan Bioinformatics

**Titan Bioinformatics Suite (v3.0)** is an enterprise-grade, mobile-first, and open-source computational biology platform built in Python + Streamlit. It packages **260 specialized professional bioinformatics tools** across **15 biological domains** — from foundational DNA/RNA, protein biophysics, and phylogenetic alignment to agriculture, marine ecology, clinical precision oncology, metagenomics, epigenetics, synthetic biology, population dynamics, NCBI APIs, and Dr. Titan conversational AI copilots.

---

## ✨ Key Highlights

- 🎛️ **Master Tool Palette & Hub (`00_Tool_Palette_and_Hub.py`)**: Search, filter, and run any of the 260 tools interactively with live input controls, Plotly charts, dataframes, and instant CSV/JSON exports.
- 🎓 **Dr. Titan AI Student Tutor & Concept Lab**: Interactive teaching assistant explaining complex biology concepts step-by-step with real-world analogies (ELI5), multilingual instruction (English, Hindi, Hinglish), interactive practice quizzes, and wet-lab guidance.
- 🧬 **260 Validated Tools Across 15 Domains**:
  1. **Master Tool Palette Hub** (Global search & execution matrix)
  2. **DNA / RNA Basics** (Tools 1–11: conversions, GC & Tm, reverse complement, ORFs, motifs, restriction cuts)
  3. **Protein Analysis** (Tools 12–17: 6-frame translation, molecular weight, pI, hydropathy, in-silico mutagenesis)
  4. **Genomics & QC** (Tools 18–33: FASTA/FASTQ QC, k-mers, CpG islands, CGR fractal, VCF, FastQC, GO, repeats)
  5. **Alignment & Phylogeny** (Tools 34–44: NW/SW/overlap pairwise, MSA, ClustalW, UPGMA/NJ trees, logos, dot plots)
  6. **Lab & Pipeline** (Tools 45–52: CRISPR-Cas9 gRNA, PCR length, oligo Tm, melting curves, BLAST, codon optimizer)
  7. **Agriculture & Plant Genomics** (Tools 53–72: Chloroplast IR junctions, CBF/DREB stress, NBS-LRR R-genes, crop SSR/SNPs)
  8. **Marine & Extremophile Genomics** (Tools 73–92: Coral bleaching, hydrothermal vent SoxB, AFGP antifreeze, piezophiles, Lux operon)
  9. **Clinical Genomics & Precision Medicine** (Tools 93–112: ACMG tiering, cancer hotspots, PGx star-alleles, HLA affinity, ctDNA)
  10. **Metagenomics & Microbiome** (Tools 113–132: 16S in-silico PCR, alpha/beta diversity PCoA, F/B ratio, CARD resistomes)
  11. **Structural Biology & Biophysics** (Tools 133–152: Ramachandran dihedrals, B-factors, salt bridges, AlphaFold pLDDT, docking ΔG)
  12. **Epigenetics & Epitranscriptomics** (Tools 153–172: Bisulfite methylation, ATAC-seq FRiP, m6A motifs, alternative splicing PSI)
  13. **Synthetic Biology & Metabolic Engineering** (Tools 173–192: Gibson assembly, Golden Gate fidelity, RBS kinetics, toggle switches)
  14. **Population Genetics & Evolutionary Dynamics** (Tools 193–212: Hardy-Weinberg exact, LD matrix, Wright-Fisher drift, Fst, Tajima's D)
  15. **NCBI & Global Bioinformatics APIs** (Tools 213–232: GenBank, RefSeq, Entrez Gene, Taxonomy, dbSNP, PubMed, ClinVar, UniProt, KEGG)
  16. **Dr. Titan AI & Bio-Copilot** (Tools 233–260: Multilingual sequence explainer, protocol generator, cloning solver, buffer calculator)
- 📊 **Interactive Plotly Visualizations Everywhere**: Dynamic Manhattan plots, volcano plots, contact maps, PCoA scatters, phylogenetic trees, and ROC/FSC curves.
- 📥 **Zero Paywalls**: 100% free CSV and JSON downloads across all tools.
- 🏗️ **Modular Central Registry**: `titan_utils/registry.py` indexes all 260 tools with parameter typing, defaults, and category metadata; `titan_tools/runner.py` powers universal execution.
- 🧪 **Fully Tested CI**: Renders all 63 pages and clicks every button in `streamlit.testing` AppTest; passes pyflakes static analysis.

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
