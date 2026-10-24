//! FASTQ / FASTQ.GZ / BGZF parsing: mmap + chunked parallel record decode.
//!
//! Robust against CRLF line endings, wrapped (multi-line) FASTQ, truncated
//! trailing records and malformed records (skipped + counted in `warnings`;
//! error messages never contain sequence data). Parallel fast path is used
//! when the input is strict 4-line FASTQ (the NGS norm); anything else falls
//! back to the same robust state machine, sequentially.

use std::path::Path;
use std::sync::atomic::{AtomicBool, Ordering};

use memmap2::Mmap;
use rayon::prelude::*;

use crate::error::{CoreError, Result};
use crate::util::trim_cr;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PhredEncoding {
    Phred33,
    Phred64,
    Ambiguous,
}

impl PhredEncoding {
    pub fn as_str(self) -> &'static str {
        match self {
            PhredEncoding::Phred33 => "phred33",
            PhredEncoding::Phred64 => "phred64",
            PhredEncoding::Ambiguous => "ambiguous",
        }
    }

    /// Offset applied to ASCII quality bytes to obtain Phred scores.
    pub fn offset(self) -> u8 {
        match self {
            PhredEncoding::Phred64 => 64,
            // Ambiguous inputs are scored with the modern Sanger offset and
            // flagged in the report.
            _ => 33,
        }
    }
}

#[derive(Debug, Default, Clone)]
pub struct ParseWarnings {
    pub malformed_records: u64,
    pub truncated_records: u64,
    pub crlf_lines: u64,
    pub empty_reads: u64,
    pub wrapped_records: u64,
}

impl ParseWarnings {
    pub fn merge(&mut self, other: &ParseWarnings) {
        self.malformed_records += other.malformed_records;
        self.truncated_records += other.truncated_records;
        self.crlf_lines += other.crlf_lines;
        self.empty_reads += other.empty_reads;
        self.wrapped_records += other.wrapped_records;
    }
}

/// A decoded record borrowing directly from the input buffer (zero-copy).
#[derive(Debug, Clone, Copy)]
pub struct RawRecord<'a> {
    pub name: &'a [u8],
    pub seq: &'a [u8],
    pub qual: &'a [u8],
}

/// Owned, columnar parse output. `seq_concat`/`qual_concat` + offsets are what
/// the Python layer hands to NumPy via `np.frombuffer` (zero-copy views).
#[derive(Debug, Default)]
pub struct ParseOutput {
    pub names: Vec<String>,
    pub seq_concat: Vec<u8>,
    pub seq_offsets: Vec<u64>,
    pub qual_concat: Vec<u8>,
    pub qual_offsets: Vec<u64>,
    pub lengths: Vec<u64>,
    pub warnings: ParseWarnings,
    pub qmin: u8,
    pub qmax: u8,
    pub truncated_by_limit: bool,
}

impl ParseOutput {
    pub fn phred(&self) -> PhredEncoding {
        if self.qmin == u8::MAX {
            return PhredEncoding::Ambiguous;
        }
        // Phred33 (Sanger / Illumina 1.8+) is the modern default; Phred64 is
        // legacy Illumina 1.3–1.7. Claim Phred64 only with positive evidence:
        // every observed byte inside the Phred64 range AND at least one byte
        // above 73 ('I' — the practical Phred33 ceiling for real instruments).
        if self.qmin >= 64 && self.qmax > 73 {
            return PhredEncoding::Phred64;
        }
        if self.qmin < 33 {
            return PhredEncoding::Ambiguous;
        }
        PhredEncoding::Phred33
    }

