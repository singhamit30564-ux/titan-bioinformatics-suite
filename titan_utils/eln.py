"""Electronic Lab Notebook (ELN) & GLP audit-trail engine.

Tracks every analysis run with:

* SHA-256 **sequence digests** for inputs and outputs (provenance without
  retention — digests survive even after the sequence is scrubbed)
* Contemporaneous UTC timestamps, operator, module, parameters, status
* **1-click GLP compliance exports**: Markdown and PDF (via
  :mod:`titan_utils.pdf_generator`)

Designed for Good Laboratory Practice (GLP) / ALCOA+ principles:
**A**ttributable · **L**egible · **C**ontemporaneous · **O**riginal ·
**A**ccurate (+ complete, consistent, enduring, available).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Sequence

from titan_utils.privacy import sha256_of_text

__all__ = [
    "RunRecord",
    "ELNLog",
    "sequence_digest",
    "new_run_id",
    "get_session_log",
    "export_markdown",
    "export_pdf",
    "GLP_PRINCIPLES",
    "ELN_TEMPLATE",
]

GLP_PRINCIPLES = (
    "Attributable — every entry names its operator and timestamp.",
    "Legible — records are human-readable and immutable-once-logged.",
    "Contemporaneous — entries are written at the time work is performed.",
    "Original — the first record (or a certified true copy) is preserved.",
    "Accurate — inputs and outputs are fingerprinted with SHA-256 digests.",
    "Complete, Consistent, Enduring, Available — the ALCOA+ expectation.",
)

ELN_TEMPLATE = {
    "study_title": "Titan Bioinformatics in-silico analysis session",
    "operator": "Titan User",
    "facilities": "Titan Bioinformatics Suite — ephemeral in-RAM compute",
    "objective": "Reproducible computational analysis under Zero Data Retention.",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def sequence_digest(sequence: "str | bytes | bytearray | None") -> str:
    """SHA-256 digest of a sequence payload (empty-safe)."""
    return sha256_of_text(sequence)


def new_run_id(prefix: str = "TITAN") -> str:
    """Short run identifier derived from a UTC timestamp + digest salt."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    salt = sha256_of_text(stamp + prefix)[:6].upper()
    return f"{prefix}-{stamp}-{salt}"


@dataclass
class RunRecord:
    """One notebook entry — a logged analysis run."""

    run_id: str
    timestamp_utc: str
    module: str
    operator: str = "Titan User"
    summary: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    input_digest: str = ""
    output_digest: str = ""
    input_kind: str = "sequence"
    input_size: int = 0
    status: str = "Completed"
    notes: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp_utc": self.timestamp_utc,
            "module": self.module,
            "operator": self.operator,
            "summary": self.summary,
            "parameters": dict(self.parameters),
            "input_sha256": self.input_digest,
            "output_sha256": self.output_digest,
            "input_kind": self.input_kind,
            "input_size_bytes": self.input_size,
            "status": self.status,
            "notes": self.notes,
        }

    def audit_row(self) -> Dict[str, Any]:
        """Flat row for the on-screen GLP audit table."""
        params = "; ".join(f"{k}={v}" for k, v in self.parameters.items())
        return {
            "Run_ID": self.run_id,
            "Timestamp (UTC)": self.timestamp_utc,
            "Module": self.module,
            "Operator": self.operator,
            "Input_SHA256": (self.input_digest[:16] + "…") if self.input_digest else "",
            "Output_SHA256": (self.output_digest[:16] + "…") if self.output_digest else "",
            "Parameters": params[:120],
            "Status": self.status,
        }


class ELNLog:
    """Session-scoped notebook: append-only list of :class:`RunRecord`."""

    def __init__(self, study: Optional[Mapping[str, Any]] = None) -> None:
        self.study: Dict[str, Any] = dict(ELN_TEMPLATE)
        if study:
            self.study.update(dict(study))
        self.records: List[RunRecord] = []

    # -- logging ------------------------------------------------------------
    def log_run(
        self,
        module: str,
        input_data: "str | bytes | bytearray | None" = None,
        output_data: "str | bytes | bytearray | None" = None,
        summary: str = "",
        parameters: Optional[Mapping[str, Any]] = None,
        operator: str = "Titan User",
        status: str = "Completed",
        notes: str = "",
        input_kind: str = "sequence",
    ) -> RunRecord:
        """Create and store a contemporaneous run record with SHA-256 digests."""
        raw = input_data if isinstance(input_data, (bytes, bytearray)) else (input_data or "")
        size = len(raw) if raw is not None else 0
        record = RunRecord(
            run_id=new_run_id(),
            timestamp_utc=_utc_now(),
            module=module,
            operator=operator or self.study.get("operator", "Titan User"),
            summary=summary,
            parameters=dict(parameters or {}),
            input_digest=sequence_digest(input_data),
            output_digest=sequence_digest(output_data),
            input_kind=input_kind,
            input_size=size,
            status=status,
            notes=notes,
        )
        self.records.append(record)
        return record

    def extend(self, records: Sequence[RunRecord]) -> None:
        self.records.extend(records)

    def clear(self) -> int:
        n = len(self.records)
        self.records.clear()
        return n

    def __len__(self) -> int:
        return len(self.records)

    # -- views ---------------------------------------------------------------
    def audit_table(self) -> List[Dict[str, Any]]:
        return [r.audit_row() for r in self.records]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "study": dict(self.study),
            "exported_utc": _utc_now(),
            "run_count": len(self.records),
            "records": [r.as_dict() for r in self.records],
            "glp_principles": list(GLP_PRINCIPLES),
        }

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), indent=2)


