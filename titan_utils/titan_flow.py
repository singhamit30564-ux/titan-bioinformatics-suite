"""Titan Flow — multi-tool automated workflow builder engine.

Chains bioinformatics steps into reproducible pipelines and packages every
result into one consolidated ``.ZIP`` download:

* ``report.pdf``    — ReportLab scientific report of the whole run
* ``results.csv``   — consolidated per-step metric table
* ``results.tsv``   — same table, tab-delimited
* ``manifest.json`` — SHA-256 provenance for input + every package file
* ``steps/``        — per-step CSV + TSV detail tables

Bundled flows: **Central Dogma**, **Crop Resilience**, **Clinical Oncology**,
**Metagenomics**. All computation is ephemeral in-RAM (Zero Data Retention).
"""
from __future__ import annotations

import io
import json
import math
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from titan_utils.export import to_csv_bytes, to_tsv_bytes
from titan_utils.pdf_generator import PdfReportSpec, PdfSection, build_pdf_report
from titan_utils.privacy import provenance_manifest, provenance_record
from titan_utils.sequence import (
    clean_sequence,
    find_orfs_simple,
    gc_content_percent,
    nucleotide_counts,
    translate,
)

__all__ = [
    "StepResult",
    "FlowResult",
    "FlowStep",
    "FlowDefinition",
    "TITAN_FLOWS",
    "list_flows",
    "get_flow",
    "run_flow",
    "build_flow_zip",
    "flow_manifest",
    "DEFAULT_PAYLOADS",
]

DEFAULT_SEQUENCE = "ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StepResult:
    """Outcome of one pipeline step."""

    step_id: str
    title: str
    summary: str
    metrics: Dict[str, str] = field(default_factory=dict)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_frame(self):
        import pandas as pd

        if self.rows:
            cols = self.columns or list(self.rows[0].keys())
            return pd.DataFrame(self.rows, columns=cols)
        return pd.DataFrame([self.metrics] if self.metrics else [], columns=self.columns or None)


