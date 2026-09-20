"""Reusable Streamlit UI fragments: header, export, Dr. Titan tip."""

from __future__ import annotations

import hashlib

import streamlit as st

from .theme import TITAN_THEME_CSS


def _widget_key(prefix: str, payload: bytes | None, discriminant: str = "") -> str:
    """Build a deterministic widget key from the payload's *content*.

    ``id()`` must never be used as a widget key: CPython only guarantees that
    an id is unique for the object's lifetime and recycles the address once the
    object is garbage-collected (verified: 1999/2000 create/destroy cycles reuse
    the same address). A recycled id can collide with a still-registered widget
    key and raise ``DuplicateWidgetID``. Hashing the content keeps the key
    stable across reruns *and* distinct between different exports.
    """
    digest = hashlib.sha1(payload).hexdigest()[:12] if payload is not None else "none"
    basis = f"{discriminant}|{digest}"
    return f"_{prefix}_{hashlib.sha1(basis.encode('utf-8')).hexdigest()[:12]}"


def apply_theme() -> None:
    """Inject the Titan CSS. Safe to call multiple times."""
    st.markdown(TITAN_THEME_CSS, unsafe_allow_html=True)


def titan_title(emoji: str, title: str, subtitle: str = "") -> None:
    """Render a consistent page header (emoji + bold title + divider)."""
    apply_theme()
    st.markdown(f"# {emoji} {title}")
    if subtitle:
        st.markdown(subtitle)
    st.markdown("---")


def smart_lock(csv_data: bytes | None = None,
               csv_filename: str = "titan_results.csv",
               pdf_label: str = "📄 Download PDF Report (Free)",
               key: str | None = None) -> None:
    """Render the export row — **fully free**, no paywall.

    - PDF button shows a friendly "use Print → Save as PDF" tip (v1.1 placeholder).
    - If csv_data is provided, a working CSV download button is shown.
    - If csv_data is None, show an info note instead of a fake gated button.

    ``key`` disambiguates the widget keys when the *same* payload is exported
    twice on one page (e.g. two tables with identical content).
    """
    st.markdown("---")
    st.markdown("### 📥 Export Results")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(pdf_label, use_container_width=True,
                     key=key or _widget_key("pdf", csv_data, pdf_label)):
            st.info("📄 PDF report generation is planned for v1.1. "
                    "For now use your browser's Print → Save as PDF, or use "
                    "the CSV export below.")
    with c2:
        if csv_data is not None:
            st.download_button(
                "📊 Download CSV (Free)",
                data=csv_data,
                file_name=csv_filename,
                mime="text/csv",
                use_container_width=True,
                key=key or _widget_key("csv", csv_data, csv_filename),
            )
        else:
            st.caption("ℹ️ Run an analysis above to enable CSV export — no paywall, all exports are free.")


def dr_titan_tip(text: str) -> None:
    """Render a consistent 'Dr. Titan' educational tip."""
    st.markdown("---")
    st.info(f"💡 **Dr. Titan's Tip:** {text}")


def sequence_metrics_row(metrics: dict) -> None:
    """Render a row of `st.metric` cards from a dict of label→value.

    Values may be a plain value or a ``(value, delta[, help])`` tuple/list.
    """
    if not metrics:
        return
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        delta = None
        help_text = None
        if isinstance(value, (tuple, list)):
            # NB: unpack in one step — reading elements off the *rebound* value
            # would slice characters out of value[0] instead of the tuple.
            value, delta, help_text = (list(value) + [None, None])[:3]
        col.metric(label, value, delta=delta, help=help_text)
