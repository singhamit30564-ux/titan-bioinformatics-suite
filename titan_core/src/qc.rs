//! One-pass streaming QC over FASTQ records.
//!
//! Per-base quality, GC%, length histogram, N-content, adapter hits,
//! over-represented k-mers, duplication estimate (HyperLogLog + Bloom) and
//! Phred-encoding autodetection. Everything accumulates in fixed/ bounded
//! memory, so 50M-read inputs do not scale RAM with input size (the only
//! unbounded structure is the exact length histogram, which is bounded by
//! distinct read lengths).

use std::collections::BTreeMap;
use std::sync::atomic::{AtomicBool, Ordering};

use rayon::prelude::*;

use crate::bloom::BloomFilter;
use crate::error::{CoreError, Result};
use crate::fastq::{plan_blocks, PhredEncoding};
use crate::hll::HyperLogLog;
use crate::kmer::KmerCounter;

pub const DEFAULT_KMER_K: usize = 8;
pub const MAX_KMER_ENTRIES: usize = 200_000;

/// Common Illumina/Universal adapter prefixes (5'→3'). Hits are counted per
/// read when the adapter occurs anywhere in the read.
pub const ADAPTERS: &[(&str, &str)] = &[
    ("Illumina_Universal", "AGATCGGAAGAG"),
    ("Illumina_SmallRNA", "TGGAATTCTCGG"),
    ("Nextera", "CTGTCTCTTATA"),
    ("PolyA", "AAAAAAAAAAAA"),
    ("PolyG", "GGGGGGGGGGGG"),
];

#[derive(Debug, Clone)]
pub struct QcParams {
    pub k: usize,
    pub adapters: Vec<(String, String)>,
}

impl Default for QcParams {
    fn default() -> Self {
        QcParams {
            k: DEFAULT_KMER_K,
            adapters: ADAPTERS
                .iter()
                .map(|(n, s)| (n.to_string(), s.to_string()))
                .collect(),
        }
    }
}

#[derive(Debug, Default)]
pub struct QcAccum {
    pub n_reads: u64,
    pub total_bases: u64,
    pub gc_bases: u64,
    pub n_bases: u64,
    pub len_min: u64,
    pub len_max: u64,
    pub length_histogram: BTreeMap<u64, u64>,
    pub qual_sum_by_pos: Vec<u64>,
    pub qual_count_by_pos: Vec<u64>,
    pub qual_byte_hist: [u64; 256],
    pub qmin: u8,
    pub qmax: u8,
    pub dup_hll: HyperLogLog,
    pub dup_bloom: BloomFilter,
    pub bloom_seen_before: u64,
    pub kmers: KmerCounter,
    pub adapter_hits: Vec<u64>,
    pub empty_reads: u64,
}

impl QcAccum {
    pub fn new(params: &QcParams) -> Self {
        QcAccum {
            len_min: u64::MAX,
            qmin: u8::MAX,
            dup_hll: HyperLogLog::new(),
            dup_bloom: BloomFilter::with_capacity(4_000_000, 0.01),
            kmers: KmerCounter::new(params.k, MAX_KMER_ENTRIES),
            adapter_hits: vec![0; params.adapters.len()],
            ..Default::default()
        }
    }

    pub fn observe(&mut self, seq: &[u8], qual: &[u8], params: &QcParams) {
        self.n_reads += 1;
        let len = seq.len() as u64;
        if len == 0 {
            self.empty_reads += 1;
        }
        self.total_bases += len;
        if len < self.len_min {
            self.len_min = len;
        }
        if len > self.len_max {
            self.len_max = len;
            self.qual_sum_by_pos.resize(len as usize, 0);
            self.qual_count_by_pos.resize(len as usize, 0);
        }
        *self.length_histogram.entry(len).or_insert(0) += 1;

        for &b in seq.iter() {
            match b {
                b'G' | b'C' | b'g' | b'c' => self.gc_bases += 1,
                b'N' | b'n' => self.n_bases += 1,
                _ => {}
            }
        }
        for (i, &q) in qual.iter().enumerate() {
            if i < self.qual_sum_by_pos.len() {
                self.qual_sum_by_pos[i] += u64::from(q);
                self.qual_count_by_pos[i] += 1;
            }
            self.qual_byte_hist[q as usize] += 1;
            if q < self.qmin {
                self.qmin = q;
            }
            if q > self.qmax {
                self.qmax = q;
            }
        }

        // Duplication sketches.
        let h = crate::util::fnv1a64(seq);
        self.dup_hll.add(h);
        if self.dup_bloom.insert_if_absent(h) {
            self.bloom_seen_before += 1;
        }

        // k-mers (canonical, 2-bit packed).
        self.kmers.add_sequence(seq);

        // Adapters.
        for (idx, (_name, motif)) in params.adapters.iter().enumerate() {
            if contains_subsequence(seq, motif.as_bytes()) {
                self.adapter_hits[idx] += 1;
            }
        }
    }

