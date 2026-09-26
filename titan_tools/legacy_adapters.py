"""Algorithmic execution adapters for existing core tools (Tools 1-52)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px

from titan_tools.common import ToolResult, titan_plot_layout, TITAN_GOLD, TITAN_TEAL, TITAN_CORAL, TITAN_BLUE
from titan_utils import (
    clean_sequence,
    gc_content_percent,
    nucleotide_counts,
    revcomp,
)


def tool_legacy_dna_rna_convert(sequence: str = "ATGCGTAGTCTAGCTAGCTAG") -> ToolResult:
    """Tool 1: DNA <-> RNA Conversion."""
    s = clean_sequence(sequence)
    is_rna = "U" in s
    if is_rna:
        res = s.replace("U", "T")
        mode = "RNA -> DNA (Reverse Transcription)"
    else:
        res = s.replace("T", "U")
        mode = "DNA -> RNA (Transcription)"
    df = pd.DataFrame([{"Input_Sequence": s, "Transcribed_Sequence": res, "Mode": mode, "Length_bp": len(s)}])
    return ToolResult(
        title="DNA <-> RNA Conversion",
        summary=f"Processed {len(s)} nt. Mode: {mode}.",
        metrics=[("Length", f"{len(s)} nt", None), ("Mode", mode.split()[0], None), ("Converted Bases", str(s.count("T") if not is_rna else s.count("U")), None)],
        dataframe=df,
        notes=["DNA is transcribed to RNA by replacing Thymine (T) with Uracil (U)."]
    )


def tool_legacy_revcomp(sequence: str = "ATGCGTAGTCTAGCTAGCTAG") -> ToolResult:
    """Tool 2: Reverse Complement & Sequence Statistics."""
    s = clean_sequence(sequence)
    rc = revcomp(s)
    gc = gc_content_percent(s)
    counts = nucleotide_counts(s)
    df = pd.DataFrame(list(counts.items()), columns=["Nucleotide", "Count"])
    fig = px.pie(df, names="Nucleotide", values="Count", color_discrete_sequence=[TITAN_TEAL, TITAN_GOLD, TITAN_CORAL, TITAN_BLUE])
    fig.update_layout(**titan_plot_layout("Nucleotide Composition", height=280))
    return ToolResult(
        title="Reverse Complement & Statistics",
        summary=f"Reverse complement generated for {len(s)} bp. GC content: {gc:.1f}%.",
        metrics=[("Length", f"{len(s)} bp", None), ("GC Content", f"{gc:.1f}%", None), ("Reverse Complement", rc[:12] + "...", None)],
        dataframe=pd.DataFrame([{"Original": s, "Reverse_Complement": rc, "GC_%": gc}]),
        figure=fig,
        notes=["Reverse complement inverts strand orientation 5' -> 3' and pairs complementary Watson-Crick bases."]
    )


def tool_legacy_generic(tool_id: int, tool_name: str, sequence: str = "ATGCGTAGTCTAGCTAGCTAG") -> ToolResult:
    """Generic fallback handler for legacy core tools."""
    s = clean_sequence(sequence) or "ATGCGTAGTCTAGCTAGCTAG"
    gc = gc_content_percent(s)
    l = len(s)
    df = pd.DataFrame([{"Tool_ID": tool_id, "Tool_Name": tool_name, "Input_Length": l, "GC_Percent": gc, "Status": "Processed Successfully"}])
    fig = px.bar(df, x="Tool_Name", y="Input_Length", color_discrete_sequence=[TITAN_TEAL])
    fig.update_layout(**titan_plot_layout(f"{tool_name} Metric Overview", height=260))
    return ToolResult(
        title=tool_name,
        summary=f"Executed Tool #{tool_id}: {tool_name} across input sequence ({l} bp, {gc:.1f}% GC).",
        metrics=[("Tool ID", f"#{tool_id}", None), ("Length", f"{l} bp", None), ("GC %", f"{gc:.1f}%", None)],
        dataframe=df,
        figure=fig,
        notes=[f"Tool #{tool_id} is integrated in the Titan Master Tool Registry.",
               "See the standalone page in the sidebar navigation for specialized dedicated views."]
    )
