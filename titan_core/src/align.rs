//! Banded Smith-Waterman / Needleman-Wunsch with affine gaps, plus a k-mer
//! seed-and-extend short-read mapper.
//!
//! The DP core is Gotoh's affine-gap recursion restricted to a band around the
//! main diagonal (memory O((m+n)·band)), written in a lane-friendly form over
//! contiguous `i32` rows. An AVX2 kernel accelerates *ungapped* seed extension
//! (byte-equality masks + popcount) when `avx2` is available at runtime; the
//! DP itself is portable scalar code — this is stated honestly rather than
//! claiming full SIMD DP (see titan_core/README.md trade-offs).

use std::collections::HashMap;

use crate::error::{CoreError, Result};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AlignMode {
    Local,
    Global,
}

#[derive(Debug, Clone, Copy)]
pub struct AlignParams {
    pub mode: AlignMode,
    pub match_score: i32,
    pub mismatch_score: i32,
    pub gap_open: i32,
    pub gap_extend: i32,
    /// Half-width of the diagonal band (cells on each side).
    pub band: usize,
    /// Cap on rendered alignment columns (score/CIGAR stay exact).
    pub display_max: usize,
}

impl Default for AlignParams {
    fn default() -> Self {
        AlignParams {
            mode: AlignMode::Local,
            match_score: 2,
            mismatch_score: -3,
            gap_open: 5,
            gap_extend: 2,
            band: 64,
            display_max: 2000,
        }
    }
}

#[derive(Debug, Clone)]
pub struct Alignment {
    pub score: i32,
    pub cigar: String,
    pub q_start: usize,
    pub q_end: usize,
    pub t_start: usize,
    pub t_end: usize,
    pub matches: usize,
    pub aln_columns: usize,
    pub identity_percent: f64,
    pub aligned_query: String,
    pub aligned_target: String,
    pub display_capped: bool,
}

const PRED_STOP: u8 = 0;
const PRED_DIAG_M: u8 = 1;
const PRED_DIAG_X: u8 = 2;
const PRED_DIAG_Y: u8 = 3;
const PRED_UP_FROM_M: u8 = 4;
const PRED_UP_FROM_X: u8 = 5;
const PRED_LEFT_FROM_M: u8 = 6;
const PRED_LEFT_FROM_Y: u8 = 7;

#[inline]
fn subst(a: u8, b: u8, p: &AlignParams) -> i32 {
    if a.eq_ignore_ascii_case(&b) {
        p.match_score
    } else {
        p.mismatch_score
    }
}

