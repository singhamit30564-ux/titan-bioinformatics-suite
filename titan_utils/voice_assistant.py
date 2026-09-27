"""Voice of Dr. Titan — client-side in-browser audio narration.

Builds self-contained HTML widgets that narrate text with the browser's
**Web Speech API** (``speechSynthesis``). Everything happens client-side:

* No audio is uploaded, synthesized server-side, or stored (ZDR friendly).
* No external TTS service, no API keys — uses the reader's local voices.
* Controls: play / pause / stop, speaking rate, pitch, language accent.

Wire into any Streamlit page with :func:`render_voice_narration`.
"""
from __future__ import annotations

import html as _html
import re
from typing import Dict, Tuple

__all__ = [
    "NARRATOR_VOICES",
    "strip_markup",
    "narration_html",
    "render_voice_narration",
    "summarize_for_speech",
]

NARRATOR_VOICES: Dict[str, Tuple[str, str]] = {
    "Dr. Titan (English)": ("en-US", "Dr. Titan narrates results and concepts in English."),
    "Dr. Titan (British)": ("en-GB", "British English narration."),
    "Dr. Titan (Hindi)": ("hi-IN", "Hindi narration for student explainers."),
    "Dr. Titan (Spanish)": ("es-ES", "Spanish narration."),
}

_SSML_TAG = re.compile(r"<[^>]+>")
_MARKDOWN_NOISE = re.compile(r"[*_`#>|\[\]()!]+")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_NL = re.compile(r"\n{3,}")


def strip_markup(text: str) -> str:
    """Strip HTML/Markdown noise so speech reads cleanly."""
    s = _html.unescape(text or "")
    s = _SSML_TAG.sub(" ", s)
    s = s.replace("**", " ").replace("__", " ")
    s = _MARKDOWN_NOISE.sub(" ", s)
    s = s.replace("→", " to ").replace("←", " from ").replace("≈", " about ")
    s = _MULTI_SPACE.sub(" ", s)
    s = _MULTI_NL.sub("\n\n", s)
    return s.strip()


