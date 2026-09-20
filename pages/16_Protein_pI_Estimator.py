import streamlit as st
import pandas as pd
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from titan_utils import clean_sequence, validate_dna, validate_rna, revcomp, gc_fraction_safe
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title("🧪", "Protein Isoelectric Point (pI) Estimator", "Refactored with Titan validation & export.")
st.markdown("Estimate the pH at which the protein has a net zero charge.")
st.markdown("---")

prot_seq = st.text_area("Enter Protein Sequence", "MRSLLILVLCFLPAALG").replace(" ", "").upper()

if st.button("Calculate pI", type="primary"):
    if any(c not in "ACDEFGHIKLMNPQRSTVWY" for c in prot_seq):
        st.error("Invalid Protein Sequence!")
    else:
        # pKa values for the ionizable side chains plus the N-/C-termini.
        # Biopython's ProteinAnalysis applies the Henderson-Hasselbalch equation
        # with these pKa values and bisects pH until the net charge is zero —
        # that zero-charge pH *is* the isoelectric point.
        pka = {'N_term': 9.69, 'C_term': 2.34, 'D': 3.86, 'E': 4.25, 'C': 8.33,
               'Y': 10.07, 'H': 6.00, 'K': 10.53, 'R': 12.48}
        counts = {aa: prot_seq.count(aa) for aa in pka if aa not in ('N_term', 'C_term')}
        acidic = counts.get('D', 0) + counts.get('E', 0)
        basic = counts.get('H', 0) + counts.get('K', 0) + counts.get('R', 0)

        try:
            analysis = ProteinAnalysis(prot_seq)
            pi = analysis.isoelectric_point()
            charge_at_7 = analysis.charge_at_pH(7.0)
        except (ValueError, ZeroDivisionError) as exc:
            st.error(f"❌ Could not calculate pI for this sequence: {exc}")
            st.stop()

        st.markdown("### 📊 Isoelectric Point")
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated pI", f"{pi:.2f}")
        c2.metric("Net Charge @ pH 7.0", f"{charge_at_7:+.3f}")
        c3.metric("Acidic / Basic Residues", f"{acidic} / {basic}")
        st.caption(
            "Residue counts shown for reference. Acidity/basicity is decided by the "
            "**net charge curve**, not by raw counts — the pKa of each group and the "
            "N-/C-termini all contribute."
        )

        if pi > 7.5:
            st.success(f"✅ **Basic protein** — pI {pi:.2f} is above 7, so the net charge "
                       f"at pH 7 is positive ({charge_at_7:+.3f}).")
        elif pi < 6.5:
            st.warning(f"⚠️ **Acidic protein** — pI {pi:.2f} is below 7, so the net charge "
                       f"at pH 7 is negative ({charge_at_7:+.3f}).")
        else:
            st.info(f"ℹ️ **Near-neutral protein** — pI {pi:.2f} sits close to pH 7 "
                    f"(net charge {charge_at_7:+.3f}).")

        with st.expander("🔬 How this is calculated"):
            st.markdown(
                "1. Every ionizable group (D, E, C, Y, H, K, R, N-terminus, C-terminus) "
                "gets a charge from the Henderson-Hasselbalch equation at a trial pH.\n"
                "2. Those charges are summed to give the **net charge**.\n"
                "3. pH is bisected until the net charge is 0 — that pH is the **pI**."
            )

        st.info("💡 **Dr. Titan's Tip:** pI is crucial for protein purification (Isoelectric Focusing). Proteins precipitate at their pI!")