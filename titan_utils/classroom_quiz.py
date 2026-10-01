"""Ephemeral classroom MCQ engine shared by the Streamlit quiz page.

The question bank is compiled into the package and works offline. A tiny,
bounded, in-process room registry is needed to synchronize separate
Streamlit browser sessions (for example, a teacher's laptop and students'
phones); it expires automatically and is never written to disk or a database.
Per-browser identity/profile is stored by the page in Streamlit session state
and browser localStorage.
"""
from __future__ import annotations

import hashlib
import random
import threading
import time
import unicodedata
from dataclasses import dataclass
from typing import Any

from titan_utils.olympiad import TIER_XP

__all__ = [
    "CLASSROOM_QUESTION_BANK",
    "MAX_ACTIVE_ROOMS",
    "MAX_STUDENTS_PER_ROOM",
    "ROOM_TTL_SECONDS",
    "MCQ",
    "create_session_code",
    "resolve_topic",
    "generate_quiz",
    "create_classroom",
    "join_classroom",
    "get_classroom",
    "get_student_progress",
    "get_leaderboard",
    "submit_answer",
    "close_classroom",
    "reset_classrooms",
]

MAX_ACTIVE_ROOMS = 128
MAX_STUDENTS_PER_ROOM = 200
ROOM_TTL_SECONDS = 6 * 60 * 60
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CLASSROOM_XP_PER_CORRECT_ANSWER = TIER_XP["Foundational"]


@dataclass(frozen=True)
class MCQ:
    """One built-in, educational multiple-choice question."""

    id: str
    topic: str
    question: str
    options: tuple[str, str, str, str]
    correct_index: int
    explanation: str

    def as_dict(self, *, include_answer: bool = False) -> dict[str, Any]:
        item: dict[str, Any] = {
            "id": self.id,
            "topic": self.topic,
            "question": self.question,
            "options": list(self.options),
            "explanation": self.explanation,
        }
        if include_answer:
            item["correct_index"] = self.correct_index
        return item


def _q(
    question_id: str,
    topic: str,
    question: str,
    options: tuple[str, str, str, str],
    correct_index: int,
    explanation: str,
) -> MCQ:
    return MCQ(question_id, topic, question, options, correct_index, explanation)


