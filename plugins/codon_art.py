"""Codon Art — Example Titan Plugin.

Converts a short text into a DNA-like sequence by mapping each letter
to a codon, then renders it as ASCII art.
"""
PLUGIN_NAME = "Codon Art"
PLUGIN_DESCRIPTION = "Convert text into DNA-codon art sequences."
PLUGIN_AUTHOR = "Titan Community"

_CODON_MAP = {
    "a": "GCT", "b": "TGA", "c": "TGT", "d": "GAT", "e": "GAA",
    "f": "TTT", "g": "GGT", "h": "CAT", "i": "ATT", "j": "ATA",
    "k": "AAA", "l": "CTT", "m": "ATG", "n": "AAT", "o": "TAA",
    "p": "CCT", "q": "CAA", "r": "CGT", "s": "TCT", "t": "ACT",
    "u": "GTT", "v": "GTT", "w": "TGG", "x": "TAG", "y": "TAT",
    "z": "TCA", " ": " - ", ".": "...", "!": "!!!",
}


def text_to_codons(text: str) -> str:
    """Convert *text* to a triple-codon DNA string."""
    return " ".join(_CODON_MAP.get(ch.lower(), "???") for ch in text)


def run(text: str = "HELLO TITAN") -> str:
    """Return codon-art string for the given *text*."""
    codons = text_to_codons(text)
    header = "5'- " + codons + " -3'"
    bar = "─" * len(header)
    return f"╔{bar}╗\n║ {header} ║\n╚{bar}╝"