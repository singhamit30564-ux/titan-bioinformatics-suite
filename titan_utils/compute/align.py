"""Sequence alignment, MSA, trees, logos — ids 34-44 (Biopython-backed).

Design notes
------------
* Pairwise modes map to ``Bio.Align.PairwiseAligner``:
    global   -> Needleman-Wunsch (mode="global")
    local    -> Smith-Waterman   (mode="local")
    overlap  -> global with free terminal gaps (end_gap_score = 0) and the
                result trimmed to the overlap region.
* Scoring: DNA +2/-1 (open -5, extend -0.5); protein BLOSUM62 (open -11,
  extend -1) selected by alphabet auto-detection.
* MSA (38-40, 44) delegates to :mod:`titan_utils.msa` (progressive
  profile alignment) — clearly labelled as Titan's own aligner, *not*
  Clustal Omega; UPGMA/NJ trees are built on p-distances of that alignment.
* Every metric comes from the actual aligned strings — identity is computed
  on aligned columns, never fabricated.
"""
from __future__ import annotations

import math
from collections import Counter
from io import StringIO
from typing import Any, Dict, List, Tuple

from . import ComputeError, free_end_gaps, guard_len, out, prepare_dna
from ..msa import MSAError, consensus as _cons, clustalw_text, progressive_msa

_MATCH, _MISMATCH, _OPEN, _EXTEND = 2.0, -1.0, -5.0, -0.5
_P_MATCH, _P_MISMATCH, _P_OPEN, _P_EXTEND = None, None, -11.0, -1.0
_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


def _is_protein_like(s: str) -> bool:
    core = s.replace("*", "")
    return bool(core) and all(ch in _AMINO_ACIDS for ch in core)


def _make_aligner(protein: bool):
    from Bio import Align
    al = Align.PairwiseAligner()
    if protein:
        al.substitution_matrix = Align.substitution_matrices.load("BLOSUM62")
        al.open_gap_score, al.extend_gap_score = _P_OPEN, _P_EXTEND
    else:
        al.match_score, al.mismatch_score = _MATCH, _MISMATCH
        al.open_gap_score, al.extend_gap_score = _OPEN, _EXTEND
    return al


def _sanitize(s: str) -> str:
    return "".join(ch for ch in (s or "").upper().split() if ch not in "-.")


