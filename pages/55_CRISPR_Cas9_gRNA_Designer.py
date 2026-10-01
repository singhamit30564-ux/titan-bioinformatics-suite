"""CRISPR gRNA Designer — supports SpCas9 (NGG), SaCas9 (NNGRRT), Cas12a (TTTV)."""
import re

import pandas as pd
import plotly.express as px
import streamlit as st

from titan_utils import clean_sequence, validate_dna
from titan_utils.i18n import t
from titan_utils.io import df_to_csv_bytes
from titan_utils.ui import dr_titan_tip, smart_lock, titan_title

titan_title(
    "🎯", "CRISPR-Cas9 gRNA Designer",
    "Design guide RNAs for CRISPR genome editing, with proper PAM "
    "recognition for SpCas9, SaCas9 and Cas12a/Cpf1.",
)

IUPAC = {  # map IUPAC ambiguity codes → character class
    "N": "[ACGT]", "R": "[AG]", "Y": "[CT]", "V": "[ACG]",
}


def compile_pam(pam: str) -> re.Pattern:
    """Compile a PAM string (with IUPAC codes) into a regex."""
    pattern = ""
    for ch in pam:
        pattern += IUPAC.get(ch, re.escape(ch))
    return re.compile(pattern)


# ---- PAM configurations ----
# For Cas9 nucleases, the PAM is *3'* of the protospacer (immediately after
# the 20-nt gRNA). For Cas12a, the PAM is *5'* of the protospacer (TTTV
# followed by the 23-nt spacer; we use 20-nt gRNA for parity).
PAMS = {
    "SpCas9 (NGG)": {
        "pam": "NGG",
        "pam_side": "3prime",
        "grna_len": 20,
        "pam_len": 3,
    },
    "SaCas9 (NNGRRT)": {
        "pam": "NNGRRT",
        "pam_side": "3prime",
        "grna_len": 21,
        "pam_len": 6,
    },
    "Cas12a/Cpf1 (TTTV)": {
        "pam": "TTTV",
        "pam_side": "5prime",
        "grna_len": 23,
        "pam_len": 4,
    },
}

st.markdown(t("### 📥 Input Sequence"))
target_seq = st.text_area(
    t("Enter Target DNA Sequence (5' → 3')"),
    "ATGCGTACGTAGCTAGCTAGCATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGGGATCGATCG",
    height=150,
)
pam_labels = {t(option): option for option in PAMS}
pam_type = pam_labels[st.radio(
    t("Select Cas protein / PAM type"),
    list(pam_labels),
    horizontal=True,
)]

if st.button(t("🎯 Design gRNAs"), type="primary", use_container_width=True):
    seq = clean_sequence(target_seq)
    seq_ok, err = validate_dna(seq, allow_iupac=False)
    # validate_dna returns a cleaned sequence AND an error message
    if err:
        st.error(t(err))
    else:
        cfg = PAMS[pam_type]
        grna_len = cfg["grna_len"]
        pam_re = compile_pam(cfg["pam"])
        pam_anchor = 0 if cfg["pam_side"] == "5prime" else grna_len
        required_len = grna_len + cfg["pam_len"]
        if len(seq) < required_len:
            st.error(t("Sequence too short — need at least {length} bp for gRNA + PAM ({pam}).", length=required_len, pam=cfg['pam']))
        else:
            with st.spinner(t("🧮 Scanning for PAM sites & extracting gRNAs...")):
                grnas = []
                total_scan = len(seq) - required_len + 1
                for i in range(total_scan):
                    window = seq[i:i + required_len]
                    if cfg["pam_side"] == "3prime":
                        grna_seq = window[:grna_len]
                        pam_seq = window[grna_len:]
                        # PAM starts at position 1 of pam_seq (0-indexed)
                        if pam_re.match(pam_seq):
                            found_pam = pam_seq
                        else:
                            continue
                    else:  # 5prime PAM (Cas12a)
                        pam_seq = window[:cfg["pam_len"]]
                        grna_seq = window[cfg["pam_len"]:cfg["pam_len"] + grna_len]
                        if pam_re.match(pam_seq):
                            found_pam = pam_seq
                        else:
                            continue

                    gc = (grna_seq.count("G") + grna_seq.count("C")) / grna_len * 100
                    if gc < 30 or gc > 70:
                        risk = "High (extreme GC)"
                    elif gc < 40 or gc > 60:
                        risk = "Medium"
                    else:
                        risk = "Low"

                    grnas.append({
                        "Position": i + 1,
                        "Strand": "+",
                        "gRNA (5'→3')": grna_seq,
                        "PAM": found_pam,
                        "GC %": round(gc, 1),
                        "Risk": risk,
                    })

            if not grnas:
                st.warning(t("⚠️ No valid gRNA targets found with the selected PAM in this sequence."))
            else:
                df = pd.DataFrame(grnas)
                st.markdown(t("### 🎯 Found {count} potential gRNA targets", count=len(df)))
                df_display = df.rename(columns=lambda column: t(column)).copy()
                risk_column = t("Risk")
                df_display[risk_column] = df_display[risk_column].map(t)
                st.dataframe(df_display, use_container_width=True, hide_index=True)

                st.markdown(t("### 📊 gRNA GC-content distribution"))
                fig = px.histogram(
                    df, x="GC %", nbins=12,
                    color_discrete_sequence=["#d4af37"],
                    title=t("Distribution of gRNA GC% — {pam}", pam=pam_type),
                )
                fig.add_vrect(
                    x0=40, x1=60, fillcolor="#66fcf1", opacity=0.2,
                    line_width=0, annotation_text=t("Ideal range (40–60%)"),
                )
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#0a0e17",
                    plot_bgcolor="#1a1f2e",
                    font=dict(color="#e0e0e0"),
                    xaxis_title=t("GC Content (%)"),
                    yaxis_title=t("Number of gRNAs"),
                )
                st.plotly_chart(fig, use_container_width=True)

                st.markdown(t("### 📈 Summary statistics"))
                low_risk = (df["Risk"] == "Low").sum()
                c1, c2, c3 = st.columns(3)
                c1.metric(t("Total gRNAs"), len(df))
                c2.metric(t("Average GC%"), f"{df['GC %'].mean():.1f}%")
                c3.metric(t("Low-risk"), int(low_risk))

                smart_lock(csv_data=df_to_csv_bytes(df), csv_filename="crispr_grnas.csv")

with st.sidebar:
    st.markdown(t("### ℹ️ How to use"))
    st.markdown("\n".join([
        t("1. Paste your DNA sequence (5' → 3')"),
        t("2. Select a Cas protein"),
        t("3. Click **Design gRNAs**"),
        t("4. Pick Low-risk gRNAs with 40–60% GC"),
        t("5. Download candidates as CSV."),
    ]))
    st.markdown(t("### 🎯 PAM sequences"))
    st.markdown("\n".join([
        t("- **SpCas9**: NGG (3' of spacer)"),
        t("- **SaCas9**: NNGRRT (3' of spacer)"),
        t("- **Cas12a**: TTTV (5' of spacer)"),
    ]))

dr_titan_tip(
    "SpCas9 gRNAs are 20 nt long, immediately followed by an NGG PAM. "
    "SaCas9 (NNGRRT) is smaller and is often used for AAV delivery; "
    "Cas12a/Cpf1 recognises TTTV at the *5'* end and leaves staggered cuts. "
    "A GC of 40–60% gives stable binding without excessive off-targets."
)
