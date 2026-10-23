/**
 * Variant Explorer — TanStack Table + Virtual over VCF rows.
 *
 * Two modes, both with chrom/QUAL/AF/consequence/ClinVar filters:
 *  - **client**: Web-Worker parsing/filtering (paste, demo, local file)
 *  - **server**: server-side filter + sort + pagination via /api/v2/vcf/query
 *    (only one page crosses the wire — built for 1M-row VCFs)
 * CSV/TSV/JSON export on both modes.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { useReactTable, getCoreRowModel, flexRender, type ColumnDef } from "@tanstack/react-table";
import { useVirtualizer } from "@tanstack/react-virtual";
import { api, downloadCsv, downloadJson, downloadTsv } from "../api/client";
import { translate, type Language } from "../i18n";
import { filterVcfRows, parseVcfRows, type VcfFilters, type VcfRow } from "../workers/vcfCore";
import { Panel } from "./common";

const PAGE_SIZE = 200;

interface ServerRow {
  CHROM: string;
  POS: number;
  ID: string;
  REF: string;
  ALT: string;
  QUAL: number | null;
  FILTER: string;
  AF: number | null;
  Consequence: string | null;
  ClinVar: string | null;
}

export function VariantExplorer({
  language,
  vcfText,
  onVcfTextChange,
  demoVcf,
  uploadId,
}: {
  language: Language;
  vcfText: string;
  onVcfTextChange: (text: string) => void;
  demoVcf: string;
  uploadId?: string | null;
}) {
  const [filters, setFilters] = useState<VcfFilters>({});
  const [page, setPage] = useState(0);
  const [sourceOpen, setSourceOpen] = useState(false);
  const [mode, setMode] = useState<"client" | "server">("client");
  const [serverRows, setServerRows] = useState<ServerRow[]>([]);
  const [serverTotal, setServerTotal] = useState(0);
  const [serverFiltered, setServerFiltered] = useState(0);
  const [sort, setSort] = useState<{ by: string; desc: boolean }>({ by: "POS", desc: false });
  const [serverError, setServerError] = useState<string | null>(null);
  const parentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (mode !== "server") return;
    if (!uploadId && !vcfText) return;
    let cancelled = false;
    api
      .queryVcf({
        upload_id: uploadId || undefined,
        vcf: uploadId ? undefined : vcfText,
        filters: {
          chrom: filters.chrom,
          qual_min: filters.qualMin,
          af_min: filters.afMin,
          af_max: filters.afMax,
          consequence: filters.consequence,
          clinvar: filters.clinvar,
          search: filters.search,
        },
        sort_by: sort.by,
        sort_desc: sort.desc,
        offset: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      })
      .then((body) => {
        if (cancelled) return;
        setServerRows(body.rows as unknown as ServerRow[]);
        setServerTotal(body.total);
        setServerFiltered(body.filtered);
        setServerError(null);
      })
      .catch((error: Error) => {
        if (!cancelled) setServerError(error.message);
      });
    return () => {
      cancelled = true;
    };
  }, [mode, uploadId, vcfText, filters, sort, page]);

  const allRows = useMemo(() => (mode === "client" && vcfText ? parseVcfRows(vcfText) : []), [vcfText, mode]);
  const filtered = useMemo(
    () => (mode === "client" ? filterVcfRows(allRows, filters) : []),
    [allRows, filters, mode],
  );
  const pageRows = useMemo(() => {
    if (mode === "server") return serverRows;
    const start = page * PAGE_SIZE;
    return filtered.slice(start, start + PAGE_SIZE);
  }, [filtered, page, mode, serverRows]);

  const columns = useMemo<ColumnDef<ServerRow | VcfRow>[]>(
    () => [
      {
        accessorKey: "chrom",
        id: "chrom",
        header: "CHROM",
        cell: (info) => (info.row.original as VcfRow).chrom ?? (info.row.original as ServerRow).CHROM,
      },
      {
        id: "pos",
        header: "POS",
        cell: (info) => {
          const row = info.row.original as VcfRow & ServerRow;
          return Number(row.pos ?? row.POS).toLocaleString();
        },
      },
      {
        id: "id",
        header: "ID",
        cell: (info) => {
          const row = info.row.original as VcfRow & ServerRow;
          return row.id ?? row.ID;
        },
      },
      {
        id: "ref",
        header: "REF",
        cell: (info) => {
          const row = info.row.original as VcfRow & ServerRow;
          return row.ref ?? row.REF;
        },
      },
      {
        id: "alt",
        header: "ALT",
        cell: (info) => {
          const row = info.row.original as VcfRow & ServerRow;
          return row.alt ?? row.ALT;
        },
      },
      {
        id: "qual",
        header: "QUAL",
        cell: (info) => {
          const row = info.row.original as VcfRow & ServerRow;
          const value = (row.qual ?? row.QUAL) as number | null;
          return value === null || value === undefined ? "." : Number(value).toFixed(1);
        },
      },
      {
        id: "filter",
        header: "FILTER",
        cell: (info) => {
          const row = info.row.original as VcfRow & ServerRow;
          return row.filter ?? row.FILTER;
        },
      },
      {
        id: "af",
        header: "AF",
        cell: (info) => {
          const row = info.row.original as VcfRow & ServerRow;
          const af = row.AF ?? row.info?.AF ?? ".";
          return af === null ? "." : String(af);
        },
      },
      {
        id: "consequence",
        header: "Consequence",
        cell: (info) => {
          const row = info.row.original as VcfRow & ServerRow;
          return row.Consequence ?? row.info?.Consequence ?? row.info?.CSQ ?? ".";
        },
      },
    ],
    [],
  );

  const table = useReactTable({ data: pageRows as never[], columns, getCoreRowModel: getCoreRowModel() });
  const rowVirtualizer = useVirtualizer({
    count: table.getRowModel().rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 34,
    overscan: 12,
  });

  const chroms = useMemo(() => [...new Set(allRows.map((row) => row.chrom))].sort(), [allRows]);
  const totalRows = mode === "server" ? serverTotal : allRows.length;
  const filteredRows = mode === "server" ? serverFiltered : filtered.length;
  const totalPages = Math.max(1, Math.ceil(filteredRows / PAGE_SIZE));

  const exportRows = (): Record<string, unknown>[] => {
    const source = mode === "server" ? (serverRows as unknown as Record<string, unknown>[]) : filtered.map((row) => ({
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
    }));
    return source;
  };

  const toggleSort = (by: string) => {
    setSort((current) => ({ by, desc: current.by === by ? !current.desc : false }));
    setPage(0);
  };

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
        <div className="field">
          <label htmlFor="vf-mode">Table engine</label>
          <select
            id="vf-mode"
            value={mode}
            onChange={(event) => {
              setMode(event.target.value as "client" | "server");
              setPage(0);
            }}
          >
            <option value="client">Client (Web Worker)</option>
            <option value="server">Server-side filter/sort/page</option>
          </select>
        </div>
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

      {mode === "server" && (
        <div className="row" style={{ marginBottom: 6 }}>
          <span className="muted">Sort (server-side):</span>
          {["POS", "QUAL", "AF", "CHROM"].map((key) => (
            <button
              key={key}
              className={`action ${sort.by === key ? "" : "secondary"}`}
              aria-pressed={sort.by === key}
              onClick={() => toggleSort(key)}
            >
              {key} {sort.by === key ? (sort.desc ? "↓" : "↑") : ""}
            </button>
          ))}
        </div>
      )}

      <p className="muted">
        {filteredRows.toLocaleString()} / {totalRows.toLocaleString()} {translate("variants.rows", language)}
        {" · "}
        {mode === "server"
          ? "server-side filter · sort · pagination (one page over the wire)"
          : "Web Worker client filter + virtual scrolling"}
      </p>
      {serverError && <p className="error-text">{serverError}</p>}

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
        <button className="action secondary" onClick={() => downloadCsv("titan_variants.csv", exportRows())}>
          {translate("export.csv", language)}
        </button>
        <button className="action secondary" onClick={() => downloadTsv("titan_variants.tsv", exportRows())}>
          {translate("export.tsv", language)}
        </button>
        <button className="action secondary" onClick={() => downloadJson("titan_variants.json", exportRows())}>
          {translate("export.json", language)}
        </button>
      </div>
    </Panel>
  );
}
