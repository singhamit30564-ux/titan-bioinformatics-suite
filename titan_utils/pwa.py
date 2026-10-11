"""PWA / Offline Mode shell for the Titan suite — manifest + service worker.

Honest scope
------------
Streamlit ships one dynamic page (not a static SPA bundle), so a classic
pre-cached "app shell" is not fully achievable the way it is for a React/Vue
PWA. This module still wires up a **real** Web App Manifest
(``static/manifest.json``) and a best-effort Service Worker
(``static/sw.js``) via ``st.components.html`` injection, with graceful
degradation: every step is wrapped so a blocked/unsupported browser leaves
the rest of the app completely unaffected (see :func:`render_pwa_injector`).

What works offline vs. what needs the network is surfaced to the user
verbatim via :data:`OFFLINE_CAPABLE` / :data:`ONLINE_ONLY` — see the "Offline
Scope" card on Home.
"""
from __future__ import annotations

from typing import Tuple

__all__ = [
    "APP_NAME",
    "THEME_COLOR",
    "MANIFEST_URL",
    "SERVICE_WORKER_URL",
    "OFFLINE_CAPABLE",
    "ONLINE_ONLY",
    "ANDROID_INSTALL_STEPS",
    "pwa_injector_html",
    "render_pwa_injector",
]

APP_NAME = "Titan Bio"
THEME_COLOR = "#0a0e17"

# Paths served by Streamlit's app-static feature (server.enableStaticServing)
# from the repository's ./static directory, see .streamlit/config.toml.
MANIFEST_URL = "./app/static/manifest.json"
SERVICE_WORKER_URL = "./app/static/sw.js"

OFFLINE_CAPABLE: Tuple[str, ...] = (
    "Browsing pages you already opened this session",
    "Flashcards you have already loaded (data/flashcards.json ships with the app)",
    "Cached tool results still shown on screen",
)

ONLINE_ONLY: Tuple[str, ...] = (
    "Dr. Titan AI chat & copilot tools",
    "Photo Se Samjhao (Groq Vision)",
    "NCBI/KEGG/UniProt and other live bioinformatics APIs",
    "BLAST and any network-backed lookups",
)

ANDROID_INSTALL_STEPS: Tuple[str, ...] = (
    "Open this app's URL in Chrome on Android.",
    "Tap the \u22ee menu (top-right three dots).",
    "Tap \"Add to Home screen\" (shows the Titan Bio gold double-helix icon).",
    "Confirm \"Add\" — Chrome creates a home-screen icon that opens in standalone mode (no browser bar).",
    "Launch it from the home screen any time, just like a native app.",
)


def pwa_injector_html(manifest_url: str = MANIFEST_URL, sw_url: str = SERVICE_WORKER_URL) -> str:
    """Build the best-effort manifest-link + service-worker registration HTML.

    Runs inside a sandboxed ``components.html`` iframe. Everything is wrapped
    in ``try/catch`` so a browser that blocks any step (common for sandboxed
    preview iframes) degrades gracefully without throwing into the host page.
    """
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8" /></head>
<body style="margin:0;background:transparent;font-family:monospace;font-size:10px;color:#8b9bb4;">
<div id="titan-pwa-status">PWA: checking browser support…</div>
<script>
(function () {{
  var statusEl = document.getElementById('titan-pwa-status');
  function setStatus(msg) {{ if (statusEl) statusEl.textContent = 'PWA: ' + msg; }}
  try {{
    var target = (window.parent && window.parent.document) ? window.parent.document : document;
    if (!target.querySelector('link[rel="manifest"]')) {{
      var link = target.createElement('link');
      link.rel = 'manifest';
      link.href = {manifest_url!r};
      target.head.appendChild(link);
    }}
    if (!target.querySelector('meta[name="theme-color"]')) {{
      var meta = target.createElement('meta');
      meta.name = 'theme-color';
      meta.content = {THEME_COLOR!r};
      target.head.appendChild(meta);
    }}
  }} catch (e) {{
    setStatus('manifest injection skipped (' + e.message + ') — app unaffected.');
  }}
  try {{
    var sw = (window.parent && window.parent.navigator && window.parent.navigator.serviceWorker)
      ? window.parent.navigator.serviceWorker
      : (navigator.serviceWorker || null);
    if (sw) {{
      sw.register({sw_url!r}).then(function () {{
        setStatus('offline shell cache active (service worker registered).');
      }}).catch(function (err) {{
        setStatus('service worker unavailable in this browser context — app works online as normal.');
      }});
    }} else {{
      setStatus('service workers not supported here — app works online as normal.');
    }}
  }} catch (e) {{
    setStatus('service worker skipped (' + e.message + ') — app unaffected.');
  }}
}})();
</script>
</body></html>"""


def render_pwa_injector(height: int = 24) -> None:
    """Best-effort PWA wiring. Never raises — failures degrade silently.

    Call once, on Home.py only (not on every tool page), so a browser that
    blocks the injection can never affect any of the 260 bioinformatics
    tools — they do not depend on this at all.
    """
    try:
        import streamlit.components.v1 as components

        components.html(pwa_injector_html(), height=height)
    except Exception:
        # Graceful degradation: the suite must keep working with zero PWA support.
        pass
