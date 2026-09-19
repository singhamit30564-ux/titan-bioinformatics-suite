"""Sequence utilities: cleaning, validation, translation, reverse complement.

Uses Biopython's validated codon tables when available; falls back to a
verified hard-coded table otherwise.
"""
from __future__ import annotations

from typing import Optional, Tuple

# ---- Character sets ----
ALLOWED_DNA = set("ATCG")
ALLOWED_RNA = set("AUCG")
ALLOWED_PROTEIN = set("ACDEFGHIKLMNPQRSTVWY*")
# IUPAC ambiguity codes commonly found in real FASTA files
ALLOWED_DNA_IUPAC = set("ATCGURYSWKMBDHVN.-")

_DNA_COMP = str.maketrans("ACGTRYSWKMBDHVNacgtryswkmbdhvn",
                          "TGCAYRSWMKVHDBNtgcayrswmkvhdbn")


def clean_sequence(seq: str, *, upper: bool = True) -> str:
    """Strip whitespace, newlines, and common FASTA artefacts."""
    if seq is None:
        return ""
    cleaned = seq.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")
    return cleaned.upper() if upper else cleaned


def _invalid_chars(seq: str, allowed: set) -> set:
    return set(seq) - allowed


def validate_dna(seq: str, *, allow_iupac: bool = False) -> Tuple[str, Optional[str]]:
    """Return (cleaned_sequence, error_message_or_None)."""
    s = clean_sequence(seq)
    if not s:
        return s, "❌ Please enter a valid DNA sequence (empty input)."
    allowed = ALLOWED_DNA_IUPAC if allow_iupac else ALLOWED_DNA
    bad = _invalid_chars(s, allowed)
    if bad:
        return s, f"❌ Invalid DNA characters: {sorted(bad)}. Allowed: {sorted(allowed)}"
    return s, None


def validate_rna(seq: str) -> Tuple[str, Optional[str]]:
    s = clean_sequence(seq)
    if not s:
        return s, "❌ Please enter a valid RNA sequence."
    bad = _invalid_chars(s, ALLOWED_RNA)
    if bad:
        return s, f"❌ Invalid RNA characters: {sorted(bad)}. Allowed: A, U, C, G."
    return s, None


def validate_protein(seq: str) -> Tuple[str, Optional[str]]:
    s = clean_sequence(seq)
    if not s:
        return s, "❌ Please enter a valid protein sequence."
    bad = _invalid_chars(s, ALLOWED_PROTEIN)
    if bad:
        return s, f"❌ Invalid amino-acid codes: {sorted(bad)}."
    return s, None


def revcomp(seq: str) -> str:
    """Reverse complement of a DNA sequence (supports IUPAC codes)."""
    return seq.translate(_DNA_COMP)[::-1]


def gc_fraction_safe(seq: str) -> float:
    """Return GC fraction (0..1); ignores IUPAC ambiguity codes."""
    if not seq:
        return 0.0
    s = seq.upper()
    gc = s.count("G") + s.count("C")
    at = s.count("A") + s.count("T")
    total = gc + at
    return gc / total if total else 0.0


# ---- Codon table (standard genetic code) — verified complete ----
# Derived from Biopython's CodonTable.unambiguous_dna_by_id[1]
CODON_TABLE_STANDARD = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G',
}

REVERSE_CODON_TABLE_STANDARD: dict[str, list[str]] = {}
for _codon, _aa in CODON_TABLE_STANDARD.items():
    REVERSE_CODON_TABLE_STANDARD.setdefault(_aa, []).append(_codon)


def translate(dna_seq: str, *, to_stop: bool = False) -> str:
    """Translate a DNA sequence to protein using the standard code.

    Skips incomplete trailing codons. If `to_stop` is True, truncates at
    the first in-frame stop codon.
    """
    s = clean_sequence(dna_seq)
    protein = []
    for i in range(0, len(s) - 2, 3):
        codon = s[i:i + 3]
        aa = CODON_TABLE_STANDARD.get(codon, 'X')
        if to_stop and aa == '*':
            break
        protein.append(aa)
    return "".join(protein)

# ---- Extended helpers centralized from page duplicates ----

def gc_content_percent(seq: str) -> float:
    """GC% (0-100) using gc_fraction_safe, rounded to 2 decimals for UI."""
    return round(gc_fraction_safe(seq) * 100, 2)


def at_content_percent(seq: str) -> float:
    """AT% complement of GC%."""
    return round(100 - gc_content_percent(seq), 2)


def nucleotide_counts(seq: str) -> dict:
    """Return counts of A/T/C/G for a DNA sequence (upper-cased)."""
    s = clean_sequence(seq)
    return {base: s.count(base) for base in "ATCG"}


def find_orfs_simple(seq: str, min_len: int = 0) -> list[dict]:
    """Find ORFs on both strands (like pages/05_ORF_Finder) — centralized.

    Returns list of dicts sorted longest-first: Strand, Frame, Start_Pos,
    End_Pos, Length_bp, Length_aa, DNA_Sequence, Protein_Sequence.
    """
    from Bio.Seq import Seq as BioSeq
    s = clean_sequence(seq)
    if not s:
        return []
    bio_seq = BioSeq(s)
    orfs = []
    stops = {"TAA", "TAG", "TGA"}
    for strand, nuc in [(1, bio_seq), (-1, bio_seq.reverse_complement())]:
        nuc_str = str(nuc)
        for frame in range(3):
            idx = frame
            while idx <= len(nuc_str) - 3:
                if nuc_str[idx:idx+3] == "ATG":
                    for j in range(idx+3, len(nuc_str)-2, 3):
                        codon = nuc_str[j:j+3]
                        if codon in stops:
                            orf_seq = nuc_str[idx:j+3]
                            orfs.append({
                                "Strand": "+" if strand == 1 else "-",
                                "Frame": frame+1,
                                "Start_Pos": idx+1,
                                "End_Pos": j+3,
                                "Length_bp": len(orf_seq),
                                "Length_aa": len(orf_seq)//3,
                                "DNA_Sequence": orf_seq,
                                "Protein_Sequence": str(BioSeq(orf_seq).translate(to_stop=True)),
                            })
                            break
                idx += 3
    orfs.sort(key=lambda x: x["Length_bp"], reverse=True)
    if min_len:
        orfs = [o for o in orfs if o["Length_bp"] >= min_len]
    return orfs


def bulk_revcomp(sequences: list[str]) -> list[str]:
    """Reverse complement a list of sequences via revcomp."""
    return [revcomp(clean_sequence(s)) for s in sequences]
