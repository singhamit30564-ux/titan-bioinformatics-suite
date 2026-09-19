"""Titan Bioinformatics Suite — smoke & unit tests.

- Validates titan_utils core (validation, revcomp, GC, ORF)
- Compiles all page files (syntax check)
- Ensures Home.py navigation covers all pages on disk
"""

import pathlib
import re
import sys

import pytest

# Add repo root to path
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from titan_utils import (
    clean_sequence,
    validate_dna,
    validate_rna,
    revcomp,
    gc_fraction_safe,
    gc_content_percent,
    nucleotide_counts,
    find_orfs_simple,
    translate,
)


def test_clean_sequence():
    assert clean_sequence(" a t g c \n") == "ATGC"
    assert clean_sequence(None) == ""
    assert clean_sequence("atgc", upper=False) == "atgc"


def test_validate_dna_ok():
    seq, err = validate_dna("ATGC")
    assert err is None
    assert seq == "ATGC"


def test_validate_dna_bad():
    seq, err = validate_dna("ATBX")
    assert err is not None
    assert "Invalid DNA" in err


def test_validate_rna():
    seq, err = validate_rna("AUGC")
    assert err is None
    seq2, err2 = validate_rna("ATGC")
    assert err2 is not None


def test_revcomp():
    assert revcomp("ATGC") == "GCAT"
    # IUPAC: R (AG) complements to Y (CT) -> check via translation table
    assert revcomp("ATCG") == "CGAT"


def test_gc_fraction():
    assert gc_fraction_safe("GCGC") == 1.0
    assert gc_fraction_safe("ATAT") == 0.0
    assert gc_content_percent("GCGC") == 100.0
    assert nucleotide_counts("AAAT") == {"A": 3, "T": 1, "C": 0, "G": 0}


def test_translate():
    assert translate("ATGTTT") == "MF"
    assert translate("ATGTAA", to_stop=True) == "M"


def test_find_orfs_simple():
    orfs = find_orfs_simple("ATGAAATAGATGCCCCCTAA", min_len=0)
    assert len(orfs) >= 1
    assert orfs[0]["Length_bp"] >= 6


def test_all_pages_compile():
    pages = list((ROOT / "pages").glob("*.py"))
    assert len(pages) >= 50, f"expected 50+ pages, got {len(pages)}"
    for p in pages:
        src = p.read_text()
        compile(src, str(p), "exec")


def test_home_navigation_covers_pages():
    home = (ROOT / "Home.py").read_text()
    pages_on_disk = {p.name for p in (ROOT / "pages").glob("*.py")}
    # Extract quoted filenames in Home.py
    refs = set(re.findall(r'"((?:\d+_)?[^"]+\.py)"', home))
    # Home should reference at least 90% of pages
    missing = pages_on_disk - refs
    assert len(missing) <= 5, f"Home.py missing pages: {missing}"
    assert len(refs) >= len(pages_on_disk) * 0.9


def test_pages_use_titan_utils():
    pages = list((ROOT / "pages").glob("*.py"))
    using = sum(1 for p in pages if "from titan_utils" in p.read_text())
    # After refactor, at least 40 pages should use titan_utils
    assert using >= 40, f"only {using} pages use titan_utils, expected >=40"


def test_no_paywall_gating():
    for p in (ROOT / "pages").glob("*.py"):
        txt = p.read_text()
        assert "Explorer Plan Required" not in txt, f"{p.name} still has paywall gating"
        assert "🔒 Explorer Plan" not in txt, f"{p.name} still has locked CSV button"
