"""Tests for the v2 job API + in-RAM job manager (fallback path only).

Covers: job lifecycle, artifacts, cancel, chunked upload, provenance, and the
engine status endpoint — with ``titan_core`` mocked as missing so the tests
exercise the pure-Python fallback deterministically.
"""
from __future__ import annotations

import base64
import json
import sys
import time

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from titan_utils import engine  # noqa: E402
from titan_utils.jobs import get_job_manager  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setitem(sys.modules, "titan_core", None)
    monkeypatch.setattr(engine, "_RUST", None, raising=False)
    monkeypatch.setattr(engine, "_RUST_TRIED", False, raising=False)
    monkeypatch.setattr(engine, "_POLICY", "auto")
    from titan_utils.api import app

    with TestClient(app) as test_client:
        yield test_client
    engine.refresh_engine()


def _wait(client, job_id: str, timeout: float = 30.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        doc = client.get(f"/api/v2/jobs/{job_id}").json()
        if doc["status"] in {"succeeded", "failed", "cancelled"}:
            return doc
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish in {timeout}s")


def test_v1_run_still_works(client):
    response = client.get("/api/run", params={"tool": "gc_content", "seq": "ATGCATGC"})
    assert response.status_code == 200
    body = response.json()
    assert body["result"]["gc_percent"] == 50.0
    assert response.headers.get("cache-control", "").startswith("no-store")
    assert body["provenance"]["zero_data_retention"] is True


def test_v2_fastq_qc_job_lifecycle(client):
    response = client.post(
        "/api/v2/jobs",
        json={"type": "fastq_qc", "params": {"fastq": "@r1\nACGTACGTAC\n+\nIIIIIIIIII\n"}},
    )
    assert response.status_code == 200
    job = response.json()
    assert job["type"] == "fastq_qc"
    final = _wait(client, job["id"])
    assert final["status"] == "succeeded", final
    assert final["engine"] == "python"
    assert final["provenance"]["input_sha256"]
    artifact = client.get(f"/api/v2/results/{job['id']}/qc_report.json")
    assert artifact.status_code == 200
    report = json.loads(artifact.content)
    assert report["n_reads"] == 1
    assert artifact.headers.get("cache-control", "").startswith("no-store")


def test_v2_vcf_parse_job(client):
    vcf = "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\nchr1\t100\trs1\tA\tG\t50\tPASS\tAF=0.25\n"
    response = client.post("/api/v2/jobs", json={"type": "vcf_parse", "params": {"vcf": vcf, "chrom": "chr1"}})
    job = response.json()
    final = _wait(client, job["id"])
    assert final["status"] == "succeeded", final
    csv_artifact = client.get(f"/api/v2/results/{job['id']}/variants.csv")
    assert b"CHROM" in csv_artifact.content


def test_v2_de_job(client):
    counts = "gene,s1,s2,s3,s4\ngeneA,100,120,400,420\ngeneB,200,210,50,60\n"
    meta = "sample,condition\ns1,control\ns2,control\ns3,treated\ns4,treated\n"
    response = client.post(
        "/api/v2/jobs",
        json={
            "type": "de",
            "params": {
                "counts_csv": counts,
                "metadata_csv": meta,
                "contrast": ["condition", "treated", "control"],
                "method": "fallback",
            },
        },
    )
    job = response.json()
    final = _wait(client, job["id"])
    assert final["status"] == "succeeded", final
    payload = json.loads(client.get(f"/api/v2/results/{job['id']}/de_results.json").content)
    assert payload["method"] == "fallback-ttest"
    assert payload["n_genes_tested"] == 2


def test_v2_cancel_and_retry(client):
    response = client.post(
        "/api/v2/jobs",
        json={"type": "variant_ml", "params": {"n_synthetic": 200}},
    )
    job = response.json()
    cancelled = client.post(f"/api/v2/jobs/{job['id']}/cancel").json()
    assert cancelled["id"] == job["id"]
    final = _wait(client, job["id"])
    assert final["status"] in {"cancelled", "succeeded", "failed"}
    retried = client.post(f"/api/v2/jobs/{job['id']}/retry").json()
    assert retried["id"] != job["id"]
    assert _wait(client, retried["id"])["status"] in {"succeeded", "failed", "cancelled"}


def test_v2_upload_chunks(client):
    upload_id = "testupload12345"
    part1 = base64.b64encode(b"@r1\nACGTACGTAC\n+\nIIIIIIIIII\n").decode()
    r1 = client.post(
        "/api/v2/upload/chunk",
        json={"upload_id": upload_id, "offset": 0, "data_b64": part1, "final": True, "name": "x.fastq"},
    )
    assert r1.status_code == 200
    assert r1.json()["complete"] is True
    job = client.post("/api/v2/jobs", json={"type": "fastq_qc", "params": {"upload_id": upload_id}}).json()
    final = _wait(client, job["id"])
    assert final["status"] == "succeeded", final


def test_v2_upload_rejects_bad_offset(client):
    upload_id = "badoffset000001"
    part = base64.b64encode(b"ACGT").decode()
    r1 = client.post(
        "/api/v2/upload/chunk", json={"upload_id": upload_id, "offset": 0, "data_b64": part, "final": False}
    )
    assert r1.status_code == 200
    r2 = client.post(
        "/api/v2/upload/chunk", json={"upload_id": upload_id, "offset": 99, "data_b64": part, "final": False}
    )
    assert r2.status_code == 400


def test_v2_unknown_job_404(client):
    assert client.get("/api/v2/jobs/doesnotexist").status_code == 404
    assert client.post("/api/v2/jobs/doesnotexist/cancel").status_code == 404
    assert client.get("/api/v2/results/doesnotexist/x.json").status_code == 404


def test_v2_invalid_job_type(client):
    response = client.post("/api/v2/jobs", json={"type": "mine_bitcoin", "params": {}})
    assert response.status_code == 400


def test_v2_engine_status(client):
    body = client.get("/api/v2/engine").json()
    assert body["python_fallback"] is True
    assert body["active"] == "python"
    assert "r_available" in body


def test_no_store_headers_everywhere(client):
    for url in ("/api/v2/jobs", "/api/v2/engine"):
        response = client.get(url)
        assert response.headers.get("cache-control", "").startswith("no-store"), url
