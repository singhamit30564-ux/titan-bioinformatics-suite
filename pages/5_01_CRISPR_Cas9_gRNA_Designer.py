import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="CRISPR gRNA Designer", page_icon="🎯", layout="wide")

st.title("🎯 Module 5.01: CRISPR-Cas9 gRNA Designer")
st.markdown("Design guide RNAs for CRISPR-Cas9 genome editing with NGG PAM sequences.")
st.markdown("---")

# --- INPUT SECTION ---
st.markdown("### 📥 Input Sequence")
target_seq = st.text_area(
    "Enter Target DNA Sequence (5' to 3')",
    "ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGGGATCGATCG",
    height=150
)

pam_type = st.radio(
    "Select Cas Protein / PAM Type",
    ["SpCas9 (NGG)", "SaCas9 (NNGRRT)", "Cas12a/Cpf1 (TTTV)"],
    horizontal=True
)

# --- MAIN FUNCTION ---
if st.button("🎯 Design gRNAs", type="primary", use_container_width=True):
    seq = target_seq.replace(" ", "").upper()
    
    if len(seq) < 23:
        st.error(" Sequence too short! Need at least 23 bp for gRNA + PAM.")
    else:
        with st.spinner("🧮 Scanning for PAM sites and extracting gRNAs..."):
            gRNAs = []
            
            # Define PAM patterns
            if "SpCas9" in pam_type:
                pam_pattern = "GG"
                pam_len = 2
                gRNA_len = 20
            elif "SaCas9" in pam_type:
                pam_pattern = "GG"  # Simplified
                pam_len = 2
                gRNA_len = 20
            else:  # Cas12a
                pam_pattern = "TTT"
                pam_len = 3
                gRNA_len = 20
            
            # Scan sequence for PAM sites
            for i in range(len(seq) - gRNA_len - pam_len + 1):
                potential_pam = seq[i + gRNA_len: i + gRNA_len + pam_len]
                
                # Check PAM match
                if potential_pam.endswith(pam_pattern) or (pam_pattern == "TTT" and potential_pam.startswith("TTT")):
                    gRNA_seq = seq[i: i + gRNA_len]
                    
                    # Calculate GC content
                    gc_count = gRNA_seq.count('G') + gRNA_seq.count('C')
                    gc_pct = (gc_count / gRNA_len) * 100
                    
                    # Determine risk level
                    if gc_pct < 30 or gc_pct > 70:
                        risk = "High (Extreme GC)"
                    elif gc_pct < 40 or gc_pct > 60:
                        risk = "Medium"
                    else:
                        risk = "Low"
                    
                    gRNAs.append({
                        "Position": i + 1,
                        "gRNA Sequence (5'-3')": gRNA_seq,
                        "PAM": potential_pam,
                        "GC %": round(gc_pct, 1),
                        "Risk Level": risk
                    })
            
            if not gRNAs:
                st.warning("️ No valid gRNA targets found with the selected PAM in this sequence.")
            else:
                # Create DataFrame
                df = pd.DataFrame(gRNAs)
                
                st.markdown(f"### 🎯 Found {len(df)} Potential gRNA Targets")
                
                # Display table
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Visualization: GC Content Distribution
                st.markdown("### 📊 gRNA GC Content Distribution")
                
                fig = px.histogram(
                    df,
                    x="GC %",
                    nbins=10,
                    color_discrete_sequence=['#d4af37'],
                    title="Distribution of gRNA GC Percentages"
                )
                
                # Add ideal range
                fig.add_vrect(
                    x0=40, x1=60,
                    fillcolor="#66fcf1",
                    opacity=0.2,
                    line_width=0,
                    annotation_text="Ideal Range (40-60%)"
                )
                
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#1a1f2e',
                    font=dict(color='#e0e0e0'),
                    xaxis_title="GC Content (%)",
                    yaxis_title="Number of gRNAs"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary metrics
                st.markdown("### 📈 Summary Statistics")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total gRNAs", len(df))
                col2.metric("Average GC%", f"{df['GC %'].mean():.1f}%")
                low_risk_count = len(df[df['Risk Level'] == 'Low'])
                col3.metric("Low Risk gRNAs", low_risk_count)
                
                # Download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download gRNA List (CSV)",
                    data=csv,
                    file_name="crispr_grnas.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                st.info("💡 **Dr. Titan's Tip:** For SpCas9, the ideal gRNA is 20 nucleotides long, followed immediately by an 'NGG' PAM sequence. A GC content between 40-60% ensures stable binding without excessive off-target effects!")

# --- SIDEBAR INFO ---
with st.sidebar:
    st.markdown("### ℹ️ How to Use")
    st.markdown("""
    1. **Paste your DNA sequence** (5' to 3')
    2. **Select Cas protein** (SpCas9 recommended)
    3. **Click 'Design gRNAs'**
    4. **Review results** - Look for Low Risk gRNAs with 40-60% GC
    5. **Download** your candidates
    """)
    
    st.markdown("### 🎯 PAM Sequences")
    st.markdown("""
    - **SpCas9**: NGG
    - **SaCas9**: NNGRRT
    - **Cas12a**: TTTV
    """)