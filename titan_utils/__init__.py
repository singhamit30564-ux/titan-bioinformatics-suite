"""Titan Bioinformatics Suite — shared utilities.

This package centralises the boilerplate that was copy-pasted across ~30
page files (sequence cleaning/validation, theme constants, the "Smart Lock"
paywall stub, Dr. Titan tip footer, I/O helpers, codon tables).
"""
from .sequence import (
    clean_sequence,
    validate_dna,
    validate_rna,
    validate_protein,
    revcomp,
    gc_fraction_safe,
    CODON_TABLE_STANDARD,
    REVERSE_CODON_TABLE_STANDARD,
    translate,
    ALLOWED_DNA,
    ALLOWED_DNA_IUPAC,
)
from .theme import TITAN_THEME_CSS, THEME
from .ui import smart_lock, dr_titan_tip, titan_title, sequence_metrics_row
from .io import safe_csv_download, safe_fasta_download

__all__ = [
    "clean_sequence",
    "validate_dna",
    "validate_rna",
    "validate_protein",
    "revcomp",
    "gc_fraction_safe",
    "CODON_TABLE_STANDARD",
    "REVERSE_CODON_TABLE_STANDARD",
    "translate",
    "ALLOWED_DNA",
    "ALLOWED_DNA_IUPAC",
    "TITAN_THEME_CSS",
    "THEME",
    "smart_lock",
    "dr_titan_tip",
    "titan_title",
    "sequence_metrics_row",
    "safe_csv_download",
    "safe_fasta_download",
]
