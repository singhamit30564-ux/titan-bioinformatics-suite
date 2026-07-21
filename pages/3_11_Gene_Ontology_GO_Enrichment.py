import streamlit as st
import plotly.express as px
import pandas as pd
import random

st.title("🧬 Module 3.11: Gene Ontology (GO) Enrichment Analyzer")
st.markdown("Analyze and visualize enriched Biological Processes, Molecular Functions, and Cellular Components.")
st.markdown("---")

# Mock Database for demonstration (In real app, this connects to GO.db or API)
go_database = {
    "GO:0006915": {"term": "Apoptotic Process", "category": "Biological Process", "p_value": 0.001, "count": 15},
    "GO:0005524": {"term": "ATP Binding", "category": "Molecular Function", "p_value": 0.005, "count": 22},
    "GO:0005634": {"term": "Nucleus", "category": "Cellular Component", "p_value": 0.01, "count": 30},
    "GO:0006955": {"term": "Immune Response", "category": "Biological Process", "p_value": 0.0001, "count": 18},
    "GO:0004672": {"term": "Protein Kinase Activity", "category": "Molecular Function", "p_value": 0.02, "count": 12},
    "GO:0016020": {"term": "Membrane", "category": "Cellular Component", "p_value": 0.03, "count": 25},
    "GO:0006351": {"term": "Transcription, DNA-templated", "category": "Biological Process", "p_value": 0.004, "count": 20},
    "GO:0003677": {"term": "DNA Binding", "category": "Molecular Function", "p_value": 0.008, "count": 14}
}

st.markdown("### 📥 Input Gene List")
gene_input = st.text_area("Enter Gene IDs or Names (comma or newline separated)", 
    "TP53, BRCA1, EGFR, MYC, AKT1, MTOR, PTEN, KRAS", height=100)

if st.button("🔬 Run GO Enrichment Analysis", type="primary", use_container_width=True):
    genes = [g.strip().upper() for g in gene_input.replace(',', '\n').split('\n') if g.strip()]
    
    if len(genes) < 2:
        st.error("❌ Please enter at least 2 genes!")
    else:
        with st.spinner("🧮 Querying GO Database & Calculating P-values..."):
            # Simulate enrichment results based on input
            results = []
            for go_id, data in go_database.items():
                # Simulate that some genes map to this GO term
                mapped_genes = random.sample(genes, min(data['count'], len(genes)))
                results.append({
                    "GO ID": go_id,
                    "Term": data['term'],
                    "Category": data['category'],
                    "Gene Count": len(mapped_genes),
                    "P-Value": data['p_value'],
                    "-log10(P-Value)": -np.log10(data['p_value']),
                    "Mapped Genes": ", ".join(mapped_genes)
                })
            
            df = pd.DataFrame(results).sort_values(by="P-Value")
            
            st.markdown("### 📊 Enrichment Results")
            
            # Volcano-style Bar Chart (-log10 P-value)
            fig = px.bar(
                df, 
                x="Term", 
                y="-log10(P-Value)", 
                color="Category",
                color_discrete_map={
                    "Biological Process": "#d4af37",      # Titan Gold
                    "Molecular Function": "#66fcf1",      # Cyan
                    "Cellular Component": "#ff0055"       # Red
                },
                hover_data=["GO ID", "Gene Count", "Mapped Genes"],
                title="GO Enrichment Significance (-log10 P-value)"
            )
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                font=dict(color='#e0e0e0'),
                xaxis_title="Gene Ontology Term",
                yaxis_title="-log10(P-Value) (Higher = More Significant)",
                xaxis_tickangle=-45
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed Table
            st.markdown("### 📋 Detailed GO Terms Table")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download GO Results (CSV)", csv, "go_enrichment.csv", "text/csv")

            st.info("💡 **Dr. Titan's Tip:** A low P-value (< 0.05) and high -log10(P-value) means the term is significantly enriched in your gene list, suggesting a common biological theme (e.g., all your genes are involved in 'Apoptosis')!")