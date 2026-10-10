"""🎮 Sequence Playground — an interactive DNA / RNA / protein sandbox.

Everything here recomputes on every keystroke and slider move using the same
validated engines the Hub uses (titan_utils.compute / thermo / msa + Biopython).
No mock numbers: if a computation is a simplification (Nussinov folding, helix
backbone), the widget says so.
"""
from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from titan_utils import thermo
from titan_utils.compute import ComputeError, prepare_dna, prepare_protein
from titan_utils.sequence import CODON_TABLE_STANDARD, revcomp
from titan_utils.ui import titan_title

st.set_page_config(page_title="Titan Sequence Playground", page_icon="🎮", layout="wide")

titan_title("🎮", "Sequence Playground", "Edit molecules interactively — live metrics, mutations, folding, maps, 3D.")
st.caption("All values recompute instantly from your sequence. Engines: Biopython NN thermodynamics, "
           "Titan MSA/translation, validated GC/ORF modules.")

# ────────────────────────────── state & mode ──────────────────────────────

DEFAULTS = {
    "DNA": "ATGAGTGCCAAAGGGCCCTTTGGGAAACGCTTAGGCGATATGGCACGAACGTGACCGGATCGATCGAATTCGGGCCCATAG",
    "RNA": "AUGAGUGCCAAAGGGCCCUUUGGGAAACGCUUAGGCGAUAUGGCACGAACGUGACCGGAUCGAUCGAAUCGGGCCCAUAG",
    "Protein": "MSAKGPFGNRLGRYGTERTGSIREDISGPIRSRKPA",
}
if "pg_seq" not in st.session_state:
    st.session_state.pg_seq = DEFAULTS["DNA"]
if "pg_mode" not in st.session_state:
    st.session_state.pg_mode = "DNA"
if "pg_mode_prev" not in st.session_state:
    st.session_state.pg_mode_prev = st.session_state.pg_mode

def _mode_swap() -> None:
    """Carry the sample sequence across mode switches (only if untouched)."""
    new = st.session_state.pg_mode
    old = st.session_state.get("pg_mode_prev")
    if old and new != old and st.session_state.pg_seq == DEFAULTS[old]:
        st.session_state.pg_seq = DEFAULTS[new]
    st.session_state.pg_mode_prev = new


top1, top2, top3 = st.columns([1.4, 4.2, 1.4])
with top1:
    mode = st.selectbox("Molecule", ["DNA", "RNA", "Protein"], key="pg_mode", on_change=_mode_swap)
with top2:
    seq = st.text_area("Sequence (5'→3')", key="pg_seq", height=110).strip().upper()
with top3:
    st.write("")
    st.write("")
    def _reset_sample() -> None:
        st.session_state.pg_seq = DEFAULTS[st.session_state.pg_mode]

    st.button("↺ Reset to sample", use_container_width=True, on_click=_reset_sample)

seq_clean = "".join(seq.split())
is_na = mode in ("DNA", "RNA")

# ────────────────────────────── clean parse ──────────────────────────────

dna = ""
prot = ""
parse_err = ""
try:
    if is_na:
        dna = prepare_dna(seq_clean).replace("U", "T")
    else:
        prot = prepare_protein(seq_clean)
except ComputeError as ex:
    parse_err = str(ex)

if parse_err:
    st.error(f"⚠️ {parse_err}")
elif not (dna or prot):
    st.info("Type a sequence above to start playing.")
    st.stop()


# ────────────────────────────── live metrics ──────────────────────────────

m1, m2, m3, m4, m5 = st.columns(5)
if is_na:
    gc = 100.0 * (dna.count("G") + dna.count("C")) / max(1, len(dna))
    counts = Counter(dna)
    try:
        tm_short = len(dna) < 14
        tm = thermo.wallace_tm(dna)[0] if tm_short else thermo.nn_tm(dna)
    except thermo.ThermoError:
        tm = float("nan")
    m1.metric("Length", f"{len(dna)} nt")
    m2.metric("GC content", f"{gc:.1f}%")
    m3.metric("Tm (duplex, 50 mM Na⁺)", f"{tm:.1f} °C", "Wallace (<14 nt)" if tm_short else "nearest-neighbor")
    m4.metric("A/T · G/C", f"{counts['A'] + counts['T']} · {counts['G'] + counts['C']}")
    m5.metric("Reverse complement", f"{len(revcomp(dna))} nt", help=revcomp(dna)[:30] + "…")