# Exactly five questions per topic keeps each room compact and predictable.
# They are authored from the suite's built-in student-learning content.
CLASSROOM_QUESTION_BANK: dict[str, tuple[MCQ, ...]] = {
    "CRISPR-Cas9": (
        _q("crispr-1", "CRISPR-Cas9", "Which PAM is required by SpCas9?", ("NGG", "TATA", "AUG", "CCAAT"), 0, "SpCas9 recognizes an NGG PAM next to its target."),
        _q("crispr-2", "CRISPR-Cas9", "What does the guide RNA do?", ("Guides Cas9 to a matching DNA target", "Repairs every DNA break", "Copies DNA into protein", "Removes all PAM sites"), 0, "The guide sequence base-pairs with the target DNA near a compatible PAM."),
        _q("crispr-3", "CRISPR-Cas9", "What is Cas9's main molecular role?", ("DNA nuclease that cuts DNA", "RNA polymerase", "Ribosomal subunit", "DNA stain"), 0, "Cas9 is an RNA-guided endonuclease."),
        _q("crispr-4", "CRISPR-Cas9", "Which repair pathway often creates small insertions or deletions?", ("Non-homologous end joining (NHEJ)", "Base pairing", "Transcription", "Translation"), 0, "NHEJ can rejoin a break imperfectly, producing indels."),
        _q("crispr-5", "CRISPR-Cas9", "Which pathway can copy a supplied repair template?", ("Homology-directed repair (HDR)", "NHEJ only", "Reverse transcription", "RNA splicing"), 0, "HDR uses a homologous template and can introduce a planned edit."),
    ),
    "GC Content": (
        _q("gc-1", "GC Content", "How is GC percentage calculated for an unambiguous DNA sequence?", ("(G + C) / sequence length × 100", "(A + T) / 3", "G × C only", "sequence length / 100"), 0, "Count G and C bases, divide by sequence length, and multiply by 100."),
        _q("gc-2", "GC Content", "Which base pair has three hydrogen bonds?", ("G–C", "A–T", "A–C", "G–T"), 0, "A G–C pair forms three hydrogen bonds; A–T forms two."),
        _q("gc-3", "GC Content", "All else being equal, what often happens as GC content rises?", ("DNA melting temperature tends to rise", "DNA length becomes zero", "All genes stop translating", "The sequence becomes RNA"), 0, "GC-rich duplexes are generally more thermally stable, though sequence context also matters."),
        _q("gc-4", "GC Content", "What does a sliding-window GC plot show?", ("Local GC variation along a sequence", "Protein molecular weight", "The number of chromosomes", "Only the sequence name"), 0, "A sliding window reports GC content for successive local sequence regions."),
        _q("gc-5", "GC Content", "What GC percentage does a sequence with 5 G/C bases out of 10 have?", ("50%", "5%", "10%", "100%"), 0, "Five divided by ten and multiplied by 100 equals 50%."),
    ),
    "DNA": (
        _q("dna-1", "DNA", "Which bases pair in standard double-stranded DNA?", ("A–T and G–C", "A–C and G–T", "A–G and C–T", "A–U and G–C"), 0, "Watson–Crick DNA pairing is A with T and G with C."),
        _q("dna-2", "DNA", "Which base is found in DNA instead of RNA?", ("Thymine (T)", "Uracil (U)", "Both are absent", "Ribose"), 0, "DNA uses thymine; RNA generally uses uracil in its place."),
        _q("dna-3", "DNA", "What is a reverse complement?", ("The reverse-order complementary DNA strand", "A protein sequence", "A list of codon frequencies", "A DNA length measurement"), 0, "It complements each base and reverses the strand to write it 5′ to 3′."),
        _q("dna-4", "DNA", "What is the usual direction used to write a DNA sequence?", ("5′ to 3′", "3′ to 5′ only", "Nucleus to cytoplasm", "There is no direction"), 0, "Nucleic acid sequences are conventionally represented 5′ to 3′."),
        _q("dna-5", "DNA", "Which set contains only the four standard DNA bases?", ("A, C, G, T", "A, C, G, U", "A, T, U, X", "C, G, U, Y"), 0, "The four standard DNA bases are adenine, cytosine, guanine, and thymine."),
    ),
    "PCR": (
        _q("pcr-1", "PCR", "What happens during PCR denaturation?", ("The DNA strands separate", "Primers are removed", "Proteins translate RNA", "DNA is stained"), 0, "High temperature separates the double-stranded DNA template."),
        _q("pcr-2", "PCR", "What binds to the template during annealing?", ("Primers", "Ribosomes", "PAM sequences", "Antibodies"), 0, "Primers anneal to complementary flanking regions of the target."),
        _q("pcr-3", "PCR", "What does DNA polymerase do in the extension step?", ("Synthesizes new DNA strands", "Separates chromosomes", "Turns DNA into amino acids", "Cuts the primers"), 0, "A thermostable polymerase extends each primer by adding nucleotides."),
        _q("pcr-4", "PCR", "Why is Taq polymerase useful in standard PCR?", ("It tolerates repeated high-temperature cycles", "It replaces primers", "It binds every PAM", "It is a type of RNA"), 0, "Taq is thermostable and remains active through repeated denaturation steps."),
        _q("pcr-5", "PCR", "What is the main role of PCR primers?", ("Define the region to be amplified and provide a starting point", "Digest the whole genome", "Translate DNA to protein", "Measure GC content"), 0, "Primers define the amplicon boundaries and provide a free end for polymerase."),
    ),
    "Central Dogma": (
        _q("dogma-1", "Central Dogma", "What is the name for making RNA from a DNA template?", ("Transcription", "Translation", "Replication", "Splicing"), 0, "RNA polymerase transcribes DNA into RNA."),
        _q("dogma-2", "Central Dogma", "What is the name for making a protein from an mRNA message?", ("Translation", "Transcription", "Replication", "Annealing"), 0, "Ribosomes translate mRNA codons into an amino-acid chain."),
        _q("dogma-3", "Central Dogma", "How many nucleotides are in a standard codon?", ("Three", "One", "Two", "Six"), 0, "A codon is a three-nucleotide unit read during translation."),
        _q("dogma-4", "Central Dogma", "Which molecule reads mRNA codons during translation?", ("Ribosome", "Cas9", "DNA ligase", "Restriction enzyme"), 0, "Ribosomes coordinate codon reading and peptide-bond formation."),
        _q("dogma-5", "Central Dogma", "Which base is used in RNA where DNA uses thymine?", ("Uracil (U)", "Guanine (G)", "Cytosine (C)", "Adenine (A)"), 0, "RNA uses uracil rather than thymine."),
    ),
    "Bioinformatics Foundations": (
        _q("bio-1", "Bioinformatics Foundations", "Which file format uses a '>' line to introduce a sequence record?", ("FASTA", "FASTQ", "VCF", "PDB"), 0, "A FASTA record begins with a '>' header line."),
        _q("bio-2", "Bioinformatics Foundations", "What extra information does FASTQ store for each read?", ("Per-base quality scores", "Protein 3D coordinates", "Only gene names", "A PAM for each base"), 0, "FASTQ pairs each sequence with encoded base-call quality scores."),
        _q("bio-3", "Bioinformatics Foundations", "What does GC content summarize?", ("The fraction of G and C bases", "The number of proteins", "A sequence's file size", "A read's quality score only"), 0, "GC content is the proportion of guanine and cytosine nucleotides."),
        _q("bio-4", "Bioinformatics Foundations", "What is a motif search used to find?", ("Occurrences of a short sequence pattern", "The mass of a protein", "A file's path", "A cell's temperature"), 0, "Motif searches locate recurring short patterns in biological sequences."),
        _q("bio-5", "Bioinformatics Foundations", "What does SHA-256 provenance provide?", ("A digest for integrity checking", "A DNA repair enzyme", "A sequence alignment", "A protein translation"), 0, "A SHA-256 digest can verify content integrity without retaining the content."),
    ),
}

