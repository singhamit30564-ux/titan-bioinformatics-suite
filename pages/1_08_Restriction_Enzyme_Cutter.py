import streamlit as st
from Bio.Seq import Seq
from Bio.Restriction import EcoRI, BamHI, HindIII, PstI, SalI, XhoI, NotI, SmaI, KpnI, XbaI
import pandas as pd
import plotly.express as px

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✂️ TITAN TOOL 8: RESTRICTION ENZYME CUTTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.title("✂️ Module 8: Restriction Enzyme Cutter")
st.markdown("Scan your DNA sequence for cut sites of the 10 most common restriction enzymes.")
st.markdown("---")

# --- INPUT SECTION ---
dna_input = st.text_area(
    "Enter DNA Sequence (5' to 3'):", 
    "GAATTCGCGGCCGCAAGCTTGGATCCCCTCGAGGTCGACGCGGCCGC", 
    height=150, 
    key="re_cutter_input"
)

st.markdown("<br>", unsafe_allow_html=True)
calculate_btn = st.button("✂️ Scan for Cut Sites", use_container_width=True, type="primary")

# --- PROCESSING & OUTPUT ---
if calculate_btn:
    clean_dna = dna_input.replace(" ", "").replace("\n", "").upper()
    
    if not clean_dna:
        st.error("❌ Please enter a valid DNA sequence.")
    elif any(char not in "ATCG" for char in clean_dna):
        st.error("❌ Invalid DNA! Only A, T, C, G are allowed.")
    else:
        try:
            seq = Seq(clean_dna)
            
            # Dictionary of enzymes to check
            enzymes_to_check = {
                'EcoRI': EcoRI,
                'BamHI': BamHI,
                'HindIII': HindIII,
                'PstI': PstI,
                'SalI': SalI,
                'XhoI': XhoI,
                'NotI': NotI,
                'SmaI': SmaI,
                'KpnI': KpnI,
                'XbaI': XbaI
            }
            
            cut_results = []
            total_cuts = 0
            
            for enz_name, enz_class in enzymes_to_check.items():
                # Biopython's search function returns a list of cut positions (1-based index)
                cut_sites = enz_class.search(seq)
                
                if cut_sites:
                    total_cuts += len(cut_sites)
                    cut_results.append({
                        'Enzyme': enz_name,
                        'Recognition_Site': str(enz_class.site),
                        'Cut_Count': len(cut_sites),
                        'Cut_Positions': ", ".join(map(str, cut_sites))
                    })
                else:
                    cut_results.append({
                        'Enzyme': enz_name,
                        'Recognition_Site': str(enz_class.site),
                        'Cut_Count': 0,
                        'Cut_Positions': "None"
                    })
            
            # Sort by cut count (descending)
            cut_results.sort(key=lambda x: x['Cut_Count'], reverse=True)
            df_results = pd.DataFrame(cut_results)
            
            # --- DISPLAY METRICS ---
            st.markdown("### 📊 Digestion Statistics")
            met_col1, met_col2, met_col3 = st.columns(3)
            met_col1.metric("📏 Sequence Length", f"{len(seq)} bp")
            met_col2.metric("✂️ Total Cut Sites", f"{total_cuts}")
            met_col3.metric("🧬 Enzymes that Cut", f"{len([r for r in cut_results if r['Cut_Count'] > 0])} / 10")
            
            st.markdown("---")
            
            # --- CUT FREQUENCY CHART ---
            st.markdown("### 📊 Cut Frequency by Enzyme")
            
            # Filter only enzymes that actually cut for a cleaner chart
            df_chart = df_results[df_results['Cut_Count'] > 0].copy()
            
            if not df_chart.empty:
                fig = px.bar(
                    df_chart, 
                    x='Enzyme', 
                    y='Cut_Count',
                    color='Enzyme',
                    color_discrete_sequence=px.colors.qualitative.Bold,
                    text_auto=True
                )
                
                fig.update_layout(
                    title="Number of Cut Sites per Enzyme",
                    xaxis_title="Restriction Enzyme",
                    yaxis_title="Number of Cuts",
                    yaxis=dict(dtick=1), # Force integer steps on y-axis
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#1a1f2e',
                    font=dict(color='#e0e0e0'),
                    showlegend=False,
                    margin=dict(t=40, b=40, l=40, r=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("---")
            else:
                st.info("ℹ️ No cut sites found for any of the 10 tested enzymes in this sequence.")
            
            # --- DETAILED TABLE ---
            st.markdown("### 📋 Detailed Cut Site Map")
            
            # Highlight rows where cuts were found
            def highlight_cuts(val):
                if isinstance(val, int) and val > 0:
                    return 'background-color: #d4af37; color: #000; font-weight: bold' # Gold
                return ''
                
            st.dataframe(
                df_results.style.applymap(highlight_cuts, subset=['Cut_Count']),
                use_container_width=True,
                hide_index=True
            )
            
            # --- THE "SMART LOCK" ---
            st.markdown("---")
            st.markdown("### 📥 Export Data")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📄 Download PDF Report (Free)", use_container_width=True):
                    st.info("📄 Generating PDF report... (Feature coming in v1.1)")
                    
            with col_btn2:
                if st.button("📊 Download CSV Data (🔒 Explorer Plan)", use_container_width=True):
                    st.warning("🔒 **Titan Explorer Plan Required.**\n\nUpgrade to unlock CSV exports, batch processing, and advanced analytics.")
                    
        except Exception as e:
            st.error(f"⚠️ Calculation Error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💡 Dr. Titan AI Tip
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
st.info("💡 **Dr. Titan's Tip:** Restriction enzymes are the 'molecular scissors' of biology. For example, **EcoRI** recognizes 'GAATTC' and cuts between G and A, leaving 'sticky ends' that are perfect for cloning!")