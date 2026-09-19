import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from collections import Counter

st.title("🔬 Module 3.03: N-grams Over/Under-Representation Analysis")
st.markdown("Find statistically over-represented or under-represented motifs (N-grams) in your DNA sequence.")
st.markdown("---")

dna_seq = st.text_area("Enter DNA Sequence", 
    "ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG", 
    height=150)

n_value = st.slider("N-gram Size (N)", 2, 5, 3, help="Length of the word to analyze (e.g., N=3 for 3-mers)")

if st.button(" Analyze N-gram Statistics", type="primary", use_container_width=True):
    seq = dna_seq.replace(" ", "").upper()
    valid_seq = [base for base in seq if base in 'ACGT']
    clean_seq = "".join(valid_seq)
    
    if len(clean_seq) < n_value:
        st.error(f"❌ Sequence too short! Need at least {n_value} bp.")
    else:
        with st.spinner("🧮 Calculating Observed vs Expected Frequencies..."):
            # 1. Extract N-grams
            ngrams = [clean_seq[i:i+n_value] for i in range(len(clean_seq) - n_value + 1)]
            observed_counts = Counter(ngrams)
            total_ngrams = len(ngrams)
            
            # 2. Calculate Expected Frequency (Markov Chain 0-order: Product of individual base frequencies)
            base_counts = Counter(clean_seq)
            total_bases = len(clean_seq)
            base_probs = {base: count / total_bases for base, count in base_counts.items()}
            
            expected_freqs = {}
            for ngram in observed_counts.keys():
                prob = 1.0
                for base in ngram:
                    prob *= base_probs.get(base, 0.001) # Avoid zero division
                expected_freqs[ngram] = prob * total_ngrams
                
            # 3. Calculate Z-Score (Over/Under Representation)
            results = []
            for ngram, obs in observed_counts.items():
                exp = expected_freqs.get(ngram, 0)
                # Z-score formula: (Observed - Expected) / sqrt(Expected)
                z_score = (obs - exp) / np.sqrt(exp) if exp > 0 else 0
                results.append({
                    'N-gram': ngram,
                    'Observed': obs,
                    'Expected': round(exp, 2),
                    'Z-Score': round(z_score, 2)
                })
                
            df = pd.DataFrame(results).sort_values(by='Z-Score', ascending=False)
            
            # 4. Visualization
            st.markdown("### 📈 Z-Score Distribution (Over vs Under Represented)")
            
            # Color code: Green for over-represented, Red for under-represented
            df['Color'] = df['Z-Score'].apply(lambda x: '#66fcf1' if x > 0 else '#ff0055')
            
            fig = px.bar(
                df.head(15), # Show top 15
                x='N-gram', 
                y='Z-Score', 
                color='Color',
                title=f"Top N-grams by Z-Score (N={n_value})",
                labels={'Z-Score': 'Statistical Significance (Z-Score)'}
            )
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='#0a0e17',
                plot_bgcolor='#1a1f2e',
                font=dict(color='#e0e0e0'),
                showlegend=False,
                yaxis=dict(title="Z-Score (Positive = Over-represented)")
            )
            
            # Add a zero line
            fig.add_hline(y=0, line_dash="dash", line_color="white")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Data Table
            st.markdown("### 📋 Detailed Statistics")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.info("💡 **Dr. Titan's Tip:** A high positive Z-score means the motif appears much more often than random chance (likely a functional motif like a binding site). A high negative Z-score means it's actively avoided by the genome!")