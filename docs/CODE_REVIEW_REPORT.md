# 🔬 Titan Bioinformatics Suite — Full Code Review & Improvement Report

**Reviewed:** 2026-10-10 · branch `arena/33a3af08-titan-bioinformatics-suite` @ `75b861c`
**Scope:** All 112 Python files (~24,900 LOC), 68 pages, tests, CI, docs, and runtime behavior
**Method:** Static analysis (pyflakes), full test-suite run, live App boot + AppTest reproductions, targeted scientific-correctness probes against Biopython

---

## 1. Executive Summary

Titan is an ambitious, largely well-engineered educational bioinformatics platform. The Streamlit plumbing is solid, the FastAPI layer is genuinely careful about privacy and input bounds, the codon table is provably correct, and the interaction-test suite (render + click every button on every page) is better than what most production apps have.

However, the review found **one confirmed app-crashing bug affecting 50 of the 260 advertised tools**, several **scientific-integrity problems where tools fabricate or ignore results while claiming analysis** (worst case: a "variant pathogenicity" tool that labels *any* input — including the text `hello world` — as a "TIER 1A PATHOGENIC CANCER DRIVER at 99% confidence"), a large block of **dead UI** (fake export buttons that the README claims were removed), and significant **doc↔code drift**.

**Overall grade: solid engineering chassis (B+), but the science layer needs an honesty-and-correctness pass (currently C−), and the Hub has a P0 crash.**

### Top-line findings

| # | Severity | Finding | Evidence |
|---|---|---|---|
| 1 | 🔴 P0 | Hub tools #3–#52 crash with uncaught `TypeError` when selected | Reproduced live in AppTest (§2.1) |
| 2 | 🔴 P0 | 50/260 registry tools are a GC-content stub labeled "Processed Successfully"; README claims "260 Validated Tools" | `titan_utils/registry.py`, `generate_registry.py` (§2.2) |
| 3 | 🔴 P0 | `tool_dr_titan_variant_pathogenicity` prints BRAF V600E + Tier 1A for *any* input, incl. `hello world` | `titan_tools/dr_titan.py:39` (§2.3) |
| 4 | 🔴 P0 | "NCBI & Global APIs" tools are hardcoded mock dicts that **fabricate data for unknown accessions**; console subtitle claims "Direct live access" | `titan_tools/ncbi_db.py` (§2.4) |
| 5 | 🟠 P1 | Runner swallows every handler exception and re-runs with **default** inputs, rendering results as if they came from the user's input | `titan_tools/runner.py:92–100` (§2.5) |
| 6 | 🟠 P1 | ~30 tool handlers compute then ignore their input (`seq` unused) and print canned "Detected" verdicts | pyflakes; e.g. `tool_bgc_domain_scanner` (§2.6) |
| 7 | 🟠 P1 | "MSA" pages do not align — they right-pad with dashes, then run conservation stats on the fiction | `pages/44` (§2.7) |
| 8 | 🟠 P1 | Tm page applies a long-DNA salt correction (16.6·log₁₀[Na⁺]) on top of the Wallace rule → wildly negative Tms for short primers | `pages/33` (§2.8) |
| 9 | 🟠 P1 | 10 pages + `smart_lock` still show dead "PDF export — coming in v1.1" buttons even though `titan_utils/pdf_generator.py` exists and works | §3.1 |
| 10 | 🟡 P2 | Zero `st.cache_data`/`cache_resource` anywhere; no `max_file_size` on any uploader; pure-Python O(n·m) Levenshtein with no length cap (freeze vector) | §4 |
| 11 | 🟡 P2 | 494 pyflakes warnings (451 unused imports; a few mask real bugs), deprecated `Bio.pairwise2` on 4 pages, `use_container_width` deprecated in installed Streamlit 1.65 | §5 |
| 12 | 🟡 P2 | ZDR "guard" (`guard_disk_write`, `EphemeralVault`) is never wired into app code — only tests call it | §6.2 |
| 13 | 🟢 P3 | Docs drift: version 3.0 vs 3.1, "52/62/63 pages" vs 68 actual, "127/208/229 tests" vs 220 actual; `MASTERPLAN.md` is a headerless broken TSV | §7 |

