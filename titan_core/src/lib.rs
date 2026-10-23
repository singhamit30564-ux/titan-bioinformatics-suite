//! PyO3 bindings — the `titan_core` Python extension module.
//!
//! Contract (mirrored exactly by `titan_utils/engine.py`'s pure-Python
//! fallback):
//!   parse_fastq(path | bytes, threads=N)   → columnar dict (zero-copy bytes)
//!   qc_fastq(path | bytes, threads=N)      → QC report dict
//!   read_bam(path | bytes, region=...)     → flagstat / MAPQ / coverage dict
//!   parse_vcf(path | bytes, filters...)    → columnar dict with pushdown
//!   align(query, target, mode=...)         → score / CIGAR / identity dict
//!   kmer_count(path | bytes, k=...)        → top k-mers + estimates
//!   map_reads(reads, reference, k=...)     → seed-and-extend placements
//!
//! All compute runs with the GIL released; `progress` is invoked from the
//! calling thread between chunks; `CancelToken` aborts between chunks.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict, PyList};
use pyo3::ToPyObject;

pub mod align;
pub mod bam;
pub mod bgzf;
pub mod bloom;
pub mod error;
pub mod fastq;
pub mod hll;
pub mod kmer;
pub mod qc;
pub mod util;
pub mod vcf;

/// Cooperative cancellation flag shared with Python.
#[pyclass(module = "titan_core")]
#[derive(Clone, Default)]
pub struct CancelToken {
    inner: Arc<AtomicBool>,
}

#[pymethods]
impl CancelToken {
    #[new]
    fn new() -> Self {
        Self::default()
    }

    /// Request cancellation; running jobs stop at the next chunk boundary.
    fn cancel(&self) {
        self.inner.store(true, Ordering::SeqCst);
    }

    fn is_cancelled(&self) -> bool {
        self.inner.load(Ordering::SeqCst)
    }

    fn reset(&self) {
        self.inner.store(false, Ordering::SeqCst);
    }

    fn __repr__(&self) -> String {
        format!("CancelToken(cancelled={})", self.is_cancelled())
    }
}

fn resolve_threads(threads: usize) -> usize {
    if threads == 0 {
        rayon::current_num_threads().max(1)
    } else {
        threads
    }
}

fn load_input(path: Option<String>, data: Option<Vec<u8>>, threads: usize) -> PyResult<fastq::InputBuffer> {
    fastq::InputBuffer::load(path.as_deref(), data.as_deref(), threads)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))
}

fn check_cancel(py: Python<'_>, cancel: &Option<Py<CancelToken>>) -> Option<Arc<AtomicBool>> {
    cancel.as_ref().map(|token| token.bind(py).borrow().inner.clone())
}

/// progress closure adapter: FnMut(u64,u64) over the Python callback.
fn make_progress(progress: Option<PyObject>) -> Option<Box<dyn FnMut(u64, u64) + Send>> {
    progress.map(|cb| {
        Box::new(move |done: u64, total: u64| {
            Python::with_gil(|py| {
                let _ = cb.call1(py, (done, total));
            });
        }) as Box<dyn FnMut(u64, u64) + Send>
    })
}

// ─────────────────────────────────────────────────────────────────────────────
// parse_fastq
// ─────────────────────────────────────────────────────────────────────────────

