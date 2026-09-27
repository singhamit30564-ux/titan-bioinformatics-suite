"""Scientific PDF report generation (ReportLab) for the Titan suite.

Produces clean, publication-grade documents entirely in RAM:

* Title block with suite branding and generation timestamp
* Numbered sections with headings, body copy, bullet lists
* Scientific tables (grid rules, header band, alternating rows)
* Monospace blocks for sequences / manifests
* Running header + "Page X of Y" footer, gold accent rules

All strings are sanitised to WinAnsi-safe text so emoji-heavy Streamlit copy
degrades gracefully instead of crashing the layout engine.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional, Sequence, Tuple
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

__all__ = [
    "PdfSection",
    "PdfReportSpec",
    "build_pdf_report",
    "build_simple_pdf",
    "pdf_safe_text",
    "TITAN_GOLD",
]

TITAN_GOLD = colors.HexColor("#d4af37")
TITAN_NAVY = colors.HexColor("#0a0e17")
TITAN_INK = colors.HexColor("#1c2430")
TITAN_MUTED = colors.HexColor("#5a6a7d")
TITAN_ROW_ALT = colors.HexColor("#f2f4f7")

_CHAR_MAP = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "--", "\u2026": "...", "\u00a0": " ",
    "\u2192": "->", "\u2190": "<-", "\u2194": "<->", "\u2022": "*",
}


def pdf_safe_text(text: Any) -> str:
    """Coerce arbitrary UI text to ReportLab-safe WinAnsi markup text."""
    s = "" if text is None else str(text)
    for src, dst in _CHAR_MAP.items():
        s = s.replace(src, dst)
    # Drop remaining characters outside Latin-1 (emoji, CJK, …).
    s = "".join(ch if (32 <= ord(ch) < 127) or (160 <= ord(ch) <= 255) else "" for ch in s)
    # Collapse runs of whitespace introduced by drops, keep newlines.
    out_lines = []
    for line in s.splitlines():
        while "  " in line:
            line = line.replace("  ", " ")
        out_lines.append(line.rstrip())
    return "\n".join(out_lines).strip()


def _para(text: Any, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(pdf_safe_text(text)).replace("\n", "<br/>"), style)


@dataclass
class PdfSection:
    """One logical block of the report."""

    heading: str = ""
    paragraphs: Sequence[str] = field(default_factory=list)
    bullets: Sequence[str] = field(default_factory=list)
    table: Optional[Tuple[Sequence[str], Sequence[Sequence[Any]]]] = None
    preformatted: str = ""
    style: str = "normal"  # "normal" | "compact"


@dataclass
class PdfReportSpec:
    """Full document specification for :func:`build_pdf_report`."""

    title: str
    subtitle: str = ""
    author: str = "Titan Bioinformatics Suite"
    sections: Sequence[PdfSection] = field(default_factory=list)
    footer_note: str = "Generated in-RAM under the Titan Zero Data Retention policy."
    generated_utc: str = ""

    def timestamp(self) -> str:
        return self.generated_utc or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitanTitle", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=19, leading=23, textColor=TITAN_INK, alignment=TA_CENTER, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "TitanSubtitle", parent=base["Normal"], fontName="Helvetica",
            fontSize=10.5, leading=14, textColor=TITAN_MUTED, alignment=TA_CENTER,
        ),
        "meta": ParagraphStyle(
            "TitanMeta", parent=base["Normal"], fontName="Helvetica",
            fontSize=8.5, leading=11, textColor=TITAN_MUTED, alignment=TA_CENTER,
        ),
        "h2": ParagraphStyle(
            "TitanH2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=12.5, leading=15, textColor=TITAN_INK,
            spaceBefore=10, spaceAfter=4, borderPadding=2,
        ),
        "body": ParagraphStyle(
            "TitanBody", parent=base["Normal"], fontName="Times-Roman",
            fontSize=10, leading=13.5, textColor=TITAN_INK,
            alignment=TA_JUSTIFY, spaceAfter=4,
        ),
        "compact": ParagraphStyle(
            "TitanCompact", parent=base["Normal"], fontName="Times-Roman",
            fontSize=8.6, leading=11, textColor=TITAN_INK, spaceAfter=2,
        ),
        "bullet": ParagraphStyle(
            "TitanBullet", parent=base["Normal"], fontName="Times-Roman",
            fontSize=9.6, leading=12.5, textColor=TITAN_INK,
            leftIndent=10, bulletIndent=2, spaceAfter=1.5,
        ),
        "mono": ParagraphStyle(
            "TitanMono", parent=base["Code"], fontName="Courier",
            fontSize=7.8, leading=9.6, textColor=TITAN_INK,
        ),
    }


def _table_flow(header: Sequence[str], rows: Sequence[Sequence[Any]], styles: dict, compact: bool = False):
    data = [[_para(c, styles["compact"]) for c in header]]
    for row in rows:
        data.append([_para(c, styles["compact"] if compact else styles["bullet"]) for c in row])
    col_count = max(len(header), 1)
    tbl = Table(data, repeatRows=1, hAlign="LEFT")
    rules = [
        ("BACKGROUND", (0, 0), (-1, 0), TITAN_GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), TITAN_NAVY),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8.4),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9c2cc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]
    for r in range(1, len(data)):
        if r % 2 == 0:
            rules.append(("BACKGROUND", (0, r), (-1, r), TITAN_ROW_ALT))
    tbl.setStyle(TableStyle(rules))
    del col_count
    return tbl


def _header_footer(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    # Running header
    canvas.setStrokeColor(TITAN_GOLD)
    canvas.setLineWidth(1.1)
    canvas.line(18 * mm, height - 14 * mm, width - 18 * mm, height - 14 * mm)
    canvas.setFont("Helvetica", 7.6)
    canvas.setFillColor(TITAN_MUTED)
    canvas.drawString(18 * mm, height - 12 * mm, "TITAN BIOINFORMATICS SUITE")
    canvas.drawRightString(width - 18 * mm, height - 12 * mm, "Scientific Report")
    # Footer
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 13.5 * mm, width - 18 * mm, 13.5 * mm)
    canvas.setFont("Helvetica", 7.4)
    canvas.drawString(18 * mm, 10 * mm, "Zero Data Retention - ephemeral in-RAM computation")
    canvas.drawRightString(width - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf_report(spec: PdfReportSpec) -> bytes:
    """Render a full scientific report and return PDF bytes (in RAM only)."""
    styles = _styles()
    story: List[Any] = []

    story.append(Spacer(1, 6))
    story.append(_para(spec.title, styles["title"]))
    if spec.subtitle:
        story.append(_para(spec.subtitle, styles["subtitle"]))
    story.append(Spacer(1, 2))
    story.append(_para(f"{pdf_safe_text(spec.author)}  |  Generated: {spec.timestamp()}", styles["meta"]))
    story.append(Spacer(1, 7))

    for idx, section in enumerate(spec.sections, start=1):
        if section.heading:
            story.append(_para(f"{idx}. {section.heading}", styles["h2"]))
        body_style = styles["compact"] if section.style == "compact" else styles["body"]
        for p in section.paragraphs:
            story.append(_para(p, body_style))
        for b in section.bullets:
            story.append(_para(f"* {b}", styles["bullet"]))
        if section.table is not None:
            header, rows = section.table
            if header or rows:
                story.append(Spacer(1, 2))
                story.append(_table_flow(header, rows, styles, compact=section.style == "compact"))
                story.append(Spacer(1, 3))
        if section.preformatted:
            safe_block = pdf_safe_text(section.preformatted)
            story.append(Spacer(1, 2))
            story.append(Preformatted(safe_block[:20000], styles["mono"]))

    if spec.footer_note:
        story.append(Spacer(1, 8))
        story.append(_para(pdf_safe_text(spec.footer_note), styles["meta"]))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=17 * mm,
        title=pdf_safe_text(spec.title),
        author=pdf_safe_text(spec.author),
        subject="Titan Bioinformatics Suite report",
    )
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()


def build_simple_pdf(title: str, body: str, subtitle: str = "") -> bytes:
    """One-section convenience report (used by generic export buttons)."""
    spec = PdfReportSpec(
        title=title,
        subtitle=subtitle or "Titan Bioinformatics Suite - Analysis Report",
        sections=[PdfSection(heading="Results Summary", paragraphs=[p for p in body.split("\n\n") if p.strip()] or [body])],
    )
    return build_pdf_report(spec)
