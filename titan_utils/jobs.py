"""In-RAM job manager for the v2 API (Layer A/B compute behind FastAPI).

Zero-Data-Retention by construction: job payloads, intermediate results and
artifacts live in process RAM only. ``MongoDB`` (or any other store) is
OPTIONAL and OFF by default — see :mod:`titan_utils.api_v2` for the
``TITAN_JOB_STORE=mongodb`` opt-in hook, which stores job *metadata* only.

Concurrency: a bounded thread pool runs job functions; progress is reported by
the compute layer via a callback; cancellation is cooperative through
:class:`titan_utils.engine.PythonCancelToken` / ``titan_core.CancelToken``.
"""
from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Optional

from titan_utils import engine as titan_engine

__all__ = ["Job", "JobManager", "JOB_TYPES", "get_job_manager"]

JOB_TYPES = ("fastq_qc", "vcf_parse", "bam_stats", "de", "variant_ml", "expression_pca")

_MAX_PARAMS_BYTES = 256 * 1024
_MAX_JOBS = 512
_MAX_ARTIFACT_BYTES = 64 * 1024 * 1024


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Job:
    job_id: str
    job_type: str
    params: dict[str, Any]
    status: str = "queued"  # queued | running | succeeded | failed | cancelled
    progress: float = 0.0
    created_utc: str = field(default_factory=_utc_now)
    started_utc: Optional[str] = None
    finished_utc: Optional[str] = None
    error: Optional[str] = None
    engine: Optional[str] = None
    engine_stats: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict, repr=False)
    cancel_token: Any = field(default=None, repr=False)
    _listeners: list = field(default_factory=list, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def summary(self) -> dict[str, Any]:
        """JSON-safe job status document (no sequence payloads)."""
        return {
            "id": self.job_id,
            "type": self.job_type,
            "status": self.status,
            "progress": round(float(self.progress), 4),
            "created_utc": self.created_utc,
            "started_utc": self.started_utc,
            "finished_utc": self.finished_utc,
            "error": self.error,
            "engine": self.engine,
            "engine_stats": self.engine_stats,
            "artifacts": sorted(self.artifacts.keys()),
            "provenance": {
                "input_sha256": self.provenance.get("input_sha256"),
                "output_sha256": self.provenance.get("output_sha256"),
                "zero_data_retention": True,
            },
        }

    def set_progress(self, value: float) -> None:
        with self._lock:
            self.progress = max(0.0, min(1.0, float(value)))
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener(self.summary())
            except Exception:
                pass

    def add_listener(self, callback: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            self._listeners.append(callback)


class JobManager:
    """Bounded, in-memory job registry + worker pool."""

    def __init__(self, max_workers: int = 4, max_jobs: int = _MAX_JOBS) -> None:
        self._jobs: dict[str, Job] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="titan-job")
        self._max_jobs = max_jobs

    def create_job(self, job_type: str, params: Mapping[str, Any]) -> Job:
        if job_type not in JOB_TYPES:
            raise ValueError(f"unknown job type '{job_type}' (allowed: {', '.join(JOB_TYPES)})")
        params_dict = dict(params or {})
        payload_size = len(repr(params_dict).encode("utf-8", "replace"))
        if payload_size > _MAX_PARAMS_BYTES:
            raise ValueError("job params exceed the size limit")
        job = Job(
            job_id=uuid.uuid4().hex,
            job_type=job_type,
            params=params_dict,
            cancel_token=titan_engine.PythonCancelToken(),
        )
        with self._lock:
            while len(self._jobs) >= self._max_jobs:
                oldest = self._order[0]
                existing = self._jobs.get(oldest)
                if existing is not None and existing.status in {"succeeded", "failed", "cancelled"}:
                    self._jobs.pop(oldest, None)
                    self._order.pop(0)
                else:
                    break
            self._jobs[job.job_id] = job
            self._order.append(job.job_id)
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            jobs = [self._jobs[jid] for jid in reversed(self._order) if jid in self._jobs]
        return [job.summary() for job in jobs[:limit]]

    def cancel_job(self, job_id: str) -> Optional[Job]:
        job = self.get_job(job_id)
        if job is None:
            return None
        job.cancel_token.cancel()
        if job.status == "queued":
            job.status = "cancelled"
            job.finished_utc = _utc_now()
        return job

    def submit(self, job: Job, runner: Callable[[Job], dict[str, Any]]) -> None:
        """Run ``runner(job)`` on the pool; artifacts land in ``job.artifacts``."""

        def _work() -> None:
            job.started_utc = _utc_now()
            job.status = "running"
            job.set_progress(0.01)
            try:
                if job.cancel_token.is_cancelled():
                    job.status = "cancelled"
                else:
                    artifacts = runner(job) or {}
                    for name, value in artifacts.items():
                        size = len(value) if isinstance(value, (bytes, bytearray, str)) else len(repr(value))
                        if size > _MAX_ARTIFACT_BYTES:
                            raise ValueError(f"artifact '{name}' exceeds the size limit")
                        job.artifacts[name] = value
                    job.status = "succeeded"
                    job.set_progress(1.0)
            except Exception as exc:  # controlled failure surfaces to the client
                job.status = "failed"
                job.error = f"{type(exc).__name__}: {exc}"[:500]
            finally:
                job.finished_utc = _utc_now()
                job.set_progress(job.progress)

        self._pool.submit(_work)

    def run_job(self, job_type: str, params: Mapping[str, Any], runner: Callable[[Job], dict[str, Any]]) -> Job:
        job = self.create_job(job_type, params)
        self.submit(job, runner)
        return job

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)


_MANAGER: Optional[JobManager] = None
_MANAGER_LOCK = threading.Lock()


def get_job_manager() -> JobManager:
    global _MANAGER
    with _MANAGER_LOCK:
        if _MANAGER is None:
            _MANAGER = JobManager()
        return _MANAGER
