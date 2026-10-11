"""📸 Photo Se Samjhao — Dr. Titan Vision AI (opt-in, Groq Vision).

Snap or upload a textbook page/diagram and Dr. Titan explains it in simple
Hinglish for a village student. This is an **opt-in enhancement**: without a
``GROQ_API_KEY`` the page still loads fully and shows a setup-instructions
card instead of failing.

Zero Data Retention: the captured/uploaded image bytes are read straight into
RAM (``getvalue()``) and sent to Groq only — this page never writes the image
to disk, and nothing is cached after the Streamlit session ends.
"""
from __future__ import annotations

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title
from titan_utils.vision import (
    RATE_LIMIT_PER_SESSION,
    VisionNotConfiguredError,
    explain_image_hinglish,
    get_groq_api_key,
)
from titan_utils.voice_assistant import render_voice_narration

titan_title(
    "📸",
    t("Photo Se Samjhao — Dr. Titan Vision"),
    t("Capture or upload a photo — Dr. Titan explains it in simple Hinglish."),
)

if "photo_explainer_request_count" not in st.session_state:
    st.session_state["photo_explainer_request_count"] = 0
if "photo_explainer_result" not in st.session_state:
    st.session_state["photo_explainer_result"] = ""

api_key = get_groq_api_key()

if not api_key:
    with st.container(border=True):
        st.warning(t("🔑 **Opt-in feature — Groq Vision key not configured.**"))
        st.markdown(t(
            "Photo Se Samjhao needs a **free** Groq API key to call the Vision model. "
            "The page still works without one — you just won't get an AI explanation yet."
        ))
        st.markdown(t(
            "**Setup (2 minutes):**\n"
            "1. Create a free key at [console.groq.com](https://console.groq.com/keys).\n"
            "2. Add it to `.streamlit/secrets.toml` as `GROQ_API_KEY = \"gsk_...\"`, "
            "or set the `GROQ_API_KEY` environment variable before launching Streamlit.\n"
            "3. Restart the app — this card disappears automatically once the key is found."
        ))
        st.caption(t("No key is ever requested here, stored, or transmitted by Titan itself."))

st.markdown("---")
st.markdown(t("### 1 · Capture or upload a photo"))
cam_col, upload_col = st.columns(2)
with cam_col:
    camera_photo = st.camera_input(t("📷 Use camera"), key="photo_explainer_camera")
with upload_col:
    uploaded_photo = st.file_uploader(
        t("🖼️ Or upload an image (jpg/png)"),
        type=["jpg", "jpeg", "png"],
        key="photo_explainer_upload",
    )

image_file = camera_photo or uploaded_photo

if image_file is not None:
    st.image(image_file, caption=t("Preview (held in RAM only — never saved to disk)"), width=320)

st.markdown("---")
st.markdown(t("### 2 · Dr. Titan, Samjhao!"))

remaining = max(0, RATE_LIMIT_PER_SESSION - st.session_state["photo_explainer_request_count"])
st.caption(t(
    "⚠️ Rate limit: {used}/{limit} explanations used this session (keeps the demo free & fast for everyone).",
    used=st.session_state["photo_explainer_request_count"],
    limit=RATE_LIMIT_PER_SESSION,
))

explain_clicked = st.button(
    t("🪄 Explain This Image (Hinglish)"),
    type="primary",
    use_container_width=True,
    key="photo_explainer_explain_btn",
)

enable_tts = st.checkbox(t("🔊 Read the explanation aloud (Voice of Dr. Titan)"), key="photo_explainer_tts")

if explain_clicked:
    if image_file is None:
        st.warning(t("📎 Please capture or upload an image first."))
    elif remaining <= 0:
        st.warning(t(
            "🚦 Session limit reached ({limit} explanations). Refresh the app to reset it.",
            limit=RATE_LIMIT_PER_SESSION,
        ))
    elif not api_key:
        st.info(t("ℹ️ Add a GROQ_API_KEY (see the setup card above) to enable AI explanations."))
    else:
        with st.spinner(t("🧑‍🏫 Dr. Titan dekh raha hai... (analyzing image)")):
            try:
                image_bytes = image_file.getvalue()
                mime_type = getattr(image_file, "type", None) or "image/jpeg"
                explanation = explain_image_hinglish(image_bytes, mime_type=mime_type, api_key=api_key)
                st.session_state["photo_explainer_request_count"] += 1
                st.session_state["photo_explainer_result"] = explanation
            except VisionNotConfiguredError:
                st.info(t("ℹ️ Groq Vision is not configured yet — see the setup card above."))
            except ValueError as exc:
                st.warning(f"⚠️ {exc}")
            except RuntimeError as exc:
                st.warning(t("🌐 Could not reach Groq Vision right now: {error}", error=str(exc)))

if st.session_state["photo_explainer_result"]:
    st.markdown("---")
    st.markdown(t("### 📖 Dr. Titan's Explanation"))
    st.markdown(st.session_state["photo_explainer_result"])
    if enable_tts:
        render_voice_narration(
            st.session_state["photo_explainer_result"],
            lang="hi-IN",
            show_text=False,
            height=150,
        )

dr_titan_tip(
    "Vision AI can misread blurry or low-light photos — hold the page flat, well-lit, "
    "and in focus. This is a simulated village-classroom helper, not a medical or "
    "exam-grading tool."
)