def get_session_log() -> ELNLog:
    """Return the notebook bound to the current Streamlit session.

    Falls back to a module-level log outside Streamlit (tests, CLI).
    """
    try:
        import streamlit as st

        if "titan_eln_log" not in st.session_state:
            st.session_state["titan_eln_log"] = ELNLog()
        return st.session_state["titan_eln_log"]
    except Exception:
        global _FALLBACK_LOG  # deliberate process-level fallback outside Streamlit
        if _FALLBACK_LOG is None:
            _FALLBACK_LOG = ELNLog()
        return _FALLBACK_LOG


_FALLBACK_LOG: Optional[ELNLog] = None


# ─────────────────────────────────────────────────────────────────────────────
# GLP compliance exports
# ─────────────────────────────────────────────────────────────────────────────

def export_markdown(log: ELNLog) -> str:
    """1-click GLP compliance export — Markdown audit report."""
    lines: List[str] = [
        "# Electronic Lab Notebook — GLP Audit Report",
        "",
        f"**Study:** {log.study.get('study_title', '')}  ",
        f"**Operator:** {log.study.get('operator', '')}  ",
        f"**Facilities:** {log.study.get('facilities', '')}  ",
        f"**Objective:** {log.study.get('objective', '')}  ",
        f"**Exported:** {_utc_now()}  ",
        f"**Runs recorded:** {len(log.records)}",
        "",
        "## GLP / ALCOA+ Principles",
        "",
    ]
    lines.extend(f"- {p}" for p in GLP_PRINCIPLES)
    lines += ["", "## Audit Trail", ""]
    if not log.records:
        lines.append("_No runs recorded yet — log an analysis to begin the audit trail._")
    for rec in log.records:
        lines += [
            f"### {rec.run_id}",
            "",
            f"- **Timestamp (UTC):** {rec.timestamp_utc}",
            f"- **Module:** {rec.module}",
            f"- **Operator:** {rec.operator}",
            f"- **Summary:** {rec.summary or '—'}",
            f"- **Status:** {rec.status}",
            f"- **Input SHA-256:** `{rec.input_digest}` ({rec.input_size} bytes, {rec.input_kind})",
            f"- **Output SHA-256:** `{rec.output_digest}`",
        ]
        if rec.parameters:
            lines.append("- **Parameters:**")
            lines.extend(f"  - `{k}` = `{v}`" for k, v in rec.parameters.items())
        if rec.notes:
            lines.append(f"- **Notes:** {rec.notes}")
        lines.append("")
    lines += [
        "---",
        "",
        "_Generated by the Titan Bioinformatics Suite ELN. All analyses executed "
        "in 100% ephemeral in-RAM buffers under the Zero Data Retention policy; "
        "only SHA-256 digests and derived metrics are retained in this report._",
        "",
    ]
    return "\n".join(lines)


def export_pdf(log: ELNLog) -> bytes:
    """1-click GLP compliance export — PDF audit report (ReportLab)."""
    from titan_utils.pdf_generator import PdfReportSpec, PdfSection, build_pdf_report

    sections: List[PdfSection] = [
        PdfSection(
            heading="Study Identification",
            paragraphs=[
                f"Study: {log.study.get('study_title', '')}",
                f"Operator: {log.study.get('operator', '')}",
                f"Facilities: {log.study.get('facilities', '')}",
                f"Objective: {log.study.get('objective', '')}",
                f"Runs recorded: {len(log.records)}",
            ],
        ),
        PdfSection(
            heading="GLP / ALCOA+ Compliance Statement",
            bullets=list(GLP_PRINCIPLES),
        ),
    ]
    if log.records:
        rows = [
            [
                r.run_id,
                r.timestamp_utc,
                r.module,
                r.input_digest[:12] + "…",
                r.output_digest[:12] + "…",
                r.status,
            ]
            for r in log.records
        ]
        sections.append(
            PdfSection(
                heading="Audit Trail",
                table=(["Run ID", "Timestamp (UTC)", "Module", "Input SHA-256", "Output SHA-256", "Status"], rows),
                style="compact",
            )
        )
        sections.append(
            PdfSection(
                heading="Detailed Run Records",
                paragraphs=[
                    (
                        f"{r.run_id} | {r.timestamp_utc} | {r.module} | {r.operator} | "
                        f"input {r.input_digest} ({r.input_size} B {r.input_kind}) | "
                        f"output {r.output_digest} | {r.status}"
                        + (f" | notes: {r.notes}" if r.notes else "")
                    )
                    for r in log.records
                ],
                style="compact",
            )
        )
    else:
        sections.append(
            PdfSection(heading="Audit Trail", paragraphs=["No runs recorded yet."])
        )

    return build_pdf_report(
        PdfReportSpec(
            title="Electronic Lab Notebook — GLP Audit Report",
            subtitle=str(log.study.get("study_title", "")),
            author=f"Operator: {log.study.get('operator', 'Titan User')}",
            sections=sections,
        )
    )