**Test suite baseline (verified on this machine):** `pytest tests/ -q` → **219 passed, 1 skipped** in ~36 s. App boots clean (`HTTP 200`). Codon-table cross-check vs Biopython: **0 mismatches on all 64 codons** ✅.

---

## 2. Critical: correctness & scientific integrity (P0/P1)

### 2.1 🔴 Hub crash — tools #3–#52 (confirmed by live reproduction)

`titan_tools/runner.py` calls `handler(**inputs_dict)`, where `inputs_dict` contains only the registry-declared inputs (`sequence`). For legacy tools the handler is:

```python
def tool_legacy_generic(tool_id: int, tool_name: str, sequence: str = ...)
```

`tool_id`/`tool_name` are never in `inputs_dict` → `TypeError` → the `except TypeError:` fallback calls `handler()` → **second `TypeError`, uncaught → red traceback box**. Reproduced by driving `pages/00_Tool_Palette_and_Hub.py` in AppTest and selecting Tool #3:

```
TypeError: tool_legacy_generic() missing 2 required positional arguments: 'tool_id' and 'tool_name'
```

This is invisible to the current interaction tests because the hub's default selection is Tool #1 (real handler) and AppTest only clicks buttons in default state — the crash is reachable via the *selectbox*, which tests never change (see §5.3).

**Fix:** pick one (a+c minimum):
a. Make `render_tool_runner` inject `tool_id`/`tool_name` for the generic adapter (inspect signature), **and**
b. make the fallback error path render `st.error` with the exception instead of re-running with defaults (§2.5), **and**
c. extend hub tests to select a few representative tools from each category (incl. a legacy generic one) via `selectbox.set_value()`.

### 2.2 🔴 50 of 260 hub tools are stubs marketed as "Validated"

`scripts/generate_registry.py` assigns `tool_legacy_dna_rna_convert` to id 1, `tool_legacy_revcomp` to id 2, and `tool_legacy_generic` to **everything else in 1–52** — a canned table of `Length` + `GC%` + "Processed Successfully", regardless of whether the tool is "ORF Finder", "CRISPR gRNA Designer" or "BLAST". Meanwhile the standalone pages implement real logic, so the same task works on `pages/05` but returns a fake GC table in the Hub.

This is a duplication-of-truth design flaw: pages embed logic that the registry can't reach.

**Fix (structural, worth doing once):** extract each page's compute function into `titan_utils/compute/<name>.py` (or into `titan_tools/legacy_adapters.py`), have both the page and a thin per-tool handler call it, and regenerate the registry to point at the real functions. Interim honesty fix: for stub-mapped tools, have the hub render a "Open dedicated page" call-to-action instead of executing the GC stub, and reword the README badge from "260 Validated Tools" to what's actually true (e.g. "68 dedicated tools + 200 registry-mapped console tools").

### 2.3 🔴 Fabricated clinical verdict — `tool_dr_titan_variant_pathogenicity`

Verified behavior (direct call):

```
'BRAF:c.1799T>A:p.V600E' → Analyzed BRAF:c.1799T>A:p.V600E. Diagnosis: TIER 1A PATHOGENIC CANCER DRIVER.
'CFTR:p.F508del'         → Analyzed CFTR:p.F508del. Diagnosis: TIER 1A PATHOGENIC CANCER DRIVER.
'hello world'            → Analyzed hello world. Diagnosis: TIER 1A PATHOGENIC CANCER DRIVER.
''                       → Analyzed . Diagnosis: TIER 1A PATHOGENIC CANCER DRIVER.
```

The entire table (T→A transversion at 1799, Val→Glu at 600, Dabrafenib+Trametinib recommendation) plus a 99%-confidence gauge is hardcoded BRAF content; the user string is only interpolated into the summary. For a suite marketed at "clinical precision oncology" and used by students, this is the single most dangerous file in the repo.

