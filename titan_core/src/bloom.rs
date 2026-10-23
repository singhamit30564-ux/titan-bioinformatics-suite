//! Streaming Bloom filter — used for duplication detection and distinct-kmer
//! sketches. Fixed-size bit vector, double hashing (Kirsch-Mitzenmacher).

use std::f64::consts::LN_2;

#[derive(Debug, Clone)]
pub struct BloomFilter {
    bits: Vec<u64>,
    n_bits: u64,
    n_hashes: u32,
    n_inserted: u64,
}

impl BloomFilter {
    /// Build a filter for `expected` items at the requested false-positive rate.
    pub fn with_capacity(expected: usize, fp_rate: f64) -> Self {
        let expected = expected.max(1) as f64;
        let fp_rate = fp_rate.clamp(1e-9, 0.5);
        // m = -n * ln(p) / (ln 2)^2
        let n_bits = ((-expected * fp_rate.ln()) / (LN_2 * LN_2))
            .ceil()
            .max(64.0) as u64;
        let n_words = (n_bits.div_ceil(64)) as usize;
        let n_hashes = (((n_bits as f64) / expected) * LN_2)
            .ceil()
            .clamp(1.0, 16.0) as u32;
        BloomFilter {
            bits: vec![0u64; n_words],
            n_bits: n_words as u64 * 64,
            n_hashes,
            n_inserted: 0,
        }
    }

    #[inline]
    fn positions(&self, key: u64) -> impl Iterator<Item = u64> + '_ {
        let h1 = key.wrapping_mul(0x9e37_79b9_7f4a_7c15);
        let h2 = key.rotate_left(31).wrapping_mul(0xc2b2_ae3d_27d4_eb4f) | 1;
        let n_bits = self.n_bits;
        let n_hashes = self.n_hashes;
        (0..n_hashes).map(move |i| h1.wrapping_add((i as u64).wrapping_mul(h2)) % n_bits)
    }

    /// Returns true when the key was newly inserted, false if already present
    /// (probabilistically — bounded by the configured false-positive rate).
    pub fn insert_if_absent(&mut self, key: u64) -> bool {
        let mut already_present = true;
        let positions: Vec<u64> = self.positions(key).collect();
        for pos in positions {
            let word = (pos / 64) as usize;
            let mask = 1u64 << (pos % 64);
            if self.bits[word] & mask == 0 {
                self.bits[word] |= mask;
                already_present = false;
            }
        }
        if !already_present {
            self.n_inserted += 1;
        }
        !already_present
    }

    pub fn contains(&self, key: u64) -> bool {
        self.positions(key).all(|pos| {
            let word = (pos / 64) as usize;
            self.bits[word] & (1u64 << (pos % 64)) != 0
        })
    }

    /// Bit-wise union — used when merging per-block sketches. Requires equal
    /// sizing; shorter filters are zero-extended.
    pub fn merge_or(&mut self, other: &BloomFilter) {
        if self.bits.len() < other.bits.len() {
            self.bits.resize(other.bits.len(), 0);
        }
        for (dst, src) in self.bits.iter_mut().zip(other.bits.iter()) {
            *dst |= *src;
        }
    }

    pub fn len(&self) -> u64 {
        self.n_inserted
    }

    pub fn is_empty(&self) -> bool {
        self.n_inserted == 0
    }
}

impl Default for BloomFilter {
    fn default() -> Self {
        BloomFilter::with_capacity(1024, 0.01)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn insert_reports_duplicates() {
        let mut bf = BloomFilter::with_capacity(1000, 0.01);
        assert!(bf.insert_if_absent(42));
        assert!(!bf.insert_if_absent(42));
        assert!(bf.contains(42));
        assert!(!bf.contains(43));
        assert_eq!(bf.len(), 1);
    }

    #[test]
    fn false_positive_rate_is_bounded() {
        let mut bf = BloomFilter::with_capacity(2000, 0.01);
        for key in 0..2000u64 {
            bf.insert_if_absent(key);
        }
        let mut fp = 0;
        for key in 100_000..110_000u64 {
            if bf.contains(key) {
                fp += 1;
            }
        }
        assert!(fp < 300, "false-positive rate too high: {fp}/10000");
    }
}
