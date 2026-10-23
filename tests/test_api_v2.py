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


def test_v2_vcf_query_server_side_filter_sort_pagination(client):
    lines = ["##fileformat=VCFv4.2", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO"]
    for i in range(1, 21):
        af = 0.001 * i
        lines.append(f"chr{i % 3}\t{i * 10}\trs{i}\tA\tG\t{i}\tPASS\tAF={af};Consequence=missense_variant;CLNSIG=Pathogenic")
    vcf = "\n".join(lines) + "\n"

    # server-side pagination: page 1 and page 2 are disjoint
    p1 = client.post(
        "/api/v2/vcf/query",
        json={"vcf": vcf, "sort_by": "POS", "offset": 0, "limit": 5},
    ).json()
    p2 = client.post(
        "/api/v2/vcf/query",
        json={"vcf": vcf, "sort_by": "POS", "offset": 5, "limit": 5},
    ).json()
    assert p1["total"] == 20 and p1["filtered"] == 20
    assert [r["POS"] for r in p1["rows"]] == [10, 20, 30, 40, 50]
    assert [r["POS"] for r in p2["rows"]] == [60, 70, 80, 90, 100]

    # server-side sort (descending)
    desc = client.post(
        "/api/v2/vcf/query",
        json={"vcf": vcf, "sort_by": "POS", "sort_desc": True, "offset": 0, "limit": 3},
    ).json()
    assert [r["POS"] for r in desc["rows"]] == [200, 190, 180]

    # server-side filters
    by_chrom = client.post(
        "/api/v2/vcf/query",
        json={"vcf": vcf, "filters": {"chrom": "chr1"}, "limit": 50},
    ).json()
    assert by_chrom["filtered"] == 7
    assert all(r["CHROM"] == "chr1" for r in by_chrom["rows"])

    by_af = client.post(
        "/api/v2/vcf/query",
        json={"vcf": vcf, "filters": {"af_min": 0.01}, "limit": 50},
    ).json()
    assert by_af["filtered"] == 11  # AF >= 0.01 → i = 10..20

    by_qual = client.post(
        "/api/v2/vcf/query",
        json={"vcf": vcf, "filters": {"qual_min": 15}, "limit": 50},
    ).json()
    assert by_qual["filtered"] == 6

    by_cons = client.post(
        "/api/v2/vcf/query",
        json={"vcf": vcf, "filters": {"consequence": "missense"}, "limit": 50},
    ).json()
    assert by_cons["filtered"] == 20

    by_clin = client.post(
        "/api/v2/vcf/query",
        json={"vcf": vcf, "filters": {"clinvar": "benign"}, "limit": 50},
    ).json()
    assert by_clin["filtered"] == 0


def test_v2_vcf_query_rejects_bad_input(client):
    assert client.post("/api/v2/vcf/query", json={}).status_code == 400
    bad_sort = client.post("/api/v2/vcf/query", json={"vcf": "##x\n", "sort_by": "DROP TABLE"})
    assert bad_sort.status_code == 400
    missing_upload = client.post("/api/v2/vcf/query", json={"upload_id": "doesnotexist1"})
    assert missing_upload.status_code == 404


def test_v2_vcf_query_over_upload_id(client):
    upload_id = "vcfqueryupload1"
    vcf = "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\nchr1\t5\trs1\tA\tT\t9\tPASS\tAF=0.1\n"
    client.post(
        "/api/v2/upload/chunk",
        json={"upload_id": upload_id, "offset": 0, "data_b64": base64.b64encode(vcf.encode()).decode(), "final": True},
    )
    body = client.post("/api/v2/vcf/query", json={"upload_id": upload_id, "limit": 10}).json()
    assert body["filtered"] == 1
    assert body["rows"][0]["CHROM"] == "chr1"
