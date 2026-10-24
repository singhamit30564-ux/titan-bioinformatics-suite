/**
 * Typed API client for the Titan FastAPI v2 job API.
 *
 * All requests are same-origin (`/api/v2/...`): the Vite dev server and the
 * Express gateway proxy to FastAPI, so browser code never hardcodes localhost
 * and sequence data is only held in RAM (Zero Data Retention).
 *
 * The OpenAPI-derived type surface lives in `schema.d.ts` (generated with
 * `npm run openapi:types` from web/openapi.json).
 */
import type { components } from "./schema";

export type JobSummary = components["schemas"]["JobSummaryModel"];
export type EngineStatus = Record<string, unknown> & {
  active: string;
  python_fallback: boolean;
  rust_version?: string | null;
  threads?: number;
  r_available?: boolean;
};

export class ApiError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

export const api = {
  createJob(type: string, params: Record<string, unknown>): Promise<JobSummary> {
    return request<JobSummary>("/api/v2/jobs", {
      method: "POST",
      body: JSON.stringify({ type, params }),
    });
  },
  /** Server-side VCF filter + sort + pagination (one page crosses the wire). */
  queryVcf(body: {
    upload_id?: string;
    vcf?: string;
    filters?: Record<string, string | number | undefined>;
    sort_by?: string;
    sort_desc?: boolean;
    offset?: number;
    limit?: number;
  }): Promise<{
    rows: Record<string, unknown>[];
    total: number;
    filtered: number;
    offset: number;
    limit: number;
    sort_by: string;
    sort_desc: boolean;
  }> {
    return request("/api/v2/vcf/query", { method: "POST", body: JSON.stringify(body) });
  },
  listJobs(limit = 100): Promise<{ jobs: JobSummary[] }> {
    return request<{ jobs: JobSummary[] }>(`/api/v2/jobs?limit=${limit}`);
  },
  getJob(id: string): Promise<JobSummary> {
    return request<JobSummary>(`/api/v2/jobs/${id}`);
  },
  cancelJob(id: string): Promise<JobSummary> {
    return request<JobSummary>(`/api/v2/jobs/${id}/cancel`, { method: "POST" });
  },
  retryJob(id: string): Promise<JobSummary> {
    return request<JobSummary>(`/api/v2/jobs/${id}/retry`, { method: "POST" });
  },
  engine(): Promise<EngineStatus> {
    return request<EngineStatus>("/api/v2/engine");
  },
  resultUrl(id: string, artifact: string): string {
    return `/api/v2/results/${id}/${encodeURIComponent(artifact)}`;
  },

  /**
   * Chunked in-RAM upload: 8 MiB base64 chunks with strict offset
   * bookkeeping. Returns the server upload_id to pass as a job param.
   */
  async uploadFile(
    file: File,
    options: { chunkBytes?: number; onProgress?: (fraction: number) => void; signal?: AbortSignal } = {},
  ): Promise<string> {
    const chunkBytes = options.chunkBytes ?? 8 * 1024 * 1024;
    const uploadId = `up-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    let offset = 0;
    for (;;) {
      const slice = file.slice(offset, offset + chunkBytes);
      const buffer = await slice.arrayBuffer();
      const chunk = new Uint8Array(buffer);
      offset += chunk.byteLength;
      const final = offset >= file.size;
      const dataB64 = bytesToBase64(chunk);
      const result = await request<{ upload_id: string; bytes_received: number; complete: boolean }>(
        "/api/v2/upload/chunk",
        {
          method: "POST",
          body: JSON.stringify({
            upload_id: uploadId,
            offset: offset - chunk.byteLength,
            data_b64: dataB64,
            final,
            name: file.name.slice(0, 256),
          }),
          signal: options.signal,
        },
      );
      options.onProgress?.(Math.min(1, result.bytes_received / Math.max(1, file.size)));
      if (result.complete) return uploadId;
    }
  },
};

/** Live job progress over WebSocket (falls back to polling on failure). */
export function streamJob(
  id: string,
  onEvent: (event: { event: string; job?: JobSummary }) => void,
  onError?: (error: Error) => void,
): { close: () => void } {
  const scheme = window.location.protocol === "https:" ? "wss" : "ws";
  let socket: WebSocket | null = null;
  let pollTimer: number | null = null;
  let closed = false;

  const startPolling = () => {
    if (closed) return;
    pollTimer = window.setInterval(async () => {
      try {
        const job = await api.getJob(id);
        onEvent({ event: "progress", job });
        if (["succeeded", "failed", "cancelled"].includes(job.status)) {
          onEvent({ event: "done", job });
          stop();
        }
      } catch (error) {
        onError?.(error as Error);
      }
    }, 1200);
  };

  try {
    socket = new WebSocket(`${scheme}://${window.location.host}/api/v2/jobs/${id}/stream`);
    socket.onmessage = (message) => {
      try {
        onEvent(JSON.parse(String(message.data)) as { event: string; job?: JobSummary });
      } catch (error) {
        onError?.(error as Error);
      }
    };
    socket.onerror = () => {
      socket?.close();
      startPolling();
    };
    socket.onclose = () => {
      if (!closed && pollTimer === null) startPolling();
    };
  } catch {
    startPolling();
  }

  const stop = () => {
    closed = true;
    if (pollTimer !== null) window.clearInterval(pollTimer);
    socket?.close();
  };
  return { close: stop };
}

export function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const step = 0x8000;
  for (let i = 0; i < bytes.length; i += step) {
    binary += String.fromCharCode(...bytes.subarray(i, i + step));
  }
  return btoa(binary);
}

export function downloadBlob(filename: string, blob: Blob): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function downloadJson(filename: string, data: unknown): void {
  downloadBlob(filename, new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
}

export function downloadCsv(filename: string, rows: Record<string, unknown>[]): void {
  downloadDelimited(filename, rows, ",");
}

export function downloadTsv(filename: string, rows: Record<string, unknown>[]): void {
  downloadDelimited(filename, rows, "\t");
}

function downloadDelimited(filename: string, rows: Record<string, unknown>[], separator: string): void {
  if (rows.length === 0) {
    downloadBlob(filename, new Blob([""], { type: "text/plain" }));
    return;
  }
  const columns = Object.keys(rows[0]);
  const escape = (value: unknown) => {
    const text = value === null || value === undefined ? "" : String(value);
    return text.includes(separator) || /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
  };
  const body = [columns.join(separator), ...rows.map((row) => columns.map((c) => escape(row[c])).join(separator))].join("\n");
  downloadBlob(filename, new Blob([body], { type: "text/plain" }));
}
