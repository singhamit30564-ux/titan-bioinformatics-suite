"""Validated nucleic-acid duplex thermodynamics for Titan.

This module is the single source of truth for melting temperature (Tm) and
duplex stability. The nearest-neighbor (NN) engine mirrors
``Bio.SeqUtils.MeltingTemp.Tm_NN`` (Allawi & SantaLucia 1997 tables via
``DNA_NN3``, salt correction method 5) so every number Titan prints is
verifiable against Biopython — the test-suite asserts agreement to 1e-6 °C
on randomized sequences and that the two-state melting-curve midpoint equals
the analytic Tm.

Methods
-------
* ``nn_tm``            — nearest-neighbor Tm (the reference method).
* ``nn_dH_dS``         — ΔH (kcal/mol) and ΔS (cal/mol/K) of duplex formation.
* ``melting_curve``    — two-state fraction-bound vs temperature.
* ``wallace_tm``       — the 2 + 4 rule; valid only for short (≤ 14 nt) primers.
* ``gc_formula_tm``    — Marmur-Doty long-DNA formula; valid for > 500 bp.

Educational honesty: the simple formulas are approximations with stated
applicability ranges; NN is used everywhere a "real" number is needed.
"""
from __future__ import annotations

import math
from typing import Tuple

R_CAL = 1.987          # universal gas constant, cal/(mol·K)
R_SI = 8.314462618     # universal gas constant, J/(mol·K)
KELVIN = 273.15

MAX_THERMO_LEN = 1000  # protects UI from megabase pastes; NN is linear-time.


class ThermoError(ValueError):
    """Raised for invalid duplex parameters (bad characters, empty, too long)."""


def _clean(seq: str) -> str:
    s = "".join((seq or "").upper().split()).replace("-", "").replace(".", "")
    if not s:
        raise ThermoError("Sequence is empty — enter at least one base.")
    if any(c not in "ATGC" for c in s):
        raise ThermoError(
            "Thermodynamics supports unambiguous DNA (A, T, G, C) only — "
            "remove ambiguity codes, gaps, or FASTA headers."
        )
    if len(s) < 4:
        raise ThermoError("Sequences shorter than 4 nt are outside the validated NN range.")
    if len(s) > MAX_THERMO_LEN:
        raise ThermoError(
            f"Sequence longer than {MAX_THERMO_LEN} nt — this engine is designed "
            "for oligos/short duplexes. Trim before calculating."
        )
    return s


def _nn_tables():
    from Bio.SeqUtils import MeltingTemp as mt  # deferred: keeps import light
    return mt


def nn_dH_dS(
    seq: str,
    *,
    selfcomp: bool = False,
    Na_mm: float = 50.0,
    K_mm: float = 0.0,
    Tris_mm: float = 0.0,
    Mg_mm: float = 0.0,
    dNTPs_mm: float = 0.0,
) -> Tuple[float, float]:
    """Return ``(dH_kcal, dS_cal_per_K)`` for a perfectly matched duplex.

    Assembly mirrors Biopython ``Tm_NN`` exactly: general initiation,
    all-A/T vs one-G/C initiation, 5'T/3'A penalty, terminal base-pair
    counts, NN zipping over dinucleotide steps, symmetry correction for
    self-complementary strands, and salt correction (method 5) on ΔS.
    """
    mt = _nn_tables()
    s = _clean(seq)
    comp = s.translate(str.maketrans("ATGC", "TACG"))
    nn = mt.DNA_NN3

    dH = nn["init"][0]
    dS = nn["init"][1]
    if not ("G" in s or "C" in s):
        dH += nn["init_allA/T"][0]
        dS += nn["init_allA/T"][1]
    else:
        dH += nn["init_oneG/C"][0]
        dS += nn["init_oneG/C"][1]
    if s.startswith("T"):
        dH += nn["init_5T/A"][0]
        dS += nn["init_5T/A"][1]
    if s.endswith("A"):
        dH += nn["init_5T/A"][0]
        dS += nn["init_5T/A"][1]
    ends = s[0] + s[-1]
    dH += nn["init_A/T"][0] * (ends.count("A") + ends.count("T"))
    dS += nn["init_A/T"][1] * (ends.count("A") + ends.count("T"))
    dH += nn["init_G/C"][0] * (ends.count("G") + ends.count("C"))
    dS += nn["init_G/C"][1] * (ends.count("G") + ends.count("C"))

    for i in range(len(s) - 1):
        key = s[i:i + 2] + "/" + comp[i:i + 2]
        pair = nn.get(key, nn.get(key[::-1]))
        if pair is None:  # pragma: no cover - ATGC input guarantees a key
            raise ThermoError(f"Missing NN parameters for dinucleotide step {key!r}.")
        dH += pair[0]
        dS += pair[1]

    if selfcomp:
        dH += nn["sym"][0]
        dS += nn["sym"][1]

    dS += mt.salt_correction(
        Na=Na_mm, K=K_mm, Tris=Tris_mm, Mg=Mg_mm, dNTPs=dNTPs_mm, method=5, seq=s
    )
    return float(dH), float(dS)


