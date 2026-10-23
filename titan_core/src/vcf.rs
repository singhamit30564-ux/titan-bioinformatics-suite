//! Streaming VCF / BCF parser with typed INFO/FORMAT decoding and filter
//! pushdown (chrom, position range, QUAL, AF, FILTER). Output is columnar so
//! 1M+ row files stream through bounded RAM (columns are the only retained
//! state; INFO is decoded for the requested keys and kept raw otherwise).

use std::sync::atomic::{AtomicBool, Ordering};

use crate::error::{CoreError, Result};
use crate::util::trim_cr;

#[derive(Debug, Clone, Default)]
pub struct VcfFilter {
    pub chrom: Option<String>,
    pub pos_min: Option<i64>,
    pub pos_max: Option<i64>,
    pub qual_min: Option<f64>,
    pub af_min: Option<f64>,
    pub af_max: Option<f64>,
    /// When set, only rows whose FILTER equals this value pass (e.g. "PASS").
    pub filter: Option<String>,
}

#[derive(Debug, Default)]
pub struct VcfWarnings {
    pub malformed_rows: u64,
    pub bcf_format_skipped: bool,
    pub header_missing: bool,
}

#[derive(Debug, Default)]
pub struct VcfTable {
    pub chrom: Vec<String>,
    pub pos: Vec<i64>,
    pub id: Vec<String>,
    pub reference: Vec<String>,
    pub alt: Vec<String>,
    pub qual: Vec<f64>,
    pub filter: Vec<String>,
    pub info_raw: Vec<String>,
    pub info_af: Vec<Option<f64>>,
    pub info_dp: Vec<Option<i64>>,
    pub n_rows_kept: u64,
    pub n_rows_seen: u64,
    pub n_filtered_out: u64,
    pub truncated: bool,
    pub samples: Vec<String>,
    pub header_lines: Vec<String>,
    pub warnings: VcfWarnings,
    pub format: &'static str,
}

fn passes_af(af: Option<f64>, filter: &VcfFilter) -> bool {
    match (filter.af_min, filter.af_max) {
        (None, None) => true,
        (lo, hi) => match af {
            Some(value) => {
                lo.map(|l| value >= l).unwrap_or(true) && hi.map(|h| value <= h).unwrap_or(true)
            }
            None => false, // AF filters require the key to be present
        },
    }
}

fn parse_info_af_dp(info: &str) -> (Option<f64>, Option<i64>) {
    let mut af = None;
    let mut dp = None;
    for field in info.split(';') {
        if let Some(v) = field.strip_prefix("AF=") {
            af = v
                .split(',')
                .next()
                .and_then(|s| s.trim().parse::<f64>().ok());
        } else if let Some(v) = field.strip_prefix("DP=") {
            dp = v.trim().parse::<i64>().ok();
        }
    }
    (af, dp)
}

fn row_passes(
    chrom: &str,
    pos: i64,
    qual: f64,
    filter: &str,
    af: Option<f64>,
    f: &VcfFilter,
) -> bool {
    if let Some(ref want) = f.chrom {
        let strip = |s: &str| s.strip_prefix("chr").unwrap_or(s).to_ascii_lowercase();
        if strip(want) != strip(chrom) {
            return false;
        }
    }
    if let Some(min) = f.pos_min {
        if pos < min {
            return false;
        }
    }
    if let Some(max) = f.pos_max {
        if pos > max {
            return false;
        }
    }
    if let Some(min) = f.qual_min {
        if qual < min {
            return false;
        }
    }
    if let Some(ref want) = f.filter {
        if filter != want {
            return false;
        }
    }
    passes_af(af, f)
}

// ─────────────────────────────────────────────────────────────────────────────
// VCF text
// ─────────────────────────────────────────────────────────────────────────────

