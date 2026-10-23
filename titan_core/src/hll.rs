//! Dense HyperLogLog estimator (14-bit precision, 16384 registers).
//!
//! Used for streaming distinct-count estimates (read duplication, distinct
//! k-mers) where keeping every key would blow RAM on 50M-read inputs.
//! Estimator: standard HLL raw estimate with linear counting for the small
//! range and large-range correction omitted (64-bit hashes make it unnecessary
//! for our cardinality scales).

pub const HLL_PRECISION: u32 = 14;
const N_REGISTERS: usize = 1 << HLL_PRECISION;

#[derive(Debug, Clone)]
pub struct HyperLogLog {
    registers: Box<[u8; N_REGISTERS]>,
    filled: u64,
}

#[inline]
fn hash64(value: u64) -> u64 {
    // SplitMix64 finalizer — strong avalanche for already-mixed keys.
    let mut z = value.wrapping_add(0x9e37_79b9_7f4a_7c15);
    z = (z ^ (z >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    z ^ (z >> 31)
}

impl Default for HyperLogLog {
    fn default() -> Self {
        Self::new()
    }
}

impl HyperLogLog {
    pub fn new() -> Self {
        HyperLogLog {
            registers: Box::new([0u8; N_REGISTERS]),
            filled: 0,
        }
    }

    pub fn add(&mut self, value: u64) {
        let h = hash64(value);
        let idx = (h >> (64 - HLL_PRECISION)) as usize;
        let w = h << HLL_PRECISION;
        // rank = leading-zero count of w plus one; w == 0 -> rank = 64-precision+1.
        let rank = if w == 0 {
            (64 - HLL_PRECISION + 1) as u8
        } else {
            (w.leading_zeros() + 1).min(255) as u8
        };
        if rank > self.registers[idx] {
            self.registers[idx] = rank;
            self.filled += 1;
        }
    }

    pub fn merge(&mut self, other: &HyperLogLog) {
        for (dst, src) in self.registers.iter_mut().zip(other.registers.iter()) {
            if *src > *dst {
                *dst = *src;
            }
        }
        self.filled = self.registers.iter().filter(|&&r| r > 0).count() as u64;
    }

    /// Estimated distinct count (float — never claim exactness).
    pub fn estimate(&self) -> f64 {
        let m = N_REGISTERS as f64;
        let alpha = 0.7213 / (1.0 + 1.079 / m);
        let mut sum = 0.0f64;
        let mut zeros = 0u32;
        for &r in self.registers.iter() {
            sum += 2f64.powi(-(r as i32));
            if r == 0 {
                zeros += 1;
            }
        }
        let raw = alpha * m * m / sum;
        if raw <= 2.5 * m && zeros > 0 {
            // Small-range correction: linear counting.
            return m * (m / zeros as f64).ln();
        }
        raw
    }

    pub fn is_empty(&self) -> bool {
        self.filled == 0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn estimates_cardinality_within_tolerance() {
        let mut hll = HyperLogLog::new();
        for key in 0..50_000u64 {
            hll.add(key);
        }
        let est = hll.estimate();
        assert!(
            (est - 50_000.0).abs() / 50_000.0 < 0.1,
            "estimate {est} too far from 50000"
        );
    }

    #[test]
    fn empty_is_zero() {
        let hll = HyperLogLog::new();
        assert!(hll.is_empty());
    }

    #[test]
    fn merge_union() {
        let mut a = HyperLogLog::new();
        let mut b = HyperLogLog::new();
        for key in 0..10_000u64 {
            a.add(key);
        }
        for key in 5_000..15_000u64 {
            b.add(key);
        }
        a.merge(&b);
        let est = a.estimate();
        assert!(
            (est - 15_000.0).abs() / 15_000.0 < 0.15,
            "merged estimate {est}"
        );
    }
}