def nn_tm(
    seq: str,
    *,
    Na_mm: float = 50.0,
    K_mm: float = 0.0,
    Tris_mm: float = 0.0,
    Mg_mm: float = 0.0,
    dNTPs_mm: float = 0.0,
    dnac1_nm: float = 25.0,
    dnac2_nm: float = 25.0,
    selfcomp: bool = False,
) -> float:
    """Nearest-neighbor Tm (°C).

    Delegates to Biopython ``Tm_NN`` (validated engine); ``nn_tm_from_params``
    below reproduces it from ``nn_dH_dS`` and the two are kept equal by tests.
    """
    mt = _nn_tables()
    s = _clean(seq)
    return float(mt.Tm_NN(
        s,
        dnac1=dnac1_nm,
        dnac2=dnac2_nm,
        selfcomp=selfcomp,
        Na=Na_mm,
        K=K_mm,
        Tris=Tris_mm,
        Mg=Mg_mm,
        dNTPs=dNTPs_mm,
        saltcorr=5,
    ))


def nn_tm_from_params(
    seq: str,
    *,
    Na_mm: float = 50.0,
    K_mm: float = 0.0,
    Tris_mm: float = 0.0,
    Mg_mm: float = 0.0,
    dNTPs_mm: float = 0.0,
    dnac1_nm: float = 25.0,
    dnac2_nm: float = 25.0,
    selfcomp: bool = False,
) -> float:
    """Same value as :func:`nn_tm`, computed from our own dH/dS + Biopython's
    concentration term ``k = (dnac1 - dnac2/2) nM`` (self-comp: ``k = dnac1``)."""
    dH, dS = nn_dH_dS(
        seq, selfcomp=selfcomp, Na_mm=Na_mm, K_mm=K_mm, Tris_mm=Tris_mm,
        Mg_mm=Mg_mm, dNTPs_mm=dNTPs_mm,
    )
    k_mol = (dnac1_nm if selfcomp else (dnac1_nm - dnac2_nm / 2.0)) * 1e-9
    if k_mol <= 0:
        raise ThermoError("Strand concentration must satisfy dnac1 > dnac2/2.")
    return 1000.0 * dH / (dS + R_CAL * math.log(k_mol)) - KELVIN


def wallace_tm(seq: str) -> Tuple[float, bool]:
    """Wallace 2 + 4 rule. Returns (Tm °C, in_valid_range ≤ 14 nt)."""
    s = _clean(seq)
    gc = s.count("G") + s.count("C")
    at = len(s) - gc
    return float(2 * at + 4 * gc), len(s) <= 14


def gc_formula_tm(seq: str, *, Na_mm: float = 50.0) -> Tuple[float, bool]:
    """Marmur-Doty long-DNA Tm: 81.5 + 0.41·%GC(%) + 16.6·log10[Na+ (M)].

    Valid for duplexes > 500 bp; returns (Tm, in_valid_range).
    """
    s = _clean(seq)
    gc_frac = (s.count("G") + s.count("C")) / len(s)
    na_m = max(1e-6, Na_mm / 1000.0)
    tm = 81.5 + 0.41 * 100.0 * gc_frac + 16.6 * math.log10(na_m)
    return float(tm), len(s) >= 500


def tm_with_formamide(seq: str, formamide_percent: float = 0.0, **kw) -> float:
    """NN Tm minus the classic Schildkraut formamide term: −0.6 °C per % (0–50)."""
    fp = max(0.0, min(50.0, float(formamide_percent)))
    return nn_tm(seq, **kw) - 0.6 * fp