    pub fn n_reads(&self) -> u64 {
        self.lengths.len() as u64
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Input loading (mmap / bytes / gzip)
// ─────────────────────────────────────────────────────────────────────────────

/// Owns the raw input bytes: either a memory map of a plain file or a heap
/// buffer (raw bytes or decompressed gzip/BGZF).
pub struct InputBuffer {
    _mmap: Option<Mmap>,
    owned: Option<Vec<u8>>,
}

impl InputBuffer {
    pub fn load(path: Option<&str>, data: Option<&[u8]>, threads: usize) -> Result<Self> {
        match (path, data) {
            (Some(_), Some(_)) => Err(CoreError::Input(
                "pass either 'path' or 'data', not both".into(),
            )),
            (None, None) => Err(CoreError::Input("no input: pass 'path' or 'data'".into())),
            (None, Some(bytes)) => {
                let owned = if crate::bgzf::is_gzip(bytes) {
                    crate::bgzf::decompress(bytes, threads)?
                } else {
                    bytes.to_vec()
                };
                Ok(InputBuffer {
                    _mmap: None,
                    owned: Some(owned),
                })
            }
            (Some(p), None) => {
                let path = Path::new(p);
                if !path.exists() {
                    return Err(CoreError::Input(format!("path not found: {p}")));
                }
                let file = std::fs::File::open(path)?;
                // Read the first bytes to sniff gzip; files >0 are safe to mmap.
                let probe_len = 4.min(std::fs::metadata(path)?.len() as usize);
                let mut probe = [0u8; 4];
                use std::io::Read;
                let mut file = file;
                file.read_exact(&mut probe[..probe_len])?;
                if probe_len >= 2 && probe[0] == 0x1f && probe[1] == 0x8b {
                    let mut raw = Vec::new();
                    std::fs::File::open(path)?.read_to_end(&mut raw)?;
                    let owned = crate::bgzf::decompress(&raw, threads)?;
                    Ok(InputBuffer {
                        _mmap: None,
                        owned: Some(owned),
                    })
                } else {
                    let mmap = unsafe { Mmap::map(&file)? };
                    Ok(InputBuffer {
                        _mmap: Some(mmap),
                        owned: None,
                    })
                }
            }
        }
    }

    pub fn as_slice(&self) -> &[u8] {
        match &self.owned {
            Some(v) => v.as_slice(),
            None => self._mmap.as_ref().map(|m| m.as_ref()).unwrap_or(&[]),
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Record state machine + block planning
// ─────────────────────────────────────────────────────────────────────────────

struct LineIter<'a> {
    buf: &'a [u8],
    pos: usize,
    last_start: usize,
}

impl<'a> LineIter<'a> {
    fn new(buf: &'a [u8], pos: usize) -> Self {
        LineIter {
            buf,
            pos,
            last_start: pos,
        }
    }

    fn next_line(&mut self) -> Option<&'a [u8]> {
        if self.pos >= self.buf.len() {
            return None;
        }
        let start = self.pos;
        self.last_start = start;
        let end = self.buf[start..]
            .iter()
            .position(|&b| b == b'\n')
            .map(|p| start + p)
            .unwrap_or(self.buf.len());
        self.pos = if end < self.buf.len() { end + 1 } else { end };
        Some(trim_cr(&self.buf[start..end]))
    }
}

/// Robust FASTQ record parser over one buffer. Handles wrapped sequence/quality
/// lines, CRLF, malformed records (skip + resync at the next '@' line) and a
/// truncated trailing record.
pub fn parse_block<'a>(
    buf: &'a [u8],
    warnings: &mut ParseWarnings,
    cancel: Option<&AtomicBool>,
) -> Vec<RawRecord<'a>> {
    let mut records = Vec::new();
    let mut it = LineIter::new(buf, 0);
    let mut checked = 0u64;
    loop {
        if let Some(flag) = cancel {
            if flag.load(Ordering::Relaxed) {
                break;
            }
        }
        // 1. Header line — must start with '@'.
        let header = match it.next_line() {
            Some(line) => line,
            None => break,
        };
        if header.is_empty() || header[0] != b'@' {
            warnings.malformed_records += 1;
            continue;
        }
        let name = &header[1..];

        // 2. Sequence lines until a '+' separator. Any line starting with '+'
        //    terminates the sequence; wrapped records accumulate length only.
        let mut seq_start = it.pos;
        let mut seq_len = 0usize;
        let mut seq_lines = 0usize;
        let mut sep_found = false;
        while let Some(line) = it.next_line() {
            if line.first() == Some(&b'+') {
                sep_found = true;
                break;
            }
            if seq_len == 0 {
                seq_start = it.last_start;
            }
            seq_len += line.len();
            seq_lines += 1;
        }
        if !sep_found {
            warnings.truncated_records += 1;
            break;
        }
        if seq_len == 0 {
            warnings.empty_reads += 1;
        }

        // 3. Quality lines until >= seq_len quality bytes ('@' is a legal Phred
        //    character, so length is the only safe stop rule).
        let qual_start = it.pos;
        let mut qual_len = 0usize;
        let mut qual_lines = 0usize;
        let mut record_complete = false;
        loop {
            let before = it.pos;
            let line = match it.next_line() {
                Some(line) => line,
                None => break,
            };
            if it.pos == before {
                break;
            }
            qual_len += line.len();
            qual_lines += 1;
            if qual_len >= seq_len {
                record_complete = true;
                break;
            }
        }
        if !record_complete {
            warnings.truncated_records += 1;
            break;
        }
        let wrapped = seq_lines > 1 || qual_lines > 1;
        if wrapped {
            // Non-contiguous seq/qual — the borrowing parser cannot hand out
            // single slices. Count it and let `collect_block` rebuild through
            // `parse_records_owned` so no read is silently lost.
            warnings.wrapped_records += 1;
            continue;
        }
        let seq_raw = &buf[seq_start..(seq_start + seq_len).min(buf.len())];
        let qual_raw = &buf[qual_start..(qual_start + qual_len).min(buf.len())];
        let seq = trim_cr(seq_raw);
        let qual = trim_cr(qual_raw);
        if seq.len() != qual.len() {
            warnings.malformed_records += 1;
        } else {
            records.push(RawRecord { name, seq, qual });
        }
        checked += 1;
        if checked.is_multiple_of(65536) {
            if let Some(flag) = cancel {
                if flag.load(Ordering::Relaxed) {
                    break;
                }
            }
        }
    }
    records
}

/// Owned-record parser — used by tests and the sequential fallback; supports
/// fully wrapped FASTQ (multi-line seq/qual) without loss.
pub fn parse_records_owned(
    buf: &[u8],
    warnings: &mut ParseWarnings,
) -> Vec<(String, Vec<u8>, Vec<u8>)> {
    let borrowed = parse_block(buf, warnings, None);
    // For wrapped FASTQ, `parse_block` skips records; re-scan linearly here.
    if warnings.wrapped_records > 0 || warnings.malformed_records > 0 {
        let mut out = Vec::new();
        let mut w2 = ParseWarnings::default();
        let mut it = LineIter::new(buf, 0);
        while let Some(l) = it.next_line() {
            let header = l.to_vec();
            if header.is_empty() || header[0] != b'@' {
                continue;
            }
            let name = String::from_utf8_lossy(&header[1..]).into_owned();
            let mut seq = Vec::new();
            let mut sep_ok = false;
            while let Some(line) = it.next_line() {
                if line.first() == Some(&b'+') {
                    sep_ok = true;
                    break;
                }
                seq.extend_from_slice(trim_cr(line));
            }
            if !sep_ok {
                w2.truncated_records += 1;
                break;
            }
            let mut qual = Vec::new();
            while qual.len() < seq.len() {
                match it.next_line() {
                    Some(line) => qual.extend_from_slice(trim_cr(line)),
                    None => break,
                }
            }
            if qual.len() != seq.len() {
                w2.malformed_records += 1;
                continue;
            }
            out.push((name, seq, qual));
        }
        warnings.merge(&w2);
        return out;
    }
    borrowed
        .into_iter()
        .map(|r| {
            (
                String::from_utf8_lossy(r.name).into_owned(),
                r.seq.to_vec(),
                r.qual.to_vec(),
            )
        })
        .collect()
}

#[derive(Debug, Default)]
pub struct Plan {
    pub strict: bool,
    pub blocks: Vec<(usize, usize)>,
}

/// Decide whether the payload is strict 4-line FASTQ and, when it is, cut it
/// into record-aligned byte blocks for parallel parsing.
pub fn plan_blocks(buf: &[u8], target_block: usize) -> Plan {
    let mut plan = Plan {
        strict: true,
        blocks: Vec::new(),
    };
    if buf.is_empty() {
        return plan;
    }
    let mut line_no = 0usize;
    let mut line_start = 0usize;
    let mut block_start = 0usize;
    let mut strict = true;
    let target_block = target_block.max(64 * 1024);
    let mut newline_positions: Vec<usize> = Vec::new();
    crate::util::find_newlines(buf, 0, &mut newline_positions);
    for &nl in &newline_positions {
        let line = trim_cr(&buf[line_start..nl]);
        let idx_in_record = line_no % 4;
        match idx_in_record {
            0 => {
                if line.is_empty() || line.first() != Some(&b'@') {
                    strict = false;
                }
            }
            1 => {
                if line.first() == Some(&b'+') {
                    strict = false; // zero-length sequence with immediate '+'
                }
            }
            2 if line.first() != Some(&b'+') => {
                strict = false;
            }
            _ => {}
        }
        line_no += 1;
        line_start = nl + 1;
        if !strict {
            break;
        }
        if line_no.is_multiple_of(4) && line_start - block_start >= target_block {
            plan.blocks.push((block_start, line_start));
            block_start = line_start;
        }
    }
    if !strict {
        plan.strict = false;
        plan.blocks.clear();
        plan.blocks.push((0, buf.len()));
        return plan;
    }
    // Verify seq/qual length equality per record on a light second pass over
    // line starts only when the stream is small; for big streams the per-record
    // parser still validates lengths and counts mismatches as malformed.
    if block_start < buf.len() {
        plan.blocks.push((block_start, buf.len()));
    }
    plan
}

// ─────────────────────────────────────────────────────────────────────────────
// Parallel parse
// ─────────────────────────────────────────────────────────────────────────────

struct BlockOut {
    names: Vec<String>,
    seq_concat: Vec<u8>,
    seq_offsets: Vec<u64>,
    qual_concat: Vec<u8>,
    qual_offsets: Vec<u64>,
    lengths: Vec<u64>,
    warnings: ParseWarnings,
    qmin: u8,
    qmax: u8,
}

impl BlockOut {
    fn new() -> Self {
        BlockOut {
            names: Vec::new(),
            seq_concat: Vec::new(),
            seq_offsets: vec![0],
            qual_concat: Vec::new(),
            qual_offsets: vec![0],
            lengths: Vec::new(),
            warnings: ParseWarnings::default(),
            qmin: u8::MAX,
            qmax: 0,
        }
    }

