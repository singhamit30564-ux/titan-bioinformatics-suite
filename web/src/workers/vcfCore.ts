/**
 * Web Worker: VCF row parsing + filtering so 1M-row tables never jank the UI.
 * Messages in: { vcfText, filters, search }  →  out: { rows, total, filtered }.
 */
export interface VcfRow {
  chrom: string;
  pos: number;
  id: string;
  ref: string;
  alt: string;
  qual: number | null;
  filter: string;
  info: Record<string, string>;
}

export interface VcfFilters {
  chrom?: string;
  qualMin?: number;
  afMin?: number;
  afMax?: number;
  consequence?: string;
  clinvar?: string;
  search?: string;
}

export function parseVcfRows(vcfText: string): VcfRow[] {
  const rows: VcfRow[] = [];
  for (const line of vcfText.split("\n")) {
    if (!line || line.startsWith("#")) continue;
    const fields = line.split("\t");
    if (fields.length < 8) continue;
    const info: Record<string, string> = {};
    for (const entry of fields[7].split(";")) {
      const eq = entry.indexOf("=");
      if (eq > 0) info[entry.slice(0, eq)] = entry.slice(eq + 1);
      else if (entry) info[entry] = "1";
    }
    rows.push({
      chrom: fields[0],
      pos: Number(fields[1]),
      id: fields[2],
      ref: fields[3],
      alt: fields[4],
      qual: fields[5] === "." ? null : Number(fields[5]),
      filter: fields[6],
      info,
    });
  }
  return rows;
}

export function filterVcfRows(rows: VcfRow[], filters: VcfFilters): VcfRow[] {
  const search = filters.search?.toLowerCase();
  return rows.filter((row) => {
    if (filters.chrom && row.chrom !== filters.chrom) return false;
    if (filters.qualMin !== undefined && (row.qual ?? 0) < filters.qualMin) return false;
    const af = row.info.AF !== undefined ? Number(String(row.info.AF).split(",")[0]) : undefined;
    if (filters.afMin !== undefined && (af ?? 0) < filters.afMin) return false;
    if (filters.afMax !== undefined && (af ?? 1) > filters.afMax) return false;
    if (filters.consequence && !(row.info.Consequence ?? row.info.CSQ ?? "").includes(filters.consequence)) return false;
    if (filters.clinvar && !(row.info.CLNSIG ?? row.info.ClinVar ?? "").toLowerCase().includes(filters.clinvar.toLowerCase())) {
      return false;
    }
    if (search) {
      const haystack = `${row.chrom}:${row.pos} ${row.id} ${row.ref}>${row.alt}`.toLowerCase();
      if (!haystack.includes(search)) return false;
    }
    return true;
  });
}
