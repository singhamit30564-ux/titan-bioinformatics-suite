"""Feature-expansion tests — ZDR privacy, 3D viewer, Titan Flow, Olympiad,
batch processor, ELN, PDF/export centers, publication studio, voice."""

import io
import json
import pathlib
import re
import sys
import zipfile

import pandas as pd
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


# ─────────────────────────────────────────────────────────────────────────────
# 1 · Zero Data Retention architecture (titan_utils/privacy.py)
# ─────────────────────────────────────────────────────────────────────────────
class TestZeroDataRetention:
    def test_sha256_provenance_known_vector(self):
        from titan_utils.privacy import sha256_hex, provenance_record

        # Well-known SHA-256 test vector.
        assert sha256_hex("abc") == (
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )
        rec = provenance_record("abc", kind="sequence", label="t")
        assert rec.digest == sha256_hex("abc")
        assert rec.algorithm == "SHA-256"
        assert rec.size_bytes == 3

    def test_provenance_manifest_chains_and_is_digets_only(self):
        from titan_utils.privacy import provenance_manifest

        manifest = provenance_manifest(
            [("input", "ATGC" * 10), ("output", "MEEP", "protein")]
        )
        assert manifest["zero_data_retention"] is True
        assert manifest["record_count"] == 2
        # No raw payloads retained in the manifest.
        blob = json.dumps(manifest)
        assert "ATGC" * 10 not in blob
        assert len(manifest["chained_digest"]) == 64

    def test_ephemeral_vault_scrubs_bytes(self):
        from titan_utils.privacy import EphemeralVault

        vault = EphemeralVault("ATGC" * 50, kind="sequence", label="unit")
        digest_before = vault.digest
        assert vault.data.startswith("ATGC")
        wiped = vault.scrub()
        assert wiped == 200
        assert vault.scrubbed is True
        assert vault.data == ""
        assert vault.size_bytes == 0
        # Provenance digest survives scrubbing (retention-free verification).
        assert vault.digest == digest_before

    def test_ephemeral_vault_context_manager_autoscrubs(self):
        from titan_utils.privacy import EphemeralVault

        with EphemeralVault("GGCC" * 25, label="ctx") as vault:
            assert vault.scrubbed is False
        assert vault.scrubbed is True

    def test_guard_disk_write_blocks_genomic_persistence(self):
        from titan_utils.privacy import (
            ZeroDataRetentionError,
            guard_disk_write,
        )

        with pytest.raises(ZeroDataRetentionError):
            guard_disk_write("reads.fastq", "anything")
        with pytest.raises(ZeroDataRetentionError):
            guard_disk_write("dump.txt", "ATGC" * 30)
        # Non-genomic artifacts may pass.
        guard_disk_write("report.pdf", b"%PDF-1.4 fake")
        guard_disk_write("manifest.json", '{"ok": true}')

    def test_sanitize_session_memory_1_click(self):
        from titan_utils.privacy import sanitize_session_memory

        state = {
            "sequence": "ATGC" * 40,
            "vcf_lines": "##fileformat=VCFv4.2\n#CHROM POS ID REF ALT",
            "tool_choice": "Central Dogma",
            "xp_points": 150,
        }
        report = sanitize_session_memory(state, also_vaults=True)
        assert report.vaults_scrubbed >= 0
        assert state["sequence"] == "[SCRUBBED]"
        assert state["tool_choice"] == "Central Dogma"
        assert state["xp_points"] == 150  # non-genomic UI state preserved
        assert "vcf_lines" not in state or state["vcf_lines"] == "[SCRUBBED]"
        assert report.total_actions >= 2
        assert "sanitized" in report.summary().lower()

    def test_is_genomic_text_classification(self):
        from titan_utils.privacy import is_genomic_text

        assert is_genomic_text("ATGC" * 30)
        assert is_genomic_text("@read1\n" + "ACGT" * 30 + "\n+\n" + "I" * 120)
        assert not is_genomic_text("Hello, ordinary prose.")
        assert not is_genomic_text(None)
        assert not is_genomic_text("short")