#[pyfunction]
#[pyo3(signature = (path=None, data=None, threads=0, progress=None, cancel=None, max_records=None))]
#[allow(clippy::too_many_arguments)]
fn parse_fastq(
    py: Python<'_>,
    path: Option<String>,
    data: Option<Vec<u8>>,
    threads: usize,
    progress: Option<PyObject>,
    cancel: Option<Py<CancelToken>>,
    max_records: Option<u64>,
) -> PyResult<PyObject> {
    let threads = resolve_threads(threads);
    let input = load_input(path.clone(), data, threads)?;
    let cancel_flag = check_cancel(py, &cancel);
    let mut progress_cb = make_progress(progress);
    let bytes = input.as_slice().to_vec();

    let output = py.allow_threads(|| {
        fastq::parse_payload(
            &bytes,
            threads,
            max_records,
            progress_cb.as_mut().map(|cb| cb.as_mut() as &mut dyn FnMut(u64, u64)),
            cancel_flag.as_deref(),
        )
    });
    let output = output.map_err(|e| match e {
        error::CoreError::Cancelled => PyErr::new::<pyo3::exceptions::PyKeyboardInterrupt, _>("cancelled"),
        other => PyErr::new::<pyo3::exceptions::PyValueError, _>(other.to_string()),
    })?;

    let dict = PyDict::new_bound(py);
    dict.set_item("engine", "rust")?;
    dict.set_item("n_reads", output.n_reads())?;
    dict.set_item("names", output.names.to_object(py))?;
    // Zero-copy hand-off: Python receives `bytes` buffers; engine.py wraps them
    // with np.frombuffer (no copy) into NumPy views.
    dict.set_item("seq_concat", PyBytes::new_bound(py, &output.seq_concat))?;
    dict.set_item("seq_offsets", output.seq_offsets.to_object(py))?;
    dict.set_item("qual_concat", PyBytes::new_bound(py, &output.qual_concat))?;
    dict.set_item("qual_offsets", output.qual_offsets.to_object(py))?;
    dict.set_item("lengths", output.lengths.to_object(py))?;
    dict.set_item("phred_encoding", output.phred().as_str())?;
    dict.set_item("truncated", output.truncated_by_limit)?;
    let warnings = PyDict::new_bound(py);
    warnings.set_item("malformed_records", output.warnings.malformed_records)?;
    warnings.set_item("truncated_records", output.warnings.truncated_records)?;
    warnings.set_item("crlf_lines", output.warnings.crlf_lines)?;
    warnings.set_item("empty_reads", output.warnings.empty_reads)?;
    warnings.set_item("wrapped_records", output.warnings.wrapped_records)?;
    dict.set_item("warnings", warnings)?;
    dict.set_item("bytes_total", bytes.len())?;
    Ok(dict.into_any().unbind())
}

// ─────────────────────────────────────────────────────────────────────────────
// qc_fastq
// ─────────────────────────────────────────────────────────────────────────────

#[pyfunction]
#[pyo3(signature = (path=None, data=None, threads=0, progress=None, cancel=None, k=8))]
#[allow(clippy::too_many_arguments)]
fn qc_fastq(
    py: Python<'_>,
    path: Option<String>,
    data: Option<Vec<u8>>,
    threads: usize,
    progress: Option<PyObject>,
    cancel: Option<Py<CancelToken>>,
    k: usize,
) -> PyResult<PyObject> {
    let threads = resolve_threads(threads);
    let input = load_input(path, data, threads)?;
    let cancel_flag = check_cancel(py, &cancel);
    let mut progress_cb = make_progress(progress);
    let bytes = input.as_slice().to_vec();
    let params = qc::QcParams { k: k.clamp(1, 32), ..Default::default() };

    let report = py.allow_threads(|| {
        qc::qc_payload(
            &bytes,
            threads,
            &params,
            progress_cb.as_mut().map(|cb| cb.as_mut() as &mut dyn FnMut(u64, u64)),
            cancel_flag.as_deref(),
        )
    });
    let report = report.map_err(|e| match e {
        error::CoreError::Cancelled => PyErr::new::<pyo3::exceptions::PyKeyboardInterrupt, _>("cancelled"),
        other => PyErr::new::<pyo3::exceptions::PyValueError, _>(other.to_string()),
    })?;
    qc_report_to_py(py, &report)
}

