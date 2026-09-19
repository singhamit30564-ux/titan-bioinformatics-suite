"""Reusable Streamlit UI fragments: header, paywall stub, Dr. Titan tip."""
from __future__ import annotations

import streamlit as st

from .theme import TITAN_THEME_CSS


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
               pdf_label: str = "📄 Download PDF Report (Free)") -> None:
    """Render the export row.

    The PDF button still produces an "in development" notice (PDF generation
    is listed as v1.1 in the masterplan). When `csv_data` is provided, a
    working CSV download button is rendered instead of the fake gating.
    """
    st.markdown("---")
    st.markdown("### 📥 Export Results")
    c1, c2 = st.columns(2)
    with c1:
        if st.button(pdf_label, use_container_width=True, key=f"_pdf_{id(csv_data)}"):
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
                key=f"_csv_{id(csv_data)}",
            )
        else:
            if st.button("📊 Download CSV (🔒 Explorer Plan)",
                         use_container_width=True,
                         key=f"_csvgate_{id(csv_data)}"):
                st.warning(
                    "🔒 **Titan Explorer Plan Required.** "
                    "Upgrade to unlock CSV exports, batch processing, "
                    "and advanced analytics."
                )


def dr_titan_tip(text: str) -> None:
    """Render a consistent 'Dr. Titan' educational tip."""
    st.markdown("---")
    st.info(f"💡 **Dr. Titan's Tip:** {text}")


def sequence_metrics_row(metrics: dict) -> None:
    """Render a row of `st.metric` cards from a dict of label→value."""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        delta = None
        help_text = None
        if isinstance(value, (tuple, list)):
            value, delta = value[0], value[1] if len(value) > 1 else None
            help_text = value[2] if len(value) > 2 else None
        col.metric(label, value, delta=delta, help=help_text)
