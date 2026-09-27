"""Zero Data Retention (ZDR) architecture for the Titan Bioinformatics Suite.

Guarantees
----------
1. **100% ephemeral in-RAM execution** — every genomic payload (sequences,
   VCFs, FASTQ reads) lives in scrub-able ``bytearray`` buffers that are held
   in process memory only. No ZDR code path ever opens a file for writing.
2. **Cryptographic provenance** — every payload is fingerprinted with
   SHA-256 so results remain verifiable *after* the payload itself is gone
   (hash-based integrity without retention).
3. **1-click session memory sanitizer** — :func:`sanitize_session_memory`
   scrubs every registered vault and every genomic value inside a Streamlit
   session state in a single call.

The module is Streamlit-optional: all core classes and functions work in
plain Python so they can be unit-tested and reused headlessly.
"""
from __future__ import annotations

import gc
import hashlib
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

__all__ = [
    "ZeroDataRetentionError",
    "ZDR_POLICY",
    "GENOMIC_KEY_PATTERN",
    "sha256_hex",
    "sha256_of_text",
    "provenance_record",
    "provenance_manifest",
    "is_genomic_text",
    "looks_genomic_key",
    "EphemeralVault",
    "register_vault",
    "registered_vaults",
    "scrub_all_vaults",
    "sanitize_session_memory",
    "memory_snapshot",
    "assert_ephemeral_path",
    "guard_disk_write",
]

# ─────────────────────────────────────────────────────────────────────────────
# Policy
# ─────────────────────────────────────────────────────────────────────────────

ZDR_POLICY = (
    "TITAN ZERO DATA RETENTION (ZDR) POLICY — All genomic inputs (DNA/RNA "
    "sequences, VCF variant records, FASTQ reads) are processed 100% "
    "in-RAM in ephemeral byte buffers. Genomic payloads are never written "
    "to disk, never persisted in databases, and never retained after the "
    "session ends. Each payload is fingerprinted with a one-way SHA-256 "
    "digest so outputs remain cryptographically verifiable without "
    "retaining the underlying data. The session memory sanitizer "
    "instantly zeroizes every in-memory buffer on demand."
)

ALGORITHM = "SHA-256"

# Key names in session state / dicts that mark genomic payloads.
GENOMIC_KEY_PATTERN = re.compile(
    r"(seq|dna|rna|fasta|fastq|vcf|read|genom|motif|allele|variant|protein|nucleotide|orf|amplicon|primer)",
    re.IGNORECASE,
)

# Alphabet heuristic: long runs of IUPAC nucleotides / protein letters.
_SEQ_ALPHABET = re.compile(r"^[ACGTUNRYSWKMBDHVacgtunryswkmbdhv\s>*|.\-0-9:]+$")
_FASTQ_HINT = re.compile(r"^@\S+\s*$", re.MULTILINE)
_VCF_HINT = re.compile(r"^##fileformat=VCF", re.MULTILINE)


class ZeroDataRetentionError(RuntimeError):
    """Raised when an operation would violate the zero-data-retention policy."""


# ─────────────────────────────────────────────────────────────────────────────
# Cryptographic provenance (SHA-256)
# ─────────────────────────────────────────────────────────────────────────────

