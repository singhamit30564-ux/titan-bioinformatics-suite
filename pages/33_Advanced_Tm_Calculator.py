"""Advanced Tm Calculator — nearest-neighbor + published salt/formamide corrections.

All numbers come from :mod:`titan_utils.thermo` (validated to match
Bio.SeqUtils.MeltingTemp.Tm_NN exactly, incl. salt corrections) — the same
engine the Hub tools use. No ad-hoc formulas live on this page anymore.
"""
import streamlit as st
import pandas as pd

from titan_utils import thermo
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title("🌡", "Advanced Tm Calculator", "Nearest-neighbor thermodynamics with salt & formamide correction.")
st.markdown(
    "Tm computed by the nearest-neighbor model (SantaLucia 1998 parameters, Marmur–Doty / "
    "Owczarzy salt corrections via Biopython). Compare with the classic Wallace and "
    "GC-formula estimates below."
)
st.markdown("---")

seq = (st.text_input("Enter DNA Sequence", "ATGCGCTAGCTAGCTAGCTAGGCTATCGATCGATCGATCGATC")
       .replace(" ", "").replace("\n", "").upper())
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    na_conc = st.slider("Na⁺ Concentration (mM)", 10, 1000, 50)
with c2:
    mg_conc = st.slider("Mg²⁺ (mM)", 0, 20, 0)
with c3:
    formamide = st.slider("Formamide (%, v/v)", 0, 20, 0)
with c4:
    oligo_nm = st.slider("Oligo conc. (nM)", 25, 1000, 25)

if st.button("🌡 Calculate Tm", type="primary", use_container_width=True):
    if not seq or any(c not in "ATCG" for c in seq):
        st.error("❌ Please enter a valid DNA sequence (A, T, C, G only).")
    elif len(seq) < 4:
        st.error("❌ Sequence too short — give at least 4 bases.")
    else:
        try:
            tm_nn = thermo.tm_with_formamide(
                seq, formamide, Na_mm=na_conc, Mg_mm=mg_conc,
                dnac1_nm=oligo_nm, dnac2_nm=oligo_nm,
            )
        except thermo.ThermoError as ex:
            st.error(f"❌ {ex}")
            st.stop()
        wallace, wallace_ok = thermo.wallace_tm(seq)
        gc_tm, salt_note = thermo.gc_formula_tm(seq, Na_mm=na_conc)
        dH, dS = thermo.nn_dH_dS(seq, Na_mm=na_conc, Mg_mm=mg_conc)
        selfcomp = thermo.self_complementary(seq)

        st.markdown("### 📊 Results")
        m1, m2, m3 = st.columns(3)
        m1.metric("Nearest-Neighbor Tm", f"{tm_nn:.2f} °C", delta="recommended", delta_color="off")
        m2.metric("Wallace (≤13 nt only)", f"{wallace:.1f} °C" if wallace_ok else "N/A (too long)")
        m3.metric("GC formula (Marmur–Doty)", f"{gc_tm:.1f} °C")

        df = pd.DataFrame([
            {"Method": "Nearest neighbor (SantaLucia/Breslauer, salt+Mg²⁺+formamide)",
             "Tm_C": round(tm_nn, 2), "Valid_for_this_input": "yes"},
            {"Method": "Wallace rule (2·A+T + 4·G+C)",
             "Tm_C": round(wallace, 2) if wallace_ok else None,
             "Valid_for_this_input": "yes" if wallace_ok else "no (length > 13 nt)"},
            {"Method": "Marmur–Doty GC formula (81.5 + 16.6·log₁₀[Na⁺] + 0.41·%GC − 600/L)",
             "Tm_C": round(gc_tm, 1), "Valid_for_this_input": salt_note},
            {"Method": "Total ΔH / ΔS of duplex",
             "Tm_C": None, "Valid_for_this_input": f"ΔH={dH:.1f} cal/mol, ΔS={dS:.1f} cal/(mol·K), self-complementary={selfcomp}"},
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download CSV", data=df_to_csv_bytes(df), file_name="titan_tm_results.csv",
                           mime="text/csv", key="tm_adv_csv")

        st.caption(
            "Notes: Wallace is only a teaching rule for 7–13-mers; the GC formula is calibrated for long "
            "genomic DNA and can be off by ±10 °C for primers. The nearest-neighbor value is the one to trust "
            "for oligos. Formamide linear-depression correction of ~0.6 °C/% (standard in hybridization buffers) "
            "is applied to the NN result."
        )
        dr_titan_tip(
            "Tm rises with salt (charge screening stabilizes the duplex) and falls ~0.6 °C per % formamide — "
            "that is why RNA hybridizations run in formamide at modest temperature instead of boiling aqueous buffer."
        )
        smart_lock()