fn qc_report_to_py(py: Python<'_>, report: &qc::QcReport) -> PyResult<PyObject> {
    let dict = PyDict::new_bound(py);
    dict.set_item("engine", "rust")?;
    dict.set_item("n_reads", report.n_reads)?;
    dict.set_item("total_bases", report.total_bases)?;
    dict.set_item("length_min", report.length_min)?;
    dict.set_item("length_max", report.length_max)?;
    dict.set_item("length_mean", report.length_mean)?;
    let hist = PyList::empty_bound(py);
    for &(len, count) in &report.length_histogram {
        let pair = PyDict::new_bound(py);
        pair.set_item("length", len)?;
        pair.set_item("count", count)?;
        hist.append(pair.unbind())?;
    }
    dict.set_item("length_histogram", hist)?;
    dict.set_item("gc_percent", report.gc_percent)?;
    dict.set_item("n_content_percent", report.n_content_percent)?;
    dict.set_item("per_base_mean_quality", report.per_base_mean_quality.to_object(py))?;
    dict.set_item("q20_percent", report.q20_percent)?;
    dict.set_item("q30_percent", report.q30_percent)?;
    dict.set_item("phred_encoding", report.phred_encoding.as_str())?;
    let dup = PyDict::new_bound(py);
    dup.set_item("method", report.duplication.method)?;
    dup.set_item("distinct_estimate", report.duplication.distinct_estimate)?;
    dup.set_item("duplication_rate_percent", report.duplication.duplication_rate_percent)?;
    dup.set_item(
        "bloom_duplicate_rate_percent",
        report.duplication.bloom_duplicate_rate_percent,
    )?;
    dict.set_item("duplication", dup)?;
    let kmers = PyList::empty_bound(py);
    for (kmer, count, pct) in &report.overrepresented_kmers {
        let pair = PyDict::new_bound(py);
        pair.set_item("kmer", kmer)?;
        pair.set_item("count", count)?;
        pair.set_item("percent", pct)?;
        kmers.append(pair.unbind())?;
    }
    dict.set_item("overrepresented_kmers", kmers)?;
    let adapters = PyList::empty_bound(py);
    for (name, hits, pct) in &report.adapter_hits {
        let pair = PyDict::new_bound(py);
        pair.set_item("adapter", name)?;
        pair.set_item("reads_with_adapter", hits)?;
        pair.set_item("percent", pct)?;
        adapters.append(pair.unbind())?;
    }
    dict.set_item("adapter_hits", adapters)?;
    dict.set_item("empty_reads", report.empty_reads)?;
    let warnings = PyDict::new_bound(py);
    warnings.set_item("malformed_records", report.warnings.malformed_records)?;
    warnings.set_item("truncated_records", report.warnings.truncated_records)?;
    dict.set_item("warnings", warnings)?;
    Ok(dict.into_any().unbind())
}

// ─────────────────────────────────────────────────────────────────────────────
// read_bam
// ─────────────────────────────────────────────────────────────────────────────

#[pyfunction]
#[pyo3(signature = (path=None, data=None, threads=0, region=None, progress=None, cancel=None))]
#[allow(clippy::too_many_arguments)]
fn read_bam(
    py: Python<'_>,
    path: Option<String>,
    data: Option<Vec<u8>>,
    threads: usize,
    region: Option<String>,
    progress: Option<PyObject>,
    cancel: Option<Py<CancelToken>>,
) -> PyResult<PyObject> {
    let threads = resolve_threads(threads);
    let input = load_input(path, data, threads)?;
    let cancel_flag = check_cancel(py, &cancel);
    let mut progress_cb = make_progress(progress);
    let bytes = input.as_slice().to_vec();

    let report = py.allow_threads(|| {
        bam::read_alignment_payload(
            &bytes,
            threads,
            region.as_deref(),
            progress_cb.as_mut().map(|cb| cb.as_mut() as &mut dyn FnMut(u64, u64)),
            cancel_flag.as_deref(),
        )
    });
    let report = report.map_err(|e| match e {
        error::CoreError::Cancelled => PyErr::new::<pyo3::exceptions::PyKeyboardInterrupt, _>("cancelled"),
        other => PyErr::new::<pyo3::exceptions::PyValueError, _>(other.to_string()),
    })?;

    let dict = PyDict::new_bound(py);
    dict.set_item("engine", "rust")?;
    dict.set_item("format", report.format)?;
    dict.set_item("header_text", report.header_text)?;
    let refs = PyList::empty_bound(py);
    for (name, len) in &report.references {
        let pair = PyDict::new_bound(py);
        pair.set_item("name", name)?;
        pair.set_item("length", len)?;
        refs.append(pair.unbind())?;
    }
    dict.set_item("references", refs)?;
    let flagstat = PyDict::new_bound(py);
    let f = &report.flagstat;
    flagstat.set_item("total", f.total)?;
    flagstat.set_item("primary", f.primary)?;
    flagstat.set_item("secondary", f.secondary)?;
    flagstat.set_item("supplementary", f.supplementary)?;
    flagstat.set_item("duplicates", f.duplicates)?;
    flagstat.set_item("mapped", f.mapped)?;
    flagstat.set_item("paired", f.paired)?;
    flagstat.set_item("read1", f.read1)?;
    flagstat.set_item("read2", f.read2)?;
    flagstat.set_item("properly_paired", f.properly_paired)?;
    flagstat.set_item("with_itself_and_mate_mapped", f.with_itself_and_mate_mapped)?;
    flagstat.set_item("singletons", f.singletons)?;
    dict.set_item("flagstat", flagstat)?;
    dict.set_item("mapq_histogram", report.mapq_histogram.to_object(py))?;
    let cov = PyList::empty_bound(py);
    for (ref_name, bins, bin_size) in &report.coverage {
        let pair = PyDict::new_bound(py);
        pair.set_item("ref", ref_name)?;
        pair.set_item("bins", bins.to_object(py))?;
        pair.set_item("bin_size", bin_size)?;
        cov.append(pair.unbind())?;
    }
    dict.set_item("coverage", cov)?;
    let sample = PyList::empty_bound(py);
    for rec in &report.records_sample {
        let pair = PyDict::new_bound(py);
        pair.set_item("name", rec.name.as_str())?;
        pair.set_item("ref", rec.ref_name.as_str())?;
        pair.set_item("pos_1based", rec.pos_1based)?;
        pair.set_item("mapq", rec.mapq)?;
        pair.set_item("flag", rec.flag)?;
        pair.set_item("cigar", rec.cigar.as_str())?;
        pair.set_item("seq_len", rec.seq_len)?;
        sample.append(pair.unbind())?;
    }
    dict.set_item("records_sample", sample)?;
    dict.set_item("n_records_scanned", report.n_records_scanned)?;
    dict.set_item("n_records_in_region", report.n_records_in_region)?;
    match &report.region {
        Some(r) => dict.set_item("region", r)?,
        None => dict.set_item("region", py.None())?,
    }
    Ok(dict.into_any().unbind())
}

