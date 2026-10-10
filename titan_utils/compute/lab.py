"""Compute functions for Titan tools 45–52 (lab & pipeline)."""
from __future__ import annotations

from typing import Any, Dict, List

from ..sequence import CODON_TABLE_STANDARD, revcomp
from . import ComputeError, guard_len, out, prepare_dna, prepare_protein

# ─────────────────────────────────────────────────────────────────────────────
# Tool 45 — CRISPR gRNA designer (PAM scan, both strands, honest scores)
# ─────────────────────────────────────────────────────────────────────────────
_PAM_CONFIGS = {
    "SpCas9": {"pam": "NGG", "side": "3prime", "guide": 20},
    "SaCas9": {"pam": "NNGRRT", "side": "3prime", "guide": 21},
    "Cas12a (Cpf1)": {"pam": "TTTV", "side": "5prime", "guide": 23},
}
_IUPAC = {"A": "A", "C": "C", "G": "G", "T": "T", "N": "[ACGT]", "R": "[AG]", "Y": "[CT]", "V": "[ACG]"}


def crispr_design(sequence: str = "ATGCGTAGTCTAGCTAGCTAGGAATGCCCTACGTTACGCAGTTTGGCAAGGTCA",
                  nuclease: str = "SpCas9", gc_min: float = 40.0, gc_max: float = 60.0,
                  strand: str = "both strands") -> Dict[str, Any]:
    import re
    s = prepare_dna(sequence)
    guard_len(s, 60_000)
    cfg = _PAM_CONFIGS.get((nuclease or "SpCas9").strip())
    if cfg is None:
        raise ComputeError(f"Unsupported nuclease. Choose: {', '.join(_PAM_CONFIGS)}.")
    pam_rx = re.compile("".join(_IUPAC[c] for c in cfg["pam"]))
    g, side = cfg["guide"], cfg["side"]
    need = g + len(cfg["pam"])
    if len(s) < need:
        raise ComputeError(f"Need ≥{need} bp for {nuclease} ({g} nt guide + PAM).")
    rows: List[Dict[str, Any]] = []
    seen = set()
    strands = [("+", s)]
    if (strand or "").lower().startswith("both"):
        strands.append(("−", revcomp(s)))
    for name, seq in strands:
        for pos in range(0, len(seq) - need + 1):
            window = seq[pos:pos + need]
            if side == "3prime":
                guide, pam = window[:g], window[g:]
            else:
                pam, guide = window[:len(cfg["pam"])], window[len(cfg["pam"]):]
            if not pam_rx.fullmatch(pam):
                continue
            if guide in seen:
                continue
            seen.add(guide)
            gc = 100.0 * (guide.count("G") + guide.count("C")) / g
            poly_t = 4 if guide.count("TTTT") else 0
            if not (float(gc_min or 40) <= gc <= float(gc_max or 60)):
                continue
            score = 100.0
            score -= abs(55 - gc) * 1.2                      # GC balance heuristic
            score -= 25.0 * poly_t                            # pol III terminator
            score = max(0.0, min(100.0, score))
            rows.append({"Strand": name, "Position_1based": pos + 1, "gRNA_DNA": guide,
                         "gRNA_RNA": guide.replace("T", "U"), "PAM": pam, "GC_%": round(gc, 1),
                         "Poly_T_4mer": "yes" if poly_t else "no", "Score": round(score, 1)})
    rows.sort(key=lambda r: -r["Score"])
    return out(
        title=f"{nuclease}: {len(rows)} candidate guide(s)",
        summary=(f"{len(rows):,} guide(s) with PAM {cfg['pam']} ({side}) pass GC {gc_min:.0f}–{gc_max:.0f}% "
                 f"in {len(s):,} bp (unique guides). Score = GC balance − poly-T penalty only."),
        metrics=[("Candidates", f"{len(rows):,}", None), ("PAM", cfg["pam"], None),
                 ("Best score", f"{rows[0]['Score']:.0f}" if rows else "—", None),
                 ("Off-target", "NOT CHECKED", "requires a genome — see notes")],
        rows=rows[:250], columns=["Strand", "Position_1based", "gRNA_DNA", "PAM", "GC_%", "Poly_T_4mer", "Score"],
        fig=({"kind": "scatter", "x": [r["GC_%"] for r in rows[:300]], "y": [r["Score"] for r in rows[:300]],
              "title": "gRNA GC% vs heuristic score", "xlabel": "GC %", "ylabel": "Score"} if rows else None),
        notes=["Educational screen: PAM match + GC window + poly-T flag. NO Doench/Azimuth efficiency model "
               "and NO genome-wide off-target search — never use for experiments without a real designer.",
               "Duplicate guide sequences (same spacer elsewhere) are reported once; count hits in the FASTA input for multiplicity."],
        fasta="".join(f">g{i+1}_{r['Strand']}_{r['Position_1based']}\n{r['gRNA_DNA']}\n"
                      for i, r in enumerate(rows[:50])),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 46 — PCR product length from primer pair on a template
# ─────────────────────────────────────────────────────────────────────────────
def pcr_product(template: str = "TTAGGATCCATGGCTAAAGGGCCCTTTGGGCCCATAGCTATGCATGCCCTAGGGGATCC",
                forward_primer: str = "ATGGCTAAAGGGCCC",
                reverse_primer: str = "CTAGGGCATGCAT",
                max_mismatches: int = 0) -> Dict[str, Any]:
    from Bio.Seq import Seq
    t = prepare_dna(template)
    f = prepare_dna(forward_primer)
    r = prepare_dna(reverse_primer)
    guard_len(t, 200_000, "template")
    for nm, p in (("forward", f), ("reverse", r)):
        if len(p) < 8:
            raise ComputeError(f"{nm} primer shorter than 8 nt — extend it.")
        if len(p) > 60:
            raise ComputeError(f"{nm} primer longer than 60 nt — this tool is for oligos.")
    mm = max(0, min(int(max_mismatches or 0), 3))
    rc = str(Seq(r).reverse_complement())

    def find_all(pat: str):
        out_pos = []
        if mm == 0:
            idx = t.find(pat, 0)
            while idx != -1:
                out_pos.append(idx)
                idx = t.find(pat, idx + 1)
            return out_pos
        Lp = len(pat)
        for i in range(len(t) - Lp + 1):
            d = sum(1 for a, b in zip(t[i:i + Lp], pat) if a != b)
            if d <= mm:
                out_pos.append((i, d))
        return out_pos

    fpos = find_all(f)
    rpos = find_all(rc)
    if not fpos or not rpos:
        missing = []
        if not fpos:
            missing.append("forward")
        if not rpos:
            missing.append("reverse (as its reverse-complement on the template)")
        raise ComputeError(f"{', '.join(missing)} binding site not found on the template "
                           f"(≤{mm} mismatch(es) allowed). Exact-match mode works for clean primers.")
    pairs = []
    for fe in fpos:
        fstart, fd = (fe[0], fe[1]) if isinstance(fe, tuple) else (fe, 0)
        for re_ in rpos:
            rstart, rd = (re_[0], re_[1]) if isinstance(re_, tuple) else (re_, 0)
            rend = rstart + len(rc)
            if rend > fstart and rend - fstart <= 20000:
                amp = t[fstart:rend]
                pairs.append({"Forward_start": fstart + 1, "Reverse_end": rend,
                              "Product_bp": len(amp),
                              "Product_GC_%": round(100 * (amp.count("G") + amp.count("C")) / len(amp), 1),
                              "Mismatches": fd + rd})
    pairs.sort(key=lambda p: (p["Mismatches"], p["Product_bp"]))
    if not pairs:
        raise ComputeError("Both primers bind but no primer pair faces each other (forward must precede the reverse site).")
    best = pairs[0]
    try:
        from ..thermo import nn_tm
        prod_tm = round(nn_tm(t[best["Forward_start"] - 1:best["Forward_start"] - 1 + min(40, best["Product_bp"])]), 1)
    except Exception:
        prod_tm = None
    return out(
        title=f"Amplicon {best['Product_bp']} bp",
        summary=(f"Forward at {best['Forward_start']:,}, reverse-complement site ends at {best['Reverse_end']:,}; "
                 f"product {best['Product_bp']:,} bp ({best['Product_GC_%']}% GC, {best['Mismatches']} mismatch(es))."),
        metrics=[("Product length", f"{best['Product_bp']:,} bp", None),
                 ("Product GC%", f"{best['Product_GC_%']}%", None),
                 ("Candidate pairs", f"{len(pairs):,}", None),
                 ("Start-region Tm", f"{prod_tm} °C" if prod_tm else "n/a", "NN Tm of amplicon's first ≤40 bp")],
        rows=pairs[:50], columns=["Forward_start", "Reverse_end", "Product_bp", "Product_GC_%", "Mismatches"],
        notes=["Annealing/extension modelling is out of scope; this is site geometry + basic amplicon stats.",
               "Reverse primer matched as its reverse complement on the template (standard convention)."],
        fasta=f">amplicon_{best['Product_bp']}bp\n{t[best['Forward_start'] - 1:best['Reverse_end']]}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 47 — Oligo Tm list + suggested annealing temperature
# ─────────────────────────────────────────────────────────────────────────────
def oligo_tms(oligos: str = "ATGGCTAAAGGGCCC\nTTTGGGCCCATAGCTATG\nCCTTAGGGAAACCC",
              method: str = "NN (nearest-neighbor)") -> Dict[str, Any]:
    from ..thermo import nn_tm, wallace_tm, ThermoError
    raw = (oligos or "").replace("\r", "")
    seqs = ["".join(l.upper().split()) for l in raw.split("\n") if l.strip()
            and not l.strip().startswith(">")]
    if not seqs:
        raise ComputeError("Enter one oligo per line.")
    if len(seqs) > 200:
        raise ComputeError("Cap: 200 oligos per run — chunk longer lists.")
    rows = []
    for i, s in enumerate(seqs, 1):
        if any(c not in "ATCG" for c in s):
            raise ComputeError(f"Oligo {i} contains non-DNA letters: {sorted(set(s) - set('ATCG'))}")
        if len(s) < 4:
            raise ComputeError(f"Oligo {i} too short (<4 nt).")
        try:
            tm = nn_tm(s)
        except ThermoError:
            tm = None
        w, w_ok = wallace_tm(s)
        chosen = tm if method.lower().startswith("nn") else w
        gc = 100.0 * (s.count("G") + s.count("C")) / len(s)
        rows.append({"Oligo_#": i, "Length": len(s), "GC_%": round(gc, 1),
                     "Tm_C": round(chosen, 1) if chosen is not None else "n/a",
                     "Wallace_C": round(w, 1), "Wallace_valid": "yes" if w_ok else "no (>14 nt)"})
    tms = [r["Tm_C"] for r in rows if isinstance(r["Tm_C"], float)]
    ta = round(min(tms) - 5.0, 1) if tms else None
    return out(
        title=f"Oligo Tm table ({len(rows)} oligos)",
        summary=(f"{method}: Tm values computed for {len(rows)} oligos; suggested annealing "
                 f"≈ {ta} °C (min Tm − 5 °C)." if ta is not None else "computed; too short for Ta advice."),
        metrics=[("Oligos", f"{len(rows)}", None),
                 ("Lowest Tm", f"{min(tms):.1f} °C" if tms else "n/a", None),
                 ("Suggested Ta", f"{ta} °C" if ta else "n/a", "min(Tm) − 5 °C heuristic"),
                 ("ΔTm spread", f"{(max(tms) - min(tms)):.1f} °C" if tms else "n/a",
                  "pairs more than ~5 °C apart will bias PCR")],
        rows=rows, columns=["Oligo_#", "Length", "GC_%", "Tm_C", "Wallace_C", "Wallace_valid"],
        fig={"kind": "bar", "x": [f"#{r['Oligo_#']}" for r in rows[:60]],
             "y": [r["Tm_C"] if isinstance(r["Tm_C"], float) else 0 for r in rows[:60]],
             "xlabel": "Oligo", "ylabel": "Tm (°C)", "title": "Tm per oligo"},
        notes=["Ta suggestion is the classic min−5 rule; gradient PCR remains the gold standard.",
               "Wallace column shown for comparison; flagged invalid above 14 nt."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 48 — DNA melting curve simulation (two-state from validated NN params)
# ─────────────────────────────────────────────────────────────────────────────
def melting_curve(sequence: str = "ATGGCTAAAGGGCCCTTTGGGCCCATAG",
                  na_mm: float = 50.0, dnac_nm: float = 25.0) -> Dict[str, Any]:
    from ..thermo import (ThermoError, fraction_bound, melting_curve as mc,
                          nn_dH_dS, nn_tm, self_complementary)
    s = prepare_dna(sequence)
    if len(s) > 120:
        raise ComputeError("Melting-curve simulation is capped at 120 nt (two-state model of a single duplex).")
    try:
        sc = self_complementary(s)
        dH, dS = nn_dH_dS(s, selfcomp=sc, Na_mm=float(na_mm or 50))
        tm = nn_tm(s, Na_mm=float(na_mm or 50), dnac1_nm=float(dnac_nm or 25),
                   dnac2_nm=float(dnac_nm or 25), selfcomp=sc)
    except ThermoError as e:
        raise ComputeError(str(e))
    temps, bounds = mc(s, temp_min_c=5.0, temp_max_c=99.0, points=120,
                       Na_mm=float(na_mm or 50),
                       dnac1_nm=float(dnac_nm or 25), dnac2_nm=float(dnac_nm or 25),
                       selfcomp=sc)
    mid = temps[max(range(len(bounds)), key=lambda i: -abs(bounds[i] - 0.5))]
    return out(
        title=f"Two-state melting curve (Tm ≈ {tm:.1f} °C)",
        summary=(f"ΔH {dH:.1f} kcal/mol, ΔS {dS:.1f} cal/mol·K → sigmoid centred at "
                 f"{tm:.1f} °C; cooperative transition (no intermediates modelled)."),
        metrics=[("Tm (NN analytic)", f"{tm:.1f} °C", "reference value"),
                 ("ΔH duplex", f"{dH:.1f} kcal/mol", None),
                 ("Cooperativity", "two-state (θ jumps 1→0)", "no bulge/intermediate states")],
        rows=[{"Temp_C": round(t, 1), "Fraction_bound": round(b, 4)} for t, b in zip(temps, bounds)],
        columns=["Temp_C", "Fraction_bound"],
        fig={"kind": "line", "x": [round(t, 1) for t in temps], "y": [round(b, 4) for b in bounds],
             "xlabel": "Temperature (°C)", "ylabel": "Fraction duplex", "title": f"Melting curve (Tm {tm:.1f} °C)"},
        notes=["ΔG(T) = ΔH − T·ΔS with ΔCp = 0 (documented simplification); same NN tables as the "
               "Tm calculator, so the curve midpoint equals the analytic Tm (unit-tested).",
               f"Coarse-grid display midpoint near {round(mid, 1)} °C; analytic Tm is the accurate one."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 49 — Indel detection (real alignment diff)
# ─────────────────────────────────────────────────────────────────────────────
def indel_detect(reference: str = "ATGGCTAAAGGGCCCTTTAAAGGGCCC",
                 sample: str = "ATGGCTAAAGGGCCCCTTTAAAGGGCCC") -> Dict[str, Any]:
    from Bio import Align
    a_raw_in = "".join((reference or "").upper().split())
    b_raw_in = "".join((sample or "").upper().split())
    guard_len(a_raw_in, 100_000, "reference")
    guard_len(b_raw_in, 100_000, "sample")
    b_has_gaps = "-" in a_raw_in or "." in a_raw_in or "-" in b_raw_in or "." in b_raw_in
    if b_has_gaps:  # pre-aligned input with explicit gaps on either row
        a = "".join(ch if ch in "ATCG" else "-" for ch in a_raw_in)
        bb = "".join(ch if ch in "ATCG" else "-" for ch in b_raw_in)
        if len(a) != len(bb):
            raise ComputeError("With pre-gapped input both rows must have equal length "
                               f"(got {len(a)} vs {len(bb)}); paste both rows of the same alignment.")
        b = bb
    else:
        a = prepare_dna(a_raw_in)
        b = prepare_dna(b_raw_in)
    rows = []
    if b_has_gaps:
        i = 0
        while i < len(bb):
            if bb[i] == "-":
                j = i
                while j < len(bb) and bb[j] == "-":
                    j += 1
                rows.append({"Type": "deletion in sample", "Ref_position": i + 1,
                             "Length": j - i, "Sequence": a[i:j]})
                i = j
            elif a[i] == "-":
                j = i
                while j < len(bb) and a[j] == "-":
                    j += 1
                rows.append({"Type": "insertion in sample", "Ref_position": i,
                             "Length": j - i, "Sequence": bb[i:j]})
                i = j
            else:
                i += 1
    elif len(a) == len(b):
        d = sum(1 for x, y in zip(a, b) if x != y)
        return out(
            title="Indel detection — equal lengths",
            summary=(f"Both sequences are {len(a):,} bp with {d} substitution(s): no length-changing "
                     "event to call. Use the alignment pages for full substitution tables."),
            metrics=[("Length", f"{len(a):,} bp", None), ("Substitutions", str(d), None),
                     ("Indels", "0 (same length)", None)],
            rows=[{"Type": "substitutions only", "Ref_position": "—", "Length": d, "Sequence": "—"}],
            columns=["Type", "Ref_position", "Length", "Sequence"],
            notes=["Indels change length; a same-length pair can only contain substitutions or equal-size exchanges."],
        )
    else:
        al = Align.PairwiseAligner()
        al.mode = "global"
        al.match_score, al.mismatch_score = 2.0, -4.0
        al.open_gap_score, al.extend_gap_score = -6.0, -0.5
        from . import free_end_gaps
        free_end_gaps(al)
        best = al.align(a, b)[0]
        ga, gb = str(best[0]), str(best[1])
        ref_pos = 0
        i = 0
        while i < len(ga):
            if ga[i] == "-":
                j = i
                while j < len(ga) and ga[j] == "-":
                    j += 1
                rows.append({"Type": "insertion in sample", "Ref_position": ref_pos,
                             "Length": j - i, "Sequence": gb[i:j]})
                i = j
            elif gb[i] == "-":
                j = i
                while j < len(gb) and gb[j] == "-":
                    j += 1
                rows.append({"Type": "deletion in sample", "Ref_position": i + 1,
                             "Length": j - i, "Sequence": a[i:j]})
                ref_pos += j - i
                i = j
            else:
                ref_pos += 1
                i += 1
    ins = sum(1 for r in rows if r["Type"].startswith("insertion"))
    dels = sum(1 for r in rows if r["Type"].startswith("deletion"))
    return out(
        title=f"Indels: {ins} ins / {dels} del",
        summary=(f"Found {len(rows)} indel event(s) via {'explicit alignment gaps' if b_has_gaps else 'global alignment diff'}; "
                 f"total {sum(r['Length'] for r in rows):,} bp changed."),
        metrics=[("Insertions", str(ins), None), ("Deletions", str(dels), None),
                 ("Total bases", f"{sum(r['Length'] for r in rows):,}", None)],
        rows=rows[:500] or [{"Type": "no indels", "Ref_position": "—", "Length": 0, "Sequence": "—"}],
        columns=["Type", "Ref_position", "Length", "Sequence"],
        notes=["Events larger than ~10 bp at read ends may be alignment artefacts, not biology."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 50 — BLAST-style seed & extend (educational simulator)
# ─────────────────────────────────────────────────────────────────────────────
def blast_local(query: str = "ATGCGTACG", subject: str = "CCATGCGTACGTTTAGCGATGCGTACGAA",
                word_size: int = 3, match_score: float = 2.0, mismatch_score: float = -1.0) -> Dict[str, Any]:
    q = prepare_dna(query)
    s = prepare_dna(subject)
    guard_len(q, 5_000)
    guard_len(s, 200_000)
    k = max(2, min(int(word_size or 3), 8))
    if len(q) < k:
        raise ComputeError(f"Query shorter than word size {k}.")
    m, mm = float(match_score), float(mismatch_score)
    hsps: List[Dict[str, Any]] = []
    # index subject words
    from collections import defaultdict
    idx: Dict[str, List[int]] = defaultdict(list)
    for j in range(len(s) - k + 1):
        idx[s[j:j + k]].append(j)
    n_seeds = 0
    for i in range(len(q) - k + 1):
        for j in idx.get(q[i:i + k], []):
            n_seeds += 1
            qi, si = i, j
            while qi > 0 and si > 0 and q[qi - 1] == s[si - 1]:
                qi, si = qi - 1, si - 1
            qe, se = i + k, j + k
            while qe < len(q) and se < len(s) and q[qe] == s[se]:
                qe, se = qe + 1, se + 1
            alnq, alns = q[qi:qe], s[si:se]
            score = sum(m if x == y else mm for x, y in zip(alnq, alns))
            if score > 0:
                hsps.append({"Query_start": qi + 1, "Query_end": qe, "Subject_start": si + 1,
                             "Subject_end": se, "Score": round(score, 1), "Length_bp": qe - qi,
                             "Identity_%": round(100.0 * sum(1 for x, y in zip(alnq, alns) if x == y) / (qe - qi), 1),
                             "Alignment": f"{alnq}\n{alns}"})
    hsps.sort(key=lambda h: -h["Score"])
    dedup, used = [], set()
    for h in hsps:
        key = (h["Query_start"], h["Query_end"], h["Subject_start"])
        if key in used:
            continue
        used.add(key)
        dedup.append(h)
    return out(
        title=f"Seed-&-extend: {len(dedup)} HSP(s)",
        summary=(f"{len(q):,}-bp query vs {len(s):,}-bp subject, exact {k}-mer seeds, ungapped extension; "
                 f"{n_seeds:,} seed hits, {len(dedup)} HSP(s) after dedup."),
        metrics=[("Word size", str(k), None), ("Seeds tried", f"{n_seeds:,}", None),
                 ("HSPs", f"{len(dedup)}", None),
                 ("Best identity", f"{dedup[0]['Identity_%']}%" if dedup else "—", None)],
        rows=[{kk: v for kk, v in h.items() if kk != "Alignment"} for h in dedup[:100]],
        columns=["Score", "Identity_%", "Length_bp", "Query_start", "Query_end", "Subject_start", "Subject_end"],
        fig=({"kind": "bar", "x": [f"HSP{i+1}" for i in range(min(10, len(dedup)))],
              "y": [h["Score"] for h in dedup[:10]], "xlabel": "HSP", "ylabel": "Score",
              "title": "Top HSP scores"} if dedup else None),
        notes=["This is a SIMULATOR for teaching BLAST mechanics: exact seeds, ungapped extension, no "
               "substitution matrix, no database search, no E-value. Real BLAST statistics "
               "(Karlin-Altschul) need proper scoring + DB size — compare against NCBI results before trusting.",
               "Subject is a single sequence here, so 'database size' = its length."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 51 — Full pipeline dashboard (one CDS in → everything out)
# ─────────────────────────────────────────────────────────────────────────────
def pipeline_dashboard(sequence: str = "ATGGCTAAAGGGCCCTTTGGGCCCATAGTAA") -> Dict[str, Any]:
    from Bio.Seq import Seq
    from ..sequence import gc_fraction_safe
    from ..thermo import nn_tm
    s = prepare_dna(sequence)
    guard_len(s, 60_000)
    gc = 100.0 * gc_fraction_safe(s)
    coding = len(s) - (len(s) % 3)
    prot = str(Seq(s[:coding]).translate()) if coding >= 3 else ""
    prot_clean = prot.replace("*", "")
    tm = nn_tm(s) if len(s) <= 1000 else None
    rows = [{"Step": "Input length", "Value": f"{len(s):,} bp"},
            {"Step": "GC content", "Value": f"{gc:.2f}%"}]
    if tm is not None:
        rows.append({"Step": "Tm (NN)", "Value": f"{tm:.1f} °C"})
    rows.append({"Step": "Translation", "Value": f"{len(prot)} aa ({prot.count('*')} stop(s))"})
    if prot_clean:
        from Bio.SeqUtils.ProtParam import ProteinAnalysis
        pa = ProteinAnalysis(prot_clean)
        rows.append({"Step": "Protein MW", "Value": f"{pa.molecular_weight():,.0f} Da"})
        rows.append({"Step": "Protein pI", "Value": f"{pa.isoelectric_point():.2f}"})
        rows.append({"Step": "GRAVY", "Value": f"{pa.gravy():+.3f}"})
    from .basic import orf_find
    orfs = orf_find(s, min_length_aa=8)
    return out(
        title="Pipeline dashboard",
        summary=(f"{len(s):,} bp → {len(prot)} aa · {gc:.1f}% GC · longest ORF "
                 + (f"{orfs['metrics'][2][1]}." if orfs.get("metrics") else "n/a.")),
        metrics=[(r["Step"], r["Value"], None) for r in rows],
        rows=rows, columns=["Step", "Value"],
        notes=["Every metric here is computed by the same functions the individual tools use "
               "(single source of truth across the suite).",
               "Assumes an in-frame CDS starting at position 1; stops shown as *."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 52 — Codon optimization (reference-derived weights, round-trip verified)
# ─────────────────────────────────────────────────────────────────────────────
def codon_optimize(protein_sequence: str = "MKVLWAALLVTFLAGCQAKVEQAVETEPEPELRQQ",
                   reference_cds: str = "", strategy: str = "reference-optimized") -> Dict[str, Any]:
    from collections import Counter
    from Bio.Seq import Seq
    p = prepare_protein(protein_sequence)
    guard_len(p, 10_000)
    if p.endswith("*"):
        p = p[:-1]
    ref = (reference_cds or "").strip()
    weights: Dict[str, Dict[str, int]] = {}
    mode = "balanced (GC≈50%, avoid long homopolymers)"
    if ref:
        cds = prepare_dna(ref)
        if len(cds) < 30:
            raise ComputeError("Reference CDS too short (<30 bp) to estimate codon weights.")
        guard_len(cds, 500_000)
        cnt: Dict[str, Counter] = {}
        for i in range(0, len(cds) - 2, 3):
            c = cds[i:i + 3]
            aa = CODON_TABLE_STANDARD.get(c)
            if aa and aa != "*":
                cnt.setdefault(aa, Counter())[c] += 1
        weights = cnt
        mode = "reference-optimized (uses codon counts from your reference CDS)"
    out_codons = []
    for aa in p:
        family = [c for c, a in CODON_TABLE_STANDARD.items() if a == aa]
        if not family:
            raise ComputeError(f"No codons for {aa!r}.")
        if aa == "M" or aa == "W":
            out_codons.append(family[0])
            continue
        if weights and aa in weights and sum(weights[aa].values()) > 0:
            w = weights[aa]
            total = sum(w.values())
            # deterministic argmax on usage with GC tie-break
            best = max(sorted(w.keys(), key=lambda c: c), key=lambda c: (w.get(c, 0), -(abs(_cgc(c) - 0.5))))
            out_codons.append(best)
            continue
        # balanced: prefer codon minimizing |GC-0.5| after concatenation, break by lex
        best, bestv = None, None
        prev = out_codons[-1] if out_codons else ""
        for c in sorted(family):
            ctx = (prev[-2:] + c) if prev else c
            longest = _max_run(ctx)
            score = abs(_cgc(c) - 0.5) * 10 + longest * 2.0
            if bestv is None or score < bestv:
                best, bestv = c, score
        out_codons.append(best)
    dna = "".join(out_codons) + "TAA"
    back = str(Seq(dna).translate())
    if back != p + "*":
        raise ComputeError("Round-trip verification failed — optimized DNA does not translate back to the input. Report this.")
    gc = 100.0 * (dna.count("G") + dna.count("C")) / len(dna)
    return out(
        title=f"Codon-optimized DNA ({len(p)} aa, verified)",
        summary=(f"{len(p):,} aa → {len(dna):,} nt via {mode}; translation round-trip verified identical; "
                 f"GC {gc:.1f}%."),
        metrics=[("Strategy", "reference" if weights else "balanced", "reference needs your CDS paste"),
                 ("GC%", f"{gc:.1f}%", None),
                 ("Round-trip", "✓ verified", "translate(optimized) == protein"),
                 ("Longest homopolymer", f"{_max_run(dna)} nt", "synthesis-risk proxy")],
        rows=[{"Codon_#": i + 1, "Amino_acid": p[i], "Codon": c} for i, c in enumerate(out_codons[:1000])],
        columns=["Codon_#", "Amino_acid", "Codon"],
        notes=["'Optimized' here means: reference-derived most-frequent codon, or a GC-balanced "
               "deterministic pick — NOT expression prediction. Avoiding T7/promoter artefacts, repeats, "
               "and mRNA structure requires commercial-grade tools.",
               "Stop codon TAA appended when the input did not end with *."],
        fasta=f">optimized_{len(p)}aa_{mode.split(' ')[0]}\n{dna}",
    )


def _cgc(codon: str) -> float:
    return sum(ch in "GC" for ch in codon) / max(1, len(codon))


def _max_run(s: str) -> int:
    best = run = 1 if s else 0
    for a, b in zip(s, s[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    return best


LAB_TOOLS = {
    45: crispr_design,
    46: pcr_product,
    47: oligo_tms,
    48: melting_curve,
    49: indel_detect,
    50: blast_local,
    51: pipeline_dashboard,
    52: codon_optimize,
}
