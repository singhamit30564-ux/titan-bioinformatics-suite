"""🏫 Teacher Dashboard — Create assignments, track submissions, export CSV.

Teachers create assignments (pick tool + task + class code). Students submit
via classroom codes. All in localStorage / session — no database required.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime

import pandas as pd
import streamlit as st

from titan_utils.i18n import t
from titan_utils.io import df_to_csv_bytes as _csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title(
    "🏫",
    "Teacher Dashboard",
    "Create bioinformatics assignments, track student submissions, and export results — all locally.",
)

# ── Session state ────────────────────────────────────────────────────────────
if "teacher_assignments" not in st.session_state:
    st.session_state["teacher_assignments"] = []
if "teacher_submissions" not in st.session_state:
    st.session_state["teacher_submissions"] = []
if "teacher_mode" not in st.session_state:
    st.session_state["teacher_mode"] = "teacher"  # or "student"

# ── Mode toggle ──────────────────────────────────────────────────────────────
mode = st.radio(
    t("Select mode:"),
    ["👩‍🏫 Teacher", "👨‍🎓 Student"],
    horizontal=True,
    label_visibility="collapsed",
)
is_teacher = "Teacher" in mode

# ── TOOL OPTIONS ─────────────────────────────────────────────────────────────
TOOL_OPTIONS = [
    "GC Content Analysis",
    "DNA → RNA Transcription",
    "Reverse Complement",
    "ORF Finder",
    "Restriction Enzyme Cutting",
    "Protein Translation",
    "Molecular Weight Calculator",
    "PCR Product Length",
    "Codon Usage Analysis",
    "Primer Design",
]

TASK_TEMPLATES = [
    "Run {tool} on the given sequence: {seq}",
    "Compare the {tool} results of two sequences",
    "Identify all ORFs using {tool}",
    "Design primers using {tool} for the target gene",
    "Calculate GC content and explain biological significance using {tool}",
]

# ════════════════════════════════════════════════════════════════════════════
# TEACHER VIEW
# ════════════════════════════════════════════════════════════════════════════
if is_teacher:
    st.subheader(t("👩‍🏫 Create New Assignment"))

    with st.form("create_assignment"):
        col1, col2 = st.columns(2)
        with col1:
            tool = st.selectbox(t("Select Tool:"), TOOL_OPTIONS)
        with col2:
            class_code = st.text_input(t("Class Code (4 chars):"), max_chars=4, placeholder="BIO1")

        task = st.text_area(
            t("Task Description:"),
            value=TASK_TEMPLATES[0].format(tool=tool, seq="ATGCGATCGATCGATCG"),
            height=100,
        )
        submitted = st.form_submit_button(t("📌 Create Assignment"), type="primary", use_container_width=True)

    if submitted and class_code.strip():
        assignment_id = hashlib.sha1(f"{tool}{class_code}{time.time()}".encode()).hexdigest()[:8]
        assignment = {
            "id": assignment_id,
            "tool": tool,
            "task": task,
            "class_code": class_code.upper().strip(),
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        st.session_state["teacher_assignments"].append(assignment)
        st.success(t("✅ Assignment created! Share class code **{code}** with students.", code=class_code.upper()))

    # ── Existing assignments ─────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(t("📋 Your Assignments"))

    assignments = st.session_state["teacher_assignments"]
    if not assignments:
        st.info(t("No assignments created yet. Use the form above to create one."))
    else:
        for asgn in assignments:
            with st.container(border=True):
                st.markdown(f"**{asgn['tool']}** — Class: `{asgn['class_code']}`")
                st.caption(t("Created: {date}", date=asgn["created"]))
                st.write(asgn["task"])

                # Submissions for this assignment
                subs = [s for s in st.session_state["teacher_submissions"] if s["assignment_id"] == asgn["id"]]
                if subs:
                    st.markdown(f"**{t('Submissions')} ({len(subs)}):**")
                    df = pd.DataFrame(subs)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.caption(t("No submissions yet."))

    # ── Export all submissions ───────────────────────────────────────────────
    all_subs = st.session_state["teacher_submissions"]
    if all_subs:
        st.markdown("---")
        df_all = pd.DataFrame(all_subs)
        smart_lock(
            csv_data=_csv_bytes(df_all),
            csv_filename="teacher_submissions.csv",
        )

# ════════════════════════════════════════════════════════════════════════════
# STUDENT VIEW
# ════════════════════════════════════════════════════════════════════════════
else:
    st.subheader(t("👨‍🎓 Submit Assignment"))

    student_name = st.text_input(t("Your Name:"), placeholder="Aarav K.")
    join_code = st.text_input(t("Enter Class Code:"), max_chars=4, placeholder="BIO1")

    # Find matching assignment
    matching = [
        a for a in st.session_state["teacher_assignments"]
        if a["class_code"] == join_code.upper().strip()
    ]

    if matching:
        for asgn in matching:
            with st.container(border=True):
                st.markdown(f"### {asgn['tool']}")
                st.write(asgn["task"])
                answer = st.text_area(
                    t("Your Answer / Result:"),
                    key=f"answer_{asgn['id']}",
                    height=120,
                    placeholder="Paste your analysis result or write your answer here...",
                )
                if st.button(t("📤 Submit"), key=f"submit_{asgn['id']}", type="primary", use_container_width=True):
                    if student_name.strip() and answer.strip():
                        sub = {
                            "assignment_id": asgn["id"],
                            "student": student_name.strip(),
                            "tool": asgn["tool"],
                            "answer_preview": answer.strip()[:100],
                            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        }
                        st.session_state["teacher_submissions"].append(sub)
                        st.success(t("✅ Submitted! Your teacher will review it."))
                    else:
                        st.error(t("Please enter your name and answer."))
    elif join_code.strip():
        st.warning(t("No assignment found for code `{code}`. Check with your teacher.", code=join_code.upper()))

st.markdown("---")
st.caption(t(
    "ℹ️ All data is stored in Streamlit session state (in-browser) — no database, "
    "no account required. Data resets when the browser tab is closed."
))

dr_titan_tip(
    "Teachers: bioinformatics is best learned by doing! Assign hands-on tasks "
    "like 'find the GC content of this gene and explain why it matters for primer design.'"
)