**Fix:** parse `GENE:c.posREF>ALT:p.Xn>Ym`; ship a small curated hotspot table (BRAF V600E, KRAS G12, EGFR L858R, CFTR F508del, HBB E6V… — 15–25 entries are enough for a teaching tool); for unrecognized input return "no annotation available — this is an educational demo, not a clinical classification". Add a permanent `st.warning` disclaimer to all clinical-domain tools. A CI test should assert *input-sensitivity* for every tool that declares a text input (§5.3).

### 2.4 🔴 "NCBI & Global Bioinformatics APIs" are offline mocks that hallucinate

`titan_tools/ncbi_db.py` (Tools 213–232) imports `urllib` but never calls the network. Unknown accessions get **invented values**: `NM_999999` → "Parsed Entrez GenBank record for NM_999999: NM_999999 Specimen (12,500 bp)". The console subtitle in `pages/73` says *"Direct live access to NCBI Entrez…"*. Students learning "how to look things up in GenBank" would be taught that a nonexistent accession has 12,500 bp.

**Fix (two-step):**
1. Immediately: return a clean "accession not found in the offline demo set" result, rename the subtitle to "Simulated NCBI record inspector (offline demo)", and gate the "live" wording.
2. Real integration: NCBI E-utilities is a plain `urllib.request` GET (`esummary.fcgi`, `efetch.fcgi`) — this repo already has the perfect template in `titan_utils/olympiad.py::groq_llama_hint` (env-gated, `timeout=`, broad except → offline fallback). Add an optional `TITAN_NCBI_LIVE=1` mode with the official 3 req/s throttle, an email/API-key env var per NCBI policy, and a "LIVE/OFFLINE" badge on every result so provenance is unambiguous.

### 2.5 🟠 Runner error-swallowing produces *confidently wrong* results

```python
try:
    res = handler(**inputs_dict)
except TypeError:
    res = handler()                       # silently runs on DEFAULT input
except Exception as ex:
    st.warning("…standard baseline parameters…")
    res = handler()                       # same, plus a buried warning
```

Any handler crash → results computed on placeholder sequences are rendered as if they answered the user's query, feeding wrong numbers into the CSV/PDF/ELN/SHA-256 provenance pipeline as though they were real (a provenance trail for a result that isn't what the user asked for is worse than no trail). **Fix:** on failure, show `st.error` with the exception, keep provenance for the *input* only, and never auto-substitute defaults.

### 2.6 🟠 Canned-verdict handlers that parse then ignore their input

`seq = sequence.upper().strip()` followed by never using `seq` (≈30 sites flagged by pyflakes in `titan_tools/*.py`, e.g. `tool_bgc_domain_scanner` prints all four NRPS domains "Detected" for the input `ATGCA`, and `tool_plant_secondary_metabolite_cluster` "detects" a P450 whenever the sequence contains a G anywhere). Some of these are honest teaching presets, but none of them *say* so. **Fix:** each such tool should either (a) actually match its signature motifs against the input, or (b) label the output "Example preset — enter a real NRPS/PKS sequence to scan" and gate the metrics. Also use the *computed* values: `tool_salt_bridge_finder` computes a Coulombic `energy` then reports a hardcoded `−3.5`.

### 2.7 🟠 "Multiple Sequence Alignment" doesn't align

`pages/44` (and 45) parse FASTA, then `ljust(max_len, '-')` — no gap insertion, no guide tree, no scoring. Per-column "conservation" on that is measuring the input's own prefix, and the default data even contains `ATGCA_TACGTAGCTAG` (invalid `_`, silently kept). Roadmap Phase 3 already admits this. **Fix options:** (1) honest rename to "Ungapped profile + conservation viewer" now; (2) implement progressive profile alignment over `Bio.Align.PairwiseAligner` distance matrix (all-python, no external tools — feasible for ≤20 sequences ≤2 kb); (3) call EBI Clustal Omega REST as optional live mode like §2.4.

### 2.8 🟠 Tm math — `pages/33_Advanced_Tm_Calculator.py`