// ─────────────────────────────────────────────────────────────────────────────
// parse_vcf
// ─────────────────────────────────────────────────────────────────────────────

#[pyfunction]
#[pyo3(signature = (
    path=None, data=None, threads=0, chrom=None, pos_min=None, pos_max=None,
    qual_min=None, af_min=None, af_max=None, filter=None, max_rows=None,
    progress=None, cancel=None
))]
#[allow(clippy::too_many_arguments)]
fn parse_vcf(
    py: Python<'_>,
    path: Option<String>,
    data: Option<Vec<u8>>,
    threads: usize,
    chrom: Option<String>,
    pos_min: Option<i64>,
    pos_max: Option<i64>,
    qual_min: Option<f64>,
    af_min: Option<f64>,
    af_max: Option<f64>,
    filter: Option<String>,
    max_rows: Option<u64>,
    progress: Option<PyObject>,
    cancel: Option<Py<CancelToken>>,
) -> PyResult<PyObject> {
    let threads = resolve_threads(threads);
    let input = load_input(path, data, threads)?;
    let cancel_flag = check_cancel(py, &cancel);
    let mut progress_cb = make_progress(progress);
    let bytes = input.as_slice().to_vec();
    let filter_spec = vcf::VcfFilter {
        chrom,
        pos_min,
        pos_max,
        qual_min,
        af_min,
        af_max,
        filter,
    };

    let table = py.allow_threads(|| {
        vcf::parse_vcf_payload(
            &bytes,
            threads,
            &filter_spec,
            max_rows,
            progress_cb.as_mut().map(|cb| cb.as_mut() as &mut dyn FnMut(u64, u64)),
            cancel_flag.as_deref(),
        )
    });
    let table = table.map_err(|e| match e {
        error::CoreError::Cancelled => PyErr::new::<pyo3::exceptions::PyKeyboardInterrupt, _>("cancelled"),
        other => PyErr::new::<pyo3::exceptions::PyValueError, _>(other.to_string()),
    })?;

    let dict = PyDict::new_bound(py);
    dict.set_item("engine", "rust")?;
    dict.set_item("format", table.format)?;
    dict.set_item("chrom", table.chrom.to_object(py))?;
    dict.set_item("pos", table.pos.to_object(py))?;
    dict.set_item("id", table.id.to_object(py))?;
    dict.set_item("ref", table.reference.to_object(py))?;
    dict.set_item("alt", table.alt.to_object(py))?;
    dict.set_item("qual", table.qual.to_object(py))?;
    dict.set_item("filter", table.filter.to_object(py))?;
    dict.set_item("info_raw", table.info_raw.to_object(py))?;
    dict.set_item("info_af", table.info_af.to_object(py))?;
    dict.set_item("info_dp", table.info_dp.to_object(py))?;
    dict.set_item("n_rows_kept", table.n_rows_kept)?;
    dict.set_item("n_rows_seen", table.n_rows_seen)?;
    dict.set_item("n_filtered_out", table.n_filtered_out)?;
    dict.set_item("truncated", table.truncated)?;
    dict.set_item("samples", table.samples.to_object(py))?;
    dict.set_item("header_lines", table.header_lines.to_object(py))?;
    let warnings = PyDict::new_bound(py);
    warnings.set_item("malformed_rows", table.warnings.malformed_rows)?;
    warnings.set_item("bcf_format_skipped", table.warnings.bcf_format_skipped)?;
    warnings.set_item("header_missing", table.warnings.header_missing)?;
    dict.set_item("warnings", warnings)?;
    Ok(dict.into_any().unbind())
}

