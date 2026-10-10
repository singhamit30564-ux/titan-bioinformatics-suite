"""Consensus Sequence Generator — column-wise majority over a real alignment.

Sequences of unequal length are aligned with the validated Titan progressive
engine first (previously they were right-padded, which fabricates consensus
positions). Columns whose top letter is under the threshold become 'N'.
"""
from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from titan_utils.msa import MSAError, progressive_msa
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title("🧬", "Consensus Sequence Generator", "Majority-rule consensus over a true alignment.")
st.markdown("Derive the majority base at every alignment column, with per-position confidence.")
st.markdown("---")

fasta_input = st.text_area(
    "Enter Sequences (FASTA — aligned or unaligned)",
    """>Seq1
ATGCGTACGAAGCTAGCC
>Seq2
ATGCGTACGAAGCTAG
>Seq3
ATGCGTGCCTAGCTAG
>Seq4
ATGCAACGTAGCTAG
""",
    height=220,
)
threshold = st.slider("Consensus Threshold (%)", 50, 100, 50,
                      help="Minimum frequency of the top letter for it to be called.")

if st.button("🔬 Generate Consensus", type="primary", use_container_width=True):
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
    raw = [(n, "".join(ch for ch in s.upper() if ch.isalpha() or ch == "-")) for n, s in records]
    raw = [(n, s) for n, s in raw if s]
    if len(raw) < 2:
        st.error("❌ Need at least 2 sequences in FASTA format.")
        st.stop()

    # keep gapped rows only when ALL rows are gapped and equal length → pre-aligned input
    gapped = all(("-" in s) for _, s in raw)
    equal = len({len(s) for _, s in raw}) == 1
    if gapped and equal:
        rows = [s for _, s in raw]
        pre = True
    else:
        try:
            stripped = [(n, "".join(ch for ch in s if ch != "-")) for n, s in raw]
            if len({s for _, s in stripped}) == 1:
                raise MSAError("All sequences are identical — nothing to align.")
            res = progressive_msa([n for n, _ in stripped], [s for _, s in stripped])
            rows = [s for _, s in res["aligned"]]
            pre = False
        except MSAError as ex:
            st.error(f"❌ {ex}")
            st.stop()

    width = len(rows[0])
    consensus, confidence, table = [], [], []
    for pos in range(width):
        letters = [r[pos] for r in rows]
        cnt = Counter(letters)
        top, tn = cnt.most_common(1)[0]
        pct = 100.0 * tn / len(rows)
        keep = top != "-" and pct >= threshold
        consensus.append(top if keep else "N")
        confidence.append(pct if keep else 0.0)
        table.append({"Position": pos + 1, "Consensus": top if keep else "N",
                      "Frequency_%": round(pct, 1), "Counts": dict(sorted(cnt.items()))})

    cons_str = "".join(consensus)
    st.markdown("### 🧬 Consensus Sequence")
    st.code(f">consensus\n{cons_str}", language="text")
    st.download_button("⬇️ Download consensus FASTA", data=f">consensus\n{cons_str}\n".encode(),
                       file_name="titan_consensus.fasta", mime="text/plain", key="cons_dl")

    fig = go.Figure(go.Bar(x=[t["Position"] for t in table], y=[t["Frequency_%"] for t in table],
                           marker_color="#00d4aa", name="Top-letter frequency %"))
    fig.add_hline(y=threshold, line_dash="dot", line_color="#d4af37",
                  annotation_text=f"threshold {threshold}%")
    fig.update_layout(title="Per-position top-letter frequency", xaxis_title="Alignment position",
                      yaxis_title="%", yaxis=dict(range=[0, 105]), template="plotly_dark",
                      paper_bgcolor="#0a0e17", plot_bgcolor="#1a1f2e", height=320)
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download position table CSV", data=df_to_csv_bytes(pd.DataFrame(
        [{k: v for k, v in r.items() if k != "Counts"} for r in table])),
        file_name="titan_consensus_positions.csv", mime="text/csv", key="cons_csv")
    n_amb = cons_str.count("N")
    st.caption(f"{'Pre-aligned input read column-wise.' if pre else 'Aligned with the Titan progressive engine first.'} "
               f"Length {width}; ambiguous (N) columns: {n_amb}.")
    dr_titan_tip("Consensus with N-masking is how degenerate primer pools and motif PWMs are built — "
                 "columns under the threshold carry no reliable signal.")
    smart_lock()
