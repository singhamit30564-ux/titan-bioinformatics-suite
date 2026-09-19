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
- 🧪 **Fully tested** — every page runs without exceptions (verified via `streamlit.testing`)
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
├── requirements.txt             # Runtime deps
├── .streamlit/config.toml       # Theme & server defaults
├── .devcontainer/               # GitHub Codespaces / VS Code dev container
├── titan_utils/                 # Shared library
│   ├── sequence.py              # Cleaning, validation, translation, revcomp, codons
│   ├── theme.py                 # Titan dark theme CSS & palette
│   ├── ui.py                    # titan_title, smart_lock, dr_titan_tip
│   └── io.py                    # CSV/FASTA download helpers
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
