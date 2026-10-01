"""Optional FastAPI endpoint for ten common Titan sequence tools.

Run with ``python -m titan_utils.api``. Request bodies are processed in RAM;
only SHA-256 fingerprints are returned as provenance. The in-memory rate limit
is per client IP and deliberately has no external cache or persistence.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import threading
import time
from collections import OrderedDict, deque
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

from titan_utils.privacy import provenance_record
from titan_utils.sequence import (
    clean_sequence,
    find_orfs_simple,
    nucleotide_counts,
    revcomp,
    translate,
    validate_dna,
    validate_rna,
)

MAX_SEQUENCE_LENGTH = 50_000
MAX_MOTIF_LENGTH = 1_000
MAX_API_RESULT_ITEMS = 1_000
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW_SECONDS = 60.0

API_TOOL_IDS = (
    "gc_content",
    "dna_complement",
    "dna_rna_conversion",
    "crispr_designer",
    "orf_finder",
    "dna_to_protein",
    "nucleotide_frequency",
    "kmer_frequency",
    "hamming_distance",
    "motif_finder",
)


class ToolAPIError(ValueError):
    """A safe client-facing tool input or lookup error."""


class InMemoryRateLimiter:
    """Thread-safe rolling-window rate limiter with bounded in-RAM IP state."""

    def __init__(
        self,
        limit: int = RATE_LIMIT_REQUESTS,
        window_seconds: float = RATE_LIMIT_WINDOW_SECONDS,
        max_tracked_ips: int = 10_000,
    ) -> None:
        if limit < 1 or window_seconds <= 0 or max_tracked_ips < 1:
            raise ValueError("Rate-limit settings must be positive.")
        self.limit = int(limit)
        self.window_seconds = float(window_seconds)
        self.max_tracked_ips = int(max_tracked_ips)
        self._events: OrderedDict[str, deque[float]] = OrderedDict()
        self._lock = threading.Lock()

    def allow(self, ip: str, *, now: float | None = None) -> bool:
        """Consume one request slot for ``ip``; return False at the limit."""
        current = float(now if now is not None else time.monotonic())
        client_ip = str(ip or "unknown")[:128]
        cutoff = current - self.window_seconds
        with self._lock:
            queue = self._events.get(client_ip)
            if queue is None:
                # Remove expired addresses first, then evict the least-recently
                # used address if many clients share this process.
                while self._events:
                    oldest_ip, oldest_events = next(iter(self._events.items()))
                    if oldest_events and oldest_events[-1] > cutoff:
                        break
                    self._events.pop(oldest_ip, None)
                while len(self._events) >= self.max_tracked_ips:
                    self._events.popitem(last=False)
                queue = deque()
                self._events[client_ip] = queue
            else:
                self._events.move_to_end(client_ip)
                while queue and queue[0] <= cutoff:
                    queue.popleft()
            if len(queue) >= self.limit:
                return False
            queue.append(current)
            return True

    def reset(self) -> None:
        """Clear tracked client windows (used by tests and local maintenance)."""
        with self._lock:
            self._events.clear()


RATE_LIMITER = InMemoryRateLimiter()


def _bounded_sequence(value: str, name: str = "seq") -> str:
    sequence = clean_sequence(str(value or ""))
    if not sequence:
        raise ToolAPIError(f"'{name}' must not be empty.")
    if len(sequence) > MAX_SEQUENCE_LENGTH:
        raise ToolAPIError(f"'{name}' exceeds the {MAX_SEQUENCE_LENGTH}-base API limit.")
    return sequence


def _validated_dna(value: str, *, allow_iupac: bool = False, name: str = "seq") -> str:
    sequence = _bounded_sequence(value, name=name)
    sequence, error = validate_dna(sequence, allow_iupac=allow_iupac)
    if error:
        raise ToolAPIError(f"Invalid DNA in '{name}'.")
    return sequence


def _validated_rna(value: str, *, name: str = "seq") -> str:
    sequence = _bounded_sequence(value, name=name)
    sequence, error = validate_rna(sequence)
    if error:
        raise ToolAPIError(f"Invalid RNA in '{name}'.")
    return sequence


def _crispr_guides(sequence: str, nuclease: str) -> dict[str, Any]:
    configurations = {
        "spcas9": {"pam": "NGG", "side": "3prime", "guide_length": 20, "pam_length": 3},
        "sacas9": {"pam": "NNGRRT", "side": "3prime", "guide_length": 21, "pam_length": 6},
        "cas12a": {"pam": "TTTV", "side": "5prime", "guide_length": 23, "pam_length": 4},
    }
    aliases = {
        "spcas9": "spcas9", "ngg": "spcas9", "sacas9": "sacas9",
        "nngrrt": "sacas9", "cas12a": "cas12a", "cpf1": "cas12a", "cas12acpf1": "cas12a", "tttv": "cas12a",
    }
    lookup = re.sub(r"[^a-z0-9]", "", str(nuclease or "SpCas9").casefold())
    selected = aliases.get(lookup)
    if selected is None:
        raise ToolAPIError("nuclease must be SpCas9, SaCas9, or Cas12a/Cpf1.")
    config = configurations[selected]
    iupac = {"N": "[ACGT]", "R": "[AG]", "Y": "[CT]", "V": "[ACG]"}
    pam_pattern = re.compile("".join(iupac.get(base, re.escape(base)) for base in config["pam"]))
    guide_length = config["guide_length"]
    pam_length = config["pam_length"]
    required = guide_length + pam_length
    if len(sequence) < required:
        return {"nuclease": selected, "pam": config["pam"], "guide_count": 0, "guides": []}

    guides: list[dict[str, Any]] = []
    total = 0
    for position in range(len(sequence) - required + 1):
        window = sequence[position:position + required]
        if config["side"] == "3prime":
            guide, pam = window[:guide_length], window[guide_length:]
        else:
            pam, guide = window[:pam_length], window[pam_length:]
        if not pam_pattern.fullmatch(pam):
            continue
        total += 1
        if len(guides) < MAX_API_RESULT_ITEMS:
            gc_percent = round((guide.count("G") + guide.count("C")) / len(guide) * 100, 1)
            guides.append({
                "position_1based": position + 1,
                "strand": "+",
                "guide_rna_dna_sequence": guide,
                "pam": pam,
                "gc_percent": gc_percent,
            })
    return {
        "nuclease": selected,
        "pam": config["pam"],
        "guide_count": total,
        "guides": guides,
        "truncated": total > len(guides),
        "educational_note": "Candidate scan only; no off-target or clinical suitability assessment is performed.",
    }


def _execute_tool(tool: str, params: dict[str, Any]) -> dict[str, Any]:
    """Run one allow-listed lightweight tool using shared titan_utils helpers."""
    sequence = str(params.get("seq", ""))
    if tool == "gc_content":
        seq = _validated_dna(sequence, allow_iupac=True)
        canonical_length = sum(seq.count(base) for base in "ATCG")
        if canonical_length == 0:
            raise ToolAPIError("GC content needs at least one A, T, C, or G base.")
        gc_count = seq.count("G") + seq.count("C")
        return {
            "length": len(seq),
            "canonical_bases": canonical_length,
            "gc_bases": gc_count,
            "gc_percent": round(gc_count / canonical_length * 100, 2),
        }

    if tool == "dna_complement":
        seq = _validated_dna(sequence, allow_iupac=True)
        return {"length": len(seq), "reverse_complement": revcomp(seq)}

    if tool == "dna_rna_conversion":
        mode = str(params.get("mode", "transcribe")).strip().casefold()
        if mode in {"transcribe", "dna_to_rna", "dna→rna"}:
            seq = _validated_dna(sequence, allow_iupac=False)
            return {"mode": "transcribe", "length": len(seq), "sequence": seq.replace("T", "U")}
        if mode in {"back_transcribe", "reverse_transcribe", "rna_to_dna", "rna→dna"}:
            seq = _validated_rna(sequence)
            return {"mode": "back_transcribe", "length": len(seq), "sequence": seq.replace("U", "T")}
        raise ToolAPIError("mode must be 'transcribe' or 'back_transcribe'.")

    if tool == "crispr_designer":
        seq = _validated_dna(sequence, allow_iupac=False)
        return _crispr_guides(seq, str(params.get("nuclease", params.get("pam", "SpCas9"))))

    if tool == "orf_finder":
        seq = _validated_dna(sequence, allow_iupac=True)
        orfs = find_orfs_simple(seq, min_len=0)
        return {"count": len(orfs), "orfs": orfs[:MAX_API_RESULT_ITEMS], "truncated": len(orfs) > MAX_API_RESULT_ITEMS}

    if tool == "dna_to_protein":
        seq = _validated_dna(sequence, allow_iupac=True)
        try:
            frame = int(params.get("frame", 0))
        except (TypeError, ValueError) as exc:
            raise ToolAPIError("frame must be 0, 1, or 2.") from exc
        if frame not in (0, 1, 2):
            raise ToolAPIError("frame must be 0, 1, or 2.")
        protein = translate(seq[frame:], to_stop=True)
        return {"frame_0based": frame, "protein": protein, "amino_acid_count": len(protein)}

    if tool == "nucleotide_frequency":
        seq = _validated_dna(sequence, allow_iupac=True)
        counts = nucleotide_counts(seq)
        canonical_length = sum(counts.values())
        frequencies = {
            base: round(count / canonical_length * 100, 2) if canonical_length else 0.0
            for base, count in counts.items()
        }
        entropy = 0.0
        if canonical_length:
            for count in counts.values():
                if count:
                    probability = count / canonical_length
                    entropy -= probability * math.log2(probability)
        return {"counts": counts, "frequencies_percent": frequencies, "shannon_entropy_bits": round(entropy, 4)}

    if tool == "kmer_frequency":
        seq = _validated_dna(sequence, allow_iupac=False)
        try:
            k = int(params.get("k", 3))
        except (TypeError, ValueError) as exc:
            raise ToolAPIError("k must be an integer from 1 to 12.") from exc
        if not 1 <= k <= 12:
            raise ToolAPIError("k must be an integer from 1 to 12.")
        from collections import Counter

        counts = Counter(seq[index:index + k] for index in range(max(0, len(seq) - k + 1)))
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return {
            "k": k,
            "windows": max(0, len(seq) - k + 1),
            "unique_kmers": len(counts),
            "top_kmers": [{"kmer": word, "count": count} for word, count in ranked[:MAX_API_RESULT_ITEMS]],
            "truncated": len(ranked) > MAX_API_RESULT_ITEMS,
        }

    if tool == "hamming_distance":
        left = _validated_dna(sequence, allow_iupac=True, name="seq")
        right = _validated_dna(str(params.get("seq2", "")), allow_iupac=True, name="seq2")
        if len(left) != len(right):
            raise ToolAPIError("Hamming distance requires sequences of equal length.")
        distance = sum(a != b for a, b in zip(left, right))
        return {"length": len(left), "distance": distance, "identity_percent": round(100 * (1 - distance / len(left)), 2)}

    if tool == "motif_finder":
        seq = _validated_dna(sequence, allow_iupac=False)
        motif = _validated_dna(str(params.get("pattern", "")), allow_iupac=False, name="pattern")
        if len(motif) > MAX_MOTIF_LENGTH:
            raise ToolAPIError(f"pattern exceeds the {MAX_MOTIF_LENGTH}-base limit.")
        positions = [match.start() + 1 for match in re.finditer(f"(?={re.escape(motif)})", seq)]
        return {"motif": motif, "count": len(positions), "positions_1based": positions[:MAX_API_RESULT_ITEMS], "truncated": len(positions) > MAX_API_RESULT_ITEMS}

    raise ToolAPIError(f"Unsupported tool '{tool}'. Choose one of the ten documented tool IDs.")


def run_tool_api(tool: str, **params: Any) -> dict[str, Any]:
    """Run a tool and add ZDR-style input/output SHA-256 provenance."""
    tool_id = str(tool or "").strip().casefold()
    if tool_id not in API_TOOL_IDS:
        raise ToolAPIError(f"Unsupported tool '{tool}'. Choose one of: {', '.join(API_TOOL_IDS)}.")
    payload = {key: params[key] for key in sorted(params)}
    input_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    result = _execute_tool(tool_id, payload)
    output_bytes = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    input_provenance = provenance_record(input_bytes, kind="api_input", label=f"api:{tool_id}")
    output_provenance = provenance_record(output_bytes, kind="api_output", label=f"api:{tool_id}:result")
    return {
        "tool": tool_id,
        "result": result,
        "provenance": {
            "algorithm": "SHA-256",
            "input_sha256": input_provenance.digest,
            "output_sha256": output_provenance.digest,
            "input_size_bytes": input_provenance.size_bytes,
            "output_size_bytes": output_provenance.size_bytes,
            "zero_data_retention": True,
        },
        "educational": True,
    }


class APIRunRequest(BaseModel):
    """Privacy-friendlier JSON POST equivalent of the GET query endpoint."""

    tool: str = Field(min_length=1, max_length=64)
    seq: str = Field(default="", max_length=MAX_SEQUENCE_LENGTH + 100)
    seq2: str = Field(default="", max_length=MAX_SEQUENCE_LENGTH + 100)
    pattern: str = Field(default="", max_length=MAX_MOTIF_LENGTH + 100)
    mode: str = Field(default="transcribe", max_length=32)
    nuclease: str = Field(default="SpCas9", max_length=32)
    pam: str = Field(default="", max_length=32)
    k: int = Field(default=3, ge=1, le=12)
    frame: int = Field(default=0, ge=0, le=2)


app = FastAPI(
    title="Titan Bioinformatics Tool API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
)


@app.middleware("http")
async def prevent_response_caching(request: Request, call_next: Any) -> Any:
    """Do not cache sequence-derived results in clients or intermediary caches."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


