//! Criterion benchmarks — run with `cargo bench --no-default-features`.
//! Numbers produced here are MEASURED on the machine that runs them;
//! `scripts/benchmark.py` records the environment next to the results and
//! never invents figures.

use criterion::{black_box, criterion_group, criterion_main, Criterion, Throughput};
use titan_core::align::{align, AlignMode, AlignParams};
use titan_core::fastq::parse_payload;
use titan_core::qc::{qc_payload, QcParams};

fn toy_fastq(n: usize, len: usize) -> Vec<u8> {
    let mut out = Vec::new();
    for i in 0..n {
        out.extend_from_slice(format!("@read{i} lane:1\n").as_bytes());
        let seq: Vec<u8> = (0..len).map(|j| b"ACGT"[(i + j) % 4]).collect();
        out.extend_from_slice(&seq);
        out.extend_from_slice(b"\n+\n");
        out.extend_from_slice(&vec![b'I'; len]);
        out.extend_from_slice(b"\n");
    }
    out
}

fn bench_fastq_parse(c: &mut Criterion) {
    let data = toy_fastq(100_000, 100);
    let mut group = c.benchmark_group("fastq_parse");
    group.throughput(Throughput::Bytes(data.len() as u64));
    group.bench_function("serial_1_thread", |b| {
        b.iter(|| parse_payload(black_box(&data), 1, None, None, None).unwrap())
    });
    group.bench_function("parallel_4_threads", |b| {
        b.iter(|| parse_payload(black_box(&data), 4, None, None, None).unwrap())
    });
    group.finish();
}

fn bench_qc(c: &mut Criterion) {
    let data = toy_fastq(50_000, 100);
    let mut group = c.benchmark_group("fastq_qc");
    group.throughput(Throughput::Bytes(data.len() as u64));
    group.bench_function("qc_4_threads", |b| {
        b.iter(|| qc_payload(black_box(&data), 4, &QcParams::default(), None, None).unwrap())
    });
    group.finish();
}

fn bench_align(c: &mut Criterion) {
    let query: Vec<u8> = (0..300usize).map(|i| b"ACGT"[i % 4]).collect();
    let target: Vec<u8> = (0..320usize).map(|i| b"ACGT"[i % 4]).collect();
    let params = AlignParams {
        mode: AlignMode::Local,
        band: 64,
        ..Default::default()
    };
    let mut group = c.benchmark_group("align_banded_sw");
    group.bench_function("local_300x320_band64", |b| {
        b.iter(|| align(black_box(&query), black_box(&target), &params).unwrap())
    });
    group.finish();
}

criterion_group!(benches, bench_fastq_parse, bench_qc, bench_align);
criterion_main!(benches);
