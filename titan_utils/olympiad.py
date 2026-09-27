"""Gamified Bio-Olympiad & Rosalind practice arena engine.

Multi-tier bioinformatics challenges (Foundational → Intermediate →
Olympiad) with **instant algorithmic grading**, XP scoring, solution
walkthroughs, and **Groq Llama-8B hints** (network-optional: when no
``GROQ_API_KEY`` is configured the arena serves rich local hints so the
suite stays fully offline-capable and Zero Data Retention compliant).

Challenge set mirrors classic Rosalind-textbook problems: nucleotide
counting, transcription, reverse complement, Hamming distance, Mendelian
dominance, Fibonacci models, protein translation, motif discovery,
consensus profiles, edit distance and ORF finding.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "TIERS",
    "TIER_XP",
    "Challenge",
    "GradeResult",
    "CHALLENGES",
    "CHALLENGES_BY_ID",
    "list_challenges",
    "get_challenge",
    "grade_attempt",
    "groq_llama_hint",
    "get_hint",
    "total_xp",
    "tier_progress",
]

TIERS: Tuple[str, ...] = ("Foundational", "Intermediate", "Olympiad")
TIER_XP: Dict[str, int] = {"Foundational": 50, "Intermediate": 100, "Olympiad": 200}

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # Groq-hosted Llama 8B


# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Challenge:
    """One graded practice problem."""

    id: str
    title: str
    tier: str
    topic: str
    prompt: str
    sample_input: str
    sample_output: str
    solver: Callable[[str], str]
    hint: str
    explanation: str
    solution_steps: Tuple[str, ...] = ()

    @property
    def xp(self) -> int:
        return TIER_XP.get(self.tier, 50)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "tier": self.tier,
            "topic": self.topic,
            "xp": self.xp,
            "prompt": self.prompt,
            "sample_input": self.sample_input,
            "sample_output": self.sample_output,
            "hint": self.hint,
        }


@dataclass
class GradeResult:
    """Instant grading feedback for one attempt."""

    challenge_id: str
    title: str
    tier: str
    correct: bool
    xp_earned: int
    expected: str
    submitted: str
    feedback: str
    method: str = "exact-match (whitespace-normalised)"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "title": self.title,
            "tier": self.tier,
            "correct": self.correct,
            "xp_earned": self.xp_earned,
            "feedback": self.feedback,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Canonical solvers (also power the auto-grader's expected outputs)
# ─────────────────────────────────────────────────────────────────────────────

def _norm_seq(s: str) -> str:
    return re.sub(r"\s+", "", s or "").upper()


def _solve_dna(s: str) -> str:
    s = _norm_seq(s)
    return f"{s.count('A')} {s.count('C')} {s.count('G')} {s.count('T')}"


def _solve_rna(s: str) -> str:
    return _norm_seq(s).replace("T", "U")


def _solve_revc(s: str) -> str:
    comp = {"A": "T", "T": "A", "G": "C", "C": "G"}
    s = _norm_seq(s)
    return "".join(comp.get(b, "N") for b in reversed(s))


def _solve_hamm(s: str) -> str:
    parts = [p for p in re.split(r"\s+", (s or "").strip()) if p]
    if len(parts) < 2:
        return "0"
    a, b = parts[0].upper(), parts[1].upper()
    return str(sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b)))


def _solve_gc(s: str) -> str:
    best_id, best_gc = "", -1.0
    records = _parse_fasta(s)
    for header, seq in records:
        seq = _norm_seq(seq)
        if not seq:
            continue
        gc = 100.0 * (seq.count("G") + seq.count("C")) / len(seq)
        if gc > best_gc:
            best_id, best_gc = header, gc
    return f"{best_id}\n{best_gc:.6f}"


def _solve_fib(s: str) -> str:
    parts = [int(p) for p in re.findall(r"\d+", s or "")]
    n = parts[0] if parts else 5
    k = parts[1] if len(parts) > 1 else 3
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, b + k * a
    return str(a)


def _solve_iprb(s: str) -> str:
    parts = [int(p) for p in re.findall(r"\d+", s or "")]
    k, m, n = (parts + [2, 2, 2])[:3]
    total = k + m + n
    if total < 2:
        return "1.00000"
    pairs = total * (total - 1) / 2.0
    favourable = (
        k * (k - 1) / 2.0 * 1.0      # AA x AA
        + k * m * 1.0                 # AA x Aa
        + k * n * 1.0                 # AA x aa
        + m * (m - 1) / 2.0 * 0.75    # Aa x Aa -> 3/4
        + m * n * 0.5                 # Aa x aa -> 1/2
    )
    return f"{favourable / pairs:.5f}"


def _solve_prot(s: str) -> str:
    from titan_utils.sequence import translate

    return translate(_norm_seq(s).replace("U", "T"), to_stop=True)


def _solve_subs(s: str) -> str:
    parts = [p for p in re.split(r"\s+", (s or "").strip()) if p]
    if len(parts) < 2:
        return ""
    text, motif = parts[0].upper(), parts[1].upper()
    return " ".join(str(m.start() + 1) for m in re.finditer(f"(?={re.escape(motif)})", text))


def _solve_cons(s: str) -> str:
    records = _parse_fasta(s)
    seqs = [_norm_seq(seq) for _, seq in records if _norm_seq(seq)]
    if not seqs:
        return ""
    length = max(len(x) for x in seqs)
    profile = {b: [0] * length for b in "ACGT"}
    for seq in seqs:
        for i, ch in enumerate(seq):
            if ch in profile:
                profile[ch][i] += 1
    consensus = ""
    for i in range(length):
        consensus += max("ACGT", key=lambda b: profile[b][i])
    lines = [consensus]
    for b in "ACGT":
        lines.append(f"{b}: " + " ".join(str(c) for c in profile[b]))
    return "\n".join(lines)


def _solve_edit(s: str) -> str:
    parts = [p for p in re.split(r"\s+", (s or "").strip()) if p]
    if len(parts) < 2:
        return "0"
    a, b = parts[0].upper(), parts[1].upper()
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return str(prev[-1])


def _solve_orf(s: str) -> str:
    from titan_utils.sequence import find_orfs_simple, translate

    s = _norm_seq(s)
    proteins = set()
    for orf in find_orfs_simple(s, min_len=0):
        prot = translate(orf.get("DNA_Sequence", ""), to_stop=True)
        if prot and prot.startswith("M"):
            proteins.add(prot)
    return "\n".join(sorted(proteins))


def _parse_fasta(text: str) -> List[Tuple[str, str]]:
    records: List[Tuple[str, str]] = []
    header = None
    chunks: List[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append((header, "".join(chunks)))
            header = line[1:].split()[0] if line[1:].split() else f"seq_{len(records) + 1}"
            chunks = []
        else:
            if header is None:
                header = "seq_1"
            chunks.append(line)
    if header is not None:
        records.append((header, "".join(chunks)))
    return records


# ─────────────────────────────────────────────────────────────────────────────
# Challenge bank
# ─────────────────────────────────────────────────────────────────────────────

CHALLENGES: List[Challenge] = [
    Challenge(
        id="DNA",
        title="Counting DNA Nucleotides",
        tier="Foundational",
        topic="DNA composition",
        prompt=(
            "Given a DNA string of length ≤ 1000, return four integers: the "
            "number of times A, C, G, T occur (space-separated, in that order)."
        ),
        sample_input="AGCTTTTCATTCTGACTGCAACGGGCAATATGTCTCTGTGTGGATTAAAAAAAGAGTGTCTGATAGCAGC",
        sample_output="20 12 17 21",
        solver=_solve_dna,
        hint="Walk the string once and keep four counters — A, C, G, T — then print them in the order A C G T.",
        explanation="Nucleotide frequency tables are the most basic descriptive statistic of a sequence.",
        solution_steps=(
            "Initialise count[A] = count[C] = count[G] = count[T] = 0.",
            "For each character, increment the matching counter.",
            "Print counts separated by spaces: A C G T.",
        ),
    ),
    Challenge(
        id="RNA",
        title="Transcribing DNA into RNA",
        tier="Foundational",
        topic="Transcription",
        prompt="Given a DNA string, transcribe it to RNA by replacing every T with U. Return the RNA string.",
        sample_input="GATGGAACTTGACTACGTAAATT",
        sample_output="GAUGGAACUUGACUACGUAAAUU",
        solver=_solve_rna,
        hint="RNA uses Uracil instead of Thymine — a single character replacement does the whole job.",
        explanation="RNA polymerase substitutes U for T during transcription; string replace models it exactly.",
        solution_steps=("Replace every 'T' with 'U'.", "Return the result — nothing else changes."),
    ),
    Challenge(
        id="REVC",
        title="Complementing a Strand of DNA",
        tier="Foundational",
        topic="Reverse complement",
        prompt=(
            "Given a DNA string, return its reverse complement: reverse the "
            "string and swap A<->T, G<->C."
        ),
        sample_input="AAAACCCGGT",
        sample_output="ACCGGGTTTT",
        solver=_solve_revc,
        hint="Reverse first, then complement each base (or complement then reverse — same result).",
        explanation="The reverse complement is how the antiparallel partner strand is written 5'→3'.",
        solution_steps=("Build a complement map A→T, T→A, G→C, C→G.", "Reverse the string.", "Map every character through the complement."),
    ),
    Challenge(
        id="HAMM",
        title="Counting Point Mutations (Hamming Distance)",
        tier="Foundational",
        topic="Mutations",
        prompt="Given two equal-length DNA strings, return the Hamming distance — the number of positions where they differ.",
        sample_input="GAGCCTACTAACGGGAT\nCATCGTAATGACGGCCT",
        sample_output="7",
        solver=_solve_hamm,
        hint="Zip both strings together and count pairs that differ.",
        explanation="Hamming distance quantifies point substitutions between aligned sequences.",
        solution_steps=("Align the strings position by position.", "Count mismatched positions.", "Return the count."),
    ),
    Challenge(
        id="GC",
        title="Computing GC Content",
        tier="Foundational",
        topic="Sequence statistics",
        prompt=(
            "Given a multi-FASTA collection, return the ID of the record with "
            "the highest GC content and its GC percentage (6 decimal places)."
        ),
        sample_input=">Rosalind_6404\nCCTGCGGAAGATCGGCACTAGAATAGCCAGAACCGTTTCTCTGAGGCTTCCGGCCTTCCC\n>Rosalind_5959\nCCATCGGTAGCGCATCCTTAGTCTTTGTGCAAGCAGTAACGATTCTGACATCGGTACGG\n>Rosalind_0808\nCCACCCTCGTGGTATGGCTAGGCATTCAGGAACCGGAGAACGCTTCAGACCAGCCCGGA",
        sample_output="Rosalind_0808\n61.016949",
        solver=_solve_gc,
        hint="For each FASTA record compute 100 * (G + C) / length and track the maximum.",
        explanation="GC content reflects duplex stability and varies across genomes and genes.",
        solution_steps=("Parse the FASTA records.", "GC% = 100 × (G + C) / length per record.", "Print the best ID and its GC% to 6 decimals."),
    ),
    Challenge(
        id="FIB",
        title="Rabbits and Recurrence Relations",
        tier="Intermediate",
        topic="Population models",
        prompt=(
            "Given n (months) and k (litter size), compute the total number of "
            "rabbit pairs after n months if every pair produces k new pairs "
            "each month from its second month (classic Fibonacci model)."
        ),
        sample_input="5 3",
        sample_output="19",
        solver=_solve_fib,
        hint="F(n) = F(n-1) + k * F(n-2), starting F(1) = F(2) = 1.",
        explanation="Generalised Fibonacci recurrences model idealised population growth.",
        solution_steps=("Start with a = b = 1.", "Repeat n-1 times: a, b = b, b + k*a.", "Return a."),
    ),
    Challenge(
        id="IPRB",
        title="Mendel's First Law",
        tier="Intermediate",
        topic="Genetics",
        prompt=(
            "Given k homozygous dominant, m heterozygous, n homozygous recessive "
            "organisms, return the probability that two randomly selected "
            "organisms produce an individual with a dominant allele "
            "(rounded to 5 decimal places)."
        ),
        sample_input="2 2 2",
        sample_output="0.78333",
        solver=_solve_iprb,
        hint="Count favourable ordered pairs: AA×anything, Aa×Aa (3/4), Aa×aa (1/2).",
        explanation="This is the classic Punnett-square / hypergeometric pairing problem.",
        solution_steps=("Total pairs = C(k+m+n, 2).", "Favourable: AA pairs always, Aa×Aa 3/4, Aa×aa 1/2.", "Divide and print 5 decimals."),
    ),
    Challenge(
        id="PROT",
        title="Translating RNA into Protein",
        tier="Intermediate",
        topic="Translation",
        prompt="Given an RNA string, translate it to the protein string it encodes, stopping at (but not including) the first stop codon.",
        sample_input="AUGGCCAUGGCGCCCAGAACUGAGAUCAAUAGUACCCGUAUUAACGGGUGA",
        sample_output="MAMAPRTEINSTRING",
        solver=_solve_prot,
        hint="Read the RNA one codon (3 nt) at a time with the standard genetic code table and stop at UAA/UAG/UGA.",
        explanation="The standard genetic code maps 64 codons to 20 amino acids plus stop signals.",
        solution_steps=("Chunk the RNA into codons.", "Look up each codon in the standard table.", "Stop at the first stop codon; join amino acids."),
    ),
    Challenge(
        id="SUBS",
        title="Finding a Motif in DNA",
        tier="Intermediate",
        topic="Motifs",
        prompt=(
            "Given two DNA strings s (text) and t (motif), return all 1-based "
            "starting positions of t as a substring of s (overlaps allowed), "
            "space-separated."
        ),
        sample_input="GATATATGCATATACTT\nATAT",
        sample_output="2 4 10",
        solver=_solve_subs,
        hint="Slide a window of len(t) over s — or use lookahead regex finditer to catch overlaps.",
        explanation="Motif discovery underpins transcription-factor binding site searches.",
        solution_steps=("For i in 0..len(s)-len(t): compare s[i:i+len(t)] to t.", "Record i+1 on match.", "Print positions space-separated."),
    ),
    Challenge(
        id="CONS",
        title="Consensus and Profile Matrix",
        tier="Olympiad",
        topic="Multiple alignment",
        prompt=(
            "Given a multi-FASTA alignment of equal-length strings, return the "
            "consensus string followed by the 4×L profile matrix rows "
            "'A: …', 'C: …', 'G: …', 'T: …' (counts per column)."
        ),
        sample_input=(
            ">Rosalind_1\nATCCAGCT\n>Rosalind_2\nGGGCAACT\n"
            ">Rosalind_3\nATGGATCT\n>Rosalind_4\nAAGCAACC\n"
            ">Rosalind_5\nTTGGAACT\n>Rosalind_6\nATGCCATT\n"
            ">Rosalind_7\nATGGCACT"
        ),
        sample_output=(
            "ATGCAACT\n"
            "A: 5 1 0 0 5 5 0 0\n"
            "C: 0 0 1 4 2 0 6 1\n"
            "G: 1 1 6 3 0 1 0 0\n"
            "T: 1 5 0 0 0 1 1 6"
        ),
        solver=_solve_cons,
        hint="Per column, count A/C/G/T; consensus picks the most frequent base (ties → lexicographic first).",
        explanation="Consensus/profile matrices summarise aligned sequence families.",
        solution_steps=("Parse all aligned strings.", "Count each base per column.", "Consensus = per-column argmax; print profile rows."),
    ),
    Challenge(
        id="EDTA",
        title="Edit Distance (Alignment Score)",
        tier="Olympiad",
        topic="Alignment",
        prompt=(
            "Given two strings, compute their edit distance — the minimum "
            "number of insertions, deletions and substitutions needed to turn "
            "one into the other."
        ),
        sample_input="PLEASANTLY\nMEANLY",
        sample_output="5",
        solver=_solve_edit,
        hint="Classic dynamic programming: d[i][j] = min(d[i-1][j]+1, d[i][j-1]+1, d[i-1][j-1] + (a[i]!=b[j])).",
        explanation="Levenshtein distance is the workhorse metric of sequence alignment.",
        solution_steps=("Build the DP table with first row/column as indices.", "Fill with the min of three moves.", "Answer = bottom-right cell."),
    ),
    Challenge(
        id="ORF",
        title="Open Reading Frames",
        tier="Olympiad",
        topic="Gene finding",
        prompt=(
            "Given a DNA string, return every distinct protein string that "
            "could be translated from an ORF (ATG…stop) on either strand, "
            "one per line, sorted alphabetically."
        ),
        sample_input="AGCCATGTAGCTAACTCAGGTTACATGGGGATGACCCCGCGACTTGGATTAGAGTCTCTTTTGGAATAAGCCTGAATGATCCGAGTAGCATCTCAG",
        sample_output=(
            "M\n"
            "MGMTPRLGLESLLE\n"
            "MLLGSFRLIPKETLIQVAGSSPCNLS\n"
            "MTPRLGLESLLE"
        ),
        solver=_solve_orf,
        hint="Search both strands (and all 3 frames each) for ATG…stop; translate each ORF and dedupe.",
        explanation="ORFs are candidate coding regions — the first gene-finding heuristic ever used.",
        solution_steps=("Take the reverse complement too.", "Find ATG…in-frame stop windows in 6 frames.", "Translate, keep M-started proteins, sort & dedupe."),
    ),
]

CHALLENGES_BY_ID: Dict[str, Challenge] = {c.id: c for c in CHALLENGES}


def list_challenges(tier: Optional[str] = None) -> List[Challenge]:
    """All challenges, optionally filtered by tier."""
    if tier and tier in TIERS:
        return [c for c in CHALLENGES if c.tier == tier]
    return list(CHALLENGES)


def get_challenge(challenge_id: str) -> Challenge:
    """Look up a challenge (falls back to the first Foundational problem)."""
    return CHALLENGES_BY_ID.get(challenge_id, CHALLENGES[0])


# ─────────────────────────────────────────────────────────────────────────────
# Instant grading + XP
# ─────────────────────────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    """Whitespace- and case-insensitive canonical form for grading."""
    return re.sub(r"\s+", "", (text or "")).upper()


def grade_attempt(challenge_id: str, input_text: str, answer_text: str) -> GradeResult:
    """Grade an attempt algorithmically — exact match after normalisation."""
    ch = get_challenge(challenge_id)
    expected = ch.solver(input_text if input_text is not None else "")
    submitted = (answer_text or "").strip()
    correct = _normalise(submitted) == _normalise(expected)
    if correct:
        feedback = (
            f"✅ Correct! +{ch.xp} XP. {ch.explanation}"
        )
    elif not submitted:
        feedback = "⏸️ No answer submitted yet — type your answer or request a hint."
    else:
        feedback = (
            f"❌ Not quite — the grader expected `{_short(expected)}`. "
            f"{ch.hint}"
        )
    return GradeResult(
        challenge_id=ch.id,
        title=ch.title,
        tier=ch.tier,
        correct=correct,
        xp_earned=ch.xp if correct else 0,
        expected=expected,
        submitted=submitted,
        feedback=feedback,
    )


def _short(text: str, limit: int = 90) -> str:
    t = re.sub(r"\s+", " ", text.strip())
    return t if len(t) <= limit else t[: limit - 1] + "…"


def total_xp(results: Sequence[GradeResult]) -> int:
    """Sum XP across graded attempts (correct attempts only)."""
    return sum(r.xp_earned for r in results)


def tier_progress(results: Sequence[GradeResult]) -> Dict[str, Dict[str, int]]:
    """Per-tier solved counts for the leaderboard UI."""
    out: Dict[str, Dict[str, int]] = {
        t: {"solved": 0, "attempted": 0, "xp": 0, "total_challenges": sum(1 for c in CHALLENGES if c.tier == t)}
        for t in TIERS
    }
    seen = set()
    for r in results:
        if r.tier in out:
            out[r.tier]["attempted"] += 1
            if r.correct:
                out[r.tier]["xp"] += r.xp_earned
                if r.challenge_id not in seen:
                    out[r.tier]["solved"] += 1
                    seen.add(r.challenge_id)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Groq Llama-8B hints (network-optional)
# ─────────────────────────────────────────────────────────────────────────────

def groq_llama_hint(
    question: str,
    api_key: "str | None" = None,
    model: str = GROQ_MODEL,
    timeout: float = 8.0,
) -> Optional[str]:
    """Ask Groq's Llama-8B for a nudge. Returns None when unreachable.

    Network access happens ONLY when an API key is present in the
    environment (``GROQ_API_KEY``) or passed explicitly — with no key the
    function is pure and offline. Failure modes degrade to ``None`` so the
    arena can serve its local hint instead.
    """
    key = api_key or os.environ.get("GROQ_API_KEY") or ""
    if not key or not question:
        return None
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": (
                "You are Dr. Titan, a bioinformatics olympiad coach. Give ONE "
                "short hint (max 2 sentences). Never give the full answer."
            )},
            {"role": "user", "content": question},
        ],
        "max_tokens": 120,
        "temperature": 0.4,
    }).encode("utf-8")
    request = urllib.request.Request(
        GROQ_API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return str(payload["choices"][0]["message"]["content"]).strip()
    except Exception:
        return None


def get_hint(challenge_id: str, use_groq: bool = True) -> Tuple[str, str]:
    """Return ``(hint_text, source)`` — Groq Llama-8B when available, else local."""
    ch = get_challenge(challenge_id)
    if use_groq:
        ai = groq_llama_hint(
            f"Challenge {ch.id} ({ch.title}, {ch.tier}): {ch.prompt} Give one hint only."
        )
        if ai:
            return ai, "Groq Llama-8B"
    return ch.hint, "Local Titan hint library"
