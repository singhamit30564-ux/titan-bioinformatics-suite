"""API v2 — job-oriented endpoints for the web dashboard (Layer C).

Contract (kept stable for ``web/`` + generated OpenAPI types):

* ``POST   /api/v2/jobs``                 — create job {type, params}
* ``GET    /api/v2/jobs``                 — job history (metadata only)
* ``GET    /api/v2/jobs/{id}``            — job status summary
* ``WS     /api/v2/jobs/{id}/stream``     — live progress events (+ cancel msg)
* ``POST   /api/v2/jobs/{id}/cancel``     — cooperative cancel
* ``POST   /api/v2/jobs/{id}/retry``      — re-run with the same params
* ``GET    /api/v2/results/{id}/{artifact}`` — in-RAM artifact bytes
* ``POST   /api/v2/upload/chunk``         — chunked in-RAM upload (ZDR)
* ``GET    /api/v2/engine``               — engine status (Rust/Python/R)

Invariants preserved from v1: 60 req/min/IP in-RAM rate limit, ``no-store``
response headers, SHA-256 provenance on inputs/outputs, and **no access
logging of sequence data** (uvicorn must run with ``access_log=False``).
MongoDB job-metadata persistence is OPTIONAL and OFF by default
(``TITAN_JOB_STORE=mongodb``); raw genomic data is never persisted.
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import threading
from typing import Any, Callable, Optional

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from titan_utils import engine as titan_engine
from titan_utils.jobs import Job, get_job_manager
from titan_utils.privacy import provenance_record

MAX_UPLOAD_CHUNK_BYTES = 8 * 1024 * 1024
MAX_UPLOAD_TOTAL_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB in-RAM ceiling
MAX_PARAM_TEXT_BYTES = 64 * 1024 * 1024

_UPLOADS: dict[str, dict[str, Any]] = {}
_UPLOADS_LOCK = threading.Lock()


class JobCreateRequest(BaseModel):
    type: str = Field(min_length=1, max_length=32)
    params: dict[str, Any] = Field(default_factory=dict)


class ProvenanceSummary(BaseModel):
    input_sha256: Optional[str] = None
    output_sha256: Optional[str] = None
    zero_data_retention: bool = True


class JobSummaryModel(BaseModel):
    """JSON-safe job status document (no sequence payloads)."""

    id: str
    type: str
    status: str
    progress: float
    created_utc: str
    started_utc: Optional[str] = None
    finished_utc: Optional[str] = None
    error: Optional[str] = None
    engine: Optional[str] = None
    engine_stats: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[str] = Field(default_factory=list)
    provenance: ProvenanceSummary = Field(default_factory=ProvenanceSummary)


class JobListModel(BaseModel):
    jobs: list[JobSummaryModel]


class UploadChunkRequest(BaseModel):
    upload_id: str = Field(min_length=8, max_length=64)
    offset: int = Field(ge=0)
    data_b64: str = Field(min_length=1)
    final: bool = False
    name: str = Field(default="upload.bin", max_length=256)


class UploadChunkResponse(BaseModel):
    upload_id: str
    bytes_received: int
    complete: bool


class VcfQueryFilters(BaseModel):
    chrom: Optional[str] = None
    qual_min: Optional[float] = None
    qual_max: Optional[float] = None
    af_min: Optional[float] = None
    af_max: Optional[float] = None
    consequence: Optional[str] = None
    clinvar: Optional[str] = None
    filter: Optional[str] = None
    search: Optional[str] = Field(default=None, max_length=256)


class VcfQueryRequest(BaseModel):
    """Server-side filter + sort + pagination over a VCF payload (1M-row safe)."""

    upload_id: Optional[str] = Field(default=None, min_length=8, max_length=64)
    vcf: Optional[str] = Field(default=None, max_length=MAX_PARAM_TEXT_BYTES)
    filters: VcfQueryFilters = Field(default_factory=VcfQueryFilters)
    sort_by: str = Field(default="POS", max_length=16)
    sort_desc: bool = False
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=500)


class VcfQueryRow(BaseModel):
    CHROM: str
    POS: int
    ID: str
    REF: str
    ALT: str
    QUAL: Optional[float] = None
    FILTER: str
    AF: Optional[float] = None
    Consequence: Optional[str] = None
    ClinVar: Optional[str] = None


class VcfQueryResponse(BaseModel):
    rows: list[VcfQueryRow]
    total: int
    filtered: int
    offset: int
    limit: int
    sort_by: str
    sort_desc: bool


# ─────────────────────────────────────────────────────────────────────────────
# Job runners (each returns {artifact_name: bytes|json-serializable})
# ─────────────────────────────────────────────────────────────────────────────

def _param_text(params: dict[str, Any], key: str, default: str = "") -> str:
    value = params.get(key, default)
    if isinstance(value, str):
        if len(value.encode("utf-8", "replace")) > MAX_PARAM_TEXT_BYTES:
            raise ValueError(f"param '{key}' exceeds the size limit")
        return value
    raise ValueError(f"param '{key}' must be a string")


def _upload_bytes(params: dict[str, Any]) -> Optional[bytes]:
    """Resolve params['upload_id'] (from /api/v2/upload/chunk) to bytes."""
    upload_id = params.get("upload_id")
    if not upload_id:
        return None
    with _UPLOADS_LOCK:
        entry = _UPLOADS.get(str(upload_id))
        if entry is None:
            raise ValueError("unknown upload_id")
        return bytes(entry["buffer"])


def _job_progress(job: Job) -> Callable[[int, int], None]:
    def _cb(done: int, total: int) -> None:
        if total > 0:
            job.set_progress(min(0.99, done / total))

    return _cb


def _run_fastq_qc(job: Job) -> dict[str, Any]:
    data = _upload_bytes(job.params) or _param_text(job.params, "fastq").encode("utf-8")
    k = int(job.params.get("k", 8))
    result = titan_engine.qc_fastq(
        data=data, k=k, progress=_job_progress(job), cancel=job.cancel_token
    )
    job.engine = result.get("engine")
    job.provenance = {
        "input_sha256": provenance_record(data, kind="fastq", label="job_input", engine=job.engine or "python").digest,
        "output_sha256": provenance_record(json.dumps(result, default=str, sort_keys=True), kind="qc_report", engine=job.engine or "python").digest,
        "zero_data_retention": True,
    }
    return {"qc_report.json": json.dumps(result, default=str).encode("utf-8")}


def _run_vcf_parse(job: Job) -> dict[str, Any]:
    data = _upload_bytes(job.params) or _param_text(job.params, "vcf").encode("utf-8")
    result = titan_engine.parse_vcf(
        data=data,
        chrom=job.params.get("chrom") or None,
        pos_min=job.params.get("pos_min"),
        pos_max=job.params.get("pos_max"),
        qual_min=job.params.get("qual_min"),
        af_min=job.params.get("af_min"),
        af_max=job.params.get("af_max"),
        filter=job.params.get("filter") or None,
        max_rows=job.params.get("max_rows"),
        progress=_job_progress(job),
        cancel=job.cancel_token,
    )
    job.engine = result.get("engine")
    frame = titan_engine.vcf_result_to_dataframe(result)
    job.provenance = {
        "input_sha256": provenance_record(data, kind="vcf", label="job_input", engine=job.engine or "python").digest,
        "output_sha256": provenance_record(frame.to_csv(index=False), kind="vcf_table", engine=job.engine or "python").digest,
        "zero_data_retention": True,
    }
    return {
        "variants.csv": frame.to_csv(index=False).encode("utf-8"),
        "parse_meta.json": json.dumps(
            {k: v for k, v in result.items() if k not in {"header_lines"}}, default=str
        ).encode("utf-8"),
    }


def _run_bam_stats(job: Job) -> dict[str, Any]:
    data = _upload_bytes(job.params) or _param_text(job.params, "alignment").encode("utf-8")
    result = titan_engine.read_alignment(
        data=data,
        region=job.params.get("region") or None,
        progress=_job_progress(job),
        cancel=job.cancel_token,
    )
    job.engine = result.get("engine")
    job.provenance = {
        "input_sha256": provenance_record(data, kind="alignment", label="job_input", engine=job.engine or "python").digest,
        "output_sha256": provenance_record(json.dumps(result, default=str, sort_keys=True), kind="flagstat", engine=job.engine or "python").digest,
        "zero_data_retention": True,
    }
    return {"bam_stats.json": json.dumps(result, default=str).encode("utf-8")}


def _run_de(job: Job) -> dict[str, Any]:
    import io as _io

    import pandas as pd

    from titan_stats.de import run_differential_expression

    counts_text = _param_text(job.params, "counts_csv")
    meta_text = _param_text(job.params, "metadata_csv")
    counts = pd.read_csv(_io.StringIO(counts_text))
    counts = counts.rename(columns={counts.columns[0]: "gene"}).set_index("gene")
    meta = pd.read_csv(_io.StringIO(meta_text))
    meta = meta.rename(columns={meta.columns[0]: "sample"}).set_index("sample")
    job.set_progress(0.2)
    result = run_differential_expression(
        counts,
        meta,
        design=str(job.params.get("design", "~ condition")),
        contrast=tuple(job.params["contrast"]) if job.params.get("contrast") else ("condition", "treated", "control"),
        method=str(job.params.get("method", "auto")),
        min_count=int(job.params.get("min_count", 10)),
        seed=int(job.params.get("seed", 1337)),
    )
    job.engine = result.get("method")
    job.provenance = result.get("provenance") or {}
    job.set_progress(0.9)
    payload = {
        "method": result["method"],
        "results": result["results"].replace({float("nan"): None}).to_dict(orient="records"),
        "n_genes_tested": result["n_genes_tested"],
        "n_genes_significant_fdr05": result["n_genes_significant_fdr05"],
        "contrast": result["contrast"],
        "warnings": result["warnings"],
    }
    return {
        "de_results.json": json.dumps(payload, default=str).encode("utf-8"),
        "de_results.csv": result["results"].to_csv(index=False).encode("utf-8"),
    }


def _run_variant_ml(job: Job) -> dict[str, Any]:
    from titan_stats.ml_variants import make_synthetic_dataset, model_card, train_pathogenicity_model

    n_rows = int(job.params.get("n_synthetic", 2000))
    job.set_progress(0.1)
    features, labels = make_synthetic_dataset(n_samples=n_rows)
    model = train_pathogenicity_model(
        features, labels, model_type=str(job.params.get("model_type", "auto")), seed=int(job.params.get("seed", 20261022))
    )
    card = model_card(model)
    job.engine = f"python/{card['backend']}"
    job.provenance = {
        "input_sha256": provenance_record(f"synthetic:{n_rows}", kind="synthetic", label="synthetic_training", engine="python").digest,
        "output_sha256": provenance_record(json.dumps(card, sort_keys=True), kind="model_card", engine="python").digest,
        "zero_data_retention": True,
    }
    job.set_progress(0.9)
    return {"model_card.json": json.dumps(card, indent=2).encode("utf-8")}


def _run_expression_pca(job: Job) -> dict[str, Any]:
    import io as _io

    import pandas as pd

    from titan_stats import dimred

    matrix_text = _param_text(job.params, "matrix_csv")
    frame = pd.read_csv(_io.StringIO(matrix_text))
    frame = frame.rename(columns={frame.columns[0]: "gene"}).set_index("gene")
    job.set_progress(0.2)
    result = dimred.pca(frame, n_components=int(job.params.get("n_components", 3)), transpose=True)
    clustering = dimred.kmeans_cluster(
        frame, n_clusters=int(job.params.get("n_clusters", 2)), transpose=True
    )
    job.engine = "python/numpy"
    job.provenance = {
        "input_sha256": provenance_record(matrix_text, kind="expression", label="job_input", engine="python").digest,
        "output_sha256": provenance_record(json.dumps(result, default=str, sort_keys=True), kind="pca", engine="python").digest,
        "zero_data_retention": True,
    }
    job.set_progress(0.9)
    return {
        "pca.json": json.dumps(result, default=str).encode("utf-8"),
        "clusters.json": json.dumps(clustering, default=str).encode("utf-8"),
    }


RUNNERS: dict[str, Callable[[Job], dict[str, Any]]] = {
    "fastq_qc": _run_fastq_qc,
    "vcf_parse": _run_vcf_parse,
    "bam_stats": _run_bam_stats,
    "de": _run_de,
    "variant_ml": _run_variant_ml,
    "expression_pca": _run_expression_pca,
}


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────

def _enforce_rate_limit(request: Request) -> None:
    try:
        from titan_utils.api import RATE_LIMITER  # reuse the in-RAM limiter

        client = request.client
        client_ip = client.host if client is not None else "unknown"
        if not RATE_LIMITER.allow(f"v2:{client_ip}"):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded: 60 requests per minute per IP.",
                headers={"Retry-After": "60"},
            )
    except HTTPException:
        raise
    except Exception:
        pass  # limiter is best-effort; never block local tooling


def create_v2_router() -> APIRouter:
    router = APIRouter(prefix="/api/v2")

    @router.post("/jobs", response_model=JobSummaryModel)
    def create_job(payload: JobCreateRequest, request: Request) -> dict[str, Any]:
        _enforce_rate_limit(request)
        manager = get_job_manager()
        try:
            job = manager.create_job(payload.type, payload.params)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        manager.submit(job, RUNNERS[payload.type])
        return job.summary()

    @router.get("/jobs", response_model=JobListModel)
    def list_jobs(request: Request, limit: int = 100) -> dict[str, Any]:
        _enforce_rate_limit(request)
        return {"jobs": get_job_manager().list_jobs(limit=min(max(limit, 1), 500))}

    @router.get("/jobs/{job_id}", response_model=JobSummaryModel)
    def get_job(job_id: str, request: Request) -> dict[str, Any]:
        _enforce_rate_limit(request)
        job = get_job_manager().get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job.summary()

    @router.post("/jobs/{job_id}/cancel", response_model=JobSummaryModel)
    def cancel_job(job_id: str, request: Request) -> dict[str, Any]:
        _enforce_rate_limit(request)
        job = get_job_manager().cancel_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job.summary()

    @router.post("/jobs/{job_id}/retry", response_model=JobSummaryModel)
    def retry_job(job_id: str, request: Request) -> dict[str, Any]:
        _enforce_rate_limit(request)
        manager = get_job_manager()
        old = manager.get_job(job_id)
        if old is None:
            raise HTTPException(status_code=404, detail="job not found")
        job = manager.create_job(old.job_type, old.params)
        manager.submit(job, RUNNERS[old.job_type])
        return job.summary()

    @router.get("/results/{job_id}/{artifact}")
    def get_result(job_id: str, artifact: str, request: Request):
        _enforce_rate_limit(request)
        job = get_job_manager().get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        if artifact not in job.artifacts:
            raise HTTPException(status_code=404, detail="artifact not found")
        value = job.artifacts[artifact]
        from fastapi.responses import Response

        media_type = "application/json" if artifact.endswith(".json") else (
            "text/csv" if artifact.endswith(".csv") else "application/octet-stream"
        )
        body = value.encode("utf-8") if isinstance(value, str) else bytes(value)
        return Response(
            content=body,
            media_type=media_type,
            headers={"Cache-Control": "no-store, max-age=0", "Pragma": "no-cache"},
        )

    @router.post("/upload/chunk", response_model=UploadChunkResponse)
    def upload_chunk(payload: UploadChunkRequest, request: Request) -> dict[str, Any]:
        _enforce_rate_limit(request)
        try:
            chunk = base64.b64decode(payload.data_b64, validate=True)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="data_b64 is not valid base64") from exc
        if len(chunk) > MAX_UPLOAD_CHUNK_BYTES:
            raise HTTPException(status_code=413, detail="chunk exceeds 8 MiB")
        with _UPLOADS_LOCK:
            entry = _UPLOADS.get(payload.upload_id)
            if entry is None:
                if payload.offset != 0:
                    raise HTTPException(status_code=400, detail="unknown upload_id with non-zero offset")
                entry = {"buffer": bytearray(), "name": payload.name}
                _UPLOADS[payload.upload_id] = entry
            buffer: bytearray = entry["buffer"]
            if payload.offset != len(buffer):
                raise HTTPException(
                    status_code=400,
                    detail=f"offset mismatch: expected {len(buffer)}",
                )
            if len(buffer) + len(chunk) > MAX_UPLOAD_TOTAL_BYTES:
                raise HTTPException(status_code=413, detail="upload exceeds the 2 GiB in-RAM ceiling")
            buffer.extend(chunk)
            total = len(buffer)
            complete = bool(payload.final)
        return {"upload_id": payload.upload_id, "bytes_received": total, "complete": complete}

    @router.get("/engine")
    def engine_status(request: Request) -> dict[str, Any]:
        _enforce_rate_limit(request)
        status = titan_engine.engine_status()
        try:
            from titan_stats.r_bridge import r_available, r_versions

            status["r_available"] = r_available()
            status["r_versions"] = r_versions() if status["r_available"] else {}
        except Exception:
            status["r_available"] = False
        return status

    @router.post("/vcf/query", response_model=VcfQueryResponse)
    def vcf_query(payload: VcfQueryRequest, request: Request) -> dict[str, Any]:
        """Server-side VCF filter + sort + pagination (for 1M-row tables).

        Accepts an in-RAM ``upload_id`` (from /api/v2/upload/chunk) or inline
        ``vcf`` text. Filtering, sorting and slicing all happen on the server;
        only one page of rows crosses the wire.
        """
        _enforce_rate_limit(request)
        if not payload.upload_id and not payload.vcf:
            raise HTTPException(status_code=400, detail="provide upload_id or vcf text")
        if payload.sort_by.upper() not in {"CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "AF"}:
            raise HTTPException(status_code=400, detail=f"unsupported sort_by '{payload.sort_by}'")
        try:
            data = _upload_bytes({"upload_id": payload.upload_id}) if payload.upload_id else (payload.vcf or "").encode("utf-8")
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        try:
            parsed = titan_engine.parse_vcf(data=data)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        n_total = len(parsed["chrom"])
        rows: list[dict[str, Any]] = []
        filters = payload.filters
        for i in range(n_total):
            info_raw = parsed["info_raw"][i] or ""
            info = {}
            for entry in info_raw.split(";"):
                if "=" in entry:
                    key, value = entry.split("=", 1)
                    info[key] = value
            af = None
            if info.get("AF") not in (None, "."):
                try:
                    af = float(str(info["AF"]).split(",")[0])
                except ValueError:
                    af = None
            consequence = info.get("Consequence", info.get("CSQ", ""))
            clinvar = info.get("CLNSIG", info.get("ClinVar", ""))
            qual = parsed["qual"][i]
            row = {
                "CHROM": str(parsed["chrom"][i]),
                "POS": int(parsed["pos"][i]),
                "ID": str(parsed["id"][i]),
                "REF": str(parsed["ref"][i]),
                "ALT": str(parsed["alt"][i]),
                "QUAL": None if qual is None else float(qual),
                "FILTER": str(parsed["filter"][i]),
                "AF": af,
                "Consequence": consequence or None,
                "ClinVar": clinvar or None,
            }
            f = filters
            if f.chrom and row["CHROM"] != f.chrom:
                continue
            if f.qual_min is not None and (row["QUAL"] or 0) < f.qual_min:
                continue
            if f.qual_max is not None and (row["QUAL"] or 0) > f.qual_max:
                continue
            if f.af_min is not None and (af if af is not None else 0) < f.af_min:
                continue
            if f.af_max is not None and (af if af is not None else 1) > f.af_max:
                continue
            if f.consequence and f.consequence.lower() not in (consequence or "").lower():
                continue
            if f.clinvar and f.clinvar.lower() not in (clinvar or "").lower():
                continue
            if f.filter and f.filter.lower() not in (row["FILTER"] or "").lower():
                continue
            if f.search:
                haystack = f"{row['CHROM']}:{row['POS']} {row['ID']} {row['REF']}>{row['ALT']}".lower()
                if f.search.lower() not in haystack:
                    continue
            rows.append(row)

        sort_key = payload.sort_by.upper()

        def _sort_value(row: dict[str, Any]) -> Any:
            if sort_key == "POS":
                return row["POS"]
            if sort_key == "QUAL":
                return row["QUAL"] if row["QUAL"] is not None else -1.0
            if sort_key == "AF":
                return row["AF"] if row["AF"] is not None else -1.0
            return str(row.get(sort_key, ""))

        rows.sort(key=_sort_value, reverse=payload.sort_desc)
        page = rows[payload.offset:payload.offset + payload.limit]
        return {
            "rows": page,
            "total": n_total,
            "filtered": len(rows),
            "offset": payload.offset,
            "limit": payload.limit,
            "sort_by": sort_key,
            "sort_desc": payload.sort_desc,
        }

    @router.websocket("/jobs/{job_id}/stream")
    async def job_stream(websocket: WebSocket, job_id: str) -> None:
        # Note: the WS endpoint intentionally skips the HTTP rate limiter
        # (long-lived connection); one connection per job is cheap in RAM.
        await websocket.accept()
        job = get_job_manager().get_job(job_id)
        if job is None:
            await websocket.send_json({"event": "error", "detail": "job not found"})
            await websocket.close()
            return
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)

        def on_update(summary: dict[str, Any]) -> None:
            try:
                queue.put_nowait(summary)
            except asyncio.QueueFull:
                pass

        job.add_listener(on_update)
        try:
            await websocket.send_json({"event": "status", "job": job.summary()})
            while True:
                get_task = asyncio.ensure_future(queue.get())
                recv_task = asyncio.ensure_future(websocket.receive_text())
                done, pending = await asyncio.wait(
                    {get_task, recv_task}, return_when=asyncio.FIRST_COMPLETED, timeout=30.0
                )
                for task in pending:
                    task.cancel()
                if not done:
                    await websocket.send_json({"event": "ping", "job": job.summary()})
                    if job.status in {"succeeded", "failed", "cancelled"}:
                        await websocket.send_json({"event": "done", "job": job.summary()})
                        break
                    continue
                for task in done:
                    if task is get_task:
                        summary = task.result()
                        await websocket.send_json({"event": "progress", "job": summary})
                        if summary.get("status") in {"succeeded", "failed", "cancelled"}:
                            await websocket.send_json({"event": "done", "job": summary})
                            await websocket.close()
                            return
                    else:
                        message = task.result()
                        if message == "cancel":
                            get_job_manager().cancel_job(job_id)
                            await websocket.send_json({"event": "cancelled", "job": job.summary()})
        except WebSocketDisconnect:
            return
        except Exception:
            try:
                await websocket.close()
            except Exception:
                pass

    return router


def register_v2_routes(app: Any) -> None:
    """Mount the v2 router + CORS allow-list onto the shared FastAPI app.

    CORS origins come from ``TITAN_CORS_ORIGINS`` (comma-separated). Default
    allows the local Vite dev server and same-host dashboard deployments; the
    Express gateway proxies to the API for production single-origin setups.
    """
    raw = os.environ.get("TITAN_CORS_ORIGINS", "")
    if raw.strip():
        origins = [part.strip() for part in raw.split(",") if part.strip()]
    else:
        origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
        max_age=600,
    )
    # Append the v2 routes directly to the router's route table (the router
    # already carries the /api/v2 prefix on each path). This keeps every entry
    # in app.routes a proper route object with a .path attribute — some tests
    # introspect the route table.
    v2_router = create_v2_router()
    for route in v2_router.routes:
        app.router.routes.append(route)
