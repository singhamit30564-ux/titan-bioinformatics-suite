/** Shared job-management hook: create, stream progress, cancel, retry. */
import { useCallback, useEffect, useRef, useState } from "react";
import { api, streamJob, type JobSummary } from "../api/client";

export interface JobHandle {
  job: JobSummary | null;
  error: string | null;
  busy: boolean;
  start: (type: string, params: Record<string, unknown>) => Promise<void>;
  cancel: () => Promise<void>;
  retry: () => Promise<void>;
}

export function useJob(): JobHandle {
  const [job, setJob] = useState<JobSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const streamRef = useRef<{ close: () => void } | null>(null);

  useEffect(() => () => streamRef.current?.close(), []);

  const attach = useCallback((summary: JobSummary) => {
    setJob(summary);
    streamRef.current?.close();
    streamRef.current = streamJob(summary.id, (event) => {
      if (event.job) setJob({ ...event.job });
    }, (streamError) => setError(streamError.message));
  }, []);

  const start = useCallback(
    async (type: string, params: Record<string, unknown>) => {
      setError(null);
      setBusy(true);
      try {
        const summary = await api.createJob(type, params);
        attach(summary);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setBusy(false);
      }
    },
    [attach],
  );

  const cancel = useCallback(async () => {
    if (!job) return;
    try {
      const summary = await api.cancelJob(job.id);
      setJob(summary);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [job]);

  const retry = useCallback(async () => {
    if (!job) return;
    setBusy(true);
    try {
      const summary = await api.retryJob(job.id);
      attach(summary);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }, [job, attach]);

  return { job, error, busy, start, cancel, retry };
}

export function useEngineStatus(): Record<string, unknown> | null {
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    api
      .engine()
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);
  return status;
}

export function useJobHistory(): { jobs: JobSummary[]; refresh: () => void } {
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const refresh = useCallback(() => {
    api
      .listJobs(200)
      .then((body) => setJobs(body.jobs))
      .catch(() => setJobs([]));
  }, []);
  useEffect(refresh, [refresh]);
  return { jobs, refresh };
}