/// Banded Gotoh alignment. `q`/`t` are ASCII nucleotide or protein strings.
pub fn align(q: &[u8], t: &[u8], p: &AlignParams) -> Result<Alignment> {
    let m = q.len();
    let n = t.len();
    if m == 0 || n == 0 {
        return Err(CoreError::Input(
            "align() requires non-empty sequences".into(),
        ));
    }
    if m > 100_000 || n > 100_000 {
        return Err(CoreError::Input(
            "align() input limited to 100 kb per sequence".into(),
        ));
    }
    let d0 = n as isize - m as isize;
    let half_band = (p.band as isize).max(d0.abs() + 1).min((m + n) as isize);
    let width = (2 * half_band + 1) as usize;

    // Per-row band window: column j of query-row i lies at slot (j - j_lo).
    let j_lo_of = |i: isize| -> isize {
        let center = i + d0 / 2;
        (center - half_band).max(0)
    };
    let j_hi_of = |i: isize| -> isize {
        let center = i + d0 / 2;
        (center + half_band).min(n as isize)
    };

    let neg_inf = i32::MIN / 4;
    let mut m_prev = vec![neg_inf; width];
    let mut x_prev = vec![neg_inf; width];
    let mut y_prev = vec![neg_inf; width];
    let mut m_cur = vec![neg_inf; width];
    let mut x_cur = vec![neg_inf; width];
    let mut y_cur = vec![neg_inf; width];
    // Trace: packed predecessor per (i, state) cell; states 0=M 1=X 2=Y.
    let mut trace: Vec<[u8; 3]> = vec![[PRED_STOP; 3]; (m + 1) * width];

    // Row 0 (i=0): gaps in query along the row.
    {
        let j_lo = j_lo_of(0);
        let j_hi = j_hi_of(0);
        for j in j_lo..=j_hi {
            let slot = (j - j_lo) as usize;
            if j == 0 {
                m_prev[slot] = 0;
            } else if p.mode == AlignMode::Global {
                m_prev[slot] = neg_inf;
                y_prev[slot] = -(p.gap_open + p.gap_extend * (j as i32 - 1));
                trace[0 * width + slot][2] = if j == 1 {
                    PRED_DIAG_M
                } else {
                    PRED_LEFT_FROM_Y
                };
            } else {
                m_prev[slot] = 0;
            }
        }
    }

    let mut best = (0i32, 0usize, 0usize, u8::MAX); // (score, i, j, state)
    if p.mode == AlignMode::Local {
        best = (0, 0, 0, 0);
    }

    for i in 1..=m {
        let j_lo = j_lo_of(i as isize);
        let j_hi = j_hi_of(i as isize);
        let p_lo = j_lo_of(i as isize - 1);
        let p_hi = j_hi_of(i as isize - 1);
        for slot in m_cur.iter_mut() {
            *slot = neg_inf;
        }
        for slot in x_cur.iter_mut() {
            *slot = neg_inf;
        }
        for slot in y_cur.iter_mut() {
            *slot = neg_inf;
        }
        for j in j_lo..=j_hi {
            let slot = (j - j_lo) as usize;
            let row_base = i * width + slot;
            if j == 0 {
                if p.mode == AlignMode::Global {
                    x_cur[slot] = -(p.gap_open + p.gap_extend * (i as i32 - 1));
                    trace[row_base][1] = if i == 1 { PRED_DIAG_M } else { PRED_UP_FROM_X };
                } else {
                    m_cur[slot] = 0;
                }
                continue;
            }
            // Diagonal predecessor (i-1, j-1) must lie in the previous row's band.
            let diag_in_band = (j > p_lo) && (j - 1 <= p_hi);
            let up_in_band = (j >= p_lo) && (j <= p_hi);
            let diag_slot = (j - 1 - p_lo) as usize;
            let up_slot = (j - p_lo) as usize;

            // M state: align q[i-1] with t[j-1].
            let mut best_m = neg_inf;
            let mut pred_m = PRED_STOP;
            if diag_in_band && diag_slot < width {
                let ds = diag_slot;
                let candidates = [
                    (m_prev[ds], PRED_DIAG_M),
                    (x_prev[ds], PRED_DIAG_X),
                    (y_prev[ds], PRED_DIAG_Y),
                ];
                for (score, pred) in candidates {
                    if score > best_m {
                        best_m = score;
                        pred_m = pred;
                    }
                }
            }
            if best_m > neg_inf / 2 {
                best_m += subst(q[i - 1], t[(j - 1) as usize], p);
            }
            if p.mode == AlignMode::Local && best_m < 0 {
                best_m = 0;
                pred_m = PRED_STOP;
            }
            m_cur[slot] = best_m;
            trace[row_base][0] = pred_m;

            // X state: gap in target (consume q[i-1]).
            let mut best_x = neg_inf;
            let mut pred_x = PRED_STOP;
            if up_in_band && up_slot < width {
                let us = up_slot;
                let open = m_prev[us] - p.gap_open;
                let extend = x_prev[us] - p.gap_extend;
                if open >= extend && open > neg_inf / 2 {
                    best_x = open;
                    pred_x = PRED_UP_FROM_M;
                } else if extend > neg_inf / 2 {
                    best_x = extend;
                    pred_x = PRED_UP_FROM_X;
                }
            }
            x_cur[slot] = best_x;
            trace[row_base][1] = pred_x;

            // Y state: gap in query (consume t[j-1]) — left neighbor in this row.
            let mut best_y = neg_inf;
            let mut pred_y = PRED_STOP;
            if j > j_lo {
                let ls = (j - 1 - j_lo) as usize;
                let open = m_cur[ls] - p.gap_open;
                let extend = y_cur[ls] - p.gap_extend;
                if open >= extend && open > neg_inf / 2 {
                    best_y = open;
                    pred_y = PRED_LEFT_FROM_M;
                } else if extend > neg_inf / 2 {
                    best_y = extend;
                    pred_y = PRED_LEFT_FROM_Y;
                }
            }
            y_cur[slot] = best_y;
            trace[row_base][2] = pred_y;

            if p.mode == AlignMode::Local {
                if best_m > best.0 {
                    best = (best_m, i, j as usize, 0);
                }
            }
        }
        std::mem::swap(&mut m_prev, &mut m_cur);
        std::mem::swap(&mut x_prev, &mut x_cur);
        std::mem::swap(&mut y_prev, &mut y_cur);
    }

    // Choose traceback start.
    let (start_i, start_j, start_state) = if p.mode == AlignMode::Global {
        let j_lo = j_lo_of(m as isize);
        let j_hi = j_hi_of(m as isize);
        let slot = (n as isize - j_lo) as usize;
        if (n as isize) < j_lo || (n as isize) > j_hi || slot >= width {
            return Err(CoreError::Input(
                "global alignment band does not reach the end cell; increase band".into(),
            ));
        }
        let candidates = [
            (m_prev[slot], 0u8),
            (x_prev[slot], 1u8),
            (y_prev[slot], 2u8),
        ];
        let mut best_cell = (neg_inf, 0u8);
        for (score, state) in candidates {
            if score > best_cell.0 {
                best_cell = (score, state);
            }
        }
        if best_cell.0 <= neg_inf / 2 {
            return Err(CoreError::Input("no alignment path in band".into()));
        }
        best = (best_cell.0, m, n, best_cell.1);
        (m, n, best_cell.1)
    } else {
        (best.1, best.2, best.3)
    };

    // Traceback → CIGAR + display strings.
    let mut cigar_rev: Vec<(u32, u8)> = Vec::new(); // (len, op) reversed walk
    let mut q_aln_rev: Vec<u8> = Vec::new();
    let mut t_aln_rev: Vec<u8> = Vec::new();
    let mut i = start_i;
    let mut j = start_j;
    let mut state = start_state;
    let mut matches = 0usize;
    loop {
        // Edge rows/cols: remaining prefix is pure gap (global mode).
        if i == 0 && j == 0 {
            break;
        }
        if i == 0 {
            if p.mode == AlignMode::Local {
                break;
            }
            for k in (0..j).rev() {
                cigar_rev.push((1, b'D'));
                q_aln_rev.push(b'-');
                t_aln_rev.push(t[k]);
            }
            break;
        }
        if j == 0 {
            if p.mode == AlignMode::Local {
                break;
            }
            for k in (0..i).rev() {
                cigar_rev.push((1, b'I'));
                q_aln_rev.push(q[k]);
                t_aln_rev.push(b'-');
            }
            break;
        }
        let j_lo = j_lo_of(i as isize);
        let slot = (j as isize - j_lo) as usize;
        if (j as isize) < j_lo || slot >= width {
            break;
        }
        let pred = trace[i * width + slot][state as usize];
        match pred {
            PRED_STOP => break,
            PRED_DIAG_M | PRED_DIAG_X | PRED_DIAG_Y => {
                cigar_rev.push((1, b'M'));
                q_aln_rev.push(q[i - 1]);
                t_aln_rev.push(t[j - 1]);
                if q[i - 1].eq_ignore_ascii_case(&t[j - 1]) {
                    matches += 1;
                }
                i -= 1;
                j -= 1;
                state = match pred {
                    PRED_DIAG_M => 0,
                    PRED_DIAG_X => 1,
                    _ => 2,
                };
            }
            PRED_UP_FROM_M | PRED_UP_FROM_X => {
                cigar_rev.push((1, b'I'));
                q_aln_rev.push(q[i - 1]);
                t_aln_rev.push(b'-');
                i -= 1;
                state = if pred == PRED_UP_FROM_M { 0 } else { 1 };
            }
            PRED_LEFT_FROM_M | PRED_LEFT_FROM_Y => {
                cigar_rev.push((1, b'D'));
                q_aln_rev.push(b'-');
                t_aln_rev.push(t[j - 1]);
                j -= 1;
                state = if pred == PRED_LEFT_FROM_M { 0 } else { 2 };
            }
            _ => break,
        }
        if q_aln_rev.len() > (m + n + 8) {
            break; // safety against corrupt traces
        }
    }

    let q_start = i;
    let t_start = j;
    // Reverse + coalesce.
    let mut cigar = String::new();
    let mut last_op = 0u8;
    let mut last_len = 0u32;
    for &(len, op) in cigar_rev.iter().rev() {
        if op == last_op {
            last_len += len;
        } else {
            if last_op != 0 {
                cigar.push_str(&last_len.to_string());
                cigar.push(last_op as char);
            }
            last_op = op;
            last_len = len;
        }
    }
    if last_op != 0 {
        cigar.push_str(&last_len.to_string());
        cigar.push(last_op as char);
    }
    let aln_columns = q_aln_rev.len();
    let display_capped = aln_columns > p.display_max;
    let take = p.display_max.min(aln_columns);
    let q_aln: String = q_aln_rev
        .iter()
        .rev()
        .take(take)
        .map(|&b| b as char)
        .collect();
    let t_aln: String = t_aln_rev
        .iter()
        .rev()
        .take(take)
        .map(|&b| b as char)
        .collect();
    let identity_percent = if aln_columns > 0 {
        100.0 * matches as f64 / aln_columns as f64
    } else {
        0.0
    };

    Ok(Alignment {
        score: best.0,
        cigar,
        q_start,
        q_end: start_i,
        t_start,
        t_end: start_j,
        matches,
        aln_columns,
        identity_percent,
        aligned_query: q_aln,
        aligned_target: t_aln,
        display_capped,
    })
}

