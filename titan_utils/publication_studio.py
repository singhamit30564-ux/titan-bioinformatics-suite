"""Publication Studio — journal styling + Okabe-Ito colorblind-safe palettes.

* **Journal styles**: Nature, Science, Cell — typography, sizing, layout and
  color rules applied to Plotly figures (and exportable as matplotlib rcParams).
* **Okabe-Ito palette**: the canonical 8-color colorblind-safe scheme,
  ordered for maximum discriminability (Okabe & Ito, 2008).
* Figure restyling helpers that keep the Titan dark theme for interactive
  views while providing print-ready white-background journal variants.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

__all__ = [
    "OKABE_ITO",
    "OKABE_ITO_ORDER",
    "okabe_ito_palette",
    "okabe_ito_pairs",
    "JOURNAL_STYLES",
    "list_journals",
    "journal_style",
    "apply_journal_style",
    "mpl_rc_params",
    "publication_figure_html",
    "FIGURE_DPI",
]

# ─────────────────────────────────────────────────────────────────────────────
# Okabe-Ito colorblind-safe palette (Okabe & Ito, "Color Universal Design")
# ─────────────────────────────────────────────────────────────────────────────

OKABE_ITO: Dict[str, str] = {
    "black": "#000000",
    "orange": "#E69F00",
    "skyblue": "#56B4E9",
    "bluishgreen": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "reddishpurple": "#CC79A7",
}

# Discriminability-first ordering (adjacent entries stay distinguishable for
# deuteranopia, protanopia and tritanopia).
OKABE_ITO_ORDER: Tuple[str, ...] = (
    "orange",
    "skyblue",
    "bluishgreen",
    "vermillion",
    "reddishpurple",
    "yellow",
    "blue",
    "black",
)

FIGURE_DPI = 300


def okabe_ito_palette(n: int = 8) -> List[str]:
    """First ``n`` Okabe-Ito hex colors in discriminability order (cycles if n > 8)."""
    order = [OKABE_ITO[k] for k in OKABE_ITO_ORDER]
    if n <= 0:
        return []
    return [order[i % len(order)] for i in range(n)]


def okabe_ito_pairs(n: int = 8) -> List[Tuple[str, str]]:
    """(name, hex) pairs — handy for legends and accessibility audits."""
    keys = list(OKABE_ITO_ORDER)[:n] if n <= 8 else [OKABE_ITO_ORDER[i % 8] for i in range(n)]
    return [(k, OKABE_ITO[k]) for k in keys]


# ─────────────────────────────────────────────────────────────────────────────
# Journal styles
# ─────────────────────────────────────────────────────────────────────────────

JOURNAL_STYLES: Dict[str, Dict[str, Any]] = {
    "Nature": {
        "label": "Nature",
        "font_body": "Times New Roman, Times, serif",
        "font_heading": "Arial, Helvetica, sans-serif",
        "base_size": 9,
        "heading_size": 11,
        "line_width": 1.2,
        "marker_size": 6,
        "column": "double",
        "aspect": 1.2,
        "background": "#ffffff",
        "grid": "#cccccc",
        "palette": okabe_ito_palette(8),
        "description": (
            "Nature: serif body text, clean single-axis frames, restrained "
            "grids, 300 dpi figures, Arial panel letters (a, b, c)."
        ),
        "rules": [
            "Sans-serif axis labels at 7-9 pt equivalent.",
            "No chart borders; keep left + bottom spines only.",
            "One hue family per panel; Okabe-Ito for categorical series.",
        ],
    },
    "Science": {
        "label": "Science",
        "font_body": "Times New Roman, Times, serif",
        "font_heading": "Helvetica, Arial, sans-serif",
        "base_size": 9,
        "heading_size": 12,
        "line_width": 1.4,
        "marker_size": 7,
        "column": "double",
        "aspect": 1.0,
        "background": "#ffffff",
        "grid": "#e0e0e0",
        "palette": okabe_ito_palette(8),
        "description": (
            "Science: serif typography, bold sans headings, high-contrast "
            "lines, generous whitespace, explicit units on all axes."
        ),
        "rules": [
            "Explicit SI units in every axis title.",
            "Legend inside the plot area when space allows.",
            "Grayscale-readable: vary marker + dash as well as hue.",
        ],
    },
    "Cell": {
        "label": "Cell",
        "font_body": "Helvetica, Arial, sans-serif",
        "font_heading": "Helvetica, Arial, sans-serif",
        "base_size": 8,
        "heading_size": 10,
        "line_width": 1.0,
        "marker_size": 5,
        "column": "single",
        "aspect": 1.5,
        "background": "#ffffff",
        "grid": "#dddddd",
        "palette": okabe_ito_palette(8),
        "description": (
            "Cell: sans-serif throughout, compact line weights, dense "
            "information design, soft-gray dashed guides."
        ),
        "rules": [
            "Compact type with tight leading.",
            "Dashed gray gridlines; no heavy frames.",
            "Colorblind-safe fills (Okabe-Ito) for stacked panels.",
        ],
    },
}


def list_journals() -> List[str]:
    """Journal names supported by the studio."""
    return list(JOURNAL_STYLES.keys())


def journal_style(journal: str = "Nature") -> Dict[str, Any]:
    """Look up a journal style dictionary (falls back to Nature)."""
    return JOURNAL_STYLES.get(journal, JOURNAL_STYLES["Nature"])


# ─────────────────────────────────────────────────────────────────────────────
# Plotly restyling
# ─────────────────────────────────────────────────────────────────────────────

def apply_journal_style(fig, journal: str = "Nature", title: str = ""):
    """Restyle a Plotly figure to a print-ready journal look (white bg)."""
    style = journal_style(journal)
    colors = style["palette"]
    fig.update_layout(
        title=dict(
            text=title or getattr(fig.layout.title, "text", "") or "",
            font=dict(family=style["font_heading"], size=style["heading_size"] + 2),
        ),
        paper_bgcolor=style["background"],
        plot_bgcolor=style["background"],
        font=dict(family=style["font_body"], size=style["base_size"] + 1),
        legend=dict(
            font=dict(family=style["font_body"], size=style["base_size"]),
            bgcolor="rgba(255,255,255,0.6)",
        ),
        margin=dict(l=60, r=20, t=50 if (title or getattr(fig.layout.title, "text", "")) else 20, b=50),
    )
    axis_style = dict(
        showgrid=True,
        gridcolor=style["grid"],
        gridwidth=0.6,
        showline=True,
        linewidth=style["line_width"],
        linecolor="#000000",
        ticks="outside",
        ticklen=3,
        mirror=False,
        zeroline=False,
    )
    fig.update_xaxes(**axis_style)
    fig.update_yaxes(**axis_style)
    # Cycle data traces through the colorblind-safe palette.
    for i, trace in enumerate(fig.data):
        color = colors[i % len(colors)]
        try:
            trace.update(line=dict(color=color, width=style["line_width"]))
        except Exception:
            pass
        if getattr(trace, "marker", None) is not None:
            try:
                trace.marker.color = color
                trace.marker.size = style["marker_size"]
            except Exception:
                pass
    return fig


def mpl_rc_params(journal: str = "Nature") -> Dict[str, Any]:
    """Matplotlib rcParams approximating the journal style (for PNG/PDF figures)."""
    style = journal_style(journal)
    serif = "serif" in style["font_body"].lower()
    return {
        "font.family": "serif" if serif else "sans-serif",
        "font.size": style["base_size"] + 1,
        "axes.titlesize": style["heading_size"] + 1,
        "axes.labelsize": style["base_size"] + 1,
        "axes.linewidth": style["line_width"],
        "axes.grid": True,
        "grid.color": style["grid"],
        "grid.linewidth": 0.6,
        "legend.fontsize": style["base_size"],
        "lines.linewidth": style["line_width"],
        "lines.markersize": style["marker_size"],
        "figure.dpi": FIGURE_DPI,
        "savefig.dpi": FIGURE_DPI,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }


def publication_figure_html(fig, journal: str = "Nature", title: str = "", height: int = 420) -> str:
    """Export a journal-styled Plotly figure as standalone HTML (for ZIP reports)."""
    styled = apply_journal_style(fig, journal=journal, title=title) if fig is not None else None
    if styled is None:
        return "<html><body><p>No figure supplied.</p></body></html>"
    inner = styled.to_html(full_html=False, include_plotlyjs="cdn")
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"<title>Titan Publication Studio — {journal}</title></head>"
        f"<body style='margin:16px;font-family:{journal_style(journal)['font_body']}'>"
        f"<h2 style='font-family:{journal_style(journal)['font_heading']}'>{title or 'Titan figure'}</h2>"
        f"<p style='color:#555;font-size:11px'>Journal style: {journal} · "
        "palette: Okabe-Ito (colorblind-safe) · Titan Bioinformatics Suite</p>"
        f"{inner}</body></html>"
    )


# Alias for API symmetry with other studios.
PALETTE_SAFE = okabe_ito_palette