# ─────────────────────────────────────────────────────────────────────────────
# 2 · In-browser 3D molecular viewer (titan_utils/mol3d.py)
# ─────────────────────────────────────────────────────────────────────────────
class TestMol3DViewer:
    def test_presets_present(self):
        from titan_utils.mol3d import MOL3D_PRESETS, MOL3D_STYLES, get_preset

        assert set(MOL3D_PRESETS) == {"cas9", "hemo", "insulin"}
        assert MOL3D_STYLES == ("Cartoon", "Stick", "Sphere", "Surface")
        for pid in ("cas9", "hemo", "insulin"):
            preset = get_preset(pid)
            assert preset.pdb.count("ATOM") >= 50
            assert "END" in preset.pdb
            assert preset.residue_count > 0

    def test_preset_descriptions_reference_pdb(self):
        from titan_utils.mol3d import MOL3D_PRESETS

        assert "5AXW" in MOL3D_PRESETS["cas9"].citation
        assert "1HHO" in MOL3D_PRESETS["hemo"].citation
        assert "4INS" in MOL3D_PRESETS["insulin"].citation

    def test_viewer_html_embeds_3dmol_and_styles(self):
        from titan_utils.mol3d import build_preset_pdb, mol3d_viewer_html

        pdb = build_preset_pdb("hemo")
        for style in ("Cartoon", "Stick", "Sphere", "Surface"):
            html = mol3d_viewer_html(pdb, style=style)
            assert "3Dmol" in html
            assert "addModel" in html
            assert style in html
        # PDB text is embedded for client-side rendering.
        assert "ATOM" in mol3d_viewer_html(pdb)

    def test_pdb_coordinates_parse_by_column(self):
        from titan_utils.mol3d import build_preset_pdb

        atom = next(l for l in build_preset_pdb("insulin").splitlines() if l.startswith("ATOM"))
        float(atom[30:38])  # x
        float(atom[38:46])  # y
        float(atom[46:54])  # z
        assert atom[21] in "AB"


# ─────────────────────────────────────────────────────────────────────────────
# 3 · Titan Flow workflow builder (titan_utils/titan_flow.py)
# ─────────────────────────────────────────────────────────────────────────────
class TestTitanFlow:
    def test_all_four_flows_run(self):
        from titan_utils.titan_flow import TITAN_FLOWS, run_flow

        assert set(TITAN_FLOWS) == {
            "central_dogma", "crop_resilience", "clinical_oncology", "metagenomics"
        }
        for fid in TITAN_FLOWS:
            result = run_flow(fid)
            assert len(result.steps) == 5
            assert result.input_digest
            assert result.consolidated_rows()
            assert result.verdict

    def test_central_dogma_end_to_end(self):
        from titan_utils.titan_flow import run_flow

        result = run_flow("central_dogma", "ATGAAATAG")
        summaries = {s.step_id: s.summary for s in result.steps}
        assert "9 nt" in summaries["cd_validate"]
        assert "mRNA" in summaries["cd_transcribe"]
        # ZIP input fingerprint matches privacy.provenance.
        from titan_utils.privacy import sha256_of_text

        assert result.input_digest == sha256_of_text("ATGAAATAG")

    def test_clinical_hotspot_hits(self):
        from titan_utils.titan_flow import run_flow

        result = run_flow("clinical_oncology", "BRAF V600E\nKRAS G12C\nUNKNOWN X999Z")
        hotspot = next(s for s in result.steps if s.step_id == "onc_hotspot")
        assert "2/3" in hotspot.summary

    def test_flow_zip_package_consolidated(self):
        from titan_utils.titan_flow import build_flow_zip, run_flow

        result = run_flow("metagenomics")
        zbytes = build_flow_zip(result)
        zf = zipfile.ZipFile(io.BytesIO(zbytes))
        names = set(zf.namelist())
        assert {"report.pdf", "results.csv", "results.tsv", "manifest.json", "README.txt"} <= names
        assert any(n.startswith("steps/") for n in names)
        assert zf.read("report.pdf")[:5] == b"%PDF-"
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["zero_data_retention"] is True
        assert manifest["flow_id"] == "metagenomics"
        # Every packaged file (except the manifest itself) is digested.
        assert {f["name"] for f in manifest["files"]} == names - {"manifest.json"}
        for entry in manifest["files"]:
            assert re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])

    def test_zip_manifest_is_digest_only(self):
        """ZDR: the manifest keeps SHA-256 fingerprints, never raw payloads."""
        from titan_utils.titan_flow import build_flow_zip, run_flow

        secret = "ATGCGGCTTAA" * 30
        result = run_flow("central_dogma", secret)
        zbytes = build_flow_zip(result)
        zf = zipfile.ZipFile(io.BytesIO(zbytes))
        manifest = json.loads(zf.read("manifest.json"))
        assert secret not in json.dumps(manifest)
        assert result.input_digest in json.dumps(manifest)  # digest IS retained
        # README states the retention policy explicitly.
        assert b"Zero Data Retention" in zf.read("README.txt")


