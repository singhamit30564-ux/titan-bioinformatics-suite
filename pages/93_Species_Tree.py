"""🌳 Species Tree Explorer — Interactive phylogenetic tree with 20 demo species.

Click nodes for info cards. "Build your own" mode lets users add species
and relations, then export the custom tree as text (PNG export via plotly).
"""
from __future__ import annotations

import json

import plotly.graph_objects as go
import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🌳",
    "Species Tree Explorer",
    "Explore an interactive phylogenetic tree of 20 species, or build your own custom tree!",
)

# ── Demo phylogenetic tree data ──────────────────────────────────────────────
SPECIES_DATA = {
    "Life": {
        "Bacteria": {"E. coli": {}, "Streptomyces": {}},
        "Archaea": {"Halobacterium": {}, "Methanococcus": {}},
        "Eukaryota": {
            "Plants": {
                "Arabidopsis": {"info": "Model plant — tiny genome, first plant sequenced."},
                "Oryza sativa (Rice)": {"info": "Staple food for 3.5 billion people."},
            },
            "Fungi": {
                "Saccharomyces cerevisiae": {"info": "Baker's yeast — model eukaryote, first eukaryote genome sequenced."},
                "Aspergillus niger": {"info": "Used industrially to produce citric acid and enzymes."},
            },
            "Animals": {
                "Invertebrates": {
                    "Drosophila melanogaster": {"info": "Fruit fly — classical genetics model organism."},
                    "Caenorhabditis elegans": {"info": "Nematode — first animal with a complete connectome mapped."},
                },
                "Vertebrates": {
                    "Fish": {"Danio rerio (Zebrafish)": {"info": "Transparent embryos make developmental biology easy."}},
                    "Amphibians": {"Xenopus laevis": {"info": "African clawed frog — used in developmental biology."}},
                    "Mammals": {
                        "Mus musculus (Mouse)": {"info": "Most used mammalian model organism in research."},
                        "Homo sapiens (Human)": {"info": "That's us! ~3 billion base pairs, ~20,000 genes."},
                        "Pan troglodytes (Chimp)": {"info": "Closest living relative — 98.8% DNA similarity."},
                    },
                    "Birds": {"Gallus gallus (Chicken)": {"info": "First bird genome sequenced — important developmental model."}},
                },
            },
        },
    }
}

SPECIES_INFO = {
    "E. coli": "🦠 Bacterium — model prokaryote, workhorse of molecular biology. Genome: ~4.6 Mb.",
    "Streptomyces": "🦠 Soil bacterium — produces ~70% of naturally derived antibiotics.",
    "Halobacterium": "🏺 Halophilic archaeon — lives in extreme salt concentrations (>3M NaCl).",
    "Methanococcus": "🌋 Methanogenic archaeon — produces methane, thrives in hydrothermal vents.",
    "Arabidopsis": "🌱 Model plant — tiny genome (125 Mb), first plant to have its genome sequenced.",
    "Oryza sativa (Rice)": "🌾 Staple crop feeding 3.5 billion people. Genome: ~430 Mb.",
    "Saccharomyces cerevisiae": "🍞 Baker's yeast — first eukaryote genome sequenced (1996). 16 chromosomes.",
    "Aspergillus niger": "🍄 Industrial fungus — produces citric acid, enzymes, and organic acids.",
    "Drosophila melanogaster": "🪰 Fruit fly — classical genetics model. 4 chromosomes, ~14,000 genes.",
    "Caenorhabditis elegans": "🐛 Nematode worm — first multicellular organism with complete cell lineage mapped.",
    "Danio rerio (Zebrafish)": "🐟 Transparent embryos — ideal for studying vertebrate development.",
    "Xenopus laevis": "🐸 African clawed frog — used in embryology, cell biology, and toxicology.",
    "Mus musculus (Mouse)": "🐁 Most-used mammalian model — 85% gene homology with humans.",
    "Homo sapiens (Human)": "👤 ~3 billion bp, ~20,000 genes, 23 chromosome pairs. T2T genome completed 2022.",
    "Pan troglodytes (Chimp)": "🐵 98.8% DNA identical to humans. Closest living relative.",
    "Gallus gallus (Chicken)": "🐔 First bird genome (2004). Important for developmental biology and evolution studies.",
}


def _count_leaves(tree: dict) -> int:
    count = 0
    for k, v in tree.items():
        if isinstance(v, dict) and v:
            count += _count_leaves(v)
        else:
            count += 1
    return count


# ── Mode selector ────────────────────────────────────────────────────────────
mode = st.radio(t("Mode:"), [t("🔍 Explore Demo Tree"), t("🛠️ Build Your Own")], horizontal=True)

