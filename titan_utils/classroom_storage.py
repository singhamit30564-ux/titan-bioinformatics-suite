"""Tiny Streamlit component for a local-only classroom profile in browser storage."""
from __future__ import annotations

from pathlib import Path
from typing import Any

_COMPONENT = None


def sync_classroom_profile(profile: dict[str, str], *, key: str = "classroom_profile") -> dict[str, str] | None:
    """Read once from localStorage and keep the latest nickname/code there.

    The browser component intentionally stores only a student nickname and the
    four-character room code. Answers and DNA inputs are never put in browser
    storage. If custom components are unavailable (for example, AppTest), the
    Streamlit page continues using session_state without failing.
    """
    global _COMPONENT
    try:
        if _COMPONENT is None:
            import streamlit.components.v1 as components

            component_dir = Path(__file__).with_name("components") / "classroom_storage"
            _COMPONENT = components.declare_component(
                "titan_classroom_profile_storage",
                path=str(component_dir),
            )
        value: Any = _COMPONENT(
            profile={
                "name": str(profile.get("name", ""))[:32],
                "code": str(profile.get("code", ""))[:4].upper(),
            },
            storage_key="titan_classroom_profile_v1",
            key=key,
        )
    except Exception:  # pragma: no cover - defensive fallback for Streamlit hosts
        return None
    if not isinstance(value, dict):
        return None
    return {
        "name": str(value.get("name", ""))[:32],
        "code": str(value.get("code", ""))[:4].upper(),
    }
