"""🎓 Course Mode — the free Titan Bioinformatics Course.

8 original chapters (DNA/RNA, protein structure, Central Dogma, tools,
sequence analysis, databases, phylogenetics, AI in biology), each with a
5-question quiz. Passing a chapter quiz (>= 60%) awards XP into the suite's
**existing** Arena XP counter (``st.session_state["olympiad_xp"]``, shared
with the Bio Olympiad & Practice Arena) rather than creating a second XP
system. Per-chapter progress is mirrored to the browser's ``localStorage``
via the same bridge Flashcards uses (:mod:`titan_utils.local_storage`) so
progress survives a reload; ``st.session_state`` is the source of truth
during the live session.
"""
from __future__ import annotations

import streamlit as st

from titan_utils.course import (
    COURSE_TITLE,
    build_course_certificate,
    chapter_completion_percent,
    get_chapter,
    grade_quiz,
    load_course,
    overall_completion_percent,
)
from titan_utils.i18n import t
from titan_utils.local_storage import sync_json_blob
from titan_utils.ui import dr_titan_tip, titan_title

STORAGE_KEY = "titan_course_progress_v1"

titan_title(
    "🎓",
    t("Titan Bioinformatics Course"),
    t("A free, self-paced ICSE/CBSE Class 12-level bioinformatics primer — 8 chapters, 40 quiz questions, and a certificate."),
)

CHAPTERS = load_course()

if "course_progress" not in st.session_state:
    st.session_state["course_progress"] = {}
if "course_bootstrapped" not in st.session_state:
    restored = sync_json_blob(STORAGE_KEY, write=False, key="course_storage_read") or {}
    if isinstance(restored.get("progress"), dict):
        st.session_state["course_progress"] = dict(restored["progress"])
    st.session_state["course_bootstrapped"] = True
    st.session_state["course_dirty"] = False
if "course_dirty" not in st.session_state:
    st.session_state["course_dirty"] = False
if "olympiad_xp" not in st.session_state:
    st.session_state["olympiad_xp"] = 0  # shared Arena XP counter (Bio Olympiad page owns the default)

if st.session_state["course_dirty"]:
    sync_json_blob(
        STORAGE_KEY,
        payload={"progress": st.session_state["course_progress"]},
        write=True,
        key="course_storage_write",
    )
    st.session_state["course_dirty"] = False

overall_pct = overall_completion_percent(st.session_state["course_progress"], CHAPTERS)
m1, m2, m3 = st.columns(3)
m1.metric(t("Course Progress"), f"{overall_pct}%")
m2.metric(t("Arena XP"), st.session_state["olympiad_xp"])
m3.metric(t("Chapters"), f"{sum(1 for ch in CHAPTERS if st.session_state['course_progress'].get(ch.id, {}).get('passed'))}/{len(CHAPTERS)}")
st.progress(overall_pct / 100)

st.markdown("---")

chapter_labels = {f"{ch.id.upper()} · {ch.title}": ch.id for ch in CHAPTERS}
selected_label = st.selectbox(t("📚 Select a chapter"), options=list(chapter_labels.keys()), key="course_chapter_select")
chapter = get_chapter(CHAPTERS, chapter_labels[selected_label])
chapter_pct = chapter_completion_percent(st.session_state["course_progress"], chapter.id)
st.caption(t("Chapter status: {percent}% ({state})", percent=chapter_pct, state=t("Passed") if chapter_pct == 100 else (t("Attempted") if chapter_pct else t("Not started"))))

tab_learn, tab_quiz = st.tabs([t("📖 Learn"), t("📝 Quiz (5 MCQs)")])

with tab_learn:
    for section in chapter.sections:
        with st.container(border=True):
            st.markdown(f"#### {section.heading}")
            st.write(section.body)

with tab_quiz:
    st.caption(t("Score at least 60% (3 of 5) to pass this chapter and earn +{xp} XP.", xp=40))
    answers = []
    with st.form(f"course_quiz_form_{chapter.id}"):
        for i, question in enumerate(chapter.quiz):
            st.markdown(f"**{i + 1}. {question.question}**")
            choice = st.radio(
                t("Choose one:"),
                options=list(range(len(question.options))),
                format_func=lambda idx, opts=question.options: opts[idx],
                key=f"course_q_{chapter.id}_{i}",
                label_visibility="collapsed",
            )
            answers.append(choice)
            st.markdown("")
        submit_clicked = st.form_submit_button(t("✅ Submit Quiz"), type="primary", use_container_width=True)

    if submit_clicked:
        grade = grade_quiz(chapter, answers)
        entry = st.session_state["course_progress"].get(chapter.id, {})
        entry["best_score"] = max(entry.get("best_score", 0), grade["correct"])
        already_passed = entry.get("passed", False)
        entry["passed"] = already_passed or grade["passed"]
        st.session_state["course_progress"][chapter.id] = entry
        st.session_state["course_dirty"] = True

        if grade["passed"] and not already_passed:
            st.session_state["olympiad_xp"] += 40
            st.success(t(
                "🎉 Passed! {correct}/{total} correct ({percent}%). +40 XP added to your Arena total.",
                correct=grade["correct"], total=grade["total"], percent=grade["percent"],
            ))
            st.balloons()
        elif grade["passed"]:
            st.success(t(
                "✅ Passed again! {correct}/{total} correct ({percent}%). (XP was already awarded for this chapter.)",
                correct=grade["correct"], total=grade["total"], percent=grade["percent"],
            ))
        else:
            st.warning(t(
                "📘 {correct}/{total} correct ({percent}%) — below the 60% pass mark. Review the chapter and try again.",
                correct=grade["correct"], total=grade["total"], percent=grade["percent"],
            ))

        with st.expander(t("📋 Answer review")):
            for i, r in enumerate(grade["results"]):
                icon = "✅" if r["correct"] else "❌"
                st.markdown(f"{icon} **{i + 1}.** {r['question']}")
                if r["explanation"]:
                    st.caption(r["explanation"])

st.markdown("---")
st.markdown(t("### 🏅 Completion Certificate"))
st.caption(t("Honest label: a free, locally generated learning certificate — not an accredited qualification."))
cert_name = st.text_input(t("Your name (as it should appear on the certificate)"), key="course_cert_name")
cert_clicked = st.button(t("📄 Generate Certificate (PDF)"), key="course_cert_btn")

if cert_clicked:
    if not cert_name.strip():
        st.warning(t("✍️ Please enter your name first."))
    else:
        pdf_bytes = build_course_certificate(cert_name, CHAPTERS, st.session_state["course_progress"])
        st.success(t("✅ Certificate generated in-RAM — download below (nothing is stored on a server)."))
        st.download_button(
            t("⬇️ Download Certificate PDF"),
            data=pdf_bytes,
            file_name=f"titan_bio_course_certificate_{cert_name.strip().replace(' ', '_')[:40]}.pdf",
            mime="application/pdf",
            key="course_cert_download",
        )

st.caption(t("Course title: {title}", title=COURSE_TITLE))

dr_titan_tip(
    "Treat the quiz score as a checkpoint, not a grade — re-read any chapter "
    "you scored under 60% on and try again. Spaced revisiting beats a single "
    "cram session, just like the Flashcards tool next door."
)
