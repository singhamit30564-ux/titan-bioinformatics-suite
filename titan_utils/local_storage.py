"""Generic browser-``localStorage`` JSON bridge for client-side persistence.

Design choice (documented, as required by the Flashcards/Course spec): this
suite already ships a tiny Streamlit component pattern for browser-local
state — :func:`titan_utils.classroom_storage.sync_classroom_profile`. Rather
than hand-rolling ``st.query_params`` persistence (which leaks state into
shareable URLs and has strict size/character limits), Flashcards' SM-2-lite
review state and Course Mode's per-chapter progress reuse that **same**
custom-component approach via a single generic bridge, so both features
persist across browser reloads without a server-side database.

Nothing genomic or personally identifying is ever stored here — only
flashcard scheduling metadata (interval/ease/due date) and course completion
percentages, both already visible in the UI.

If custom components are unavailable (e.g. ``streamlit.testing`` AppTest, or
a host that disables them) every function here returns ``None`` and callers
keep working from ``st.session_state`` alone — this is optional persistence,
never a hard dependency.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

_COMPONENT = None


def _component():
    global _COMPONENT
    if _COMPONENT is None:
        import streamlit.components.v1 as components

        component_dir = Path(__file__).with_name("components") / "local_json_storage"
        _COMPONENT = components.declare_component(
            "titan_local_json_storage",
            path=str(component_dir),
        )
    return _COMPONENT


def sync_json_blob(
    storage_key: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    write: bool = False,
    key: str = "local_json_storage",
) -> Optional[Dict[str, Any]]:
    """Read (and optionally write) a JSON blob from the browser's localStorage.

    Parameters
    ----------
    storage_key:
        The localStorage key, e.g. ``"titan_flashcards_v1"``.
    payload:
        When ``write=True``, this dict replaces the stored blob. Ignored when
        ``write=False`` (read-only sync).
    write:
        Set ``True`` to persist ``payload``; ``False`` to just read back
        whatever is already stored (used once per session on first load).
    key:
        Streamlit widget key — must be unique per call site on a page.

    Returns ``None`` when components are unavailable or nothing is stored yet
    (callers should keep using ``st.session_state`` as the source of truth).
    """
    try:
        value: Any = _component()(
            storage_key=storage_key,
            payload=payload or {},
            write=bool(write),
            key=key,
        )
    except Exception:  # pragma: no cover - defensive fallback for odd hosts
        return None
    if not isinstance(value, dict):
        return None
    return value
