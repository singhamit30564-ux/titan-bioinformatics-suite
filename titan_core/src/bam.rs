//! BAM (binary) / SAM (text) decoding: parallel BGZF inflate + record-walk
//! planning + parallel record decode.
//!
//! Region queries scan and filter (`chr:start-end`, 1-based inclusive) — no
//! index file is required, which keeps the ZDR bytes-in path intact. Coverage
//! depth tracks are computed from CIGAR reference-consuming ops into fixed
//! bins per reference. The flagstat summary matches `samtools flagstat` field
//! semantics (total, primary, secondary, supplementary, duplicates, mapped,
//! paired, read1, read2, properly paired, singletons).

use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};

use rayon::prelude::*;

use crate::error::{CoreError, Result};
use crate::util::trim_cr;

const SAMPLE_LIMIT: usize = 1000;
const COVERAGE_BINS: usize = 1000;

#[derive(Debug, Clone, Default)]
pub struct FlagStats {
    pub total: u64,
    pub primary: u64,
    pub secondary: u64,
    pub supplementary: u64,
    pub duplicates: u64,
    pub mapped: u64,
    pub paired: u64,
    pub read1: u64,
    pub read2: u64,
    pub properly_paired: u64,
    pub with_itself_and_mate_mapped: u64,
    pub singletons: u64,
}

impl FlagStats {
    fn observe(&mut self, flag: u16) {
        self.total += 1;
        if flag & 0x100 != 0 {
            self.secondary += 1;
        } else if flag & 0x800 != 0 {
            self.supplementary += 1;
        } else {
            self.primary += 1;
        }
        if flag & 0x400 != 0 {
            self.duplicates += 1;
        }
        let mapped = flag & 0x4 == 0;
        if mapped {
            self.mapped += 1;
        }
        if flag & 0x1 != 0 {
            self.paired += 1;
            if flag & 0x40 != 0 {
                self.read1 += 1;
            }
            if flag & 0x80 != 0 {
                self.read2 += 1;
            }
            if flag & 0x2 != 0 {
                self.properly_paired += 1;
            }
            if mapped && flag & 0x8 == 0 {
                self.with_itself_and_mate_mapped += 1;
            }
            if mapped && flag & 0x8 != 0 {
                self.singletons += 1;
            }
        }
    }

    fn merge(&mut self, other: &FlagStats) {
        self.total += other.total;
        self.primary += other.primary;
        self.secondary += other.secondary;
        self.supplementary += other.supplementary;
        self.duplicates += other.duplicates;
        self.mapped += other.mapped;
        self.paired += other.paired;
        self.read1 += other.read1;
        self.read2 += other.read2;
        self.properly_paired += other.properly_paired;
        self.with_itself_and_mate_mapped += other.with_itself_and_mate_mapped;
        self.singletons += other.singletons;
    }
}

#[derive(Debug, Clone)]
pub struct Region {
    pub chrom: Option<String>,
    pub start: i64, // 1-based inclusive
    pub end: i64,   // 1-based inclusive; i64::MAX = open
}

impl Region {
    pub fn parse(text: &str) -> Result<Region> {
        let text = text.trim();
        if text.is_empty() {
            return Ok(Region {
                chrom: None,
                start: 1,
                end: i64::MAX,
            });
        }
        // "chr1:100-200" or "chr1" or "chr1:100" (open end).
        let (chrom, rest) = match text.split_once(':') {
            Some((c, rest)) => (Some(c.to_string()), rest),
            None => (Some(text.to_string()), ""),
        };
        let (start, end) = if rest.is_empty() {
            (1, i64::MAX)
        } else if let Some((s, e)) = rest.split_once('-') {
            let start: i64 = s
                .replace(',', "")
                .parse()
                .map_err(|_| CoreError::Input("region start must be an integer".into()))?;
            let end: i64 = e
                .replace(',', "")
                .parse()
                .map_err(|_| CoreError::Input("region end must be an integer".into()))?;
            (start, end)
        } else {
            let start: i64 = rest
                .replace(',', "")
                .parse()
                .map_err(|_| CoreError::Input("region start must be an integer".into()))?;
            (start, i64::MAX)
        };
        if start < 1 || end < start {
            return Err(CoreError::Input("invalid region bounds".into()));
        }
        Ok(Region { chrom, start, end })
    }