* `tm_wallace = 2*AT + 4*GC` is *defined* for short oligos in physiological salt; adding `16.6·log10([Na⁺]/1M)` (a Schildkraut-Lifson correction meant for long duplexes calibrated at 1 M) drives a 12-mer poly-A from 24 °C to 2.4 °C. The `64.9 + 41·(GC−16.4)/len` branch is likewise already a "salt-defined" empirical formula → double-correction.
* No nearest-neighbor option, though the master plan promises "NN + Wallace".
* **Fix:** implement SantaLucia 1998 NN with the standard `[Na⁺]` correction *inside* the NN framework (`ΔS° += 0.368·N·ln[Na⁺]`), keep Wallace as a labeled quick rule with no salt term, and show per-method formulas. Seed `16` (pI) shows the right pattern — it delegates to `Bio.SeqUtils.ProtParam` after its fix.

### 2.9 Similar integrity nits worth sweeping at the same time

* `pages/60_BLAST_Local_Search.py` — exact-seed & extend with unit match scores, no scoring matrix, no E-value. Rename to "Seed-&-Extend (BLAST simulator)", and either add a Karlin-Altschul style E-value estimate or state why there isn't one.
* `pages/09_Hamming_Edit_Distance.py` — validates with its own inline `any(char not in "ATCG")` while importing (unused) `validate_dna`; two error-handling idioms per page invite drift (also the pattern behind 451 unused imports).
* `tool_codis_match_probability`-style population tools should surface their assumptions (`p_locus = 0.05` is buried; the "1 in a trillion" headline depends entirely on it).
* `titan_utils/sequence.py:translate()` silently emits `X` for ambiguous codons — fine, but the DNA→protein page should count and report X's so students notice IUPAC input changed the result.

---

## 3. Dead & misleading UI

### 3.1 Placeholder exports on ~10 pages (despite the machinery existing)

Pages 03, 04, 05, 06, 07, 08, 09, 10, 11, 20 and `titan_utils/ui.py:smart_lock` show a PDF button that just prints "Feature coming in v1.1" — while `titan_utils/pdf_generator.py::build_pdf_report` already produces real reports inside `runner.py`. Page 09 goes further: a button labeled "📊 Download CSV (🔒 Explorer)" prints "✅ CSV export unlocked" and exports **nothing** — the exact fake paywall the README says was removed in PR #2 (README: "Paywall removed").

**Fix:** one helper `render_exports(df, title, sections)` in `titan_utils/ui.py` that wires `df_to_csv_bytes` + `build_pdf_report` + `st.download_button`; then delete the placeholders and update `smart_lock`. This is a half-day task that closes ~15 misleading buttons and makes the README true again.

### 3.2 i18n coverage vs promise

Only 10 pages' bodies are translated (`i18n.py:16`), yet the sidebar advertises हिंदी everywhere and 230 `t()` calls across 68 pages return English passthrough for most bodies. The dict-keyed-by-exact-English-string design also means any copy edit silently un-translates a string. **Fix:** move to key-based catalogs (JSON/YAML per locale), fail CI on missing keys for pages in `SUPPORTED_HINDI_TOOL_PAGES`, and make the selector honestly say "Hindi beta — 10 pages".

---

## 4. Performance, robustness & scale (P2)

