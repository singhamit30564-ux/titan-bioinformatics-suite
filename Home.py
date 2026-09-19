"""Titan Bioinformatics Suite — Home (native Streamlit multi-page entry).

Uses ``st.navigation`` (Streamlit ≥ 1.37) to produce a clean, *grouped*
sidebar without fake separator pages. Falls back to a hero page if the
feature isn't available.
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
    # e.g. "03_GC_Content_Melting_Temp.py" → "GC Content & Melting Temp"
    stem = filename.replace(".py", "")
    # Strip leading NN_ index
    if "_" in stem and stem[:2].isdigit():
        stem = stem.split("_", 1)[1]
    title = stem.replace("_", " ").replace("and", "&").title()
    # Small tweaks for nicer titles
    replacements = {
        "Dna": "DNA", "Rna": "RNA", "Gc": "GC", "Tm": "Tm", "Crispr": "CRISPR",
        "Pcr": "PCR", "Blast": "BLAST", "Fasta": "FASTA", "Fastq": "FASTQ",
        "Qc": "QC", "Ms A": "MSA", "Vcf": "VCF", "Cgr": "CGR", "Orf": "ORF",
        "Grna": "gRNA", "Cas9": "Cas9", "Snp": "SNP", "Indel": "InDel",
        "Dna/Rna": "DNA/RNA", "Kegg": "KEGG", "Go": "GO", "Pi": "pI",
        "Usm": "USM", "Mw": "MW",
    }
    for k, v in replacements.items():
        title = title.replace(k, v)
    return st.Page(str(PAGES_DIR / filename), title=title, icon="🧪")


# Build grouped navigation. The order of categories and filenames below
# controls the sidebar order.
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


def _render_home():
    # ---- Sidebar branding ----
    with st.sidebar:
        st.title("🧬 TITAN BIOINFORMATICS")
        st.caption("Next-Gen Bioinformatics Platform")
        st.markdown("---")
        st.info("Built by **Shivay Singh**\n\nAge 12 · Future CEO")
        st.caption("v2.0 — cleaned & validated build")

    # ---- Hero ----
    st.title("🧬 TITAN BIOINFORMATICS")
    st.subheader("Next-Generation AI-Powered Bioinformatics Platform")
    st.markdown("---")

    cols = st.columns(4)
    for col, (emoji, label) in zip(
        cols,
        [("⚡", "Fast"), ("🔒", "Private"), ("🌍", "Multilingual"), ("🎓", "Student-Friendly")],
    ):
        col.markdown(f"### {emoji} {label}")

    st.markdown("---")
    st.markdown("## 🚀 Welcome to the Future of Biology")
    st.markdown(
        "Built by **Shivay Singh** — a 12-year-old founder on a mission to make "
        "bioinformatics accessible to everyone, everywhere. Select a tool from "
        "the grouped sidebar on the left to begin."
    )
    st.markdown("---")

    st.markdown("## 📂 Tool Categories")
    categories = [
        ("🧬", "1 · DNA / RNA Basics",
         "Conversion, GC & Tm, reverse complement, ORFs, motifs, restriction "
         "digest, codon usage, Hamming/Edit distance, Shannon entropy, "
         "Central Dogma.",
         f"{len(cat1_dna)} tools"),
        ("🥩", "2 · Protein Analysis",
         "6-frame translation, molecular weight, isoelectric point (pI), "
         "Kyte-Doolittle hydropathy, reverse translation, in-silico "
         "mutagenesis.",
         f"{len(cat2_prot)} tools"),
        ("🧪", "3 · Genomics & QC",
         "FASTA/FASTQ, k-mers, N-grams, CpG islands, CGR, VCF, FastQC, "
         "GO enrichment, tandem repeats, GC skew, KEGG, Tm, random DNA.",
         f"{len(cat3_genome)} tools"),
        ("🔄", "4 · Alignment & Phylogeny",
         "Pairwise (NW/SW/overlap), MSA, ClustalW, UPGMA/NJ trees, distance "
         "heatmaps, sequence logos, dot plots, consensus.",
         f"{len(cat4_align)} tools"),
        ("🧫", "5 · Lab & Pipeline",
         "CRISPR gRNA, PCR, oligo Tm, melting curves, InDels, BLAST, full "
         "dogma dashboard, codon optimizer with CAI.",
         f"{len(cat5_lab)} tools"),
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
    st.markdown("### Why Titan?")
    st.markdown(
        "✅ **50+ Professional Tools** — from DNA analysis to molecular cloning  \n"
        "✅ **Mobile-First Design** — works on phones, tablets, desktops  \n"
        "✅ **Free & Open Source** — no hidden charges  \n"
        "✅ **Built with ❤️** by a young bioinformatics enthusiast"
    )
    st.success("👈 **Open the sidebar (top-left) to browse all tools.**")

    st.markdown("---")
    st.markdown(
        "<center><b>🧬 Titan Bioinformatics Suite</b><br/>"
        "Built with ❤️ by Shivay Singh · Python · Streamlit · Biopython</center>",
        unsafe_allow_html=True,
    )


# Try to use st.navigation; if unavailable (older Streamlit), fall back to
# a single hero page that links via st.page_link.
try:
    home = st.Page(_render_home, title="Home", icon="🏠", default=True)
    nav = st.navigation(
        {
            "🏠 Home": [home],
            "🧬 1 · DNA / RNA Basics":      [_page(f) for f in cat1_dna],
            "🥩 2 · Protein Analysis":      [_page(f) for f in cat2_prot],
            "🧪 3 · Genomics & QC":         [_page(f) for f in cat3_genome],
            "🔄 4 · Alignment & Phylogeny": [_page(f) for f in cat4_align],
            "🧫 5 · Lab & Pipeline":        [_page(f) for f in cat5_lab],
        }
    )
    nav.run()
except Exception:  # pragma: no cover — older Streamlit
    _render_home()
    st.markdown("### Quick Links")
    for group in (cat1_dna, cat2_prot, cat3_genome, cat4_align, cat5_lab):
        for fname in group[:3]:  # show a handful
            st.page_link(str(PAGES_DIR / fname))
