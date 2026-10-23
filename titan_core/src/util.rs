//! Small shared helpers: SWAR newline scanning, byte histograms, hashing.

/// Scan `buf` for `\n` byte positions using SWAR 8-byte-at-a-time loads.
/// `offset` is the absolute position of `buf[0]`; results are absolute.
#[inline]
pub fn find_newlines(buf: &[u8], offset: usize, out: &mut Vec<usize>) {
    const WORD: usize = 8;
    let mut i = 0usize;
    let n = buf.len();
    while i + WORD <= n {
        let mut word = [0u8; WORD];
        word.copy_from_slice(&buf[i..i + WORD]);
        let v = u64::from_le_bytes(word);
        // bytes equal to 0x0A: classic haszero-style mask.
        let lo = 0x0101_0101_0101_0101u64;
        let hi = 0x8080_8080_8080_8080u64;
        let x = v ^ (lo * u64::from(b'\n'));
        let mask = (x.wrapping_sub(lo)) & !x & hi;
        if mask != 0 {
            for b in 0..WORD {
                if buf[i + b] == b'\n' {
                    out.push(offset + i + b);
                }
            }
        }
        i += WORD;
    }
    while i < n {
        if buf[i] == b'\n' {
            out.push(offset + i);
        }
        i += 1;
    }
}

/// Count `\n` bytes (SWAR) — used for record-alignment planning.
#[inline]
pub fn count_newlines(buf: &[u8]) -> usize {
    const WORD: usize = 8;
    let mut count = 0usize;
    let mut i = 0usize;
    let n = buf.len();
    while i + WORD <= n {
        let mut word = [0u8; WORD];
        word.copy_from_slice(&buf[i..i + WORD]);
        let v = u64::from_le_bytes(word);
        let lo = 0x0101_0101_0101_0101u64;
        let hi = 0x8080_8080_8080_8080u64;
        let x = v ^ (lo * u64::from(b'\n'));
        let mask = (x.wrapping_sub(lo)) & !x & hi;
        count += (mask >> 7).count_ones() as usize;
        i += WORD;
    }
    while i < n {
        if buf[i] == b'\n' {
            count += 1;
        }
        i += 1;
    }
    count
}

/// Strip one trailing `\r` (CRLF tolerance).
#[inline]
pub fn trim_cr(line: &[u8]) -> &[u8] {
    match line.split_last() {
        Some((b'\r', rest)) => rest,
        _ => line,
    }
}

/// FNV-1a 64-bit — used for k-mer/duplicate hashing where a stable, simple
/// hash is enough (HLL/Bloom re-mix internally).
#[inline]
pub fn fnv1a64(data: &[u8]) -> u64 {
    let mut h = 0xcbf2_9ce4_8422_2325u64;
    for &b in data {
        h ^= u64::from(b);
        h = h.wrapping_mul(0x1000_0000_01b3);
    }
    h
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn newline_scan_matches_naive() {
        let mut buf = Vec::new();
        for i in 0..1000usize {
            buf.extend_from_slice(format!("line{i}\n").as_bytes());
        }
        let mut found = Vec::new();
        find_newlines(&buf, 0, &mut found);
        let naive: Vec<usize> = buf
            .iter()
            .enumerate()
            .filter(|(_, b)| **b == b'\n')
            .map(|(i, _)| i)
            .collect();
        assert_eq!(found, naive);
        assert_eq!(count_newlines(&buf), naive.len());
    }

    #[test]
    fn trim_cr_works() {
        assert_eq!(trim_cr(b"ACGT\r"), b"ACGT");
        assert_eq!(trim_cr(b"ACGT"), b"ACGT");
    }
}