# ── Two-state melting curves ────────────────────────────────────────────────
def fraction_bound(
    seq: str,
    temp_c: float,
    *,
    Na_mm: float = 50.0,
    K_mm: float = 0.0,
    Tris_mm: float = 0.0,
    Mg_mm: float = 0.0,
    dNTPs_mm: float = 0.0,
    dnac1_nm: float = 25.0,
    dnac2_nm: float = 25.0,
    selfcomp: bool = False,
) -> float:
    """Fraction of strands in duplex at ``temp_c`` (two-state model, ΔCp = 0).

    A+B ⇌ AB (non-self-complementary) or 2A ⇌ A2 (self-complementary) mass
    action solved as a quadratic in the duplex concentration ``b``. The
    midpoint θ = 0.5 coincides with Biopython's Tm by construction.
    """
    s = _clean(seq)
    dH, dS = nn_dH_dS(
        s, selfcomp=selfcomp, Na_mm=Na_mm, K_mm=K_mm, Tris_mm=Tris_mm,
        Mg_mm=Mg_mm, dNTPs_mm=dNTPs_mm,
    )
    dG_J = dH * 4184.0 - (float(temp_c) + KELVIN) * dS * 4.184
    exponent = -dG_J / (R_SI * (float(temp_c) + KELVIN))
    if exponent > 700.0:
        return 1.0  # fully associated (exp would overflow)
    if exponent < -700.0:
        return 0.0  # fully dissociated
    K_a = math.exp(exponent)  # association constant, M^-1
    if K_a <= 0:
        return 0.0

    if selfcomp:
        a0 = dnac1_nm * 1e-9
        # 2A ⇌ A2 : with x = free strand, (a0 - x)/2 = K x²  →  2Kx² + x - a0 = 0.
        # Rationalized root x = 2a0 / (1 + sqrt(1 + 8·K·a0)) — no cancellation
        # even when K·a0 is tiny (the naive (-1+sqrt(...))/(4K) form collapses
        # to 0 in float64 for 1 + 8Ka0 ≈ 1).
        x = 2.0 * a0 / (1.0 + math.sqrt(1.0 + 8.0 * K_a * a0))
        x = min(max(x, 0.0), a0)
        bound = (a0 - x) / a0 if a0 > 0 else 0.0
        return float(min(1.0, max(0.0, bound)))

    a0 = dnac1_nm * 1e-9
    lo = dnac2_nm * 1e-9
    if lo <= 0 or a0 <= 0:
        raise ThermoError(
            "fraction_bound requires both strand concentrations (dnac1_nm and "
            "dnac2_nm > 0); the UI melting curves always pass both."
        )
    if a0 > 3.0 * lo:
        raise ThermoError(
            "Melting curves assume strands within 3-fold of equimolar "
            "(dnac1 ≤ 3×dnac2) so the 50% midpoint tracks the Tm definition."
        )
    # K b = (a0 - b)(lo - b)  →  b² - S b + a0·lo = 0, S = a0+lo+1/K
    S = a0 + lo + 1.0 / K_a
    disc = max(0.0, S * S - 4.0 * a0 * lo)
    b = 2.0 * a0 * lo / (S + math.sqrt(disc))  # numerically stable smaller root
    total = a0 + lo
    return float(min(1.0, max(0.0, 2.0 * b / total))) if total > 0 else 0.0


def melting_curve(
    seq: str,
    *,
    temp_min_c: float = 5.0,
    temp_max_c: float = 99.0,
    points: int = 200,
    **kw,
):
    """Return ``(temps_C, fraction_bound)`` for plotting; midpoint marks Tm."""
    pts = max(50, min(500, int(points)))
    step = (temp_max_c - temp_min_c) / (pts - 1)
    temps = [temp_min_c + step * i for i in range(pts)]
    bounds = [fraction_bound(seq, t, **kw) for t in temps]
    return temps, bounds


def curve_tm_midpoint(seq: str, **kw) -> float:
    """Tm defined numerically as where fraction_bound crosses 0.5.

    θ is monotonically decreasing in temperature, so θ > 0.5 means we are
    below the midpoint and the search window moves up.
    """
    lo, hi = -60.0, 160.0
    if fraction_bound(seq, hi, **kw) >= 0.5:  # pragma: no cover - extreme inputs
        return hi
    if fraction_bound(seq, lo, **kw) <= 0.5:  # pragma: no cover - extreme inputs
        return lo
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if fraction_bound(seq, mid, **kw) > 0.5:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


# ── Convenience analytics ──────────────────────────────────────────────────
def self_complementary(seq: str) -> bool:
    """True when the sequence equals its own reverse complement."""
    s = _clean(seq)
    if len(s) % 2:
        return False
    comp = s.translate(str.maketrans("ATGC", "TACG"))
    return s == comp[::-1]


def terminal_stem_bp(seq: str, *, min_stem: int = 3) -> Tuple[int, float]:
    """Educational hairpin screen: complementary stem length at the 5'/3' ends.

    Returns ``(stem_bp, approx_penalty_kcal)`` where the penalty is −1.0
    kcal/mol per stem bp — a documented heuristic for flagging primer
    hairpins, NOT a folding free energy.
    """
    s = _clean(seq)
    comp = s.translate(str.maketrans("ATGC", "TACG"))[::-1]
    best = 0
    for i in range(len(s) // 2):
        if s[i] == comp[i]:
            best += 1
        else:
            break
    if best < min_stem:
        best = 0
    return best, -1.0 * best if best else 0.0