def _pairwise(seq1: str, seq2: str, mode: str) -> Dict[str, Any]:
    a, b = _sanitize(seq1), _sanitize(seq2)
    guard_len(a, 20_000, "sequence 1")
    guard_len(b, 20_000, "sequence 2")
    if len(a) < 2 or len(b) < 2:
        raise ComputeError("Both sequences need at least 2 characters.")
    if not _is_protein_like(a) or not _is_protein_like(b):
        a = prepare_dna(a)
        b = prepare_dna(b)
        protein = False
    else:
        protein = True
    mlow = (mode or "global").lower()
    al = _make_aligner(protein)
    al.mode = "local" if mlow.startswith("local") else "global"
    if mlow.startswith("overlap"):
        free_end_gaps(al)
    try:
        best = al.align(a, b)[0]
    except Exception as e:  # noqa: BLE001
        raise ComputeError(f"Alignment failed: {e}") from e
    row_a, row_b = str(best[0]), str(best[1])
    a_off = b_off = 0
    if mlow.startswith("overlap"):
        both = [i for i, (x, y) in enumerate(zip(row_a, row_b)) if x != "-" and y != "-"]
        if not both:
            raise ComputeError("No overlap found between the two sequences.")
        s, t = both[0], both[-1] + 1
        a_off = len(row_a[:s].replace("-", ""))
        b_off = len(row_b[:s].replace("-", ""))
        row_a, row_b = row_a[s:t], row_b[s:t]
    a_start = a_off + 1
    b_start = b_off + 1
    W = 60
    blocks = []
    for s in range(0, len(row_a), W):
        block_a = row_a[s:s + W]
        block_b = row_b[s:s + W]
        mid = "".join("|" if x == y and x != "-" else ("." if x != "-" and y != "-" else " ")
                      for x, y in zip(block_a, block_b))
        blocks.append({"Block": s // W + 1, "Query_start": a_start + s,
                       "Query": block_a, "Match": mid, "Target": block_b})
    ncol = len(row_a)
    nmatch = sum(1 for x, y in zip(row_a, row_b) if x == y and x != "-")
    ngap = sum(1 for x, y in zip(row_a, row_b) if x == "-" or y == "-")
    ident = nmatch / ncol if ncol else 0.0
    flat_a = row_a.replace("-", "")
    flat_b = row_b.replace("-", "")
    mode_label = {"global": "global (Needleman–Wunsch)",
                  "local": "local (Smith–Waterman)",
                  "overlap": "overlap (terminal gaps free)"}[
        "local" if mlow.startswith("local") else ("overlap" if mlow.startswith("overlap") else "global")]
    metrics = [
        ("Score", f"{best.score:g}", "raw Biopython alignment score"),
        ("Identity", f"{100.0 * ident:.1f}%", "matching columns / aligned columns"),
        ("Aligned columns", str(ncol), ""),
        ("Matches / mismatches", f"{nmatch} / {ncol - nmatch - ngap}", ""),
        ("Gap columns", str(ngap), ""),
    ]
    if mlow.startswith("overlap"):
        metrics.append(("Query overlap start", str(a_start), ""))
        metrics.append(("Subject overlap start", str(b_start), ""))
    notes = [f"Biopython PairwiseAligner, {mode_label}; scoring: "
             + ("BLOSUM62, gap open -11 / extend -1 (protein)" if protein else
                "match +2 / mismatch -1, gap open -5 / extend -0.5 (nucleotide)").rstrip(".")]
    summary = f"{mode_label.capitalize()} alignment: score {best.score:g}, identity {100.0 * ident:.1f}% over {ncol} columns."
    return out("Pairwise Alignment", summary, metrics, blocks, notes=notes,
               fasta=f">aligned_query\n{flat_a}\n>aligned_target\n{flat_b}\n")


def pairwise_align(seq1: str = "ATGGCTAAAGGGCCCTTTAAAGGGCCC",
                   seq2: str = "ATGGCTAAAGGG---CCCTTTAAAGGGCCC",
                   mode: str = "global (Needleman-Wunsch) | local (Smith-Waterman) | overlap (ends free)") -> Dict[str, Any]:
    m = (mode or "global").lower()
    key = "local" if m.startswith("local") else ("overlap" if m.startswith("overlap") else "global")
    return _pairwise(seq1, seq2, key)


def local_align(seq1: str = "TTTTGGATGAAAGGGCCCTTTAGCCC",
                seq2: str = "ATGAAAGGGCCCTTTAG") -> Dict[str, Any]:
    return _pairwise(seq1, seq2, "local")


def global_align(seq1: str = "ATGGCTAAAGGGCCCTTTAAAGGGCCC",
                 seq2: str = "ATGGCTAAAGGGCCCCTTTAAAGGGCCC") -> Dict[str, Any]:
    return _pairwise(seq1, seq2, "global")


def overlap_align(seq1: str = "ATGGCTAAAGGGCCCTTT",
                  seq2: str = "CCCTTTAAAGGGCCC") -> Dict[str, Any]:
    return _pairwise(seq1, seq2, "overlap")


# ─────────────────────────── MSA ───────────────────────────