// ─────────────────────────────────────────────────────────────────────────────
// align / map_reads
// ─────────────────────────────────────────────────────────────────────────────

#[pyfunction]
#[pyo3(signature = (query, target, mode="local", match_score=2, mismatch_score=-3, gap_open=5, gap_extend=2, band=64))]
#[allow(clippy::too_many_arguments)]
fn align(
    py: Python<'_>,
    query: String,
    target: String,
    mode: &str,
    match_score: i32,
    mismatch_score: i32,
    gap_open: i32,
    gap_extend: i32,
    band: usize,
) -> PyResult<PyObject> {
    let params = align::AlignParams {
        mode: match mode {
            "global" | "needleman_wunsch" | "nw" => align::AlignMode::Global,
            _ => align::AlignMode::Local,
        },
        match_score,
        mismatch_score,
        gap_open,
        gap_extend,
        band,
        ..Default::default()
    };
    let q = query.as_bytes().to_vec();
    let t = target.as_bytes().to_vec();
    let result = py.allow_threads(|| align::align(&q, &t, &params));
    let aln = result.map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    let dict = PyDict::new_bound(py);
    dict.set_item("engine", "rust")?;
    dict.set_item("score", aln.score)?;
    dict.set_item("cigar", aln.cigar)?;
    dict.set_item("q_start", aln.q_start)?;
    dict.set_item("q_end", aln.q_end)?;
    dict.set_item("t_start", aln.t_start)?;
    dict.set_item("t_end", aln.t_end)?;
    dict.set_item("matches", aln.matches)?;
    dict.set_item("aln_columns", aln.aln_columns)?;
    dict.set_item("identity_percent", aln.identity_percent)?;
    dict.set_item("aligned_query", aln.aligned_query)?;
    dict.set_item("aligned_target", aln.aligned_target)?;
    dict.set_item("display_capped", aln.display_capped)?;
    dict.set_item("mode", mode)?;
    dict.set_item("simd_extension", align::simd_extension_available())?;
    Ok(dict.into_any().unbind())
}

#[pyfunction]
#[pyo3(signature = (reads, reference, ref_name="ref", k=12, threads=0))]
fn map_reads(
    py: Python<'_>,
    reads: Vec<String>,
    reference: String,
    ref_name: &str,
    k: usize,
    threads: usize,
) -> PyResult<PyObject> {
    let threads = resolve_threads(threads);
    let read_bytes: Vec<Vec<u8>> = reads.iter().map(|s| s.as_bytes().to_vec()).collect();
    let reference_bytes = reference.as_bytes().to_vec();
    let placements = py.allow_threads(|| {
        align::map_reads(&read_bytes, &reference_bytes, ref_name, k, threads)
    });
    let placements = placements.map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    let dict = PyDict::new_bound(py);
    dict.set_item("engine", "rust")?;
    let list = PyList::empty_bound(py);
    for p in &placements {
        let item = PyDict::new_bound(py);
        item.set_item("read_index", p.read_index)?;
        item.set_item("ref_name", p.ref_name.as_str())?;
        item.set_item("pos_0based", p.pos_0based)?;
        item.set_item("score", p.score)?;
        item.set_item("matches", p.matches)?;
        item.set_item("mismatches", p.mismatches)?;
        item.set_item("strand", p.strand.to_string())?;
        list.append(item.unbind())?;
    }
    dict.set_item("placements", list)?;
    dict.set_item("n_reads", reads.len())?;
    dict.set_item("n_placed", placements.len())?;
    Ok(dict.into_any().unbind())
}