    pub fn merge(&mut self, other: &QcAccum) {
        self.n_reads += other.n_reads;
        self.total_bases += other.total_bases;
        self.gc_bases += other.gc_bases;
        self.n_bases += other.n_bases;
        self.empty_reads += other.empty_reads;
        self.len_min = self.len_min.min(other.len_min);
        self.len_max = self.len_max.max(other.len_max);
        for (&len, &count) in &other.length_histogram {
            *self.length_histogram.entry(len).or_insert(0) += count;
        }
        if self.qual_sum_by_pos.len() < other.qual_sum_by_pos.len() {
            self.qual_sum_by_pos.resize(other.qual_sum_by_pos.len(), 0);
            self.qual_count_by_pos.resize(other.qual_count_by_pos.len(), 0);
        }
        for (i, &v) in other.qual_sum_by_pos.iter().enumerate() {
            self.qual_sum_by_pos[i] += v;
        }
        for (i, &v) in other.qual_count_by_pos.iter().enumerate() {
            self.qual_count_by_pos[i] += v;
        }
        for i in 0..256 {
            self.qual_byte_hist[i] += other.qual_byte_hist[i];
        }
        self.qmin = self.qmin.min(other.qmin);
        self.qmax = self.qmax.max(other.qmax);
        self.dup_hll.merge(&other.dup_hll);
        self.bloom_seen_before += other.bloom_seen_before;
        self.dup_bloom.merge_or(&other.dup_bloom);
        self.kmers.merge(&other.kmers);
        if self.adapter_hits.len() < other.adapter_hits.len() {
            self.adapter_hits.resize(other.adapter_hits.len(), 0);
        }
        for (i, &v) in other.adapter_hits.iter().enumerate() {
            self.adapter_hits[i] += v;
        }
    }
}

#[inline]
fn contains_subsequence(haystack: &[u8], needle: &[u8]) -> bool {
    if needle.is_empty() || needle.len() > haystack.len() {
        return false;
    }
    haystack.windows(needle.len()).any(|w| w == needle)
}

// ─────────────────────────────────────────────────────────────────────────────
// Report
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug)]
pub struct QcReport {
    pub engine: &'static str, // filled by the binding layer
    pub n_reads: u64,
    pub total_bases: u64,
    pub length_min: u64,
    pub length_max: u64,
    pub length_mean: f64,
    pub length_histogram: Vec<(u64, u64)>,
    pub gc_percent: f64,
    pub n_content_percent: f64,
    pub per_base_mean_quality: Vec<f64>,
    pub q20_percent: f64,
    pub q30_percent: f64,
    pub phred_encoding: PhredEncoding,
    pub duplication: DuplicationStats,
    pub overrepresented_kmers: Vec<(String, u64, f64)>,
    pub adapter_hits: Vec<(String, u64, f64)>,
    pub empty_reads: u64,
    pub warnings: crate::fastq::ParseWarnings,
}

#[derive(Debug)]
pub struct DuplicationStats {
    pub method: &'static str,
    pub distinct_estimate: f64,
    pub duplication_rate_percent: f64,
    pub bloom_duplicate_rate_percent: f64,
}

fn detect_phred(hist: &[u64; 256]) -> PhredEncoding {
    let mut qmin = u8::MAX;
    let mut qmax = 0u8;
    for (b, &count) in hist.iter().enumerate() {
        if count > 0 {
            let b = b as u8;
            qmin = qmin.min(b);
            qmax = qmax.max(b);
        }
    }
    if qmin == u8::MAX {
        return PhredEncoding::Ambiguous;
    }
    if qmin >= 64 {
        return PhredEncoding::Phred64;
    }
    if qmax <= 60 || (qmin < 59 && qmax <= 74) {
        return PhredEncoding::Phred33;
    }
    PhredEncoding::Ambiguous
}

