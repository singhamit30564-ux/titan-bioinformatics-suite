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


def test_master_registry_completeness():
    from titan_utils.registry import get_all_tools, get_tool_by_id, search_tools, CATEGORIES
    tools = get_all_tools()
    assert len(tools) == 260, f"expected 260 tools in registry, got {len(tools)}"
    assert len(CATEGORIES) == 15, f"expected 15 categories, got {len(CATEGORIES)}"
    
    # Check bounds
    assert get_tool_by_id(1) is not None
    assert get_tool_by_id(260) is not None
    assert get_tool_by_id(261) is None

    # Search check
    crispr_hits = search_tools("CRISPR")
    assert len(crispr_hits) >= 3


def test_dr_titan_ai_student_tutor():
    from titan_tools.student_tutor import tool_dr_titan_ai_student_tutor
    res_en = tool_dr_titan_ai_student_tutor(topic="Central Dogma", language="English")
    assert "Central Dogma" in res_en.title
    assert res_en.dataframe is not None
    assert len(res_en.metrics) >= 3

    res_hi = tool_dr_titan_ai_student_tutor(topic="CRISPR-Cas9", language="Hinglish")
    assert res_hi.figure is not None
    assert len(res_hi.notes) >= 3


def test_domain_representative_tools_execute():
    import titan_tools as tt
    
    # Sample from each domain
    agri_res = tt.tool_chloroplast_ir_junction_mapper()
    assert "Chloroplast" in agri_res.title
    
    marine_res = tt.tool_coral_bleaching_stress()
    assert "Coral" in marine_res.title

    clin_res = tt.tool_acmg_pathogenicity_classifier()
    assert "ACMG" in clin_res.title

    meta_res = tt.tool_alpha_diversity_estimator()
    assert "Alpha Diversity" in meta_res.title

    struct_res = tt.tool_ramachandran_validator()
    assert "Ramachandran" in struct_res.title

    epi_res = tt.tool_bisulfite_conversion_rate()
    assert "Bisulfite" in epi_res.title

    syn_res = tt.tool_golden_gate_fidelity()
    assert "Golden Gate" in syn_res.title

    pop_res = tt.tool_hardy_weinberg_exact()
    assert "Hardy-Weinberg" in pop_res.title

    ncbi_res = tt.tool_ncbi_nucleotide_fetch()
    assert "NCBI" in ncbi_res.title

    copilot_res = tt.tool_dr_titan_eli5_generator()
    assert "Explain Like I'm 5" in copilot_res.title or "ELI5" in copilot_res.title