    fn matches(&self, chrom: &str, pos1: i64) -> bool {
        if let Some(ref c) = self.chrom {
            if c != chrom && !(c == "*" && chrom == "*") {
                // tolerate 'chr' prefix differences
                let strip = |s: &str| s.strip_prefix("chr").unwrap_or(s);
                if strip(c) != strip(chrom) {
                    return false;
                }
            }
        }
        pos1 >= self.start && pos1 <= self.end
    }
}

#[derive(Debug, Clone)]
pub struct RecordSample {
    pub name: String,
    pub ref_name: String,
    pub pos_1based: i64,
    pub mapq: u8,
    pub flag: u16,
    pub cigar: String,
    pub seq_len: usize,
}

#[derive(Debug, Default)]
struct BlockStats {
    flagstat: FlagStats,
    mapq_hist: [u64; 256],
    coverage: HashMap<String, Vec<u64>>, // ref → per-bin aligned-base depth sums
    sample: Vec<RecordSample>,
    in_region: u64,
}

fn cigar_string(ops: &[(u32, u32)]) -> String {
    let mut out = String::new();
    for &(len, op) in ops {
        out.push_str(&len.to_string());
        out.push(b"MIDNSHP=X"[op as usize] as char);
    }
    out
}

/// Reference length consumed by a CIGAR (ops M/D/N/=/X).
#[allow(dead_code)]
fn ref_span(ops: &[(u32, u32)]) -> u64 {
    ops.iter()
        .filter(|(_, op)| matches!(op, 0 | 2 | 3 | 7 | 8))
        .map(|(len, _)| *len as u64)
        .sum()
}

