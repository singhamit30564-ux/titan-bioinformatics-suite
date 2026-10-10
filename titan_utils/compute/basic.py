"""Compute functions for Titan tools 1–17 (DNA/RNA basics & protein core).

Every function is pure (no Streamlit), derives ALL numbers from its inputs,
and documents simplifications in its "notes". Scientific core delegates to
Biopython's validated implementations wherever one exists.
"""
from __future__ import annotations

import math
from typing import Any, Dict

from Bio.Seq import Seq

from ..sequence import (
    CODON_TABLE_STANDARD,
    gc_fraction_safe,
    revcomp,
)
from ..thermo import (
    ThermoError,
    nn_tm,
    self_complementary,
    wallace_tm,
)
from . import ComputeError, guard_len, out, prepare_dna, prepare_protein

# ─────────────────────────────────────────────────────────────────────────────
# Tool 1 — DNA ↔ RNA conversion
# ─────────────────────────────────────────────────────────────────────────────
def dna_rna_convert(sequence: str = "ATGCGATCGATCGATCGATCGATC") -> Dict[str, Any]:
    raw = "".join((sequence or "").upper().split())
    has_u, has_t = "U" in raw, "T" in raw
    if has_u and has_t:
        raise ComputeError(
            "Sequence mixes U and T. Paste a pure RNA (A,U,G,C) or DNA (A,T,G,C) strand."
        )
    if has_u:
        converted = raw.replace("U", "T")
        mode = "RNA → DNA (back-transcription)"
        s = converted
    else:
        converted = raw.replace("T", "U")
        mode = "DNA → RNA (transcription)"
        s = raw
    guard_len(s)
    if not s:
        raise ComputeError("Empty sequence — paste DNA or RNA.")
    n_swap = (raw.count("U") if has_u else raw.count("T"))
    return out(
        title=mode,
        summary=(f"Converted {len(s):,} nt ({n_swap:,} bases swapped). "
                 f"Uracil{' replaces' if not has_u else ' was replaced by'} thymine "
                 f"{'in the product' if not has_u else 'during back-transcription'}."),
        metrics=[("Input length", f"{len(s):,} nt", None),
                 ("Bases swapped", f"{n_swap:,}", None),
                 ("Mode", "RNA→DNA" if has_u else "DNA→RNA", None)],
        rows=[{"Position_range": f"1-{len(s)}", "Strand_in": raw[:40] + ("…" if len(raw) > 40 else ""),
               "Strand_out": converted[:40] + ("…" if len(converted) > 40 else "")}],
        columns=["Position_range", "Strand_in", "Strand_out"],
        notes=["Transcription substitutes U for T (and vice versa) in this literal "
               "conversion; it does not model promoter/RNA-pol mechanics."],
        fasta=f">{mode.split(' ')[0]}_converted\n{converted}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 2 — Reverse complement & statistics
# ─────────────────────────────────────────────────────────────────────────────
def revcomp_stats(sequence: str = "ATGCGATCGATCGATCGATCGATC") -> Dict[str, Any]:
    s = prepare_dna(sequence, allow_iupac=True)
    guard_len(s)
    rc = revcomp(s)
    counts = {b: s.count(b) for b in "ATCG"}
    gc = gc_fraction_safe(s) * 100
    longest_run = _longest_homopolymer(s)
    palin = self_complementary(s) if all(c in "ATGC" for c in s) else None
    try:
        tm = nn_tm(s) if all(c in "ATGC" for c in s) and 4 <= len(s) <= 1000 else None
    except ThermoError:
        tm = None
    rows = [{"Nucleotide": b, "Count": counts[b], "Percent": round(100 * counts[b] / len(s), 2)}
            for b in "ATCG"]
    return out(
        title="Reverse Complement & Composition",
        summary=(f"{len(s):,} bp analysed; GC {gc:.2f}%; longest homopolymer {longest_run[1]}×{longest_run[0]}."
                 + (" The sequence is self-complementary (its own reverse complement)." if palin else "")),
        metrics=[("Length", f"{len(s):,} bp", None),
                 ("GC content", f"{gc:.2f}%", None),
                 ("Longest run", f"{longest_run[1]}×{longest_run[0]}", None),
                 ("Tm (NN, 50 mM Na⁺)", f"{tm:.1f} °C" if tm is not None else "n/a",
                  "Bio.SeqUtils.MeltingTemp.Tm_NN" if tm is not None else None)],
        rows=rows, columns=["Nucleotide", "Count", "Percent"],
        fig={"kind": "pie", "labels": [r["Nucleotide"] for r in rows],
             "values": [r["Count"] for r in rows], "title": "Base composition"},
        notes=["Chargaff parity of the *double strand* (A=T, C=G) is expected; a single "
               "strand deviating is normal.",
               f"Reverse complement (5'→3'): {rc[:60]}{'…' if len(rc) > 60 else ''}"],
        fasta=f">revcomp\n{rc}",
    )


def _longest_homopolymer(s: str):
    best = (s[0] if s else "-", 0)
    cur, run = s[0] if s else "", 1
    for c in s[1:]:
        if c == cur:
            run += 1
        else:
            cur, run = c, 1
        if run > best[1]:
            best = (cur, run)
    return best


# ─────────────────────────────────────────────────────────────────────────────
# Tool 3 — GC content + Tm with sliding window
# ─────────────────────────────────────────────────────────────────────────────
def gc_content_tm(sequence: str = "ATGCGCTAGCTAGCTAGCTAGCTAGCGCGCGCATGCA",
                  window: int = 20, step: int = 10) -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s)
    n = len(s)
    window = max(2, min(int(window or 20), n))
    step = max(1, min(int(step or 1), window))
    gc = 100.0 * (s.count("G") + s.count("C")) / n
    w_tm = wallace = None
    if n >= 4:
        w_tm = nn_tm(s)
        wallace, _in_range = wallace_tm(s)
    starts = list(range(0, max(1, n - window + 1), step))
    series = []
    for st in starts:
        seg = s[st:st + window]
        series.append({"start": st + 1,
                       "gc_percent": round(100.0 * (seg.count("G") + seg.count("C")) / max(1, len(seg)), 2)})
    return out(
        title="GC Content & Melting Temperature",
        summary=(f"{n:,} bp at {gc:.2f}% GC. NN Tm (25 nM strands, 50 mM Na⁺): "
                 + (f"{w_tm:.1f} °C." if w_tm is not None else "not computed (sequence too short.)")),
        metrics=[("Length", f"{n:,} bp", None),
                 ("GC content", f"{gc:.2f}%", None),
                 ("Tm nearest-neighbor", f"{w_tm:.1f} °C" if w_tm is not None else "n/a",
                  "SantaLucia/Allawi NN via Biopython, salt-corrected"),
                 ("Tm Wallace (≤14 nt)", f"{wallace:.0f} °C" if wallace is not None else "n/a",
                  "2·(A+T) + 4·(G+C); accurate only for very short oligos" if n <= 14 else
                  "OUT OF RANGE for this length — shown for teaching only")],
        rows=[{"Window_start_1based": d["start"], "GC_percent": d["gc_percent"]} for d in series],
        columns=["Window_start_1based", "GC_percent"],
        fig={"kind": "line", "x": [d["start"] for d in series], "y": [d["gc_percent"] for d in series],
             "xlabel": "Window start (bp)", "ylabel": "GC %", "title": f"GC profile (window {window} bp)"},
        notes=["NN is the reference method; Wallace/GC% are labeled approximations.",
               "Sliding window recomputes GC% every step without smoothing."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 4 — Mutation / SNP detection between two equal-length sequences
# ─────────────────────────────────────────────────────────────────────────────
def mutation_snp(ref_sequence: str = "ATGGCACGTACGTAGCATTGA",
                 alt_sequence: str = "ATGGCACGTTGGTAAATTTGA") -> Dict[str, Any]:
    ref = prepare_dna(ref_sequence)
    alt = prepare_dna(alt_sequence)
    if len(ref) != len(alt):
        raise ComputeError(
            f"Sequences differ in length ({len(ref)} vs {len(alt)}). This tool compares "
            "aligned, same-length sequences; trim or align first."
        )
    guard_len(ref, 100_000, "sequence")
    ti = tv = 0
    rows = []
    purines = set("AG")
    for i, (a, b) in enumerate(zip(ref, alt)):
        if a == b:
            continue
        transition = (a in purines) == (b in purines)
        ti += transition
        tv += not transition
        codon_i = i // 3
        codon_effect = "—"
        if len(ref) % 3 == 0:
            rc_, ac_ = ref[codon_i * 3:codon_i * 3 + 3], alt[codon_i * 3:codon_i * 3 + 3]
            aa1 = CODON_TABLE_STANDARD.get(rc_, "X")
            aa2 = CODON_TABLE_STANDARD.get(ac_, "X")
            codon_effect = ("silent" if aa1 == aa2 else
                            "nonsense" if aa2 == "*" else
                            "missense" if aa1 != "X" and aa2 != "X" else "unknown")
        rows.append({"Position_1based": i + 1, "Ref": a, "Alt": b,
                     "Type": "transition" if transition else "transversion",
                     "Codon": codon_i + 1 if len(ref) % 3 == 0 else "—",
                     "Coding_effect": codon_effect})
    total = len(rows)
    tv_denom = (ti + tv) or 1
    return out(
        title="Variant Differences (SNP table)",
        summary=(f"{total:,} differences across {len(ref):,} bp; Ti/Tv = "
                 f"{(ti / tv_denom if ti + tv else 0):.2f} ({ti} transitions / {tv} transversions)."
                 + (" Sequences are identical." if total == 0 else "")),
        metrics=[("Positions compared", f"{len(ref):,}", None),
                 ("Differences", f"{total:,}", None),
                 ("Ti/Tv ratio", f"{ti / tv_denom:.2f}" if ti + tv else "0.00",
                  "≈2+ suggests coding/selected variants; ≈0.5 neutral drift expectation")],
        rows=rows or [{"Position_1based": "—", "Ref": "—", "Alt": "—", "Type": "no differences",
                       "Codon": "—", "Coding_effect": "—"}],
        columns=["Position_1based", "Ref", "Alt", "Type", "Codon", "Coding_effect"],
        fig=({"kind": "bar", "x": ["transitions", "transversions"], "y": [ti, tv],
              "xlabel": "Substitution class", "ylabel": "Count", "title": "Substitution spectrum"}
             if total else None),
        notes=["Coding effect assumes the input is a CDS read 5'→3' in frame 0 and unspliced.",
               "Ti/Tv uses the standard purine↔purine / pyrimidine↔pyrimidine definition."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 5 — ORF finder (6 frames, ATG→stop)
# ─────────────────────────────────────────────────────────────────────────────
def orf_find(sequence: str = "ATGAAAGGGCCCCTATAGGGTGAATGCGCCTAG",
             min_length_aa: int = 10) -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s, 200_000)
    min_aa = max(1, int(min_length_aa or 10))
    bio = Seq(s)
    orfs = []
    for strand, nuc in (("+", bio), ("-", bio.reverse_complement())):
        n = str(nuc)
        for frame in range(3):
            i = frame
            while i + 3 <= len(n):
                if n[i:i + 3] == "ATG":
                    prot = []
                    j = i + 3
                    end = None
                    while j + 3 <= len(n):
                        codon = n[j:j + 3]
                        aa = CODON_TABLE_STANDARD.get(codon, "X")
                        if aa == "*":
                            end = j + 3
                            break
                        prot.append(aa)
                        j += 3
                    if end:
                        plen = len(prot)
                        if plen >= min_aa:
                            orfs.append({"Strand": strand, "Frame": frame + 1,
                                         "Start_1based": i + 1, "End_1based": end,
                                         "Length_aa": plen,
                                         "Protein": "".join(prot),
                                         "DNA": n[i:end]})
                        i = end  # continue scanning after this stop for nested starts
                        continue
                i += 3
    orfs.sort(key=lambda o: o["Length_aa"], reverse=True)
    longest = orfs[0]["Length_aa"] if orfs else 0
    return out(
        title="Open Reading Frames (ATG → stop, 6 frames)",
        summary=(f"Found {len(orfs):,} ORFs ≥ {min_aa} aa (longest {longest} aa)."
                 if orfs else f"No ORF ≥ {min_aa} aa found in {len(s):,} bp."),
        metrics=[("Sequence length", f"{len(s):,} bp", None),
                 ("ORFs (≥ threshold)", f"{len(orfs):,}", None),
                 ("Longest ORF", f"{longest} aa", None)],
        rows=[{k: v for k, v in o.items() if k != "DNA"} for o in orfs[:200]],
        columns=["Strand", "Frame", "Start_1based", "End_1based", "Length_aa", "Protein"],
        fig=({"kind": "bar", "x": [f"{o['Strand']}{o['Frame']}@{o['Start_1based']}" for o in orfs[:15]],
              "y": [o["Length_aa"] for o in orfs[:15]], "xlabel": "ORF (strand/frame@start)",
              "ylabel": "Length (aa)", "title": "Top ORFs by length"} if orfs else None),
        notes=["Stops at the first in-frame stop codon per start; nested ATGs before a stop "
               "are reported as separate ORFs sharing the same stop.",
               "Start-codon dependence is a computational convention — some real genes start with GTG/TTG."],
        fasta="".join(f">ORF_{i+1}_{o['Strand']}{o['Frame']}_{o['Start_1based']}-{o['End_1based']}\n{o['DNA']}\n"
                      for i, o in enumerate(orfs[:20])),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 6 — Motif / pattern finder (literal or regex, both strands)
# ─────────────────────────────────────────────────────────────────────────────
def motif_find(sequence: str = "GGAATTCATGCTGAATTCGCG",
               motif: str = "GAATTC",
               mode: str = "literal (IUPAC codes ok)",
               both_strands: str = "forward only") -> Dict[str, Any]:
    import re
    s = prepare_dna(sequence, allow_iupac=True)
    guard_len(s, 100_000)
    m = (motif or "").upper().strip()
    if not m:
        raise ComputeError("Enter a motif to search for.")
    hits = []
    if mode.startswith("regex"):
        if len(m) > 200:
            raise ComputeError("Regex patterns are capped at 200 characters (safety).")
        try:
            rx = re.compile(m)
        except re.error as e:
            raise ComputeError(f"Invalid regex: {e}") from e
        for match in rx.finditer(s):
            if match.end() > match.start():
                hits.append({"Strand": "+", "Start_1based": match.start() + 1,
                             "End_1based": match.end(), "Match": match.group()})
    else:
        iupac = {"A": "A", "C": "C", "G": "G", "T": "T",
                 "R": "[AG]", "Y": "[CT]", "S": "[GC]", "W": "[AT]", "K": "[GT]",
                 "M": "[AC]", "B": "[CGT]", "D": "[AGT]", "H": "[ACT]", "V": "[ACG]", "N": "[ACGT]"}
        bad = sorted({c for c in m if c not in iupac})
        if bad:
            raise ComputeError(f"Motif contains unsupported letters {bad}. Allowed: ACGT + IUPAC codes (RN YSWKMBDHVN).")
        rx = re.compile("".join(iupac[c] for c in m))
        for match in rx.finditer(s):
            hits.append({"Strand": "+", "Start_1based": match.start() + 1,
                         "End_1based": match.end(), "Match": match.group()})
        if both_strands.startswith("both"):
            rcs = revcomp(s)
            for match in rx.finditer(rcs):
                hits.append({"Strand": "−", "Start_1based": len(s) - match.end() + 1,
                             "End_1based": len(s) - match.start(), "Match": match.group()})
    return out(
        title=f"Motif hits for “{m}”",
        summary=(f"{len(hits):,} match(es) of “{m}” in {len(s):,} bp"
                 + (f" across both strands." if both_strands.startswith("both") and mode != "regex" else ".")),
        metrics=[("Motif", m[:60], None), ("Matches", f"{len(hits):,}", None),
                 ("Motif length", f"{len(m)}", None)],
        rows=hits[:500] or [{"Strand": "—", "Start_1based": "—", "End_1based": "—",
                             "Match": "no matches found"}],
        columns=["Strand", "Start_1based", "End_1based", "Match"],
        fig=None,
        notes=["Overlapping matches are reported (zero-width lookahead semantics via finditer on the literal pattern).",
               "Regex mode runs against the forward strand only and is length-capped to protect the server."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 7 — Restriction enzyme cutter (Biopython Restriction)
# ─────────────────────────────────────────────────────────────────────────────
def restriction_cut(sequence: str = "GAATTCGGATCCCTGCAGGCGCGCCATGCAT",
                    enzymes: str = "EcoRI, BamHI, PstI, NotI, SmaI") -> Dict[str, Any]:
    from Bio import Restriction
    s = prepare_dna(sequence)
    guard_len(s, 100_000)
    wanted = [e.strip() for e in (enzymes or "").split(",") if e.strip()]
    if not wanted:
        raise ComputeError("Enter comma-separated enzyme names, e.g. EcoRI, BamHI.")
    rows, unknown = [], []
    for name in wanted:
        enz = getattr(Restriction, name, None)
        if enz is None:
            unknown.append(name)
            continue
        try:
            cuts = list(enz.search(Seq(s)))
        except Exception:  # non-DNA alphabets etc.
            unknown.append(name)
            continue
        for pos in cuts:
            rows.append({"Enzyme": name, "Cut_site_1based": int(pos) + 1,
                         "Recognition": str(getattr(enz, "site", enz)).upper(),
                         "Frequency_bp": enz.freq,
                         "Type": enz.elucidate()[:80] if hasattr(enz, "elucidate") else ""})
    if unknown:
        raise ComputeError(f"Unknown enzyme(s): {', '.join(unknown)} — use Biopython names (e.g. EcoRI, NotI).")
    rows.sort(key=lambda r: r["Cut_site_1based"])
    per_enz = {}
    for r in rows:
        per_enz[r["Enzyme"]] = per_enz.get(r["Enzyme"], 0) + 1
    frag_positions = [0] + sorted({r["Cut_site_1based"] for r in rows}) + [len(s)]
    fragments = [frag_positions[i + 1] - frag_positions[i] for i in range(len(frag_positions) - 1)]
    return out(
        title=f"Restriction map ({len(rows)} cut(s))",
        summary=(f"{len(rows):,} cut site(s) for {len(wanted)} enzymes in {len(s):,} bp (linear DNA)."
                 if rows else f"No cut sites found for {', '.join(wanted)} in {len(s):,} bp."),
        metrics=[("Enzymes checked", f"{len(wanted)}", None),
                 ("Total cuts", f"{len(rows):,}", None),
                 ("Fragments", f"{len(fragments):,}", None)],
        rows=[{"Enzyme": k, "Cuts": v} for k, v in sorted(per_enz.items())] or
             [{"Enzyme": "—", "Cuts": 0}],
        columns=["Enzyme", "Cuts"],
        fig=({"kind": "bar", "x": list(per_enz.keys()), "y": list(per_enz.values()),
              "xlabel": "Enzyme", "ylabel": "Cuts", "title": "Cuts per enzyme"} if per_enz else None),
        notes=["Positions come from Bio.Restriction (validated enzyme database); DNA is treated "
               "as linear — circular plasmids add one fragment when cut once.",
               f"Predicted fragment sizes (bp): {fragments[:50]}"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 8 — Codon usage of one CDS (observed + RSCU, no external table)
# ─────────────────────────────────────────────────────────────────────────────
def codon_usage(sequence: str = "ATGAAAGGGCCCTTTGGGCCCATAG", table: str = "Standard") -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s, 100_000)
    if len(s) < 3:
        raise ComputeError("Sequence shorter than one codon — paste a CDS.")
    codons: Dict[str, int] = {}
    aa_family: Dict[str, list] = {}
    for i in range(0, len(s) - 2, 3):
        c = s[i:i + 3]
        aa = CODON_TABLE_STANDARD.get(c, "X")
        codons[c] = codons.get(c, 0) + 1
        aa_family.setdefault(aa, []).append(c)
    rscu = {}
    for aa, fam in aa_family.items():
        syn = [c for c in CODON_TABLE_STANDARD if CODON_TABLE_STANDARD[c] == aa]
        n_syn = max(1, len(syn))
        for c in fam:
            expected = sum(codons.get(s2, 0) for s2 in syn) / n_syn
            rscu[c] = codons[c] / expected if expected > 0 else 1.0
    total_codons = sum(codons.values())
    rows = sorted(({"Codon": c, "Amino_acid": CODON_TABLE_STANDARD.get(c, "X"),
                    "Count": n, "Freq_percent": round(100 * n / total_codons, 2),
                    "RSCU": round(rscu.get(c, 1.0), 2)} for c, n in codons.items()),
                  key=lambda r: (-r["Count"], r["Codon"]))
    gc3 = gc3_tot = 0
    for c, n in codons.items():
        gc3_tot += n
        gc3 += n * sum(ch in "GC" for ch in c[2])
    return out(
        title="Codon Usage of your CDS",
        summary=(f"{total_codons:,} codons from {len(s):,} bp; most used: "
                 + (f"{rows[0]['Codon']} ({rows[0]['Amino_acid']}, {rows[0]['Freq_percent']}%)." if rows else "—")),
        metrics=[("Codons", f"{total_codons:,}", None),
                 ("Unique codons", f"{len(codons)}", None),
                 ("GC3 content", f"{100.0 * gc3 / max(1, gc3_tot):.1f}%",
                  "GC fraction at third codon positions — correlates with expression bias")],
        rows=rows, columns=["Codon", "Amino_acid", "Count", "Freq_percent", "RSCU"],
        fig={"kind": "bar", "x": [r["Codon"] for r in rows[:20]], "y": [r["Count"] for r in rows[:20]],
             "xlabel": "Codon", "ylabel": "Count", "title": "Top 20 codons"},
        notes=["RSCU = 1 means the codon is used as often as its synonymous family average; "
               "values are computed from THIS sequence only (no organism table is assumed).",
               f"Trailing {len(s) % 3} bases skipped when length is not a multiple of 3."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 9 — Hamming & Levenshtein distance
# ─────────────────────────────────────────────────────────────────────────────
def hamming_edit(seq1: str = "ATGCGCTAG", seq2: str = "ATGCACTAGC") -> Dict[str, Any]:
    from . import MAX_LEV_LEN
    a = prepare_dna(seq1, allow_iupac=False)
    b = prepare_dna(seq2, allow_iupac=False)
    if max(len(a), len(b)) > MAX_LEV_LEN:
        raise ComputeError(
            f"Edit distance is limited to {MAX_LEV_LEN:,} bp per strand here "
            "(quadratic pure-Python DP). Use pages 40–42 alignment for longer inputs."
        )
    hamming = sum(x != y for x, y in zip(a, b)) if len(a) == len(b) else None
    lev = _levenshtein(a, b)
    ident = 100.0 * (1 - lev / max(len(a), len(b), 1))
    return out(
        title="Pairwise Distance Metrics",
        summary=(f"Levenshtein {lev} (identity ≈ {ident:.1f}%) over lengths "
                 f"{len(a):,}/{len(b):,}." +
                 (f" Hamming distance {hamming}." if hamming is not None
                  else " Hamming requires equal lengths (not met).")),
        metrics=[("Lengths", f"{len(a):,} / {len(b):,}", None),
                 ("Hamming", str(hamming) if hamming is not None else "n/a",
                  "substitutions only, equal-length sequences"),
                 ("Levenshtein", str(lev), "edit ops: insert, delete, substitute"),
                 ("Percent identity", f"{ident:.2f}%", "1 − Levenshtein/max(len)")],
        rows=[{"Metric": "Hamming", "Value": str(hamming) if hamming is not None else "n/a"},
              {"Metric": "Levenshtein", "Value": str(lev)},
              {"Metric": "Identity_%", "Value": f"{ident:.2f}"}],
        columns=["Metric", "Value"],
        notes=["Percent identity here is a length-normalized edit score — NOT an "
               "alignment identity (see Pairwise Alignment for gapped identity)."],
    )


def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# ─────────────────────────────────────────────────────────────────────────────
# Tool 10 — Nucleotide frequency & Shannon entropy
# ─────────────────────────────────────────────────────────────────────────────
def nucleotide_entropy(sequence: str = "ATGCGATCGATCGATCGATCGATC") -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s, 1_000_000)
    counts = {b: s.count(b) for b in "ATCG"}
    n = len(s)
    ent = 0.0
    for c in counts.values():
        if c:
            p = c / n
            ent -= p * math.log2(p)
    return out(
        title="Base Frequencies & Shannon Entropy",
        summary=(f"Entropy {ent:.3f} bits/base of {math.log2(4):.0f} possible; "
                 f"dominant base {max(counts, key=counts.get)} ({max(counts.values()):,})."),
        metrics=[("Length", f"{n:,} nt", None),
                 ("Shannon entropy", f"{ent:.3f} bits", "max 2 bits = perfectly uniform A/T/G/C"),
                 ("Uniformity", f"{ent / 2.0 * 100:.1f}%", "fraction of theoretical maximum")],
        rows=[{"Base": b, "Count": counts[b], "Freq_percent": round(100 * counts[b] / n, 2)} for b in "ATCG"],
        columns=["Base", "Count", "Freq_percent"],
        fig={"kind": "bar", "x": list("ATCG"), "y": [counts[b] for b in "ATCG"],
             "xlabel": "Base", "ylabel": "Count", "title": "Composition"},
        notes=["Entropy is computed over the 4 canonical bases; ambiguity codes are excluded "
               "by validation upstream."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 11 — Central dogma visualizer (DNA → mRNA → protein)
# ─────────────────────────────────────────────────────────────────────────────
def central_dogma(sequence: str = "ATGGCTAGCTTGCCTGTATAA",
                  strand: str = "forward (+)",
                  frame: int = 1) -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s, 50_000)
    f = max(0, min(2, int(frame or 1) - 1))
    text = f"frame {f + 1} ({'reverse (−)' if str(strand).lower().startswith('reverse') else 'forward (+)'})"
    selfcomp = False
    seq_use = str(Seq(s).reverse_complement()) if str(strand).lower().startswith("reverse") else s
    coding = seq_use[f:]
    mrna = coding.replace("T", "U")
    protein = str(Seq(coding).translate())
    stop_at = protein.find("*")
    protein_trunc = protein if stop_at < 0 else protein[:stop_at + 1]
    rows = []
    n_codons = min(len(coding) // 3, 1000)
    for i in range(n_codons):
        codon = coding[3 * i:3 * i + 3]
        rows.append({"Codon_#": i + 1, "DNA_codon": codon, "mRNA_codon": codon.replace("T", "U"),
                     "Amino_acid": CODON_TABLE_STANDARD.get(codon, "X"),
                     "Protein_letter": protein_trunc[i] if i < len(protein_trunc) else "—"})
    return out(
        title="Central Dogma: DNA → mRNA → Protein",
        summary=(f"{n_codons:,} codons translated in {text}; "
                 + (f"first stop (TAA/TAG/TGA) at codon {stop_at + 1}." if stop_at >= 0 else "no in-frame stop codon found.")),
        metrics=[("Template length", f"{len(s):,} bp", None),
                 ("mRNA length", f"{len(mrna):,} nt", "T→U replacement, same length"),
                 ("Polypeptide", f"{len(protein_trunc)} aa", "up to first stop inclusive")],
        rows=rows, columns=["Codon_#", "DNA_codon", "mRNA_codon", "Amino_acid", "Protein_letter"],
        fig={"kind": "bar", "x": ["DNA (bp)", "mRNA (nt)", "Protein (aa)"],
             "y": [len(s), len(mrna), len(protein_trunc)], "xlabel": "Molecule",
             "ylabel": "Units", "title": "Dogma length cascade"},
        notes=["No 5' cap, poly-A tail, splicing, or RNA editing is modeled (prokaryotic style).",
               f"Protein: {protein_trunc[:80]}{'…' if len(protein_trunc) > 80 else ''}"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 12 — DNA → protein (6-frame)
# ─────────────────────────────────────────────────────────────────────────────
def six_frame_translate(sequence: str = "ATGGCTAAAGGGCCCTTTTAA",
                        strand: str = "both strands") -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s, 50_000)
    bio = Seq(s)
    strands = [("+", bio)] if strand.lower().startswith("forward") else [
        ("+", bio), ("-", bio.reverse_complement())
    ]
    rows = []
    for sname, nuc in strands:
        n = str(nuc)
        for fr in range(3):
            prot = str(Seq(n[fr:len(n) - ((len(n) - fr) % 3)]).translate())
            rows.append({"Strand": sname, "Frame": fr + 1, "Protein": prot,
                         "Length_aa": len(prot), "Stops": prot.count("*"),
                         "Longest_no_stop": _longest_between_stops(prot)})
    best = max(rows, key=lambda r: r["Longest_no_stop"])
    return out(
        title="Six-Frame Translation",
        summary=(f"Longest stop-free stretch: {best['Longest_no_stop']} aa on strand "
                 f"{best['Strand']} frame {best['Frame']}."),
        metrics=[("Frames computed", f"{len(rows)}", None),
                 ("Best frame", f"{best['Strand']}{best['Frame']}", None),
                 ("Best open length", f"{best['Longest_no_stop']} aa", None)],
        rows=rows, columns=["Strand", "Frame", "Length_aa", "Stops", "Longest_no_stop", "Protein"],
        fig={"kind": "bar", "x": [f"{r['Strand']}{r['Frame']}" for r in rows],
             "y": [r["Longest_no_stop"] for r in rows], "xlabel": "Frame",
             "ylabel": "Longest open stretch (aa)", "title": "Open stretch per frame"},
        notes=["Ambiguous codons translate as X; Biopython's genetic code is used for fidelity."],
    )


def _longest_between_stops(p: str) -> int:
    return max((len(seg) for seg in p.split("*")), default=0)


# ─────────────────────────────────────────────────────────────────────────────
# Tool 13 — Molecular weight
# ─────────────────────────────────────────────────────────────────────────────
def molecular_weight(sequence: str = "MKVLWAALLVTFLAGCQAKVEQAVETEPEPELRQQTEWQSGQRWELALGRFWDYLRWVQTLSEQVQEELLSSQVTQELRALMDETMKELKAYKSELEEQLTPVAEETRARLSKELQAAQARLGADMEDVCGRLVQYRGEVQAMLGQSTEELRVRLASHLRKLRKRLLRDADDLQKRLAVYQAGREGAGLELQEqFILEQI",
                     molecule: str = "auto") -> Dict[str, Any]:
    from Bio.SeqUtils import molecular_weight as biow
    body_lines = [l for l in (sequence or "").splitlines() if not l.strip().startswith((">", ";"))]
    raw = "".join("".join(body_lines).upper().split()).rstrip("*")
    if not raw:
        raise ComputeError("Empty sequence.")
    kinds = set(raw)
    if molecule == "auto":
        if kinds <= set("ATCG"):
            mol = "DNA"
        elif kinds <= set("AUCG"):
            mol = "RNA"
        elif kinds <= set("ACDEFGHIKLMNPQRSTVWY"):
            mol = "protein"
        else:
            raise ComputeError(f"Cannot auto-detect molecule type (letters {sorted(kinds)[:8]}…). "
                               "Choose DNA, RNA, or protein explicitly.")
    else:
        mol = {"dna": "DNA", "rna": "RNA", "protein": "protein"}[molecule.strip().lower()]
    if mol in ("DNA", "RNA") and not kinds <= (set("ATCG") if mol == "DNA" else set("AUCG")):
        raise ComputeError(f"Letters {sorted(kinds - (set('ATCG') if mol=='DNA' else set('AUCG')))} are not valid {mol}.")
    guard_len(raw, 500_000)
    mw = float(biow(raw, seq_type=mol))
    per = mw / len(raw)
    unit = "Da/base" if mol != "protein" else "Da/residue"
    return out(
        title=f"Molecular Weight ({mol})",
        summary=(f"{mol} of {len(raw):,} units weighs {mw:,.1f} Da ({mw / 1000:,.2f} kDa); "
                 f"mean {per:,.2f} {unit}."),
        metrics=[("Mass", f"{mw:,.1f} Da", "Biopython molecular_weight, average isotopes"),
                 ("Mass", f"{mw / 1000:,.3f} kDa", None),
                 ("Monomer mean", f"{per:,.2f} {unit}", None)],
        rows=[{"Molecule": mol, "Count": len(raw), "MW_Da": round(mw, 2),
               "MW_kDa": round(mw / 1000, 4), "Mean_unit_Da": round(per, 3)}],
        columns=["Molecule", "Count", "MW_Da", "MW_kDa", "Mean_unit_Da"],
        notes=["Average (not monoisotopic) mass, water removed for polymer — same convention as Biopython."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 14 — Back-translation (protein → DNA)
# ─────────────────────────────────────────────────────────────────────────────
_REVCODON: Dict[str, list] = {}
for _c, _aa in CODON_TABLE_STANDARD.items():
    _REVCODON.setdefault(_aa, []).append(_c)
for _l in _REVCODON.values():
    _l.sort()


def back_translate(protein: str = "MKVLWAALLVTFLAGCQAK",
                   strategy: str = "first codon per amino acid",
                   seed: int = 12345) -> Dict[str, Any]:
    import random as _r
    p = prepare_protein(protein, allow_stop=True)
    guard_len(p, 20_000)
    rng = _r.Random(seed)
    out_codons = []
    for aa in p:
        choices = _REVCODON.get(aa, [])
        if not choices:
            raise ComputeError(f"No codons for letter {aa!r}.")
        if strategy.startswith("first"):
            pick = choices[0]
        elif strategy.startswith("last"):
            pick = choices[-1]
        else:  # "random (seeded)"
            pick = rng.choice(choices)
        out_codons.append(pick)
    dna = "".join(out_codons)
    # round-trip validation — a back-translation MUST re-translate identically
    back = "".join(CODON_TABLE_STANDARD.get(dna[i:i + 3], "X") for i in range(0, len(dna), 3))
    if back != p:
        raise ComputeError("Internal round-trip check failed — report this input to the maintainers.")
    gc = 100.0 * (dna.count("G") + dna.count("C")) / len(dna)
    return out(
        title="Back-Translation (Protein → DNA)",
        summary=(f"{len(p):,} aa → {len(dna):,} nt using strategy “{strategy}”. "
                 f"Round-trip translation verified identical. GC {gc:.1f}%."),
        metrics=[("DNA length", f"{len(dna):,} bp", None),
                 ("Strategy", strategy.split(" (")[0], None),
                 ("Product GC%", f"{gc:.1f}%", None)],
        rows=[{"Codon_#": i + 1, "Amino_acid": p[i], "Chosen_codon": c} for i, c in enumerate(out_codons[:500])],
        columns=["Codon_#", "Amino_acid", "Chosen_codon"],
        notes=["Back-translation is one-way: many DNA sequences encode this protein; this is ONE valid answer, "
               "not 'the' gene. Random mode is deterministic for a fixed seed.",
               "No organism codon-usage table is consulted; use the Codon Optimizer with a reference for that."],
        fasta=f">backtranslated\n{dna}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 15 — In-silico point mutagenesis (with coding effect)
# ─────────────────────────────────────────────────────────────────────────────
_AA_PROPS = {
    "A": ("Ala", "nonpolar", 0.0), "R": ("Arg", "positive", 1.0), "N": ("Asn", "polar", 0.0),
    "D": ("Asp", "negative", -1.0), "C": ("Cys", "polar", 0.0), "Q": ("Gln", "polar", 0.0),
    "E": ("Glu", "negative", -1.0), "G": ("Gly", "nonpolar", 0.0), "H": ("His", "positive", 0.5),
    "I": ("Ile", "nonpolar", 0.0), "L": ("Leu", "nonpolar", 0.0), "K": ("Lys", "positive", 1.0),
    "M": ("Met", "nonpolar", 0.0), "F": ("Phe", "nonpolar", 0.0), "P": ("Pro", "nonpolar", 0.0),
    "S": ("Ser", "polar", 0.0), "T": ("Thr", "polar", 0.0), "W": ("Trp", "nonpolar", 0.0),
    "Y": ("Tyr", "polar", 0.0), "V": ("Val", "nonpolar", 0.0), "*": ("Stop", "stop", 0.0),
    "X": ("Any", "unknown", 0.0),
}


def in_silico_mutagenesis(sequence: str = "ATGGCTAAAGGGCCCTTTTAA",
                          position: int = 4, new_base: str = "C") -> Dict[str, Any]:
    s = prepare_dna(sequence)
    guard_len(s, 50_000)
    try:
        pos = int(position)
    except (TypeError, ValueError):
        raise ComputeError("Position must be a positive integer (1-based).")
    if not 1 <= pos <= len(s):
        raise ComputeError(f"Position {pos} is outside 1..{len(s)}.")
    nb = (new_base or "").strip().upper()[:1]
    if nb not in "ATCG":
        raise ComputeError("New base must be A, T, C, or G.")
    if nb == s[pos - 1]:
        raise ComputeError("New base equals the reference base — nothing would change.")
    mut = s[:pos - 1] + nb + s[pos:]
    codon_idx = (pos - 1) // 3
    old_codon = s[codon_idx * 3:codon_idx * 3 + 3]
    new_codon = mut[codon_idx * 3:codon_idx * 3 + 3]
    aa_old = CODON_TABLE_STANDARD.get(old_codon, "X")
    aa_new = CODON_TABLE_STANDARD.get(new_codon, "X")
    if len(s) % 3 == 0:
        p_old = "".join(CODON_TABLE_STANDARD.get(s[i:i + 3], "X") for i in range(0, len(s), 3))
        p_new = "".join(CODON_TABLE_STANDARD.get(mut[i:i + 3], "X") for i in range(0, len(mut), 3))
    else:
        p_old = p_new = None
    if aa_new == aa_old:
        effect = "silent (same amino acid)"
    elif aa_new == "*":
        effect = "nonsense (creates a stop)"
    elif aa_old == "*":
        effect = "stop-loss"
    else:
        effect = "missense"
    chg = _AA_PROPS[aa_new][2] - _AA_PROPS[aa_old][2]
    return out(
        title=f"Point mutation c.{pos}{s[pos - 1]}>{nb}",
        summary=(f"codon {codon_idx + 1}: {old_codon}({aa_old}) → {new_codon}({aa_new}): {effect}. "
                 + (f"Charge shift {chg:+.1f}." if effect == "missense" else "")),
        metrics=[("Position", f"{pos:,}", None), ("Codon", f"{old_codon} → {new_codon}", None),
                 ("Amino acid", f"{aa_old} → {aa_new}", None), ("Effect", effect.split(" (")[0], None)],
        rows=[{"Codon_#": codon_idx + 1, "DNA_old": old_codon, "DNA_new": new_codon,
               "AA_old": _AA_PROPS[aa_old][0], "AA_new": _AA_PROPS[aa_new][0], "Effect": effect,
               "Charge_shift": f"{chg:+.1f}"}],
        columns=["Codon_#", "DNA_old", "DNA_new", "AA_old", "AA_new", "Effect", "Charge_shift"],
        notes=["Assumes the input is a single unspliced CDS in frame 0.",
               f"Mutant DNA: {mut[:80]}{'…' if len(mut) > 80 else ''}"]
              + ([f"Protein unchanged: {'yes' if p_old == p_new else 'no'}; "
                  f"new protein length {len(p_new)} aa."] if p_old else []),
        fasta=f">mutant_c{pos}{s[pos-1]}{nb}\n{mut}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 16 — Protein isoelectric point (Biopython ProtParam)
# ─────────────────────────────────────────────────────────────────────────────
def protein_pi(sequence: str = "MKVLWAALLVTFLAGCQAK") -> Dict[str, Any]:
    from Bio.SeqUtils.ProtParam import ProteinAnalysis
    p = prepare_protein(sequence)
    guard_len(p, 50_000)
    clean_p = p.replace("*", "").replace("X", "")
    skipped = len(p) - len(clean_p)
    if not clean_p:
        raise ComputeError("No chargeable residues found.")
    pa = ProteinAnalysis(clean_p)
    pi = float(pa.isoelectric_point())
    charge_at = {v: float(pa.charge_at_pH(v)) for v in (2.0, 7.0, pi, 10.5)}
    acids = clean_p.count("D") + clean_p.count("E")
    bases = clean_p.count("K") + clean_p.count("R") + clean_p.count("H")
    return out(
        title=f"Isoelectric Point ≈ {pi:.2f}",
        summary=(f"Henderson–Hasselbalch pI from Bio.SeqUtils.ProtParam over {len(clean_p):,} aa "
                 f"({acids} acidic vs {bases} basic side chains)."),
        metrics=[("pI", f"{pi:.2f}", "pH of zero net charge"),
                 ("Charge @ pH 7", f"{charge_at[7.0]:+.1f}", None),
                 ("Acidic/Basic", f"{acids}/{bases}", "D+E vs K+R+H counts"),
                 ("Excluded", f"{skipped} X/* residues" if skipped else "none", None)],
        rows=[{"pH": k, "Net_charge": round(v, 2)} for k, v in sorted(charge_at.items())],
        columns=["pH", "Net_charge"],
        notes=["Uses the EMBOSS/Biopython pKa set; pI depends slightly on the chosen pKa table.",
               "X and * are excluded from the charge calculation (listed in metrics)."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 17 — Hydropathy (Kyte–Doolittle) with sliding window
# ─────────────────────────────────────────────────────────────────────────────
def hydropathy_plot(sequence: str = "MKVLWAALLVTFLAGCQAKVEQAVETEPEPELRQQTEWQSG",
                    window: int = 9) -> Dict[str, Any]:
    p = prepare_protein(sequence)
    guard_len(p, 20_000)
    from Bio.SeqUtils.ProtParam import ProteinAnalysis
    clean = p.replace("X", "").replace("*", "")
    if len(clean) < 2:
        raise ComputeError("Protein too short for a hydropathy scan.")
    pa = ProteinAnalysis(clean)
    w = max(3, min(int(window or 9), len(clean)))
    try:
        series = [float(v) for v in pa.gravy_window_list(window=w, edge="expand")[:5000]]
    except Exception:
        series = None
    gravy = float(pa.gravy())
    if series is None:  # very old Biopython signature fallback
        kd = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5,
              "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8,
              "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2}
        series = []
        for i in range(0, max(1, len(clean) - w + 1)):
            seg = clean[i:i + w]
            series.append(sum(kd[c] for c in seg) / len(seg))
    peaks = [i + 1 for i in range(1, len(series) - 1)
             if series[i] > 1.6 and series[i] >= series[i - 1] and series[i] >= series[i + 1]]
    tm_hits = [i for i, v in enumerate(series) if v > 1.6]
    return out(
        title="Kyte–Doolittle Hydropathy",
        summary=(f"GRAVY = {gravy:+.3f} over {len(clean):,} aa (window {w}); "
                 f"{len(peaks)} prominent hydrophobic peaks (>1.6) — putative TM segments."),
        metrics=[("GRAVY", f"{gravy:+.3f}", "grand average of hydropathy; >0 = hydrophobic"),
                 ("Window", str(w), None),
                 ("Candidate TM segments", f"{len(peaks):,}", "local maxima with score > +1.6")],
        rows=[{"Window_center": i + (w + 1) // 2, "Score": round(v, 3),
               "Above_TM_threshold": "yes" if v > 1.6 else "no"} for i, v in enumerate(series[:2000])],
        columns=["Window_center", "Score", "Above_TM_threshold"],
        fig={"kind": "line", "x": list(range(1, len(series) + 1))[:2000], "y": [round(v, 3) for v in series[:2000]],
             "xlabel": "Window center (residue)", "ylabel": "KD score", "title": "Hydropathy profile"},
        notes=["Kyte–Doolittle scale; >1.6 is a heuristic membrane-inclusion cut-off, "
               "not a validated TM prediction — use a dedicated tool (Phobius/TMHMM) for real calls."],
    )


BASIC_TOOLS = {
    1: dna_rna_convert,
    2: revcomp_stats,
    3: gc_content_tm,
    4: mutation_snp,
    5: orf_find,
    6: motif_find,
    7: restriction_cut,
    8: codon_usage,
    9: hamming_edit,
    10: nucleotide_entropy,
    11: central_dogma,
    12: six_frame_translate,
    13: molecular_weight,
    14: back_translate,
    15: in_silico_mutagenesis,
    16: protein_pi,
    17: hydropathy_plot,
}
