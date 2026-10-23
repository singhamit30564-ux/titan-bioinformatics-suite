"""Interaction smoke tests — every page must work when a user *uses* it.

The pre-existing suite only compiled the pages (``py_compile``), which cannot
catch runtime errors such as a missing ``import math``, a removed pandas/plotly
API, or a typo in a column name. These tests actually render every page with
``streamlit.testing`` and click every button, so a broken tool fails CI instead
of failing silently in front of a user.

Both failure modes are treated as failures:

* an **uncaught exception** (Streamlit's red traceback), and
* an **error banner** (``st.error``) — several pages wrap their body in a broad
  ``try/except Exception`` and report "Calculation Error: ...", which hides the
  real problem while still leaving the user with no results.
"""

import pathlib
import re
import subprocess
import sys

import pytest
from streamlit.testing.v1 import AppTest

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = sorted((ROOT / "pages").glob("*.py"))
PAGE_IDS = [p.name for p in PAGES]

RENDER_TIMEOUT = 90
CLICK_TIMEOUT = 300


def _fresh(page: pathlib.Path, timeout: int) -> AppTest:
    at = AppTest.from_file(str(page), default_timeout=timeout)
    at.run()
    return at


def _problems(at: AppTest) -> list[str]:
    """Collect uncaught exceptions and error banners from a script run."""
    found = []
    for exc in at.exception:
        found.append(f"uncaught exception: {exc.value}")
    for err in at.error:
        found.append(f"error banner: {err.value}")
    return found


def test_pages_were_discovered():
    """Guard against the glob silently matching nothing."""
    assert len(PAGES) >= 50, f"expected 50+ pages, found {len(PAGES)}"


def test_home_entrypoint_renders_cleanly():
    """The Streamlit entrypoint (and its st.navigation wiring) must load."""
    at = AppTest.from_file(str(ROOT / "Home.py"), default_timeout=RENDER_TIMEOUT).run()
    assert not _problems(at), _problems(at)
    assert at.title, "Home.py rendered no title"


def test_home_navigation_covers_every_page():
    """A page that exists on disk but is missing from the nav is invisible."""
    registered = set(re.findall(r'"(\d+_[^"]+\.py)"', (ROOT / "Home.py").read_text()))
    on_disk = {p.name for p in PAGES}

    assert not on_disk - registered, f"not reachable from Home.py nav: {sorted(on_disk - registered)}"
    assert not registered - on_disk, f"nav points at missing files: {sorted(registered - on_disk)}"


def test_no_undefined_names():
    """Static guard for missing imports and shadowed definitions.

    Runtime tests only catch a broken code path when a user actually reaches it
    (e.g. the missing ``import math`` on the Tm page survived a render-only
    suite). pyflakes flags that class of bug statically.
    """
    targets = [str(p) for p in PAGES]
    targets += [str(ROOT / "Home.py"), str(ROOT / "conftest.py")]
    targets += sorted(str(p) for p in (ROOT / "titan_utils").glob("*.py"))

    proc = subprocess.run(
        [sys.executable, "-m", "pyflakes", *targets],
        capture_output=True, text=True,
    )
    if "No module named" in proc.stderr:
        pytest.skip("pyflakes is not installed")

    dangerous = [
        line for line in proc.stdout.splitlines()
        if "undefined name" in line or "redefinition" in line
    ]
    assert not dangerous, "pyflakes found undefined or shadowed names:\n  " + "\n  ".join(dangerous)


@pytest.mark.parametrize("page", PAGES, ids=PAGE_IDS)
def test_page_renders_cleanly(page: pathlib.Path):
    at = _fresh(page, RENDER_TIMEOUT)
    problems = _problems(at)
    assert not problems, f"{page.name} failed to render:\n  " + "\n  ".join(problems)