_TOPIC_ALIASES = {
    "crispr": "CRISPR-Cas9",
    "cas9": "CRISPR-Cas9",
    "gc": "GC Content",
    "gc content": "GC Content",
    "melting temperature": "GC Content",
    "dna": "DNA",
    "reverse complement": "DNA",
    "complement": "DNA",
    "pcr": "PCR",
    "primer": "PCR",
    "central dogma": "Central Dogma",
    "transcription": "Central Dogma",
    "translation": "Central Dogma",
}


def resolve_topic(topic: str) -> tuple[str, bool]:
    """Map a teacher topic to built-in content; unknown topics use foundations."""
    cleaned = " ".join(str(topic or "").split())[:80]
    if not cleaned:
        raise ValueError("Enter a classroom topic, such as CRISPR or DNA.")
    lower = cleaned.casefold()
    # Prefer the most specific alias if the teacher enters a longer phrase.
    for alias in sorted(_TOPIC_ALIASES, key=len, reverse=True):
        if alias in lower:
            return _TOPIC_ALIASES[alias], True
    return "Bioinformatics Foundations", False


def generate_quiz(topic: str) -> tuple[MCQ, ...]:
    """Return five offline MCQs with reproducibly mixed answer positions.

    A private ``random.Random(42)`` keeps option order deterministic across
    runs/tests while avoiding the predictable pattern of every answer being A.
    """
    resolved, _matched = resolve_topic(topic)
    bank_questions = CLASSROOM_QUESTION_BANK[resolved]
    if len(bank_questions) != 5 or any(len(q.options) != 4 for q in bank_questions):
        raise RuntimeError("The built-in classroom bank must contain five four-option MCQs.")
    rng = random.Random(42)
    answer_positions = list(range(4))
    rng.shuffle(answer_positions)
    questions = []
    for question_index, question in enumerate(bank_questions):
        correct_option = question.options[question.correct_index]
        distractors = [
            option for index, option in enumerate(question.options)
            if index != question.correct_index
        ]
        rng.shuffle(distractors)
        shuffled_answer = answer_positions[question_index % len(answer_positions)]
        shuffled = list(distractors)
        shuffled.insert(shuffled_answer, correct_option)
        questions.append(MCQ(
            id=question.id,
            topic=question.topic,
            question=question.question,
            options=tuple(shuffled),  # type: ignore[arg-type]
            correct_index=shuffled_answer,
            explanation=question.explanation,
        ))
    return tuple(questions)