else:
    from Bio.SeqUtils.ProtParam import ProteinAnalysis
    pa = ProteinAnalysis(prot.replace("X", "A") if "X" in prot else prot)
    gravy = pa.gravy()
    m1.metric("Length", f"{len(prot)} aa")
    m2.metric("Molecular weight", f"{pa.molecular_weight() / 1000:.2f} kDa")
    m3.metric("pI", f"{pa.isoelectric_point():.2f}")
    m4.metric("GRAVY (hydropathy)", f"{gravy:+.3f}")
    m5.metric("Stops inside", f"{prot.count('*')}")

st.markdown("---")

tab_live, tab_mut, tab_code, tab_fold, tab_build = st.tabs(
    ["📈 Property tracks", "✂️ Mutation studio", "🧬 Code & cut map", "🌡 Fold & melt", "🧱 Construct builder"]
)

# ────────────────────────────── tracks ──────────────────────────────

with tab_live:
    if is_na:
        win = st.slider("Sliding window (nt)", 10, min(500, max(10, len(dna))), min(120, max(10, len(dna) // 2 or 10)), key="pg_win")
        starts, gcs = [], []
        for i in range(0, max(1, len(dna) - win + 1)):
            w = dna[i:i + win]
            starts.append(i + 1)
            gcs.append(100.0 * (w.count("G") + w.count("C")) / len(w))
        skew = [(w.count("G") - w.count("C")) / max(1, w.count("G") + w.count("C"))
                for w in (dna[i:i + win] for i in range(0, max(1, len(dna) - win + 1)))]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=starts, y=gcs, name="GC %", line=dict(color="#00d4aa")))
        fig.add_trace(go.Scatter(x=starts, y=skew, name="GC skew (−1..1)", line=dict(color="#d4af37"), yaxis="y2"))
        fig.update_layout(template="plotly_dark", height=340, margin=dict(l=40, r=40, t=30, b=40),
                          plot_bgcolor="#0d1117", paper_bgcolor="#161b22", font_color="#e6edf3",
                          yaxis=dict(title="GC %"), yaxis2=dict(title="skew", overlaying="y", side="right", showgrid=False))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Window {win} nt. Computed on your sequence — N-substituted positions (RNA-only letters) count as non-GC.")
    else:
        win = st.slider("Hydropathy window (aa)", 3, 31, 9, step=2, key="pg_win_p")
        KD = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5, "G": -0.4,
              "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6, "S": -0.8,
              "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2, "X": 0.0, "*": 0.0}
        h = [KD.get(c, 0.0) for c in prot]
        centers, smoothed = [], []
        half = win // 2
        for i in range(len(h)):
            lo, hi = max(0, i - half), min(len(h), i + half + 1)
            centers.append(i + 1)
            smoothed.append(sum(h[lo:hi]) / (hi - lo))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=centers, y=smoothed, mode="lines", name=f"Kyte–Doolittle (w={win})",
                                 line=dict(color="#00d4aa")))
        fig.add_hline(y=0, line=dict(color="#4a90e2", dash="dot"))
        fig.update_layout(template="plotly_dark", height=340, margin=dict(l=40, r=40, t=30, b=40),
                          plot_bgcolor="#0d1117", paper_bgcolor="#161b22", font_color="#e6edf3",
                          xaxis_title="Residue", yaxis_title="Mean hydropathy")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Kyte–Doolittle scale; peaks above 0 are hydrophobic (transmembrane-like stretches).")

# ────────────────────────────── mutation studio ──────────────────────────────