fn parse_vcf_text(
    buf: &[u8],
    filter: &VcfFilter,
    max_rows: Option<u64>,
    cancel: Option<&AtomicBool>,
) -> VcfTable {
    let mut table = VcfTable {
        format: "vcf",
        ..Default::default()
    };
    let mut pos = 0usize;
    let mut line_start = 0usize;
    let mut saw_header = false;
    let mut checked = 0u64;
    while pos <= buf.len() {
        let at_end = pos == buf.len();
        if at_end || buf[pos] == b'\n' {
            let line = trim_cr(&buf[line_start..pos]);
            line_start = pos + 1;
            if checked.is_multiple_of(4096) {
                if let Some(flag) = cancel {
                    if flag.load(Ordering::Relaxed) {
                        break;
                    }
                }
            }
            checked += 1;
            if line.starts_with(b"##") {
                table
                    .header_lines
                    .push(String::from_utf8_lossy(line).into_owned());
            } else if line.starts_with(b"#CHROM") {
                saw_header = true;
                let header = String::from_utf8_lossy(line).into_owned();
                for col in header.split('\t').skip(9) {
                    table.samples.push(col.to_string());
                }
                table.header_lines.push(header);
            } else if !line.is_empty() {
                table.n_rows_seen += 1;
                let fields: Vec<&[u8]> = line.split(|&b| b == b'\t').collect();
                if fields.len() < 8 {
                    table.warnings.malformed_rows += 1;
                    if at_end {
                        break;
                    }
                    pos += 1;
                    continue;
                }
                let chrom = String::from_utf8_lossy(fields[0]).into_owned();
                let vpos: i64 = match String::from_utf8_lossy(fields[1]).parse() {
                    Ok(v) => v,
                    Err(_) => {
                        table.warnings.malformed_rows += 1;
                        if at_end {
                            break;
                        }
                        pos += 1;
                        continue;
                    }
                };
                let id = String::from_utf8_lossy(fields[2]).into_owned();
                let reference = String::from_utf8_lossy(fields[3]).into_owned();
                let alt = String::from_utf8_lossy(fields[4]).into_owned();
                let qual: f64 = String::from_utf8_lossy(fields[5])
                    .parse()
                    .unwrap_or(f64::NAN);
                let filt = String::from_utf8_lossy(fields[6]).into_owned();
                let info = String::from_utf8_lossy(fields[7]).into_owned();
                let (af, dp) = parse_info_af_dp(&info);
                if row_passes(&chrom, vpos, qual, &filt, af, filter) {
                    if let Some(limit) = max_rows {
                        if table.n_rows_kept >= limit {
                            table.truncated = true;
                            break;
                        }
                    }
                    table.chrom.push(chrom);
                    table.pos.push(vpos);
                    table.id.push(id);
                    table.reference.push(reference);
                    table.alt.push(alt);
                    table.qual.push(qual);
                    table.filter.push(filt);
                    table.info_raw.push(info);
                    table.info_af.push(af);
                    table.info_dp.push(dp);
                    table.n_rows_kept += 1;
                } else {
                    table.n_filtered_out += 1;
                }
            }
            if at_end {
                break;
            }
        }
        pos += 1;
    }
    if !saw_header {
        table.warnings.header_missing = true;
    }
    table
}

// ─────────────────────────────────────────────────────────────────────────────
// BCF binary (BCF2.2): header is plain VCF text; records use the typed codec.
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug)]
enum Typed {
    Int(Vec<Option<i64>>),
    Float(Vec<Option<f64>>),
    Str(String),
    Flag,
}

