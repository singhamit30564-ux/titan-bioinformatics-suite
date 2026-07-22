import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Titan Bioinformatics",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Titan Theme
st.markdown("""
<style>
    .main {
        background-color: #0a0e17;
    }
    .stApp {
        background-color: #0a0e17;
    }
    h1, h2, h3 {
        color: #d4af37 !important;
    }
    .sidebar .sidebar-content {
        background-color: #1a1f2e;
    }
    .stButton>button {
        background-color: #d4af37;
        color: #0a0e17;
        border: none;
        font-weight: bold;
    }
    .css-1d391kg {
        background-color: #0a0e17;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.title("🧬 TITAN BIOINFORMATICS")
    st.markdown("---")
    
    # Main Navigation
    st.markdown("### 📍 Main Menu")
    page = st.radio(
        "Navigate to:",
        ["Home", "Category 1: DNA/RNA Basics", "Category 2: Protein Analysis", 
         "Category 3: Genomics & QC", "Category 4: Alignment & Phylogeny",
         "Category 5: Lab & Pipeline"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.info("Built by Shivay Singh\n\nAge 12 | Future CEO")

# Home Page
if page == "Home":
    st.title("🧬 TITAN BIOINFORMATICS")
    st.subheader("Next-Generation AI-Powered Bioinformatics Platform")
    st.markdown("---")
    
    # Features
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### ⚡ Fast")
    with col2:
        st.markdown("### 🔒 Secure")
    with col3:
        st.markdown("### 🌍 Multilingual")
    with col4:
        st.markdown("### 🎓 Student-Friendly")
    
    st.markdown("---")
    st.markdown("## 🚀 Welcome to the Future of Biology")
    st.markdown("Built by **Shivay Singh** - A 12-year-old founder on a mission to make bioinformatics accessible to everyone, everywhere.")
    
    st.markdown("---")
    st.markdown("### Why Choose Titan?")
    st.markdown("""
    ✅ **50+ Professional Tools** - From DNA analysis to Clinical Genomics  
    ✅ **Mobile-First Design** - Works perfectly on your phone/tablet  
    ✅ **Free & Open Source** - No hidden charges  
    ✅ **Built with Love** - By a young bioinformatics enthusiast
    """)
    
    st.markdown("---")
    st.success("👈 **Select a category from the sidebar to get started!**")

# Category 1
elif page == "Category 1: DNA/RNA Basics":
    st.title("🧬 Category 1: DNA/RNA Basics")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("1️ DNA ↔ RNA Converter", use_container_width=True):
            st.switch_page("pages/1_DNA_RNA_Converter.py")
        if st.button("2️⃣ GC Content Calculator", use_container_width=True):
            st.switch_page("pages/2_GC_Content.py")
        if st.button("3️⃣ Reverse Complement", use_container_width=True):
            st.switch_page("pages/1_03_Reverse_Complement.py")
        if st.button("4️⃣ GC Content Advanced", use_container_width=True):
            st.switch_page("pages/1_04_GC_Content.py")
        if st.button("5️⃣ Mutation Simulator", use_container_width=True):
            st.switch_page("pages/1_05_Mutation.py")
        if st.button("6️⃣ ORF Finder", use_container_width=True):
            st.switch_page("pages/1_06_ORF_Finder.py")
        if st.button("7️ Motif Pattern Search", use_container_width=True):
            st.switch_page("pages/1_07_Motif_Pattern.py")
        if st.button("8️⃣ Restriction Enzyme Analyzer", use_container_width=True):
            st.switch_page("pages/1_08_Restriction.py")
        if st.button("9️ Codon Usage Table", use_container_width=True):
            st.switch_page("pages/1_09_Codon_Usage.py")
        if st.button("🔟 Hamming Distance", use_container_width=True):
            st.switch_page("pages/1_10_Hamming.py")
        if st.button("1️⃣1️ Nucleotide Frequency", use_container_width=True):
            st.switch_page("pages/1_11_Nucleotide.py")
        if st.button("1️⃣2️ Central Dogma Visualizer", use_container_width=True):
            st.switch_page("pages/1_12_Central_Dogma.py")

# Category 2
elif page == "Category 2: Protein Analysis":
    st.title("🥩 Category 2: Protein Analysis")
    st.markdown("---")
    
    st.info("🚧 Protein Analysis tools coming soon! (Category 2 expansion)")
    st.markdown("Current tools in other categories can handle protein translation.")

# Category 3
elif page == "Category 3: Genomics & QC":
    st.title(" Category 3: Genomics & QC")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("3_01 FASTA/FASTQ Parser", use_container_width=True):
            st.switch_page("pages/3_01_FASTA_FA.py")
        if st.button("3_02 K-mer Frequency", use_container_width=True):
            st.switch_page("pages/3_02_Kmer_Frequency.py")
        if st.button("3_03 N-grams Analysis", use_container_width=True):
            st.switch_page("pages/3_03_Ngrams_Analysis.py")
        if st.button("3_04 CpG Island Detector", use_container_width=True):
            st.switch_page("pages/3_04_CpG_Island_Detector.py")
        if st.button("3_06 Chaos Game Representation", use_container_width=True):
            st.switch_page("pages/3_06_Chaos_Game_Representation.py")
        if st.button("3_07 DNA Shape Analysis", use_container_width=True):
            st.switch_page("pages/3_07_DNA_Shape_Analysis.py")
        if st.button("3_09 VCF Variant Viewer", use_container_width=True):
            st.switch_page("pages/3_09_VCF_Variant_Viewer.py")
        if st.button("3_10 Read Quality Control", use_container_width=True):
            st.switch_page("pages/3_10_Read_Quality_Control.py")
        if st.button("3_11 Gene Ontology GO", use_container_width=True):
            st.switch_page("pages/3_11_Gene_Ontology_GO_Enrichment.py")
        if st.button("3_12 KEGG Pathway Mapper", use_container_width=True):
            st.switch_page("pages/3_12_KEGG_Pathway_Mapper.py")

# Category 4
elif page == "Category 4: Alignment & Phylogeny":
    st.title("🔄 Category 4: Alignment & Phylogeny")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("4_01 Pairwise Alignment", use_container_width=True):
            st.switch_page("pages/4_01_Pairwise_Alignment.py")
        if st.button("4_02 Smith-Waterman Local", use_container_width=True):
            st.switch_page("pages/4_02_Local_Alignment_SmithWaterman.py")
        if st.button("4_03 Needleman-Wunsch Global", use_container_width=True):
            st.switch_page("pages/4_03_Global_Alignment_NeedlemanWunsch.py")
        if st.button("4_04 Overlap Alignment", use_container_width=True):
            st.switch_page("pages/4_04_Overlap_Alignment.py")
        if st.button("4_05 MSA Basic", use_container_width=True):
            st.switch_page("pages/4_05_Multiple_Sequence_Alignment_MSA.py")
        if st.button("4_06 ClustalW Style", use_container_width=True):
            st.switch_page("pages/4_06_MSA_ClustalW_Style.py")
        if st.button("4_07 Phylogenetic Tree", use_container_width=True):
            st.switch_page("pages/4_07_Phylogenetic_Tree_Builder.py")
        if st.button("4_08 Distance Matrix", use_container_width=True):
            st.switch_page("pages/4_08_Distance_Matrix_Calculator.py")
        if st.button("4_09 Sequence Logo", use_container_width=True):
            st.switch_page("pages/4_09_Sequence_Logo_Generator.py")
        if st.button("4_11 Dot Plot", use_container_width=True):
            st.switch_page("pages/4_11_Dot_Plot_Similarity.py")
        if st.button("4_12 Consensus Generator", use_container_width=True):
            st.switch_page("pages/4_12_Consensus_Sequence_Generator.py")

# Category 5
elif page == "Category 5: Lab & Pipeline":
    st.title("🧪 Category 5: Lab & Pipeline")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("5_01 CRISPR gRNA Designer", use_container_width=True):
            st.switch_page("pages/5_01_CRISPR_Cas9_gRNA_Designer.py")
        if st.button("5_02 Primer Design Advanced", use_container_width=True):
            st.switch_page("pages/5_02_Primer_Design_Tm_GC_Hairpin.py")
        if st.button("5_03 PCR Product Calculator", use_container_width=True):
            st.switch_page("pages/5_03_PCR_Primer_Product_Length.py")
        if st.button("5_04 Oligo Tm Calculator", use_container_width=True):
            st.switch_page("pages/5_04_Oligo_Tm_Annealing_Temp.py")
        if st.button("5_05 DNA Melting Curve", use_container_width=True):
            st.switch_page("pages/5_05_DNA_Melting_Curve_Simulation.py")
        if st.button("5_06 SNP Detection", use_container_width=True):
            st.switch_page("pages/5_06_SNP_Detection_Frequency.py")
        if st.button("5_07 InDel Detection", use_container_width=True):
            st.switch_page("pages/5_07_InDel_Detection.py")
        if st.button("5_08 BLAST Search", use_container_width=True):
            st.switch_page("pages/5_08_BLAST_Local_Search_Mock.py")
        if st.button("5_09 Full Pipeline Dashboard", use_container_width=True):
            st.switch_page("pages/5_09_Full_Pipeline_DNA_RNA_Protein_Graph.py")

# Footer
st.markdown("---")
st.markdown("""
<center>

**🧬 Titan Bioinformatics Suite**  
Built with ❤️ by Shivay Singh | Age 12

</center>
""", unsafe_allow_html=True)