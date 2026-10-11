"""Course Mode — the free "Titan Bioinformatics Course" engine.

Loads ``data/course.json`` (8 original chapters covering ICSE/CBSE Class 12
bioinformatics basics), grades each chapter's 5-question quiz using the same
instant exact-match grading spirit as :mod:`titan_utils.olympiad`'s Bio
Olympiad Arena, and builds a completion certificate with the existing
ReportLab-based :mod:`titan_utils.pdf_generator` (no new PDF dependency).

Progress persistence reuses the same browser ``localStorage`` JSON bridge as
Flashcards (see :mod:`titan_utils.local_storage`) — per-chapter completion
percentage is mirrored to the browser so progress survives a reload, while
XP is additionally merged into the suite's existing Arena XP counter
(``st.session_state["olympiad_xp"]``, the same counter used by the Bio
Olympiad & Practice Arena) so Course Mode plugs into the existing
progression system rather than inventing a second one.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from titan_utils.pdf_generator import PdfReportSpec, PdfSection, build_pdf_report

__all__ = [
    "DATA_PATH",
    "COURSE_TITLE",
    "QUIZ_XP",
    "PASS_THRESHOLD",
    "QuizQuestion",
    "Section",
    "Chapter",
    "load_course",
    "get_chapter",
    "grade_quiz",
    "chapter_completion_percent",
    "overall_completion_percent",
    "build_course_certificate",
]

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "course.json"
COURSE_TITLE = "Titan Bioinformatics Course — 2026"
QUIZ_XP = 40  # per passed chapter quiz — smaller than Olympiad tiers (50/100/200)
PASS_THRESHOLD = 0.6  # 3 of 5 correct


@dataclass(frozen=True)
class QuizQuestion:
    question: str
    options: Sequence[str]
    correct_index: int
    explanation: str = ""


@dataclass(frozen=True)
class Section:
    heading: str
    body: str


@dataclass(frozen=True)
class Chapter:
    id: str
    title: str
    sections: Sequence[Section] = field(default_factory=tuple)
    quiz: Sequence[QuizQuestion] = field(default_factory=tuple)


def load_course(path: "Path | None" = None) -> List[Chapter]:
    """Load the 8-chapter course from ``data/course.json``."""
    target = path or DATA_PATH
    with open(target, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    chapters: List[Chapter] = []
    for item in raw:
        sections = tuple(Section(heading=s["heading"], body=s["body"]) for s in item.get("sections", []))
        quiz = tuple(
            QuizQuestion(
                question=q["question"],
                options=tuple(q["options"]),
                correct_index=int(q["correct_index"]),
                explanation=q.get("explanation", ""),
            )
            for q in item.get("quiz", [])
        )
        chapters.append(Chapter(id=item["id"], title=item["title"], sections=sections, quiz=quiz))
    return chapters


def get_chapter(chapters: Sequence[Chapter], chapter_id: str) -> Chapter:
    for ch in chapters:
        if ch.id == chapter_id:
            return ch
    raise KeyError(f"Unknown chapter id: {chapter_id!r}")


def grade_quiz(chapter: Chapter, answers: Sequence[int]) -> Dict[str, Any]:
    """Grade a list of selected option indices against ``chapter.quiz``.

    Returns a dict with per-question correctness, the raw score, percentage,
    pass/fail against :data:`PASS_THRESHOLD`, and XP earned (0 if not passed).
    """
    total = len(chapter.quiz)
    results = []
    correct_count = 0
    for i, question in enumerate(chapter.quiz):
        chosen = answers[i] if i < len(answers) else -1
        is_correct = chosen == question.correct_index
        if is_correct:
            correct_count += 1
        results.append({
            "question": question.question,
            "chosen_index": chosen,
            "correct_index": question.correct_index,
            "correct": is_correct,
            "explanation": question.explanation,
        })
    percent = (correct_count / total * 100.0) if total else 0.0
    passed = total > 0 and (correct_count / total) >= PASS_THRESHOLD
    return {
        "chapter_id": chapter.id,
        "total": total,
        "correct": correct_count,
        "percent": round(percent, 1),
        "passed": passed,
        "xp_earned": QUIZ_XP if passed else 0,
        "results": results,
    }


def chapter_completion_percent(progress: Dict[str, Any], chapter_id: str) -> int:
    """0/50/100 — not started / attempted / passed, used for the progress UI."""
    entry = progress.get(chapter_id) or {}
    if entry.get("passed"):
        return 100
    if entry.get("best_score") is not None:
        return 50
    return 0


def overall_completion_percent(progress: Dict[str, Any], chapters: Sequence[Chapter]) -> int:
    if not chapters:
        return 0
    total = sum(chapter_completion_percent(progress, ch.id) for ch in chapters)
    return round(total / (len(chapters) * 100) * 100)


def build_course_certificate(
    student_name: str,
    chapters: Sequence[Chapter],
    progress: Dict[str, Any],
) -> bytes:
    """Render a completion certificate PDF in RAM (ReportLab, no disk write)."""
    name = (student_name or "Student").strip() or "Student"
    completed = [ch for ch in chapters if progress.get(ch.id, {}).get("passed")]
    percent = overall_completion_percent(progress, chapters)
    now = datetime.now(timezone.utc).strftime("%d %B %Y")

    status_line = (
        f"has successfully completed all {len(chapters)} chapters"
        if len(completed) == len(chapters)
        else f"has completed {len(completed)} of {len(chapters)} chapters ({percent}% overall)"
    )

    spec = PdfReportSpec(
        title=COURSE_TITLE,
        subtitle="Certificate of Completion",
        author="Titan Bioinformatics Suite",
        sections=[
            PdfSection(
                heading="Certificate",
                paragraphs=[
                    f"This certifies that {name} {status_line} of the free "
                    f"Titan Bioinformatics Course, covering DNA/RNA fundamentals, "
                    f"protein structure, the Central Dogma, bioinformatics tools, "
                    f"sequence analysis, biological databases, phylogenetics, and "
                    f"AI in biology.",
                    f"Issued: {now}.",
                ],
            ),
            PdfSection(
                heading="Chapters Completed",
                bullets=[f"{ch.title} — {'Passed' if ch in completed else 'Not yet passed'}" for ch in chapters],
                style="compact",
            ),
        ],
        footer_note=(
            "This is a self-paced, free educational certificate generated locally by the "
            "Titan Bioinformatics Suite. It is a learning milestone, not an accredited "
            "academic qualification."
        ),
    )
    return build_pdf_report(spec)