def _parse_fasta_records(text: str, field: str = "sequence", max_n: int = 64,
                         min_len: int = 4, max_len: int = 10_000) -> List[Tuple[str, str]]:
    if not text or not text.strip():
        raise ComputeError(f"No {field} data provided.")
    text = text.strip()
    recs: List[Tuple[str, str]] = []
    if text.startswith(">"):
        name, buf = None, []
        for line in text.splitlines():
            if line.startswith(">"):
                if name is not None:
                    recs.append((name, "".join(buf)))
                parts = line[1:].split()
                name, buf = (parts[0] if parts else f"seq{len(recs) + 1}"), []
            elif line.strip() and not line.startswith(";"):
                buf.append(line.strip())
        if name is not None:
            recs.append((name, "".join(buf)))
    else:
        for i, line in enumerate(text.splitlines(), start=1):
            s = line.strip()
            if s:
                recs.append((f"seq{i}", s))
    if not recs:
        raise ComputeError(f"No {field} records could be parsed.")
    if len(recs) > max_n:
        raise ComputeError(f"Only {max_n} {field} records are supported (got {len(recs)}).")
    for _, s in recs:
        if len(s) < min_len:
            raise ComputeError(f"Sequences must be at least {min_len} characters.")
        guard_len(s, max_len, field)
    return recs


def _msa(fasta: str, gap_open: float) -> Dict[str, Any]:
    recs = _parse_fasta_records(fasta or "", "sequence", max_n=64, min_len=4)
    names = [n for n, _ in recs]
    seqs = [s for _, s in recs]
    if len(names) < 2:
        raise ComputeError("At least two sequences are required.")
    if len(set(seqs)) == 1:
        raise ComputeError("All sequences are identical — nothing to align.")
    try:
        return progressive_msa(names, seqs, protein=_is_protein_like(seqs[0]),
                               gap_open=abs(float(gap_open or 10.0)) or 10.0)
    except MSAError as e:
        raise ComputeError(str(e)) from e


def _conserved_columns(rows: List[str]) -> int:
    """Number of columns where every non-gap letter is identical."""
    if not rows:
        return 0
    total = 0
    for i in range(len(rows[0])):
        letters = {r[i] for r in rows} - {"-"}
        if len(letters) <= 1:
            total += 1
    return total


def msa_align(fasta_sequences: str = ">seq1\nATGGCTAAAGGGCCCTTTAAAGGGCCC\n>seq2\nATGGCTAAAGGG---CCCTTTAAAGGG\n>seq3\nATGGCTCAAGGGCCCTTTAAAGGGCCC",
              gap_open_penalty: float = 10.0) -> Dict[str, Any]:
    res = _msa(fasta_sequences, gap_open_penalty)
    width = res["width"]
    pairs = res["aligned"]
    rows = [{"Sequence": n, "Length": len(s), "Gaps": s.count("-"), "Aligned": s}
            for n, s in pairs]
    ident = res["identity"]
    fully = _conserved_columns([s for _, s in pairs])
    fasta_out = "\n".join(f">{n}\n{s}" for n, s in pairs)
    notes = [
        "Progressive profile alignment implemented in titan_utils/msa.py (affine gap costs; "
        "BLOSUM62 for proteins). Not Clustal Omega — guide tree is Titan's own UPGMA.",
        f"Mean pairwise column identity after alignment: {100.0 * ident:.1f}%; fully conserved columns: {fully}.",
    ]
    return out("Multiple Sequence Alignment",
               f"{len(rows)} sequences aligned to width {width} (mean pairwise identity {100.0 * ident:.1f}%).",
               [("Sequences", str(len(rows)), ""), ("Alignment width", str(width), ""),
                ("Mean pairwise identity", f"{100.0 * ident:.1f}%", "column-based, after alignment"),
                ("Fully conserved columns", f"{fully} / {width}", "")],
               rows, columns=["Sequence", "Length", "Gaps", "Aligned"],
               notes=notes, fasta=fasta_out + "\n", newick=res.get("newick"))


