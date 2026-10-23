//! gzip / BGZF decompression with multithreaded BGZF-block expansion.
//!
//! * Plain bytes → returned untouched (zero-copy).
//! * Single-member gzip → `flate2` inflate (single-threaded; the gzip format
//!   does not describe where its deflate stream ends, so members cannot be
//!   split safely without decoding).
//! * BGZF / multi-member gzip where each member carries a `BC` extra field →
//!   members are located by header parsing and inflated **in parallel** with
//!   rayon (this covers `.bam`, `.vcf.gz` from htslib and bgzipped FASTQ).

use std::io::Read;

use flate2::read::GzDecoder;
use rayon::prelude::*;

use crate::error::{CoreError, Result};

#[inline]
pub fn is_gzip(input: &[u8]) -> bool {
    input.len() >= 2 && input[0] == 0x1f && input[1] == 0x8b
}

/// BGZF = gzip member whose FEXTRA field contains the `BC` subfield.
pub fn is_bgzf(input: &[u8]) -> bool {
    if input.len() < 16 || !is_gzip(input) {
        return false;
    }
    let flg = input[3];
    if flg & 0x04 == 0 {
        return false;
    }
    let xlen = u16::from_le_bytes([input[10], input[11]]) as usize;
    let mut i = 12usize;
    let end = 12usize.saturating_add(xlen).min(input.len());
    while i + 4 <= end {
        let si1 = input[i];
        let si2 = input[i + 1];
        let slen = u16::from_le_bytes([input[i + 2], input[i + 3]]) as usize;
        if si1 == b'B' && si2 == b'C' && slen == 2 {
            return true;
        }
        i += 4 + slen;
    }
    false
}

/// Return the byte ranges (start, end) of every BGZF member, including the
/// trailing EOF marker block when present. Fails on a truncated member.
fn split_bgzf_members(input: &[u8]) -> Result<Vec<(usize, usize)>> {
    let mut members = Vec::new();
    let mut pos = 0usize;
    while pos < input.len() {
        if input.len() - pos < 18 {
            return Err(CoreError::Parse("truncated BGZF block header".into()));
        }
        let hdr = &input[pos..];
        if hdr[0] != 0x1f || hdr[1] != 0x8b || hdr[2] != 8 {
            return Err(CoreError::Parse("invalid gzip magic in BGZF stream".into()));
        }
        if hdr[3] & 0x04 == 0 {
            return Err(CoreError::Parse("BGZF block missing FEXTRA".into()));
        }
        let xlen = u16::from_le_bytes([hdr[10], hdr[11]]) as usize;
        let mut bsize: Option<u16> = None;
        let mut i = 12usize;
        let xend = 12usize + xlen;
        if xend > hdr.len() {
            return Err(CoreError::Parse("truncated BGZF extra field".into()));
        }
        while i + 4 <= xend {
            let slen = u16::from_le_bytes([hdr[i + 2], hdr[i + 3]]) as usize;
            if hdr[i] == b'B' && hdr[i + 1] == b'C' && slen == 2 {
                if i + 6 > hdr.len() {
                    return Err(CoreError::Parse("truncated BGZF BC subfield".into()));
                }
                bsize = Some(u16::from_le_bytes([hdr[i + 4], hdr[i + 5]]));
                break;
            }
            i += 4 + slen;
        }
        let bsize = bsize.ok_or_else(|| CoreError::Parse("BGZF block missing BC subfield".into()))?;
        let total = bsize as usize + 1;
        if pos + total > input.len() {
            return Err(CoreError::Parse("truncated BGZF block payload".into()));
        }
        members.push((pos, pos + total));
        pos += total;
    }
    Ok(members)
}

fn inflate_one(member: &[u8]) -> Result<Vec<u8>> {
    let mut out = Vec::new();
    let mut decoder = GzDecoder::new(member);
    decoder
        .read_to_end(&mut out)
        .map_err(|e| CoreError::Parse(format!("gzip inflate failed: {e}")))?;
    Ok(out)
}

