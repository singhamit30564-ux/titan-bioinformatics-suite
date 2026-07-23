import streamlit as st

st.set_page_config(page_title="Titan Bioinformatics", page_icon="", layout="wide")

# --- PROFESSIONAL DARK THEME CSS ---
st.markdown("""
<style>
.header-main {font-size: 2.4rem; font-weight: 700; color: #66fcf1; text-align: center; margin-bottom: 0.5rem;}
.header-sub {font-size: 1.1rem; color: #8b9bb4; text-align: center; margin-bottom: 2rem;}
.card {background: #1a1f2e; border-radius: 10px; padding: 1.2rem; margin: 0.6rem 0; border-left: 4px solid #66fcf1; transition: 0.2s;}
.card:hover {background: #222838;}
.card h3 {color: #66fcf1; margin-top: 0; font-size: 1.1rem;}
.card p {color: #c9d1d9; font-size: 0.95rem; margin-bottom: 0.5rem;}
.badge {display: inline-block; background: #2d3748; color: #a0aec0; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.75rem; margin-right: 0.4rem;}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown('<div class="header-main"> Titan Bioinformatics Suite</div>', unsafe_allow_html=True)
st.markdown('<div class="header-sub">Computational Biology Tools • Built by Shivay Singh</div>', unsafe_allow_html=True)

# --- TOOL CATEGORIES ---
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card"><h3>🔬 Sequence Analysis</h3><p>GC Content, Reverse Complement, ORF Finder, Restriction Mapper, Codon Optimizer</p><span class="badge">Core</span><span class="badge">Validated</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><h3>📊 Alignment & Phylogeny</h3><p>Pairwise/Global/Local Alignment, MSA, Distance Matrix, Phylogenetic Trees (NJ/UPGMA)</p><span class="badge">Advanced</span><span class="badge">Visual</span></div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card"><h3>🧪 CRISPR & Molecular</h3><p>gRNA Designer (Off-target scoring), Primer Tm Calculator, PCR Product Size, Melting Curve</p><span class="badge">Lab Ready</span><span class="badge">Optimized</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><h3>📈 Visualization & Export</h3><p>Sequence Logo, Dot Plot, Hydropathy Plot, FASTA/CSV Export, Responsive UI</p><span class="badge">Polished</span><span class="badge">Cloud Deployed</span></div>', unsafe_allow_html=True)

st.markdown("---")

# --- QUICK START & STATUS ---
st.info("💡 **How to Use:** Select any tool from the sidebar. All modules support direct input, real-time analysis, and one-click export.")
st.success("✅ **Project Status:** 50+ Tools • Zero Dependencies • Streamlit Cloud Live • Actively Maintained")

# --- FOOTER NOTE ---
st.markdown("<div style='text-align: center; color: #4a5568; margin-top: 2rem; font-size: 0.85rem;'>Built with Python, Streamlit & Biopython | Open for Academic Collaboration</div>", unsafe_allow_html=True)