def create_session_code(topic: str, nonce: str | int) -> str:
    """Create a four-character, deterministic room code without RNG state."""
    digest = hashlib.sha256(f"{topic.strip().casefold()}|{nonce}".encode("utf-8")).digest()
    return "".join(_CODE_ALPHABET[byte & 31] for byte in digest[:4])


def _normalise_name(name: str) -> tuple[str, str]:
    display = unicodedata.normalize("NFKC", str(name or ""))
    display = "".join(ch for ch in display if not unicodedata.category(ch).startswith("C"))
    display = " ".join(display.split())[:32]
    if not display:
        raise ValueError("Enter a student name or classroom nickname.")
    return display.casefold(), display


_ROOMS: dict[str, dict[str, Any]] = {}
_ROOM_LOCK = threading.RLock()


def _cleanup_rooms(now: float) -> None:
    expired = [
        code for code, room in _ROOMS.items()
        if now - room["created_at"] > ROOM_TTL_SECONDS
    ]
    for code in expired:
        _ROOMS.pop(code, None)
    while len(_ROOMS) > MAX_ACTIVE_ROOMS:
        oldest = min(_ROOMS, key=lambda code: _ROOMS[code]["created_at"])
        _ROOMS.pop(oldest, None)


def _room_snapshot(room: dict[str, Any], *, include_answers: bool = False) -> dict[str, Any]:
    students = []
    for student in room["students"].values():
        item = {
            "name": student["name"],
            "xp": student["xp"],
            "correct": student["correct"],
            "answered": len(student["answers"]),
            "complete": len(student["answers"]) == len(room["questions"]),
        }
        if include_answers:
            item["answers"] = {
                str(index): {"correct": answer["correct"], "xp_earned": answer["xp_earned"]}
                for index, answer in student["answers"].items()
            }
        students.append(item)
    students.sort(key=lambda item: (-item["xp"], -item["correct"], item["name"].casefold()))
    return {
        "code": room["code"],
        "topic": room["topic"],
        "student_limit": room["student_limit"],
        "status": room["status"],
        "created_at": room["created_at"],
        "question_count": len(room["questions"]),
        "questions": [question.as_dict() for question in room["questions"]],
        "students": students,
        "joined_count": len(students),
        "leaderboard": [
            {"rank": index, **student}
            for index, student in enumerate(students, start=1)
        ],
    }


def create_classroom(topic: str, student_limit: int, *, now: float | None = None) -> dict[str, Any]:
    """Create a bounded ephemeral room and return a public snapshot."""
    resolved, _matched = resolve_topic(topic)
    try:
        count = int(student_limit)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Student count must be between 1 and {MAX_STUDENTS_PER_ROOM}.") from exc
    if (
        isinstance(student_limit, bool)
        or count != student_limit
        or not 1 <= count <= MAX_STUDENTS_PER_ROOM
    ):
        raise ValueError(f"Student count must be between 1 and {MAX_STUDENTS_PER_ROOM}.")
    created_at = float(now if now is not None else time.time())
    nonce = str(int(created_at * 1_000_000_000))
    with _ROOM_LOCK:
        _cleanup_rooms(created_at)
        for attempt in range(MAX_ACTIVE_ROOMS + 1):
            code = create_session_code(resolved, f"{nonce}:{attempt}")
            if code not in _ROOMS:
                break
        else:  # pragma: no cover - bounded collision fallback
            raise RuntimeError("Could not allocate a unique classroom code.")
        questions = generate_quiz(resolved)
        _ROOMS[code] = {
            "code": code,
            "topic": resolved,
            "student_limit": count,
            "status": "active",
            "created_at": created_at,
            "questions": questions,
            "students": {},
        }
        _cleanup_rooms(created_at)
        return _room_snapshot(_ROOMS[code])


def _find_room(code: str, now: float | None = None) -> dict[str, Any] | None:
    selected = str(code or "").strip().upper()
    current_time = float(now if now is not None else time.time())
    _cleanup_rooms(current_time)
    return _ROOMS.get(selected)


def get_classroom(code: str, *, now: float | None = None) -> dict[str, Any] | None:
    """Return a copy-safe room snapshot, or ``None`` for an unknown/expired code."""
    with _ROOM_LOCK:
        room = _find_room(code, now=now)
        return _room_snapshot(room) if room else None