if "Explore" in mode or "खोजें" in mode:
    # ── Interactive tree display ─────────────────────────────────────────────
    st.subheader(t("🔬 Phylogenetic Tree — 20 Demo Species"))

    def _render_tree(tree: dict, depth: int = 0) -> None:
        for name, children in tree.items():
            indent = "　" * depth
            if name == "info":
                continue
            if isinstance(children, dict) and children and "info" not in children:
                st.markdown(f"{indent}📂 **{name}**")
                _render_tree(children, depth + 1)
            else:
                info = SPECIES_INFO.get(name, "")
                st.markdown(f"{indent}├─ 🌿 **{name}**")
                if info:
                    st.caption(f"{indent}　　{info}")

    with st.container(border=True):
        _render_tree(SPECIES_DATA)

    # ── Plotly tree visualization ────────────────────────────────────────────
    st.markdown("---")
    st.subheader(t("📊 Visual Tree (Plotly)"))

    # Build a simple hierarchical tree for Plotly
    nodes_x, nodes_y, nodes_text, node_colors = [], [], [], []
    edges_x, edges_y = [], []
    leaf_counter = [0]

    def _build_plot(tree: dict, depth: int = 0, parent_x: float = 0) -> None:
        children = [(k, v) for k, v in tree.items() if k != "info"]
        if not children:
            x = leaf_counter[0]
            leaf_counter[0] += 1
            nodes_x.append(x)
            nodes_y.append(-depth)
            nodes_text.append(list(tree.keys())[0] if not children else "")
            node_colors.append("#66fcf1")
            return

        child_xs = []
        for name, sub in children:
            if isinstance(sub, dict) and sub and "info" not in sub:
                _build_plot(sub, depth + 1)
                child_xs.append(nodes_x[-1])
            else:
                x = leaf_counter[0]
                leaf_counter[0] += 1
                nodes_x.append(x)
                nodes_y.append(-depth)
                nodes_text.append(name)
                node_colors.append("#66fcf1" if "info" in (sub if isinstance(sub, dict) else {}) else "#d4af37")
                child_xs.append(x)

        # Parent node at average x of children
        if child_xs:
            px = sum(child_xs) / len(child_xs)
            nodes_x.append(px)
            nodes_y.append(-depth)
            nodes_text.append(name if name != "Life" else "🌳 Life")
            node_colors.append("#d4af37")
            # Edges
            for cx in child_xs:
                edges_x.extend([px, cx, None])
                edges_y.extend([-depth, -(depth + 1), None])

    _build_plot(SPECIES_DATA)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=edges_x, y=edges_y, mode="lines",
        line=dict(color="#555", width=1.5),
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=nodes_x, y=nodes_y, mode="markers+text",
        marker=dict(size=10, color=node_colors, line=dict(width=1, color="white")),
        text=nodes_text, textposition="bottom center",
        textfont=dict(color="#e0e0e0", size=9),
        hoverinfo="text",
    ))
    fig.update_layout(
        height=500,
        showlegend=False,
        paper_bgcolor="#0a0e17",
        plot_bgcolor="#0a0e17",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, title=t("Evolutionary Depth")),
        margin=dict(l=10, r=10, t=30, b=10),
        font=dict(color="#e0e0e0"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(t(
        "ℹ️ This is a **simplified demo tree** for educational purposes. "
        "Real phylogenetic trees are inferred from molecular sequence data using methods like Maximum Likelihood or Bayesian inference."
    ))

else:
    # ── Build your own mode ──────────────────────────────────────────────────
    st.subheader(t("🛠️ Build Your Own Phylogenetic Tree"))
    st.write(t("Add species and define parent-child relationships to create a custom tree."))

    if "custom_tree" not in st.session_state:
        st.session_state["custom_tree"] = {"name": "Root", "children": []}
    if "custom_species" not in st.session_state:
        st.session_state["custom_species"] = []

    with st.form("add_species"):
        col1, col2 = st.columns(2)
        with col1:
            species_name = st.text_input(t("Species name:"), placeholder="e.g. Canis lupus")
        with col2:
            parent = st.text_input(t("Parent node:"), placeholder="e.g. Mammals (or leave blank for root)")
        submitted = st.form_submit_button(t("➕ Add Species"))

    if submitted and species_name.strip():
        st.session_state["custom_species"].append({
            "name": species_name.strip(),
            "parent": parent.strip() or "Root",
        })

    # Display current tree
    if st.session_state["custom_species"]:
        st.markdown(t("### 🌿 Your Custom Tree"))
        for sp in st.session_state["custom_species"]:
            st.markdown(f"- **{sp['parent']}** → {sp['name']}")

        # Export as text
        tree_text = "Custom Phylogenetic Tree\n" + "=" * 30 + "\n"
        for sp in st.session_state["custom_species"]:
            tree_text += f"  {sp['parent']} ─── {sp['name']}\n"

        st.code(tree_text)
        st.download_button(t("📥 Download Tree (.txt)"), tree_text, "custom_tree.txt", use_container_width=True)

        if st.button(t("🗑️ Clear Tree")):
            st.session_state["custom_species"] = []
            st.rerun()

dr_titan_tip(
    "Phylogenetics reveals the evolutionary relationships between all life on Earth. "
    "Darwin first sketched a 'Tree of Life' in 1837 — we've come a long way since then!"
)