fn add_coverage(
    coverage: &mut HashMap<String, Vec<u64>>,
    ref_name: &str,
    ref_len: i64,
    pos0: i64,
    ops: &[(u32, u32)],
    region: Option<&Region>,
) {
    if ref_len <= 0 {
        return;
    }
    let bins = COVERAGE_BINS;
    let bin_size = ((ref_len as f64) / bins as f64).max(1.0);
    let entry = coverage
        .entry(ref_name.to_string())
        .or_insert_with(|| vec![0; bins]);
    let mut cursor = pos0;
    for &(len, op) in ops {
        let consumes = matches!(op, 0 | 2 | 3 | 7 | 8);
        if consumes {
            // Accumulate per-bin overlap of [cursor, cursor+len).
            let mut left = cursor;
            let right = cursor + i64::from(len);
            while left < right {
                let bin = ((left as f64) / bin_size) as usize;
                let bin_end = (((bin + 1) as f64) * bin_size) as i64;
                let chunk = (right.min(bin_end) - left).max(0) as u64;
                if bin < entry.len() {
                    // Only count bases inside the requested region.
                    let count = match region {
                        Some(r) => {
                            // positions are 0-based internally; region is 1-based.
                            let mut counted = 0u64;
                            for p in left..right.min(bin_end) {
                                if r.matches(ref_name, p + 1) {
                                    counted += 1;
                                }
                            }
                            counted
                        }
                        None => chunk,
                    };
                    entry[bin] += count;
                }
                left = bin_end;
            }
            cursor = right;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// BAM binary decode
// ─────────────────────────────────────────────────────────────────────────────

struct BamHeader {
    text: String,
    references: Vec<(String, i64)>,
    records_start: usize,
}

fn decode_bam_header(buf: &[u8]) -> Result<BamHeader> {
    if buf.len() < 12 || &buf[0..4] != b"BAM\x01" {
        return Err(CoreError::Parse("not a BAM stream (bad magic)".into()));
    }
    let l_text = i32::from_le_bytes(buf[4..8].try_into().unwrap()) as usize;
    let mut pos = 8 + l_text;
    if pos + 4 > buf.len() {
        return Err(CoreError::Parse("truncated BAM header text".into()));
    }
    let text = String::from_utf8_lossy(&buf[8..8 + l_text]).into_owned();
    let n_ref = i32::from_le_bytes(buf[pos..pos + 4].try_into().unwrap());
    pos += 4;
    let mut references = Vec::with_capacity(n_ref.max(0) as usize);
    for _ in 0..n_ref.max(0) {
        if pos + 4 > buf.len() {
            return Err(CoreError::Parse("truncated BAM reference list".into()));
        }
        let l_name = i32::from_le_bytes(buf[pos..pos + 4].try_into().unwrap()) as usize;
        pos += 4;
        if pos + l_name + 4 > buf.len() {
            return Err(CoreError::Parse("truncated BAM reference entry".into()));
        }
        let name_bytes = &buf[pos..pos + l_name];
        let name_bytes = name_bytes.strip_suffix(&[0u8][..]).unwrap_or(name_bytes);
        let name = String::from_utf8_lossy(trim_cr(name_bytes)).into_owned();
        pos += l_name;
        let l_ref = i32::from_le_bytes(buf[pos..pos + 4].try_into().unwrap());
        pos += 4;
        references.push((name, i64::from(l_ref)));
    }
    Ok(BamHeader {
        text,
        references,
        records_start: pos,
    })
}

/// Walk record headers (block_size only) to find record-boundary offsets for
/// parallel decode. Cheap: one 4-byte read per record.
fn plan_bam_blocks(buf: &[u8], start: usize, target_records: usize) -> Result<Vec<(usize, usize)>> {
    let mut blocks = Vec::new();
    let mut pos = start;
    let mut block_start = start;
    let mut count = 0usize;
    while pos + 4 <= buf.len() {
        let block_size = i32::from_le_bytes(buf[pos..pos + 4].try_into().unwrap());
        if block_size <= 0 || pos + 4 + block_size as usize > buf.len() {
            // Truncated trailing record — stop cleanly.
            break;
        }
        pos += 4 + block_size as usize;
        count += 1;
        if count >= target_records {
            blocks.push((block_start, pos));
            block_start = pos;
            count = 0;
        }
    }
    if block_start < pos {
        blocks.push((block_start, pos));
    }
    if blocks.is_empty() && start < buf.len() {
        blocks.push((start, start));
    }
    Ok(blocks)
}

fn decode_bam_records(
    buf: &[u8],
    references: &[(String, i64)],
    region: Option<&Region>,
    collect_samples: bool,
    cancel: Option<&AtomicBool>,
) -> BlockStats {
    let mut stats = BlockStats::default();
    let mut pos = 0usize;
    let mut checked = 0u64;
    while pos + 4 <= buf.len() {
        if checked % 4096 == 0 {
            if let Some(flag) = cancel {
                if flag.load(Ordering::Relaxed) {
                    break;
                }
            }
        }
        checked += 1;
        let block_size = i32::from_le_bytes(buf[pos..pos + 4].try_into().unwrap());
        if block_size <= 0 || pos + 4 + block_size as usize > buf.len() {
            break;
        }
        let rec = &buf[pos + 4..pos + 4 + block_size as usize];
        pos += 4 + block_size as usize;
        if rec.len() < 32 {
            continue;
        }
        let ref_id = i32::from_le_bytes(rec[0..4].try_into().unwrap());
        let rpos = i32::from_le_bytes(rec[4..8].try_into().unwrap());
        let l_read_name = rec[8] as usize;
        let mapq = rec[9];
        let n_cigar_op = u16::from_le_bytes(rec[12..14].try_into().unwrap()) as usize;
        let flag = u16::from_le_bytes(rec[14..16].try_into().unwrap());
        let l_seq = i32::from_le_bytes(rec[16..20].try_into().unwrap()) as usize;
        let name_end = 32 + l_read_name;
        if name_end > rec.len() {
            continue;
        }
        let ref_name = if ref_id >= 0 && (ref_id as usize) < references.len() {
            references[ref_id as usize].0.clone()
        } else {
            "*".to_string()
        };
        let ref_len = if ref_id >= 0 && (ref_id as usize) < references.len() {
            references[ref_id as usize].1
        } else {
            0
        };
        let pos_1based = if rpos >= 0 { i64::from(rpos) + 1 } else { 0 };
        let cigar_off = name_end;
        let cigar_end = cigar_off + n_cigar_op * 4;
        if cigar_end > rec.len() {
            continue;
        }
        let mut ops: Vec<(u32, u32)> = Vec::with_capacity(n_cigar_op);
        for i in 0..n_cigar_op {
            let v = u32::from_le_bytes(
                rec[cigar_off + i * 4..cigar_off + i * 4 + 4]
                    .try_into()
                    .unwrap(),
            );
            ops.push((v >> 4, v & 0xf));
        }
        let in_region = ref_id >= 0
            && match region {
                Some(r) => r.matches(&ref_name, pos_1based),
                None => true,
            };
        if in_region {
            stats.in_region += 1;
            stats.flagstat.observe(flag);
            stats.mapq_hist[mapq as usize] += 1;
            if ref_id >= 0 {
                add_coverage(
                    &mut stats.coverage,
                    &ref_name,
                    ref_len,
                    i64::from(rpos),
                    &ops,
                    region,
                );
            }
            if collect_samples && stats.sample.len() < SAMPLE_LIMIT {
                stats.sample.push(RecordSample {
                    name: String::from_utf8_lossy(&rec[32..name_end.saturating_sub(1)])
                        .into_owned(),
                    ref_name,
                    pos_1based,
                    mapq,
                    flag,
                    cigar: cigar_string(&ops),
                    seq_len: l_seq,
                });
            }
        }
    }
    stats
}

// ─────────────────────────────────────────────────────────────────────────────
// SAM text decode
// ─────────────────────────────────────────────────────────────────────────────

fn decode_sam(
    buf: &[u8],
    region: Option<&Region>,
    collect_samples: bool,
    cancel: Option<&AtomicBool>,
) -> (String, Vec<(String, i64)>, BlockStats) {
    let mut header_lines = Vec::new();
    let mut references: Vec<(String, i64)> = Vec::new();
    let mut stats = BlockStats::default();
    let mut line_start = 0usize;
    let mut checked = 0u64;
    let mut pos = 0usize;
    while pos <= buf.len() {
        if pos == buf.len() || buf[pos] == b'\n' {
            let line = trim_cr(&buf[line_start..pos]);
            line_start = pos + 1;
            if checked % 4096 == 0 {
                if let Some(flag) = cancel {
                    if flag.load(Ordering::Relaxed) {
                        break;
                    }
                }
            }
            checked += 1;
            if line.starts_with(b"@") {
                let header = String::from_utf8_lossy(line).into_owned();
                if header.starts_with("@SQ") {
                    // @SQ SN:chr1 LN:248956422
                    let mut name = String::new();
                    let mut len = 0i64;
                    for field in header.split('\t').skip(1) {
                        if let Some(v) = field.strip_prefix("SN:") {
                            name = v.to_string();
                        } else if let Some(v) = field.strip_prefix("LN:") {
                            len = v.parse().unwrap_or(0);
                        }
                    }
                    if !name.is_empty() {
                        references.push((name, len));
                    }
                }
                header_lines.push(header);
            } else if !line.is_empty() {
                let fields: Vec<&[u8]> = line.split(|&b| b == b'\t').collect();
                if fields.len() < 11 {
                    continue;
                }
                let flag: u16 = String::from_utf8_lossy(fields[1]).parse().unwrap_or(0);
                let ref_name = String::from_utf8_lossy(fields[2]).into_owned();
                let pos_1based: i64 = String::from_utf8_lossy(fields[3]).parse().unwrap_or(0);
                let mapq: u8 = String::from_utf8_lossy(fields[4]).parse().unwrap_or(0);
                let cigar = String::from_utf8_lossy(fields[5]).into_owned();
                let seq_len = fields[9].len();
                let in_region = match region {
                    Some(r) => r.matches(&ref_name, pos_1based),
                    None => true,
                };
                if in_region {
                    stats.in_region += 1;
                    stats.flagstat.observe(flag);
                    stats.mapq_hist[mapq as usize] += 1;
                    let ref_len = references
                        .iter()
                        .find(|(n, _)| n == &ref_name)
                        .map(|(_, l)| *l)
                        .unwrap_or(0);
                    if pos_1based > 0 {
                        let ops = parse_cigar_str(&cigar);
                        add_coverage(
                            &mut stats.coverage,
                            &ref_name,
                            ref_len,
                            pos_1based - 1,
                            &ops,
                            region,
                        );
                    }
                    if collect_samples && stats.sample.len() < SAMPLE_LIMIT {
                        stats.sample.push(RecordSample {
                            name: String::from_utf8_lossy(fields[0]).into_owned(),
                            ref_name,
                            pos_1based,
                            mapq,
                            flag,
                            cigar,
                            seq_len,
                        });
                    }
                }
            }
            if pos == buf.len() {
                break;
            }
        }
        pos += 1;
    }
    (header_lines.join("\n"), references, stats)
}

fn parse_cigar_str(cigar: &str) -> Vec<(u32, u32)> {
    let mut ops = Vec::new();
    let mut num = 0u32;
    for ch in cigar.chars() {
        if ch.is_ascii_digit() {
            num = num * 10 + ch.to_digit(10).unwrap_or(0);
        } else {
            let op = match ch {
                'M' => 0,
                'I' => 1,
                'D' => 2,
                'N' => 3,
                'S' => 4,
                'H' => 5,
                'P' => 6,
                '=' => 7,
                'X' => 8,
                _ => 9,
            };
            if op != 9 {
                ops.push((num, op));
            }
            num = 0;
        }
    }
    ops
}

// ─────────────────────────────────────────────────────────────────────────────
// Public entry point
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug)]
pub struct BamReport {
    pub format: &'static str,
    pub header_text: String,
    pub references: Vec<(String, i64)>,
    pub flagstat: FlagStats,
    pub mapq_histogram: Vec<u64>,
    pub coverage: Vec<(String, Vec<u64>, f64)>, // (ref, bin totals, bin_size)
    pub records_sample: Vec<RecordSample>,
    pub n_records_scanned: u64,
    pub n_records_in_region: u64,
    pub region: Option<String>,
}

/// Decode a BAM/SAM payload. `threads` parallelizes BGZF inflate and record
/// decode; `region` filters ("chr:start-end"); `progress(done, total)` reports
/// bytes; `cancel` aborts between blocks.
pub fn read_alignment_payload(
    data: &[u8],
    threads: usize,
    region: Option<&str>,
    progress: Option<&mut dyn FnMut(u64, u64)>,
    cancel: Option<&AtomicBool>,
) -> Result<BamReport> {
    let region = match region {
        Some(text) => Some(Region::parse(text)?),
        None => None,
    };
    let is_bam = data.len() >= 4 && &data[0..4] == b"BAM\x01";
    let is_gz = crate::bgzf::is_gzip(data);
    let raw: Vec<u8> = if is_gz {
        crate::bgzf::decompress(data, threads)?
    } else {
        data.to_vec()
    };

    if !is_bam && !(raw.len() >= 4 && &raw[0..4] == b"BAM\x01") {
        // Treat as SAM text.
        let (header_text, references, mut stats) = decode_sam(&raw, region.as_ref(), true, cancel);
        if let Some(cb) = progress.as_mut() {
            cb(raw.len() as u64, raw.len() as u64);
        }
        let coverage = stats
            .coverage
            .drain()
            .map(|(ref_name, bins)| {
                let ref_len = references
                    .iter()
                    .find(|(n, _)| n == &ref_name)
                    .map(|(_, l)| *l)
                    .unwrap_or(0);
                let bin_size = if ref_len > 0 {
                    (ref_len as f64 / COVERAGE_BINS as f64).max(1.0)
                } else {
                    1.0
                };
                (ref_name, bins, bin_size)
            })
            .collect();
        return Ok(BamReport {
            format: "sam",
            header_text,
            references,
            flagstat: stats.flagstat,
            mapq_histogram: stats.mapq_hist.to_vec(),
            coverage,
            records_sample: stats.sample,
            n_records_scanned: stats.flagstat.total,
            n_records_in_region: stats.in_region,
            region: region.map(|r| format_region(&r)),
        });
    }

    let header = decode_bam_header(&raw)?;
    let blocks = plan_bam_blocks(&raw, header.records_start, 200_000)?;
    let mut per_block: Vec<BlockStats> = if threads == 1 || blocks.len() <= 1 {
        blocks
            .iter()
            .map(|&(s, e)| {
                decode_bam_records(
                    &raw[s..e],
                    &header.references,
                    region.as_ref(),
                    true,
                    cancel,
                )
            })
            .collect()
    } else {
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(threads)
            .build()
            .map_err(|e| CoreError::Io(format!("thread pool build failed: {e}")))?;
        pool.install(|| {
            blocks
                .par_iter()
                .map(|&(s, e)| {
                    decode_bam_records(
                        &raw[s..e],
                        &header.references,
                        region.as_ref(),
                        true,
                        cancel,
                    )
                })
                .collect()
        })
    };

    let mut merged = BlockStats::default();
    let total_bytes = raw.len() as u64;
    for (i, block) in per_block.drain(..).enumerate() {
        if cancel.map(|f| f.load(Ordering::Relaxed)).unwrap_or(false) {
            return Err(CoreError::Cancelled);
        }
        merged.flagstat.merge(&block.flagstat);
        for (idx, &v) in block.mapq_hist.iter().enumerate() {
            merged.mapq_hist[idx] += v;
        }
        for (ref_name, bins) in block.coverage {
            let entry = merged
                .coverage
                .entry(ref_name)
                .or_insert_with(|| vec![0; COVERAGE_BINS]);
            for (dst, src) in entry.iter_mut().zip(bins.iter()) {
                *dst += src;
            }
        }
        let room = SAMPLE_LIMIT.saturating_sub(merged.sample.len());
        merged.sample.extend(block.sample.into_iter().take(room));
        merged.in_region += block.in_region;
        if let Some(cb) = progress.as_mut() {
            let frac = ((i + 1) as f64 / blocks.len().max(1) as f64) * total_bytes as f64;
            cb(frac.min(total_bytes), total_bytes);
        }
    }
    if let Some(cb) = progress.as_mut() {
        cb(total_bytes, total_bytes);
    }

    let coverage = merged
        .coverage
        .drain()
        .map(|(ref_name, bins)| {
            let ref_len = header
                .references
                .iter()
                .find(|(n, _)| n == &ref_name)
                .map(|(_, l)| *l)
                .unwrap_or(0);
            let bin_size = if ref_len > 0 {
                (ref_len as f64 / COVERAGE_BINS as f64).max(1.0)
            } else {
                1.0
            };
            (ref_name, bins, bin_size)
        })
        .collect();

    Ok(BamReport {
        format: "bam",
        header_text: header.text,
        references: header.references,
        flagstat: merged.flagstat,
        mapq_histogram: merged.mapq_hist.to_vec(),
        coverage,
        records_sample: merged.sample,
        n_records_scanned: merged.flagstat.total,
        n_records_in_region: merged.in_region,
        region: region.map(|r| format_region(&r)),
    })
}

fn format_region(r: &Region) -> String {
    match (&r.chrom, r.end) {
        (Some(c), i64::MAX) => format!("{c}:{}-", r.start),
        (Some(c), e) => format!("{c}:{}-{}", r.start, e),
        (None, _) => "*".to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn region_parse_and_match() {
        let r = Region::parse("chr1:100-200").unwrap();
        assert!(r.matches("chr1", 150));
        assert!(!r.matches("chr1", 250));
        assert!(!r.matches("chr2", 150));
        assert!(Region::parse("chr2").unwrap().matches("chr2", 999999));
    }

    #[test]
    fn cigar_ref_span() {
        let ops = vec![(10, 0u32), (2, 1), (5, 2), (20, 0)];
        assert_eq!(ref_span(&ops), 35);
        assert_eq!(cigar_string(&ops), "10M2I5D20M");
    }

    #[test]
    fn sam_text_flagstat() {
        let sam = b"@HD\tVN:1.6\n@SQ\tSN:chr1\tLN:1000\nr1\t0\tchr1\t1\t60\t10M\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII\nr2\t4\t*\t0\t0\t*\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII\n";
        let report = read_alignment_payload(sam, 1, None, None, None).unwrap();
        assert_eq!(report.format, "sam");
        assert_eq!(report.flagstat.total, 2);
        assert_eq!(report.flagstat.mapped, 1);
        assert_eq!(report.references.len(), 1);
    }

    #[test]
    fn sam_region_filter() {
        let sam = b"@SQ\tSN:chr1\tLN:1000\nr1\t0\tchr1\t100\t60\t10M\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII\nr2\t0\tchr1\t500\t60\t10M\t*\t0\t0\tACGTACGTAC\tIIIIIIIIII\n";
        let report = read_alignment_payload(sam, 1, Some("chr1:1-200"), None, None).unwrap();
        assert_eq!(report.n_records_in_region, 1);
    }
}
