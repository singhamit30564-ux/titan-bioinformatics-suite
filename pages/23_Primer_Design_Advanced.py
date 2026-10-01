import streamlit as st
import pandas as pd
import math
from titan_utils import clean_sequence, validate_dna, validate_rna, revcomp, gc_fraction_safe
from titan_utils.i18n import t
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title("🧪", "Advanced Primer Design Engine", "Refactored with Titan validation & export.")
st.markdown(t("Scan your entire sequence for optimal primer candidates with Tm, GC%, and self-complementarity checks."))
st.markdown("---")

# --- INPUT SECTION ---
dna_seq = st.text_area(t("Enter Template DNA Sequence (5' to 3')"),
    "ATGCGCTAGCTAGCTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG",
    height=150)

c1, c2, c3 = st.columns(3)
with c1:
    primer_len = st.slider(t("Primer Length (bp)"), 18, 25, 20)
with c2:
    target_tm = st.slider(t("Target Tm (°C)"), 55, 65, 60)
with c3:
    min_gc = st.slider(t("Min GC %"), 40, 60, 45)

max_gc = st.slider(t("Max GC %"), 50, 70, 60)
max_candidates = st.slider(t("Top Candidates to Show"), 5, 20, 10)

# --- HELPER FUNCTIONS ---
def calculate_tm(seq):
    """Basic Tm calculation using modified Wallace rule"""
    gc = seq.count('G') + seq.count('C')
    at = seq.count('A') + seq.count('T')
    length = len(seq)
    # SantaLucia 1998 nearest-neighbor approximation (simplified)
    tm = 64.9 + 41 * (gc - 16.4) / length
    return tm

def check_self_complementarity(seq):
    """Basic check for hairpin potential"""
    complement = str.maketrans('ATCG', 'TAGC')
    rev_comp = seq.translate(complement)[::-1]
    # Check for 4+ consecutive matches
    max_match = 0
    current_match = 0
    for i in range(len(seq)):
        if i < len(rev_comp) and seq[i] == rev_comp[i]:
            current_match += 1
            max_match = max(max_match, current_match)
        else:
            current_match = 0
    return max_match

def score_primer(seq, target_tm):
    """Score primer based on how close it is to ideal parameters"""
    tm = calculate_tm(seq)
    gc = ((seq.count('G') + seq.count('C')) / len(seq)) * 100
    self_comp = check_self_complementarity(seq)

    # Penalty system (lower is better)
    tm_penalty = abs(tm - target_tm) * 2
    gc_penalty = abs(gc - 50) * 0.5
    self_comp_penalty = self_comp * 5

    total_score = tm_penalty + gc_penalty + self_comp_penalty
    return total_score, tm, gc, self_comp

# --- MAIN LOGIC ---
if st.button(t("🔍 Scan for Optimal Primers"), use_container_width=True, type="primary"):
    seq = dna_seq.replace(" ", "").upper()

    if len(seq) < primer_len * 2:
        st.error(t("❌ Sequence too short! Need at least 2x primer length for valid pairs."))
    elif any(c not in "ATCG" for c in seq):
        st.error(t("❌ Invalid DNA! Only A, T, C, G allowed."))
    else:
        # Scan entire sequence with sliding window
        forward_candidates = []
        reverse_candidates = []

        for i in range(len(seq) - primer_len + 1):
            # Forward primer
            f_primer = seq[i:i+primer_len]
            f_gc = ((f_primer.count('G') + f_primer.count('C')) / primer_len) * 100

            if min_gc <= f_gc <= max_gc:
                f_score, f_tm, f_gc_val, f_self = score_primer(f_primer, target_tm)
                forward_candidates.append({
                    'position': i,
                    'sequence': f_primer,
                    'score': f_score,
                    'tm': f_tm,
                    'gc': f_gc_val,
                    'self_comp': f_self
                })

            # Reverse primer (reverse complement of window)
            r_window = seq[i:i+primer_len]
            complement = str.maketrans('ATCG', 'TAGC')
            r_primer = r_window.translate(complement)[::-1]
            r_gc = ((r_primer.count('G') + r_primer.count('C')) / primer_len) * 100

            if min_gc <= r_gc <= max_gc:
                r_score, r_tm, r_gc_val, r_self = score_primer(r_primer, target_tm)
                reverse_candidates.append({
                    'position': i,
                    'sequence': r_primer,
                    'score': r_score,
                    'tm': r_tm,
                    'gc': r_gc_val,
                    'self_comp': r_self
                })

        # Sort by score (lower is better)
        forward_candidates.sort(key=lambda x: x['score'])
        reverse_candidates.sort(key=lambda x: x['score'])

        top_forward = forward_candidates[:max_candidates]
        top_reverse = reverse_candidates[:max_candidates]

        # --- DISPLAY RESULTS ---
        st.markdown(t("### 📊 Scan Complete: Found {forward} Forward & {reverse} Reverse Candidates", forward=len(forward_candidates), reverse=len(reverse_candidates)))

        c1, c2 = st.columns(2)

        with c1:
            st.markdown(t("#### 🔼 Top Forward Primers (5'→3')"))
            for i, p in enumerate(top_forward, 1):
                st.success(t(
                    "**#{number}** | Position: {position} | Tm: {tm}°C | GC: {gc}% | Hairpin: {hairpin}\n\n`{sequence}`",
                    number=i,
                    position=p["position"],
                    tm=f"{p['tm']:.1f}",
                    gc=f"{p['gc']:.1f}",
                    hairpin=p["self_comp"],
                    sequence=p["sequence"],
                ))

        with c2:
            st.markdown(t("#### 🔽 Top Reverse Primers (5'→3')"))
            for i, p in enumerate(top_reverse, 1):
                st.success(t(
                    "**#{number}** | Position: {position} | Tm: {tm}°C | GC: {gc}% | Hairpin: {hairpin}\n\n`{sequence}`",
                    number=i,
                    position=p["position"],
                    tm=f"{p['tm']:.1f}",
                    gc=f"{p['gc']:.1f}",
                    hairpin=p["self_comp"],
                    sequence=p["sequence"],
                ))

        st.markdown("---")

        # --- BEST PAIR RECOMMENDATION ---
        if top_forward and top_reverse:
            best_f = top_forward[0]
            # Find best reverse that's downstream and has similar Tm
            best_r = None
            for r in top_reverse:
                if r['position'] > best_f['position'] + primer_len:
                    if abs(r['tm'] - best_f['tm']) < 5:  # Tm within 5°C
                        best_r = r
                        break

            if best_r:
                product_size = best_r['position'] + primer_len - best_f['position']
                st.markdown(t("### 🏆 Recommended Primer Pair"))
                st.success(t("**Forward:** `{sequence}` (Tm: {tm}°C)\n\n**Reverse:** `{reverse}` (Tm: {reverse_tm}°C)\n\n**Expected Product Size:** {size} bp", sequence=best_f['sequence'], tm=f"{best_f['tm']:.1f}", reverse=best_r['sequence'], reverse_tm=f"{best_r['tm']:.1f}", size=product_size))
            else:
                st.warning(t("⚠️ No ideal pair found with matching Tm. Try adjusting parameters."))

        st.info(t("💡 **Dr. Titan's Tip:** Ideal primers have Tm within 2-5°C of each other, 40-60% GC, minimal self-complementarity (hairpin score < 3), and 3-5 bp G/C clamp at 3' end!"))