@pytest.mark.parametrize("page", PAGES, ids=PAGE_IDS)
def test_every_button_runs_cleanly(page: pathlib.Path):
    """Click each button on its own fresh run and assert nothing breaks.

    The page ships working defaults for every input, so a successful click must
    produce results — not an error, and not a half-rendered page.
    """
    labels = [b.label for b in _fresh(page, RENDER_TIMEOUT).button]
    if not labels:
        pytest.skip(f"{page.name} has no buttons")

    failures = []
    for index, label in enumerate(labels):
        at = _fresh(page, RENDER_TIMEOUT)
        at.button[index].click().run(timeout=CLICK_TIMEOUT)
        problems = _problems(at)
        if problems:
            failures.append(f"button {label!r}:\n    " + "\n    ".join(problems))

    assert not failures, f"{page.name} broke on click:\n  " + "\n  ".join(failures)


# ─────────────────────────────────────────────────────────────────────────────
# Pro Engine additions (Layer A/B): pages 98/99/100 + console tools 261–265
# ─────────────────────────────────────────────────────────────────────────────

PRO_PAGES = ["98_Differential_Expression.py", "99_Variant_ML.py", "100_Expression_Explorer.py"]

PRO_PRIMARY_BUTTONS = {
    "98_Differential_Expression.py": "🧬 Run Differential Expression",
    "99_Variant_ML.py": "🧪 Train on SYNTHETIC dataset",
    "100_Expression_Explorer.py": "🧭 Run PCA & Clustering",
}


def test_pro_engine_pages_are_discovered():
    """The Layer B pages must be in the auto-glob, not just on disk."""
    for name in PRO_PAGES:
        assert name in PAGE_IDS, f"{name} missing from page discovery"


@pytest.mark.parametrize("page_name", PRO_PAGES)
def test_pro_page_primary_action_runs_cleanly(page_name: str):
    """Click the main analysis button and assert a clean happy path (no
    st.error banners on success — export buttons are no-ops on fresh state)."""
    page = ROOT / "pages" / page_name
    label = PRO_PRIMARY_BUTTONS[page_name]
    at = _fresh(page, RENDER_TIMEOUT)
    matching = [b for b in at.button if b.label == label]
    assert matching, f"{page_name}: primary button {label!r} not found"
    at.button[[b.label for b in at.button].index(label)].click().run(timeout=CLICK_TIMEOUT)
    assert not _problems(at), f"{page_name} broke on {label!r}:\n  " + "\n  ".join(_problems(at))


def test_pro_tool_handlers_return_toolresults():
    """Console tools 261–265 must produce the shared ToolResult contract."""
    from titan_tools.common import ToolResult
    from titan_tools.pro import (
        tool_pro_bam_stats,
        tool_pro_differential_expression,
        tool_pro_fast_qc,
        tool_pro_fast_vcf,
        tool_pro_variant_ml,
    )

    tiny_fastq = "@r1\nACGTACGTACGTACGTACGT\n+\nIIIIIIIIIIIIIIIIIIII\n"
    tiny_vcf = (
        "##fileformat=VCFv4.2\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        "chr1\t100\trs1\tA\tG\t50\tPASS\tAF=0.001;Consequence=frameshift_variant\n"
    )
    tiny_sam = (
        "@HD\tVN:1.6\tSO:unsorted\n"
        "@SQ\tSN:chr1\tLN:1000\n"
        "read1\t0\tchr1\t100\t60\t4M\t*\t0\t0\tACGT\tIIII\n"
    )
    counts_csv = "gene,s1,s2,s3,s4\ngeneA,100,120,400,420\ngeneB,200,210,50,60\n"
    meta_csv = "sample,condition\ns1,control\ns2,control\ns3,treated\ns4,treated\n"

    results = {
        "fast_qc": tool_pro_fast_qc(fastq_data=tiny_fastq, k=8),
        "fast_vcf": tool_pro_fast_vcf(vcf_data=tiny_vcf),
        "bam_stats": tool_pro_bam_stats(sam_data=tiny_sam),
        "de": tool_pro_differential_expression(counts_data=counts_csv, metadata=meta_csv),
        "variant_ml": tool_pro_variant_ml(n_synthetic=300),
    }
    for name, res in results.items():
        assert isinstance(res, ToolResult), name
        assert res.title and res.summary, name
        assert res.extra_data.get("engine_stats", {}).get("engine"), f"{name} missing engine_stats"