# ─────────────────────────────────────────────────────────────────────────────
# 4 · Bio-Olympiad & practice arena (titan_utils/olympiad.py)
# ─────────────────────────────────────────────────────────────────────────────
class TestOlympiad:
    def test_tiers_and_challenge_bank(self):
        from titan_utils.olympiad import CHALLENGES, TIERS, list_challenges

        assert TIERS == ("Foundational", "Intermediate", "Olympiad")
        assert len(CHALLENGES) >= 10
        for tier in TIERS:
            assert list_challenges(tier)

    def test_sample_datasets_self_grade(self):
        from titan_utils.olympiad import CHALLENGES, grade_attempt

        for ch in CHALLENGES:
            grade = grade_attempt(ch.id, ch.sample_input, ch.sample_output)
            assert grade.correct, f"{ch.id} sample failed: {grade.feedback}"
            assert grade.xp_earned == ch.xp

    def test_wrong_answers_earn_no_xp(self):
        from titan_utils.olympiad import grade_attempt

        grade = grade_attempt("DNA", "ACGTACGTACGTACGTACGTACGT", "0 0 0 0")
        assert grade.correct is False
        assert grade.xp_earned == 0
        assert "Not quite" in grade.feedback

    def test_whitespace_and_case_tolerant_grading(self):
        from titan_utils.olympiad import grade_attempt

        grade = grade_attempt("RNA", "ATGC" * 10, "  augc" * 10 + "  ")
        assert grade.correct

    def test_xp_totals_and_progress(self):
        from titan_utils.olympiad import grade_attempt, tier_progress, total_xp

        g1 = grade_attempt("DNA", "ACGTACGTACGTACGTACGTACGT", "6 6 6 6")
        g2 = grade_attempt("EDTA", "PLEASANTLY\nMEANLY", "5")
        assert total_xp([g1, g2]) == 250
        progress = tier_progress([g1, g2])
        assert progress["Foundational"]["solved"] == 1
        assert progress["Olympiad"]["xp"] == 200

    def test_hints_offline_fallback(self):
        """No API key → local hints, never a network call."""
        import os

        os.environ.pop("GROQ_API_KEY", None)
        from titan_utils.olympiad import get_hint, groq_llama_hint

        text, source = get_hint("IPRB")
        assert source == "Local Titan hint library"
        assert len(text) > 20
        assert groq_llama_hint("hello", api_key="") is None

    def test_known_solvers(self):
        from titan_utils.olympiad import CHALLENGES_BY_ID

        assert CHALLENGES_BY_ID["DNA"].solver("ACGTACGT") == "2 2 2 2"
        assert CHALLENGES_BY_ID["RNA"].solver("ATGC") == "AUGC"
        assert CHALLENGES_BY_ID["REVC"].solver("AAAACCCGGT") == "ACCGGGTTTT"
        assert CHALLENGES_BY_ID["IPRB"].solver("2 2 2") == "0.78333"
        assert CHALLENGES_BY_ID["PROT"].solver(
            "AUGGCCAUGGCGCCCAGAACUGAGAUCAAUAGUACCCGUAUUAACGGGUGA"
        ) == "MAMAPRTEINSTRING"


# ─────────────────────────────────────────────────────────────────────────────
# 5 · High-throughput batch processor (titan_utils/batch_processor.py)
# ─────────────────────────────────────────────────────────────────────────────
class TestBatchProcessor:
    def test_parse_multi_fasta(self):
        from titan_utils.batch_processor import parse_multi_fasta

        records = parse_multi_fasta(">a first\nATGCATGC\nGGCC\n>b\nTTTTAAAA")
        assert len(records) == 2
        assert records[0].name == "a"
        assert records[0].sequence == "ATGCATGCGGCC"
        assert records[1].length == 8

    def test_parse_tolerates_bare_sequence(self):
        from titan_utils.batch_processor import parse_multi_fasta

        records = parse_multi_fasta("ATGCATGCATGCATGCATGC")
        assert len(records) == 1
        assert records[0].name == "record_1"

    def test_run_batch_metrics_and_digests(self):
        from titan_utils.batch_processor import DEFAULT_BATCH_FASTA, run_batch

        result = run_batch(DEFAULT_BATCH_FASTA)
        assert result.record_count == 5
        df = result.to_frame()
        assert {"Record_ID", "Length_bp", "GC_Percent", "SHA256"} <= set(df.columns)
        assert all(len(h) == 64 for h in df["SHA256"])
        summary = result.summary()
        assert summary["zero_data_retention"] is True
        assert summary["total_bp"] == df["Length_bp"].sum()

    def test_build_batch_zip_contents(self):
        from titan_utils.batch_processor import build_batch_zip, run_batch

        result = run_batch(">x\n" + "ATGC" * 40)
        zf = zipfile.ZipFile(io.BytesIO(build_batch_zip(result)))
        names = set(zf.namelist())
        assert {
            "batch_results.csv", "batch_results.tsv", "batch_summary.json",
            "records.fasta", "manifest.json", "README.txt",
        } == names
        assert zf.read("records.fasta").startswith(b">x")
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["tool"].startswith("Titan High-Throughput")
        assert {f["name"] for f in manifest["files"]} == names - {"manifest.json"}