def msa_clustalw(fasta_sequences: str = ">seq1\nATGGCTAAAGGGCCCTTTAAAGGGCCC\n>seq2\nATGGCTAAAGGG---CCCTTTAAAGGG\n>seq3\nATGGCTCAAGGGCCCTTTAAAGGGCCC",
                 line_length: int = 60) -> Dict[str, Any]:
    res = _msa(fasta_sequences, 10.0)
    txt = clustalw_text(res["aligned"], max(20, int(line_length or 60)))
    rows = [{"Line": i + 1, "Text": ln} for i, ln in enumerate(txt.splitlines())]
    notes = ["ClustalW-style *rendering* of the Titan progressive alignment (see the MSA tool). "
             "Numbers at right are ungap-counts per row; '*' marks fully conserved columns."]
    return out("MSA (ClustalW format)",
               f"{len(res['aligned'])} sequences, width {res['width']}, rendered in blocks.",
               [("Sequences", str(len(res["aligned"])), ""), ("Alignment width", str(res["width"]), "")],
               rows, columns=["Line", "Text"], notes=notes, text=txt)


def _pdist_pair(x: str, y: str) -> float:
    d = c = 0
    for a, b in zip(x, y):
        if a == "-" or b == "-":
            continue
        c += 1
        if a != b:
            d += 1
    return d / c if c else 0.0


def build_tree(alignment_fasta: str = ">seq1\nATGGCTAAAGGGCCCTTTAAAGGGCCC\n>seq2\nATGGCTAAAGGGCCCTTTAAAGGG---\n>seq3\nATGGCTCAAGGGCCCTTTAAAGGGCCC",
               method: str = "UPGMA (rooted) | Neighbour-Joining") -> Dict[str, Any]:
    recs = _parse_fasta_records(alignment_fasta or "", "alignment", max_n=64, min_len=4, max_len=20_000)
    names = [n for n, _ in recs]
    rows = [s for _, s in recs]
    if len(names) < 3:
        raise ComputeError("A tree needs at least three sequences.")
    if len({len(r) for r in rows}) != 1:
        raise ComputeError("Rows must have equal length — paste an alignment "
                           "(or run the MSA tool first and copy its output).")
    from Bio import Phylo
    from Bio.Phylo.TreeConstruction import DistanceMatrix, DistanceTreeConstructor
    m = (method or "UPGMA").lower()
    nj = m.startswith(("n", "nei"))
    n = len(names)
    lower = [[0.0 if j == i else _pdist_pair(rows[i], rows[j]) for j in range(i + 1)] for i in range(n)]
    tree = (DistanceTreeConstructor().nj if nj else DistanceTreeConstructor().upgma)(DistanceMatrix(names, lower))
    tree.root.name = None
    nh = StringIO()
    Phylo.write(tree, nh, "newick")
    ah = StringIO()
    Phylo.draw_ascii(tree, file=ah)
    rows_out = [{"Line": i + 1, "Text": ln} for i, ln in enumerate(ah.getvalue().splitlines())]
    notes = [f"Distance-based {'Neighbour-Joining' if nj else 'UPGMA'} tree via Biopython "
             "DistanceTreeConstructor on p-distances (fraction of differing non-gap columns) of the input "
             "alignment. For exploration and teaching, not publication phylogenetics."]
    return out("Phylogenetic Tree", f"{'NJ' if nj else 'UPGMA'} tree from {len(names)} aligned sequences.",
               [("Taxa", str(n), ""), ("Method", "Neighbour-Joining" if nj else "UPGMA", ""),
                ("Alignment length", str(len(rows[0])), "")],
               rows_out, columns=["Line", "Text"], notes=notes,
               newick=nh.getvalue().strip(), text=ah.getvalue())


