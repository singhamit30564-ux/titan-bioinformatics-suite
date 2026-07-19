import streamlit as st
from datetime import datetime

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧬 TITAN BIOINFORMATICS - MAIN DASHBOARD
# 👑 Built by Shivay Singh (Founder & CEO)
# 📱 Mobile-First | 🌍 Multilingual | ⚡ Lightning Fast
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Page Configuration
st.set_page_config(
    page_title="Titan Bioinformatics",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎨 TITAN PREMIUM THEME (Black, Gold, Crimson, White)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0a0e17;
        color: #e0e0e0;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1a1f2e;
        border-right: 2px solid #d4af37;
    }
    
    /* Gold Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #d4af37 0%, #f4d03f 100%);
        color: #0a0e17;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #f4d03f 0%, #d4af37 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
    }
    
    /* Headers - Gold Color */
    h1, h2, h3 {
        color: #d4af37 !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Text Input & Areas */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        background-color: #1a1f2e;
        color: #66fcf1;
        border: 1px solid #45a29e;
        border-radius: 5px;
    }
    
    /* Success Messages */
    .stSuccess {
        background-color: #1a4d2e;
        color: #90EE90;
        border-left: 4px solid #2ecc71;
    }
    
    /* Warning/Locked Messages */
    .stWarning {
        background-color: #4d2e1a;
        color: #ffd700;
        border-left: 4px solid #d4af37;
    }
    
    /* Custom Badge */
    .titan-badge {
        background: linear-gradient(135deg, #d4af37, #f4d03f);
        color: #0a0e17;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  MAIN DASHBOARD UI
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Header Section
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.markdown("<div style='font-size: 50px;'>🧬</div>", unsafe_allow_html=True)
with col_title:
    st.title("TITAN BIOINFORMATICS")
    st.caption("Next-Generation AI-Powered Bioinformatics Platform")

# Status Bar
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="titan-badge">⚡ Fast</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="titan-badge">🔒 Secure</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="titan-badge">🌍 Multilingual</div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="titan-badge">🎓 Student-Friendly</div>', unsafe_allow_html=True)

st.markdown("---")

# Welcome Section
st.markdown("""
## 🚀 Welcome to the Future of Biology

**Built by Shivay Singh** - A 12-year-old founder on a mission to make bioinformatics 
accessible to everyone, everywhere.

### Why Choose Titan?
✅ **50+ Professional Tools** - From DNA analysis to Clinical Genomics  
✅ **Mobile-First Design** - Works perfectly on your phone/tablet  
✅ **Multilingual Support** - Hindi, Spanish, Arabic & more (Coming Soon)  
✅ **Zero Ads** - Clean, distraction-free experience  
✅ **AI-Powered Assistant** - Dr. Titan helps you 24/7  
✅ **Free for Students** - First 100 students get lifetime access  

---
""")

# Features Grid
st.markdown("### 🧪 Available Tool Categories")

col_feat1, col_feat2, col_feat3 = st.columns(3)

with col_feat1:
    st.info("**🧬 Sequence Analysis**\n\nDNA/RNA Conversion, Translation, ORF Finder, GC Content")
    
with col_feat2:
    st.warning("**🏥 Clinical Genomics**\n\nClinVar Integration, Variant Analysis, Disease Mapping")
    
with col_feat3:
    st.error("**💊 Chemoinformatics**\n\nPubChem Search, Drug Design, Molecular Properties")

st.markdown("---")

# Founder's Message
st.markdown("""
### 👑 Founder's Note

> *"I'm building Titan because I believe every student, regardless of their location or 
> language, deserves access to world-class bioinformatics tools. This is just the beginning."*

**— Shivay Singh** (Founder & CEO, Titan Bioinformatics)

---
""")

# Footer
st.markdown("""
<div style='text-align: center; color: #66fcf1; padding: 20px;'>
    <p><b>🧬 Titan Bioinformatics</b> | Built with ❤️ by Shivay Singh</p>
    <p style='font-size: 12px; color: #95a5a6;'>
        Version 1.0.0 | © 2026 | Zero Data Retention Policy | Enterprise-Grade Security
    </p>
</div>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📱 SIDEBAR NAVIGATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

with st.sidebar:
    st.markdown("## 🛠️ TITAN TOOLS")
    st.markdown("---")
    
    # Navigation Menu
    st.markdown("### 📂 Categories")
    
    # Note: These links will activate once we create the files in the 'pages' folder
    st.page_link("pages/1_DNA_RNA_Conversion.py", label="🧬 DNA ↔ RNA", icon="🔄")
    st.page_link("pages/2_GC_Content.py", label="📊 GC Content", icon="📈")
    st.page_link("pages/3_Translation.py", label="🔬 Translation", icon="🧪")
    
    st.markdown("---")
    st.info("🚧 **More tools coming soon!**\n\n50+ tools under development")
    
    st.markdown("---")
    
    # User Status
    st.markdown("### 👤 Account")
    st.success("🎓 **Free Student Plan**\n\n✅ Unlimited Analysis\n❌ CSV Export (Locked)")
    
    st.markdown("---")
    
    # Language Selector (Future Feature)
    st.markdown("### 🌍 Language")
    lang = st.selectbox("Select Language", ["🇬🇧 English", "🇮🇳 हिंदी", "🇪🇸 Español", "🇸🇦 العربية"])
    
    st.markdown("---")
    
    # Contact
    st.markdown("### 📞 Support")
    st.markdown("[💬 Report Issue](#) | [📚 Documentation](#)")