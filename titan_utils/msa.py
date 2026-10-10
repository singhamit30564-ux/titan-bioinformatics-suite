"""Progressive multiple-sequence alignment for Titan (pure Python + Biopython).

Pipeline (the classic progressive strategy, honestly documented):
1. all-vs-all pairwise alignments with ``Bio.Align.PairwiseAligner`` (validated
   C implementation);
2. distances from those alignments (1 − pairwise identity over the full
   aligned width, gap columns counted as non-matching);
3. an UPGMA guide tree (implemented here; Biopython's UPGMA/NJ remain
   available for the tree pages);
4. bottom-up profile–profile alignment with mean sum-of-columns substitution
   scores and a linear gap penalty — a documented simplification of Clustal's
   affine sum-of-pairs objective.

This produces a REAL gapped alignment (insertions can be placed internally,
unlike the old dash-padding demo). It is a teaching-grade aligner — NOT a
replacement for Clustal Omega / MUSCLE / MAFFT for research, and the pages say
so.
"""
from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

MAX_DP_CELLS_PER_MERGE = 2_000_000


class MSAError(ValueError):
    """Raised for invalid or oversized MSA inputs."""


def _blosum():
    from Bio.Align import substitution_matrices
    return substitution_matrices.load("BLOSUM62")


class _Scoring:
    """Substitution lookup; profiles also use −1 for residue-vs-gap columns."""

    def __init__(self, protein: bool):
        if protein:
            m = _blosum()
            idx = {c: i for i, c in enumerate("ARNDCQEGHILKMFPSTWYV") if c in m}

            def sub(a: str, b: str) -> float:
                ia, ib = idx.get(a), idx.get(b)
                if ia is None or ib is None:
                    return -1.0  # X / unknown letters behave as mismatches
                return float(m[ia, ib])
        else:
            def sub(a: str, b: str) -> float:
                return 1.0 if a == b else -1.0
        self.sub = sub
        self.gap_pen = -1.0  # residue vs gap in a profile-profile column


def _pairwise(a: str, b: str, protein: bool, gap_open: float, gap_extend: float):
    from Bio import Align
    al = Align.PairwiseAligner()
    al.mode = "global"
    if protein:
        al.substitution_matrix = _blosum()
    else:
        al.match_score, al.mismatch_score = 1.0, -1.0
    al.open_gap_score = -gap_open
    al.extend_gap_score = -gap_extend
    try:
        return al.align(a, b)[0]
    except Exception:  # empty/degenerate sequences etc.
        return None


def identity_after_pairwise(a: str, b: str, protein: bool, gap_open: float = 10.0,
                            gap_extend: float = 0.5) -> float:
    """Matched columns / total aligned columns (gap columns count as mismatches)."""
    if a == b:
        return 1.0
    aln = _pairwise(a, b, protein, gap_open, gap_extend)
    if aln is None:
        return 0.0
    g1, g2 = str(aln[0]), str(aln[1])
    aligned = len(g1)
    if not aligned:
        return 0.0
    matches = sum(1 for x, y in zip(g1, g2) if x == y and x != "-")
    return matches / aligned


def distance_matrix(sequences: Sequence[str], protein: bool = False,
                    gap_open: float = 10.0, gap_extend: float = 0.5) -> List[List[float]]:
    n = len(sequences)
    d = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            ident = identity_after_pairwise(sequences[i], sequences[j], protein, gap_open, gap_extend)
            d[i][j] = d[j][i] = max(0.0, min(1.0, 1.0 - ident))
    return d


