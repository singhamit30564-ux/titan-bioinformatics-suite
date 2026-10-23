"""Dr. Titan Vision — optional "Photo Se Samjhao" Groq Vision helper.

Network access happens **only** when a Groq API key is configured (via
``st.secrets["GROQ_API_KEY"]`` or the ``GROQ_API_KEY`` environment variable).
With no key the module stays pure/offline and callers should render a
setup-instructions card instead of crashing — this mirrors the existing
network-optional pattern used by :mod:`titan_utils.olympiad` for Groq hints.

Zero Data Retention
--------------------
Images are base64-encoded and sent straight from RAM to the Groq API; this
module never opens a file for writing and never persists image bytes.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.request
from pathlib import Path
from typing import Optional

__all__ = [
    "GROQ_API_URL",
    "GROQ_VISION_MODEL",
    "DR_TITAN_VISION_SYSTEM_PROMPT",
    "MAX_IMAGE_BYTES",
    "RATE_LIMIT_PER_SESSION",
    "VisionNotConfiguredError",
    "get_groq_api_key",
    "encode_image_base64",
    "build_vision_request_body",
    "explain_image_hinglish",
]

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_VISION_MODEL = "llama-3.2-11b-vision-preview"

DR_TITAN_VISION_SYSTEM_PROMPT = (
    "You are Dr. Titan, a warm village-school science teacher. Explain this "
    "textbook page or photo to a village student in simple Hinglish (a "
    "natural mix of Hindi and English, written in Roman script). Keep the "
    "explanation under 200 words. If the image is not educational — not a "
    "textbook page, diagram, or science-related photo — say so honestly "
    "instead of inventing an explanation."
)

# Soft guard so a huge camera photo is not silently base64-inflated forever.
MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 4 MB

# Documented, honest session cap shown in the UI (see pages/80_Photo_Explainer.py).
RATE_LIMIT_PER_SESSION = 20


class VisionNotConfiguredError(RuntimeError):
    """Raised when Groq Vision is called without an API key configured."""


def get_groq_api_key(explicit: Optional[str] = None) -> str:
    """Resolve the Groq API key: explicit value > ``st.secrets`` > env var.

    Returns ``""`` (never raises) when nothing is configured, so pages can
    render an opt-in setup card instead of crashing. ``st.secrets`` is only
    consulted when a secrets file actually exists — some Streamlit versions
    render a visible error element even for caught missing-secrets errors.
    """
    if explicit:
        return explicit
    try:
        import streamlit as st

        secrets_paths = (
            Path.home() / ".streamlit" / "secrets.toml",
            Path.cwd() / ".streamlit" / "secrets.toml",
        )
        if any(path.is_file() for path in secrets_paths):
            value = st.secrets.get("GROQ_API_KEY")  # type: ignore[union-attr]
            if value:
                return str(value)
    except Exception:
        pass
    return os.environ.get("GROQ_API_KEY", "") or ""


def encode_image_base64(image_bytes: bytes) -> str:
    """Base64-encode raw image bytes (in RAM only)."""
    return base64.b64encode(image_bytes).decode("ascii")


def build_vision_request_body(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    model: str = GROQ_VISION_MODEL,
    user_prompt: str = "Explain this textbook page/image.",
) -> bytes:
    """Build the JSON request payload Groq's chat-completions API expects."""
    b64 = encode_image_base64(image_bytes)
    data_url = f"data:{mime_type};base64,{b64}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": DR_TITAN_VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        "max_tokens": 450,
        "temperature": 0.5,
    }
    return json.dumps(payload).encode("utf-8")


def explain_image_hinglish(
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    api_key: Optional[str] = None,
    model: str = GROQ_VISION_MODEL,
    timeout: float = 25.0,
) -> str:
    """Ask Groq Vision to explain ``image_bytes`` in simple Hinglish.

    Raises :class:`VisionNotConfiguredError` when no API key is available and
    :class:`ValueError` for empty/oversized images. Network/API failures
    propagate as :class:`RuntimeError` so the caller can show a friendly
    message without silently pretending the call succeeded.
    """
    if not image_bytes:
        raise ValueError("No image data supplied — capture or upload a photo first.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image is {len(image_bytes) / 1_000_000:.1f} MB — please use a photo "
            f"under {MAX_IMAGE_BYTES / 1_000_000:.0f} MB."
        )

    key = get_groq_api_key(api_key)
    if not key:
        raise VisionNotConfiguredError(
            "GROQ_API_KEY is not configured. Photo Se Samjhao is an opt-in "
            "feature — add a free key from console.groq.com to enable it."
        )

    body = build_vision_request_body(image_bytes, mime_type=mime_type, model=model)
    request = urllib.request.Request(
        GROQ_API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as exc:  # pragma: no cover - network failure path
        raise RuntimeError(f"Groq Vision request failed: {exc}") from exc

    try:
        payload = json.loads(raw)
        return str(payload["choices"][0]["message"]["content"]).strip()
    except Exception as exc:  # pragma: no cover - malformed API response
        raise RuntimeError(f"Groq Vision returned an unexpected response: {exc}") from exc