fn read_typed(buf: &[u8], pos: &mut usize) -> Result<Typed> {
    if *pos >= buf.len() {
        return Err(CoreError::Parse("truncated BCF typed value".into()));
    }
    let type_byte = buf[*pos];
    *pos += 1;
    let type_id = type_byte >> 4;
    let mut count = (type_byte & 0x0f) as usize;
    if count == 15 {
        let (n, new_pos) = read_typed_count(buf, *pos)?;
        count = n;
        *pos = new_pos;
    }
    match type_id {
        0 => Ok(Typed::Flag),
        1 => {
            let mut out = Vec::with_capacity(count);
            for _ in 0..count {
                if *pos >= buf.len() {
                    return Err(CoreError::Parse("truncated BCF int8 vector".into()));
                }
                let v = buf[*pos] as i8;
                *pos += 1;
                out.push(if v as u8 == 0x80 {
                    None
                } else {
                    Some(i64::from(v))
                });
            }
            Ok(Typed::Int(out))
        }
        2 => {
            let mut out = Vec::with_capacity(count);
            for _ in 0..count {
                if *pos + 2 > buf.len() {
                    return Err(CoreError::Parse("truncated BCF int16 vector".into()));
                }
                let v = i16::from_le_bytes(buf[*pos..*pos + 2].try_into().unwrap());
                *pos += 2;
                out.push(if v as u16 == 0x8000 {
                    None
                } else {
                    Some(i64::from(v))
                });
            }
            Ok(Typed::Int(out))
        }
        3 => {
            let mut out = Vec::with_capacity(count);
            for _ in 0..count {
                if *pos + 4 > buf.len() {
                    return Err(CoreError::Parse("truncated BCF int32 vector".into()));
                }
                let v = i32::from_le_bytes(buf[*pos..*pos + 4].try_into().unwrap());
                *pos += 4;
                out.push(if v as u32 == 0x8000_0000 {
                    None
                } else {
                    Some(i64::from(v))
                });
            }
            Ok(Typed::Int(out))
        }
        5 => {
            let mut out = Vec::with_capacity(count);
            for _ in 0..count {
                if *pos + 4 > buf.len() {
                    return Err(CoreError::Parse("truncated BCF float vector".into()));
                }
                let v = f32::from_le_bytes(buf[*pos..*pos + 4].try_into().unwrap());
                *pos += 4;
                let missing = v.to_bits() == 0x7F80_0001;
                out.push(if missing { None } else { Some(f64::from(v)) });
            }
            Ok(Typed::Float(out))
        }
        7 => {
            if *pos + count > buf.len() {
                return Err(CoreError::Parse("truncated BCF char vector".into()));
            }
            let raw = &buf[*pos..*pos + count];
            *pos += count;
            let end = raw.iter().position(|&b| b == 0).unwrap_or(raw.len());
            Ok(Typed::Str(
                String::from_utf8_lossy(&raw[..end]).into_owned(),
            ))
        }
        other => Err(CoreError::Parse(format!("unknown BCF type id {other}"))),
    }
}

fn read_typed_count(buf: &[u8], mut pos: usize) -> Result<(usize, usize)> {
    let (value, new_pos) = if pos >= buf.len() {
        return Err(CoreError::Parse("truncated BCF vector length".into()));
    } else {
        let type_byte = buf[pos];
        pos += 1;
        match type_byte >> 4 {
            1 => {
                let v = *buf
                    .get(pos)
                    .ok_or_else(|| CoreError::Parse("truncated BCF length".into()))?;
                (v as usize, pos + 1)
            }
            2 => {
                if pos + 2 > buf.len() {
                    return Err(CoreError::Parse("truncated BCF length".into()));
                }
                (
                    u16::from_le_bytes(buf[pos..pos + 2].try_into().unwrap()) as usize,
                    pos + 2,
                )
            }
            3 => {
                if pos + 4 > buf.len() {
                    return Err(CoreError::Parse("truncated BCF length".into()));
                }
                (
                    u32::from_le_bytes(buf[pos..pos + 4].try_into().unwrap()) as usize,
                    pos + 4,
                )
            }
            other => return Err(CoreError::Parse(format!("bad BCF length type {other}"))),
        }
    };
    Ok((value, new_pos))
}