with tab_mut:
    if not is_na:
        st.info("Mutation studio operates on DNA. Switch the Molecule selector to DNA to mutate codons and watch the protein change.")
    else:
        colA, colB = st.columns([2, 1])
        with colA:
            pos = st.number_input("Position (1-based)", 1, len(dna), min(1, len(dna) // 2), key="pg_mpos")
        with colB:
            newbase = st.selectbox("Substitute with", list("ATCG"), index=1, key="pg_mbase")
        mutated = dna[: pos - 1] + newbase + dna[pos:]
        changed = dna[pos - 1] != newbase

        # real diff metrics
        gc0 = 100.0 * (dna.count("G") + dna.count("C")) / len(dna)
        gc1 = 100.0 * (mutated.count("G") + mutated.count("C")) / len(mutated)
        try:
            tm0 = thermo.nn_tm(dna) if len(dna) >= 14 else thermo.wallace_tm(dna)[0]
            tm1 = thermo.nn_tm(mutated) if len(mutated) >= 14 else thermo.wallace_tm(mutated)[0]
        except thermo.ThermoError:
            tm0 = tm1 = float("nan")

        # codon-level consequence (frame of position: assume ORF starts at position 1, frame chosen by user)
        frame = st.radio("Reading frame start", [1, 2, 3], horizontal=True, key="pg_frame")
        def _translate(s: str):
            codons = [s[i:i + 3] for i in range(frame - 1, len(s) - 2, 3)]
            return "".join(CODON_TABLE_STANDARD.get(c, "?") for c in codons if len(c) == 3)
        p0 = _translate(dna)
        p1 = _translate(mutated)
        codon_idx = (pos - frame) // 3
        cons = "—"
        if changed and 0 <= codon_idx < min(len(p0), len(p1)):
            a0, a1 = p0[codon_idx], p1[codon_idx]
            if a0 == a1:
                cons = "synonymous (same aa)"
            elif a1 == "*":
                cons = "nonsense (stop gained)"
            elif a0 == "*":
                cons = "stop lost"
            else:
                cons = f"missense {a0}→{a1}"
        elif not changed:
            cons = "no change (same base)"

        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Δ GC", f"{gc1 - gc0:+.2f} pts", help=f"{gc0:.2f}% → {gc1:.2f}%")
        d2.metric("Δ Tm", f"{tm1 - tm0:+.2f} °C", help=f"{tm0:.2f} → {tm1:.2f} °C")
        d3.metric("Codon effect (this frame)", cons)
        n_aa_diff = sum(1 for x, y in zip(p0, p1) if x != y)
        d4.metric("Protein diffs", f"{n_aa_diff} aa", help=f"{min(len(p0), len(p1))} codons compared")

        st.markdown("**Alignment preview** (mutation marked)")
        rowq = list(dna)
        rowq[pos - 1] = newbase
        mark = ["|" if a == b else "^" for a, b in zip(dna, "".join(rowq))]
        W = 60
        for s0 in range(0, len(dna), W):
            st.code(f"DNA    {dna[s0:s0+W]}\nMUT    {''.join(rowq)[s0:s0+W]}\n       {''.join(mark)[s0:s0+W]}",
                    language="text")
        def _apply_mut() -> None:
            raw = "".join(st.session_state.pg_seq.strip().upper().split())
            try:
                cur = prepare_dna(raw).replace("U", "T")
            except ComputeError:
                return
            pos_ = int(st.session_state.pg_mpos)
            base_ = st.session_state.pg_mbase
            if not (1 <= pos_ <= len(cur)) or cur[pos_ - 1] == base_:
                return
            mut = cur[: pos_ - 1] + base_ + cur[pos_:]
            st.session_state.pg_seq = mut if st.session_state.pg_mode == "DNA" else mut.replace("T", "U")

        st.button("✂️ Apply mutation", type="primary", disabled=not changed, on_click=_apply_mut)

# ────────────────────────────── code & cut map ──────────────────────────────

with tab_code:
    cT1, cT2 = st.columns([1, 1])
    with cT1:
        st.markdown("**Six-frame translation** (real Biopython-free table lookup, stops as `*`)")
        frames = []
        for strand, s in (("+", dna), ("−", revcomp(dna))):
            for f in range(3):
                codons = [s[i:i + 3] for i in range(f, len(s) - 2, 3)]
                pep = "".join(CODON_TABLE_STANDARD.get(c, "?") for c in codons if len(c) == 3)
                frames.append({"Strand_frame": f"{strand}{f + 1}", "Len_aa": len(pep),
                               "Stops": pep.count("*"), "Longest_no_stop": max((len(x) for x in pep.split("*")), default=0),
                               "Peptide": pep[:120] + ("…" if len(pep) > 120 else "")})
        st.dataframe(pd.DataFrame(frames), use_container_width=True, hide_index=True)
        fasta_mode = mode == "DNA" or mode == "RNA"
        if fasta_mode:
            longest = max(frames, key=lambda d: d["Longest_no_stop"])
            st.caption(f"Longest open stretch: {longest['Strand_frame']} with {longest['Longest_no_stop']} aa before a stop.")
    with cT2:
        st.markdown("**Restriction map** (Biopython sites on your sequence)")
        enz_input = st.text_input("Enzymes", "EcoRI, BamHI, HindIII, PstI", key="pg_enz")
        try:
            from Bio.Restriction import Restriction
            from Bio.Seq import Seq
            enzymes = []
            for name in [x.strip() for x in enz_input.split(",") if x.strip()]:
                enz = getattr(Restriction, name, None)
                if enz is None:
                    st.warning(f"Unknown enzyme '{name}' skipped (try EcoRI, BamHI, HindIII, PstI, NotI, SmaI).")
                else:
                    enzymes.append(enz)
            cuts = []
            for enz in enzymes:
                for c in enz.search(Seq(dna)):
                    cuts.append({"Enzyme": str(enz), "Pos": int(c)})
            if cuts:
                figm = go.Figure()
                figm.add_trace(go.Scatter(x=[0, len(dna)], y=[0, 0], mode="lines", line=dict(color="#4a90e2", width=4), name="sequence"))
                for i, enz in enumerate(enzymes):
                    xs = [c["Pos"] for c in cuts if c["Enzyme"] == str(enz)]
                    if xs:
                        figm.add_trace(go.Scatter(x=xs, y=[0.05 + 0.05 * i] * len(xs), mode="markers",
                                                  marker_symbol="line-ns-open", marker=dict(size=26, color="#ff4757"),
                                                  name=f"{enz} ({len(xs)})"))
                figm.update_layout(template="plotly_dark", height=240, margin=dict(l=10, r=10, t=10, b=30),
                                   plot_bgcolor="#0d1117", paper_bgcolor="#161b22", font_color="#e6edf3",
                                   xaxis=dict(title="position (nt)", range=[-2, len(dna) + 2]), yaxis=dict(showticklabels=True, range=[-0.05, 0.5]))
                st.plotly_chart(figm, use_container_width=True)
                st.caption(f"{len(cuts)} cut site(s). Cut position = after the reported base (0 = before first base).")
            else:
                st.info("No sites for those enzymes in this sequence — that's a real answer, not a failure.")
        except Exception as ex:  # noqa: BLE001
            st.error(f"Restriction scan unavailable: {ex}")

# ────────────────────────────── fold & melt ──────────────────────────────

with tab_fold:
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        st.markdown("**Melting curve** (two-state NN thermodynamics)")
        try:
            if len(dna if is_na else prot) > 200 and is_na:
                raise thermo.ThermoError("Keep sequences ≤ 200 nt for the two-state melt model.")
            if not is_na:
                raise thermo.ThermoError("Melting curves apply to duplex nucleic acids — switch to DNA.")
            tm = thermo.nn_tm(dna)
            temps, bounds = thermo.melting_curve(dna, temp_min_c=tm - 15, temp_max_c=tm + 15, points=120)
            ff = go.Figure(go.Scatter(x=temps, y=bounds, mode="lines", line=dict(color="#00d4aa")))
            ff.add_vline(x=tm, line_dash="dot", line_color="#d4af37", annotation_text=f"Tm {tm:.1f}°C")
            ff.update_layout(template="plotly_dark", height=280, margin=dict(l=40, r=10, t=10, b=40),
                             plot_bgcolor="#0d1117", paper_bgcolor="#161b22", font_color="#e6edf3",
                             xaxis_title="°C", yaxis_title="fraction bound")
            st.plotly_chart(ff, use_container_width=True)
        except thermo.ThermoError as ex:
            st.info(str(ex))
    with fcol2:
        st.markdown("**RNA secondary structure** — Nussinov base-pair maximization")
        st.caption("Maximizes base-pair count only (no stacking/loops/energy). Honest schoolbook folding for teaching, ≤180 nt.")
        rnaseq = (seq_clean if mode == "RNA" else dna).replace("T", "U")
        if len(rnaseq) > 180:
            rnaseq = rnaseq[:180]
            st.caption("Truncated to first 180 nt for the O(n³) DP.")
        if mode == "Protein":
            st.info("Folding view applies to RNA/DNA strands.")
        else:
            n = len(rnaseq)
            MINLOOP = 3
            dp = [[0] * n for _ in range(n)]
            for span in range(MINLOOP + 2, n + 1):
                for i in range(n - span + 1):
                    j = i + span - 1
                    best = dp[i][j - 1]
                    pair = (rnaseq[i], rnaseq[j]) in {("A", "U"), ("U", "A"), ("G", "C"), ("C", "G"), ("G", "U"), ("U", "G")}
                    if pair and 1 + dp[i + 1][j - 1] > best:
                        best = 1 + dp[i + 1][j - 1]
                    for k in range(i + 1, j - MINLOOP):
                        v = dp[i][k] + dp[k + 1][j]
                        if v > best:
                            best = v
                    dp[i][j] = best
            # traceback
            pairs = []
            stack = [(0, n - 1)]
            while stack:
                i, j = stack.pop()
                if j - i < MINLOOP + 1:
                    continue
                if dp[i][j] == dp[i][j - 1]:
                    stack.append((i, j - 1))
                    continue
                pair = (rnaseq[i], rnaseq[j]) in {("A", "U"), ("U", "A"), ("G", "C"), ("C", "G"), ("G", "U"), ("U", "G")}
                if pair and dp[i][j] == 1 + dp[i + 1][j - 1]:
                    pairs.append((i, j))
                    stack.append((i + 1, j - 1))
                    continue
                for k in range(i + 1, j - MINLOOP):
                    if dp[i][j] == dp[i][k] + dp[k + 1][j]:
                        stack.extend([(i, k), (k + 1, j)])
                        break
            pairs.sort()
            arcs = []
            for a, b in pairs:
                t_ = np.linspace(0, np.pi, 40)
                cx, cy = (a + b) / 2, 0
                r = (b - a) / 2
                arcs.append(go.Scatter(x=cx + r * np.cos(t_), y=cy + r * np.sin(t_), mode="lines",
                                       line=dict(color="#9b59b6", width=1), hoverinfo="skip", showlegend=False))
            arcfig = go.Figure(arcs + [go.Scatter(x=list(range(n)), y=[0] * n, mode="markers",
                                                   marker=dict(size=5, color="#e6edf3"),
                                                   text=[f"{i + 1}:{rnaseq[i]}" for i in range(n)],
                                                   hoverinfo="text", name="nucleotide")])
            arcfig.update_layout(template="plotly_dark", height=240, margin=dict(l=10, r=10, t=10, b=20),
                                 plot_bgcolor="#0d1117", paper_bgcolor="#161b22", font_color="#e6edf3",
                                 xaxis=dict(title="position", range=[-1, n]), yaxis=dict(range=[-0.6, max(1.0, n * 0.04)]),
                                 showlegend=False)
            st.plotly_chart(arcfig, use_container_width=True)
            opened = {a: b for a, b in pairs}
            closed = {b: a for a, b in pairs}
            db_chars = []
            for i in range(n):
                if i in opened:
                    db_chars.append("(")
                elif i in closed:
                    db_chars.append(")")
                else:
                    db_chars.append(".")
            st.caption(f"**{len(pairs)} base pairs** maximized. Dot-bracket: `{''.join(db_chars)[:160]}`")

    if not is_na:
        st.markdown("**Protein 3D** — schematic backbone (α-helix) built from your sequence")
        try:
            from titan_utils.mol3d import build_helix_pdb, render_mol3d_viewer
            pdb_text = build_helix_pdb("A", min(len(prot), 120))
            render_mol3d_viewer(pdb_text, style="Cartoon", height=360)
            st.caption("Cartoon coordinates generated by titan_utils.mol3d for visualization of length/shape only — "
                       "not a folded structure. For predicted structures use AlphaFold DB.")
        except Exception as ex:  # noqa: BLE001
            st.info(f"3D viewer unavailable here: {ex}")

# ────────────────────────────── construct builder ──────────────────────────────

with tab_build:
    st.markdown("**Plasmid / construct builder** — concatenate parts, inspect the circle")
    st.caption("Each line = one part: `name SEQUENCE` or bare sequence. No promoter biology is simulated — "
               "this is pure sequence assembly with real statistics.")
    parts_txt = st.text_area("Parts", "promoter TATAAAAGGGTTGACATCGATCGATCG\nRBS AGGAGGAAAAA\nmarker ATGAGTGCCAAAGGGCCCTTTGGG\nterminator TTTAAATTTGGGCCCTTTAAATA",
                             height=120, key="pg_parts")
    parts = []
    for line in parts_txt.splitlines():
        line = line.strip()
        if not line:
            continue
        if " " in line:
            nm, sq = line.split(" ", 1)
        else:
            nm, sq = f"part{len(parts) + 1}", line
        sq = "".join(sq.upper().split())
        sq = "".join(c for c in sq if c in "ATCG")
        if sq:
            parts.append((nm, sq))
    if len(parts) < 2:
        st.info("Add at least two parts (one per line) to build a construct.")
    else:
        circular = st.toggle("Circular (plasmid)", value=True, key="pg_circ")
        joined = "".join(s for _, s in parts)
        if circular:
            joined += "GATC" * 2  # minimal seam spacer so junctions aren't artificially fused
            st.caption("4 bp spacer inserted at the junction region for read-through checks.")
        gcj = 100.0 * (joined.count("G") + joined.count("C")) / len(joined)
        rows, off = [], 0
        for nm, sq in parts:
            rows.append({"Part": nm, "Start": off + 1, "End": off + len(sq), "Length": len(sq),
                         "GC_%": round(100.0 * (sq.count("G") + sq.count("C")) / len(sq), 1)})
            off += len(sq)
        dfp = pd.DataFrame(rows)
        ffig = go.Figure()
        colors = ["#00d4aa", "#d4af37", "#ff4757", "#4a90e2", "#9b59b6", "#2ecc71", "#e67e22", "#95a5a6"]
        for i, r in enumerate(rows):
            ffig.add_trace(go.Scatter(x=[r["Start"], r["End"]], y=[0, 0], mode="lines",
                                      line=dict(width=16, color=colors[i % len(colors)]), name=r["Part"]))
        # ORFs on the construct
        for f in range(3):
            codons = [joined[k:k + 3] for k in range(f, len(joined) - 2, 3)]
            pep = "".join(CODON_TABLE_STANDARD.get(c, "?") for c in codons if len(c) == 3)
            run = 0
            for idx, aa in enumerate(pep + "*"):
                if aa not in ("*", "?"):
                    run += 1
                else:
                    if run >= 25:
                        s0 = f + 3 * (idx - run) + 1
                        e0 = f + 3 * idx
                        ffig.add_trace(go.Scatter(x=[max(1, s0), e0], y=[0.12, 0.12], mode="lines",
                                                  line=dict(width=4, color="#e6edf3", dash="dot"),
                                                  name=f"ORF f{f + 1} {run}aa"))
                    run = 0
        ffig.update_layout(template="plotly_dark", height=220, margin=dict(l=10, r=10, t=10, b=40),
                           plot_bgcolor="#0d1117", paper_bgcolor="#161b22", font_color="#e6edf3",
                           xaxis=dict(title=f"construct position ({len(joined)} bp, {gcj:.1f}% GC)",
                                      range=[0, len(joined)]), yaxis=dict(range=[-0.1, 0.3], showticklabels=False))
        st.plotly_chart(ffig, use_container_width=True)
        st.dataframe(dfp, use_container_width=True, hide_index=True)
        total_gc = f"{gcj:.1f}%"
        st.success(f"Construct: **{len(joined)} bp**, GC {total_gc}, {len(parts)} parts. "
                   "Download FASTA below to run it through the Hub tools (e.g. #5 ORF, #7 Restriction).")
        st.download_button("⬇️ Download construct FASTA", data=f">titan_construct_{len(joined)}bp\n{joined}\n".encode(),
                           file_name="titan_construct.fasta", mime="text/plain", key="pg_fasta")
