import { describe, expect, it } from "vitest";
import { filterVcfRows, parseVcfRows } from "../src/workers/vcfCore";
import { translate, LANGUAGES } from "../src/i18n";

const VCF = `##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t100\trs1\tA\tG\t50\tPASS\tAF=0.001;Consequence=frameshift_variant;CLNSIG=Pathogenic
chr1\t200\trs2\tC\tT\t5\tLowQual\tAF=0.4;Consequence=synonymous_variant;CLNSIG=Benign
chr2\t300\trs3\tG\tGA\t60\tPASS\tAF=0.02;Consequence=missense_variant
malformed line`;

describe("parseVcfRows", () => {
  it("parses data rows and skips headers/malformed lines", () => {
    const rows = parseVcfRows(VCF);
    expect(rows).toHaveLength(3);
    expect(rows[0]).toMatchObject({ chrom: "chr1", pos: 100, id: "rs1", ref: "A", alt: "G", qual: 50 });
    expect(rows[0].info.AF).toBe("0.001");
    expect(rows[2].qual).toBe(60);
  });

  it("handles empty input", () => {
    expect(parseVcfRows("")).toHaveLength(0);
    expect(parseVcfRows("##only=header\n#CHROM\tPOS")).toHaveLength(0);
  });
});

describe("filterVcfRows", () => {
  const rows = parseVcfRows(VCF);

  it("filters by chrom and QUAL", () => {
    expect(filterVcfRows(rows, { chrom: "chr2" })).toHaveLength(1);
    expect(filterVcfRows(rows, { qualMin: 40 })).toHaveLength(2);
  });

  it("filters by allele frequency range", () => {
    expect(filterVcfRows(rows, { afMax: 0.05 })).toHaveLength(2);
    expect(filterVcfRows(rows, { afMin: 0.3 })).toHaveLength(1);
  });

  it("filters by consequence and ClinVar", () => {
    expect(filterVcfRows(rows, { consequence: "frameshift" })).toHaveLength(1);
    expect(filterVcfRows(rows, { clinvar: "pathogenic" })).toHaveLength(1);
  });

  it("supports free-text search", () => {
    expect(filterVcfRows(rows, { search: "rs3" })).toHaveLength(1);
    expect(filterVcfRows(rows, { search: "chr1" })).toHaveLength(2);
  });
});

describe("i18n", () => {
  it("has both languages for every used key", () => {
    for (const key of ["app.title", "nav.jobs", "job.cancel", "export.csv", "zdr.notice"]) {
      for (const language of LANGUAGES) {
        expect(translate(key, language)).not.toBe(key);
      }
    }
  });
});
