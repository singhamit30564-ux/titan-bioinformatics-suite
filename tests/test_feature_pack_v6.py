"""Feature Pack v6 — focused coverage for the 5 new additions.

Covers: Photo Se Samjhao (Vision AI), PWA/Offline Mode, Flashcards + SM-2-lite,
Course Mode, and the Android (Capacitor) wrapper. At least 3 tests per
feature, plus an explicit AppTest smoke test for each of the 3 new Streamlit
pages (generic page coverage also runs these in
``tests/test_page_interactions.py``).
"""
from __future__ import annotations

import json
import pathlib

import pytest
from streamlit.testing.v1 import AppTest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RENDER_TIMEOUT = 90


# ─────────────────────────────────────────────────────────────────────────────
# Feature 1 — 📸 Photo Se Samjhao (Vision AI)
# ─────────────────────────────────────────────────────────────────────────────

class TestPhotoExplainerVision:
    def test_get_groq_api_key_defaults_empty_without_secrets_or_env(self, monkeypatch):
        from titan_utils.vision import get_groq_api_key

        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        assert get_groq_api_key() == ""
        assert get_groq_api_key(explicit="gsk_explicit") == "gsk_explicit"
        monkeypatch.setenv("GROQ_API_KEY", "gsk_env_value")
        assert get_groq_api_key() == "gsk_env_value"

    def test_explain_image_hinglish_raises_without_key_and_on_empty_image(self, monkeypatch):
        from titan_utils.vision import VisionNotConfiguredError, explain_image_hinglish

        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(VisionNotConfiguredError):
            explain_image_hinglish(b"fake-bytes", api_key=None)
        with pytest.raises(ValueError):
            explain_image_hinglish(b"", api_key="gsk_test")

    def test_build_vision_request_body_embeds_base64_and_hinglish_system_prompt(self):
        from titan_utils.vision import DR_TITAN_VISION_SYSTEM_PROMPT, build_vision_request_body, encode_image_base64

        raw = b"\x89PNG\r\n\x1a\nFAKE_IMAGE_BYTES"
        body = json.loads(build_vision_request_body(raw, mime_type="image/png"))
        assert body["messages"][0]["content"] == DR_TITAN_VISION_SYSTEM_PROMPT
        assert "Hinglish" in DR_TITAN_VISION_SYSTEM_PROMPT and "200 words" in DR_TITAN_VISION_SYSTEM_PROMPT
        image_payload = body["messages"][1]["content"][1]["image_url"]["url"]
        assert image_payload.startswith("data:image/png;base64,")
        assert encode_image_base64(raw) in image_payload

    def test_page_loads_with_setup_card_when_groq_key_is_missing(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        at = AppTest.from_file(str(ROOT / "pages" / "80_Photo_Explainer.py"), default_timeout=RENDER_TIMEOUT).run()
        assert not at.exception, [e.value for e in at.exception]
        assert not at.error, [e.value for e in at.error]
        warnings = " ".join(w.value for w in at.warning)
        assert "Groq Vision key not configured" in warnings


# ─────────────────────────────────────────────────────────────────────────────
# Feature 2 — 📵 PWA / Offline Mode
# ─────────────────────────────────────────────────────────────────────────────

class TestPWAOfflineMode:
    def test_manifest_json_is_valid_and_matches_module_constants(self):
        from titan_utils.pwa import APP_NAME, THEME_COLOR

        manifest = json.loads((ROOT / "static" / "manifest.json").read_text(encoding="utf-8"))
        assert manifest["name"] == APP_NAME
        assert manifest["theme_color"] == THEME_COLOR == "#0a0e17"
        assert manifest["display"] == "standalone"
        icon_srcs = {icon["src"] for icon in manifest["icons"]}
        for icon in icon_srcs:
            assert (ROOT / "static" / icon).exists(), f"missing icon referenced by manifest: {icon}"

    def test_service_worker_never_intercepts_non_get_requests(self):
        sw_source = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
        assert "addEventListener(\"fetch\"" in sw_source
        assert "request.method !== \"GET\"" in sw_source  # never caches/blocks POST (AI/API calls)
        assert "CACHE_NAME" in sw_source

    def test_render_pwa_injector_never_raises_even_without_components(self, monkeypatch):
        from titan_utils import pwa

        def _boom(*args, **kwargs):
            raise RuntimeError("components unavailable in this host")

        monkeypatch.setattr(pwa, "render_pwa_injector", pwa.render_pwa_injector)  # sanity import
        import streamlit.components.v1 as components

        monkeypatch.setattr(components, "html", _boom)
        pwa.render_pwa_injector()  # must swallow the exception (graceful degradation)

    def test_home_shows_offline_scope_and_install_cards(self):
        at = AppTest.from_file(str(ROOT / "Home.py"), default_timeout=RENDER_TIMEOUT).run()
        assert not at.exception, [e.value for e in at.exception]
        markdown_text = " ".join(md.value for md in at.markdown)
        assert "Offline Mode & Install App" in markdown_text
        assert "Honest Offline Scope" in markdown_text
        assert "Install App (Android)" in markdown_text


# ─────────────────────────────────────────────────────────────────────────────
# Feature 3 — 🎴 Flashcards + Spaced Repetition
# ─────────────────────────────────────────────────────────────────────────────

class TestFlashcardsSpacedRepetition:
    def test_seed_deck_has_fifty_unique_cards_with_required_fields(self):
        from titan_utils.flashcards import load_seed_cards

        cards = load_seed_cards()
        assert len(cards) == 50
        ids = [c["id"] for c in cards]
        assert len(set(ids)) == 50
        for card in cards:
            assert card["term"].strip()
            assert card["definition"].strip()
            assert card["chapter"].strip()

    def test_sm2_lite_grows_interval_on_success_and_resets_on_failure(self):
        from datetime import date
        from titan_utils.flashcards import new_card_state, sm2_update

        today = date(2026, 1, 1)
        state = new_card_state("fc001")
        state = sm2_update(state, quality=5, today=today)
        assert state.interval == 1 and state.due_date == "2026-01-02"
        state = sm2_update(state, quality=5, today=date(2026, 1, 2))
        assert state.interval == 6
        state = sm2_update(state, quality=5, today=date(2026, 1, 8))
        assert state.interval > 6  # ease-multiplied growth

        lapsed = sm2_update(state, quality=1, today=date(2026, 2, 1))
        assert lapsed.interval == 1  # a failed recall resets the interval
        assert lapsed.ease < state.ease  # and nudges ease down

    def test_due_cards_and_progress_counts_reflect_review_state(self):
        from datetime import date
        from titan_utils.flashcards import CardState, due_cards, progress_counts

        cards = [{"id": "a", "chapter": "X"}, {"id": "b", "chapter": "X"}]
        today = date(2026, 1, 10)
        states = {"a": CardState(card_id="a", interval=5, ease=2.5, due_date="2026-01-20", reviews=2)}
        due = due_cards(cards, states, today)
        assert [c["id"] for c in due] == ["b"]  # "a" not due yet, "b" never reviewed -> due

        counts = progress_counts(cards, states, today)
        assert counts["total"] == 2
        assert counts["due"] == 1
        assert counts["reviewed"] == 1

    def test_flashcards_page_renders_cleanly(self):
        at = AppTest.from_file(str(ROOT / "pages" / "81_Flashcards.py"), default_timeout=RENDER_TIMEOUT).run()
        assert not at.exception, [e.value for e in at.exception]
        assert not at.error, [e.value for e in at.error]


# ─────────────────────────────────────────────────────────────────────────────
# Feature 4 — 🎓 Course Mode
# ─────────────────────────────────────────────────────────────────────────────

class TestCourseMode:
    def test_course_json_has_eight_chapters_with_five_question_quizzes(self):
        from titan_utils.course import load_course

        chapters = load_course()
        assert len(chapters) == 8
        for chapter in chapters:
            assert 3 <= len(chapter.sections) <= 4
            assert len(chapter.quiz) == 5
            for question in chapter.quiz:
                assert len(question.options) == 4
                assert 0 <= question.correct_index < 4

    def test_grade_quiz_passes_at_threshold_and_fails_below_it(self):
        from titan_utils.course import grade_quiz, load_course

        chapter = load_course()[0]
        all_correct = [q.correct_index for q in chapter.quiz]
        grade = grade_quiz(chapter, all_correct)
        assert grade["correct"] == 5 and grade["passed"] is True and grade["xp_earned"] == 40

        all_wrong = [(q.correct_index + 1) % 4 for q in chapter.quiz]
        grade_fail = grade_quiz(chapter, all_wrong)
        assert grade_fail["correct"] == 0 and grade_fail["passed"] is False and grade_fail["xp_earned"] == 0

    def test_certificate_pdf_bytes_are_a_valid_pdf(self):
        from titan_utils.course import build_course_certificate, load_course

        chapters = load_course()
        progress = {chapters[0].id: {"passed": True, "best_score": 5}}
        pdf_bytes = build_course_certificate("Test Student", chapters, progress)
        assert pdf_bytes[:4] == b"%PDF"
        assert len(pdf_bytes) > 1000

    def test_course_page_renders_cleanly(self):
        at = AppTest.from_file(str(ROOT / "pages" / "82_Course.py"), default_timeout=RENDER_TIMEOUT).run()
        assert not at.exception, [e.value for e in at.exception]
        assert not at.error, [e.value for e in at.error]


# ─────────────────────────────────────────────────────────────────────────────
# Feature 5 — 📱 Android (Capacitor) Wrapper
# ─────────────────────────────────────────────────────────────────────────────

class TestAndroidWrapper:
    def test_capacitor_config_has_required_app_identity_fields(self):
        config = json.loads((ROOT / "android-wrapper" / "capacitor.config.json").read_text(encoding="utf-8"))
        assert config["appId"] == "com.titan.bio"
        assert config["appName"] == "Titan Bio"
        assert config["webDir"] == "www"
        assert config["plugins"]["SplashScreen"]["backgroundColor"] == "#0a0e17"

    def test_package_json_lists_capacitor_dependencies(self):
        package = json.loads((ROOT / "android-wrapper" / "package.json").read_text(encoding="utf-8"))
        deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
        assert "@capacitor/core" in deps
        assert "@capacitor/cli" in deps
        assert "@capacitor/android" in deps

    def test_readme_documents_five_build_steps_and_is_honest_about_scope(self):
        readme = (ROOT / "android-wrapper" / "README.md").read_text(encoding="utf-8")
        for step_marker in ("1. **Install dependencies**", "2. **Add the Android platform**",
                            "3. **Point the wrapper", "4. **Open the project",
                            "5. **Build the APK**"):
            assert step_marker in readme, f"missing build step: {step_marker}"
        assert "WebView" in readme
        assert "beta" in readme.lower()

    def test_www_placeholder_exists_and_is_not_claimed_as_the_real_ui(self):
        index_html = (ROOT / "android-wrapper" / "www" / "index.html").read_text(encoding="utf-8")
        assert "NOT the app's real UI" in index_html