# ─────────────────────────────────────────────────────────────────────────────
# 6 · Electronic lab notebook (titan_utils/eln.py)
# ─────────────────────────────────────────────────────────────────────────────
class TestELN:
    def test_log_run_records_sha256_digests(self):
        from titan_utils.eln import ELNLog, sequence_digest

        log = ELNLog()
        rec = log.log_run("Unit Module", input_data="ATGC" * 10, output_data="res")
        assert rec.input_digest == sequence_digest("ATGC" * 10)
        assert rec.output_digest == sequence_digest("res")
        assert rec.run_id.startswith("TITAN-")
        assert len(log) == 1
        assert log.audit_table()[0]["Input_SHA256"].endswith("…")

    def test_markdown_glp_export(self):
        from titan_utils.eln import ELNLog, export_markdown

        log = ELNLog()
        log.log_run("Flow", input_data="ATGC" * 20, summary="demo run", parameters={"k": 2})
        md = export_markdown(log)
        assert "# Electronic Lab Notebook" in md
        assert "GLP" in md and "ALCOA" in md
        assert "SHA-256" in md
        assert "Attributable" in md
        assert "k" in md  # parameters rendered

    def test_pdf_glp_export(self):
        from titan_utils.eln import ELNLog, export_pdf

        log = ELNLog()
        log.log_run("Batch", input_data=">a\nATGC", summary="batch run")
        pdf = export_pdf(log)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 1000

    def test_json_export_is_digest_only(self):
        from titan_utils.eln import ELNLog

        log = ELNLog()
        secret = "CGTACGTACGTACGTACGTACGTA"
        log.log_run("X", input_data=secret)
        blob = log.to_json()
        assert secret not in blob
        assert "input_sha256" in blob


# ─────────────────────────────────────────────────────────────────────────────
# 7 · PDF generator + multi-format export center
# ─────────────────────────────────────────────────────────────────────────────
class TestPdfGenerator:
    def test_scientific_report_builds(self):
        from titan_utils.pdf_generator import (
            PdfReportSpec,
            PdfSection,
            build_pdf_report,
            build_simple_pdf,
        )

        pdf = build_pdf_report(
            PdfReportSpec(
                title="Study 🧬 of Things",
                subtitle="emoji-heavy copy ✓",
                sections=[
                    PdfSection(heading="Intro", paragraphs=["Body — text."], bullets=["b1", "b2"]),
                    PdfSection(heading="Table", table=(["A", "B"], [[1, 2], [3, 4]])),
                    PdfSection(heading="Seq", preformatted=">s1\nATGC"),
                ],
            )
        )
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 1500
        simple = build_simple_pdf("Title", "Line one.\n\nLine two.")
        assert simple[:5] == b"%PDF-"

    def test_pdf_safe_text_strips_unsafe_chars(self):
        from titan_utils.pdf_generator import pdf_safe_text

        clean = pdf_safe_text("Hello 🧬 — world ✓")
        assert "Hello" in clean and "world" in clean
        assert all(ord(c) < 256 for c in clean)


class TestExportCenter:
    def test_all_five_formats(self):
        from titan_utils.export import EXPORT_FORMATS, build_export

        df = pd.DataFrame({"A": [1, 2], "B": ["x", "y"]})
        records = {"s1": "ATGC" * 10, "s2": "GGCC" * 10}
        assert EXPORT_FORMATS == ("csv", "tsv", "json", "fasta", "fastq")
        assert b"A,B" in build_export("csv", df)
        assert b"A\tB" in build_export("tsv", df)
        assert b'"A"' in build_export("json", df)
        assert build_export("fasta", records).startswith(b">s1")
        fastq = build_export("fastq", records)
        assert fastq.startswith(b"@s1") and b"\n+\n" in fastq

    def test_unknown_format_raises(self):
        from titan_utils.export import build_export

        with pytest.raises(ValueError):
            build_export("docx", {})

    def test_export_filenames(self):
        from titan_utils.export import export_filename, export_mime

        assert export_filename("My Result!", "csv") == "My_Result_.csv"
        assert export_mime("fastq") == "text/plain"