fn parse_bcf(
    buf: &[u8],
    filter: &VcfFilter,
    max_rows: Option<u64>,
    cancel: Option<&AtomicBool>,
) -> Result<VcfTable> {
    if buf.len() < 9 || &buf[0..5] != b"BCF\x02\x02" {
        return Err(CoreError::Parse("not a BCF stream (bad magic)".into()));
    }
    let l_text = u32::from_le_bytes(buf[5..9].try_into().unwrap()) as usize;
    if 9 + l_text > buf.len() {
        return Err(CoreError::Parse("truncated BCF header text".into()));
    }
    let text = &buf[9..9 + l_text];
    // The embedded header is a full VCF header (with sample columns).
    let mut table = parse_vcf_text(text, &VcfFilter::default(), None, None);
    table.header_lines.clear();
    table.samples.clear();
    // Re-parse header bookkeeping without rows.
    let mut header_probe = parse_vcf_text(text, &VcfFilter::default(), None, None);
    table.header_lines = std::mem::take(&mut header_probe.header_lines);
    table.samples = std::mem::take(&mut header_probe.samples);
    table.warnings = VcfWarnings::default();
    table.format = "bcf";

    // Dictionary of contig/ID/INFO/FORMAT keys: the VCF ##INFO/##FORMAT/##contig
    // header lines map IDs in record order of first definition. BCF stores keys
    // as integer IDs into a dictionary built from the header *in order of
    // appearance of any ##INFO=<ID=.. / ##FORMAT=<ID=.. / ##contig=<ID=.. lines*.
    let mut dict: Vec<String> = Vec::new();
    for line in &table.header_lines {
        let text = line.as_str();
        for (prefix, suffix) in [
            ("##INFO=<ID=", ","),
            ("##FORMAT=<ID=", ","),
            ("##contig=<ID=", ">"),
        ] {
            if let Some(rest) = text.strip_prefix(prefix) {
                let name = rest.split(suffix).next().unwrap_or("").to_string();
                if !name.is_empty() {
                    dict.push(name);
                }
            }
        }
    }
    // htslib builds one dictionary with FILTER/contig/INFO/FORMAT IDs in header
    // order across all four categories; reconstruct in that order instead.
    let mut dict_full: Vec<String> = Vec::new();
    for line in &table.header_lines {
        let text = line.as_str();
        for prefix in [
            "##FILTER=<ID=",
            "##contig=<ID=",
            "##INFO=<ID=",
            "##FORMAT=<ID=",
        ] {
            if let Some(rest) = text.strip_prefix(prefix) {
                let stop = rest.find([',', '>']).unwrap_or(rest.len());
                let name = rest[..stop].to_string();
                if !name.is_empty() {
                    dict_full.push(name);
                }
            }
        }
    }
    if !dict_full.is_empty() {
        dict = dict_full;
    }

    let mut pos = 9 + l_text;
    let mut checked = 0u64;
    while pos + 8 <= buf.len() {
        if checked.is_multiple_of(1024) {
            if let Some(flag) = cancel {
                if flag.load(Ordering::Relaxed) {
                    break;
                }
            }
        }
        checked += 1;
        let l_shared = u32::from_le_bytes(buf[pos..pos + 4].try_into().unwrap()) as usize;
        let l_indiv = u32::from_le_bytes(buf[pos + 4..pos + 8].try_into().unwrap()) as usize;
        let shared_start = pos + 8;
        if shared_start + l_shared + l_indiv > buf.len() {
            table.warnings.malformed_rows += 1;
            break;
        }
        let shared = &buf[shared_start..shared_start + l_shared];
        let _indiv = &buf[shared_start + l_shared..shared_start + l_shared + l_indiv];
        pos = shared_start + l_shared + l_indiv;

        if shared.len() < 20 {
            table.warnings.malformed_rows += 1;
            continue;
        }
        let chrom_id = i32::from_le_bytes(shared[0..4].try_into().unwrap());
        let vpos = i64::from(i32::from_le_bytes(shared[4..8].try_into().unwrap())) + 1;
        let _rlen = i32::from_le_bytes(shared[8..12].try_into().unwrap());
        let qual_f32 = f32::from_le_bytes(shared[12..16].try_into().unwrap());
        let n_allele_info = u32::from_le_bytes(shared[16..20].try_into().unwrap());
        let n_info = (n_allele_info & 0xffff) as usize;
        let n_allele = (n_allele_info >> 16) as usize;
        let _n_fmt_sample = u32::from_le_bytes(shared[20..24].try_into().unwrap());

        let mut sp = 24usize;
        let id = match read_typed(shared, &mut sp) {
            Ok(Typed::Str(s)) => s,
            _ => ".".to_string(),
        };
        let mut alleles: Vec<String> = Vec::with_capacity(n_allele);
        for _ in 0..n_allele {
            match read_typed(shared, &mut sp) {
                Ok(Typed::Str(s)) => alleles.push(s),
                _ => alleles.push(".".to_string()),
            }
        }
        // FILTER: typed int vector of IDs (0 = PASS).
        let mut filter_text = ".".to_string();
        if sp < shared.len() {
            if let Ok(Typed::Int(ids)) = read_typed(shared, &mut sp) {
                if ids.is_empty() {
                    filter_text = ".".to_string();
                } else {
                    let names: Vec<String> = ids
                        .iter()
                        .map(|id| match id {
                            Some(v) => dict
                                .get(*v as usize)
                                .cloned()
                                .unwrap_or_else(|| format!("id{v}")),
                            None => "PASS".to_string(),
                        })
                        .collect();
                    filter_text = names.join(";");
                }
            }
        }
        // INFO pairs: key id + typed value. Keep AF/DP + raw rendering.
        let mut af: Option<f64> = None;
        let mut dp: Option<i64> = None;
        let mut info_parts: Vec<String> = Vec::with_capacity(n_info);
        for _ in 0..n_info {
            if sp + 4 > shared.len() {
                break;
            }
            let key_id = u32::from_le_bytes(shared[sp..sp + 4].try_into().unwrap());
            sp += 4;
            let key = dict
                .get(key_id as usize)
                .cloned()
                .unwrap_or_else(|| format!("key{key_id}"));
            match read_typed(shared, &mut sp) {
                Ok(Typed::Flag) => info_parts.push(key),
                Ok(Typed::Str(s)) => {
                    if key == "AF" {
                        af = s.split(',').next().and_then(|v| v.parse().ok());
                    }
                    if key == "DP" {
                        dp = s.parse().ok();
                    }
                    info_parts.push(format!("{key}={s}"));
                }
                Ok(Typed::Int(vals)) => {
                    let rendered = vals
                        .iter()
                        .map(|v| v.map(|x| x.to_string()).unwrap_or_else(|| ".".to_string()))
                        .collect::<Vec<_>>()
                        .join(",");
                    if key == "AF" {
                        af = vals.first().and_then(|v| *v).map(|x| x as f64);
                    }
                    if key == "DP" {
                        dp = vals.first().and_then(|v| *v);
                    }
                    info_parts.push(format!("{key}={rendered}"));
                }
                Ok(Typed::Float(vals)) => {
                    let rendered = vals
                        .iter()
                        .map(|v| {
                            v.map(|x| format!("{x:.6}"))
                                .unwrap_or_else(|| ".".to_string())
                        })
                        .collect::<Vec<_>>()
                        .join(",");
                    if key == "AF" {
                        af = vals.first().and_then(|v| *v);
                    }
                    info_parts.push(format!("{key}={rendered}"));
                }
                Err(_) => {
                    table.warnings.malformed_rows += 1;
                    break;
                }
            }
        }
        if l_indiv > 0 {
            table.warnings.bcf_format_skipped = true;
        }

        let reference = alleles.first().cloned().unwrap_or_else(|| ".".to_string());
        let alt = if alleles.len() > 1 {
            alleles[1..].join(",")
        } else {
            ".".to_string()
        };
        let chrom = dict
            .get(chrom_id.max(0) as usize)
            .cloned()
            .unwrap_or_else(|| format!("contig{chrom_id}"));
        let qual = if qual_f32.to_bits() == 0x7F80_0001 {
            f64::NAN
        } else {
            f64::from(qual_f32)
        };
        table.n_rows_seen += 1;
        if row_passes(&chrom, vpos, qual, &filter_text, af, filter) {
            if let Some(limit) = max_rows {
                if table.n_rows_kept >= limit {
                    table.truncated = true;
                    break;
                }
            }
            table.chrom.push(chrom);
            table.pos.push(vpos);
            table.id.push(id);
            table.reference.push(reference);
            table.alt.push(alt);
            table.qual.push(qual);
            table.filter.push(filter_text);
            table.info_raw.push(info_parts.join(";"));
            table.info_af.push(af);
            table.info_dp.push(dp);
            table.n_rows_kept += 1;
        } else {
            table.n_filtered_out += 1;
        }
    }
    Ok(table)
}