def distance_matrix_tool(alignment_fasta: str = ">seq1\nATGGCTAAAGGGCCCTTTAAAGGGCCC\n>seq2\nATGGCTAAAGGGCCCTTTAAAGGG---\n>seq3\nATGGCTCAAGGGCCCTTTAAAGGGCCC") -> Dict[str, Any]:
    recs = _parse_fasta_records(alignment_fasta or "", "alignment", max_n=32, min_len=4, max_len=20_000)
    if len(recs) < 2:
        raise ComputeError("At least two sequences are required.")
    if len({len(s) for _, s in recs}) != 1:
        raise ComputeError("Rows must have equal length — paste an alignment file.")
    rows = [s for _, s in recs]
    names = [n for n, _ in recs]
    n = len(names)
    M = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i):
            M[i][j] = M[j][i] = round(_pdist_pair(rows[i], rows[j]), 4)
    flat = [{"Sequence_1": names[i], "Sequence_2": names[j],
             "p_distance": M[i][j], "Identity_%": round(100 * (1 - M[i][j]), 1)}
            for i in range(n) for j in range(i + 1, n)]
    notes = [f"p-distance = differing columns / compared columns; gap columns excluded from numerator and "
             f"denominator. Alignment width {len(rows[0])}."]
    return out("Pairwise Distance Matrix", f"{n} sequences → {len(flat)} pairwise distances.",
               [("Sequences", str(n), ""), ("Alignment width", str(len(rows[0])), "")],
               flat, columns=["Sequence_1", "Sequence_2", "p_distance", "Identity_%"],
               fig={"kind": "heatmap", "x": names, "y": names, "grid": M, "title": "p-distance matrix"},
               notes=notes)


def sequence_logo(fasta_sequences: str = ">seq1\nATGGCTAAAGGGCCCTTT\n>seq2\nATGGCTAAAGGGTCCTTT\n>seq3\nATGGCTCAAGGGCCCTTT",
                  method: str = "Shannon information content (bits)") -> Dict[str, Any]:
    recs = _parse_fasta_records(fasta_sequences or "", "sequence", max_n=64, min_len=2)
    rows = [s for _, s in recs]
    if len({len(r) for r in rows}) != 1:
        raise ComputeError("Sequence logo needs equal-length sequences. Align them first "
                           "(MSA tool) and paste the aligned rows.")
    n = len(rows)
    width = len(rows[0])
    maxbits = math.log2(20) if _is_protein_like(rows[0]) else math.log2(4)
    per_col = []
    ic_total = 0.0
    for i in range(width):
        cnt = Counter(r[i] for r in rows)
        ent = -sum((c / n) * math.log2(c / n) for c in cnt.values())
        ic = max(0.0, maxbits - ent)
        ic_total += ic
        per_col.append({"Position": i + 1, "Information_content_bits": round(ic, 3),
                        "Frequencies": {k: round(v / n, 3) for k, v in sorted(cnt.items())},
                        "Consensus": cnt.most_common(1)[0][0]})
    notes = [f"Per-column Shannon information content IC = {maxbits:.2f} bits max − H "
             "(log2 of alphabet size: nucleotides 4, proteins 20). No small-sample correction "
             "applied, so IC can be inflated for short alignments."]
    return out("Sequence Logo",
               f"Logo of {width} columns × {n} sequences; total IC {ic_total:.1f} bits.",
               [("Columns", str(width), ""), ("Sequences", str(n), ""),
                ("Mean IC (bits/col)", f"{ic_total / width:.3f}", "")],
               per_col, columns=["Position", "Information_content_bits", "Consensus", "Frequencies"],
               fig={"kind": "bar", "x": [str(c["Position"]) for c in per_col],
                    "y": [c["Information_content_bits"] for c in per_col],
                    "xlabel": "Alignment position", "ylabel": "IC (bits)",
                    "title": "Sequence logo — information content per column"},
               notes=notes)