# ─────────────────────────────────────────────────────────────────────────────
# 8 · Publication studio + voice assistant
# ─────────────────────────────────────────────────────────────────────────────
class TestPublicationStudio:
    def test_okabe_ito_palette(self):
        from titan_utils.publication_studio import (
            OKABE_ITO,
            okabe_ito_palette,
        )

        assert len(OKABE_ITO) == 8
        palette = okabe_ito_palette(5)
        assert len(palette) == 5
        assert all(c.startswith("#") and len(c) == 7 for c in palette)
        assert palette == okabe_ito_palette(5)  # deterministic
        assert len(okabe_ito_palette(12)) == 12  # cycles

    def test_journal_styles(self):
        from titan_utils.publication_studio import (
            JOURNAL_STYLES,
            journal_style,
            list_journals,
            mpl_rc_params,
        )

        assert list_journals() == ["Nature", "Science", "Cell"]
        for journal in list_journals():
            style = journal_style(journal)
            assert style["background"] == "#ffffff"
            assert style["palette"]
            assert mpl_rc_params(journal)["savefig.dpi"] == 300
        assert journal_style("Lancet") is JOURNAL_STYLES["Nature"]  # fallback

    def test_apply_journal_style_to_plotly_figure(self):
        import plotly.graph_objects as go

        from titan_utils.publication_studio import apply_journal_style

        fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[1, 4, 9], mode="lines+markers"))
        styled = apply_journal_style(fig, "Nature", title="Fig. 1")
        assert styled.layout.paper_bgcolor == "#ffffff"
        assert styled.layout.font.family.startswith("Times")
        assert styled.layout.title.text == "Fig. 1"

    def test_publication_figure_html(self):
        import plotly.graph_objects as go

        from titan_utils.publication_studio import publication_figure_html

        fig = go.Figure(go.Bar(x=["a", "b"], y=[1, 2]))
        html = publication_figure_html(fig, "Cell", "Fig. 2")
        assert "Okabe-Ito" in html
        assert "Cell" in html


class TestVoiceAssistant:
    def test_strip_markup(self):
        from titan_utils.voice_assistant import strip_markup

        assert strip_markup("# Title **bold** `code` <b>html</b>") == "Title bold code html"

    def test_narration_html_client_side(self):
        from titan_utils.voice_assistant import narration_html

        html = narration_html("GC content is 42.5 percent.", autoplay=True)
        assert "speechSynthesis" in html
        assert "GC content is 42.5 percent." in html
        assert "42.5" in html
        # No server-side TTS endpoints — narration is browser-local.
        assert "http" not in html.replace("http-equiv", "")

    def test_summarize_for_speech_trims(self):
        from titan_utils.voice_assistant import summarize_for_speech

        long_text = "Sentence one is here. " * 100
        short = summarize_for_speech(long_text, max_chars=200)
        assert len(short) <= 230


# ─────────────────────────────────────────────────────────────────────────────
# 9 · Wiring — runner / pages / Home integration
# ─────────────────────────────────────────────────────────────────────────────
class TestWiring:
    def test_runner_exposes_advanced_export_center(self):
        src = (ROOT / "titan_tools" / "runner.py").read_text()
        assert "Advanced Export Center" in src
        assert "provenance_record" in src
        assert "Log this run to ELN" in src
        assert "narration_html" in src

    def test_new_pages_exist_and_use_titan_utils(self):
        for name in (
            "75_Titan_Flow_Pipeline_Builder.py",
            "76_Bio_Olympiad_and_Practice_Arena.py",
            "77_Batch_Processor_and_Archive.py",
            "78_Electronic_Lab_Notebook_Audit.py",
        ):
            path = ROOT / "pages" / name
            assert path.exists(), name
            assert "from titan_utils" in path.read_text()

    def test_home_nav_references_studio_pages(self):
        home = (ROOT / "Home.py").read_text()
        for name in (
            "75_Titan_Flow_Pipeline_Builder.py",
            "76_Bio_Olympiad_and_Practice_Arena.py",
            "77_Batch_Processor_and_Archive.py",
            "78_Electronic_Lab_Notebook_Audit.py",
        ):
            assert f'"{name}"' in home, f"Home.py missing {name}"

    def test_hub_wires_studio_features(self):
        hub = (ROOT / "pages" / "00_Tool_Palette_and_Hub.py").read_text()
        assert "render_mol3d_viewer" in hub
        assert "sanitize_session_memory" in hub
        assert "75_Titan_Flow_Pipeline_Builder.py" in hub

    def test_requirements_include_reportlab(self):
        reqs = (ROOT / "requirements.txt").read_text().lower()
        assert "reportlab" in reqs
