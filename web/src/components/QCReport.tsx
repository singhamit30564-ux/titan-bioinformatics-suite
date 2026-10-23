/** One-pass streaming FASTQ QC job + report charts (canvas histogram + SVG). */
import { useState } from "react";
import { downloadJson, api } from "../api/client";
import { translate, type Language } from "../i18n";
import { useJob } from "../hooks/useJobs";
import type { UploadResult } from "./Upload";
import { Metric, Panel, Progress, StatusBadge } from "./common";

interface QcReport {
  n_reads: number;
  total_bases: number;
  mean_read_length: number;
  gc_percent: number;
  q20_percent: number;
  q30_percent: number;
  per_base_mean_quality: number[];
  top_kmers: { kmer: string; count: number; percent: number }[];
  adapter_hits: { adapter: string; count: number }[];
  duplicate_estimate_percent: number;
  phred_encoding: string;
  engine: string;
}

export function QCReport({ language, upload }: { language: Language; upload: UploadResult | null }) {
  const { job, error, busy, start, cancel, retry } = useJob();
  const [report, setReport] = useState<QcReport | null>(null);

  const run = async () => {
    if (!upload) return;
    await start("fastq_qc", { upload_id: upload.uploadId });
  };

  const loadArtifact = async () => {
    if (!job || job.status !== "succeeded") return;
    const response = await fetch(api.resultUrl(job.id, "qc_report.json"), { cache: "no-store" });
    setReport((await response.json()) as QcReport);
  };

  return (
    <Panel
      title={translate("nav.qc", language)}
      actions={
        <div className="row">
          <button className="action" disabled={!upload || busy} onClick={() => void run()}>
            {translate("qc.run", language)}
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
      {job && (
        <div className="row" style={{ marginBottom: 10 }}>
          <StatusBadge status={job.status} />
          <span className="muted">{job.engine ?? ""}</span>
          <span className="muted">{(job.progress * 100).toFixed(0)}%</span>
          <div style={{ flex: 1, minWidth: 180 }}>
            <Progress fraction={job.progress} />
          </div>
        </div>
      )}
      {error && <p className="error-text">{error}</p>}
      {job?.status === "succeeded" && !report && (
        <button className="action secondary" onClick={() => void loadArtifact()}>
          Load report
        </button>
      )}
      {report && (
        <>
          <div className="grid">
            <Metric label="Reads" value={report.n_reads.toLocaleString()} />
            <Metric label="Bases" value={report.total_bases.toLocaleString()} />
            <Metric label="Mean length" value={`${report.mean_read_length.toFixed(1)} bp`} />
            <Metric label="GC %" value={`${report.gc_percent.toFixed(2)}%`} />
            <Metric label="Q20 %" value={`${report.q20_percent.toFixed(2)}%`} />
            <Metric label="Q30 %" value={`${report.q30_percent.toFixed(2)}%`} />
            <Metric label="Dup (est.) %" value={`${report.duplicate_estimate_percent.toFixed(2)}%`} />
            <Metric label="Phred" value={report.phred_encoding} />
          </div>
          <h3>Per-base mean quality</h3>
          <PerBaseQualitySvg values={report.per_base_mean_quality} />
          <h3>Top k-mers</h3>
          <table className="data">
            <thead>
              <tr>
                <th>k-mer</th>
                <th>Count</th>
                <th>%</th>
              </tr>
            </thead>
            <tbody>
              {report.top_kmers.map((row) => (
                <tr key={row.kmer}>
                  <td>{row.kmer}</td>
                  <td>{row.count}</td>
                  <td>{row.percent.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="row" style={{ marginTop: 10 }}>
            <button className="action secondary" onClick={() => downloadJson("titan_qc_report.json", report)}>
              {translate("export.json", language)}
            </button>
          </div>
        </>
      )}
    </Panel>
  );
}

export function PerBaseQualitySvg({ values }: { values: number[] }) {
  const width = 720;
  const height = 220;
  const pad = 30;
  const maxQ = Math.max(40, ...values);
  const points = values
    .map((value, index) => {
      const x = pad + (index / Math.max(1, values.length - 1)) * (width - 2 * pad);
      const y = height - pad - (value / maxQ) * (height - 2 * pad);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Per-base mean quality"
      style={{ width: "100%", background: "#0d1320", borderRadius: 8 }}
    >
      {[10, 20, 30, 40].map((q) => {
        const y = height - pad - (q / maxQ) * (height - 2 * pad);
        return (
          <g key={q}>
            <line x1={pad} x2={width - pad} y1={y} y2={y} stroke="#2a3142" strokeDasharray="4 4" />
            <text x={4} y={y + 4} fill="#9aa4b2" fontSize="10">
              Q{q}
            </text>
          </g>
        );
      })}
      <polyline points={points} fill="none" stroke="#d4af37" strokeWidth="2.5" />
    </svg>
  );
}