def upgma(d: List[List[float]]) -> Tuple[List[Tuple[int, int]], str, Dict[int, float]]:
    """Classic UPGMA on a symmetric matrix.

    Returns (merge_order, newick, heights). Merge order drives progressive
    alignment; the Newick string embeds branch heights.
    """
    n = len(d)
    if n < 2:
        raise MSAError("Tree building needs at least 2 sequences.")
    members = {i: [i] for i in range(n)}
    label = {i: f"seq{i + 1}" for i in range(n)}
    dist: Dict[frozenset, float] = {frozenset((i, j)): d[i][j] for i in range(n) for j in range(i + 1, n)}
    alive = set(range(n))
    nid = n
    order: List[Tuple[int, int]] = []
    heights: Dict[int, float] = {}
    while len(alive) > 1:
        arr = sorted(alive)
        best = None
        for x in range(len(arr)):
            for y in range(x + 1, len(arr)):
                a, b = arr[x], arr[y]
                dd = dist[frozenset((a, b))]
                if best is None or dd < best[0]:
                    best = (dd, a, b)
        dd, a, b = best
        h = dd / 2.0
        merged = nid
        nid += 1
        order.append((a, b))
        members[merged] = members[a] + members[b]
        label[merged] = f"({label[a]},{label[b]}):{h:.5g}"
        heights[merged] = h
        sa, sb = len(members[a]), len(members[b])
        for c in alive:
            if c in (a, b):
                continue
            dist[frozenset((merged, c))] = (
                dist[frozenset((a, c))] * sa + dist[frozenset((b, c))] * sb
            ) / (sa + sb)
        alive.discard(a)
        alive.discard(b)
        alive.add(merged)
    root = next(iter(alive))
    return order, label[root] + ";", heights


def _profile_score_matrix(A: List[str], B: List[str], scoring: _Scoring) -> List[List[float]]:
    """S[i][j] = mean over row pairs of the substitution score at (A col i, B col j)."""
    from collections import Counter
    mA, mB = len(A), len(B)
    ca = [Counter(col) for col in zip(*A)]
    cb = [Counter(col) for col in zip(*B)]
    la, lb = len(ca), len(cb)
    S = [[0.0] * lb for _ in range(la)]
    for i in range(la):
        ci = ca[i]
        for j in range(lb):
            cj = cb[j]
            tot = 0.0
            for x, nx in ci.items():
                for y, ny in cj.items():
                    if x == "-" and y == "-":
                        s = 0.0
                    elif x == "-" or y == "-":
                        s = scoring.gap_pen
                    else:
                        s = scoring.sub(x, y)
                    tot += nx * ny * s
            S[i][j] = tot / (mA * mB)
    return S


def _align_profiles(A: List[str], B: List[str], scoring: _Scoring, gap_penalty: float) -> List[str]:
    """Needleman-style DP over profile columns; returns merged row strings."""
    la, lb = len(A[0]), len(B[0])
    if la * lb > MAX_DP_CELLS_PER_MERGE:
        raise MSAError(
            f"Profile merge would need {la * lb:,} DP cells (cap {MAX_DP_CELLS_PER_MERGE:,}). "
            "Reduce the number or length of sequences, or use a dedicated aligner."
        )
    S = _profile_score_matrix(A, B, scoring)
    NEG = float("-inf")
    M = [[0.0] * (lb + 1) for _ in range(la + 1)]
    ptr = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(1, la + 1):
        M[i][0] = M[i - 1][0] + S[i - 1][0] - gap_penalty
        ptr[i][0] = 2
    for j in range(1, lb + 1):
        M[0][j] = M[0][j - 1] + S[0][j - 1] - gap_penalty
        ptr[0][j] = 1
    for i in range(1, la + 1):
        Mi, Mip, pi, Si = M[i], M[i - 1], ptr[i], S[i - 1]
        for j in range(1, lb + 1):
            diag = Mip[j - 1] + Si[j - 1]
            up = Mip[j] - gap_penalty          # gap column for B while A advances
            left = Mi[j - 1] - gap_penalty     # gap column for A while B advances
            best, p = diag, 0
            if up > best:
                best, p = up, 2
            if left > best:
                best, p = left, 1
            Mi[j] = best
            pi[j] = p
    mA, mB = len(A), len(B)
    colA: List[str] = []
    colB: List[str] = []
    i, j = la, lb
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            p = ptr[i][j]
        else:
            p = 2 if i > 0 else 1  # exhausted side: consume remaining as gaps
        if p == 0:
            colA.append("".join(row[i - 1] for row in A))
            colB.append("".join(row[j - 1] for row in B))
            i, j = i - 1, j - 1
        elif p == 1:   # came from the left: B consumed a column, A gets a gap
            colA.append("-" * mA)
            colB.append("".join(row[j - 1] for row in B))
            j -= 1
        else:          # came from above: A consumed a column, B gets a gap
            colA.append("".join(row[i - 1] for row in A))
            colB.append("-" * mB)
            i -= 1
    colA.reverse()
    colB.reverse()
    rows = [""] * (mA + mB)
    for k in range(len(colA)):
        a_part, b_part = colA[k], colB[k]
        for r in range(mA):
            rows[r] += a_part[r]
        for r in range(mB):
            rows[mA + r] += b_part[r]
    return rows


