//! Alignment kernel benchmarks (criterion). See fastq_bench.rs for parse/QC.

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use titan_core::align::{map_reads, ungapped_score, AlignMode, AlignParams};

fn bench_ungapped(c: &mut Criterion) {
    let a: Vec<u8> = (0..4096usize).map(|i| b"ACGT"[i % 4]).collect();
    let mut b = a.clone();
    b[17] = b'N';
    c.bench_function("ungapped_score_4kb", |ben| {
        ben.iter(|| ungapped_score(black_box(&a), black_box(&b)))
    });
}

fn bench_global(c: &mut Criterion) {
    let query: Vec<u8> = (0..200usize).map(|i| b"ACGT"[(i * 3) % 4]).collect();
    let target: Vec<u8> = (0..220usize).map(|i| b"ACGT"[(i * 3) % 4]).collect();
    let params = AlignParams {
        mode: AlignMode::Global,
        band: 32,
        ..Default::default()
    };
    c.bench_function("global_200x220_band32", |ben| {
        ben.iter(|| {
            titan_core::align::align(black_box(&query), black_box(&target), &params).unwrap()
        })
    });
}

fn bench_map_reads(c: &mut Criterion) {
    let reference: Vec<u8> = (0..50_000usize).map(|i| b"ACGT"[(i * 7) % 4]).collect();
    let reads: Vec<Vec<u8>> = (0..100)
        .map(|i| reference[i * 40..i * 40 + 100].to_vec())
        .collect();
    c.bench_function("map_100_reads_vs_50kb_ref", |ben| {
        ben.iter(|| map_reads(black_box(&reads), black_box(&reference), "ref", 12, 4).unwrap())
    });
}

criterion_group!(benches, bench_ungapped, bench_global, bench_map_reads);
criterion_main!(benches);