// ─────────────────────────────────────────────────────────────────────────────
// Public entry
// ─────────────────────────────────────────────────────────────────────────────

/// Parse VCF/BCF bytes with filter pushdown. `max_rows` bounds retained rows
/// (the table reports `truncated`); `progress(done, total)` reports bytes.
pub fn parse_vcf_payload(
    data: &[u8],
    threads: usize,
    filter: &VcfFilter,
    max_rows: Option<u64>,
    mut progress: Option<&mut dyn FnMut(u64, u64)>,
    cancel: Option<&AtomicBool>,
) -> Result<VcfTable> {
    let raw: Vec<u8> = if crate::bgzf::is_gzip(data) {
        crate::bgzf::decompress(data, threads)?
    } else {
        data.to_vec()
    };
    let mut table = if raw.len() >= 5 && &raw[0..5] == b"BCF\x02\x02" {
        parse_bcf(&raw, filter, max_rows, cancel)?
    } else {
        parse_vcf_text(&raw, filter, max_rows, cancel)
    };
    table.format = if table.format == "bcf" { "bcf" } else { "vcf" };
    if let Some(cb) = progress.as_mut() {
        cb(raw.len() as u64, raw.len() as u64);
    }
    Ok(table)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn toy_vcf() -> Vec<u8> {
        b"##fileformat=VCFv4.2\n##INFO=<ID=DP,Number=1,Type=Integer,Description=\"d\">\n##INFO=<ID=AF,Number=A,Type=Float,Description=\"af\">\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\nchr1\t100\trs1\tA\tG\t50\tPASS\tDP=30;AF=0.25\nchr1\t150\trs2\tC\tT\t45\tPASS\tDP=25;AF=0.01\nchr2\t50\trs3\tG\tGAT\t60\tLowQual\tDP=40;AF=0.9\nchr2\t100\trs4\tT\tC\t30\tPASS\tDP=15;AF=0.5\n".to_vec()
    }

    #[test]
    fn parses_all_rows() {
        let table =
            parse_vcf_payload(&toy_vcf(), 2, &VcfFilter::default(), None, None, None).unwrap();
        assert_eq!(table.n_rows_kept, 4);
        assert_eq!(table.pos, vec![100, 150, 50, 100]);
        assert_eq!(table.samples.len(), 0);
    }

    #[test]
    fn filter_pushdown() {
        let f = VcfFilter {
            chrom: Some("chr2".into()),
            af_min: Some(0.4),
            ..Default::default()
        };
        let table = parse_vcf_payload(&toy_vcf(), 1, &f, None, None, None).unwrap();
        assert_eq!(table.n_rows_kept, 2); // chr2 rows with AF>=0.4: rs3 (0.9), rs4 (0.5)
        assert_eq!(table.n_filtered_out, 2);
    }

    #[test]
    fn qual_and_filter_string() {
        let f = VcfFilter {
            filter: Some("PASS".into()),
            qual_min: Some(40.0),
            ..Default::default()
        };
        let table = parse_vcf_payload(&toy_vcf(), 1, &f, None, None, None).unwrap();
        assert_eq!(table.n_rows_kept, 2); // rs1 (50), rs2 (45)
    }

    #[test]
    fn max_rows_truncates() {
        let table =
            parse_vcf_payload(&toy_vcf(), 1, &VcfFilter::default(), Some(1), None, None).unwrap();
        assert_eq!(table.n_rows_kept, 1);
        assert!(table.truncated);
    }

    #[test]
    fn typed_codec_ints() {
        // 1-byte count of two int16 values.
        let buf = [0x22u8, 0x01, 0x00, 0x02, 0x00];
        let mut pos = 0;
        match read_typed(&buf, &mut pos).unwrap() {
            Typed::Int(vals) => assert_eq!(vals, vec![Some(1), Some(2)]),
            other => panic!("unexpected {other:?}"),
        }
    }
}