pub fn build_report(accum: QcAccum, params: &QcParams, warnings: crate::fastq::ParseWarnings) -> QcReport {
    let phred = detect_phred(&accum.qual_byte_hist);
    let offset = u64::from(phred.offset());
    let total_bases = accum.total_bases.max(1) as f64;
    let per_base_mean_quality: Vec<f64> = accum
        .qual_sum_by_pos
        .iter()
        .zip(accum.qual_count_by_pos.iter())
        .map(|(&s, &c)| {
            if c == 0 {
                0.0
            } else {
                (s / c) as f64 - offset as f64
            }
        })
        .collect();
    let mut q20 = 0u64;
    let mut q30 = 0u64;
    for (b, &count) in accum.qual_byte_hist.iter().enumerate() {
        if count == 0 {
            continue;
        }
        let score = b as i64 - offset as i64;
        if score >= 20 {
            q20 += count;
        }
        if score >= 30 {
            q30 += count;
        }
    }
    let total_q = accum.qual_byte_hist.iter().sum::<u64>().max(1) as f64;
    let distinct = accum.dup_hll.estimate().min(accum.n_reads as f64);
    let dup_rate = if accum.n_reads > 0 {
        100.0 * (1.0 - distinct / accum.n_reads as f64)
    } else {
        0.0
    };
    let bloom_rate = if accum.n_reads > 0 {
        100.0 * accum.bloom_seen_before as f64 / accum.n_reads as f64
    } else {
        0.0
    };
    let total_kmers = accum.kmers.total().max(1) as f64;
    let overrepresented_kmers: Vec<(String, u64, f64)> = accum
        .kmers
        .top(20)
        .into_iter()
        .map(|(kmer, count)| {
            let pct = 100.0 * count as f64 / total_kmers;
            (kmer, count, pct)
        })
        .filter(|(_, _, pct)| *pct >= 0.05)
        .collect();
    let adapter_hits: Vec<(String, u64, f64)> = params
        .adapters
        .iter()
        .enumerate()
        .map(|(i, (name, _motif))| {
            let hits = accum.adapter_hits.get(i).copied().unwrap_or(0);
            let pct = if accum.n_reads > 0 {
                100.0 * hits as f64 / accum.n_reads as f64
            } else {
                0.0
            };
            (name.clone(), hits, pct)
        })
        .collect();
    QcReport {
        engine: "python", // overwritten by callers with the real engine name
        n_reads: accum.n_reads,
        total_bases: accum.total_bases,
        length_min: if accum.n_reads == 0 { 0 } else { accum.len_min },
        length_max: accum.len_max,
        length_mean: if accum.n_reads > 0 {
            accum.total_bases as f64 / accum.n_reads as f64
        } else {
            0.0
        },
        length_histogram: accum.length_histogram.into_iter().collect(),
        gc_percent: 100.0 * accum.gc_bases as f64 / total_bases,
        n_content_percent: 100.0 * accum.n_bases as f64 / total_bases,
        per_base_mean_quality,
        q20_percent: 100.0 * q20 as f64 / total_q,
        q30_percent: 100.0 * q30 as f64 / total_q,
        phred_encoding: phred,
        duplication: DuplicationStats {
            method: "hyperloglog(14-bit)+bloom",
            distinct_estimate: distinct,
            duplication_rate_percent: dup_rate.max(0.0),
            bloom_duplicate_rate_percent: bloom_rate.min(100.0),
        },
        overrepresented_kmers,
        adapter_hits,
        empty_reads: accum.empty_reads,
        warnings,
    }
}

