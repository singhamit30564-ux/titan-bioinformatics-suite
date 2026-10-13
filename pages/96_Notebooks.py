"""🔬 Public Lab Notebooks — Publish ELN entries publicly (localStorage-based).

Users publish entries as share text. Gallery of 5 demo notebooks.
Each entry: title, tool used, result summary, SHA-256 provenance.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🔬",
    "Public Lab Notebooks",
    "Share your Titan experiments with the community! Publish ELN entries, explore demo notebooks, and verify provenance.",
)

# ── Demo notebooks ───────────────────────────────────────────────────────────
DEMO_NOTEBOOKS = [
    {
        "title": "GC Content Analysis of GFP Gene",
        "tool": "GC Content & Melting Temperature",
        "author": "Shivay S.",
        "date": "2026-01-15",
        "summary": "Analyzed the GC content of the Green Fluorescent Protein (GFP) gene from Aequorea victoria. Found 58.3% GC content, indicating high thermostability. Optimal primer Tm calculated at 64.2°C.",
        "result_snapshot": "GC Content: 58.3% | Length: 717 bp | Melting Temp: 87.6°C",
    },
    {
        "title": "ORF Discovery in Bacteriophage Lambda",
        "tool": "ORF Finder",
        "author": "Priya M.",
        "date": "2026-02-03",
        "summary": "Identified 3 forward and 2 reverse ORFs in a 2kb region of bacteriophage lambda DNA. The longest ORF (1,245 bp) corresponds to the tail fibre gene.",
        "result_snapshot": "ORFs found: 5 | Longest: 1,245 bp (forward frame +1)",
    },
    {
        "title": "Restriction Enzyme Map of pUC19",
        "tool": "Restriction Enzyme Cutter",
        "author": "Arjun R.",
        "date": "2026-02-20",
        "summary": "Mapped EcoRI, BamHI, and HindIII cut sites on the pUC19 plasmid (2,686 bp). EcoRI cuts once in the MCS, BamHI and HindIII also cut in the MCS — confirming the cloning site layout.",
        "result_snapshot": "EcoRI: 1 cut (pos 396) | BamHI: 1 cut (pos 418) | HindIII: 1 cut (pos 447)",
    },
    {
        "title": "Protein Translation of Insulin Gene",
        "tool": "DNA to Protein Translator",
        "author": "Meera K.",
        "date": "2026-03-10",
        "summary": "Translated the human insulin (INS) mRNA coding sequence (CDS) to protein. Verified that the signal peptide (24 aa) is cleaved, producing the mature preproinsulin chain.",
        "result_snapshot": "CDS: 333 bp | Protein: 110 aa | MW: 11.98 kDa",
    },
    {
        "title": "Primer Design for BRCA1 Exon 11",
        "tool": "Primer Design Advanced",
        "author": "Ananya T.",
        "date": "2026-03-25",
        "summary": "Designed primers to amplify a 450 bp region of BRCA1 exon 11. Forward primer Tm: 59.8°C, reverse primer Tm: 60.2°C. No primer dimers detected. GC clamp present at 3' end.",
        "result_snapshot": "Fwd: 5'-ATGGATTTACGGACC-3' (Tm 59.8°C) | Rev: 5'-TCAGCTGCTGTTAAT-3' (Tm 60.2°C)",
    },
]


def _generate_provenance(title: str, tool: str, summary: str, date_str: str) -> str:
    """Generate a SHA-256 provenance string for an entry."""
    payload = f"{title}|{tool}|{summary}|{date_str}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ── Session state ────────────────────────────────────────────────────────────
if "user_notebooks" not in st.session_state:
    st.session_state["user_notebooks"] = []

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_gallery, tab_publish = st.tabs([t("📖 Gallery"), t("✍️ Publish Entry")])

# ── Gallery tab ──────────────────────────────────────────────────────────────
with tab_gallery:
    st.subheader(t("📖 Community Notebooks"))

    all_notebooks = DEMO_NOTEBOOKS + st.session_state["user_notebooks"]
    for nb in all_notebooks:
        provenance = _generate_provenance(nb["title"], nb["tool"], nb["summary"], nb["date"])
        is_demo = nb in DEMO_NOTEBOOKS

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                label = "(demo)" if is_demo else ""
                st.markdown(f"### 📓 {nb['title']} {label}")
                st.caption(f"🔬 **Tool:** {nb['tool']} | 👤 **Author:** {nb['author']} | 📅 {nb['date']}")
                st.write(t(nb["summary"]))
                st.code(nb["result_snapshot"])
            with col2:
                with st.expander(t("🔗 Provenance")):
                    st.caption(t("SHA-256 hash of the entry:"))
                    st.code(provenance[:32] + "...", language=None)
                    st.caption(t("Full hash (click to copy):"))
                    st.code(provenance, language=None)

    if not st.session_state["user_notebooks"]:
        st.caption(t("💡 Publish your own entry in the 'Publish Entry' tab!"))

# ── Publish tab ──────────────────────────────────────────────────────────────
with tab_publish:
    st.subheader(t("✍️ Publish a Lab Notebook Entry"))

    with st.form("publish_entry"):
        title = st.text_input(t("Title:"), placeholder="e.g. My first BLAST search")
        tool = st.text_input(t("Tool used:"), placeholder="e.g. BLAST Local Search")
        author = st.text_input(t("Your name:"), placeholder="e.g. Student_42")
        summary = st.text_area(t("Result summary:"), height=120, placeholder="Describe what you did and what you found...")
        result_snapshot = st.text_input(t("Key result snapshot:"), placeholder="e.g. 3 hits found, E-value < 1e-10")

        submitted = st.form_submit_button(t("📤 Publish Entry"), type="primary", use_container_width=True)

    if submitted and title.strip() and summary.strip():
        entry = {
            "title": title.strip(),
            "tool": tool.strip() or "General",
            "author": author.strip() or "Anonymous",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "summary": summary.strip(),
            "result_snapshot": result_snapshot.strip() or "No snapshot provided.",
        }
        st.session_state["user_notebooks"].append(entry)
        provenance = _generate_provenance(entry["title"], entry["tool"], entry["summary"], entry["date"])

        st.success(t("✅ Entry published!"))

        # Share text
        share_text = (
            f"📓 I just published a lab notebook entry on Titan Bioinformatics Suite!\n"
            f"Title: {entry['title']}\n"
            f"Tool: {entry['tool']}\n"
            f"Provenance SHA-256: {provenance[:16]}...\n"
            f"🧬 Try it yourself!"
        )
        st.code(share_text)

st.markdown("---")
st.caption(t(
    "ℹ️ Entries are stored in Streamlit session state (browser-local). "
    "The SHA-256 provenance hash lets you verify that an entry has not been tampered with."
))

dr_titan_tip(
    "A lab notebook is a scientist's best friend! Document everything — even failed experiments "
    "teach you something. Your future self will thank you for good notes."
)