"""Compute functions for Titan tools 18–33 (genomics & QC)."""
from __future__ import annotations

from typing import Any, Dict, List

from ..sequence import gc_fraction_safe, revcomp
from . import ComputeError, MAX_SEQ_LEN, guard_len, out, prepare_dna

MAX_PASTE = 4_000_000      # characters allowed for pasted file content
MAX_RECORDS = 5000


# ─────────────────────────────────────────────────────────────────────────────
# Tool 18 — FASTA / FASTQ QC (paste)
# ─────────────────────────────────────────────────────────────────────────────
def _is_fastq(lines: List[str]) -> bool:
    return (len(lines) >= 4 and lines[0].startswith("@")
            and len(lines[1]) == len(lines[3]) and any(c in lines[3] for c in "!\"#$%&'()*+,-./"))


def file_qc(text: str = ">read1\nATGCGATCGATCGCGGCGATCGATCGATCG\n>read2\nGGGCCCTTTAAATTTGGGCCCAAA",
          fmt: str = "auto") -> Dict[str, Any]:
    raw = (text or "").replace("\r", "")
    if not raw.strip():
        raise ComputeError("Paste FASTA (with >headers) or FASTQ content first.")
    guard_len(raw, MAX_PASTE, "pasted text")
    lines = raw.split("\n")
    fastq = fmt == "FASTQ" if fmt in ("FASTA", "FASTQ") else _is_fastq([l for l in lines if l.strip()])
    rows, quals = [], []
    if fastq:
        recs = [l for l in lines if l.strip()]
        if len(recs) % 4:
            raise ComputeError(f"FASTQ must come in groups of 4 lines — found {len(recs)} non-blank lines.")
        n = len(recs) // 4
        if n > MAX_RECORDS:
            raise ComputeError(f"{n:,} reads exceeds the {MAX_RECORDS:,}-read cap here — use the Batch Processor page.")
        for i in range(n):
            name, seq, plus, qual = recs[4 * i:4 * i + 4]
            if not seq:
                raise ComputeError(f"Empty sequence at read {i + 1}.")
            q = [ord(c) - 33 for c in qual]
            if any(v < 0 or v > 93 for v in q):
                raise ComputeError(f"Non-Phred+33 quality characters at read {i + 1}.")
            mean_q = sum(q) / len(q)
            frac_low = sum(1 for v in q if v < 20) / len(q)
            rows.append({"Read": i + 1, "ID": name[1:].split()[0] if name.startswith("@") else i + 1,
                         "Length": len(seq), "GC_%": round(100 * gc_fraction_safe(seq), 1),
                         "Mean_Q": round(mean_q, 1), "Q>=20_bases": f"{(1 - frac_low) * 100:.1f}%",
                         "Ns": seq.upper().count("N")})
            quals.extend(q)
        h = [0] * 47
        for v in quals:
            h[min(v, 46)] += 1
        fmt_label = "FASTQ"
    else:
        seqs: List[List[str]] = []
        cur: List[str] = []
        name_cur = ""
        for l in lines:
            if l.startswith(">"):
                if cur:
                    seqs.append([name_cur, "".join(cur)])
                parts = l[1:].strip().split(maxsplit=1)
                name_cur = parts[0] if parts else f"record{len(seqs) + 1}"
                cur = []
            elif l.strip():
                cur.append(l.strip())
        if cur or name_cur:
            seqs.append([name_cur, "".join(cur)])
        seqs = [s for s in seqs if s[1]]
        if not seqs:
            raise ComputeError("No sequences found (need >header lines in FASTA).")
        if len(seqs) > MAX_RECORDS:
            raise ComputeError(f"{len(seqs):,} records exceeds the {MAX_RECORDS:,}-record cap here.")
        for i, (nm, s) in enumerate(seqs, 1):
            up = s.upper()
            bad = sorted({c for c in up if c not in set("ACGTURYSWKMBDHVN-." )})
            rows.append({"Record": i, "ID": nm, "Length": len(up),
                         "GC_%": round(100 * gc_fraction_safe(up), 1),
                         "Ns": up.count("N"), "Bad_chars": ",".join(bad) if bad else "—"})
        h = []
        fmt_label = "FASTA"
    tot = sum(r["Length"] for r in rows)
    mean_gc = sum(r["GC_%"] for r in rows) / max(1, len(rows))
    fig = ({"kind": "bar", "x": list(range(47)), "y": h, "xlabel": "Phred Q", "ylabel": "Bases",
            "title": "Base quality histogram (Q0–Q46)"} if h else
           {"kind": "bar", "x": [str(r["ID"]) for r in rows[:30]], "y": [r["Length"] for r in rows[:30]],
            "xlabel": "Record", "ylabel": "Length (bp)", "title": "Record lengths"})
    return out(
        title=f"{fmt_label} QC ({len(rows):,} records)",
        summary=(f"{len(rows):,} {fmt_label} records, {tot:,} total bases, mean GC {mean_gc:.1f}%"
                 + (f"; mean read quality Q{sum(quals) / max(1, len(quals)):.1f}." if h else ".")),
        metrics=[("Records", f"{len(rows):,}", None), ("Total bases", f"{tot:,}", None),
                 ("Mean GC", f"{mean_gc:.1f}%", None),
                 ("Mean read Q", f"Q{sum(quals) / max(1, len(quals)):.1f}" if h else "n/a", None)],
        rows=rows[:500], columns=list(rows[0].keys()), fig=fig,
        notes=["Quality encoding assumed Phred+33 (Sanger/Illumina 1.8+).",
               "This is a QC summary, not a repair tool — bad-character records are flagged, not modified."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 19 — k-mer frequency
# ─────────────────────────────────────────────────────────────────────────────
def kmer_frequency(sequence: str = "ATGCGATCGATCGATCGCATCGATC", k: int = 3,
                   top: int = 15) -> Dict[str, Any]:
    from collections import Counter
    s = prepare_dna(sequence)
    guard_len(s, 1_000_000)
    k = max(1, min(int(k or 3), 12))
    if len(s) < k:
        raise ComputeError(f"k={k} exceeds sequence length {len(s)}.")
    counts = Counter(s[i:i + k] for i in range(len(s) - k + 1))
    ranked = counts.most_common(max(1, min(int(top or 15), 50)))
    total = sum(counts.values())
    return out(
        title=f"{k}-mer Spectrum",
        summary=(f"{total:,} {k}-mers with {len(counts):,} unique; top “{ranked[0][0]}” "
                 f"({ranked[0][1]:,}×, {100 * ranked[0][1] / total:.1f}%)."),
        metrics=[("Windows", f"{total:,}", None), ("Unique k-mers", f"{len(counts):,}", None),
                 ("Space size 4^k", f"{4 ** k:,}", "how many distinct k-mers exist at all")],
        rows=[{"kmer": km, "Count": n, "Freq_percent": round(100 * n / total, 3)} for km, n in ranked],
        columns=["kmer", "Count", "Freq_percent"],
        fig={"kind": "bar", "x": [km for km, _ in ranked], "y": [n for _, n in ranked],
             "xlabel": f"{k}-mer", "ylabel": "Count", "title": f"Top {len(ranked)} {k}-mers"},
        notes=["Forward strand only; reverse-complement folding can be enabled on the dedicated page."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 20 — n-gram over/under-representation vs uniform model
# ─────────────────────────────────────────────────────────────────────────────
def ngrams_analysis(sequence: str = "ATGATGATGCGCGCGCATCATCAGTAGG", n: int = 3,
                    top: int = 12) -> Dict[str, Any]:
    from collections import Counter
    import math
    s = prepare_dna(sequence)
    guard_len(s, 500_000)
    n = max(1, min(int(n or 3), 10))
    if len(s) - n + 1 < n:
        raise ComputeError("Sequence too short for this n-gram size.")
    counts = Counter(s[i:i + n] for i in range(len(s) - n + 1))
    total = sum(counts.values())
    exp = total / (4 ** n)
    rows = sorted(({"ngram": g, "Observed": c, "Expected_uniform": round(exp, 1),
                    "log2_OE": round(math.log2(c / exp) if c else -99, 2)} for g, c in counts.items()),
                  key=lambda r: -r["Observed"])
    over = [r for r in rows if r["log2_OE"] >= 1][:10]
    under = [r for r in sorted(rows, key=lambda r: r["log2_OE"]) if r["log2_OE"] <= -1][:10]
    return out(
        title=f"{n}-gram Enrichment (uniform background)",
        summary=(f"{total:,} words scored against the uniform 4^{n} model; "
                 f"{len(over)} over-represented (log2(O/E) ≥ +1), {len(under)} under-represented."),
        metrics=[("Words", f"{total:,}", None),
                 ("Over-represented", f"{len(over)}", "log2 O/E ≥ 1 vs uniform"),
                 ("Most enriched", over[0]["ngram"] if over else "—", None)],
        rows=rows[:max(1, min(int(top or 12), 50))],
        columns=["ngram", "Observed", "Expected_uniform", "log2_OE"],
        fig={"kind": "bar", "x": [r["ngram"] for r in rows[:15]], "y": [r["log2_OE"] for r in rows[:15]],
             "xlabel": "n-gram", "ylabel": "log2(O/E)", "title": "Log-ratio vs uniform"},
        notes=["Background is a uniform model, NOT a shuffled/mononucleotide-preserving one — "
               "composition bias inflates all ratios; read them as relative only."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 21 — Simple PCR primer pair design
# ─────────────────────────────────────────────────────────────────────────────
def primer_design(target: str = "ATGGCTAAAGGGCCCTTTGGGCCCATAGTTGCATCGATCGATCGATTAGCATGCGGATCCAAAT",
                  tm_low: float = 56.0, tm_high: float = 62.0, primer_len: int = 21) -> Dict[str, Any]:
    from Bio.Seq import Seq
    s = prepare_dna(target)
    guard_len(s, 20_000)
    L = max(15, min(int(primer_len or 21), 30))
    lo, hi = sorted((float(tm_low or 56), float(tm_high or 62)))
    if len(s) < 2 * L + 10:
        raise ComputeError(f"Target needs at least {2 * L + 10} bp to design a primer pair (got {len(s)}).")
    from ..thermo import nn_tm as _tm, ThermoError as _TE

    def ok_candidate(p: str) -> bool:
        try:
            t = _tm(p)
        except _TE:
            return False
        gc = 100.0 * (p.count("G") + p.count("C")) / len(p)
        if not (lo - 6 <= t <= hi + 6) or not (35 <= gc <= 65):
            return False
        if any(p[i:i + 5] == p[i] * 5 for i in range(len(p) - 4)):
            return False
        return not p.endswith("GGGG") and not p.endswith("AAAA")

    cands: List[Dict[str, Any]] = []
    step = max(1, len(s) // 5000)
    for fs in range(0, len(s) - 2 * L, step):
        f = s[fs:fs + L]
        if not ok_candidate(f):
            continue
        tmf = _tm(f)
        best = None
        for rs in range(fs + L, min(fs + 800, len(s))):
            rwin = s[rs:rs + L]
            if len(rwin) < L:
                break
            r = str(Seq(rwin).reverse_complement())
            if not ok_candidate(r):
                continue
            t = _tm(r)
            d = abs(t - tmf)
            if d > 2.5:
                continue
            score = abs((tmf + t) / 2 - (lo + hi) / 2) + d
            if best is None or score < best[0]:
                best = (score, rs, r, t)
        if best:
            _, rs, r, tmr = best
            cands.append({"fwd_pos": fs + 1, "fwd": f, "fwd_Tm": round(tmf, 1),
                          "rev_pos": rs + 1, "rev": r, "rev_Tm": round(tmr, 1),
                          "product_bp": rs + L - fs,
                          "gc_f": round(100 * (f.count("G") + f.count("C")) / L, 1),
                          "gc_r": round(100 * (r.count("G") + r.count("C")) / L, 1)})
            if len(cands) >= 25:
                break
    cands.sort(key=lambda c: abs((c["fwd_Tm"] + c["rev_Tm"]) / 2 - (lo + hi) / 2))
    if not cands:
        return out(
            title="Primer Design — no pair found",
            summary=f"No forward/reverse pair satisfied Tm {lo:.0f}–{hi:.0f} °C and 35–65% GC inside {len(s):,} bp.",
            metrics=[("Candidates", "0", None)],
            rows=[{"fwd_pos": "—", "fwd": "—", "fwd_Tm": "—", "rev_pos": "—", "rev": "—",
                   "rev_Tm": "—", "product_bp": "—", "gc_f": "—", "gc_r": "—"}],
            columns=list(cands[0].keys()) if cands else
            ["fwd_pos", "fwd", "fwd_Tm", "rev_pos", "rev", "rev_Tm", "product_bp", "gc_f", "gc_r"],
            notes=["Widen the Tm range or the target sequence, then retry."],
        )
    best = cands[0]
    return out(
        title=f"Primer pair (amplicon {best['product_bp']} bp)",
        summary=(f"Best pair at {best['fwd_pos']}–{best['rev_pos'] + L - 1}; ΔTm "
                 f"{abs(best['fwd_Tm'] - best['rev_Tm']):.1f} °C, Tm {best['fwd_Tm']}/{best['rev_Tm']} °C (NN)."),
        metrics=[("Amplicon", f"{best['product_bp']} bp", None),
                 ("Pair ΔTm", f"{abs(best['fwd_Tm'] - best['rev_Tm']):.1f} °C", "kept ≤ 2.5 °C"),
                 ("Candidates", f"{len(cands)}", None)],
        rows=cands[:10], columns=list(best.keys()),
        fig={"kind": "bar", "x": [f"pair {i+1}" for i in range(min(10, len(cands)))],
             "y": [c["product_bp"] for c in cands[:10]], "xlabel": "Rank",
             "ylabel": "Product (bp)", "title": "Candidate amplicon sizes"},
        notes=["Heuristics: NN Tm window, 35–65% GC, no 5-run homopolymers, ΔTm ≤ 2.5 °C; "
               "no secondary-structure/dimer free-energy screening — validate before ordering.",
               "Positions are 1-based on the input (forward) strand."],
        fasta=f">forward_{best['fwd_pos']}\n{best['fwd']}\n>reverse_{best['rev_pos']}\n{best['rev']}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 22 — CpG island detection (Gardiner-Garden-style)
# ─────────────────────────────────────────────────────────────────────────────
def cpg_islands(sequence: str = "ATGCATGCATGC" + "CGCGATCGATCGCGCGATCGCGATCG" * 6 + "ATATATATATAT",
                window: int = 200, min_gc: float = 0.5, min_oe: float = 0.6) -> Dict[str, Any]:
    import numpy as np
    s = prepare_dna(sequence)
    guard_len(s, 1_000_000)
    w = max(50, min(int(window or 200), max(50, len(s))))
    gc_min = float(min_gc or 0.5)
    oe_min = float(min_oe or 0.6)
    arr = np.frombuffer(s.encode("ascii"), dtype=np.uint8).astype(np.int64)
    isg = (arr == ord("G")).astype(np.int64)
    isc = (arr == ord("C")).astype(np.int64)
    gcf = (isg + isc)
    cg = np.zeros_like(gcf)
    cg[:-1] = ((isc[:-1] == 1) & (isg[1:] == 1)).astype(np.int64)
    cs = np.concatenate(([0], gcf.cumsum()))
    cg_cum = np.concatenate(([0], cg.cumsum()))
    c_cum = np.concatenate(([0], isc.cumsum()))
    g_cum = np.concatenate(([0], isg.cumsum()))
    n = len(s)
    starts = np.arange(0, max(0, n - w + 1))
    gcfrac = (cs[starts + w] - cs[starts]) / w
    ccount = (c_cum[starts + w] - c_cum[starts])
    gcount = (g_cum[starts + w] - g_cum[starts])
    cgcount = (cg_cum[starts + w] - cg_cum[starts])
    denom = np.where(ccount * gcount == 0, np.nan, cgcount * w / (ccount * gcount))
    good = (gcfrac >= gc_min) & (np.nan_to_num(denom, nan=0.0) >= oe_min)
    islands = []
    i = 0
    good_l = good.tolist()
    while i < len(good_l):
        if good_l[i]:
            j = i
            while j + 1 < len(good_l) and good_l[j + 1]:
                j += 1
            length = j - i + w
            seg = s[i:j + w]
            seg_gc = 100.0 * (seg.count("G") + seg.count("C")) / max(1, len(seg))
            seg_oe = (seg.count("CG") * len(seg)) / max(1, seg.count("C") * seg.count("G"))
            islands.append({"Start_1based": i + 1, "Length_bp": length,
                            "GC_percent": round(seg_gc, 1), "ObsExp_CpG": round(seg_oe, 2)})
            i = j + 1
        else:
            i += 1
    return out(
        title=f"CpG islands: {len(islands)} candidate(s)",
        summary=(f"Window {w} bp, GC ≥ {gc_min:.0%}, O/E ≥ {oe_min:.0%} (Gardiner-Garden-style): "
                 + (f"{len(islands)} island(s); longest {max(x['Length_bp'] for x in islands):,} bp."
                    if islands else "no islands in this input.")),
        metrics=[("Sequence", f"{n:,} bp", None), ("CpG islands", f"{len(islands)}", None),
                 ("Overall CpG O/E", f"{(s.count('CG') * n) / max(1, s.count('C') * s.count('G')):.2f}", None)],
        rows=islands[:100] or [{"Start_1based": "—", "Length_bp": 0, "GC_percent": 0, "ObsExp_CpG": 0}],
        columns=["Start_1based", "Length_bp", "GC_percent", "ObsExp_CpG"],
        fig={"kind": "line", "x": (starts + 1).tolist(), "y": np.round(gcfrac, 3).tolist(),
             "xlabel": "Window start", "ylabel": "GC fraction", "title": "GC% across sliding windows"},
        notes=["Merging is maximal-run (windows in a run fuse into one island); promoter prediction "
               "and genome-wide behaviour require the full genome, not this demo.",
               "O/E = count(CG)·len / (count(C)·count(G))."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 23 — Chaos Game Representation
# ─────────────────────────────────────────────────────────────────────────────
def cgr_plot(sequence: str = "ATGCGATCGGATCGATCGATCGATCGATCGATCG" * 4,
             max_points: int = 5000) -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s, MAX_SEQ_LEN)
    npts = min(len(s), max(500, min(int(max_points or 5000), 200_000)))
    corners = {"A": (0.0, 0.0), "T": (1.0, 0.0), "G": (1.0, 1.0), "C": (0.0, 1.0)}
    x, y = 0.5, 0.5
    xs, ys = [], []
    for ch in s[:npts]:
        cx, cy = corners[ch]
        x, y = (x + cx) / 2.0, (y + cy) / 2.0
        xs.append(round(x, 5))
        ys.append(round(y, 5))
    quad = [0, 0, 0, 0]
    for px, py in zip(xs, ys):
        q = (0 if py < 0.5 else 2) + (0 if px < 0.5 else 1)
        quad[q] += 1
    return out(
        title="Chaos Game Representation",
        summary=(f"Plotted {npts:,} of {len(s):,} bases; quadrant split (C/A/T/G): {quad[2]}·{quad[0]}·{quad[1]}·{quad[3]}."),
        metrics=[("Points", f"{npts:,}", None), ("Sequence", f"{len(s):,} bp", None),
                 ("Down-sampled", "yes" if npts < len(s) else "no", None)],
        rows=[{"Quadrant": qn, "Points": c} for qn, c in zip(("lower-left A", "lower-right T",
                                                               "upper-left C", "upper-right G"), quad)],
        columns=["Quadrant", "Points"],
        fig={"kind": "scatter", "x": xs, "y": ys, "title": "CGR", "xlabel": "", "ylabel": ""},
        notes=["CGR quadrants: A lower-left, T lower-right, G upper-right, C upper-left "
               "(standard convention); oligonucleotide families occupy nested squares."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 24 — DNA shape proxy (A-tract / TpA content; explicitly a proxy)
# ─────────────────────────────────────────────────────────────────────────────
def dna_shape_proxy(sequence: str = "AAAAATACAAAAATACGCTAGCTAGCGCGCGCAAAAATACAAAA",
                    window: int = 10) -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s, 200_000)
    w = max(5, min(int(window or 10), 50))
    if len(s) < w:
        raise ComputeError(f"Need at least {w} bp for a {w}-bp window.")
    rows = []
    for i in range(0, len(s) - w + 1):
        seg = s[i:i + w]
        atracts = sum(1 for j in range(len(seg) - 3) if seg[j:j + 4] in ("AAAA", "AAAT", "AATT", "TAAA", "TTAA"))
        tpa = sum(1 for j in range(len(seg) - 1) if seg[j:j + 2] == "TA")
        gc = 100.0 * (seg.count("G") + seg.count("C")) / w
        rigidity = round(100.0 * (seg.count("GC") + seg.count("CG")) / max(1, w - 1), 1)
        rows.append({"Start": i + 1, "Atract_4mers": atracts, "TpA_steps": tpa,
                     "GC_percent": round(gc, 1), "CpG_steps_percent": rigidity})
    top = sorted(rows, key=lambda r: (-r["Atract_4mers"], -r["TpA_steps"]))[:20]
    return out(
        title="DNA Shape PROXY (not DNAshape™)",
        summary=(f"{len(rows):,} windows scored for narrow-groove A-tract content and flexible "
                 "TpA steps. High A-tract windows are the classic curvature/flexibility proxies."),
        metrics=[("Windows", f"{len(rows):,}", None),
                 ("Max A-tract score", str(max(r['Atract_4mers'] for r in rows)), None),
                 ("Total TpA steps", str(s.count("TA")), None)],
        rows=top, columns=["Start", "Atract_4mers", "TpA_steps", "GC_percent", "CpG_steps_percent"],
        fig={"kind": "line", "x": [r["Start"] for r in rows[:2000]],
             "y": [r["Atract_4mers"] for r in rows[:2000]],
             "xlabel": "Window start", "ylabel": "A-tract 4-mers", "title": "A-tract density profile"},
        notes=["This is an explicitly SIMPLIFIED proxy (A-tract and TpA counting), not minor-groove "
               "width / propeller / roll from the Zhou-Rohs DNAshape model — do not cite as shape numbers."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 25 — VCF variant table
# ─────────────────────────────────────────────────────────────────────────────
def vcf_parse(text: str = """##fileformat=VCFv4.2
##FILTER=<ID=PASS,Description=\"All filters passed\">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t1017\trsid1\tA\tG\t100\tPASS\tDP=42
chr1\t2435\trsid2\tG\tC\t55\tPASS\tDP=13
chr1\t9999\trsid3\tAT\tA\t12\tLowQual\tDP=4""",
          min_qual: float = 0.0, chrom: str = "") -> Dict[str, Any]:
    raw = (text or "").replace("\r", "")
    if not raw.strip():
        raise ComputeError("Paste VCF content (##header, #CHROM line, then records).")
    guard_len(raw, MAX_PASTE, "pasted text")
    lines = raw.split("\n")
    header_i = None
    for i, l in enumerate(lines):
        if l.startswith("#CHROM"):
            header_i = i
            break
    if header_i is None:
        raise ComputeError("No #CHROM header line — is this a VCF?")
    cols = lines[header_i].lstrip("#").split("\t")
    need = {"CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO"}
    missing = need - set(cols)
    if missing:
        raise ComputeError(f"VCF header is missing required columns: {sorted(missing)}.")
    idx = {c: cols.index(c) for c in ["CHROM", "POS", "REF", "ALT", "QUAL", "INFO"]}
    purines = set("AG")
    rows, by_chrom = [], {}
    ti = tv = 0
    nrec = 0
    for l in lines[header_i + 1:]:
        if not l or l.startswith("#"):
            continue
        f = l.split("\t")
        if len(f) < 8:
            continue
        try:
            qual = float(f[idx["QUAL"]]) if f[idx["QUAL"]] != "." else 0.0
        except ValueError:
            qual = 0.0
        if qual < float(min_qual or 0):
            continue
        if chrom and f[idx["CHROM"]] != chrom:
            continue
        nrec += 1
        ref, alts = f[idx["REF"]], f[idx["ALT"]]
        by_chrom[f[idx["CHROM"]]] = by_chrom.get(f[idx["CHROM"]], 0) + 1
        typ = "SNV"
        ti_tv = ""
        if alts and "," not in alts and len(ref) == len(alts) == 1:
            typ = "SNV"
            if ref in purines == (alts in purines) or ref not in purines and alts not in purines:
                ti += 1
                ti_tv = "Ti"
            else:
                tv += 1
                ti_tv = "Tv"
        elif len(ref) != len(alts):
            typ = "indel"
        info = dict(kv.split("=", 1) if "=" in kv else (kv, "") for kv in f[idx["INFO"]].split(";"))
        rows.append({"CHROM": f[idx["CHROM"]], "POS": int(f[idx["POS"]]), "ID": f[cols.index("ID")],
                     "REF": ref, "ALT": alts, "QUAL": qual, "Type": typ, "Ti_Tv": ti_tv,
                     "DP": info.get("DP", "")})
        if len(rows) >= 2000:
            break
    if nrec == 0:
        raise ComputeError("Header parsed, but zero records passed the filters (check QUAL/chrom).")
    return out(
        title=f"VCF: {nrec:,} variant(s)",
        summary=(f"{nrec:,} records (showing ≤2000); {len(by_chrom)} contigs; "
                 f"{ti}/{tv} Ti/Tv across biallelic SNVs ({ti / max(1, ti + tv):.2f})."),
        metrics=[("Variants", f"{nrec:,}", None), ("Contigs", f"{len(by_chrom)}", None),
                 ("Ti/Tv (SNVs)", f"{ti / max(1, ti + tv):.2f}", "≈2 typical exome; ≈0.5 means random")],
        rows=rows, columns=["CHROM", "POS", "ID", "REF", "ALT", "QUAL", "Type", "Ti_Tv", "DP"],
        fig={"kind": "bar", "x": list(by_chrom.keys())[:40], "y": list(by_chrom.values())[:40],
             "xlabel": "Contig", "ylabel": "Variants", "title": "Variants per contig"},
        notes=["Multi-allelic and non-SNV records are typed but excluded from the Ti/Tv numerator.",
               "Full-file stats are computed before the display cap of 2000 rows."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 26 — Per-read / per-base quality (FASTQ text)
# ─────────────────────────────────────────────────────────────────────────────
def read_quality(text: str = """@read1
ATGCGATCGATCGCGGCGATCGAT
+
IIIIIIIIIIIIIIIIIIIIIIII
@read2
GGGCCCTTTAAATTTGGGCCCAAC
+
777777999999ABFFFFFFEEED""", trim_q: int = 20) -> Dict[str, Any]:
    raw = (text or "").replace("\r", "")
    lines = [l for l in raw.split("\n") if l.strip()]
    if not lines:
        raise ComputeError("Paste FASTQ records first.")
    guard_len(raw, MAX_PASTE, "pasted text")
    if len(lines) % 4:
        raise ComputeError("FASTQ needs 4 lines per record.")
    n = min(len(lines) // 4, MAX_RECORDS)
    q33 = min(40, max(2, int(trim_q or 20)))
    max_len = max(len(lines[4 * i + 1]) for i in range(n))
    base_good = [0] * max_len
    base_tot = [0] * max_len
    reads_low = 0
    mean_all = 0.0
    for i in range(n):
        seq, qual = lines[4 * i + 1], lines[4 * i + 3]
        qv = [max(0, min(93, ord(c) - 33)) for c in qual[:len(seq)]]
        mean_all += (sum(qv) / len(qv)) if qv else 0
        if qv and sum(qv) / len(qv) < q33:
            reads_low += 1
        for j, v in enumerate(qv):
            if j < max_len:
                base_tot[j] += 1
                base_good[j] += v >= q33
    prof = [round(100 * g / max(1, t), 1) for g, t in zip(base_good, base_tot)]
    worst = min(range(len(prof)), key=lambda i: prof[i]) if prof else 0
    return out(
        title=f"Quality Control: {n:,} reads",
        summary=(f"Mean quality Q{mean_all / max(1, n):.1f}; {reads_low:,} read(s) below mean Q{q33}; "
                 f"worst per-base position: {worst + 1} ({prof[worst]:.0f}% ≥ Q{q33})."),
        metrics=[("Reads", f"{n:,}", None), ("Mean Q", f"Q{mean_all / max(1, n):.1f}", None),
                 (f"Reads < Q{q33}", f"{reads_low:,}", None),
                 ("Read length", f"{max_len} bp", None)],
        rows=[{"Cycle": i + 1, "Percent_above_Q": p} for i, p in enumerate(prof[:250])],
        columns=["Cycle", "Percent_above_Q"],
        fig={"kind": "line", "x": list(range(1, len(prof) + 1)), "y": prof,
             "xlabel": "Cycle", "ylabel": f"% bases ≥ Q{q33}", "title": "Per-base quality profile"},
        notes=["Phred+33 assumed; Q≥20 (p(err) ≤ 1%) is the standard pass threshold, adjustable.",
               "Mean Q is the average of per-read means (reads are weighted equally, not per-base)."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 27 — GO term frequency counter (honest, non-statistical)
# ─────────────────────────────────────────────────────────────────────────────
def go_term_counter(term_list: str = "GO:0006915\nGO:0006915\nGO:0007046\nGO:0008150\nGO:0006915\nGO:0003674") -> Dict[str, Any]:
    import re
    raw = term_list or ""
    guard_len(raw, 500_000, "pasted text")
    found = re.findall(r"GO:\d{7}", raw.upper())
    if not found:
        raise ComputeError("No GO:####### accessions found in the text.")
    from collections import Counter
    counts = Counter(found)
    total = sum(counts.values())
    rows = [{"GO_term": g, "Occurrences": c, "Percent": round(100 * c / total, 1)}
            for g, c in counts.most_common(50)]
    return out(
        title="GO Term Frequency (counter, not enrichment)",
        summary=(f"{len(counts)} distinct terms over {total:,} mentions; most frequent "
                 f"{rows[0]['GO_term']} ({rows[0]['Percent']}%)."),
        metrics=[("Total mentions", f"{total:,}", None), ("Distinct terms", f"{len(counts)}", None),
                 ("Top term", rows[0]["GO_term"], None)],
        rows=rows, columns=["GO_term", "Occurrences", "Percent"],
        fig={"kind": "bar", "x": [r["GO_term"] for r in rows[:15]],
             "y": [r["Occurrences"] for r in rows[:15]], "xlabel": "GO term",
             "ylabel": "Occurrences", "title": "Term frequencies"},
        notes=["This is a frequency tally only — real GO enrichment (hypergeometric/Fisher with a "
               "genome background, e.g. QuickGO/g:Profiler) is NOT computed here."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 28 — Tandem repeat finder (periodicity scan)
# ─────────────────────────────────────────────────────────────────────────────
def tandem_repeats(sequence: str = "GATAGATAGATAGATAGATCTTGGCACAGATAGATAGATAGATAG" * 2,
                   min_period: int = 2, max_period: int = 20, min_copies: int = 5) -> Dict[str, Any]:
    import numpy as np
    s = prepare_dna(sequence)
    guard_len(s, MAX_SEQ_LEN)
    n = len(s)
    arr = np.frombuffer(s.encode("ascii"), dtype=np.uint8)
    lo = max(2, int(min_period or 2))
    hi = min(int(max_period or 20), max(2, n // max(1, int(min_copies or 5))))
    mc = max(2, int(min_copies or 5))
    found = []
    for p in range(lo, hi + 1):
        if n <= p:
            break
        eq = arr[:-p] == arr[p:]  # s[i] == s[i+p] for every offset
        idx = 0
        L = len(eq)
        while idx < L:
            if eq[idx]:
                j = idx
                while j + 1 < L and eq[j + 1]:
                    j += 1
                run = j - idx + 1
                if run >= (mc - 1) * p:
                    start = idx
                    end = idx + run + p
                    unit = s[start:start + p]
                    copies = (end - start) // p
                    found.append({"Start_1based": start + 1, "End_1based": end, "Period": p,
                                  "Unit": unit, "Copies": copies,
                                  "Span_bp": end - start})
                idx = j + 1
            else:
                idx += 1
    found.sort(key=lambda f: -f["Span_bp"])
    merged, used = [], set()
    for f in found:
        key = (f["Start_1based"], f["Period"])
        if key in used:
            continue
        used.add(key)
        if merged and f["Start_1based"] <= merged[-1]["End_1based"] and f["Period"] < merged[-1]["Period"]:
            continue
        merged.append(f)
    return out(
        title=f"Tandem repeats: {len(merged)} locus/loci",
        summary=(f"Periodicity scan (p={lo}–{hi}, ≥{mc} copies) over {n:,} bp found {len(merged)} "
                 + (f"repeats; largest {merged[0]['Copies']}× “{merged[0]['Unit']}” ({merged[0]['Span_bp']} bp)."
                    if merged else "no qualifying tandem repeats.")),
        metrics=[("Sequence", f"{n:,} bp", None), ("Repeats", f"{len(merged)}", None),
                 ("Periods tried", f"{lo}–{hi}", None)],
        rows=merged[:100] or [{"Start_1based": "—", "End_1based": "—", "Period": 0, "Unit": "—",
                               "Copies": 0, "Span_bp": 0}],
        columns=["Start_1based", "End_1based", "Period", "Unit", "Copies", "Span_bp"],
        fig=({"kind": "bar", "x": [f"p{f['Period']}@{f['Start_1based']}" for f in merged[:15]],
              "y": [f["Copies"] for f in merged[:15]], "xlabel": "Repeat", "ylabel": "Copies",
              "title": "Tandem repeat copy numbers"} if merged else None),
        notes=["A tandem repeat requires period-p self-similarity; interruptions split loci — "
               "TRF-style probabilistic scoring is NOT used."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 29 — GC skew (Ori/Cter heuristic)
# ─────────────────────────────────────────────────────────────────────────────
def gc_skew(sequence: str = "ATGCGCGCGCATATATATATATATATATGCATCGATCGATCGATCGATCG",
            window: int = 0) -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s, MAX_SEQ_LEN)
    n = len(s)
    w = int(window or 0)
    w = w if w >= 20 else max(20, n // 100 or 20)
    if n < w:
        w = n
    g = s.count("G")
    c = s.count("C")
    overall = (g - c) / max(1, g + c)
    starts = list(range(0, n - w + 1, max(1, w // 2)))
    skew_series = []
    for st in starts:
        seg = s[st:st + w]
        gs, cs = seg.count("G"), seg.count("C")
        skew_series.append({"start": st + 1, "skew": (gs - cs) / max(1, gs + cs)})
    cum = 0.0
    cumpts = []
    for d in skew_series:
        cum += d["skew"]
        cumpts.append({"start": d["start"], "cum": cum})
    if cumpts:
        mn = min(cumpts, key=lambda d: d["cum"])
        mx = max(cumpts, key=lambda d: d["cum"])
    else:
        mn = mx = {"start": 0, "cum": 0}
    return out(
        title="GC Skew Profile",
        summary=(f"Cumulative (G−C)/(G+C) over {w}-bp windows: minimum near {mn['start']:,} bp, "
                 f"maximum near {mx['start']:,} bp — on circular bacterial chromosomes the minimum "
                 "often marks oriC and the maximum terC (heuristic)."),
        metrics=[("Length", f"{n:,} bp", None), ("Overall skew", f"{overall:+.3f}", None),
                 ("Min cum (→ oriC?)", f"{mn['start']:,} bp", "heuristic"),
                 ("Max cum (→ terC?)", f"{mx['start']:,} bp", "heuristic")],
        rows=[{"Window_start": d["start"], "Skew": round(d["skew"], 4)} for d in skew_series[:2000]],
        columns=["Window_start", "Skew"],
        fig={"kind": "line", "x": [d["start"] for d in cumpts], "y": [round(d["cum"], 3) for d in cumpts],
             "xlabel": "Position (bp)", "ylabel": "Cumulative skew", "title": "Cumulative GC skew"},
        notes=["Cumulative-skew extrema are an approximate Ori/Cter heuristic for bacterial/organellar "
               "genomes; eukaryotic chromosomes show no such global pattern."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 30 — KEGG pathway lookup (curated offline subset)
# ─────────────────────────────────────────────────────────────────────────────
_KEGG_PATHWAYS = {
    "hsa00010": ("Glycolysis / Gluconeogenesis", "central carbon metabolism"),
    "hsa00020": ("Citrate cycle (TCA cycle)", "energy metabolism"),
    "hsa00190": ("Oxidative phosphorylation", "energy metabolism"),
    "hsa03010": ("Ribosome", "genetic information processing"),
    "hsa03030": ("DNA replication", "genetic information processing"),
    "hsa04110": ("Cell cycle", "human diseases / cancer"),
    "hsa04115": ("p53 signaling pathway", "human diseases / cancer"),
    "hsa04210": ("Apoptosis", "human diseases / neurodegenerative"),
    "hsa04010": ("MAPK signaling pathway", "signal transduction"),
    "hsa04012": ("ErbB signaling pathway", "signal transduction / cancer"),
    "hsa04014": ("Ras signaling pathway", "signal transduction"),
    "hsa04630": ("JAK-STAT signaling pathway", "signal transduction / immunology"),
    "hsa04151": ("PI3K-Akt signaling pathway", "signal transduction / cancer"),
    "hsa04060": ("Cytokine-cytokine receptor interaction", "immune system"),
    "hsa04930": ("Type II diabetes mellitus", "human diseases / endocrine"),
    "hsa00061": ("Fatty acid biosynthesis", "lipid metabolism"),
    "hsa00071": ("Fatty acid degradation", "lipid metabolism"),
    "hsa00520": ("Streptomycin biosynthesis", "biosynthesis of secondary metabolites"),
}
_KEGG_GENES = {
    "TP53": ["hsa04115", "hsa04110"], "MDM2": ["hsa04115"],
    "KRAS": ["hsa04014", "hsa04010"], "EGFR": ["hsa04012", "hsa04010"],
    "BRCA1": ["hsa03030", "hsa04110"], "PIK3CA": ["hsa04151"],
    "JAK2": ["hsa04630"], "STAT3": ["hsa04630"], "AKT1": ["hsa04151"],
    "MYC": ["hsa04110", "hsa04010"], "BAX": ["hsa04210", "hsa04115"],
    "CASP9": ["hsa04210"], "RAF1": ["hsa04010"], "BRAF": ["hsa04010", "hsa04014"],
    "CDKN2A": ["hsa04115", "hsa04110"],
}


def kegg_map(query: str = "TP53") -> Dict[str, Any]:
    q = (query or "").strip().upper()
    if not q:
        raise ComputeError("Enter a KEGG pathway ID (hsa######) or a gene symbol.")
    if q.startswith("HSA"):
        name, cat = _KEGG_PATHWAYS.get(q, (None, None))
        if not name:
            raise ComputeError(
                f"{q} is not in the offline subset ({len(_KEGG_PATHWAYS)} pathways). "
                "Live REST lookup is pending — see notes.")
        rows = [{"Query": q, "Pathway": name, "Category": cat,
                 "URL": f"https://www.kegg.jp/entry/{q}"}]
        fig = None
        summ = f"Pathway {q}: {name} [{cat}]."
    else:
        ids = _KEGG_GENES.get(q, [])
        if not ids:
            raise ComputeError(
                f"Gene “{q}” is not in the curated 15-gene offline map; this is a DEMO lookup, "
                "not the full KEGG database.")
        rows = [{"Query": q, "Pathway": _KEGG_PATHWAYS[i][0], "Category": _KEGG_PATHWAYS[i][1],
                 "URL": f"https://www.kegg.jp/entry/{i}"} for i in ids]
        summ = f"{q} mapped to {len(ids)} curated pathway(s)."
        fig = {"kind": "bar", "x": [r["Pathway"] for r in rows], "y": [1] * len(rows),
               "xlabel": "Pathway", "ylabel": "", "title": f"{q} — curated memberships"}
    return out(
        title=f"KEGG offline map: {q}",
        summary=summ,
        metrics=[("Genes covered", f"{len(_KEGG_GENES)}", "curated subset"),
                 ("Pathways covered", f"{len(_KEGG_PATHWAYS)}", "curated subset"),
                 ("Mode", "OFFLINE DEMO", "no network call is made by this tool")],
        rows=rows, columns=["Query", "Pathway", "Category", "URL"],
        fig=fig,
        notes=["Deliberately NOT a live API tool: membership is a tiny hand-curated set for teaching; "
               "absence from the list is NOT biological absence (check https://rest.kegg.jp/find/links)."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 31 — Advanced Tm (all methods + ΔG37)
# ─────────────────────────────────────────────────────────────────────────────
def advanced_tm(sequence: str = "ATGCGCTAGCTAGCTAGCTA", na_mm: float = 50.0,
                dnac_nm: float = 25.0, formamide_percent: float = 0.0) -> Dict[str, Any]:
    from ..thermo import nn_dH_dS, nn_tm, self_complementary, wallace_tm, gc_formula_tm
    s = prepare_dna(sequence)
    if len(s) > 1000:
        raise ComputeError("Advanced Tm covers oligos ≤ 1000 nt (NN model range here).")
    na = max(5.0, min(float(na_mm or 50), 1000.0))
    ct = max(0.1, min(float(dnac_nm or 25), 100000.0))
    fa = max(0.0, min(float(formamide_percent or 0), 50.0))
    sc = self_complementary(s)
    tm = nn_tm(s, Na_mm=na, dnac1_nm=ct, dnac2_nm=ct, selfcomp=sc)
    tm_fa = tm - 0.6 * fa
    wallace, wallace_ok = wallace_tm(s)
    gc_tm, gc_ok = gc_formula_tm(s, Na_mm=na)
    dH, dS = nn_dH_dS(s, selfcomp=sc, Na_mm=na)
    dg37 = dH - (310.15) * dS / 1000.0
    rows = [
        {"Method": "Nearest-neighbor (Allawi/SantaLucia via Biopython)", "Tm_C": round(tm, 2),
         "Valid_for_this_input": "yes", "Note": f"{'self-comp: k=Ct' if sc else 'non-self-comp: k=dnac1−dnac2/2'}; salt-corrected"},
        {"Method": f"Wallace 2+4 rule", "Tm_C": round(wallace, 2),
         "Valid_for_this_input": "yes" if wallace_ok else "NO — ≤14 nt only", "Note": "no salt term defined"},
        {"Method": "Marmur-Doty GC formula (long DNA)", "Tm_C": round(gc_tm, 2),
         "Valid_for_this_input": "yes" if gc_ok else "NO — >500 bp only", "Note": "salt term included at 1 M Na⁺ reference"},
        {"Method": "NN − 0.6°C·%formamide", "Tm_C": round(tm_fa, 2),
         "Valid_for_this_input": "yes" if fa else "skipped (no formamide)", "Note": f"{fa:.0f}% formamide"},
    ]
    return out(
        title=f"Tm {tm:.1f} °C (NN, {na:.0f} mM Na⁺, {ct:g} nM)",
        summary=(f"NN reference: {tm:.1f} °C; ΔH {dH:.1f} kcal/mol, ΔS {dS:.1f} cal/mol·K, "
                 f"ΔG37 {dg37:.1f} kcal/mol; {'self-complementary duplex' if sc else 'non-self-complementary'}."),
        metrics=[("Tm (NN)", f"{tm:.1f} °C", "the reference number — use this one"),
                 ("ΔH / ΔS", f"{dH:.1f} / {dS:.1f}", "kcal/mol and cal/(mol·K)"),
                 ("ΔG37", f"{dg37:.1f} kcal/mol", "duplex stability at 37 °C"),
                 ("Formamide-corrected", f"{tm_fa:.1f} °C" if fa else "n/a", None)],
        rows=rows, columns=["Method", "Tm_C", "Valid_for_this_input", "Note"],
        notes=["Each method states its own applicability — simple rules are shown to COMPARE, not to choose freely.",
               "Salt model: Biopython method 5 (Na⁺/K⁺/Tris/Mg²⁺/dNTP effective monovalent)."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 32 — Bulk reverse complement
# ─────────────────────────────────────────────────────────────────────────────
def bulk_revcomp_tool(text: str = "ATGCGATCG\nGGGAAACCCTTT\nACGTACGT") -> Dict[str, Any]:
    raw = (text or "").replace("\r", "")
    if not raw.strip():
        raise ComputeError("Enter sequences one-per-line (or multi-FASTA).")
    guard_len(raw, MAX_PASTE, "text")
    lines = raw.split("\n")
    if any(l.startswith(">") for l in lines):
        names, seqs = [], []
        for l in lines:
            if l.startswith(">"):
                names.append(l[1:].strip().split(maxsplit=1)[0] if len(l) > 1 else f"rec{len(names) + 1}")
                seqs.append("")
            elif l.strip() and seqs:
                seqs[-1] += l.strip()
        items = list(zip(names, seqs))
    else:
        items = [(f"line_{i + 1}", l.strip()) for i, l in enumerate(lines) if l.strip()]
    rows, fasta_out = [], []
    ok = err = 0
    for name, seq in items:
        up = seq.upper()
        if up and all(c in "ACGTNURYSWKMBDHVN.-" for c in up):
            rc = revcomp(up.replace("U", "T"))
            rows.append({"ID": name, "Length": len(up), "Status": "ok", "RevComp": rc[:60] + ("…" if len(rc) > 60 else "")})
            fasta_out.append(f">{name}_rc\n{rc}")
            ok += 1
        else:
            rows.append({"ID": name, "Length": len(up), "Status": "invalid characters", "RevComp": "—"})
            err += 1
    if not rows:
        raise ComputeError("Nothing to process.")
    return out(
        title=f"Bulk reverse complement ({ok} ok / {err} skipped)",
        summary=(f"{ok:,} sequences reverse-complemented, {err:,} skipped for invalid characters."
                 + (f" ({len(items)} FASTA records)" if any(l.startswith('>') for l in lines) else "")),
        metrics=[("Processed", f"{ok:,}", None), ("Skipped", f"{err:,}", None),
                 ("Total input", f"{len(items):,}", None)],
        rows=rows[:500], columns=["ID", "Length", "Status", "RevComp"],
        notes=["IUPAC ambiguity codes are complemented per the standard table (R→Y, W→W, S→S, …)."],
        fasta="\n".join(fasta_out[:500]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 33 — Random DNA generator (seeded, reproducible)
# ─────────────────────────────────────────────────────────────────────────────
def random_generator(length: int = 200, gc_percent: float = 50.0, seed: int = 42,
                     alphabet: str = "DNA") -> Dict[str, Any]:
    import random as _r
    L = max(10, min(int(length or 200), 200_000))
    gc = max(0.0, min(float(gc_percent or 50), 100.0))
    alpha = "ATCG" if not (alphabet or "").upper().startswith("RNA") else "AUCG"
    g1 = gc / 200.0
    a1 = (1.0 - gc / 100.0) / 2.0
    weights = [a1, a1, g1, g1]
    rng = _r.Random(seed if seed is not None else _r.randrange(2 ** 31))
    total_w = sum(weights) or 1.0
    weights = [w / total_w for w in weights]
    seq = "".join(rng.choices(alpha, weights=weights, k=L))
    counts = {c: seq.count(c) for c in alpha}
    actual_gc = 100.0 * (counts[alpha[2]] + counts[alpha[3]]) / L
    homopol = max((len(run) for run in _runs(seq)), default=1)
    return out(
        title=f"Random {alphabet or 'DNA'} ({L:,} nt, seed {seed})",
        summary=(f"Generated {L:,} nt; requested {gc:.1f}% GC, achieved {actual_gc:.1f}%; "
                 f"longest homopolymer {homopol} nt. Reproducible with the same seed."),
        metrics=[("Length", f"{L:,} nt", None), ("Target/actual GC", f"{gc:.0f}% / {actual_gc:.1f}%", None),
                 ("Seed", str(seed), "same seed ⇒ same sequence"), ("Max homopolymer", f"{homopol} nt", None)],
        rows=[{"Base": b, "Count": counts[b], "Percent": round(100 * counts[b] / L, 2)} for b in alpha],
        columns=["Base", "Count", "Percent"],
        fig={"kind": "bar", "x": list(alpha), "y": [counts[b] for b in alpha],
             "xlabel": "Base", "ylabel": "Count", "title": "Generated composition"},
        notes=["i.i.d. sampling per position — no dinucleotide structure (CpG etc. follow by chance); "
               "use Markov models for genome-like statistics.",
               f"Sequence (first 240 nt): {seq[:240]}"],
        fasta=f">random_{L}bp_seed{seed}\n{seq}",
    )


def _runs(s: str):
    if not s:
        return
    cur, n = s[0], 1
    for c in s[1:]:
        if c == cur:
            n += 1
        else:
            yield n * cur
            cur, n = c, 1
    yield n * cur


GENOMICS_TOOLS = {
    18: file_qc,
    19: kmer_frequency,
    20: ngrams_analysis,
    21: primer_design,
    22: cpg_islands,
    23: cgr_plot,
    24: dna_shape_proxy,
    25: vcf_parse,
    26: read_quality,
    27: go_term_counter,
    28: tandem_repeats,
    29: gc_skew,
    30: kegg_map,
    31: advanced_tm,
    32: bulk_revcomp_tool,
    33: random_generator,
}