def dotplot(seq1: str = "ATGGCTAAAGGGCCCTTTAAAGGGCCC", seq2: str = "ATGGCTAAAGGGCCCCTTTAAAGGGCCC",
            window: int = 7) -> Dict[str, Any]:
    a, b = _sanitize(seq1), _sanitize(seq2)
    guard_len(a, 4_000, "sequence 1")
    guard_len(b, 4_000, "sequence 2")
    k = max(1, int(window or 7))
    hits = []
    kb: Dict[str, List[int]] = {}
    for j in range(0, len(b) - k + 1):
        kb.setdefault(b[j:j + k], []).append(j)
    for i in range(0, len(a) - k + 1):
        for j in kb.get(a[i:i + k], ()):
            hits.append((i + 1, j + 1))
    rows = [{"Query_pos": i, "Subject_pos": j} for i, j in hits[:2000]]
    hs = set(hits)
    best_run = 0
    for (i, j) in hits:
        if (i - 1, j - 1) not in hs:
            L = 0
            while (i + L, j + L) in hs:
                L += 1
            best_run = max(best_run, L)
    notes = [f"Exact {k}-mer matches (window={k}); reverse-complement diagonals are not drawn. "
             "Longest diagonal run ≈ length of the longest exactly shared segment."]
    return out("Dot Plot", f"{len(hits)} exact {k}-mer matches; longest diagonal {best_run + k - 1} bp.",
               [("Matches", str(len(hits)), ""), ("Longest diagonal (bp)", str(best_run + k - 1), ""),
                ("Window (k)", str(k), "")],
               rows, columns=["Query_pos", "Subject_pos"],
               fig={"kind": "scatter", "x": [i for i, _ in hits[:2000]], "y": [j for _, j in hits[:2000]],
                    "xlabel": "Sequence 1 position", "ylabel": "Sequence 2 position",
                    "title": f"Dot plot (k={k})"}, notes=notes)


def consensus_sequence(alignment_fasta: str = ">seq1\nATGGCTAAAGGGCCCTTTAAAGGGCCC\n>seq2\nATGGCTAAAGGGCCCTTTAAAGG\n>seq3\nATGGCTCAAGGGCCCTTTAAAGGGCCC",
                       method: str = "Majority rule (IUPAC ambiguity)", threshold: float = 0.6) -> Dict[str, Any]:
    recs = _parse_fasta_records(alignment_fasta or "", "sequence", max_n=64, min_len=4)
    rows = [s for _, s in recs]
    if len({len(r) for r in rows}) != 1:
        res = _msa(alignment_fasta, 10.0)
        rows = [s for _, s in res["aligned"]]
        pre_aligned = False
    else:
        pre_aligned = True
    width = len(rows[0])
    cons = _cons(rows, float(threshold or 0.6))
    counts = []
    for i in range(width):
        c = Counter(r[i] for r in rows)
        top, tn = c.most_common(1)[0]
        counts.append({"Position": i + 1, "Consensus": cons[i], "Top_letter": top,
                       "Top_frequency": round(tn / len(rows), 3),
                       "Gaps": c.get("-", 0)})
    notes = [("Input is a gapped alignment — consensus read column-wise." if pre_aligned
              else "Sequences were first aligned with the Titan progressive MSA, then read column-wise."),
             "Columns whose top letter is under the threshold are reported as N (or X for proteins)."]
    return out("Consensus Sequence",
               f"Consensus of {len(rows)} sequences across {width} columns (threshold {float(threshold or 0.6):.0%}).",
               [("Length", str(width), ""), ("Sequences", str(len(rows)), ""),
                ("Ambiguity (N/X)", str(cons.count("N") + cons.count("X")), "columns under threshold")],
               counts, columns=["Position", "Consensus", "Top_letter", "Top_frequency", "Gaps"],
               fasta=f">consensus\n{cons}\n", notes=notes,
               text=f"Consensus ({width} columns):\n{cons}")


ALIGN_TOOLS = {
    34: pairwise_align,
    35: local_align,
    36: global_align,
    37: overlap_align,
    38: msa_align,
    39: msa_clustalw,
    40: build_tree,
    41: distance_matrix_tool,
    42: sequence_logo,
    43: dotplot,
    44: consensus_sequence,
}