| Area | Problem | Fix |
|---|---|---|
| Caching | **0** uses of `st.cache_data`/`st.cache_resource` in the whole repo; every widget change re-runs handlers (hub consoles run on *every rerun* via `auto_run=True`), re-parses enzyme tables, re-renders PDF bytes in `_render_export_center` | Decorate pure compute functions with `st.cache_data(ttl=…)` keyed by sequence digest (you already have `sequence_digest`!); build PDFs only when the download is clicked (or cache by payload hash) |
| Uploads | `st.file_uploader` on pages 20/27/77 with no `max_file_size` (0 usages repo-wide); FASTA parsing via `s += line` is O(n²) | `max_file_size=5–10`, stream via `Bio.SeqIO.parse(io.TextIOWrapper(uploaded))`, cap records with a "first N + count total" strategy and `st.status` progress |
| Hot algorithms | Levenshtein in pure Python per rerun with no cap (two 10 kb strings ≈ 10⁸ cell ops → frozen tab); CGR loop per point; dot-plot O(n²); pairwise pages O(n·m) Python DP | Guard rails (`if max_len > 2000: st.error`) now; then numpy-vectorize rows, or use `Bio.Align.PairwiseAligner` (C-impl) which replaces three hand-rolled DP pages at once |
| Regex | User pattern passed straight to `re.compile` in motif pages; pathological patterns hang the server thread (ReDoS) | Try/except `re.error`, cap pattern length, and offer "literal" vs "regex" modes |
| Deprecations | 4 pages on `Bio.pairwise2` (deprecated, warning in CI); `use_container_width` is deprecated in Streamlit 1.65 (removal announced 2025-12-31 — already past!) and used on dozens of widgets; pinned CI uses `>=1.37` so behavior will diverge | Migrate to `Bio.Align.PairwiseAligner`; sweep to `width='stretch'`; pin `streamlit>=1.45,<2` (or the tested version) and set `biopython>=1.84` |
| Concurrency | Classroom quiz rooms are process-local dicts (documented, but undetected); Home.py wraps `st.navigation` in `except Exception:` which silently degrades nav to quick-links | Detect multi-worker (`os.environ`, or a heartbeat PID check) and banner it; narrow the Home.py except to a log + `st.exception` |
| Offline | 3Dmol.js and Plotly.js load from CDN, while the 3D viewer is sold as "fully client-side" | Vendor the JS in `static/` and serve locally, or state the network requirement |

---

## 5. Tests, CI & code quality

### 5.1 Baseline quality — genuine strengths to keep

* Interaction tests render **every** page and click **every** button, and treat both uncaught exceptions *and* `st.error` banners as failures. That's rare and excellent.
* `titan_utils/api.py` is the model citizen: allow-listed tools, bounded payloads (50 kb, k≤12, 1 000 items), rolling-window rate limiter with bounded memory, `Cache-Control: no-store`, provenance hashes, access-log suppression, GET+POST (POST to keep sequences out of URL history).
* `_widget_key` content-hash fix (id() recycling), GA-keyed widget discipline, and the codon table verified 64/64 vs Biopython.

### 5.2 What static analysis found

