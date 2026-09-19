import streamlit as st
from Bio import Phylo
from Bio.Phylo.TreeConstruction import DistanceCalculator, DistanceTreeConstructor
from Bio.Align import MultipleSeqAlignment
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import matplotlib.pyplot as plt
import io

st.title("🌳 Module 4.07: Phylogenetic Tree Builder")
st.markdown("Construct evolutionary trees using UPGMA or Neighbor-Joining (NJ) algorithms.")
st.markdown("---")

# --- INPUT ---
fasta_input = st.text_area("Enter Sequences in FASTA format", 
    """>Human
ATGCGTACGT
>Chimp
ATGCGTACGA
>Gorilla
ATGCGTACCT
>Orangutan
ATGCGTACGG""", height=200)

method = st.radio("Tree Building Method", ["UPGMA", "Neighbor-Joining (NJ)"], horizontal=True)

if st.button(" Build Evolutionary Tree", type="primary", use_container_width=True):
    try:
        # Parse FASTA
        records = []
        current_id = ""
        current_seq = ""
        for line in fasta_input.strip().split('\n'):
            if line.startswith('>'):
                if current_id:
                    records.append(SeqRecord(Seq(current_seq), id=current_id))
                current_id = line[1:].strip()
                current_seq = ""
            else:
                current_seq += line.strip()
        if current_id:
            records.append(SeqRecord(Seq(current_seq), id=current_id))
            
        if len(records) < 3:
            st.error("❌ Need at least 3 sequences to build a tree!")
        else:
            with st.spinner("🧮 Calculating Distance Matrix & Building Tree..."):
                alignment = MultipleSeqAlignment(records)
                
                # Calculate Distance Matrix
                calculator = DistanceCalculator('identity')
                distance_matrix = calculator.get_distance(alignment)
                
                # Build Tree
                constructor = DistanceTreeConstructor(calculator, 'nj' if 'NJ' in method else 'upgma')
                tree = constructor.build_tree(alignment)
                
                # --- PLOT TREE ---
                fig, ax = plt.subplots(figsize=(10, 6))
                Phylo.draw(tree, axes=ax, do_show=False)
                
                # Style the plot for Titan Theme
                ax.set_facecolor('#1a1f2e')
                fig.patch.set_facecolor('#0a0e17')
                ax.title.set_color('#d4af37')
                ax.title.set_text(f"{method} Phylogenetic Tree")
                for label in ax.get_yticklabels():
                    label.set_color('#e0e0e0')
                for spine in ax.spines.values():
                    spine.set_color('#d4af37')
                    
                st.pyplot(fig)
                
                # --- DOWNLOAD BUTTON (SMART LOCK) ---
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(" Download Newick File (Free)", use_container_width=True):
                        Phylo.write(tree, "titan_tree.nwk", "newick")
                        with open("titan_tree.nwk", "r") as f:
                            st.download_button("⬇️ Save .nwk", f.read(), file_name="titan_tree.nwk")
                with c2:
                    if st.button("📊 Export High-Res SVG ( Pro)", use_container_width=True):
                        st.warning("🔒 **Titan Explorer Plan Required.**\nUpgrade to unlock vector graphics export for publications!")

                st.info("💡 **Dr. Titan's Tip:** UPGMA assumes a constant molecular clock (all branches evolve at the same rate). Neighbor-Joining (NJ) does not, making NJ much more accurate for real-world evolutionary data!")
                
    except Exception as e:
        st.error(f"❌ Tree Building Error: {e}")