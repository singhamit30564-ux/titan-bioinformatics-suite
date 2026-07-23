import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Distance Matrix", page_icon="📏", layout="wide")
st.title("📏 Module 4.08: Distance Matrix Calculator")
st.markdown("Calculate p-distance between aligned sequences and visualize as a heatmap.")
st.markdown("---")

# --- INPUT ---
fasta_input = st.text_area(
    "Enter Sequences in FASTA format",
    """>Human
ATGCGTACGT
>Chimp
ATGCGTACGA
>Gorilla
ATGCGTACCT
>Orangutan
ATGCGTACGG""",
    height=180
)

if st.button("🧮 Calculate Distance Matrix", type="primary", use_container_width=True):
    if not fasta_input.strip():
        st.error("⚠️ Please enter at least one sequence in FASTA format.")
    else:
        try:
            # --- ROBUST FASTA PARSER ---
            lines = fasta_input.strip().splitlines()
            seqs, names = [], []
            current_name, current_seq_parts = "", []
            
            for line in lines:
                clean = line.strip()
                if not clean: continue
                if clean.startswith(">"):
                    if current_name:
                        names.append(current_name)
                        seqs.append("".join(current_seq_parts).upper())
                    current_name = clean[1:].split()[0]
                    current_seq_parts = []
                else:
                    current_seq_parts.append(clean)
            if current_name:
                names.append(current_name)
                seqs.append("".join(current_seq_parts).upper())
                
            # --- VALIDATION ---
            if len(seqs) < 2:
                st.error("⚠️ Need at least 2 sequences to calculate a matrix.")
            else:
                lengths = [len(s) for s in seqs]
                if len(set(lengths)) > 1:
                    st.error(f"🚨 Sequences must be EQUAL length! Found: {lengths}. Align them first.")
                else:
                    valid_chars = set("ATCG-")
                    for i, s in enumerate(seqs):
                        invalid = set(s) - valid_chars
                        if invalid:
                            st.error(f" Invalid chars in '{names[i]}': {invalid}. Use only A,T,C,G,-")
                            break
                    else:
                        # --- CALCULATE P-DISTANCE ---
                        with st.spinner(" Calculating pairwise distances..."):
                            n = len(seqs)
                            L = lengths[0]
                            dist_matrix = np.zeros((n, n))
                            
                            for i in range(n):
                                for j in range(i + 1, n):
                                    diffs = sum(1 for a, b in zip(seqs[i], seqs[j]) if a != b and a != '-' and b != '-')
                                    dist = diffs / L
                                    dist_matrix[i, j] = dist
                                    dist_matrix[j, i] = dist
                            
                            # --- DISPLAY ---
                            df_dist = pd.DataFrame(dist_matrix, index=names, columns=names)
                            
                            st.markdown("###  Distance Matrix")
                            st.dataframe(df_dist.style.background_gradient(cmap="YlOrRd", vmin=0, vmax=1), use_container_width=True)
                            
                            fig = px.imshow(
                                df_dist.values,
                                x=names, y=names,
                                text_auto=".3f",
                                aspect="auto",
                                color_continuous_scale="Viridis",
                                title="Pairwise p-Distance Heatmap"
                            )
                            fig.update_layout(template="plotly_dark", paper_bgcolor='#0a0e17', plot_bgcolor='#1a1f2e')
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.success(f"✅ Matrix calculated for {n} sequences (Length: {L} bp)")
                            
        except Exception as e:
            st.error(f"🚨 Unexpected Error: {str(e)}")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ℹ️ How It Works")
    st.markdown("""
    1. Paste **aligned** sequences in FASTA format
    2. All sequences MUST be same length
    3. Tool calculates **p-distance** (proportional difference)
    4. Heatmap shows evolutionary divergence
    """)
    st.info("💡 **Tip:** Use MSA tools (Clustal, MUSCLE) before this step!")
# --- DR. TITAN'S TIP ---
st.markdown("""
---
💡 **Dr. Titan's Tip:** 
p-distance of 0.01 = 1% sequence divergence. For reference:
- **Human vs Chimp**: ~0.012 (1.2% different)
- **Human vs Gorilla**: ~0.018 (1.8% different)
- Values >0.10 indicate distant evolutionary relationship
- Always use **aligned sequences** (MSA) before calculating distances!
""")