`pyflakes` over the full tree (incl. `titan_tools/` and `scripts/`, which CI *doesn't* check): **494 warnings — 451 "imported but unused", 43 substantive**, including the ~30 "computed then unused" locals in §2.6 and 4 f-strings with no placeholders. CI only fails on `undefined name`/`redefinition`, and only for `pages/`+`titan_utils/`+`Home.py`.

**Fix:** adopt `ruff` with a committed `pyproject.toml` (`select = ["F","E9","B","SIM","UP"]`); `ruff check --fix` auto-clears the 451 unused imports in one commit; then run ruff over **the whole repo** in CI and ratchet `ignore` list down instead of growing it. Add `ruff format` (or black) + `pre-commit`; add `py_compile`-equivalent for `titan_tools/`.

### 5.3 Missing test classes (highest ROI first)

1. **Registry↔handler resolution:** assert `get_handler()` is non-None for all 260 specs and that handler signatures are satisfiable from the spec's declared inputs (would have caught §2.1 and any future typo).
2. **Input-sensitivity contract:** for every tool with a text input, `tool(x1)` ≠ `tool(x2)` for two probes, *or* the tool is listed in a registry field `static_preset=True` and the UI renders the preset badge. This mechanically enumerates §2.3/§2.6-style fakes.
3. **Golden science data:** Tm vs Primer3 on ~10 oligos; pI vs EMBOSS `iep`; 6-frame translation of a real RefSeq CDS vs `Bio.Seq.translate` (already proven for the table — extend to frames); UPGMA tree on 5 fixed sequences; EcoRI/BamHI cut sites on λ DNA.
4. **Hub deep-link test:** change the tool selectbox to one tool per category and assert clean render (finds §2.1 without a dedicated crash test).
5. **`pytest.ini` hygiene:** add `filterwarnings = error::DeprecationWarning` (scoped) so Biopython/Streamlit deprecations break CI *before* they break users.
6. Coverage: add `pytest-cov`, report % on `titan_utils/` (the pure-logic layer is where 80% is realistically achievable) — currently most of the 260 handlers have no direct assertions at all.

### 5.4 CI/build improvements

* Matrix `python-version: ["3.10","3.12","3.13"]` (devcontainer says 3.11; requirements say 3.10+; nothing tests 3.12/3.13 today).
* Add `pip-compile`-style constraints or a `requirements.lock` — `>=` floors mean CI today ≠ CI tomorrow (this repo already got bitten once by pandas `Styler.applymap` removal, per the README's own fix log).
* Cache the AppTest suite is the slow job; split "unit" vs "interaction" as the README already implies, mark interaction tests `@pytest.mark.slow` and run per-PR.
* Add Dependabot (`pip` + `github-actions`), an issue/PR template, and a CI status badge on real CI (README badges are static shields with hand-maintained numbers).

---

## 6. Security & privacy review

### 6.1 Good (verified, keep)

No `eval/exec/pickle/subprocess` anywhere; no secrets committed (Groq key only ever read from env); no disk writes for analysis data (all exports are in-RAM bytes → `st.download_button`); FastAPI limits + `no-store`; usage stats off in `.streamlit/config.toml`.

### 6.2 Gaps to close

1. **Optional-API default bind is `0.0.0.0` with no auth** (`titan_utils/api.py:__main__`). A rate-limited public endpoint is fine, but the README's "deploy" instructions plus a `0.0.0.0` default invites careless exposure. **Fix:** default `127.0.0.1`, require an explicit flag to bind publicly, and add optional `TITAN_API_TOKEN` bearer auth + `CORSMiddleware` config. (The 60/min limit is also per-`request.client.host` — behind any proxy that's the proxy IP; document `--proxy-headers`/`FORWARDED_ALLOW_IPS` for uvicorn.)
2. **ZDR guards are decorative.** `guard_disk_write`/`EphemeralVault`/`sanitize_session_memory` exist and are unit-tested, but grep shows **zero** call sites in app code. The "100% ephemeral in-RAM" claim is currently *true by accident* (nobody writes files), not *enforced*. **Fix:** either thread the vault/guard into the upload & export paths, or soften the policy language to "no code path writes to disk" + keep the sanitizer. Right now `assert_ephemeral_path` is a promise nobody presents at.
3. **Voice widget injection (low sev, easy fix).** `narration_html` escapes backticks and `${` but not `</script>` inside the JS template literal; a crafted sequence echo in `res.summary` can close the script tag and run JS **inside the component iframe** (self-XSS, same-origin component messages). **Fix:** `.replace("</", "<\\/")` plus HTML-escape `spoken_js` consistently; do the same audit for `mol3d` embedding.
4. **Classroom rooms** are unauthenticated 4-char codes — fine for a classroom toy, but add a "rooms are public to anyone with the code" note in the host UI and cap joins/answers per room (currently only a student limit).

---

## 7. Documentation & repo hygiene drift (fix in one pass)

* README says v3.0 + "52 tool pages" + "63 pages" + "127/208/229 tests" in different sections; actual: version string `v3.1` in `Home.py`, **68** page files, **220** tests. Badges are hand-tuned shields, CI status isn't shown.
* `MASTERPLAN.md` renders as a broken tab-separated fragment (a table without header/pipe syntax) — convert to a proper checklist table or fold into a GitHub Project board and delete.
* `scripts/generate_registry.py` contains a real typo: the title-fixups map has `("Ms A", "MSA")` instead of `("Msa", "MSA")`, so generated registry names render "Msa Clustalw Format"; its title-casing logic is a *copy* of Home.py's (third copy lives in the page-title regex pipeline) — all three will drift. Extract one `titan_utils/naming.py:pretty_title(filename)`.
* No `CHANGELOG.md`, no `pyproject.toml` (the repo can't be `pip install -e`'d; that's also why tests need `conftest.py` sys.path hacking), no Dockerfile despite README deployment instructions, no docs/ site.
* `pytest addopts -q` hides per-test results in CI; CI overrides with `-v`, fine — but add `-ra` to summarize skips (one page always skips as "no buttons" — that's page 79's tab flow, worth an explicit test instead).

---

## 8. What to add (roadmap, in priority order)

### 8.1 Short wins (each ≤ 1 day)

1. Fix §2.1 hub crash + §3.1 export wiring — **before any new features**.
2. ruff sweep (451 warnings vanish) + whole-repo lint in CI.
3. `max_file_size` on all three uploaders + upload-length guards on Levenshtein/dot-plot/CGR.
4. Registry generator single-source titles + "260 handler-resolution" test.
5. Honest labels pass: rename "live"/"AI"/"BLAST"/"MSA" wording per §2.4/§2.3/§2.7/§2.9, add an `EDU_DEMO` badge on any `static_preset` tool (one styled `st.caption`, reused everywhere).

### 8.2 Feature work the codebase is one refactor away from

6. **Real NCBI live mode** (E-utilities via urllib with §2.4's fallback pattern; `LIVE/OFFLINE` badge; results cache with TTL) — delivers the un-checked "Phase 2" roadmap item.
7. **Shared compute layer + page↔hub unification** (end §2.2 for good): every tool = one pure function in a package, page and hub and FastAPI all call it; the FastAPI allow-list then grows to "all tools" almost free.
8. **Progressive MSA** over `PairwiseAligner` (≤20×2 kb) → real Clustal-style output on pages 44/45, feeding a *real* sequence-logo/conservation story on 48.
9. **Nearest-neighbor Tm suite** (SantaLucia NN tables in `titan_utils/thermo.py`, used by pages 03/33/57/58 + `titan_tools` oligo tools) with salt & formamide corrections — also replaces the scattered 2+4/4(G+C) reimplementations.
10. **Session history browser** (Phase 5 item): ELN `RunRecord`s already exist; add a global "My runs" tab (in-RAM, ZDR-consistent) with re-run/compare and provenance diffing.
11. **LLM "Dr. Titan Copilot" behind an env key** like the Olympiad hint path (Groq already integrated there — reuse for page 74's promised "Gemini-powered" tools; today they are pure templates, and MASTERPLAN's claim should be softened until then).
12. **Real codon-optimization** for page 62: replace naive most-frequent-codon picking with a weighted sampling honoring forbidden motifs (BsaI sites, homopolymers, GC windows) — the data tables (`titan_tools` already embeds usage tables) make this self-contained.

### 8.3 Platform / community

13. `pyproject.toml` (packages, `[tool.ruff]`, `[tool.pytest.ini_options]`), Dockerfile + `docker-compose` for the API, Streamlit Community Cloud button, Dependabot, PR/issue templates.
14. Python 3.10–3.13 test matrix; weekly scheduled CI to catch upstream deprecations early (that's how the pandas/plotly breakage in the README's fix-log happened mid-quarter).
15. A tiny docs site (mkdocs) with the tool table *generated from the registry* (kills the manual counts), per-tool "what's real vs simulated" status column, and the contributor guide.
16. Accessibility & i18n sprint: key-based catalogs, Hindi parity for all pages in the top-20 nav, Plotly `aria` descriptions, colorblind mode (the `publication_studio` Okabe-Ito palettes exist — wire a global toggle that makes every figure use them).

---

## 9. Suggested execution order for the next PR series

| PR | Contents | Est. |
|---|---|---|
| 1 | Hub crash fix (inject tool_id/name; kill silent-default rerun; hub selectbox-change test) | S |
| 2 | Honest-labeling pass (§2.3, §2.4, §2.6, §2.7, §2.9) + `static_preset` registry flag + input-sensitivity test | M |
| 3 | Exports: `render_exports` helper, wire real PDF everywhere, delete v1.1 placeholders, page-09 fake-lock button removal | S |
| 4 | ruff + whole-repo lint + upload/length guards + deprecation sweep (`PairwiseAligner`, `width=`, pinning) | M |
| 5 | NCBI live mode behind `TITAN_NCBI_LIVE` + cache + LIVE badge | M |
| 6 | Shared compute layer for legacy tools 1–52; registry regeneration; delete GC stub path | L |
| 7 | NN thermo module + Tm page rewrite; progressive MSA; session history tab; pyproject/Docker/docs | L (split 3 PRs) |

---

*Report generated from static analysis, a full test-suite run, live app smoke tests, and AppTest reproductions of the hub crash. All quoted outputs are verbatim from this repo state; line references point at `75b861c`.*