def _enforce_rate_limit(request: Request) -> None:
    client = request.client
    client_ip = client.host if client is not None else "unknown"
    if not RATE_LIMITER.allow(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded: 60 requests per minute per IP.",
            headers={"Retry-After": str(int(RATE_LIMIT_WINDOW_SECONDS))},
        )


def _execute_request(tool: str, **params: Any) -> dict[str, Any]:
    try:
        return run_tool_api(tool, **params)
    except ToolAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/run")
def run_api_get(
    request: Request,
    tool: str = Query(..., min_length=1, max_length=64),
    seq: str = Query("", max_length=MAX_SEQUENCE_LENGTH + 100),
    seq2: str = Query("", max_length=MAX_SEQUENCE_LENGTH + 100),
    pattern: str = Query("", max_length=MAX_MOTIF_LENGTH + 100),
    mode: str = Query("transcribe", max_length=32),
    nuclease: str = Query("SpCas9", max_length=32),
    pam: str = Query("", max_length=32),
    k: int = Query(3, ge=1, le=12),
    frame: int = Query(0, ge=0, le=2),
) -> dict[str, Any]:
    """GET /api/run?tool=gc_content&seq=ATGC"""
    _enforce_rate_limit(request)
    return _execute_request(
        tool,
        seq=seq,
        seq2=seq2,
        pattern=pattern,
        mode=mode,
        nuclease=nuclease,
        pam=pam,
        k=k,
        frame=frame,
    )


@app.post("/api/run")
def run_api_post(payload: APIRunRequest, request: Request) -> dict[str, Any]:
    """JSON-body variant avoids placing sequence input in a URL."""
    _enforce_rate_limit(request)
    return _execute_request(
        payload.tool,
        seq=payload.seq,
        seq2=payload.seq2,
        pattern=payload.pattern,
        mode=payload.mode,
        nuclease=payload.nuclease,
        pam=payload.pam,
        k=payload.k,
        frame=payload.frame,
    )


if __name__ == "__main__":  # pragma: no cover - exercised by the optional service
    import uvicorn

    parser = argparse.ArgumentParser(description="Run the Titan optional API service.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args()
    # Query sequences must not be echoed into routine access logs.
    uvicorn.run(app, host=args.host, port=args.port, access_log=False)
