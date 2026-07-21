import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.title(" Module 3.09: VCF Variant Viewer")
st.markdown("Parse and visualize Variant Call Format (VCF) files to analyze SNPs and Indels.")
st.markdown("---")

# --- INPUT SECTION ---
vcf_input = st.text_area("Paste VCF Content (or upload below)", 
    """##fileformat=VCFv4.2
##INFO=<ID=DP,Number=1,Type=Integer,Description="Total Depth">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t100\trs123\tA\tG\t50\tPASS\tDP=30
chr1\t150\trs124\tC\tT\t45\tPASS\tDP=25
chr1\t200\trs125\tG\tGAT\t60\tPASS\tDP=40
chr2\t50\trs126\tT\tC\t55\tLowQual\tDP=10
chr2\t100\trs127\tA\tA\t30\tPASS\tDP=15""", 
    height=250)

uploaded_file = st.file_uploader("Or Upload a .vcf file", type=["vcf", "txt"])

if st.button("🔬 Parse VCF Data", type="primary", use_container_width=True):
    data_to_parse = vcf_input
    if uploaded_file is not None:
        data_to_parse = uploaded_file.getvalue().decode("utf-8")
        
    if not data_to_parse.strip():
        st.error("❌ Please paste VCF content or upload a file!")
    else:
        with st.spinner(" Parsing Variants..."):
            try:
                # Parse VCF
                lines = data_to_parse.strip().split('\n')
                header_line = ""
                data_lines = []
                
                for line in lines:
                    if line.startswith('#CHROM'):
                        header_line = line[2:] # Remove ##
                    elif not line.startswith('#'):
                        data_lines.append(line)
                
                if not header_line or not data_lines:
                    st.warning("⚠️ No valid VCF data found. Ensure it has a #CHROM header line.")
                else:
                    # Create DataFrame
                    columns = header_line.split('\t')
                    df = pd.DataFrame([line.split('\t') for line in data_lines], columns=columns)
                    
                    # Convert POS to numeric
                    df['POS'] = pd.to_numeric(df['POS'], errors='coerce')
                    
                    st.markdown("### 📋 Variant Table")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # --- ANALYSIS & CHARTS ---
                    st.markdown("### 📊 Variant Analysis")
                    
                    # 1. Variant Type (SNP vs INDEL)
                    def get_variant_type(row):
                        if len(row['REF']) == 1 and len(row['ALT']) == 1:
                            return "SNP"
                        elif len(row['REF']) > len(row['ALT']):
                            return "Deletion"
                        elif len(row['REF']) < len(row['ALT']):
                            return "Insertion"
                        else:
                            return "Complex"
                            
                    df['Type'] = df.apply(get_variant_type, axis=1)
                    
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.markdown("**Variant Types Distribution**")
                        type_counts = df['Type'].value_counts().reset_index()
                        type_counts.columns = ['Type', 'Count']
                        
                        fig_pie = px.pie(type_counts, values='Count', names='Type', 
                                         color_discrete_sequence=['#d4af37', '#66fcf1', '#ff0055', '#ffffff'],
                                         hole=0.4)
                        fig_pie.update_layout(paper_bgcolor='#0a0e17', font=dict(color='#e0e0e0'))
                        st.plotly_chart(fig_pie, use_container_width=True)
                        
                    with c2:
                        st.markdown("**Chromosome Distribution**")
                        chrom_counts = df['CHROM'].value_counts().reset_index()
                        chrom_counts.columns = ['Chromosome', 'Count']
                        
                        fig_bar = px.bar(chrom_counts, x='Chromosome', y='Count',
                                         color_discrete_sequence=['#d4af37'])
                        fig_bar.update_layout(paper_bgcolor='#0a0e17', plot_bgcolor='#1a1f2e', font=dict(color='#e0e0e0'))
                        st.plotly_chart(fig_bar, use_container_width=True)
                        
                    # 2. Transition vs Transversion (Ti/Tv) for SNPs
                    snps = df[df['Type'] == 'SNP']
                    transitions = 0
                    transversions = 0
                    pairs = [('A','G'), ('G','A'), ('C','T'), ('T','C')]
                    
                    for _, row in snps.iterrows():
                        if (row['REF'], row['ALT']) in pairs:
                            transitions += 1
                        else:
                            transversions += 1
                            
                    titv_ratio = transitions / transversions if transversions > 0 else 0
                    
                    st.markdown("### 🧬 SNP Analysis (Ti/Tv Ratio)")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total SNPs", len(snps))
                    col2.metric("Transitions (Ti)", transitions)
                    col3.metric("Transversions (Tv)", transversions)
                    
                    st.info(f"**Ti/Tv Ratio:** `{titv_ratio:.2f}` (Normal human genome is ~2.0-2.1)")
                    
                    # Download button
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("️ Download Parsed Variants (CSV)", csv, "variants.csv", "text/csv")

            except Exception as e:
                st.error(f"❌ Parsing Error: {e}. Please check VCF format.")

st.info("💡 **Dr. Titan's Tip:** VCF (Variant Call Format) is the standard file type for storing gene sequence variations. A Ti/Tv ratio of ~2.0 indicates high-quality whole-genome sequencing data!")