/// Decompress `input`, expanding BGZF members on a bounded rayon pool.
/// Non-gzip input is returned unchanged.
pub fn decompress(input: &[u8], threads: usize) -> Result<Vec<u8>> {
    if !is_gzip(input) {
        return Ok(input.to_vec());
    }
    if is_bgzf(input) {
        return decompress_bgzf_parallel(input, threads);
    }
    inflate_one(input)
}

fn decompress_bgzf_parallel(input: &[u8], threads: usize) -> Result<Vec<u8>> {
    let members = split_bgzf_members(input)?;
    let mut pieces: Vec<Vec<u8>> = if threads == 1 || members.len() <= 1 {
        members
            .iter()
            .map(|&(s, e)| inflate_one(&input[s..e]))
            .collect::<Result<Vec<_>>>()?
    } else {
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(threads)
            .build()
            .map_err(|e| CoreError::Io(format!("thread pool build failed: {e}")))?;
        pool.install(|| {
            members
                .par_iter()
                .map(|&(s, e)| inflate_one(&input[s..e]))
                .collect::<Result<Vec<_>>>()
        })?
    };
    let total = pieces.iter().map(Vec::len).sum();
    let mut out = Vec::with_capacity(total);
    for piece in pieces.drain(..) {
        out.extend_from_slice(&piece);
    }
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use flate2::write::GzEncoder;
    use flate2::Compression;
    use std::io::Write;

    fn gzip_bytes(data: &[u8]) -> Vec<u8> {
        let mut enc = GzEncoder::new(Vec::new(), Compression::default());
        enc.write_all(data).unwrap();
        enc.finish().unwrap()
    }

    /// Build a BGZF-style stream: gzip members whose extra field carries `BC`.
    fn bgzf_member(data: &[u8]) -> Vec<u8> {
        let payload = {
            let mut enc = GzEncoder::new(Vec::new(), Compression::default());
            enc.write_all(data).unwrap();
            enc.finish().unwrap()
        };
        // Rewrite the header with FEXTRA + BC(=payload_len+25-1 adjusted below).
        let mut body = payload[10..].to_vec(); // skip original 10-byte header
        let xlen = 6usize;
        let total = 12 + xlen + body.len();
        let mut out = Vec::with_capacity(total);
        out.extend_from_slice(&[0x1f, 0x8b, 8, 0x04, 0, 0, 0, 0, 0, 0xff]);
        out.extend_from_slice(&(xlen as u16).to_le_bytes());
        out.extend_from_slice(b"BC");
        out.extend_from_slice(&2u16.to_le_bytes());
        out.extend_from_slice(&((total - 1) as u16).to_le_bytes());
        out.append(&mut body);
        out
    }

    #[test]
    fn plain_bytes_pass_through() {
        let data = b"ACGTACGT".to_vec();
        assert_eq!(decompress(&data, 2).unwrap(), data);
    }

    #[test]
    fn single_gzip_member_roundtrip() {
        let raw = b"@r1\nACGT\n+\nIIII\n".repeat(100);
        let gz = gzip_bytes(&raw);
        assert!(is_gzip(&gz) && !is_bgzf(&gz));
        assert_eq!(decompress(&gz, 2).unwrap(), raw);
    }

    #[test]
    fn bgzf_parallel_roundtrip() {
        let mut stream = Vec::new();
        let mut expected = Vec::new();
        for i in 0..8u8 {
            let chunk = vec![b'A' + i; 512];
            stream.extend_from_slice(&bgzf_member(&chunk));
            expected.extend_from_slice(&chunk);
        }
        assert!(is_bgzf(&stream));
        let out = decompress_bgzf_parallel(&stream, 4).unwrap();
        assert_eq!(out, expected);
    }

    #[test]
    fn truncated_bgzf_reports_parse_error() {
        let mut stream = bgzf_member(b"ACGT");
        stream.truncate(stream.len() - 5);
        assert!(decompress_bgzf_parallel(&stream, 2).is_err());
    }
}
