"""Multiple Sequence Alignment — Titan progressive profile aligner.

This page previously "aligned" sequences by right-padding them with gaps,
which is not an alignment. It now delegates to :func:`titan_utils.msa.progressive_msa`
(affine-gap profile alignment, BLOSUM62 for proteins, UPGMA guide tree) — the
same validated engine behind Hub tool 38. It is a teaching-grade aligner, not
Clustal Omega, and says so.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from titan_utils.msa import MSAError, progressive_msa
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title("🧬", "Multiple Sequence Alignment", "Progressive profile alignment (Titan engine).")
st.markdown(
    "Align several DNA/RNA or protein sequences and inspect per-column conservation. "
    "Powered by the in-house progressive aligner (guide tree: UPGMA; affine gap costs)."
)
st.markdown("---")

fasta_input = st.text_area(
    "Enter Sequences (FASTA)",
    """>Seq1
ATGCGTACGAAGCTAGCC
>Seq2
ATGCGTACGAAGCTAG
>Seq3
ATGCGTGCCTAGCTAG
>Seq4
ATGCAACGTAGCTAG
""",
    height=250,
)
cA, cB = st.columns([3, 1])
with cB:
    gap_open = st.slider("Gap open cost", 4.0, 20.0, 10.0, 0.5)
with cA:
    st.caption("Gap extension is fixed at 0.5 and profile gap at 1.5 (standard defaults).")

if st.button("🔬 Perform MSA", type="primary", use_container_width=True):
    records = []
    name, buf = None, []
    for line in (fasta_input or "").strip().splitlines():
        if line.startswith(">"):
            if name is not None:
                records.append((name, "".join(buf)))
            name, buf = line[1:].strip() or f"seq{len(records) + 1}", []
        elif name is not None:
            buf.append(line.strip())
    if name is not None:
        records.append((name, "".join(buf)))
    # strip any gap-like placeholders from raw input; the aligner inserts its own
    records = [(n, "".join(ch for ch in s.upper() if ch.isalpha())) for n, s in records]
    records = [(n, s) for n, s in records if s]

    if len(records) < 2:
        st.error("❌ Need at least 2 non-empty sequences in FASTA format.")
    elif len({s for _, s in records}) == 1:
        st.error("❌ All input sequences are identical — nothing to align.")
    else:
        try:
            res = progressive_msa([n for n, _ in records], [s for _, s in records],
                                  gap_open=gap_open)
        except MSAError as ex:
            st.error(f"❌ {ex}")
            st.stop()

        aligned = res["aligned"]
        width = res["width"]
        rows_s = [s for _, s in aligned]

        st.markdown("### 📋 Aligned Sequences")
        for name_a, seq_a in aligned:
            st.code(f">{name_a}\n{seq_a}", language="text")

        st.markdown("### 📈 Conservation Analysis")
        conservation = []
        for i in range(width):
            letters = [s[i] for s in rows_s]
            top = max(set(letters), key=letters.count)
            conservation.append(100.0 * letters.count(top) / len(letters))
        fig = go.Figure(go.Scatter(x=list(range(1, width + 1)), y=conservation, mode="lines+markers",
                                   line=dict(color="#d4af37", width=3), name="Conservation %"))
        fig.update_layout(title="Column Conservation (top-letter frequency)",
                          xaxis_title="Alignment position", yaxis_title="Conservation (%)",
                          yaxis=dict(range=[0, 105]), template="plotly_dark",
                          paper_bgcolor="#0a0e17", plot_bgcolor="#1a1f2e", height=340)
        st.plotly_chart(fig, use_container_width=True)

        df = pd.DataFrame([{"Sequence": n, "Aligned": s, "Gaps": s.count("-")} for n, s in aligned])
        st.dataframe(df, use_container_width=True, hide_index=True)
        fasta_bytes = ("\n".join(f">{n}\n{s}" for n, s in aligned) + "\n").encode()
        st.download_button("⬇️ Download aligned FASTA", data=fasta_bytes,
                           file_name="titan_msa.fasta", mime="text/plain", key="msa_fasta")

        m1, m2, m3 = st.columns(3)
        m1.metric("Sequences", str(len(aligned)))
        m2.metric("Alignment width", f"{width} cols")
        m3.metric("Mean pairwise identity", f"{100.0 * res['identity']:.1f}%")
        if res.get("newick"):
            st.caption(f"Guide tree (Newick): `{res['newick']}`")
        st.info("⚠️ Titan's progressive aligner — a correct, reproducible teaching implementation. "
                "For publication-grade MSA use Clustal Omega / MUSCLE / MAFFT externally.")
        dr_titan_tip("Highly conserved columns (near 100%) mark functionally or structurally important sites; "
                     "insertions cluster in loop/hypervariable regions.")
        smart_lock()