/// Streaming QC entry point: record-aligned parallel blocks merged into one
/// `QcAccum`; `progress(bytes_done, bytes_total)` is called between blocks.
pub fn qc_payload(
    data: &[u8],
    threads: usize,
    params: &QcParams,
    progress: Option<&mut dyn FnMut(u64, u64)>,
    cancel: Option<&AtomicBool>,
) -> Result<QcReport> {
    let plan = plan_blocks(data, 8 * 1024 * 1024);
    let per_block = |range: (usize, usize)| -> (QcAccum, crate::fastq::ParseWarnings) {
        let mut warnings = crate::fastq::ParseWarnings::default();
        let mut accum = QcAccum::new(params);
        let records = crate::fastq::parse_block(&data[range.0..range.1], &mut warnings, cancel);
        for rec in records {
            accum.observe(rec.seq, rec.qual, params);
        }
        (accum, warnings)
    };
    let mut results: Vec<(QcAccum, crate::fastq::ParseWarnings)> = if threads == 1 || plan.blocks.len() <= 1 {
        plan.blocks.iter().map(|&r| per_block(r)).collect()
    } else {
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(threads)
            .build()
            .map_err(|e| CoreError::Io(format!("thread pool build failed: {e}")))?;
        pool.install(|| plan.blocks.par_iter().map(|&r| per_block(r)).collect())
    };

    let mut merged = QcAccum::new(params);
    let mut warnings = crate::fastq::ParseWarnings::default();
    let total = data.len() as u64;
    let mut done = 0u64;
    for (accum, warn) in results.drain(..) {
        if cancel.map(|f| f.load(Ordering::Relaxed)).unwrap_or(false) {
            return Err(CoreError::Cancelled);
        }
        merged.merge(&accum);
        warnings.merge(&warn);
        done += 1;
        if let Some(cb) = progress.as_mut() {
            let frac = (done as f64 / plan.blocks.len().max(1) as f64) * total as f64;
            cb(frac.min(total), total);
        }
    }
    if let Some(cb) = progress.as_mut() {
        cb(total, total);
    }
    Ok(build_report(merged, params, warnings))
}

/// Convenience: quick QC over a single seq/qual pair (used by tests).
pub fn quick_read_metrics(seq: &[u8], qual: &[u8]) -> (u64, u64, u64) {
    let gc = seq.iter().filter(|&&b| matches!(b, b'G' | b'C' | b'g' | b'c')).count() as u64;
    let n = seq.iter().filter(|&&b| matches!(b, b'N' | b'n')).count() as u64;
    (seq.len().max(qual.len()) as u64, gc, n)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fastq_bytes(n: usize, len: usize) -> Vec<u8> {
        let mut out = Vec::new();
        for i in 0..n {
            out.extend_from_slice(format!("@r{i}\n").as_bytes());
            let seq: Vec<u8> = (0..len).map(|j| b"ACGT"[(i + j) % 4]).collect();
            out.extend_from_slice(&seq);
            out.extend_from_slice(b"\n+\n");
            out.extend_from_slice(&vec![if i % 10 == 0 { b'?' } else { b'I' }; len]);
            out.extend_from_slice(b"\n");
        }
        out
    }

    #[test]
    fn qc_counts_reads_and_gc() {
        let data = fastq_bytes(100, 50);
        let report = qc_payload(&data, 2, &QcParams::default(), None, None).unwrap();
        assert_eq!(report.n_reads, 100);
        assert_eq!(report.total_bases, 5000);
        assert!((report.gc_percent - 50.0).abs() < 1e-6);
        assert_eq!(report.length_min, 50);
        assert_eq!(report.phred_encoding, PhredEncoding::Phred33);
    }

    #[test]
    fn duplication_of_identical_reads_is_high() {
        let mut out = Vec::new();
        for i in 0..50 {
            out.extend_from_slice(format!("@r{i}\nACGTACGTAC\n+\nIIIIIIIIII\n").as_bytes());
        }
        let report = qc_payload(&out, 2, &QcParams::default(), None, None).unwrap();
        assert!(report.duplication.duplication_rate_percent > 90.0);
    }

    #[test]
    fn adapter_detection() {
        let mut out = Vec::new();
        for i in 0..10 {
            out.extend_from_slice(format!("@r{i}\n").as_bytes());
            out.extend_from_slice(b"TTTTTTTTTTAGATCGGAAGAGCCCCCCCCCC");
            out.extend_from_slice(b"\n+\n");
            out.extend_from_slice(&vec![b'I'; 32]);
            out.extend_from_slice(b"\n");
        }
        let report = qc_payload(&out, 1, &QcParams::default(), None, None).unwrap();
        let universal = report
            .adapter_hits
            .iter()
            .find(|(name, _, _)| name == "Illumina_Universal")
            .unwrap();
        assert_eq!(universal.1, 10);
    }
}
