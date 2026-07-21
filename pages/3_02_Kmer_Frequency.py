import streamlit as st
import plotly.express as px
import pandas as pd
from collections import Counter

st.title("🧩 Module 3.02: K-mer Frequency Analyzer")
st.markdown("Count and visualize the frequency of all possible K-mers (subsequences of length K) in a DNA sequence.")
st.markdown("---")

dna_seq = st.text_area("Enter DNA Sequence", 
    "ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG", 
    height=150)

k_value = st.slider("K-mer Size (K)", 2, 6, 3, help="Length of the subsequence to count (e.g., K=3 means 3-base words like 'ATG')")
top_n = st.slider("Show Top N K-mers", 5, 20, 10)

if st.button("🔍 Analyze K-mer Frequency", type="primary", use_container_width=True):
    seq = dna_seq.replace(" ", "").upper()
    
    # Filter only valid nucleotides
    valid_seq = [base for base in seq if base in 'ACGT']
    clean_seq = "".join(valid_seq)
    
    if len(clean_seq) < k_value:
        st.error(f"❌ Sequence too short! Need at least {k_value} bp for K={k_value}.")
    else:
        with st.spinner("🧮 Counting K-mers..."):
            # Extract all K-mers
            kmers = [clean_seq[i:i+k_value] for i in range(len(clean_seq) - k_value + 1)]
            
            # Count frequencies
            kmer_counts = Counter(kmers)
            total_kmers = len(kmers)
            unique_kmers = len(kmer_counts)
            
            # Create DataFrame for plotting
            df = pd.DataFrame.from_dict(kmer_counts, orient='index', columns=['Count']).reset_index()
            df.columns = ['K-mer', 'Count']
            df = df.sort_values(by='Count', ascending=False).head(top_n)
            df['Frequency (%)'] = (df['Count'] / total_kmers) * 100
            
            # Display Metrics
            st.markdown("### 📊 Summary Statistics")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total K-mers", f"{total_kmers:,}")
            c2.metric("Unique K-mers", f"{unique_kmers}")
            c3.metric("Max Frequency", f"{df.iloc[0]['Frequency (%)']:.2f}%")
            
            # Plotly Bar Chart
            st.markdown(f"### 📈 Top {top_n} Most Frequent {k_value}-mers")
            fig = px.bar(
                df, 
                x='K-mer', 
                y='Count', 
                text='Count',
                color='K-mer',
                color_discrete_sequence=px.colors.sequential.YlOrBr # Titan Gold/Orange theme
            )
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                font=dict(color='#e0e0e0'),
                xaxis_title=f"K-mer Sequence (K={k_value})",
                yaxis_title="Frequency Count",
                showlegend=False
            )
            
            # Add text on top of bars
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Full Table
            with st.expander("📋 View Full K-mer Table"):
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.info("💡 **Dr. Titan's Tip:** K-mer analysis is the foundation of genome assembly and species identification! A sudden spike in a specific K-mer often indicates repetitive elements or sequencing errors.")