def join_classroom(code: str, name: str, *, now: float | None = None) -> dict[str, Any]:
    """Join a room by code and nickname; no account or personal data required."""
    student_key, display_name = _normalise_name(name)
    with _ROOM_LOCK:
        room = _find_room(code, now=now)
        if not room:
            raise ValueError("Classroom code not found or expired. Check the four-character code.")
        if room["status"] != "active":
            raise ValueError("This classroom is closed to new answers.")
        if student_key not in room["students"]:
            if len(room["students"]) >= room["student_limit"]:
                raise ValueError("This classroom has reached its student limit.")
            room["students"][student_key] = {
                "name": display_name,
                "xp": 0,
                "correct": 0,
                "answers": {},
            }
        return {
            "room": _room_snapshot(room),
            "student": {
                "name": room["students"][student_key]["name"],
                "xp": room["students"][student_key]["xp"],
                "correct": room["students"][student_key]["correct"],
                "answered": len(room["students"][student_key]["answers"]),
            },
        }


def get_student_progress(code: str, name: str, *, now: float | None = None) -> dict[str, Any] | None:
    """Get one participant's answers and public quiz after joining."""
    try:
        student_key, _display = _normalise_name(name)
    except ValueError:
        return None
    with _ROOM_LOCK:
        room = _find_room(code, now=now)
        if not room or student_key not in room["students"]:
            return None
        student = room["students"][student_key]
        return {
            "room": _room_snapshot(room),
            "student": {
                "name": student["name"],
                "xp": student["xp"],
                "correct": student["correct"],
                "answered": len(student["answers"]),
                "answers": {
                    index: dict(answer)
                    for index, answer in student["answers"].items()
                },
            },
        }


def get_leaderboard(code: str, *, now: float | None = None) -> list[dict[str, Any]]:
    """Return rank, nickname, score, and Arena-compatible XP for a room."""
    room = get_classroom(code, now=now)
    return room["leaderboard"] if room else []


def submit_answer(
    code: str,
    name: str,
    question_index: int,
    choice_index: int,
    *,
    now: float | None = None,
) -> dict[str, Any]:
    """Record one answer, award Foundational Arena XP once, and return feedback."""
    student_key, _display = _normalise_name(name)
    if isinstance(question_index, bool) or isinstance(choice_index, bool):
        raise ValueError("Choose one of the listed answer options.")
    try:
        question_index, choice_index = int(question_index), int(choice_index)
    except (TypeError, ValueError) as exc:
        raise ValueError("Choose one of the listed answer options.") from exc
    with _ROOM_LOCK:
        room = _find_room(code, now=now)
        if not room:
            raise ValueError("Classroom code not found or expired.")
        if room["status"] != "active":
            raise ValueError("This classroom is closed.")
        student = room["students"].get(student_key)
        if not student:
            raise ValueError("Join the classroom before answering.")
        if not 0 <= question_index < len(room["questions"]):
            raise ValueError("Question number is out of range.")
        if not 0 <= choice_index < 4:
            raise ValueError("Choose one of the four answer options.")
        if question_index in student["answers"]:
            return {
                "accepted": False,
                "already_answered": True,
                "correct": student["answers"][question_index]["correct"],
                "xp_earned": 0,
                "score": student["xp"],
            }
        if question_index != len(student["answers"]):
            raise ValueError("Answer the quiz questions in order.")
        question = room["questions"][question_index]
        correct = choice_index == question.correct_index
        earned = CLASSROOM_XP_PER_CORRECT_ANSWER if correct else 0
        student["answers"][question_index] = {
            "choice_index": choice_index,
            "correct": correct,
            "xp_earned": earned,
        }
        student["xp"] += earned
        student["correct"] += int(correct)
        return {
            "accepted": True,
            "already_answered": False,
            "correct": correct,
            "xp_earned": earned,
            "score": student["xp"],
            "correct_index": question.correct_index,
            "explanation": question.explanation,
        }


def close_classroom(code: str, *, now: float | None = None) -> bool:
    """Close a room to new joins/submissions while keeping its score visible."""
    with _ROOM_LOCK:
        room = _find_room(code, now=now)
        if not room:
            return False
        room["status"] = "closed"
        return True


def reset_classrooms() -> None:
    """Clear process-local room memory (test helper and local admin utility)."""
    with _ROOM_LOCK:
        _ROOMS.clear()