def progressive_msa(names: Sequence[str], seqs: Sequence[str], *, protein: bool = False,
                    gap_open: float = 10.0, gap_extend: float = 0.5,
                    msa_gap: float = 1.5) -> Dict[str, object]:
    """Return {"aligned": [(name, row)], "width": int, "identity": float, "newick": str}."""
    if len(seqs) != len(names) or len(seqs) < 2:
        raise MSAError("MSA needs at least 2 sequences.")
    if len(seqs) > 64:
        raise MSAError(f"{len(seqs)} sequences exceeds the 64-sequence cap for this engine.")
    scoring = _Scoring(protein)
    d = distance_matrix(seqs, protein=protein, gap_open=gap_open, gap_extend=gap_extend)
    order, newick, _heights = upgma(d)
    prof: Dict[int, List[str]] = {i: [seqs[i]] for i in range(len(seqs))}
    merge_children: Dict[int, Tuple[int, int]] = {}
    nid = len(seqs)
    for a, b in order:
        prof[nid] = _align_profiles(prof[a], prof[b], scoring, msa_gap)
        merge_children[nid] = (a, b)
        nid += 1
    root = nid - 1
    final_rows = prof[root]
    leaves = _leaf_order(root, merge_children, len(seqs))
    aligned = [(names[leaves[k]], final_rows[k]) for k in range(len(seqs))]
    return {"aligned": aligned, "width": len(final_rows[0]),
            "identity": column_identity(final_rows), "newick": newick}


def _leaf_order(node: int, merges: Dict[int, Tuple[int, int]], n: int) -> List[int]:
    if node < n:
        return [node]
    a, b = merges[node]
    return _leaf_order(a, merges, n) + _leaf_order(b, merges, n)


def column_identity(rows: List[str]) -> float:
    """Mean per-column dominance: majority non-gap residue fraction."""
    if not rows:
        return 0.0
    width = len(rows[0])
    tot = 0.0
    counted = 0
    for j in range(width):
        col = [r[j] for r in rows if r[j] != "-"]
        if not col:
            continue
        counts: Dict[str, int] = {}
        for c in col:
            counts[c] = counts.get(c, 0) + 1
        tot += max(counts.values()) / len(col)
        counted += 1
    return tot / counted if counted else 0.0


def consensus(rows: List[str], threshold: float = 0.6) -> str:
    """Majority-rule consensus; N (nucleotide) / X (protein) below threshold."""
    if not rows:
        return ""
    width = len(rows[0])
    protein_like = any(any(c not in "ATCGUN-" for c in r if c.isalpha()) for r in rows)
    out_chars = []
    for j in range(width):
        col = [r[j] for r in rows if r[j] != "-"]
        if not col:
            out_chars.append("-")
            continue
        counts: Dict[str, int] = {}
        for c in col:
            counts[c] = counts.get(c, 0) + 1
        best, bn = max(counts.items(), key=lambda kv: (kv[1], kv[0]))
        out_chars.append(best if bn / len(col) >= threshold else ("X" if protein_like else "N"))
    return "".join(out_chars)


def clustalw_text(pairs: List[Tuple[str, str]], block: int = 60) -> str:
    """Render aligned (name, row) pairs in ClustalW block format with a '*' line."""
    if not pairs:
        return ""
    width = len(pairs[0][1])
    lines: List[str] = []
    for start in range(0, width, block):
        for name, seq in pairs:
            chunk = seq[start:start + block]
            lines.append(f"{name[:12]:<12s} {chunk:<{block}s} {start + len(chunk)}")
        star = []
        for k in range(min(block, width - start)):
            col = [seq[start + k] for _, seq in pairs]
            star.append("*" if len(set(col)) == 1 and col[0] != "-" else " ")
        lines.append(" " * 13 + "".join(star))
        lines.append("")
    return "\n".join(lines)
