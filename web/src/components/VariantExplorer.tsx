/**
 * Variant Explorer — TanStack Table + Virtual over worker-filtered VCF rows,
 * with chrom/QUAL/AF/consequence/ClinVar filters and CSV/JSON export.
 */
import { useMemo, useRef, useState } from "react";
import { useReactTable, getCoreRowModel, flexRender, type ColumnDef } from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { downloadCsv, downloadJson } from "../api/client";
import { translate, type Language } from "../i18n";
import { filterVcfRows, parseVcfRows, type VcfFilters, type VcfRow } from "../workers/vcfCore";
import { Panel } from "./common";

const PAGE_SIZE = 200;

export function VariantExplorer({
  language,
  vcfText,
  onVcfTextChange,
  demoVcf,
}: {
  language: Language;
  vcfText: string;
  onVcfTextChange: (text: string) => void;
  demoVcf: string;
}) {
  const [filters, setFilters] = useState<VcfFilters>({});
  const [page, setPage] = useState(0);
  const [sourceOpen, setSourceOpen] = useState(false);
  const parentRef = useRef<HTMLDivElement>(null);

  const allRows = useMemo(() => (vcfText ? parseVcfRows(vcfText) : []), [vcfText]);
  const filtered = useMemo(() => filterVcfRows(allRows, filters), [allRows, filters]);
  const pageRows = useMemo(() => {
    const start = page * PAGE_SIZE;
    return filtered.slice(start, start + PAGE_SIZE);
  }, [filtered, page]);

  const columns = useMemo<ColumnDef<VcfRow>[]>(
    () => [
      { accessorKey: "chrom", header: "CHROM" },
      { accessorKey: "pos", header: "POS", cell: (info) => Number(info.getValue()).toLocaleString() },
      { accessorKey: "id", header: "ID" },
      { accessorKey: "ref", header: "REF" },
      { accessorKey: "alt", header: "ALT" },
      {
        accessorKey: "qual",
        header: "QUAL",
        cell: (info) => {
          const value = info.getValue() as number | null;
          return value === null ? "." : value.toFixed(1);
        },
      },
      { accessorKey: "filter", header: "FILTER" },
      {
        id: "af",
        header: "AF",
        cell: (info) => info.row.original.info.AF ?? ".",
      },
      {
        id: "consequence",
        header: "Consequence",
        cell: (info) => info.row.original.info.Consequence ?? info.row.original.info.CSQ ?? ".",
      },
    ],
    [],
  );

  const table = useReactTable({ data: pageRows, columns, getCoreRowModel: getCoreRowModel() });
  const rowVirtualizer = useVirtualizer({
    count: table.getRowModel().rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 34,
    overscan: 12,
  });

  const chroms = useMemo(() => [...new Set(allRows.map((row) => row.chrom))].sort(), [allRows]);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

  return (
    <Panel title={translate("nav.variants", language)}>
      <div className="row" style={{ marginBottom: 8 }}>
        <button className="action secondary" onClick={() => setSourceOpen((open) => !open)} aria-expanded={sourceOpen}>
          VCF source
        </button>
        <button className="action secondary" onClick={() => onVcfTextChange(demoVcf)}>
          Load demo VCF
        </button>
        <label className="action secondary" style={{ cursor: "pointer" }}>
          Open .vcf file
          <input
            type="file"
            accept=".vcf,.txt,text/plain"
            style={{ display: "none" }}
            onChange={async (event) => {
              const file = event.target.files?.item(0);
              if (file) onVcfTextChange(await file.text());
            }}
          />
        </label>
      </div>
      {sourceOpen && (
        <textarea
          aria-label="Paste VCF"
          rows={6}
          style={{ width: "100%", marginBottom: 10 }}
          value={vcfText}
          onChange={(event) => onVcfTextChange(event.target.value)}
        />
      )}
      <div className="row">
        <div className="field">
          <label htmlFor="vf-chrom">CHROM</label>
          <select
            id="vf-chrom"
            value={filters.chrom ?? ""}
            onChange={(event) => {
              setFilters({ ...filters, chrom: event.target.value || undefined });
              setPage(0);
            }}
          >
            <option value="">all</option>
            {chroms.map((chrom) => (
              <option key={chrom} value={chrom}>
                {chrom}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="vf-qual">QUAL ≥</label>
          <input
            id="vf-qual"
            type="number"
            value={filters.qualMin ?? ""}
            onChange={(event) => {
              setFilters({ ...filters, qualMin: event.target.value === "" ? undefined : Number(event.target.value) });
              setPage(0);
            }}
          />
        </div>
        <div className="field">
          <label htmlFor="vf-afmin">AF min</label>
          <input
            id="vf-afmin"
            type="number"
            step="0.01"
            value={filters.afMin ?? ""}
            onChange={(event) => {
              setFilters({ ...filters, afMin: event.target.value === "" ? undefined : Number(event.target.value) });
              setPage(0);
            }}
          />
        </div>
        <div className="field">
          <label htmlFor="vf-afmax">AF max</label>
          <input
            id="vf-afmax"
            type="number"
            step="0.01"
            value={filters.afMax ?? ""}
            onChange={(event) => {
              setFilters({ ...filters, afMax: event.target.value === "" ? undefined : Number(event.target.value) });
              setPage(0);
            }}
          />
        </div>
        <div className="field">
          <label htmlFor="vf-cons">Consequence</label>
          <input
            id="vf-cons"
            type="text"
            placeholder="frameshift…"
            value={filters.consequence ?? ""}
            onChange={(event) => {
              setFilters({ ...filters, consequence: event.target.value || undefined });
              setPage(0);
            }}
          />
        </div>
        <div className="field">
          <label htmlFor="vf-clin">ClinVar</label>
          <input
            id="vf-clin"
            type="text"
            placeholder="Pathogenic…"
            value={filters.clinvar ?? ""}
            onChange={(event) => {
              setFilters({ ...filters, clinvar: event.target.value || undefined });
              setPage(0);
            }}
          />
        </div>
        <div className="field" style={{ flex: 1 }}>
          <label htmlFor="vf-search">{translate("variants.search", language)}</label>
          <input
            id="vf-search"
            type="search"
            style={{ width: "100%" }}
            value={filters.search ?? ""}
            onChange={(event) => {
              setFilters({ ...filters, search: event.target.value || undefined });
              setPage(0);
            }}
          />
        </div>
      </div>

      <p className="muted">
        {filtered.length.toLocaleString()} / {allRows.length.toLocaleString()} {translate("variants.rows", language)}
        {" · "}server-side job filter + client-side worker filter
      </p>

      <div ref={parentRef} className="virtual-wrap" role="region" aria-label="variant table" tabIndex={0}>
        <table className="data virtual-table">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} colSpan={header.colSpan}>
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {rowVirtualizer.getVirtualItems().map((virtualRow) => {
              const row = table.getRowModel().rows[virtualRow.index];
              if (!row) return null;
              return (
                <tr key={row.id} style={{ position: "absolute", transform: `translateY(${virtualRow.start}px)` }}>
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="row" style={{ marginTop: 10 }}>
        <button className="action secondary" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>
          ‹ Prev
        </button>
        <span className="muted">
          Page {page + 1} / {totalPages}
        </span>
        <button
          className="action secondary"
          disabled={page + 1 >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
        >
          Next ›
        </button>
        <button
          className="action secondary"
          onClick={() =>
            downloadCsv(
              "titan_variants.csv",
              filtered.map((row) => ({
                CHROM: row.chrom,
                POS: row.pos,
                ID: row.id,
                REF: row.ref,
                ALT: row.alt,
                QUAL: row.qual,
                FILTER: row.filter,
                INFO: Object.entries(row.info)
                  .map(([k, v]) => `${k}=${v}`)
                  .join(";"),
              })),
            )
          }
        >
          {translate("export.csv", language)}
        </button>
        <button className="action secondary" onClick={() => downloadJson("titan_variants.json", filtered)}>
          {translate("export.json", language)}
        </button>
      </div>
    </Panel>
  );
}
