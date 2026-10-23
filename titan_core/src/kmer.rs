//! Canonical 2-bit packed k-mer counting with a bounded hash map.
//!
//! k ≤ 32 fits a `u64` (2 bits/base). Counting is canonical: each k-mer is
//! stored as `min(fwd, revcomp)` so strand orientation does not split counts.
//! The map is bounded (`max_entries`) — when full, only already-present k-mers
//! keep accumulating, which keeps RAM flat on huge inputs; `truncated` reports
//! that state honestly.

use std::collections::HashMap;

use rayon::prelude::*;

use crate::util::fnv1a64;

#[derive(Debug, Clone, Default)]
pub struct KmerCounter {
    k: usize,
    max_entries: usize,
    counts: HashMap<u64, u64>,
    total: u64,
    distinct_skipped: u64,
}

/// Pack up to 32 bases into 2-bit form (A=0, C=1, G=2, T=3; anything else →
/// returns None so the window is skipped).
pub fn pack_kmer(seq: &[u8]) -> Option<u64> {
    if seq.len() > 32 {
        return None;
    }
    let mut packed = 0u64;
    for &b in seq {
        let bits = match b {
            b'A' | b'a' => 0u64,
            b'C' | b'c' => 1u64,
            b'G' | b'g' => 2u64,
            b'T' | b't' => 3u64,
            _ => return None,
        };
        packed = (packed << 2) | bits;
    }
    Some(packed)
}

/// Reverse complement of a 2-bit packed k-mer of length `k`.
pub fn revcomp_packed(packed: u64, k: usize) -> u64 {
    let mut out = 0u64;
    for i in 0..k {
        let bits = (packed >> (2 * i)) & 0b11;
        out = (out << 2) | (3 - bits);
    }
    out
}

#[inline]
pub fn canonical(packed: u64, k: usize) -> u64 {
    let rc = revcomp_packed(packed, k);
    packed.min(rc)
}

/// Unpack a 2-bit k-mer back to ACGT bytes.
pub fn unpack_kmer(packed: u64, k: usize) -> String {
    let mut out = Vec::with_capacity(k);
    for i in (0..k).rev() {
        let bits = (packed >> (2 * i)) & 0b11;
        out.push(b"ACGT"[bits as usize]);
    }
    String::from_utf8(out).unwrap_or_default()
}

impl KmerCounter {
    pub fn new(k: usize, max_entries: usize) -> Self {
        KmerCounter {
            k: k.clamp(1, 32),
            max_entries: max_entries.max(1),
            counts: HashMap::new(),
            total: 0,
            distinct_skipped: 0,
        }
    }

    pub fn k(&self) -> usize {
        self.k
    }

    pub fn total(&self) -> u64 {
        self.total
    }

    /// True when the bounded map has dropped (or would immediately drop) any
    /// distinct k-mer: either a key was skipped at the bound, or the map is
    /// full, so estimates are truncated from here on.
    pub fn truncated(&self) -> bool {
        self.distinct_skipped > 0 || self.counts.len() >= self.max_entries
    }

    pub fn unique(&self) -> u64 {
        self.counts.len() as u64
    }

    pub fn add_sequence(&mut self, seq: &[u8]) {
        let k = self.k;
        if seq.len() < k {
            return;
        }
        for window in seq.windows(k) {
            if let Some(packed) = pack_kmer(window) {
                self.add_packed(canonical(packed, k));
            }
        }
    }

    pub fn add_packed(&mut self, key: u64) {
        self.total += 1;
        match self.counts.get_mut(&key) {
            Some(count) => *count += 1,
            None => {
                if self.counts.len() < self.max_entries {
                    self.counts.insert(key, 1);
                } else {
                    self.distinct_skipped += 1;
                }
            }
        }
    }

