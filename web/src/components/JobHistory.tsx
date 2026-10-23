/** Job history (metadata only — never sequence payloads). */
import { translate, type Language } from "../i18n";
import { useJobHistory } from "../hooks/useJobs";
import { downloadJson } from "../api/client";
import { Panel, Progress, StatusBadge } from "./common";

export function JobHistory({ language }: { language: Language }) {
  const { jobs, refresh } = useJobHistory();
  return (
    <Panel
      title={translate("nav.jobs", language)}
      actions={
        <div className="row">
          <button className="action secondary" onClick={refresh}>
            Refresh
          </button>
          <button className="action secondary" onClick={() => downloadJson("titan_job_history.json", jobs)}>
            {translate("export.json", language)}
          </button>
        </div>
      }
    >
      <table className="data">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>{translate("job.status", language)}</th>
            <th>{translate("job.progress", language)}</th>
            <th>Engine</th>
            <th>Created (UTC)</th>
            <th>Input SHA-256</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td title={job.id}>{job.id.slice(0, 8)}…</td>
              <td>{job.type}</td>
              <td>
                <StatusBadge status={job.status} />
              </td>
              <td style={{ minWidth: 120 }}>
                <Progress fraction={job.progress} />
              </td>
              <td>{job.engine ?? "—"}</td>
              <td>{job.created_utc}</td>
              <td title={job.provenance?.input_sha256 ?? ""}>
                {(job.provenance?.input_sha256 ?? "").slice(0, 12) || "—"}
              </td>
            </tr>
          ))}
          {jobs.length === 0 && (
            <tr>
              <td colSpan={7} className="muted">
                No jobs yet — runs are kept in RAM and listed here while the API process lives (ZDR).
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </Panel>
  );
}