@dataclass
class FlowResult:
    """Full pipeline run result."""

    flow_id: str
    title: str
    description: str
    payload_kind: str
    input_digest: str
    input_size: int
    started_utc: str
    steps: List[StepResult] = field(default_factory=list)
    verdict: str = ""

    @property
    def duration_label(self) -> str:
        return "ephemeral in-RAM run"

    def consolidated_rows(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for idx, step in enumerate(self.steps, start=1):
            if step.rows:
                for row in step.rows:
                    entry = {"Step": idx, "Step_ID": step.step_id, "Step_Name": step.title}
                    entry.update(row)
                    rows.append(entry)
            else:
                entry = {"Step": idx, "Step_ID": step.step_id, "Step_Name": step.title}
                entry.update(step.metrics)
                rows.append(entry)
        return rows

    def summary_paragraphs(self) -> List[str]:
        out = [
            f"Flow: {self.title} ({self.flow_id})",
            f"Input: {self.payload_kind}, {self.input_size} bytes, SHA-256 {self.input_digest}",
            f"Steps executed: {len(self.steps)} — {self.duration_label}.",
        ]
        for step in self.steps:
            out.append(f"{step.title}: {step.summary}")
        if self.verdict:
            out.append(f"Verdict: {self.verdict}")
        return out


@dataclass(frozen=True)
class FlowStep:
    """One step definition: metadata + pure runner function."""

    id: str
    name: str
    description: str
    fn: Callable[[str], StepResult]


@dataclass(frozen=True)
class FlowDefinition:
    """A named multi-tool pipeline."""

    id: str
    name: str
    emoji: str
    description: str
    payload_kind: str
    default_payload: str
    steps: Tuple[FlowStep, ...]
    tags: Tuple[str, ...] = ()


# ─────────────────────────────────────────────────────────────────────────────
# Shared step helpers
# ─────────────────────────────────────────────────────────────────────────────

def _clean(payload: str) -> str:
    return clean_sequence(payload)


def _split_records(payload: str) -> List[Tuple[str, str]]:
    """Split a multi-FASTA-ish payload into (header, sequence) pairs."""
    records: List[Tuple[str, str]] = []
    header = None
    chunks: List[str] = []
    for raw in (payload or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append((header, clean_sequence("".join(chunks))))
            header = line[1:].strip() or f"record_{len(records) + 1}"
            chunks = []
        else:
            if header is None:
                header = "record_1"
            chunks.append(line)
    if header is not None:
        records.append((header, clean_sequence("".join(chunks))))
    if not records and (payload or "").strip():
        records.append(("record_1", clean_sequence(payload)))
    return [(h, s) for h, s in records if s]


# ─────────────────────────────────────────────────────────────────────────────
# Flow 1 — Central Dogma
# ─────────────────────────────────────────────────────────────────────────────

def _cd_validate(payload: str) -> StepResult:
    s = _clean(payload)
    counts = nucleotide_counts(s)
    ok = bool(s) and all(c in "ACGT" for c in s)
    rows = [{"Nucleotide": k, "Count": v, "Percent": round(100.0 * v / len(s), 2) if s else 0.0}
            for k, v in counts.items()]
    return StepResult(
        step_id="cd_validate",
        title="Sequence Validation & Composition",
        summary=f"Validated {len(s)} nt DNA ({'canonical ACGT' if ok else 'contains non-ACGT characters'}).",
        metrics={"Length_bp": str(len(s)), "GC_%": f"{gc_content_percent(s):.2f}", "Valid": "yes" if ok else "check"},
        rows=rows,
        columns=["Nucleotide", "Count", "Percent"],
        notes=["Validation runs on cleaned, uppercase sequence in RAM only."],
    )


def _cd_transcribe(payload: str) -> StepResult:
    s = _clean(payload)
    rna = s.replace("T", "U")
    return StepResult(
        step_id="cd_transcribe",
        title="Transcription (DNA → mRNA)",
        summary=f"Transcribed {len(s)} nt to mRNA ({rna[:24]}{'…' if len(rna) > 24 else ''}).",
        metrics={"mRNA_Length": str(len(rna)), "Uracil_Count": str(rna.count("U")), "GC_%": f"{gc_content_percent(rna):.2f}"},
        rows=[{"Fragment": "mRNA_1", "Sequence": rna, "Length_nt": len(rna)}],
        columns=["Fragment", "Sequence", "Length_nt"],
        notes=["Thymine is replaced by Uracil during transcription (RNA polymerase)."],
    )


def _cd_translate(payload: str) -> StepResult:
    s = _clean(payload)
    protein = translate(s, to_stop=False)
    stops = protein.count("*")
    return StepResult(
        step_id="cd_translate",
        title="Translation (mRNA → Protein)",
        summary=f"Translated {len(s)} nt to {len(protein)} aa ({stops} stop codon(s)).",
        metrics={"Protein_aa": str(len(protein)), "Stop_Codons": str(stops), "Met_Start": "yes" if protein.startswith("M") else "no"},
        rows=[{"Frame": 1, "Protein": protein, "Length_aa": len(protein)}],
        columns=["Frame", "Protein", "Length_aa"],
        notes=["Standard genetic code; translation stops conceptually at the first '*'."],
    )


def _cd_orfs(payload: str) -> StepResult:
    s = _clean(payload)
    orfs = find_orfs_simple(s, min_len=30)
    rows = [
        {"ORF": i + 1, "Strand": o.get("Strand", "+"), "Frame": o.get("Frame", 1),
         "Start": o.get("Start_Pos"), "End": o.get("End_Pos"), "Length_bp": o.get("Length_bp")}
        for i, o in enumerate(orfs[:25])
    ]
    return StepResult(
        step_id="cd_orfs",
        title="ORF Discovery",
        summary=f"Found {len(orfs)} ORF(s) ≥ 30 bp across 6 frames.",
        metrics={"ORFs": str(len(orfs)), "Longest_bp": str(max((o.get("Length_bp", 0) for o in orfs), default=0))},
        rows=rows,
        columns=["ORF", "Strand", "Frame", "Start", "End", "Length_bp"],
        notes=["Open reading frames start with ATG and end at an in-frame stop."],
    )


def _cd_gc(payload: str) -> StepResult:
    s = _clean(payload)
    gc = gc_content_percent(s)
    tm = 64.9 + 41.0 * (sum(s.count(b) for b in "GC") - 16.4) / max(len(s), 1)
    return StepResult(
        step_id="cd_gc",
        title="GC Content & Melting Temperature",
        summary=f"GC = {gc:.2f}%, Wallace Tm ≈ {2 * (s.count('A') + s.count('T')) + 4 * (s.count('G') + s.count('C'))}°C, salt-adjusted Tm ≈ {tm:.1f}°C.",
        metrics={"GC_%": f"{gc:.2f}", "Tm_salt_C": f"{tm:.1f}", "AT_%": f"{100.0 - gc:.2f}"},
        rows=[{"Metric": "GC content", "Value": f"{gc:.2f} %"},
              {"Metric": "Salt-adjusted Tm", "Value": f"{tm:.1f} °C"},
              {"Metric": "Wallace Tm (short oligo)", "Value": f"{2 * (s.count('A') + s.count('T')) + 4 * (s.count('G') + s.count('C'))} °C"}],
        columns=["Metric", "Value"],
        notes=["Tm estimates support PCR primer design discussions."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Flow 2 — Crop Resilience
# ─────────────────────────────────────────────────────────────────────────────

_SSR_MOTIFS = ("AT", "AG", "GA", "GC", "TA", "AAG", "CTT", "CCA", "GAA", "GATA")
_STRESS_MOTIFS = {
    "DRE/CRT core": ("RCCGAC", "Dehydration-responsive element (CBF/DREB binding)"),
    "ABRE": ("ACGTG", "Abscisic acid-responsive element (stress signaling)"),
    "LTRE": ("CCGAAA", "Low-temperature responsive element"),
    "W-box": ("TGACC", "WRKY transcription-factor binding (pathogen response)"),
    "HSE": ("nGAAn", "Heat-shock element consensus"),
}


def _crop_qc(payload: str) -> StepResult:
    s = _clean(payload)
    n_count = s.count("N")
    return StepResult(
        step_id="crop_qc",
        title="Marker Sequence QC",
        summary=f"QC on {len(s)} bp marker input: {n_count} ambiguous base(s), GC {gc_content_percent(s):.1f}%.",
        metrics={"Length_bp": str(len(s)), "Ambiguous_N": str(n_count), "GC_%": f"{gc_content_percent(s):.2f}"},
        rows=[{"Check": "Length ≥ 50 bp", "Result": "PASS" if len(s) >= 50 else "REVIEW"},
              {"Check": "Ambiguous bases (N)", "Result": "PASS" if n_count == 0 else f"{n_count} found"},
              {"Check": "GC in 30-70%", "Result": "PASS" if 30 <= gc_content_percent(s) <= 70 else "REVIEW"}],
        columns=["Check", "Result"],
    )


def _crop_ssr(payload: str) -> StepResult:
    s = _clean(payload)
    hits = []
    for motif in _SSR_MOTIFS:
        for m in re.finditer(rf"({motif}){{4,}}", s):
            repeat = len(m.group()) // len(motif)
            hits.append({"SSR_Motif": motif, "Repeats": repeat, "Start": m.start() + 1,
                         "End": m.end(), "Span_bp": len(m.group())})
    return StepResult(
        step_id="crop_ssr",
        title="SSR / Microsatellite Marker Scan",
        summary=f"Detected {len(hits)} SSR tract(s) with ≥4 perfect repeats.",
        metrics={"SSR_Count": str(len(hits)), "Motifs_Scanned": str(len(_SSR_MOTIFS))},
        rows=hits,
        columns=["SSR_Motif", "Repeats", "Start", "End", "Span_bp"],
        notes=["Polymorphic SSRs power cultivar fingerprinting and marker-assisted selection."],
    )


def _crop_stress(payload: str) -> StepResult:
    s = _clean(payload).replace("U", "T")
    rows = []
    for name, (core, desc) in _STRESS_MOTIFS.items():
        if core == "nGAAn":
            pat = r"[ACGT]GA[ACGT]{2}"
        else:
            pat = core.replace("R", "[AG]").replace("W", "[AT]")
        count = len(re.findall(f"(?=({pat}))", s))
        if count:
            rows.append({"Element": name, "Consensus": core, "Hits": count, "Function": desc})
    total = sum(r["Hits"] for r in rows)
    return StepResult(
        step_id="crop_stress",
        title="Abiotic/Biotic Stress Regulatory Element Scan",
        summary=f"Found {total} cis-regulatory stress element hit(s) across {len(rows)} element families.",
        metrics={"Stress_Elements": str(len(rows)), "Total_Hits": str(total)},
        rows=rows,
        columns=["Element", "Consensus", "Hits", "Function"],
        notes=["DREB/CBF and WRKY pathways orchestrate drought, cold and pathogen resilience."],
    )


def _crop_rgene(payload: str) -> StepResult:
    s = _clean(payload).upper()
    if set(s) <= set("ACGTN"):
        # Translate in silico for motif scanning.
        s = translate(s, to_stop=False)
    motifs = {
        "P-loop (Kinase-1a)": (r"[GS]G[A-Z]{2}[GS]GK[ST]", "ATP/GTP binding"),
        "Kinase-2": (r"[LV]{3}[LV]DD[VW]", "Mg2+ coordination"),
        "GLPL": (r"GLPL[ATLV]", "LRR conserved core"),
    }
    rows = []
    for name, (pat, fn) in motifs.items():
        for m in re.finditer(pat, s):
            rows.append({"Motif": name, "Start": m.start() + 1, "End": m.end(),
                         "Matched": m.group(), "Function": fn})
    klass = "CC-NBS-LRR-like" if any(r["Motif"] == "Kinase-2" for r in rows) else (
        "NBS-LRR candidate" if rows else "No NBS-LRR signature")
    return StepResult(
        step_id="crop_rgene",
        title="R-Gene (NBS-LRR) Motif Profiling",
        summary=f"Scanned translated space for resistance motifs → {klass}.",
        metrics={"Motif_Hits": str(len(rows)), "Predicted_Class": klass},
        rows=rows,
        columns=["Motif", "Start", "End", "Matched", "Function"],
    )


def _crop_verdict(payload: str) -> StepResult:
    s = _clean(payload)
    gc = gc_content_percent(s)
    ssr_total = sum(1 for motif in _SSR_MOTIFS for _ in re.finditer(rf"({motif}){{4,}}", s))
    score = min(100.0, 35.0 + 4.0 * ssr_total + (15.0 if 35 <= gc <= 65 else 0.0))
    verdict = "Strong resilience-marker candidate" if score >= 60 else "Moderate marker candidate"
    return StepResult(
        step_id="crop_verdict",
        title="Crop Resilience Verdict",
        summary=f"Composite resilience score {score:.1f}/100 → {verdict}.",
        metrics={"Score": f"{score:.1f}", "Verdict": verdict},
        rows=[{"Component": "SSR richness", "Score": f"{min(40.0, 4.0 * ssr_total):.1f}"},
              {"Component": "GC stability window", "Score": "15.0" if 35 <= gc <= 65 else "5.0"},
              {"Component": "Base score", "Score": "35.0"}],
        columns=["Component", "Score"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Flow 3 — Clinical Oncology
# ─────────────────────────────────────────────────────────────────────────────

_HOTSPOTS = {
    ("BRAF", "V600E"): ("Melanoma, colorectal, thyroid", "BRAF/MEK inhibitors (vemurafenib, dabrafenib)"),
    ("KRAS", "G12C"): ("NSCLC, colorectal", "KRAS G12C inhibitors (sotorasib, adagrasib)"),
    ("EGFR", "L858R"): ("NSCLC", "EGFR TKIs (erlotinib, osimertinib)"),
    ("EGFR", "T790M"): ("NSCLC (resistance)", "Osimertinib (3rd-gen EGFR TKI)"),
    ("PIK3CA", "H1047R"): ("Breast, endometrial", "PI3Kα inhibitors (alpelisib)"),
    ("TP53", "R175H"): ("Multiple carcinomas", "Clinical trials / MDM2 inhibitors"),
    ("IDH1", "R132H"): ("Glioma, AML", "IDH1 inhibitors (ivosidenib)"),
}

_VARIANT_RE = re.compile(
    r"(?P<gene>[A-Za-z][A-Za-z0-9\-]*)\s*(?:p\.)?[:\s]\s*(?P<hgvsp>[A-Z]\d+[A-Z*])"
)


def _parse_variants(payload: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for line in (payload or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _VARIANT_RE.search(line.upper().replace("P.", "p."))
        if m:
            out.append((str(m.group("gene")), str(m.group("hgvsp"))))
    return out


def _onc_parse(payload: str) -> StepResult:
    variants = _parse_variants(payload)
    rows = [{"Gene": g, "Protein_Change": v, "Parsed": "yes"} for g, v in variants]
    return StepResult(
        step_id="onc_parse",
        title="Variant Parsing & Normalization",
        summary=f"Parsed {len(variants)} variant(s) from the clinical payload.",
        metrics={"Variants": str(len(variants)), "Format": "GENE p.X123Y"},
        rows=rows,
        columns=["Gene", "Protein_Change", "Parsed"],
        notes=["Nomenclature: HGVS protein-level one-letter substitution, e.g. BRAF V600E."],
    )


def _onc_hotspot(payload: str) -> StepResult:
    rows = []
    for gene, change in _parse_variants(payload):
        key = (gene, change)
        if key in _HOTSPOTS:
            cancer, therapy = _HOTSPOTS[key]
            rows.append({"Gene": gene, "Change": change, "Hotspot": "known",
                         "Tumor_Types": cancer, "Therapy_Implication": therapy})
        else:
            rows.append({"Gene": gene, "Change": change, "Hotspot": "not in curated panel",
                         "Tumor_Types": "—", "Therapy_Implication": "review literature / ClinVar"})
    known = sum(1 for r in rows if r["Hotspot"] == "known")
    return StepResult(
        step_id="onc_hotspot",
        title="Oncogenic Hotspot Classification",
        summary=f"{known}/{len(rows)} variant(s) match curated oncogenic hotspots.",
        metrics={"Curated_Hotspots": str(known), "Total": str(len(rows))},
        rows=rows,
        columns=["Gene", "Change", "Hotspot", "Tumor_Types", "Therapy_Implication"],
    )


def _onc_tmb(payload: str) -> StepResult:
    variants = _parse_variants(payload)
    n = len(variants)
    tmb = n / 1.0  # mutations per Mb, simplified panel assumption
    band = "High" if tmb >= 10 else ("Intermediate" if tmb >= 3 else "Low")
    return StepResult(
        step_id="onc_tmb",
        title="Tumor Mutational Burden (TMB) Estimate",
        summary=f"Estimated TMB ≈ {tmb:.1f} mut/Mb → {band} burden (1 Mb panel assumption).",
        metrics={"TMB_mut_per_Mb": f"{tmb:.1f}", "Burden_Band": band},
        rows=[{"Metric": "Mutation count", "Value": str(n)},
              {"Metric": "Panel size (assumed)", "Value": "1.0 Mb"},
              {"Metric": "TMB", "Value": f"{tmb:.1f} mut/Mb"},
              {"Metric": "Band", "Value": band}],
        columns=["Metric", "Value"],
        notes=["TMB ≥ 10 mut/Mb predicts response to immune checkpoint blockade in some tumors."],
    )


def _onc_msi(payload: str) -> StepResult:
    s = _clean(payload.replace("\n", "").replace(" ", ""))
    mono = len(re.findall(r"(A{8,}|T{8,}|C{8,}|G{8,})", s))
    di = len(re.findall(r"((?:AT){5,}|(?:AG){5,}|(?:CA){5,}|(?:GT){5,})", s))
    instable = mono + di >= 2
    return StepResult(
        step_id="onc_msi",
        title="Microsatellite Instability (MSI) Screen",
        summary=f"Found {mono} mono- and {di} di-nucleotide repeat tract(s) ≥ threshold → MSI-{'High' if instable else 'Stable'} surrogate.",
        metrics={"Mono_Tracts": str(mono), "Di_Tracts": str(di), "MSI_Status": "MSI-H surrogate" if instable else "MSS surrogate"},
        rows=[{"Tract_Type": "Mononucleotide", "Count": mono},
              {"Tract_Type": "Dinucleotide", "Count": di},
              {"Tract_Type": "Status", "Count": "MSI-H surrogate" if instable else "MSS surrogate"}],
        columns=["Tract_Type", "Count"],
    )


def _onc_report(payload: str) -> StepResult:
    variants = _parse_variants(payload)
    known = sum(1 for g, c in variants if (g, c) in _HOTSPOTS)
    tier = "Tier I/II (actionable)" if known else "Tier III (variants of unknown significance)"
    return StepResult(
        step_id="onc_report",
        title="Clinical Interpretation Summary",
        summary=f"{len(variants)} variant(s); {known} actionable → {tier}.",
        metrics={"Actionable": str(known), "Tier": tier},
        rows=[{"Section": "Variants analysed", "Value": str(len(variants))},
              {"Section": "Curated hotspots", "Value": str(known)},
              {"Section": "Reporting tier", "Value": tier}],
        columns=["Section", "Value"],
        notes=["Somatic variant reporting follows AMP/ASCO/CAP tiering conventions."],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Flow 4 — Metagenomics
# ─────────────────────────────────────────────────────────────────────────────

def _meta_ingest(payload: str) -> StepResult:
    records = _split_records(payload)
    rows = [{"Read_ID": h, "Length_nt": len(s), "GC_%": round(gc_content_percent(s), 2)}
            for h, s in records]
    total = sum(len(s) for _, s in records)
    return StepResult(
        step_id="meta_ingest",
        title="Amplicon Ingest & Per-Read QC",
        summary=f"Ingested {len(records)} amplicon record(s), {total} nt total.",
        metrics={"Records": str(len(records)), "Total_nt": str(total),
                 "Mean_Length": f"{(total / len(records)):.1f}" if records else "0"},
        rows=rows,
        columns=["Read_ID", "Length_nt", "GC_%"],
    )


def _meta_otu(payload: str) -> StepResult:
    records = _split_records(payload)
    clusters: List[Tuple[str, str]] = []  # (representative, members)
    for header, seq in records:
        placed = False
        for rep, members in clusters:
            shorter = min(len(rep), len(seq))
            if shorter == 0:
                continue
            same = sum(1 for a, b in zip(rep[:shorter], seq[:shorter]) if a == b)
            if same / shorter >= 0.97:
                members.append(header)
                placed = True
                break
        if not placed:
            clusters.append((seq, [header]))
    rows = [{"OTU": f"OTU_{i + 1}", "Members": ", ".join(m), "Size": len(m),
             "Rep_Length": len(rep)}
            for i, (rep, m) in enumerate(clusters)]
    return StepResult(
        step_id="meta_otu",
        title="OTU Clustering (97% identity)",
        summary=f"Clustered {len(records)} read(s) into {len(clusters)} OTU(s) at 97% identity.",
        metrics={"OTUs": str(len(clusters)), "Reads": str(len(records)),
                 "Clustering_Threshold": "97%"},
        rows=rows,
        columns=["OTU", "Members", "Size", "Rep_Length"],
        notes=["97% 16S identity approximates the species-level boundary."],
    )


def _meta_diversity(payload: str) -> StepResult:
    records = _split_records(payload)
    clusters: Dict[str, List[str]] = {}
    for header, seq in records:
        key = seq[:50] if seq else header
        clusters.setdefault(key, []).append(header)
    counts = [len(v) for v in clusters.values()]
    total = sum(counts) or 1
    shannon = -sum((c / total) * math.log(c / total) for c in counts if c)
    simpson = 1.0 - sum((c / total) ** 2 for c in counts)
    richness = len(counts)
    evenness = shannon / math.log(richness) if richness > 1 else 0.0
    return StepResult(
        step_id="meta_diversity",
        title="Alpha Diversity Indices",
        summary=f"Shannon H' = {shannon:.3f}, Simpson 1-D = {simpson:.3f}, richness = {richness}.",
        metrics={"Shannon_H": f"{shannon:.3f}", "Simpson_1D": f"{simpson:.3f}",
                 "Richness": str(richness), "Evenness": f"{evenness:.3f}"},
        rows=[{"Index": "Shannon H'", "Value": f"{shannon:.3f}"},
              {"Index": "Simpson 1-D", "Value": f"{simpson:.3f}"},
              {"Index": "Observed richness", "Value": str(richness)},
              {"Index": "Pielou evenness", "Value": f"{evenness:.3f}"}],
        columns=["Index", "Value"],
    )


def _meta_taxonomy(payload: str) -> StepResult:
    records = _split_records(payload)
    rows = []
    for header, seq in records:
        gc = gc_content_percent(seq)
        if gc > 60:
            clade = "Actinobacteria-like (high-GC)"
        elif gc < 40:
            clade = "Firmicutes-like (low-GC)"
        else:
            clade = "Proteobacteria-like (mid-GC)"
        rows.append({"Read_ID": header, "GC_%": round(gc, 2), "Provisional_Clade": clade})
    return StepResult(
        step_id="meta_taxonomy",
        title="Provisional GC-Based Taxonomic Binning",
        summary=f"Assigned {len(rows)} provisional clade bin(s) from GC signatures.",
        metrics={"Binned": str(len(rows))},
        rows=rows,
        columns=["Read_ID", "GC_%", "Provisional_Clade"],
        notes=["GC binning is a coarse heuristic — full taxonomy needs reference alignment."],
    )


def _meta_amr(payload: str) -> StepResult:
    s = _clean(payload.replace("\n", " "))
    markers = {
        "blaTEM-like": "ACTTGG",
        "mecA-like": "GCAAAT",
        "sul1-like": "CGAAGC",
        "tetM-like": "GGTTAT",
        "intI1-like": "ACCGAC",
    }
    rows = [{"Marker": k, "Motif": v, "Hits": s.count(v)} for k, v in markers.items() if s.count(v)]
    total = sum(r["Hits"] for r in rows)
    return StepResult(
        step_id="meta_amr",
        title="Antibiotic Resistance Marker Screen",
        summary=f"Detected {total} AMR marker motif hit(s) across {len(rows)} gene families.",
        metrics={"AMR_Hits": str(total), "Families": str(len(rows))},
        rows=rows,
        columns=["Marker", "Motif", "Hits"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# Flow registry
# ─────────────────────────────────────────────────────────────────────────────

TITAN_FLOWS: Dict[str, FlowDefinition] = {
    "central_dogma": FlowDefinition(
        id="central_dogma",
        name="Central Dogma Pipeline",
        emoji="🧬",
        description=(
            "DNA validation → transcription → translation → ORF discovery → "
            "GC/Tm biophysics — the complete gene-expression walkthrough."
        ),
        payload_kind="DNA sequence",
        default_payload=DEFAULT_SEQUENCE,
        steps=(
            FlowStep("cd_validate", "Sequence Validation & Composition", "Validate + nucleotide counts", _cd_validate),
            FlowStep("cd_transcribe", "Transcription", "DNA → mRNA", _cd_transcribe),
            FlowStep("cd_translate", "Translation", "mRNA → protein", _cd_translate),
            FlowStep("cd_orfs", "ORF Discovery", "6-frame ORF scan", _cd_orfs),
            FlowStep("cd_gc", "GC & Tm Biophysics", "GC% and melting temperature", _cd_gc),
        ),
        tags=("expression", "education", "core"),
    ),
    "crop_resilience": FlowDefinition(
        id="crop_resilience",
        name="Crop Resilience Pipeline",
        emoji="🌾",
        description=(
            "Marker QC → SSR microsatellite scan → stress cis-element profiling → "
            "R-gene NBS-LRR motifs → composite resilience verdict."
        ),
        payload_kind="plant marker DNA",
        default_payload=(
            "ATATATATATATATATATATATGCGCGCGCAAGAAGAAGAAGCTTCTTCTT"
            "GCCGACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTACGTAC"
            "TTGACCTTGGCCAATTGGCCAATTGGCCAATTAGATATATATATATATAT"
        ),
        steps=(
            FlowStep("crop_qc", "Marker Sequence QC", "Length / N / GC checks", _crop_qc),
            FlowStep("crop_ssr", "SSR Marker Scan", "Microsatellite discovery", _crop_ssr),
            FlowStep("crop_stress", "Stress Element Scan", "DREB/ABRE/LTRE/W-box/HSE", _crop_stress),
            FlowStep("crop_rgene", "R-Gene Motif Profile", "NBS-LRR motifs", _crop_rgene),
            FlowStep("crop_verdict", "Resilience Verdict", "Composite score", _crop_verdict),
        ),
        tags=("agriculture", "markers", "stress"),
    ),
    "clinical_oncology": FlowDefinition(
        id="clinical_oncology",
        name="Clinical Oncology Pipeline",
        emoji="🩺",
        description=(
            "Variant parsing → hotspot classification → TMB estimate → MSI screen → "
            "tiered clinical interpretation summary."
        ),
        payload_kind="somatic variant list",
        default_payload=(
            "BRAF V600E\n"
            "KRAS G12C\n"
            "EGFR L858R\n"
            "PIK3CA H1047R\n"
        ),
        steps=(
            FlowStep("onc_parse", "Variant Parsing & Normalization", "HGVS-style parsing", _onc_parse),
            FlowStep("onc_hotspot", "Hotspot Classification", "Curated oncogenic hotspots", _onc_hotspot),
            FlowStep("onc_tmb", "TMB Estimate", "Mutational burden", _onc_tmb),
            FlowStep("onc_msi", "MSI Screen", "Microsatellite instability", _onc_msi),
            FlowStep("onc_report", "Clinical Interpretation", "AMP/ASCO/CAP-style tiering", _onc_report),
        ),
        tags=("clinical", "variants", "therapy"),
    ),
    "metagenomics": FlowDefinition(
        id="metagenomics",
        name="Metagenomics Pipeline",
        emoji="🦠",
        description=(
            "Amplicon ingest → 97% OTU clustering → alpha diversity indices → "
            "GC-based provisional taxonomy → AMR marker screen."
        ),
        payload_kind="multi-FASTA 16S amplicons",
        default_payload=(
            ">sample_A\n"
            "ATGCGATCGATCGGCTAATGCGATCGATCGGCTAATGCGATCGATCGGCTAATGCGGCTAAT\n"
            ">sample_B\n"
            "ATGCGATCGATCGGCTAATGCGATCGATCGGCTAATGCGATCGATCGGCTAATGCGGCTAAT\n"
            ">sample_C\n"
            "GGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAA\n"
            ">sample_D\n"
            "ATATCGCGATATCGCGATATCGCGATATCGCGATATCGCGATATCGCGATATCGCGATATCGCG\n"
        ),
        steps=(
            FlowStep("meta_ingest", "Amplicon Ingest & QC", "Multi-FASTA parsing", _meta_ingest),
            FlowStep("meta_otu", "OTU Clustering", "97% identity clustering", _meta_otu),
            FlowStep("meta_diversity", "Alpha Diversity", "Shannon / Simpson", _meta_diversity),
            FlowStep("meta_taxonomy", "Provisional Taxonomy", "GC-signature binning", _meta_taxonomy),
            FlowStep("meta_amr", "AMR Marker Screen", "Resistance motifs", _meta_amr),
        ),
        tags=("microbiome", "16S", "diversity"),
    ),
}

DEFAULT_PAYLOADS: Dict[str, str] = {fid: f.default_payload for fid, f in TITAN_FLOWS.items()}


def list_flows() -> List[Dict[str, Any]]:
    """Registry rows for the workflow builder UI."""
    return [
        {
            "id": f.id,
            "name": f.name,
            "emoji": f.emoji,
            "description": f.description,
            "steps": str(len(f.steps)),
            "payload_kind": f.payload_kind,
            "tags": ", ".join(f.tags),
        }
        for f in TITAN_FLOWS.values()
    ]


def get_flow(flow_id: str) -> FlowDefinition:
    """Look up a flow (falls back to Central Dogma)."""
    return TITAN_FLOWS.get(flow_id, TITAN_FLOWS["central_dogma"])


# ─────────────────────────────────────────────────────────────────────────────
# Execution + packaging
# ─────────────────────────────────────────────────────────────────────────────

def run_flow(flow_id: str, payload: Optional[str] = None) -> FlowResult:
    """Execute every step of a flow on ``payload`` (ephemeral in RAM)."""
    flow = get_flow(flow_id)
    data = payload if payload is not None else flow.default_payload
    rec = provenance_record(data, kind=flow.payload_kind, label=f"flow_input:{flow.id}")
    result = FlowResult(
        flow_id=flow.id,
        title=f"{flow.emoji} {flow.name}",
        description=flow.description,
        payload_kind=flow.payload_kind,
        input_digest=rec.digest,
        input_size=rec.size_bytes,
        started_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )
    for step in flow.steps:
        result.steps.append(step.fn(data))

    known_hits = len(result.consolidated_rows())
    result.verdict = (
        f"Pipeline complete — {len(result.steps)} tools chained, "
        f"{known_hits} aggregate result rows, input fingerprint {rec.short}… (ZDR compliant)."
    )
    return result


def flow_manifest(result: FlowResult, files: Sequence[Tuple[str, bytes]]) -> Dict[str, Any]:
    """Digest-only manifest for a flow package (see privacy.provenance_manifest)."""
    items = [("flow_input", result.input_digest)]
    items += [(name, data, "artifact") for name, data in files]
    # Hash the already-digested input string to keep provenance homogeneous.
    manifest = provenance_manifest(items)
    manifest["flow_id"] = result.flow_id
    manifest["flow_title"] = result.title
    manifest["started_utc"] = result.started_utc
    manifest["step_count"] = len(result.steps)
    manifest["payload_kind"] = result.payload_kind
    manifest["input_sha256"] = result.input_digest
    manifest["files"] = [
        {"name": name, "sha256": provenance_record(data, kind="artifact", label=name).digest,
         "size_bytes": len(data)}
        for name, data in files
    ]
    return manifest


def build_flow_zip(result: FlowResult) -> bytes:
    """Consolidate a flow run into one ZIP package (built entirely in RAM).

    Contents: ``report.pdf``, ``results.csv``, ``results.tsv``,
    ``manifest.json`` and per-step tables under ``steps/``.
    """
    rows = result.consolidated_rows()
    import pandas as pd

    table = pd.DataFrame(rows)
    csv_bytes = to_csv_bytes(table)
    tsv_bytes = to_tsv_bytes(table)

    # Per-step detail files.
    step_files: List[Tuple[str, bytes]] = []
    for idx, step in enumerate(result.steps, start=1):
        df = step.to_frame()
        stem = f"steps/step_{idx:02d}_{step.step_id}"
        step_files.append((f"{stem}.csv", to_csv_bytes(df)))
        step_files.append((f"{stem}.tsv", to_tsv_bytes(df)))

    # Scientific PDF report.
    sections = [
        PdfSection(
            heading="Pipeline Overview",
            paragraphs=result.summary_paragraphs(),
        ),
        PdfSection(
            heading="Input Provenance (SHA-256)",
            paragraphs=[
                f"Input kind: {result.payload_kind}",
                f"Input SHA-256: {result.input_digest}",
                f"Input size: {result.input_size} bytes (ephemeral, not retained)",
            ],
        ),
    ]
    for step in result.steps:
        sections.append(
            PdfSection(
                heading=step.title,
                paragraphs=[step.summary] + [f"Note: {n}" for n in step.notes],
                bullets=[f"{k}: {v}" for k, v in step.metrics.items()],
                style="compact",
            )
        )
    pdf_bytes = build_pdf_report(PdfReportSpec(
        title=f"Titan Flow Report — {result.title}",
        subtitle=f"{result.description}",
        sections=sections,
    ))

    core_files: List[Tuple[str, bytes]] = [
        ("report.pdf", pdf_bytes),
        ("results.csv", csv_bytes),
        ("results.tsv", tsv_bytes),
    ]
    readme_bytes = (
        "TITAN FLOW — consolidated pipeline package\n"
        f"Flow: {result.title}\n"
        f"Generated: {result.started_utc}\n\n"
        "Files:\n  report.pdf    — full scientific report\n"
        "  results.csv   — consolidated step metrics (CSV)\n"
        "  results.tsv   — consolidated step metrics (TSV)\n"
        "  manifest.json — SHA-256 provenance for every file\n"
        "  steps/        — per-step CSV + TSV detail tables\n\n"
        "Zero Data Retention: every payload was processed 100% in ephemeral\n"
        "RAM buffers and streamed straight to your browser in this download —\n"
        "the Titan servers keep no sequences, VCFs or FASTQ reads on disk.\n"
        "manifest.json retains SHA-256 fingerprints for verifiable provenance.\n"
    ).encode("utf-8")
    all_files = core_files + step_files + [("README.txt", readme_bytes)]
    manifest = flow_manifest(result, all_files)
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in all_files:
            zf.writestr(name, data)
        zf.writestr("manifest.json", manifest_bytes)
    return buffer.getvalue()