    fn push_record(&mut self, name: &[u8], seq: &[u8], qual: &[u8]) {
        self.names.push(String::from_utf8_lossy(name).into_owned());
        self.seq_concat.extend_from_slice(seq);
        self.seq_offsets.push(self.seq_concat.len() as u64);
        self.qual_concat.extend_from_slice(qual);
        self.qual_offsets.push(self.qual_concat.len() as u64);
        self.lengths.push(seq.len() as u64);
        for &q in qual {
            if q < self.qmin {
                self.qmin = q;
            }
            if q > self.qmax {
                self.qmax = q;
            }
        }
    }
}

fn collect_block(buf: &[u8], cancel: Option<&AtomicBool>) -> BlockOut {
    let mut out = BlockOut::new();
    let mut warnings = ParseWarnings::default();
    let records = parse_block(buf, &mut warnings, cancel);
    for rec in records {
        out.push_record(rec.name, rec.seq, rec.qual);
    }
    // Wrapped records were skipped by the borrowing parser — recover them
    // through the owned path so no read is silently lost.
    if warnings.wrapped_records > 0 {
        let mut w2 = ParseWarnings::default();
        let owned = parse_records_owned(buf, &mut w2);
        if owned.len() as u64 > out.lengths.len() as u64 {
            out.names.clear();
            out.seq_concat.clear();
            out.seq_offsets = vec![0];
            out.qual_concat.clear();
            out.qual_offsets = vec![0];
            out.lengths.clear();
            for (name, seq, qual) in owned {
                out.push_record(name.as_bytes(), &seq, &qual);
            }
        }
    }
    out.warnings = warnings;
    out
}

/// Parse an in-memory FASTQ payload with optional parallelism.
/// `progress` is invoked as `progress(bytes_done, bytes_total)` from the
/// calling thread between blocks (never from rayon workers).
pub fn parse_payload(
    data: &[u8],
    threads: usize,
    max_records: Option<u64>,
    mut progress: Option<&mut dyn FnMut(u64, u64)>,
    cancel: Option<&AtomicBool>,
) -> Result<ParseOutput> {
    let plan = plan_blocks(data, 8 * 1024 * 1024);
    let mut outputs: Vec<BlockOut> = if threads == 1 || plan.blocks.len() <= 1 {
        plan.blocks
            .iter()
            .map(|&(s, e)| collect_block(&data[s..e], cancel))
            .collect()
    } else {
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(threads)
            .build()
            .map_err(|e| CoreError::Io(format!("thread pool build failed: {e}")))?;
        pool.install(|| {
            plan.blocks
                .par_iter()
                .map(|&(s, e)| collect_block(&data[s..e], cancel))
                .collect::<Vec<BlockOut>>()
        })
    };

    let mut merged = ParseOutput {
        seq_offsets: vec![0],
        qual_offsets: vec![0],
        ..Default::default()
    };
    // Default qmin is 0; start at the sentinel MAX so block-wise
    // `min()` reduction preserves the true minimum (required for the
    // Phred64 autodetect to ever fire on high-offset data).
    merged.qmin = u8::MAX;
    let total = data.len() as u64;
    let mut done_bytes = 0u64;
    for block in outputs.drain(..) {
        if cancel.map(|f| f.load(Ordering::Relaxed)).unwrap_or(false) {
            return Err(CoreError::Cancelled);
        }
        merged.warnings.merge(&block.warnings);
        merged.qmin = merged.qmin.min(block.qmin);
        merged.qmax = merged.qmax.max(block.qmax);
        for (i, name) in block.names.iter().enumerate() {
            if let Some(limit) = max_records {
                if merged.lengths.len() as u64 >= limit {
                    merged.truncated_by_limit = true;
                    break;
                }
            }
            let s0 = block.seq_offsets[i] as usize;
            let s1 = block.seq_offsets[i + 1] as usize;
            let q0 = block.qual_offsets[i] as usize;
            let q1 = block.qual_offsets[i + 1] as usize;
            merged.names.push(name.clone());
            merged
                .seq_concat
                .extend_from_slice(&block.seq_concat[s0..s1]);
            merged.seq_offsets.push(merged.seq_concat.len() as u64);
            merged
                .qual_concat
                .extend_from_slice(&block.qual_concat[q0..q1]);
            merged.qual_offsets.push(merged.qual_concat.len() as u64);
            merged.lengths.push(block.lengths[i]);
        }
        done_bytes += (block.seq_concat.len() + block.qual_concat.len()) as u64;
        if let Some(cb) = progress.as_mut() {
            cb(done_bytes.min(total), total);
        }
        if merged.truncated_by_limit {
            break;
        }
    }
    if let Some(cb) = progress.as_mut() {
        cb(total, total);
    }
    Ok(merged)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn toy_fastq(n: usize, len: usize) -> Vec<u8> {
        let mut out = Vec::new();
        for i in 0..n {
            out.extend_from_slice(format!("@read{} desc\n", i).as_bytes());
            out.extend_from_slice(&vec![b"ACGT"[i % 4]; len]);
            out.extend_from_slice(b"\n+\n");
            out.extend_from_slice(&vec![b'I'; len]);
            out.extend_from_slice(b"\n");
        }
        out
    }

    #[test]
    fn parses_strict_records() {
        let data = toy_fastq(10, 20);
        let out = parse_payload(&data, 2, None, None, None).unwrap();
        assert_eq!(out.n_reads(), 10);
        assert_eq!(out.lengths.iter().sum::<u64>(), 200);
        assert_eq!(out.names[0], "read0 desc");
        assert_eq!(out.phred(), PhredEncoding::Phred33);
    }

    #[test]
    fn parallel_matches_serial() {
        let data = toy_fastq(5000, 60);
        let a = parse_payload(&data, 1, None, None, None).unwrap();
        let b = parse_payload(&data, 4, None, None, None).unwrap();
        assert_eq!(a.names, b.names);
        assert_eq!(a.seq_concat, b.seq_concat);
        assert_eq!(a.qual_concat, b.qual_concat);
    }

    #[test]
    fn crlf_and_truncation_are_tolerated() {
        // Vec<u8> has no str::replace-style API; convert LF to CRLF byte-wise.
        let mut data = Vec::new();
        for byte in toy_fastq(3, 10) {
            if byte == b'\n' {
                data.push(b'\r');
            }
            data.push(byte);
        }
        data.extend_from_slice(b"@broken\nACGT\n+\n"); // truncated: 4 quals < 4? qual empty < seq
        let out = parse_payload(&data, 2, None, None, None).unwrap();
        assert_eq!(out.n_reads(), 3);
        assert!(out.warnings.truncated_records >= 1);
    }

    #[test]
    fn malformed_records_are_skipped_not_fatal() {
        let mut data = toy_fastq(2, 8);
        data.extend_from_slice(b"garbage line without header\n");
        data.extend_from_slice(&toy_fastq(2, 8));
        let out = parse_payload(&data, 2, None, None, None).unwrap();
        assert_eq!(out.n_reads(), 4);
        assert!(out.warnings.malformed_records >= 1);
    }

    #[test]
    fn max_records_cap() {
        let data = toy_fastq(50, 10);
        let out = parse_payload(&data, 2, Some(10), None, None).unwrap();
        assert_eq!(out.n_reads(), 10);
        assert!(out.truncated_by_limit);
    }

    #[test]
    fn wrapped_fastq_recovers_all_records() {
        let data = b"@r1\nACGTAC\nGTACGT\n+\nIIIIII\nIIIIII\n@r2\nACGT\n+\nIIII\n".to_vec();
        let mut warnings = ParseWarnings::default();
        let owned = parse_records_owned(&data, &mut warnings);
        assert_eq!(owned.len(), 2);
        assert_eq!(owned[0].1, b"ACGTACGTACGT");
    }
}
