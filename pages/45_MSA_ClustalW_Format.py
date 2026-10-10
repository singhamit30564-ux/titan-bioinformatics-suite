"""MSA in ClustalW layout — real progressive alignment (Titan engine), honest formatting.

The old version right-padded sequences and printed a fake
"CLUSTAL W (1.82)" header. Now the alignment is produced by
``titan_utils.msa.progressive_msa`` and rendered with ``clustalw_text``
(stars = fully conserved columns; ':'/'.' similarity classes are *not* faked —
Clustal's colour classes would require the full Henikoff scoring, so the
marker line is the conservative '*' style only).
"""
import streamlit as st

from titan_utils.msa import MSAError, clustalw_text, progressive_msa
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title("🧾", "MSA · ClustalW Format", "Clustal-style block rendering of the Titan alignment.")
st.markdown("Aligns with the progressive engine, then prints the alignment in ClustalW block format.")
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
line_len = st.slider("Block width", 20, 80, 60, 10)

if st.button("🧾 Render ClustalW", type="primary", use_container_width=True):
    records, name, buf = [], None, []
    for line in (fasta_input or "").strip().splitlines():
        if line.startswith(">"):
            if name is not None:
                records.append((name, "".join(buf)))
            name, buf = line[1:].strip() or f"seq{len(records) + 1}", []
        elif name is not None:
            buf.append(line.strip())
    if name is not None:
        records.append((name, "".join(buf)))
    records = [(n, "".join(ch for ch in s.upper() if ch.isalpha())) for n, s in records]
    records = [(n, s) for n, s in records if s]

    if len(records) < 2:
        st.error("❌ Need at least 2 sequences in FASTA format.")
    elif len({s for _, s in records}) == 1:
        st.error("❌ All sequences are identical — nothing to align.")
    else:
        try:
            res = progressive_msa([n for n, _ in records], [s for _, s in records])
            txt = clustalw_text(res["aligned"], int(line_len))
        except MSAError as ex:
            st.error(f"❌ {ex}")
            st.stop()
        st.code(txt, language="text")
        st.download_button("⬇️ Download .aln (Clustal format)", data=txt.encode(),
                           file_name="titan_msa.aln", mime="text/plain", key="aln_dl")
        st.caption(f"Aligned by titan_utils.msa (progressive, UPGMA guide); width {res['width']}, "
                   "mean pairwise identity "
                   f"{100.0 * res['identity']:.1f}%. This is ClustalW-style *formatting*, not the ClustalW program.")
        dr_titan_tip("In Clustal files '*' marks columns identical in every sequence — the signature of "
                     "strong functional constraint.")
        smart_lock()
