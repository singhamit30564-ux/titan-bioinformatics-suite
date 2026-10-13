"""⚡ Weekly Challenge — Rosalind-style timed bioinformatics problems.

5 rotating problems (seed=42 selects one for the current week).
Leaderboard (localStorage). Share result text button.
"""
from __future__ import annotations

import hashlib
import random
import time
from datetime import date

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "⚡",
    "Weekly Bioinformatics Challenge",
    "Solve a Rosalind-style bioinformatics problem every week. Timed, scored, with a leaderboard!",
)

# ── Problem bank ─────────────────────────────────────────────────────────────
PROBLEMS = [
    {
        "id": "count_bases",
        "title": "🧬 Count Nucleotide Frequencies",
        "description": (
            "Given a DNA string of length ≤ 1000 bp, count how many times each nucleotide "
            "(A, C, G, T) appears.\n\n"
            "**Input:** A DNA string s\n"
            "**Output:** Four integers — counts of A, C, G, T separated by spaces."
        ),
        "example_input": "AGCTTTTCATTCTGACTGCAACGGGCAATATGTCTCTGTGTGGATTAAAAAAAGAGTGTCTGATAGCAGC",
        "example_output": "20 12 17 21",
        "test_cases": [
            {"input": "AGCTTTTCATTCTGACTGCAACGGGCAATATGTCTCTGTGTGGATTAAAAAAAGAGTGTCTGATAGCAGC", "expected": "20 12 17 21"},
            {"input": "AAAA", "expected": "4 0 0 0"},
            {"input": "ACGTACGT", "expected": "2 2 2 2"},
        ],
        "hint": "Use Python's str.count() method for each base.",
        "difficulty": "Easy",
        "xp": 20,
    },
    {
        "id": "reverse_complement",
        "title": "🔄 Reverse Complement",
        "description": (
            "Given a DNA string, output its reverse complement.\n\n"
            "**Input:** A DNA string s\n"
            "**Output:** The reverse complement of s."
        ),
        "example_input": "AAAACCCGGT",
        "example_output": "ACCGGGTTTT",
        "test_cases": [
            {"input": "AAAACCCGGT", "expected": "ACCGGGTTTT"},
            {"input": "ATGC", "expected": "GCAT"},
            {"input": "ACGT", "expected": "ACGT"},
        ],
        "hint": "Complement: A↔T, C↔G. Then reverse the string.",
        "difficulty": "Easy",
        "xp": 20,
    },
    {
        "id": "gc_content",
        "title": "📊 GC Content Calculator",
        "description": (
            "Given a DNA string, calculate the GC content as a percentage.\n\n"
            "**Input:** A DNA string s\n"
            "**Output:** GC content as a percentage rounded to 6 decimal places."
        ),
        "example_input": "AGCTATAG",
        "example_output": "37.500000",
        "test_cases": [
            {"input": "AGCTATAG", "expected": "37.500000"},
            {"input": "AAAA", "expected": "0.000000"},
            {"input": "GCGC", "expected": "100.000000"},
        ],
        "hint": "GC% = (count of G + count of C) / length × 100",
        "difficulty": "Easy",
        "xp": 20,
    },
    {
        "id": "rna_splicing",
        "title": "✂️ Remove Introns",
        "description": (
            "Given a DNA string and a set of intron substrings, remove all intron occurrences "
            "from the DNA and transcribe the remaining exons into RNA.\n\n"
            "**Input:** DNA string on line 1, introns on subsequent lines.\n"
            "**Output:** RNA string (DNA→RNA: T→U) after removing introns."
        ),
        "example_input": "ATGCATGC\nATGC",
        "example_output": "",
        "test_cases": [
            {"input": "ATGCATGC\nATGC", "expected": ""},
            {"input": "AUGCAUGC\nAUGC", "expected": ""},
            {"input": "ATGCGATCG\nGC", "expected": "AUAU"},
        ],
        "hint": "Remove all occurrences of each intron (in order), then transcribe T→U.",
        "difficulty": "Medium",
        "xp": 30,
    },
    {
        "id": "hamming_distance",
        "title": "📏 Hamming Distance",
        "description": (
            "Given two DNA strings of equal length, compute their Hamming distance "
            "(number of positions where the characters differ).\n\n"
            "**Input:** Two DNA strings s and t (one per line)\n"
            "**Output:** The Hamming distance (integer)."
        ),
        "example_input": "GAGCCTACTAACGGGAT\nCATCGTAATGACGGCCT",
        "example_output": "7",
        "test_cases": [
            {"input": "GAGCCTACTAACGGGAT\nCATCGTAATGACGGCCT", "expected": "7"},
            {"input": "AAAA\nTTTT", "expected": "4"},
            {"input": "ATGC\nATGC", "expected": "0"},
        ],
        "hint": "Compare characters at each position and count mismatches.",
        "difficulty": "Medium",
        "xp": 30,
    },
]


