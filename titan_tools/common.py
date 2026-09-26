"""Common data structures and visualization utilities for Titan tool engines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import pandas as pd
import plotly.graph_objects as go

TITAN_GOLD = "#d4af37"
TITAN_TEAL = "#00d4aa"
TITAN_CORAL = "#ff4757"
TITAN_BLUE = "#4a90e2"
TITAN_GREEN = "#2ecc71"
TITAN_PURPLE = "#9b59b6"
TITAN_BG = "#0d1117"
TITAN_PAPER = "#161b22"
TITAN_GRID = "#21262d"
TITAN_TEXT = "#e6edf3"


@dataclass
class ToolResult:
    title: str
    summary: str
    metrics: list[tuple[str, str, str | None]] = field(default_factory=list)
    dataframe: pd.DataFrame | None = None
    figure: go.Figure | None = None
    fasta: str | None = None
    notes: list[str] = field(default_factory=list)
    extra_data: dict[str, Any] = field(default_factory=dict)


def titan_plot_layout(
    title: str = "",
    xaxis_title: str = "",
    yaxis_title: str = "",
    height: int = 420,
) -> dict[str, Any]:
    """Return standard dark-theme Plotly layout dictionary."""
    return dict(
        title=dict(text=title, font=dict(color=TITAN_GOLD, size=16)),
        plot_bgcolor=TITAN_BG,
        paper_bgcolor=TITAN_PAPER,
        font=dict(color=TITAN_TEXT, family="Courier New, monospace"),
        xaxis=dict(
            title=xaxis_title,
            gridcolor=TITAN_GRID,
            zerolinecolor=TITAN_GRID,
            showline=True,
            linecolor=TITAN_GRID,
        ),
        yaxis=dict(
            title=yaxis_title,
            gridcolor=TITAN_GRID,
            zerolinecolor=TITAN_GRID,
            showline=True,
            linecolor=TITAN_GRID,
        ),
        margin=dict(l=40, r=40, t=50, b=40),
        height=height,
    )
