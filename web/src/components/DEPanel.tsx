/** Differential-expression job panel (PyDESeq2 / R / fallback-ttest). */
import { useState } from "react";
import { api, downloadCsv, downloadJson, downloadTsv } from "../api/client";
import { translate, type Language } from "../i18n";
import { useJob } from "../hooks/useJobs";
import { Panel, Progress, StatusBadge } from "./common";
import { VolcanoChart } from "./Charts";

interface DeResult {
  method: string;
  results: { gene: string; baseMean: number; log2FC: number; stat: number; pvalue: number; padj: number | null }[];
  n_genes_tested: number;
  n_genes_significant_fdr05: number;
  contrast: [string, string, string];
  warnings: string[];
}

const DEFAULT_COUNTS = `gene,s1,s2,s3,s4,s5,s6
GENE_A,100,120,110,400,420,410
GENE_B,200,210,195,50,60,55
GENE_C,80,90,85,85,88,90
GENE_D,15,12,18,300,320,290
GENE_E,500,480,510,490,505,495`;

const DEFAULT_META = `sample,condition,batch
s1,control,b1
s2,control,b2
s3,control,b1
s4,treated,b2
s5,treated,b1
s6,treated,b2`;

export function DEPanel({ language }: { language: Language }) {
  const { job, error, busy, start, cancel, retry } = useJob();
  const [countsCsv, setCountsCsv] = useState(DEFAULT_COUNTS);
  const [metaCsv, setMetaCsv] = useState(DEFAULT_META);
  const [result, setResult] = useState<DeResult | null>(null);
  const [selection, setSelection] = useState<Set<string>>(new Set());

  const run = async () => {
    await start("de", {
      counts_csv: countsCsv,
      metadata_csv: metaCsv,
      design: "~ condition",
      contrast: ["condition", "treated", "control"],
      method: "auto",
    });
  };

  const loadArtifact = async () => {
    if (!job || job.status !== "succeeded") return;
    const response = await fetch(api.resultUrl(job.id, "de_results.json"), { cache: "no-store" });
    setResult((await response.json()) as DeResult);
  };

  return (
    <Panel
      title={translate("nav.de", language)}
      actions={
        <div className="row">
          <button className="action" disabled={busy} onClick={() => void run()}>
            {translate("de.run", language)}
          </button>
          {job && ["queued", "running"].includes(job.status) && (
            <button className="action danger" onClick={() => void cancel()}>
              {translate("job.cancel", language)}
            </button>
          )}
          {job && ["failed", "cancelled"].includes(job.status) && (
            <button className="action secondary" onClick={() => void retry()}>
              {translate("job.retry", language)}
            </button>
          )}
        </div>
      }
    >
      <div className="grid">
        <div>
          <label htmlFor="de-counts">Counts matrix CSV (genes × samples)</label>
          <textarea
            id="de-counts"
            rows={8}
            style={{ width: "100%" }}
            value={countsCsv}
            onChange={(event) => setCountsCsv(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="de-meta">Sample metadata CSV</label>
          <textarea
            id="de-meta"
            rows={8}
            style={{ width: "100%" }}
            value={metaCsv}
            onChange={(event) => setMetaCsv(event.target.value)}
          />
        </div>
      </div>
      {job && (
        <div className="row" style={{ margin: "10px 0" }}>
          <StatusBadge status={job.status} />
          <span className="muted">{job.engine ?? ""}</span>
          <div style={{ flex: 1, minWidth: 180 }}>
            <Progress fraction={job.progress} />
          </div>
        </div>
      )}
      {error && <p className="error-text">{error}</p>}
      {job?.status === "succeeded" && !result && (
        <button className="action secondary" onClick={() => void loadArtifact()}>
          Load DE results
        </button>
      )}
      {result && (
        <>
          <p>
            Method <span className="hl">{result.method}</span> · {result.n_genes_tested} genes tested ·{" "}
            {result.n_genes_significant_fdr05} significant (FDR 0.05) · contrast{" "}
            <span className="hl">{result.contrast.join(" / ")}</span>
          </p>
          {result.warnings.length > 0 && (
            <p className="muted">Warnings: {result.warnings.join("; ")}</p>
          )}
          <VolcanoChart
            rows={result.results.map((row) => ({
              gene: row.gene,
              log2FC: row.log2FC,
              padj: row.padj ?? 1,
            }))}
            language={language}
            selection={selection}
            onSelectionChange={setSelection}
          />
          <div className="row">
            <button
              className="action secondary"
              onClick={() => downloadCsv("titan_de_results.csv", result.results as unknown as Record<string, unknown>[])}
            >
              {translate("export.csv", language)}
            </button>
            <button
              className="action secondary"
              onClick={() => downloadTsv("titan_de_results.tsv", result.results as unknown as Record<string, unknown>[])}
            >
              {translate("export.tsv", language)}
            </button>
            <button className="action secondary" onClick={() => downloadJson("titan_de_results.json", result)}>
              {translate("export.json", language)}
            </button>
          </div>
        </>
      )}
    </Panel>
  );
}