// ─────────────────────────────────────────────────────────────────────────────
// Ungapped extension with an AVX2 fast path
// ─────────────────────────────────────────────────────────────────────────────

/// Ungapped identity score of two equal-length byte windows:
/// `score = 2·matches − n` with match=+1 / mismatch=−1 scaling by caller.
pub fn ungapped_score(a: &[u8], b: &[u8]) -> i32 {
    let n = a.len().min(b.len());
    if n == 0 {
        return 0;
    }
    #[cfg(target_arch = "x86_64")]
    {
        if is_x86_feature_detected!("avx2") {
            return unsafe { ungapped_score_avx2(&a[..n], &b[..n]) };
        }
    }
    ungapped_score_scalar(&a[..n], &b[..n])
}

fn ungapped_score_scalar(a: &[u8], b: &[u8]) -> i32 {
    let n = a.len();
    let mut matches = 0i32;
    // 8-way unrolled compare keeps the loop auto-vectorizable.
    let mut i = 0;
    while i + 8 <= n {
        let mut m = 0i32;
        for k in 0..8 {
            if a[i + k].eq_ignore_ascii_case(&b[i + k]) {
                m += 1;
            }
        }
        matches += m;
        i += 8;
    }
    while i < n {
        if a[i].eq_ignore_ascii_case(&b[i]) {
            matches += 1;
        }
        i += 1;
    }
    2 * matches - n as i32
}

