//! Parser fuzzing with proptest: random-ish FASTQ/VCF payloads must never
//! panic — they either parse or return a counted warning / error.
//!
//! Run: `cargo test --no-default-features --test fuzz_parsers`

use proptest::prelude::*;
use titan_core::fastq::{parse_payload, parse_records_owned, ParseWarnings};
use titan_core::vcf::{parse_vcf_payload, VcfFilter};

proptest! {
    #![proptest_config(ProptestConfig::with_cases(256))]

    #[test]
    fn fastq_random_bytes_never_panic(data in proptest::collection::vec(any::<u8>(), 0..4096)) {
        let _ = parse_payload(&data, 2, None, None, None);
    }

    #[test]
    fn fastq_malformed_records_never_panic(
        chunks in proptest::collection::vec(("[^\n]{0,40}\n").prop_map(|s| s), 0..120),
    ) {
        let data: Vec<u8> = chunks.concat().into_bytes();
        let mut warnings = ParseWarnings::default();
        let owned = parse_records_owned(&data, &mut warnings);
        // Whatever the structure, the parser must not panic and must not emit
        // a record whose seq/qual lengths disagree.
        for (_name, seq, qual) in &owned {
            prop_assert_eq!(seq.len(), qual.len());
        }
    }

    #[test]
    fn vcf_random_bytes_never_panic(data in proptest::collection::vec(any::<u8>(), 0..2048)) {
        let _ = parse_vcf_payload(&data, 2, &VcfFilter::default(), None, None, None);
    }

    #[test]
    fn vcf_random_rows_respect_max_rows(
        rows in proptest::collection::vec(
            "[a-z0-9]{1,5}\\t[1-9][0-9]{0,6}\\t.\\t[ACGT]{1,5}\\t[ACGT]{1,5}\\t[0-9]{1,3}\\t(PASS|.)\\t[^\n]*\n",
            0..60,
        ),
        limit in 0u64..20,
    ) {
        let mut data = b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n".to_vec();
        for row in &rows {
            data.extend_from_slice(row.as_bytes());
        }
        let table = parse_vcf_payload(&data, 1, &VcfFilter::default(), Some(limit), None, None).unwrap();
        prop_assert!(table.n_rows_kept <= limit.max(1) || limit == 0);
    }
}