def _get_week_seed() -> int:
    """Deterministic seed based on the current ISO week."""
    today = date.today()
    return today.isocalendar()[1] + today.year * 52


def _get_current_problem() -> dict:
    """Select the problem for this week (rotating)."""
    seed = _get_week_seed()
    random.seed(seed)
    return random.choice(PROBLEMS)


# ── Session state ────────────────────────────────────────────────────────────
if "challenge_submitted" not in st.session_state:
    st.session_state["challenge_submitted"] = False
if "challenge_result" not in st.session_state:
    st.session_state["challenge_result"] = None
if "challenge_leaderboard" not in st.session_state:
    st.session_state["challenge_leaderboard"] = []

problem = _get_current_problem()

# ── Problem display ──────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(f"### {problem['title']}")
    diff_emoji = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}
    st.caption(f"{diff_emoji.get(problem['difficulty'], '🟢')} {problem['difficulty']} | ⚡ {problem['xp']} XP")
    st.markdown(t(problem["description"]))

    with st.expander(t("📝 Example")):
        st.code(f"Input:\n{problem['example_input']}\n\nOutput:\n{problem['example_output']}")

    with st.expander(t("💡 Hint")):
        st.info(t(problem["hint"]))

# ── Answer submission ────────────────────────────────────────────────────────
st.markdown("---")
name = st.text_input(t("Your name:"), placeholder="Student_42", key="challenge_name")

answer = st.text_area(
    t("Your answer (one output per test case, one per line):"),
    height=120,
    placeholder="Enter your answers, one per line...",
    key="challenge_answer",
)

if st.button(t("📤 Submit Solution"), type="primary", use_container_width=True) and answer.strip():
    lines = [l.strip() for l in answer.strip().split("\n") if l.strip()]
    test_cases = problem["test_cases"]
    correct = 0
    total = len(test_cases)

    results = []
    for i, tc in enumerate(test_cases):
        expected = tc["expected"]
        got = lines[i] if i < len(lines) else ""
        is_correct = got == expected
        correct += int(is_correct)
        results.append({"case": i + 1, "expected": expected, "got": got, "pass": is_correct})

    score = int(correct / total * problem["xp"])
    st.session_state["challenge_submitted"] = True
    st.session_state["challenge_result"] = {
        "correct": correct, "total": total, "score": score, "results": results,
    }

    # Add to leaderboard
    entry_name = name.strip() or "Anonymous"
    st.session_state["challenge_leaderboard"].append({
        "name": entry_name, "score": score, "correct": correct, "total": total,
    })

# ── Results ──────────────────────────────────────────────────────────────────
if st.session_state["challenge_result"]:
    result = st.session_state["challenge_result"]
    st.markdown("### 📊 Results")
    for r in result["results"]:
        if r["pass"]:
            st.success(t("Test case {n}: ✅ Correct! ({got})", n=r["case"], got=r["got"]))
        else:
            st.error(t("Test case {n}: ❌ Expected `{expected}`, got `{got}`", n=r["case"], expected=r["expected"], got=r["got"]))

    st.metric(t("Score"), f"{result['score']}/{problem['xp']} XP")

    # Share text
    share = f"⚡ I scored {result['correct']}/{result['total']} on this week's Titan Bioinformatics Challenge! Can you beat me? 🧬"
    st.code(share)

    if st.button(t("🔄 Try Again")):
        st.session_state["challenge_submitted"] = False
        st.session_state["challenge_result"] = None
        st.rerun()

# ── Leaderboard ──────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader(t("🏅 Leaderboard"))
lb = st.session_state["challenge_leaderboard"]
if lb:
    lb_sorted = sorted(lb, key=lambda x: x["score"], reverse=True)
    for i, entry in enumerate(lb_sorted[:10], 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
        st.markdown(f"{medal} **{entry['name']}** — {entry['score']} XP ({entry['correct']}/{entry['total']})")
else:
    st.info(t("No submissions yet. Be the first!"))

dr_titan_tip(
    "Practice on Rosalind.info to build real bioinformatics programming skills! "
    "Each problem teaches you a core concept — from counting nucleotides to genome assembly."
)