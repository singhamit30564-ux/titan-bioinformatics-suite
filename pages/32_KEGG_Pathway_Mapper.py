import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.title("🗺️ Module 3.12: KEGG Pathway Mapper & Visualizer")
st.markdown("Map your gene list to biological pathways and visualize the interactions using a network graph.")
st.markdown("---")

# --- INPUT SECTION ---
gene_input = st.text_area("Enter Gene List (comma or newline separated)", 
    "TP53, BRCA1, EGFR, MYC, AKT1, MTOR, PTEN, KRAS, CDK4, RB1", height=150)

if st.button("️ Map to KEGG Pathways", type="primary", use_container_width=True):
    genes = [g.strip().upper() for g in gene_input.replace(',', '\n').split('\n') if g.strip()]
    
    if len(genes) < 2:
        st.error("❌ Please enter at least 2 genes!")
    else:
        with st.spinner("🧮 Querying KEGG Database & Building Network..."):
            
            # Mock KEGG Pathway Database (Real-world logic simulation)
            kegg_db = {
                "p53 signaling pathway": ["TP53", "MDM2", "ATM", "ATR", "CDKN1A", "BAX", "PUMA"],
                "Cell cycle": ["CDK4", "RB1", "TP53", "MYC", "CCND1", "E2F1"],
                "PI3K-Akt signaling pathway": ["AKT1", "MTOR", "PTEN", "PIK3CA", "EGFR", "KRAS"],
                "Homologous recombination": ["BRCA1", "BRCA2", "RAD51", "PALB2", "ATM"],
                "Pathways in cancer": ["TP53", "BRCA1", "EGFR", "MYC", "AKT1", "MTOR", "PTEN", "KRAS", "CDK4", "RB1"],
                "MicroRNAs in cancer": ["TP53", "MYC", "KRAS", "EGFR", "PTEN"]
            }
            
            # Filter pathways that contain at least one of our input genes
            mapped_pathways = {}
            for pathway, pathway_genes in kegg_db.items():
                common_genes = [g for g in genes if g in pathway_genes]
                if common_genes:
                    mapped_pathways[pathway] = common_genes
                    
            if not mapped_pathways:
                st.warning("️ No KEGG pathways found for the provided genes. Try adding TP53, BRCA1, or EGFR.")
            else:
                # --- NETWORK GRAPH VISUALIZATION ---
                st.markdown("### 🕸️ Gene-Pathway Interaction Network")
                
                nodes = []
                edges = []
                node_colors = []
                node_sizes = []
                node_text = []
                
                # Add Pathway Nodes (Central)
                for i, pathway in enumerate(mapped_pathways.keys()):
                    nodes.append(pathway)
                    node_colors.append('#d4af37') # Titan Gold for Pathways
                    node_sizes.append(30)
                    node_text.append(f"<b>Pathway:</b> {pathway}<br>Genes: {len(mapped_pathways[pathway])}")
                    
                    # Add Gene Nodes & Edges
                    for gene in mapped_pathways[pathway]:
                        if gene not in nodes:
                            nodes.append(gene)
                            node_colors.append('#66fcf1') # Cyan for Genes
                            node_sizes.append(15)
                            node_text.append(f"<b>Gene:</b> {gene}")
                        
                        edges.append((pathway, gene))
                
                # Calculate positions for a circular layout
                n_nodes = len(nodes)
                theta = np.linspace(0, 2 * np.pi, n_nodes)
                x_pos = np.cos(theta)
                y_pos = np.sin(theta)
                
                node_positions = {node: (x, y) for node, x, y in zip(nodes, x_pos, y_pos)}
                
                # Create Edge Traces
                edge_x = []
                edge_y = []
                for edge in edges:
                    x0, y0 = node_positions[edge[0]]
                    x1, y1 = node_positions[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    
                edge_trace = go.Scatter(
                    x=edge_x, y=edge_y,
                    line=dict(width=1, color='#555555'),
                    hoverinfo='none',
                    mode='lines')
                
                # Create Node Trace
                node_x = [node_positions[node][0] for node in nodes]
                node_y = [node_positions[node][1] for node in nodes]
                
                node_trace = go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    hoverinfo='text',
                    hovertext=node_text,
                    text=[node if len(node) < 10 else node[:8]+'..' for node in nodes],
                    textposition="top center",
                    marker=dict(
                        showscale=False,
                        color=node_colors,
                        size=node_sizes,
                        line_width=2))
                
                fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='KEGG Pathway Interaction Network',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        template="plotly_dark",
                        paper_bgcolor='#0a0e17',
                        plot_bgcolor='#1a1f2e'))
                
                st.plotly_chart(fig, use_container_width=True)
                
                # --- DATA TABLE ---
                st.markdown("### 📋 Mapped Pathways Details")
                table_data = []
                for pathway, genes_list in mapped_pathways.items():
                    table_data.append({
                        "KEGG Pathway": pathway,
                        "Mapped Genes": ", ".join(genes_list),
                        "Gene Count": len(genes_list)
                    })
                    
                df = pd.DataFrame(table_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Pathway Map (CSV)", csv, "kegg_mapping.csv", "text/csv")

                st.info("💡 **Dr. Titan's Tip:** KEGG (Kyoto Encyclopedia of Genes and Genomes) maps genes to biological pathways. If your genes cluster heavily in the 'p53 signaling pathway', it strongly suggests the sample is undergoing cell-cycle arrest or apoptosis!")