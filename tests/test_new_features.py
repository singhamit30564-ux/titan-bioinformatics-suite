"""Focused regression coverage for Hindi UI, Classroom Quiz, and Tool API."""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestHindiInterface:
    def test_dictionary_translates_hindi_and_preserves_english_fallback(self):
        from titan_utils.i18n import t

        assert t("Home", "हिंदी") == "मुखपृष्ठ"
        assert t("Home", "English") == "Home"
        assert t("untranslated label", "हिंदी") == "untranslated label"

    def test_all_sidebar_pages_have_hindi_titles_and_body_fallback_is_explicit(self):
        from titan_utils.i18n import (
            SUPPORTED_HINDI_TOOL_PAGES,
            localized_page_title,
            page_has_hindi_translation,
            t,
        )

        page_files = {path.name for path in (ROOT / "pages").glob("*.py")}
        assert SUPPORTED_HINDI_TOOL_PAGES <= page_files
        assert len(SUPPORTED_HINDI_TOOL_PAGES) == 10
        assert page_has_hindi_translation("03_GC_Content_Melting_Temp.py")
        assert page_has_hindi_translation("55_CRISPR_Cas9_gRNA_Designer.py")
        assert not page_has_hindi_translation("06_Motif_Pattern_Finder.py")
        assert localized_page_title("79_Classroom_Quiz_Mode.py", "Classroom Quiz", "hi") == "कक्षा प्रश्नोत्तरी मोड"
        note = t("Untranslated tools remain in English. Hindi translations are coming soon.", "hi")
        assert "अंग्रेज़ी" in note and "जल्द" in note

    def test_sidebar_navigation_groups_are_localized(self):
        from titan_utils.i18n import HINDI, TRANSLATIONS

        groups = (
            "🏠 Home",
            "🎛️ Master Suite Hub",
            "🧬 1 · DNA / RNA Basics",
            "🥩 2 · Protein Analysis",
            "🚀 16 · Flow · Arena · ELN",
            "🎓 17 · Classroom Quiz",
        )
        assert all(TRANSLATIONS[HINDI].get(label) for label in groups)
        assert all(TRANSLATIONS[HINDI][label] != label for label in groups)


class TestClassroomQuiz:
    def setup_method(self):
        from titan_utils.classroom_quiz import reset_classrooms

        reset_classrooms()

    def teardown_method(self):
        from titan_utils.classroom_quiz import reset_classrooms

        reset_classrooms()

    def test_topic_builds_five_builtin_mcqs_and_unknown_topic_falls_back(self):
        from titan_utils.classroom_quiz import generate_quiz, resolve_topic

        questions = generate_quiz("CRISPR gene editing")
        assert len(questions) == 5
        assert all(len(question.options) == 4 for question in questions)
        assert {question.correct_index for question in questions} == {0, 1, 2, 3}
        assert questions == generate_quiz("crispr")
        assert resolve_topic("a topic not in the bank")[0] == "Bioinformatics Foundations"

    def test_four_character_codes_and_student_limit(self):
        from titan_utils.classroom_quiz import (
            MAX_STUDENTS_PER_ROOM,
            ROOM_TTL_SECONDS,
            create_classroom,
            create_session_code,
            get_classroom,
            join_classroom,
        )

        code = create_session_code("CRISPR", "teacher-session-1")
        assert code == create_session_code("crispr", "teacher-session-1")
        assert re.fullmatch(r"[A-HJ-NP-Z2-9]{4}", code)
        room = create_classroom("CRISPR", 1, now=1000.0)
        assert re.fullmatch(r"[A-HJ-NP-Z2-9]{4}", room["code"])
        join_classroom(room["code"], "Asha", now=1000.0)
        with pytest.raises(ValueError, match="student limit"):
            join_classroom(room["code"], "Ravi", now=1000.0)
        with pytest.raises(ValueError, match="Student count"):
            create_classroom("DNA", MAX_STUDENTS_PER_ROOM + 1, now=1001.0)
        assert get_classroom(room["code"], now=1000.0 + ROOM_TTL_SECONDS + 1) is None

    def test_answers_award_arena_xp_once_and_update_leaderboard(self):
        from titan_utils.classroom_quiz import (
            CLASSROOM_XP_PER_CORRECT_ANSWER,
            create_classroom,
            generate_quiz,
            get_leaderboard,
            join_classroom,
            submit_answer,
        )
        from titan_utils.olympiad import TIER_XP

        room = create_classroom("CRISPR", 2, now=2000.0)
        join_classroom(room["code"], "Asha", now=2000.0)
        answer = submit_answer(
            room["code"], "Asha", 0, generate_quiz("CRISPR")[0].correct_index, now=2000.0
        )
        duplicate = submit_answer(room["code"], "Asha", 0, 0, now=2000.0)
        board = get_leaderboard(room["code"], now=2000.0)
        assert answer["accepted"] is True and answer["correct"] is True
        assert answer["xp_earned"] == TIER_XP["Foundational"] == CLASSROOM_XP_PER_CORRECT_ANSWER
        assert duplicate["accepted"] is False and duplicate["xp_earned"] == 0
        assert board[0]["name"] == "Asha" and board[0]["xp"] == 50


class TestToolAPI:
    def test_ten_allow_listed_tools_return_json_provenance(self):
        from titan_utils.api import API_TOOL_IDS, app, run_tool_api
        from titan_utils.privacy import sha256_of_text

        assert len(API_TOOL_IDS) == 10
        routes = [route for route in app.routes if route.path == "/api/run"]
        assert {method for route in routes for method in route.methods} == {"GET", "POST"}
        response = run_tool_api("gc_content", seq="ATGC")
        assert response["result"]["gc_percent"] == 50.0
        assert response["provenance"]["algorithm"] == "SHA-256"
        assert response["provenance"]["input_sha256"] == sha256_of_text('{"seq":"ATGC"}')
        assert re.fullmatch(r"[0-9a-f]{64}", response["provenance"]["output_sha256"])
        assert response["provenance"]["zero_data_retention"] is True

    def test_rate_limit_is_60_per_minute_per_ip_in_memory(self):
        from titan_utils.api import InMemoryRateLimiter

        limiter = InMemoryRateLimiter(limit=60, window_seconds=60)
        assert all(limiter.allow("192.0.2.1", now=0.0) for _ in range(60))
        assert not limiter.allow("192.0.2.1", now=1.0)
        assert limiter.allow("192.0.2.2", now=1.0)
        assert limiter.allow("192.0.2.1", now=60.1)

    def test_tool_validation_and_crispr_api_handler(self):
        from titan_utils.api import ToolAPIError, run_tool_api

        seq = "ATGC" * 5 + "AGG"
        guides = run_tool_api("crispr_designer", seq=seq, nuclease="SpCas9")["result"]
        assert guides["guide_count"] == 1
        assert guides["guides"][0]["pam"] == "AGG"
        with pytest.raises(ToolAPIError, match="Unsupported tool"):
            run_tool_api("not_a_tool", seq="ATGC")
        with pytest.raises(ToolAPIError, match="equal length"):
            run_tool_api("hamming_distance", seq="ATGC", seq2="ATG")