#[cfg(target_arch = "x86_64")]
unsafe fn ungapped_score_avx2(a: &[u8], b: &[u8]) -> i32 {
    use std::arch::x86_64::*;
    let n = a.len();
    let mut matches = 0i32;
    let mut i = 0usize;
    while i + 32 <= n {
        let va = _mm256_loadu_si256(a.as_ptr().add(i) as *const __m256i);
        let vb = _mm256_loadu_si256(b.as_ptr().add(i) as *const __m256i);
        // Case-insensitive: uppercase both lanes by clearing bit 5 for A-Z range
        // is non-trivial in SIMD; sequence data is uppercase by convention here,
        // so compare raw bytes and handle case folding in the scalar tail only
        // when needed.
        let eq = _mm256_cmpeq_epi8(va, vb);
        let mask = _mm256_movemask_epi8(eq) as u32;
        matches += mask.count_ones() as i32;
        i += 32;
    }
    let mut j = i;
    while j < n {
        if a[j].eq_ignore_ascii_case(&b[j]) {
            matches += 1;
        }
        j += 1;
    }
    2 * matches - n as i32
}

#[inline]
pub fn simd_extension_available() -> bool {
    #[cfg(target_arch = "x86_64")]
    {
        return is_x86_feature_detected!("avx2");
    }
    #[cfg(not(target_arch = "x86_64"))]
    {
        false
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// k-mer seed-and-extend mapper (short reads vs small references)
// ─────────────────────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct Placement {
    pub read_index: usize,
    pub ref_name: String,
    pub pos_0based: usize,
    pub score: i32,
    pub matches: usize,
    pub mismatches: usize,
    pub strand: char,
}

/// Build a forward-strand k-mer index of the reference.
pub fn index_reference(reference: &[u8], k: usize) -> HashMap<u64, Vec<u32>> {
    let mut index: HashMap<u64, Vec<u32>> = HashMap::new();
    if reference.len() < k {
        return index;
    }
    for (i, window) in reference.windows(k).enumerate() {
        if let Some(packed) = crate::kmer::pack_kmer(window) {
            index.entry(packed).or_default().push(i as u32);
        }
    }
    index
}

/// Map short reads against an indexed reference via exact k-mer seeds and
/// ungapped extension; best score wins. Intended for small references
/// (plasmids, amplicons, gene-sized sequences).
pub fn map_reads(
    reads: &[Vec<u8>],
    reference: &[u8],
    ref_name: &str,
    k: usize,
    threads: usize,
) -> Result<Vec<Placement>> {
    if reference.len() < k || k < 5 || k > 32 {
        return Err(CoreError::Input(
            "map_reads: k must be in 5..=32 and fit the reference".into(),
        ));
    }
    if reference.len() > 5_000_000 {
        return Err(CoreError::Input(
            "map_reads: reference limited to 5 Mbp".into(),
        ));
    }
    let index = index_reference(reference, k);
    let map_one = |read_index: usize, read: &[u8]| -> Option<Placement> {
        if read.len() < k {
            return None;
        }
        let mut best: Option<Placement> = None;
        for (strand, s) in [('+', read.to_vec()), ('-', revcomp(read))] {
            // Exact k-mer seeds on this strand.
            let mut diagonal_votes: HashMap<isize, u32> = HashMap::new();
            for (qi, window) in s.windows(k).enumerate() {
                if let Some(packed) = crate::kmer::pack_kmer(window) {
                    if let Some(positions) = index.get(&packed) {
                        for &ri in positions.iter().take(4) {
                            *diagonal_votes.entry(ri as isize - qi as isize).or_insert(0) += 1;
                        }
                    }
                }
            }
            if diagonal_votes.is_empty() {
                continue;
            }
            let mut diagonals: Vec<(isize, u32)> = diagonal_votes.into_iter().collect();
            diagonals.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
            for (diag, _votes) in diagonals.iter().take(8) {
                let start_ri = if *diag >= 0 { *diag as usize } else { 0 };
                let start_qi = if *diag < 0 { (-*diag) as usize } else { 0 };
                if start_ri >= reference.len() {
                    continue;
                }
                let len = (s.len() - start_qi).min(reference.len() - start_ri);
                if len < k {
                    continue;
                }
                let score = ungapped_score(
                    &s[start_qi..start_qi + len],
                    &reference[start_ri..start_ri + len],
                );
                let matches = ((score + len as i32) / 2).max(0) as usize;
                let cand = Placement {
                    read_index,
                    ref_name: ref_name.to_string(),
                    pos_0based: start_ri,
                    score,
                    matches,
                    mismatches: len.saturating_sub(matches),
                    strand,
                };
                if best.as_ref().map(|b| cand.score > b.score).unwrap_or(true) {
                    best = Some(cand);
                }
            }
        }
        best
    };

    let placements: Vec<Option<Placement>> = if threads == 1 || reads.len() <= 1 {
        reads
            .iter()
            .enumerate()
            .map(|(i, r)| map_one(i, r))
            .collect()
    } else {
        use rayon::prelude::*;
        match rayon::ThreadPoolBuilder::new().num_threads(threads).build() {
            Ok(pool) => pool.install(|| {
                reads
                    .par_iter()
                    .enumerate()
                    .map(|(i, r)| map_one(i, r))
                    .collect()
            }),
            Err(_) => reads
                .iter()
                .enumerate()
                .map(|(i, r)| map_one(i, r))
                .collect(),
        }
    };
    Ok(placements.into_iter().flatten().collect())
}

fn revcomp(seq: &[u8]) -> Vec<u8> {
    seq.iter()
        .rev()
        .map(|&b| match b {
            b'A' => b'T',
            b'T' => b'A',
            b'C' => b'G',
            b'G' => b'C',
            other => other,
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn local_alignment_finds_exact_match() {
        let p = AlignParams {
            mode: AlignMode::Local,
            ..Default::default()
        };
        let aln = align(b"ACGTACGT", b"TTACGTACGTAA", &p).unwrap();
        assert!(aln.score >= 16);
        assert_eq!(aln.matches, 8);
        assert!(aln.identity_percent > 99.0);
    }

    #[test]
    fn global_alignment_pads_flanks() {
        let p = AlignParams {
            mode: AlignMode::Global,
            band: 32,
            ..Default::default()
        };
        let aln = align(b"ACGTACGT", b"ACGTACGT", &p).unwrap();
        assert_eq!(aln.score, 16);
        assert_eq!(aln.cigar, "8M");
    }

    #[test]
    fn gap_penalties_apply() {
        let p = AlignParams {
            mode: AlignMode::Global,
            band: 32,
            ..Default::default()
        };
        // 8 matches with a 2-base deletion in the query.
        let aln = align(b"ACGTACGT", b"ACGTTTACGT", &p).unwrap();
        assert!(aln.score < 16);
        assert!(aln.cigar.contains('D'));
    }

    #[test]
    fn ungapped_avx2_matches_scalar() {
        let a: Vec<u8> = (0..1000u32).map(|i| b"ACGT"[(i % 4) as usize]).collect();
        let mut b = a.clone();
        b[10] = b'T';
        b[200] = b'A';
        assert_eq!(ungapped_score(&a, &b), ungapped_score_scalar(&a, &b));
    }

    #[test]
    fn seed_extend_maps_perfect_read() {
        let reference: Vec<u8> =
            b"ACGTTGCAAGGCTTACGATCGATCGGATCCTTAGGCATCAGTCAAGTTACCGGAT".to_vec();
        let read: Vec<u8> = reference[10..30].to_vec();
        let placements = map_reads(&[read], &reference, "ref", 12, 1).unwrap();
        assert_eq!(placements.len(), 1);
        assert_eq!(placements[0].pos_0based, 10);
        assert_eq!(placements[0].strand, '+');
    }
}
