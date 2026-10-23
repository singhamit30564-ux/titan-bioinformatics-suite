"""Provenance records for statistical runs (Rust/Python/R engines alike).

Compatible with :mod:`titan_utils.privacy` (SHA-256 fingerprints, no payload
retention) and the ELN audit trail (see :meth:`titan_utils.eln.ELNLog.log_run`).
"""
from __future__ import annotations

import platform
import sys
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from titan_utils.privacy import provenance_record


def _package_versions(names: Sequence[str]) -> dict[str, Optional[str]]:
    versions: dict[str, Optional[str]] = {}
    for name in names:
        try:
            module = __import__(name)
            versions[name] = getattr(module, "__version__", "unknown")
        except Exception:
            versions[name] = None
    return versions


def stats_provenance(
    *,
    analysis: str,
    inputs: Mapping[str, Any],
    params: Mapping[str, Any],
    seed: int = 0,
    engine: str = "python",
    extra_packages: Sequence[str] = (),
    r_versions: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    """Build a provenance record for one statistical run.

    ``inputs`` maps label → payload (str/bytes/bytearray) that is fingerprinted
    with SHA-256 and *not* retained. ``params`` must already be JSON-safe.
    """
    records = {}
    for label, payload in inputs.items():
        rec = provenance_record(payload, kind="stats_input", label=str(label))
        records[str(label)] = rec.as_dict()
    packages = _package_versions(
        ("numpy", "pandas", "scipy", "sklearn", "pydeseq2", "xgboost", "shap", "umap")
        + tuple(extra_packages)
    )
    payload = {
        "algorithm": "SHA-256",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "analysis": analysis,
        "engine": engine,
        "seed": int(seed),
        "inputs": records,
        "params": dict(params),
        "package_versions": packages,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "r_versions": dict(r_versions or {}),
        "zero_data_retention": True,
    }
    return payload


def provenance_to_eln_parameters(prov: Mapping[str, Any]) -> dict[str, Any]:
    """Flatten a provenance record into ELN ``parameters`` (digests only)."""
    flat: dict[str, Any] = {
        "analysis": prov.get("analysis"),
        "engine": prov.get("engine"),
        "seed": prov.get("seed"),
    }
    for label, rec in (prov.get("inputs") or {}).items():
        flat[f"input:{label}:sha256"] = rec.get("digest", "")[:16]
        flat[f"input:{label}:bytes"] = rec.get("size_bytes")
    versions = prov.get("package_versions") or {}
    flat["packages"] = ", ".join(
        f"{name}={version}" for name, version in sorted(versions.items()) if version
    )
    if prov.get("r_versions"):
        flat["r"] = ", ".join(f"{k}={v}" for k, v in prov["r_versions"].items())
    return flat
