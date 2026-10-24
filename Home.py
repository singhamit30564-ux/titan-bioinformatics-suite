"""Titan Bioinformatics Suite — Home (native Streamlit multi-page entry).

Uses ``st.navigation`` (Streamlit ≥ 1.37) to produce a clean, *grouped*
sidebar covering all 260 tools across 15 biological domains.
"""
from pathlib import Path
import re

import streamlit as st

from titan_utils.i18n import (
    LANGUAGE_OPTIONS,
    SUPPORTED_HINDI_TOOL_PAGES,
    is_hindi,
    localized_page_title,
    t,
)
from titan_utils.pwa import ANDROID_INSTALL_STEPS, OFFLINE_CAPABLE, ONLINE_ONLY, render_pwa_injector
from titan_utils.ui import apply_theme

st.set_page_config(
    page_title="Titan Bioinformatics",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

PAGES_DIR = Path(__file__).parent / "pages"

# This selector runs before st.navigation so it remains visible on every page.
selected_language = st.sidebar.selectbox(
    t("Language / भाषा"),
    options=LANGUAGE_OPTIONS,
    key="app_language",
)


def _page(filename: str, language: str) -> st.Page:
    """Build a page with a stable URL and localized sidebar title."""
    stem = Path(filename).stem
    if "_" in stem and stem[:2].isdigit():
        stem = stem.split("_", 1)[1]
    title = stem.replace("_", " ").replace(" and ", " & ").title()
    replacements = {
        "Dna": "DNA", "Rna": "RNA", "Gc": "GC", "Tm": "Tm", "Crispr": "CRISPR",
        "Pcr": "PCR", "Blast": "BLAST", "Fasta": "FASTA", "Fastq": "FASTQ",
        "Qc": "QC", "Msa": "MSA", "Vcf": "VCF", "Cgr": "CGR", "Orf": "ORF",
        "Grna": "gRNA", "Cas9": "Cas9", "Snp": "SNP", "Indel": "InDel",
        "Kegg": "KEGG", "Go": "GO", "Pi": "pI", "Usm": "USM", "Mw": "MW",
        "Ncbi": "NCBI", "Api": "API", "Apis": "APIs", "Ai": "AI", "Dr": "Dr.",
        "Clustalw": "ClustalW", "Smithwaterman": "Smith-Waterman",
        "Needlemanwunsch": "Needleman-Wunsch",
    }
    for key, value in replacements.items():
        title = re.sub(rf"\b{re.escape(key)}\b", value, title, flags=re.IGNORECASE)
    title = localized_page_title(filename, title, language)
    return st.Page(
        str(PAGES_DIR / filename),
        title=title,
        icon="🧪",
        url_path=Path(filename).stem.lower(),
    )


# Tool categories for sidebar navigation
cat0_hub = [
    "00_Tool_Palette_and_Hub.py",
]
cat1_dna = [
    "01_DNA_RNA_Conversion.py",
    "02_Reverse_Complement_Stats.py",
    "03_GC_Content_Melting_Temp.py",
    "04_Mutation_SNP_Detection.py",
    "05_ORF_Finder.py",
    "06_Motif_Pattern_Finder.py",
    "07_Restriction_Enzyme_Cutter.py",
    "08_Codon_Usage_Frequency.py",
    "09_Hamming_Edit_Distance.py",
    "10_Nucleotide_Frequency_Entropy.py",
    "11_Central_Dogma_Visualizer.py",
]
cat2_prot = [
    "12_DNA_to_Protein_Translator.py",
    "13_Molecular_Weight_Calculator.py",
    "14_Protein_to_DNA_BackTranslator.py",
    "15_In_Silico_Mutagenesis.py",
    "16_Protein_pI_Estimator.py",
    "17_Hydropathy_Plot.py",
]
cat3_genome = [
    "20_FASTA_FASTQ_Parser_QC.py",
    "21_Kmer_Frequency.py",
    "22_Ngrams_Analysis.py",
    "23_Primer_Design_Advanced.py",
    "24_CpG_Island_Detector.py",
    "25_Chaos_Game_Representation.py",
    "26_DNA_Shape_Analysis.py",
    "27_VCF_Variant_Viewer.py",
    "28_Read_Quality_Control.py",
    "29_Gene_Ontology_GO_Enrichment.py",
    "30_Tandem_Repeat_Finder.py",
    "31_GC_Skew_Plotter.py",
    "32_KEGG_Pathway_Mapper.py",
    "33_Advanced_Tm_Calculator.py",
    "34_Bulk_Reverse_Complement.py",
    "35_Random_DNA_Generator.py",
]
cat4_align = [
    "40_Pairwise_Alignment.py",
    "41_Local_Alignment_SmithWaterman.py",
    "42_Global_Alignment_NeedlemanWunsch.py",
    "43_Overlap_Alignment.py",
    "44_Multiple_Sequence_Alignment.py",
    "45_MSA_ClustalW_Format.py",
    "46_Phylogenetic_Tree_Builder.py",
    "47_Distance_Matrix_Calculator.py",
    "48_Sequence_Logo_Generator.py",
    "49_Dot_Plot_Similarity.py",
    "50_Consensus_Sequence_Generator.py",
]
cat5_lab = [
    "55_CRISPR_Cas9_gRNA_Designer.py",
    "56_PCR_Product_Length_Calculator.py",
    "57_Oligo_Tm_Annealing_Temp.py",
    "58_DNA_Melting_Curve_Simulation.py",
    "59_InDel_Detection.py",
    "60_BLAST_Local_Search.py",
    "61_Full_Pipeline_Dashboard.py",
    "62_Codon_Optimizer.py",
]
cat6_agri = [
    "65_Agriculture_and_Plant_Genomics.py",
]
cat7_marine = [
    "66_Marine_and_Extremophile_Genomics.py",
]
cat8_clinical = [
    "67_Clinical_Genomics_Precision_Medicine.py",
]
cat9_metagenomics = [
    "68_Metagenomics_and_Microbiome.py",
]
cat10_structural = [
    "69_Structural_Biology_and_Biophysics.py",
]
cat11_epigenetics = [
    "70_Epigenetics_and_Epitranscriptomics.py",
]
cat12_synthetic = [
    "71_Synthetic_Biology_Metabolic_Eng.py",
]
cat13_population = [
    "72_Population_Genetics_Evolution.py",
]
cat14_ncbi = [
    "73_NCBI_and_Global_Bioinformatics_APIs.py",
]
cat15_dr_titan = [
    "74_Dr_Titan_AI_Bio_Copilot.py",
]
cat16_studio = [
    "75_Titan_Flow_Pipeline_Builder.py",
    "76_Bio_Olympiad_and_Practice_Arena.py",
    "77_Batch_Processor_and_Archive.py",
    "78_Electronic_Lab_Notebook_Audit.py",
]
cat17_classroom = ["79_Classroom_Quiz_Mode.py"]
cat18_learning_lab = [
    "80_Photo_Explainer.py",
    "81_Flashcards.py",
    "82_Course.py",
]
cat19_v7_features = [
    "83_Virtual_Lab.py",
    "84_Ask_Paper.py",
    "85_Bio_News.py",
    "86_Teacher.py",
    "87_Cell_Game.py",
    "88_Titan_Eye.py",
    "89_Plugins.py",
    "90_NEET_Prep.py",
    "91_Careers.py",
    "92_Calendar.py",
    "93_Species_Tree.py",
    "94_Achievements.py",
    "95_Challenge.py",
    "96_Notebooks.py",
    "97_Flash_Duel.py",
]
cat20_pro = [
    "98_Differential_Expression.py",
    "99_Variant_ML.py",
    "100_Expression_Explorer.py",
]


def _render_home():
    # Sidebar branding
    with st.sidebar:
        st.title(t("🧬 TITAN BIOINFORMATICS SUITE"))
        st.caption(t("Next-Gen Multi-Domain Bioinformatics Platform"))
        st.markdown("---")
        st.info(t("Built by **Shivay Singh**\n\nAge 12 · Future CEO"))
        st.caption(t("v3.1 — 260 Tools · Titan Flow · Practice Arena · ELN · Zero Data Retention"))
        st.markdown("---")
        # ⚡ Pro Engine — compute engine toggle + availability status card.
        from titan_utils import engine as pro_engine

        pro_engine.render_engine_toggle(key="home_pro_engine_toggle")
        with st.container(border=True):
            st.markdown("#### 🛠️ Engine Status")
            status = pro_engine.engine_status()
            st.caption(f"Active: **{status['active']}** · policy: `{status['policy']}`")
            st.caption(f"Rust titan_core: {'✅ ' + str(status.get('rust_version') or 'available') if status['rust_available'] else '❌ not installed'}")
            st.caption("Python fallback: ✅ always available")
            if status.get("features"):
                st.caption("Rust features: " + ", ".join(status["features"][:6]))

    # Hero
    st.title(t("🧬 TITAN BIOINFORMATICS SUITE"))
    st.subheader(t("Next-Generation AI-Powered Multi-Domain Bioinformatics Platform (260 Tools)"))
    st.markdown("---")

    cols = st.columns(4)
    for col, (emoji, label, desc) in zip(
        cols,
        [
            ("⚡", "260 Tools", "Comprehensive multi-domain analytical depth"),
            ("🎓", "AI Student Tutor", "ELI5, Hindi/Hinglish, and interactive quizzes"),
            ("🛡️", "Zero Data Retention", "100% ephemeral in-RAM genomics with SHA-256 provenance"),
            ("🚀", "Studio Consoles", "Titan Flow workflows, 3D viewer, practice arena, GLP ELN"),
        ],
    ):
        with col:
            with st.container(border=True):
                st.markdown(f"### {emoji} {t(label)}")
                st.caption(t(desc))

    st.markdown("---")
    st.markdown(t("## 🚀 Welcome to the Future of Computational Biology"))
    st.markdown(t(
        "Built by **Shivay Singh** — a 12-year-old founder on a mission to make "
        "bioinformatics accessible, intuitive, and enjoyable for students, researchers, and clinicians everywhere. "
        "Search through the **Master Tool Palette & Hub** or choose a specialized console from the sidebar to begin."
    ))
    st.markdown("---")

    st.markdown(t("## 📂 Biological Domains & Consoles (260 Tools)"))
    categories = [
        ("🎛️", "0 · Master Tool Hub", "Unified search, filtration, and instant execution matrix across all 260 tools.", "1 unified palette"),
        ("🧬", "1 · DNA / RNA Basics", "Conversion, GC & Tm, reverse complement, ORFs, motifs, restriction cutter, codon usage, entropy.", "11 tools"),
        ("🥩", "2 · Protein Analysis", "6-frame translation, molecular weight, isoelectric point (pI), hydropathy, in-silico mutagenesis.", "6 tools"),
        ("🧪", "3 · Genomics & QC", "FASTA/FASTQ QC, k-mers, CpG islands, CGR fractal, VCF, FastQC, GO enrichment, tandem repeats.", "16 tools"),
        ("🔄", "4 · Alignment & Phylogeny", "Pairwise (NW/SW/overlap), MSA, ClustalW, UPGMA/NJ trees, distance heatmaps, sequence logos.", "11 tools"),
        ("🧫", "5 · Lab & Pipeline", "CRISPR gRNA designer, PCR, oligo Tm, DNA melting curves, InDels, BLAST local search, codon optimizer.", "8 tools"),
        ("🌾", "6 · Agriculture & Plants", "Chloroplast IR junctions, CBF/DREB stress, NBS-LRR R-genes, crop cultivar fingerprinting, SSRs.", "20 tools (53–72)"),
        ("🌊", "7 · Marine & Extremophile", "Coral bleaching, hydrothermal vent SoxB, AFGP antifreeze, piezophile desaturases, luciferase Lux.", "20 tools (73–92)"),
        ("🩺", "8 · Clinical & Precision", "ACMG pathogenicity classifier, oncogenic hotspots, PGx star-alleles, HLA affinity, ctDNA liquid biopsy.", "20 tools (93–112)"),
        ("🦠", "9 · Metagenomics & Micro", "16S PCR, alpha/beta diversity PCoA, F/B ratio, CARD resistomes, VFDB virulence, wastewater surveillance.", "20 tools (113–132)"),
        ("📐", "10 · Structural Biology", "Ramachandran dihedrals, B-factors, salt bridges, AlphaFold pLDDT, docking free energy, SASA.", "20 tools (133–152)"),
        ("🧬", "11 · Epigenetics & RNA", "Bisulfite methylation, ATAC-seq FRiP, m6A motifs, ChIP-seq peaks, alternative splicing PSI.", "20 tools (153–172)"),
        ("⚙️", "12 · Synthetic Biology", "Gibson assembly, Golden Gate fidelity, RBS kinetics, toggle switches, repressilator, cell-free TX-TL.", "20 tools (173–192)"),
        ("👥", "13 · Population & Evolution", "Hardy-Weinberg test, LD matrix, Wright-Fisher drift, Fst subdivision, Tajima's D, archaic ABBA-BABA.", "20 tools (193–212)"),
        ("🌐", "14 · NCBI & Global APIs", "GenBank nucleotide, RefSeq protein, Entrez Gene, Taxonomy, dbSNP, PubMed, ClinVar, UniProt, KEGG.", "20 tools (213–232)"),
        ("🤖", "15 · Dr. Titan AI Copilot", "Multilingual explainer, protocol generator, cloning solver, student tutor, buffer calculator, audit.", "28 tools (233–260)"),
        ("🚀", "16 · Titan Flow, Arena & ELN", "Workflow builder with ZIP packages, bio-olympiad practice arena, batch processor archive, GLP lab notebook, 3D viewer, ZDR privacy.", "4 studio consoles"),
        ("🎓", "17 · Classroom Quiz", "Teacher-led five-question MCQ sessions with four-character join codes, mobile access, and XP leaderboard.", "1 classroom mode"),
        ("🧪", "18 · Learning Lab", "Photo Se Samjhao vision AI (opt-in), spaced-repetition flashcards, and the free Titan Bioinformatics Course with a PDF certificate.", "3 new consoles"),
        ("🎮", "19 · V7 Feature Pack", "Virtual lab, paper explainer, bio-news, teacher dashboard, cell game, globe, plugins, NEET prep, careers, calendar, species tree, achievements, challenges, notebooks, flashcard duel.", "15 new consoles"),
        ("⚡", "20 · Pro Engine · Stats · Dashboard", "Rust-accelerated FASTQ/BAM/VCF parsing (titan_core with Python fallback), differential expression (PyDESeq2 / R bridge / labeled fallback), variant ML on SYNTHETIC data, expression explorer.", "3 pro consoles"),
    ]
    for i in range(0, len(categories), 2):
        c1, c2 = st.columns(2)
        for col, cat in zip((c1, c2), categories[i:i + 2]):
            emoji, name, desc, cnt = cat
            with col:
                with st.container(border=True):
                    st.markdown(f"### {emoji} {t(name)}")
                    st.caption(t(cnt))
                    st.write(t(desc))

    st.markdown("---")
    st.markdown(t("### 🎓 Teaching & Mentoring Students Worldwide"))
    st.markdown(t(
        "Titan Bioinformatics is crafted to empower learners of all stages — from school students writing their "
        "first Python scripts to university graduates and clinical bioinformaticians. Every single tool includes "
        "a **Dr. Titan Student Learning Corner** with plain-language explanations, biological context, and real-world impact!"
    ))
    st.success(t("👈 **Open the sidebar (top-left) to explore all 260 tools or jump into the Master Tool Hub.**"))

    # ── PWA / Offline Mode (opt-in, beta, graceful degradation) ─────────────
    st.markdown("---")
    st.markdown(t("## 📵 Offline Mode & Install App (beta)"))
    pwa_col1, pwa_col2 = st.columns(2)
    with pwa_col1:
        with st.container(border=True):
            st.markdown(t("#### 🔌 Honest Offline Scope"))
            st.markdown(t("**Works offline:**"))
            for item in OFFLINE_CAPABLE:
                st.caption(f"✅ {t(item)}")
            st.markdown(t("**Needs internet:**"))
            for item in ONLINE_ONLY:
                st.caption(f"🌐 {t(item)}")
            st.caption(t(
                "This is a best-effort Progressive Web App shell, not a guaranteed full offline "
                "mode — if your browser blocks the service worker, every tool keeps working online as normal."
            ))
    with pwa_col2:
        with st.container(border=True):
            st.markdown(t("#### 📲 Install App (Android)"))
            for i, step in enumerate(ANDROID_INSTALL_STEPS, start=1):
                st.markdown(f"{i}. {t(step)}")
            st.caption(t(
                "An installable home-screen icon launches the suite in standalone mode "
                "(no browser address bar) — it is still the same live web app underneath."
            ))
    render_pwa_injector()

    st.markdown("---")
    st.markdown(t(
        "<center><b>🧬 Titan Bioinformatics Suite (v3.0)</b><br/>"
        "Built with ❤️ by Shivay Singh · Python · Streamlit · Biopython · Plotly · NumPy · Pandas</center>"
    ), unsafe_allow_html=True)


# Multi-page navigation wiring
try:
    home = st.Page(
        _render_home,
        title=t("Home", selected_language),
        icon="🏠",
        default=True,
        url_path="home",
    )
    nav = st.navigation(
        {
            t("🏠 Home", selected_language): [home],
            t("🎛️ Master Suite Hub", selected_language): [_page(f, selected_language) for f in cat0_hub],
            t("🧬 1 · DNA / RNA Basics", selected_language): [_page(f, selected_language) for f in cat1_dna],
            t("🥩 2 · Protein Analysis", selected_language): [_page(f, selected_language) for f in cat2_prot],
            t("🧪 3 · Genomics & QC", selected_language): [_page(f, selected_language) for f in cat3_genome],
            t("🔄 4 · Alignment & Phylogeny", selected_language): [_page(f, selected_language) for f in cat4_align],
            t("🧫 5 · Lab & Pipeline", selected_language): [_page(f, selected_language) for f in cat5_lab],
            t("🌾 6 · Agriculture & Plants", selected_language): [_page(f, selected_language) for f in cat6_agri],
            t("🌊 7 · Marine & Extremophile", selected_language): [_page(f, selected_language) for f in cat7_marine],
            t("🩺 8 · Clinical & Precision", selected_language): [_page(f, selected_language) for f in cat8_clinical],
            t("🦠 9 · Metagenomics & Micro", selected_language): [_page(f, selected_language) for f in cat9_metagenomics],
            t("📐 10 · Structural Biology", selected_language): [_page(f, selected_language) for f in cat10_structural],
            t("🧬 11 · Epigenetics & RNA", selected_language): [_page(f, selected_language) for f in cat11_epigenetics],
            t("⚙️ 12 · Synthetic Biology", selected_language): [_page(f, selected_language) for f in cat12_synthetic],
            t("👥 13 · Population & Evolution", selected_language): [_page(f, selected_language) for f in cat13_population],
            t("🌐 14 · NCBI & Global APIs", selected_language): [_page(f, selected_language) for f in cat14_ncbi],
            t("🤖 15 · Dr. Titan AI Copilot", selected_language): [_page(f, selected_language) for f in cat15_dr_titan],
            t("🚀 16 · Flow · Arena · ELN", selected_language): [_page(f, selected_language) for f in cat16_studio],
            t("🎓 17 · Classroom Quiz", selected_language): [_page(f, selected_language) for f in cat17_classroom],
            t("🧪 18 · Learning Lab", selected_language): [_page(f, selected_language) for f in cat18_learning_lab],
            t("🎮 19 · V7 Feature Pack", selected_language): [_page(f, selected_language) for f in cat19_v7_features],
            t("⚡ 20 · Pro Engine · Stats · Dashboard", selected_language): [_page(f, selected_language) for f in cat20_pro],
        }
    )

    # The note is shown only while a page with English-only body copy is open.
    page_url = getattr(nav, "url_path", "")
    supported_paths = {Path(name).stem.lower() for name in SUPPORTED_HINDI_TOOL_PAGES}
    if is_hindi(selected_language) and page_url not in supported_paths | {"home"}:
        st.sidebar.info(t(
            "Untranslated tools remain in English. Hindi translations are coming soon.",
            selected_language,
        ))
    nav.run()
except Exception:  # pragma: no cover — older Streamlit
    _render_home()
    st.markdown(t("### Quick Links"))
    for group in (
        cat0_hub, cat1_dna, cat2_prot, cat3_genome, cat4_align, cat5_lab,
        cat6_agri, cat7_marine, cat8_clinical, cat9_metagenomics,
        cat10_structural, cat11_epigenetics, cat12_synthetic,
        cat13_population, cat14_ncbi, cat15_dr_titan, cat16_studio,
        cat17_classroom, cat18_learning_lab, cat19_v7_features, cat20_pro,
    ):
        for fname in group[:2]:
            st.page_link(str(PAGES_DIR / fname))
