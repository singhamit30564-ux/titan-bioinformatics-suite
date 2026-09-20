"""Unit tests for the shared UI helpers and page-level regressions."""

import pathlib

import pytest
from streamlit.testing.v1 import AppTest

from titan_utils.ui import _widget_key

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGES = ROOT / "pages"


# --------------------------------------------------------------------------
# sequence_metrics_row — used to slice characters out of the value string
# --------------------------------------------------------------------------
def test_sequence_metrics_row_unpacks_value_delta_and_help():
    """A (value, delta, help) tuple must render all three parts intact."""
    at = AppTest.from_string(
        """
import streamlit as st
from titan_utils.ui import sequence_metrics_row

sequence_metrics_row({
    "Length": ("1200 bp", "+50", "Sequence length in base pairs"),
    "GC": ("55.4 %", "-0.3", "GC content percentage"),
    "Plain": "42 bp",
})
""",
        default_timeout=30,
    ).run()

    assert not at.exception
    assert [m.label for m in at.metric] == ["Length", "GC", "Plain"]

    assert [m.value for m in at.metric] == ["1200 bp", "55.4 %", "42 bp"]
    assert [m.delta for m in at.metric] == ["+50", "-0.3", ""]
    # The regression: help used to be a stray character of the value ("0", ".").
    assert [m.help for m in at.metric] == [
        "Sequence length in base pairs",
        "GC content percentage",
        "",
    ]


def test_sequence_metrics_row_handles_empty_and_short_tuples():
    at = AppTest.from_string(
        """
from titan_utils.ui import sequence_metrics_row

sequence_metrics_row({})                       # must not raise
sequence_metrics_row({"Solo": ("7",)})         # 1-tuple
sequence_metrics_row({"Pair": ("7", "+1")})    # 2-tuple
sequence_metrics_row({"Long": ("7", "+1", "tip", "extra")})
""",
        default_timeout=30,
    ).run()

    assert not at.exception
    assert [(m.value, m.delta, m.help) for m in at.metric] == [
        ("7", "", ""),
        ("7", "+1", ""),
        ("7", "+1", "tip"),
    ]


# --------------------------------------------------------------------------
# smart_lock / widget keys — id() is recyclable and must not key a widget
# --------------------------------------------------------------------------
def test_widget_key_is_content_based_and_stable():
    same_a = _widget_key("csv", b"a,b\n1,2\n")
    same_b = _widget_key("csv", b"a,b\n1,2\n")
    other = _widget_key("csv", b"a,b\n9,9\n")

    assert same_a == same_b, "identical payloads must produce the same key"
    assert same_a != other, "different payloads must produce different keys"
    assert _widget_key("pdf", b"x") != _widget_key("csv", b"x")
    assert _widget_key("csv", None) != _widget_key("csv", b"")


def test_widget_key_survives_garbage_collection():
    """CPython reuses id() after GC, so two equal payloads can share an id."""
    ids = []
    for _ in range(50):
        payload = b"col\n" + b"1\n" * 100
        ids.append(id(payload))
        del payload

    assert len(set(ids)) < len(ids), "precondition: ids really are recycled"
    # ...yet the widget key stays identical, because it hashes content, not id().
    assert len({_widget_key("csv", b"col\n" + b"1\n" * 100) for _ in range(50)}) == 1


def test_two_exports_on_one_page_do_not_collide():
    at = AppTest.from_string(
        """
import pandas as pd
import streamlit as st
from titan_utils.ui import smart_lock
from titan_utils import df_to_csv_bytes

smart_lock(df_to_csv_bytes(pd.DataFrame({"A": [1, 2]})), "first.csv")
smart_lock(df_to_csv_bytes(pd.DataFrame({"B": ["x"]})), "second.csv")
""",
        default_timeout=30,
    ).run()

    # A duplicate widget key aborts the run with DuplicateWidgetID.
    assert not at.exception
    assert len(at.get("download_button")) == 2


# --------------------------------------------------------------------------
# Static guard: APIs removed from our dependency floors
# --------------------------------------------------------------------------
def test_no_removed_pandas_styler_applymap():
    """Styler.applymap was removed in pandas 2.1 (requirements floor: 2.2)."""
    offenders = sorted(p.name for p in PAGES.glob("*.py") if ".style.applymap(" in p.read_text())
    assert not offenders, f"use Styler.map instead — found in: {offenders}"


# --------------------------------------------------------------------------
# pI page — must report a real isoelectric point, not a residue-count guess
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "sequence,expected_pi,expected_word",
    [
        ("MRSLLILVLCFLPAALG", 8.00, "Basic"),
        # Poly-alanine has no ionizable side chains; the old count-based
        # "heuristic" called it neutral, but its real pI is ~5.57 (acidic).
        ("AAAAAAAA", 5.57, "Acidic"),
    ],
)
def test_pi_page_reports_real_isoelectric_point(sequence, expected_pi, expected_word):
    at = AppTest.from_file(str(PAGES / "16_Protein_pI_Estimator.py"), default_timeout=90)
    at.run()
    at.text_area[0].set_value(sequence)
    at.button[0].click()
    at.run()

    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]

    metrics = {m.label: m.value for m in at.metric}
    assert "Estimated pI" in metrics, f"no pI reported — got {metrics}"
    assert float(metrics["Estimated pI"]) == pytest.approx(expected_pi, abs=0.05)

    # The verdict is rendered through st.success / st.warning / st.info.
    rendered = " ".join(
        element.value
        for kind in ("markdown", "success", "warning", "info", "caption")
        for element in at.get(kind)
    )
    assert expected_word in rendered, f"expected a {expected_word} verdict, got: {rendered[:200]}"