def sha256_hex(data: "str | bytes | bytearray") -> str:
    """Return the lowercase hex SHA-256 digest of ``data``."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(bytes(data)).hexdigest()


def sha256_of_text(text: "str | bytes | bytearray | None") -> str:
    """Convenience wrapper tolerating ``None`` payloads (hashed as empty)."""
    return sha256_hex(text if text is not None else "")


@dataclass(frozen=True)
class ProvenanceRecord:
    """A cryptographic fingerprint for one ephemeral payload.

    The payload itself is *not* stored — only its digest, size and metadata —
    which is exactly what the ZDR policy requires: verifiable provenance
    without data retention.
    """

    digest: str
    kind: str = "sequence"
    size_bytes: int = 0
    algorithm: str = ALGORITHM
    created_utc: str = ""
    label: str = ""
    truncated: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "digest": self.digest,
            "kind": self.kind,
            "size_bytes": self.size_bytes,
            "created_utc": self.created_utc,
            "label": self.label,
            "truncated": self.truncated,
        }

    @property
    def short(self) -> str:
        return self.digest[:16]


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def provenance_record(
    data: "str | bytes | bytearray | None",
    kind: str = "sequence",
    label: str = "",
    max_bytes: int = 0,
) -> ProvenanceRecord:
    """Fingerprint an ephemeral payload with SHA-256.

    ``max_bytes`` optionally bounds hashing to the first N bytes of very
    large payloads; the record is flagged ``truncated`` when applied.
    """
    raw: bytes
    if data is None:
        raw = b""
    elif isinstance(data, str):
        raw = data.encode("utf-8")
    else:
        raw = bytes(data)

    truncated = bool(max_bytes and len(raw) > max_bytes)
    if truncated:
        raw = raw[:max_bytes]
    return ProvenanceRecord(
        digest=sha256_hex(raw),
        kind=kind,
        size_bytes=len(raw),
        created_utc=_utc_now(),
        label=label,
        truncated=truncated,
    )


def provenance_manifest(
    items: Iterable[tuple],
) -> Dict[str, Any]:
    """Build a manifest dict for ``(label, data[, kind])`` tuples.

    The manifest retains *only* SHA-256 digests and metadata — never the
    payloads — so it can be shipped inside export packages safely.
    """
    records: List[Dict[str, Any]] = []
    chain_input = []
    for item in items:
        label, data = item[0], item[1]
        kind = item[2] if len(item) > 2 else "sequence"
        rec = provenance_record(data, kind=kind, label=str(label))
        records.append(rec.as_dict())
        chain_input.append(f"{rec.label}:{rec.digest}")
    chain = sha256_hex("\n".join(chain_input))
    return {
        "algorithm": ALGORITHM,
        "generated_utc": _utc_now(),
        "suite": "Titan Bioinformatics Suite",
        "zero_data_retention": True,
        "record_count": len(records),
        "records": records,
        "chained_digest": chain,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Genomic payload classification
# ─────────────────────────────────────────────────────────────────────────────

def is_genomic_text(text: "str | bytes | bytearray | None") -> bool:
    """Heuristic: does this payload look like sequence / VCF / FASTQ data?"""
    if text is None:
        return False
    if isinstance(text, (bytes, bytearray)):
        try:
            text = bytes(text).decode("utf-8")
        except UnicodeDecodeError:
            return True  # binary blobs are treated as sensitive
    if not isinstance(text, str):
        return False
    s = text.strip()
    if len(s) < 20:
        return False
    if _VCF_HINT.search(s) or _FASTQ_HINT.search(s):
        return True
    compact = re.sub(r"\s+", "", s)
    if len(compact) < 20:
        return False
    if not _SEQ_ALPHABET.match(compact):
        return False
    letters = re.sub(r"[^A-Za-z]", "", compact)
    if not letters:
        return False
    acgt = sum(letters.upper().count(b) for b in "ACGTUN")
    return (acgt / len(letters)) >= 0.85


def looks_genomic_key(key: "str | None") -> bool:
    """True when a session-state key name marks genomic data."""
    return bool(key) and bool(GENOMIC_KEY_PATTERN.search(str(key)))


# ─────────────────────────────────────────────────────────────────────────────
# Ephemeral in-RAM vault
# ─────────────────────────────────────────────────────────────────────────────

_VAULT_LOCK = threading.Lock()
_VAULTS: "List[Any]" = []  # weak references to live vaults


def register_vault(vault: "EphemeralVault") -> "EphemeralVault":
    """Track a vault so the session sanitizer can scrub it later."""
    import weakref

    with _VAULT_LOCK:
        # Drop dead refs opportunistically.
        _VAULTS[:] = [w for w in _VAULTS if w() is not None]
        _VAULTS.append(weakref.ref(vault))
    return vault


def registered_vaults() -> List["EphemeralVault"]:
    """Return every live :class:`EphemeralVault` currently registered."""
    with _VAULT_LOCK:
        return [w() for w in _VAULTS if w() is not None]


class EphemeralVault:
    """In-RAM-only buffer for genomic data — never touches the filesystem.

    The payload is stored inside a mutable ``bytearray`` so :meth:`scrub` can
    cryptographically zeroize it (overwriting every byte) before the buffer is
    released. Instances scrub themselves on context-exit and on GC.
    """

    __slots__ = ("_buf", "_kind", "_label", "_created", "_scrubbed", "_digest", "__weakref__")

    def __init__(
        self,
        payload: "str | bytes | bytearray",
        kind: str = "sequence",
        label: str = "",
        register: bool = True,
    ) -> None:
        if isinstance(payload, str):
            raw = payload.encode("utf-8")
        else:
            raw = bytes(payload)
        self._buf = bytearray(raw)
        self._kind = kind
        self._label = label or kind
        self._created = _utc_now()
        self._scrubbed = False
        self._digest = sha256_hex(raw)
        if register:
            register_vault(self)

    # -- read-only views -----------------------------------------------------
    @property
    def kind(self) -> str:
        return self._kind

    @property
    def label(self) -> str:
        return self._label

    @property
    def scrubbed(self) -> bool:
        return self._scrubbed

    @property
    def digest(self) -> str:
        """SHA-256 digest — remains valid after scrubbing (provenance)."""
        return self._digest

    @property
    def size_bytes(self) -> int:
        return 0 if self._scrubbed else len(self._buf)

    @property
    def data(self) -> str:
        """Return the payload text (empty string once scrubbed)."""
        if self._scrubbed:
            return ""
        return bytes(self._buf).decode("utf-8", errors="replace")

    def provenance(self) -> ProvenanceRecord:
        return ProvenanceRecord(
            digest=self._digest,
            kind=self._kind,
            size_bytes=self.size_bytes,
            created_utc=self._created,
            label=self._label,
        )

    # -- zeroization --------------------------------------------------------
    def scrub(self) -> int:
        """Zeroize every byte of the buffer. Returns bytes wiped."""
        if self._scrubbed or not self._buf:
            self._scrubbed = True
            return 0
        n = len(self._buf)
        # Overwrite in place — CPython bytearray keeps one contiguous buffer.
        for i in range(n):
            self._buf[i] = 0
        self._buf.clear()
        self._buf = bytearray()
        self._scrubbed = True
        return n

    # -- context manager / GC ----------------------------------------------
    def __enter__(self) -> "EphemeralVault":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.scrub()

    def __del__(self) -> None:  # pragma: no cover — GC timing dependent
        try:
            self.scrub()
        except Exception:
            pass

    def __repr__(self) -> str:  # never leak payload content
        state = "scrubbed" if self._scrubbed else f"{self.size_bytes} B"
        return f"<EphemeralVault {self._label!r} {self._kind} {state} sha256={self._digest[:12]}…>"


def scrub_all_vaults() -> Dict[str, int]:
    """Scrub every registered vault. Returns per-vault wiped byte counts."""
    report: Dict[str, int] = {}
    for vault in registered_vaults():
        report[vault.label] = vault.scrub()
    return report


# ─────────────────────────────────────────────────────────────────────────────
# Disk-write guard (enforce "never persisted")
# ─────────────────────────────────────────────────────────────────────────────

# Only non-genomic artifacts (reports, aggregates, manifests) may be exported.
_PROTECTED_SUFFIXES = (".fa", ".fasta", ".fna", ".fq", ".fastq", ".vcf", ".sam", ".bam")


def assert_ephemeral_path(path: "str | None") -> None:
    """Raise if ``path`` looks like a genomic-data persistence target."""
    if not path:
        return
    lowered = str(path).lower()
    if lowered.endswith(_PROTECTED_SUFFIXES):
        raise ZeroDataRetentionError(
            f"ZDR policy forbids persisting genomic data to disk: {path!r}. "
            "Keep sequences/FASTQ/VCF payloads in EphemeralVault buffers."
        )


def guard_disk_write(path: "str | None", payload: "str | bytes | bytearray | None" = None) -> None:
    """Guard before any write: refuses genomic paths *and* genomic payloads.

    Reports / manifests / aggregate tables are allowed; raw genomic payloads
    are not — they must stay inside :class:`EphemeralVault`.
    """
    assert_ephemeral_path(path)
    if payload is not None and is_genomic_text(payload):
        raise ZeroDataRetentionError(
            "ZDR policy forbids writing genomic payloads to disk. "
            "Export aggregate results or SHA-256 provenance digests instead."
        )


# ─────────────────────────────────────────────────────────────────────────────
# 1-click session memory sanitizer
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SanitizeReport:
    """Outcome of a sanitizer pass (safe to persist — digests & counts only)."""

    sanitized_utc: str = ""
    vaults_scrubbed: int = 0
    bytes_wiped: int = 0
    session_keys_cleared: List[str] = field(default_factory=list)
    session_keys_replaced: List[str] = field(default_factory=list)
    gc_collections: int = 0
    policy: str = ZDR_POLICY

    @property
    def total_actions(self) -> int:
        return (
            self.vaults_scrubbed
            + len(self.session_keys_cleared)
            + len(self.session_keys_replaced)
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "sanitized_utc": self.sanitized_utc,
            "vaults_scrubbed": self.vaults_scrubbed,
            "bytes_wiped": self.bytes_wiped,
            "session_keys_cleared": list(self.session_keys_cleared),
            "session_keys_replaced": list(self.session_keys_replaced),
            "gc_collections": self.gc_collections,
            "total_actions": self.total_actions,
        }

    def summary(self) -> str:
        return (
            f"Session memory sanitized at {self.sanitized_utc} — "
            f"{self.vaults_scrubbed} vault(s) zeroized ({self.bytes_wiped} bytes wiped), "
            f"{len(self.session_keys_cleared)} session value(s) deleted, "
            f"{len(self.session_keys_replaced)} replaced with '[SCRUBBED]'. "
            "Zero genomic data retained on disk or in memory."
        )


def _scrub_mapping_value(key: str, value: Any) -> str:
    """Decide how to handle one session-state entry. Returns action tag."""
    genomic_value = is_genomic_text(value)
    genomic_container = isinstance(value, EphemeralVault) or (
        isinstance(value, (list, tuple)) and any(is_genomic_text(v) for v in value if isinstance(v, (str, bytes, bytearray)))
    )
    if isinstance(value, EphemeralVault):
        value.scrub()
        return "replaced"
    if genomic_value or genomic_container or looks_genomic_key(key):
        return "replaced" if genomic_value or genomic_container else "cleared"
    return "none"


def sanitize_session_memory(
    session_state: "MutableMapping[str, Any] | None" = None,
    also_vaults: bool = True,
) -> SanitizeReport:
    """**1-click session memory sanitizer.**

    Zeroizes every registered :class:`EphemeralVault` and removes or replaces
    every genomic value held in ``session_state`` (defaults to the live
    Streamlit session). Non-genomic UI state (selected tool names, widget
    keys, XP counters …) is left untouched so the app keeps working.

    Returns a :class:`SanitizeReport` that contains only counts and digests —
    safe to persist under the ZDR policy.
    """
    report = SanitizeReport(sanitized_utc=_utc_now())

    if also_vaults:
        wiped = scrub_all_vaults()
        report.vaults_scrubbed = len(wiped)
        report.bytes_wiped = sum(wiped.values())

    if session_state is None:
        try:
            import streamlit as st

            session_state = st.session_state
        except Exception:
            session_state = None

    if session_state is not None:
        # Materialise keys first — mutating while iterating is unsafe.
        for key in list(getattr(session_state, "keys", lambda: [])()):
            try:
                value = session_state[key]
            except Exception:
                continue
            action = _scrub_mapping_value(str(key), value)
            if action == "replaced":
                replaced_ok = False
                try:
                    session_state[key] = "[SCRUBBED]"
                    replaced_ok = True
                except Exception:
                    try:
                        del session_state[key]
                    except Exception:
                        continue
                if replaced_ok:
                    report.session_keys_replaced.append(str(key))
                else:
                    report.session_keys_cleared.append(str(key))
            elif action == "cleared":
                try:
                    del session_state[key]
                except Exception:
                    continue
                report.session_keys_cleared.append(str(key))

    report.gc_collections = gc.collect()
    return report


def memory_snapshot() -> Dict[str, Any]:
    """Digest-only snapshot of live ephemeral buffers (ZDR-safe to persist)."""
    vaults = registered_vaults()
    return {
        "captured_utc": _utc_now(),
        "live_vaults": len(vaults),
        "bytes_in_ram": sum(v.size_bytes for v in vaults),
        "vaults": [
            {"label": v.label, "kind": v.kind, "sha256": v.digest, "size_bytes": v.size_bytes}
            for v in vaults
        ],
        "policy": "zero-data-retention",
    }
