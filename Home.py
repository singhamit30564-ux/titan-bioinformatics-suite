"""Titan Bioinformatics Suite — Home (native Streamlit multi-page entry).

Uses ``st.navigation`` (Streamlit ≥ 1.37) to produce a clean, *grouped*
sidebar covering all 260 tools across 15 biological domains.
"""
from pathlib import Path

import streamlit as st

from titan_utils.ui import apply_theme

st.set_page_config(
    page_title="Titan Bioinformatics",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

PAGES_DIR = Path(__file__).parent / "pages"


def _page(filename: str) -> st.Page:
    """Build an st.Page with a nicely cleaned title."""
    stem = filename.replace(".py", "")
    if "_" in stem and stem[:2].isdigit():
        stem = stem.split("_", 1)[1]
    title = stem.replace("_", " ").replace("and", "&").title()
    replacements = {
        "Dna": "DNA", "Rna": "RNA", "Gc": "GC", "Tm": "Tm", "Crispr": "CRISPR",
        "Pcr": "PCR", "Blast": "BLAST", "Fasta": "FASTA", "Fastq": "FASTQ",
        "Qc": "QC", "Ms A": "MSA", "Vcf": "VCF", "Cgr": "CGR", "Orf": "ORF",
        "Grna": "gRNA", "Cas9": "Cas9", "Snp": "SNP", "Indel": "InDel",
        "Dna/Rna": "DNA/RNA", "Kegg": "KEGG", "Go": "GO", "Pi": "pI",
        "Usm": "USM", "Mw": "MW", "Ncbi": "NCBI", "Api": "API", "Apis": "APIs",
        "Ai": "AI", "Eng": "Engineering", "Med": "Medicine", "Dr": "Dr.",
    }
    for k, v in replacements.items():
        title = title.replace(k, v)
    return st.Page(str(PAGES_DIR / filename), title=title, icon="🧪")


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


def _render_home():
    # Sidebar branding
    with st.sidebar:
        st.title("🧬 TITAN BIOINFORMATICS")
        st.caption("Next-Gen Multi-Domain Bioinformatics Platform")
        st.markdown("---")
        st.info("Built by **Shivay Singh**\n\nAge 12 · Future CEO")
        st.caption("v3.0 — 260 Tools Master Suite & AI Student Tutor")

    # Hero
    st.title("🧬 TITAN BIOINFORMATICS SUITE")
    st.subheader("Next-Generation AI-Powered Multi-Domain Bioinformatics Platform (260 Tools)")
    st.markdown("---")

    cols = st.columns(4)
    for col, (emoji, label, desc) in zip(
        cols,
        [
            ("⚡", "260 Tools", "Comprehensive multi-domain analytical depth"),
            ("🎓", "AI Student Tutor", "ELI5, Hindi/Hinglish, and interactive quizzes"),
            ("🔒", "100% Free & Open", "No subscriptions, paywalls, or feature locks"),
            ("🚀", "Interactive Consoles", "Plotly visuals, CSV/JSON exports, and Dr. Titan tips"),
        ],
    ):
        with col:
            with st.container(border=True):
                st.markdown(f"### {emoji} {label}")
                st.caption(desc)

    st.markdown("---")
    st.markdown("## 🚀 Welcome to the Future of Computational Biology")
    st.markdown(
        "Built by **Shivay Singh** — a 12-year-old founder on a mission to make "
        "bioinformatics accessible, intuitive, and enjoyable for students, researchers, and clinicians everywhere. "
        "Search through the **Master Tool Palette & Hub** or choose a specialized console from the sidebar to begin."
    )
    st.markdown("---")

    st.markdown("## 📂 Biological Domains & Consoles (260 Tools)")
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
    ]
    for i in range(0, len(categories), 2):
        c1, c2 = st.columns(2)
        for col, cat in zip((c1, c2), categories[i:i + 2]):
            emoji, name, desc, cnt = cat
            with col:
                with st.container(border=True):
                    st.markdown(f"### {emoji} {name}")
                    st.caption(cnt)
                    st.write(desc)

    st.markdown("---")
    st.markdown("### 🎓 Teaching & Mentoring Students Worldwide")
    st.markdown(
        "Titan Bioinformatics is crafted to empower learners of all stages — from school students writing their "
        "first Python scripts to university graduates and clinical bioinformaticians. Every single tool includes "
        "a **Dr. Titan Student Learning Corner** with plain-language explanations, biological context, and real-world impact!"
    )
    st.success("👈 **Open the sidebar (top-left) to explore all 260 tools or jump into the Master Tool Hub.**")

    st.markdown("---")
    st.markdown(
        "<center><b>🧬 Titan Bioinformatics Suite (v3.0)</b><br/>"
        "Built with ❤️ by Shivay Singh · Python · Streamlit · Biopython · Plotly · NumPy · Pandas</center>",
        unsafe_allow_html=True,
    )


# Multi-page navigation wiring
try:
    home = st.Page(_render_home, title="Home", icon="🏠", default=True)
    nav = st.navigation(
        {
            "🏠 Home": [home],
            "🎛️ Master Suite Hub":          [_page(f) for f in cat0_hub],
            "🧬 1 · DNA / RNA Basics":      [_page(f) for f in cat1_dna],
            "🥩 2 · Protein Analysis":      [_page(f) for f in cat2_prot],
            "🧪 3 · Genomics & QC":         [_page(f) for f in cat3_genome],
            "🔄 4 · Alignment & Phylogeny": [_page(f) for f in cat4_align],
            "🧫 5 · Lab & Pipeline":        [_page(f) for f in cat5_lab],
            "🌾 6 · Agriculture & Plants":  [_page(f) for f in cat6_agri],
            "🌊 7 · Marine & Extremophile": [_page(f) for f in cat7_marine],
            "🩺 8 · Clinical & Precision":  [_page(f) for f in cat8_clinical],
            "🦠 9 · Metagenomics & Micro":  [_page(f) for f in cat9_metagenomics],
            "📐 10 · Structural Biology":   [_page(f) for f in cat10_structural],
            "🧬 11 · Epigenetics & RNA":    [_page(f) for f in cat11_epigenetics],
            "⚙️ 12 · Synthetic Biology":    [_page(f) for f in cat12_synthetic],
            "👥 13 · Population & Evolution": [_page(f) for f in cat13_population],
            "🌐 14 · NCBI & Global APIs":   [_page(f) for f in cat14_ncbi],
            "🤖 15 · Dr. Titan AI Copilot": [_page(f) for f in cat15_dr_titan],
        }
    )
    nav.run()
except Exception:  # pragma: no cover — older Streamlit
    _render_home()
    st.markdown("### Quick Links")
    for group in (cat0_hub, cat1_dna, cat2_prot, cat3_genome, cat4_align, cat5_lab, cat6_agri, cat7_marine, cat8_clinical, cat9_metagenomics, cat10_structural, cat11_epigenetics, cat12_synthetic, cat13_population, cat14_ncbi, cat15_dr_titan):
        for fname in group[:2]:
            st.page_link(str(PAGES_DIR / fname))
