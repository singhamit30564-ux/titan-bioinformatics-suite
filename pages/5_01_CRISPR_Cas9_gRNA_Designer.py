import streamlit as st
import pandas as pd
import plotly.express as px

st.title("✂️ Module 5.01: CRISPR-Cas9 gRNA Designer")
st.markdown("Identify potential guide RNA (gRNA) targets with NGG PAM sequences and analyze their GC content.")
st.markdown("---")

# --- INPUT SECTION ---
target_seq = st.text_area("Enter Target DNA Sequence (5' to 3')", 
    "ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGGGATCGATCG", 
    height=150)

pam_type = st.radio("Select Cas Protein / PAM Type", 
    ["SpCas9 (NGG)", "SaCas9 (NNGRRT)", "Cas12a/Cpf1 (TTTV)"], 
    horizontal=True)

if st.button("🎯 Design gRNAs", type="primary", use_container_width=True):
    seq = target_seq.replace(" ", "").upper()
    
    if len(seq) < 23:
        st.error("❌ Sequence too short! Need at least 23 bp for gRNA + PAM.")
    else:
        with st.spinner("🧮 Scanning for PAM sites and extracting gRNAs..."):
            gRNAs = []
            
            # Define PAM regex patterns (simplified for scanning)
            if "SpCas9" in pam_type:
                pam_pattern = "GG"
                pam_len = 2
                gRNA_len = 20
            elif "SaCas9" in pam_type:
                pam_pattern = "GG" # Simplified for demo, real is NNGRRT
                pam_len = 2
                gRNA_len = 20
            else: # Cas12a
                pam_pattern = "TTT"
                pam_len = 3
                gRNA_len = 20
                
            # Scan sequence
            for i in range(len(seq) - gRNA_len - pam_len + 1):
                potential_pam = seq[i+gRNA_len : i+gRNA_len+pam_len]
                
                # Check if it matches PAM (simplified match for SpCas9 'GG')
                if potential_pam.endswith(pam_pattern) or (pam_pattern == "TTT" and potential_pam.startswith("TTT")):
                    gRNA_seq = seq[i : i+gRNA_len]
                    
                    # Calculate GC content of the gRNA (Ideal is 40-60%)
                    gc_count = gRNA_seq.count('G') + gRNA_seq.count('C')
                    gc_pct = (gc_count / gRNA_len) * 100
                    
                    # Simple off-target risk score (mock logic: lower GC at 3' end is better, but we'll just flag extreme GC)
                    risk = "Low"
                    if gc_pct < 30 or gc_pct > 70:
                        risk = "High (Extreme GC)"
                    elif gc_pct < 40 or gc_pct > 60:
                        risk = "Medium"
                        
                    gRNAs.append({
                        "Position": i + 1,
                        "gRNA Sequence (5'-3')": gRNA_seq,
                        "PAM": potential_pam,
                        "GC %": round(gc_pct, 1),
                        "Risk Level": risk
                    })
            
            if not gRNAs:
                st.warning("⚠️ No valid gRNA targets found with the selected PAM in this sequence.")
            else:
                df = pd.DataFrame(gRNAs)
                
                st.markdown(f"### 🎯 Found {len(df)} Potential gRNA Targets")
                
                # Color code the risk level
                def color_risk(val):
                    if val == "Low": return 'background-color: #1a472a; color: #66fcf1' # Greenish
                    if val == "Medium": return 'background-color: #4a3b00; color: #d4af37' # Goldish
                    return 'background-color: #4a0000; color: #ff0055' # Reddish

                st.dataframe(df.style.applymap(color_risk, subset=['Risk Level']), use_container_width=True, hide_index=True)
                
                # Visualization: GC Content Distribution
                st.markdown("### 📊 gRNA GC Content Distribution")
                fig = px.histogram(
                    df, 
                    x="GC %", 
                    nbins=10,
                    color_discrete_sequence=['#d4af37'],
                    title="Distribution of gRNA GC Percentages"
                )
                
                # Add ideal range lines
                fig.add_vrect(x0=40, x1=60, fillcolor="#66fcf1", opacity=0.2, line_width=0, annotation_text="Ideal Range (40-60%)")
                
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#1a1f2e',
                    font=dict(color='#e0e0e0'),
                    xaxis_title="GC Content (%)",
                    yaxis_title="Number of gRNAs"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Download button
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download gRNA List (CSV)", csv, "crispr_grnas.csv", "text/csv")

                st.info("💡 **Dr. Titan's Tip:** For SpCas9, the ideal gRNA is 20 nucleotides long, followed immediately by an 'NGG' PAM sequence. A GC content between 40-60% ensures stable binding without excessive off-target effects!")