def summarize_for_speech(text: str, max_chars: int = 600) -> str:
    """Condense long result copy into a narratable paragraph."""
    s = strip_markup(text)
    if len(s) <= max_chars:
        return s
    cut = s[:max_chars]
    stop = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "), cut.rfind("\n"))
    return (cut[: stop + 1] if stop > max_chars // 3 else cut).strip() + " ..."


def narration_html(
    text: str,
    lang: str = "en-US",
    autoplay: bool = False,
    rate: float = 1.0,
    pitch: float = 1.0,
    show_text: bool = True,
    accent: str = "#d4af37",
) -> str:
    """Build the self-contained Web Speech API narration widget HTML."""
    spoken = strip_markup(text)
    if not spoken:
        spoken = "No narration text available yet."
    spoken_js = spoken.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    safe_visible = _html.escape(spoken)
    rate = max(0.5, min(2.0, float(rate)))
    pitch = max(0.5, min(2.0, float(pitch)))
    text_block = (
        f"<div class='vtx-text'>{safe_visible}</div>"
        if show_text
        else ""
    )
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8" />
<style>
  html, body {{ margin: 0; padding: 0; background: #0a0e17; }}
  .vtx-wrap {{ font-family: 'Courier New', monospace; color: #e0e0e0; padding: 8px; }}
  .vtx-title {{ color: {accent}; font-size: 12px; font-weight: bold; letter-spacing: 1px; }}
  .vtx-row {{ display: flex; gap: 6px; margin: 8px 0; flex-wrap: wrap; align-items: center; }}
  .vtx-btn {{ border: none; border-radius: 6px; padding: 6px 14px; cursor: pointer;
             font-size: 12px; font-weight: bold; background: {accent}; color: #0a0e17; }}
  .vtx-btn.secondary {{ background: #222838; color: #e0e0e0; }}
  .vtx-slider {{ width: 110px; }}
  .vtx-status {{ font-size: 10px; color: #8b9bb4; margin-top: 4px; }}
  .vtx-text {{ font-size: 11px; color: #b9c2cc; line-height: 1.5; max-height: 120px;
             overflow-y: auto; border-left: 2px solid {accent}; padding-left: 8px; }}
  label {{ font-size: 10px; color: #8b9bb4; }}
</style>
</head>
<body>
<div class="vtx-wrap">
  <div class="vtx-title">VOICE OF DR. TITAN — IN-BROWSER NARRATION</div>
  <div class="vtx-row">
    <button class="vtx-btn" id="vtx-play">▶ Play</button>
    <button class="vtx-btn secondary" id="vtx-pause">⏸ Pause</button>
    <button class="vtx-btn secondary" id="vtx-stop">■ Stop</button>
  </div>
  <div class="vtx-row">
    <label>Rate <input class="vtx-slider" id="vtx-rate" type="range" min="0.5" max="2" step="0.1" value="{rate}"/></label>
    <label>Pitch <input class="vtx-slider" id="vtx-pitch" type="range" min="0.5" max="2" step="0.1" value="{pitch}"/></label>
    <label>Accent
      <select id="vtx-lang" style="background:#222838;color:#e0e0e0;border:none;border-radius:4px;padding:3px;">
        <option value="en-US" {'selected' if lang == 'en-US' else ''}>English (US)</option>
        <option value="en-GB" {'selected' if lang == 'en-GB' else ''}>English (UK)</option>
        <option value="hi-IN" {'selected' if lang == 'hi-IN' else ''}>Hindi (India)</option>
        <option value="es-ES" {'selected' if lang == 'es-ES' else ''}>Spanish</option>
      </select>
    </label>
  </div>
  {text_block}
  <div class="vtx-status" id="vtx-status">Ready — narration runs 100% in your browser (no audio is uploaded or stored).</div>
</div>
<script>
  (function () {{
    var transcript = `{spoken_js}`;
    var synth = window.speechSynthesis;
    var status = document.getElementById('vtx-status');
    if (!synth) {{
      status.textContent = 'Web Speech API not available in this browser.';
      return;
    }}
    function speak() {{
      synth.cancel();
      var u = new SpeechSynthesisUtterance(transcript);
      u.lang = document.getElementById('vtx-lang').value;
      u.rate = parseFloat(document.getElementById('vtx-rate').value);
      u.pitch = parseFloat(document.getElementById('vtx-pitch').value);
      var voices = synth.getVoices() || [];
      var pick = null;
      for (var i = 0; i < voices.length; i++) {{
        if (voices[i].lang === u.lang) {{ pick = voices[i]; break; }}
      }}
      if (pick) {{ u.voice = pick; }}
      u.onstart = function () {{ status.textContent = 'Narrating (client-side speechSynthesis)…'; }};
      u.onend = function () {{ status.textContent = 'Narration complete — nothing was stored.'; }};
      u.onerror = function () {{ status.textContent = 'Speech synthesis interrupted.'; }};
      synth.speak(u);
    }}
    document.getElementById('vtx-play').addEventListener('click', function () {{
      if (synth.paused && synth.speaking) {{ synth.resume(); status.textContent = 'Narrating…'; }}
      else {{ speak(); }}
    }});
    document.getElementById('vtx-pause').addEventListener('click', function () {{
      if (synth.speaking) {{ synth.pause(); status.textContent = 'Paused.'; }}
    }});
    document.getElementById('vtx-stop').addEventListener('click', function () {{
      synth.cancel(); status.textContent = 'Stopped — buffers cleared.';
    }});
    {"speak();" if autoplay else ""}
  }})();
</script>
</body>
</html>"""


def render_voice_narration(
    text: str,
    lang: str = "en-US",
    autoplay: bool = False,
    rate: float = 1.0,
    pitch: float = 1.0,
    show_text: bool = True,
    height: int = 190,
) -> None:
    """Render the Dr. Titan narration widget in the current Streamlit page."""
    from titan_utils.mol3d import embed_html

    embed_html(
        narration_html(
            text, lang=lang, autoplay=autoplay, rate=rate, pitch=pitch, show_text=show_text
        ),
        height=height,
    )