// ─────────────────────────────────────────────────────────────────────────────
// kmer_count
// ─────────────────────────────────────────────────────────────────────────────

#[pyfunction]
#[pyo3(signature = (path=None, data=None, k=8, threads=0, top=20, max_entries=200000, progress=None, cancel=None))]
#[allow(clippy::too_many_arguments)]
fn kmer_count(
    py: Python<'_>,
    path: Option<String>,
    data: Option<Vec<u8>>,
    k: usize,
    threads: usize,
    top: usize,
    max_entries: usize,
    progress: Option<PyObject>,
    cancel: Option<Py<CancelToken>>,
) -> PyResult<PyObject> {
    let threads = resolve_threads(threads);
    let input = load_input(path, data, threads)?;
    let cancel_flag = check_cancel(py, &cancel);
    let mut progress_cb = make_progress(progress);
    let bytes = input.as_slice().to_vec();
    let k = k.clamp(1, 32);

    let counter = py.allow_threads(|| {
        if let Some(cb) = progress_cb.as_mut() {
            cb(0, bytes.len() as u64);
        }
        // K-mer counting runs over the whole payload as one sequence stream;
        // record boundaries do not affect canonical k-mers, so this is exact.
        let mut counter = kmer::KmerCounter::new(k, max_entries);
        if let Some(flag) = cancel_flag.as_deref() {
            if !flag.load(Ordering::Relaxed) {
                counter.add_sequence(&bytes);
            }
        } else {
            counter.add_sequence(&bytes);
        }
        if let Some(cb) = progress_cb.as_mut() {
            cb(bytes.len() as u64, bytes.len() as u64);
        }
        counter
    });

    let dict = PyDict::new_bound(py);
    dict.set_item("engine", "rust")?;
    dict.set_item("k", counter.k())?;
    dict.set_item("total_kmers", counter.total())?;
    dict.set_item("unique_kmers", counter.unique())?;
    dict.set_item("distinct_estimate", counter.distinct_estimate())?;
    dict.set_item("truncated", counter.truncated())?;
    let list = PyList::empty_bound(py);
    for (kmer, count) in counter.top(top) {
        let item = PyDict::new_bound(py);
        item.set_item("kmer", kmer)?;
        item.set_item("count", count)?;
        list.append(item.unbind())?;
    }
    dict.set_item("top_kmers", list)?;
    Ok(dict.into_any().unbind())
}

// ─────────────────────────────────────────────────────────────────────────────
// engine_info
// ─────────────────────────────────────────────────────────────────────────────

#[pyfunction]
fn engine_info(py: Python<'_>) -> PyResult<PyObject> {
    let dict = PyDict::new_bound(py);
    dict.set_item("name", "titan_core")?;
    dict.set_item("version", env!("CARGO_PKG_VERSION"))?;
    dict.set_item("rayon_threads", rayon::current_num_threads())?;
    let features = PyList::empty_bound(py);
    for feature in [
        "parse_fastq",
        "qc_fastq",
        "read_bam",
        "parse_vcf",
        "align",
        "map_reads",
        "kmer_count",
        "cancel_token",
        "progress_callback",
        "bgzf_parallel",
    ] {
        features.append(feature)?;
    }
    dict.set_item("features", features)?;
    dict.set_item("simd_extension", align::simd_extension_available())?;
    Ok(dict.into_any().unbind())
}

#[pymodule]
fn titan_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<CancelToken>()?;
    m.add_function(wrap_pyfunction!(parse_fastq, m)?)?;
    m.add_function(wrap_pyfunction!(qc_fastq, m)?)?;
    m.add_function(wrap_pyfunction!(read_bam, m)?)?;
    m.add_function(wrap_pyfunction!(parse_vcf, m)?)?;
    m.add_function(wrap_pyfunction!(align, m)?)?;
    m.add_function(wrap_pyfunction!(map_reads, m)?)?;
    m.add_function(wrap_pyfunction!(kmer_count, m)?)?;
    m.add_function(wrap_pyfunction!(engine_info, m)?)?;
    m.add("__engine_name__", "titan_core")?;
    m.add("__engine_version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}
