"""Execution adapters for Hub tools 1-52 — real engines, no stubs.

Every legacy tool ID maps 1:1 to the validated computation in
:mod:`titan_utils.compute` (which itself wraps Biopython / pandas /
NumPy plus the in-house ``titan_utils.thermo`` and ``titan_utils.msa``
engines). These adapters only translate the canonical result dict into a
:class:`ToolResult` with a dark-theme Plotly figure — they never
recompute, guess or fabricate anything.

``ADAPTER_BY_ID`` is the authoritative id → callable map consumed by
``scripts/generate_registry.py`` to derive each tool's input widgets from
the *real* function signature.
"""
from __future__ import annotations

import functools
import json
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go

from titan_tools.common import (
    TITAN_BLUE,
    TITAN_CORAL,
    TITAN_GOLD,
    TITAN_GREEN,
    TITAN_PURPLE,
    TITAN_TEAL,
    ToolResult,
    titan_plot_layout,
)
from titan_utils.compute import COMPUTE_BY_ID

_SERIES_COLORS = [TITAN_TEAL, TITAN_GOLD, TITAN_CORAL, TITAN_BLUE, TITAN_GREEN, TITAN_PURPLE]


# ─────────────────────────── figure builder ───────────────────────────

def _build_figure(spec: Optional[Dict[str, Any]]) -> Optional[go.Figure]:
    """Materialise a ``fig`` specification dict into a themed Plotly figure."""
    if not spec:
        return None
    kind = (spec.get("kind") or "").lower()
    title = spec.get("title") or ""
    x = spec.get("x") or []
    y = spec.get("y") or []
    xlabel = spec.get("xlabel") or ""
    ylabel = spec.get("ylabel") or ""
    height = int(spec.get("height") or (300 if kind == "pie" else 380))
    fig = go.Figure()
    if kind == "bar":
        fig.add_trace(go.Bar(x=list(x), y=[float(v) for v in y], marker_color=TITAN_TEAL))
    elif kind == "line":
        fig.add_trace(go.Scatter(x=list(x), y=[float(v) for v in y], mode="lines",
                                 line=dict(color=TITAN_TEAL, width=2)))
    elif kind == "pie":
        labels = spec.get("labels") or x
        values = spec.get("values") or y
        fig.add_trace(go.Pie(labels=list(labels), values=[float(v) for v in values], hole=0.45,
                             textfont=dict(color="#e6edf3"), textinfo="percent+label"))
    elif kind == "scatter":
        fig.add_trace(go.Scatter(x=list(x), y=list(y), mode="markers",
                                 marker=dict(color=TITAN_GOLD, size=4)))
    elif kind == "heatmap":
        grid = spec.get("grid") or []
        fig.add_trace(go.Heatmap(z=grid, x=list(x), y=list(y),
                                 colorscale="Viridis", zmid=0 if _symmetric(grid) else None))
        height = 420
    else:
        return None
    fig.update_layout(**titan_plot_layout(title, xaxis_title=xlabel, yaxis_title=ylabel, height=height))
    return fig


def _symmetric(grid: List[List[float]]) -> bool:
    if not grid or len(grid) != len(grid[0]):
        return False
    n = len(grid)
    return all(abs(grid[i][j] - grid[j][i]) < 1e-9 for i in range(n) for j in range(n))


# ─────────────────────────── result conversion ───────────────────────────

def _cell(v: Any) -> Any:
    """Flatten dict/list cells so st.dataframe shows them compactly."""
    if isinstance(v, (dict, list)):
        return json.dumps(v, separators=(",", ":"), ensure_ascii=False)
    return v


def _to_result(res: Dict[str, Any]) -> ToolResult:
    rows = res.get("rows") or []
    cols: List[str] = list(res.get("columns") or (list(rows[0].keys()) if rows else []))
    df: Optional[pd.DataFrame] = None
    if rows:
        df = pd.DataFrame([{c: _cell(r.get(c)) for c in cols} for r in rows], columns=cols)
    metrics: List[tuple] = []
    for m in res.get("metrics") or []:
        m = list(m)
        name, value = m[0], str(m[1])
        note = m[2] if len(m) > 2 else None
        metrics.append((name, value, note or None))
    extra: Dict[str, Any] = {}
    for key in ("text", "newick", "html"):
        if res.get(key):
            extra[key] = res[key]
    return ToolResult(
        title=res.get("title", "Result"),
        summary=res.get("summary", ""),
        metrics=metrics,
        dataframe=df,
        figure=_build_figure(res.get("fig")),
        fasta=res.get("fasta"),
        notes=list(res.get("notes") or []),
        extra_data=extra,
    )


# ─────────────────────────── adapter factory ───────────────────────────

def _make_adapter(tool_id: int, compute_fn: Callable[..., Dict[str, Any]]) -> Callable[..., ToolResult]:
    @functools.wraps(compute_fn)  # copies __signature__/__doc__ → registry derives real inputs
    def adapter(*args: Any, **kwargs: Any) -> ToolResult:
        return _to_result(compute_fn(*args, **kwargs))

    name = f"tool_legacy_{tool_id:02d}_{compute_fn.__name__}"
    adapter.__name__ = name
    adapter.__qualname__ = name
    adapter._titan_tool_id = tool_id  # type: ignore[attr-defined]
    return adapter


_adapters: Dict[str, Callable[..., ToolResult]] = {}
ADAPTER_BY_ID: Dict[int, Callable[..., ToolResult]] = {}
for _tid, _fn in COMPUTE_BY_ID.items():
    _ad = _make_adapter(_tid, _fn)
    globals()[_ad.__name__] = _ad
    _adapters[_ad.__name__] = _ad
    ADAPTER_BY_ID[_tid] = _ad

# Stable, human-friendly aliases for the two historically named handlers.
tool_legacy_dna_rna_convert = ADAPTER_BY_ID[1]
tool_legacy_revcomp = ADAPTER_BY_ID[2]
_adapters.setdefault("tool_legacy_dna_rna_convert", tool_legacy_dna_rna_convert)
_adapters.setdefault("tool_legacy_revcomp", tool_legacy_revcomp)

__all__ = [
    "ADAPTER_BY_ID",
    "ToolResult",
    "tool_legacy_dna_rna_convert",
    "tool_legacy_revcomp",
] + [k for k in _adapters if k.startswith("tool_legacy_")]


def tool_legacy_generic(tool_id: int, tool_name: str = "", **inputs: Any) -> ToolResult:
    """Dispatch by tool id to the real engine. Kept for backwards compatibility
    of any caller that still uses the generic name — it is *not* a fallback
    that fabricates output: unknown ids raise, engine errors propagate."""
    fn = COMPUTE_BY_ID.get(int(tool_id))
    if fn is None:
        raise LookupError(f"No compute engine registered for tool id {tool_id}.")
    return _to_result(fn(**inputs))