    pub fn merge(&mut self, other: &KmerCounter) {
        self.total += other.total;
        self.distinct_skipped += other.distinct_skipped;
        for (&key, &count) in &other.counts {
            match self.counts.get_mut(&key) {
                Some(c) => *c += count,
                None => {
                    if self.counts.len() < self.max_entries {
                        self.counts.insert(key, count);
                    } else {
                        self.distinct_skipped += 1;
                    }
                }
            }
        }
    }

    /// Top-N by count (ties broken on the unpacked k-mer for determinism).
    pub fn top(&self, n: usize) -> Vec<(String, u64)> {
        let mut ranked: Vec<(String, u64)> = self
            .counts
            .iter()
            .map(|(&key, &count)| (unpack_kmer(key, self.k), count))
            .collect();
        ranked.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
        ranked.truncate(n);
        ranked
    }

    /// Distinct count estimate via an HLL sketch of counted keys (exact when
    /// the map did not truncate).
    pub fn distinct_estimate(&self) -> f64 {
        if !self.truncated() {
            return self.counts.len() as f64;
        }
        let mut hll = crate::hll::HyperLogLog::new();
        for &key in self.counts.keys() {
            hll.add(fnv1a64(&key.to_le_bytes()));
        }
        hll.estimate()
    }
}

/// Parallel k-mer counting over whole sequence payloads (multi-FASTA blocks
/// split on record boundaries by the caller).
pub fn count_sequences(
    sequences: &[Vec<u8>],
    k: usize,
    max_entries: usize,
    threads: usize,
) -> KmerCounter {
    let merged = if threads == 1 || sequences.len() <= 1 {
        let mut acc = KmerCounter::new(k, max_entries);
        for seq in sequences {
            acc.add_sequence(seq);
        }
        acc
    } else {
        let pool = rayon::ThreadPoolBuilder::new().num_threads(threads).build();
        match pool {
            Ok(pool) => pool.install(|| {
                let parts: Vec<KmerCounter> = sequences
                    .par_iter()
                    .map(|seq| {
                        let mut part = KmerCounter::new(k, max_entries);
                        part.add_sequence(seq);
                        part
                    })
                    .collect();
                let mut acc = KmerCounter::new(k, max_entries);
                for part in &parts {
                    acc.merge(part);
                }
                acc
            }),
            Err(_) => {
                let mut acc = KmerCounter::new(k, max_entries);
                for seq in sequences {
                    acc.add_sequence(seq);
                }
                acc
            }
        }
    };
    merged
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pack_unpack_roundtrip() {
        let packed = pack_kmer(b"ACGTACGT").unwrap();
        assert_eq!(unpack_kmer(packed, 8), "ACGTACGT");
    }

    #[test]
    fn canonical_is_strand_symmetric() {
        let fwd = pack_kmer(b"ACGTACGT").unwrap();
        let rev = pack_kmer(
            b"ACGTACGT"
                .iter()
                .rev()
                .map(|&b| match b {
                    b'A' => b'T',
                    b'T' => b'A',
                    b'C' => b'G',
                    _ => b'C',
                })
                .collect::<Vec<u8>>()
                .as_slice(),
        )
        .unwrap();
        assert_eq!(canonical(fwd, 8), canonical(rev, 8));
    }

    #[test]
    fn counts_kmers() {
        let mut counter = KmerCounter::new(2, 1000);
        counter.add_sequence(b"ACGT");
        // windows: AC CA GT → canonical: AC, AC(CT->AG? no: CT rc = AG), GT rc=AC
        assert_eq!(counter.total(), 3);
        assert!(counter.unique() >= 2);
    }

    #[test]
    fn bounded_map_sets_truncated_flag() {
        let mut counter = KmerCounter::new(3, 4);
        counter.add_sequence(b"AAAACCCCGGGGTTTT");
        assert!(counter.truncated());
    }

    #[test]
    fn invalid_bases_are_skipped() {
        assert!(pack_kmer(b"ACNT").is_none());
    }
}
