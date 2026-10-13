"""🧪 Virtual Lab Simulator — Three interactive experiments with step-by-step guidance.

Experiments: DNA Extraction, Gel Electrophoresis, PCR.
Progress is saved in session_state. Wrong steps trigger failure with explanation.
"""
from __future__ import annotations

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🧪",
    "Virtual Lab Simulator",
    "Hands-on step-by-step experiments: DNA Extraction, Gel Electrophoresis, and PCR — all simulated in your browser.",
)

# ── Experiment definitions ──────────────────────────────────────────────────

EXPERIMENTS = {
    "dna_extraction": {
        "name": "🧬 DNA Extraction",
        "description": "Extract DNA from a cheek cell sample using household reagents.",
        "steps": [
            {"id": "collect", "label": "Collect cheek cell sample with mouthwash", "correct": True, "explain_fail": "You must collect cells first!"},
            {"id": "lysis", "label": "Add lysis buffer (detergent + salt) to break open cells", "correct": True, "explain_fail": "Cell lysis is needed to release DNA from the nucleus."},
            {"id": "incubate", "label": "Incubate at 60°C for 10 minutes", "correct": True, "explain_fail": "Heat helps denature proteins and dissolve lipids."},
            {"id": "filter", "label": "Filter the mixture through cheesecloth/coffee filter", "correct": True, "explain_fail": "Filtration removes cell debris, leaving DNA in solution."},
            {"id": "precipitate", "label": "Layer cold ethanol on top of the filtrate", "correct": True, "explain_fail": "DNA is insoluble in cold ethanol — it precipitates at the interface."},
            {"id": "spool", "label": "Spool out the white DNA strands with a glass rod", "correct": True, "explain_fail": "Spooling collects the precipitated DNA fibres."},
        ],
        "score_per_step": 15,
        "bonus": 10,
    },
    "gel_electrophoresis": {
        "name": "⚡ Gel Electrophoresis",
        "description": "Separate DNA fragments by size using an agarose gel.",
        "steps": [
            {"id": "prepare_gel", "label": "Prepare 1% agarose gel with TAE buffer", "correct": True, "explain_fail": "You need a gel matrix for fragments to migrate through."},
            {"id": "add_ethidium", "label": "Add ethidium bromide / safe stain to the gel", "correct": True, "explain_fail": "A DNA stain lets you visualise bands under UV light."},
            {"id": "load_samples", "label": "Load DNA ladder and samples into wells", "correct": True, "explain_fail": "Samples must be pipetted into the wells before running."},
            {"id": "run_gel", "label": "Run the gel at 100V for 45 minutes", "correct": True, "explain_fail": "Electric current drives DNA through the gel — smaller fragments move faster."},
            {"id": "visualise", "label": "Visualise bands under UV / blue light", "correct": True, "explain_fail": "You can't see DNA bands without a transilluminator or blue light."},
            {"id": "analyse", "label": "Estimate fragment sizes by comparing to the DNA ladder", "correct": True, "explain_fail": "The ladder is your molecular ruler — always compare bands to it!"},
        ],
        "score_per_step": 15,
        "bonus": 10,
    },
    "pcr": {
        "name": "🔬 PCR (Polymerase Chain Reaction)",
        "description": "Amplify a target DNA sequence through repeated thermal cycles.",
        "steps": [
            {"id": "design_primers", "label": "Design forward and reverse primers flanking the target", "correct": True, "explain_fail": "Primers define the region to amplify — you can't skip this!"},
            {"id": "prepare_mix", "label": "Prepare PCR master mix (Taq pol, dNTPs, buffer, primers, template)", "correct": True, "explain_fail": "All reagents must be mixed before thermal cycling."},
            {"id": "denature", "label": "Denature at 94–95°C for 30 seconds", "correct": True, "explain_fail": "High heat separates the double-stranded template into single strands."},
            {"id": "anneal", "label": "Anneal primers at 50–65°C for 30 seconds", "correct": True, "explain_fail": "Primers bind to their complementary sequences at the annealing temperature."},
            {"id": "extend", "label": "Extend at 72°C for 1 minute per kilobase", "correct": True, "explain_fail": "Taq polymerase synthesises new DNA strands at 72°C."},
            {"id": "repeat_cycles", "label": "Repeat for 25–35 cycles, then hold at 4°C", "correct": True, "explain_fail": "Repeated cycles exponentially amplify the target — aim for 25–35 cycles!"},
        ],
        "score_per_step": 15,
        "bonus": 10,
    },
}

# ── Session state bootstrap ─────────────────────────────────────────────────
if "vlab_exp" not in st.session_state:
    st.session_state["vlab_exp"] = None
if "vlab_step" not in st.session_state:
    st.session_state["vlab_step"] = 0
if "vlab_score" not in st.session_state:
    st.session_state["vlab_score"] = 0
if "vlab_failed" not in st.session_state:
    st.session_state["vlab_failed"] = False
if "vlab_completed" not in st.session_state:
    st.session_state["vlab_completed"] = []
if "vlab_total_score" not in st.session_state:
    st.session_state["vlab_total_score"] = 0


def _reset_exp(exp_id: str) -> None:
    st.session_state["vlab_exp"] = exp_id
    st.session_state["vlab_step"] = 0
    st.session_state["vlab_score"] = 0
    st.session_state["vlab_failed"] = False


# ── Experiment selector ──────────────────────────────────────────────────────
exp_keys = list(EXPERIMENTS.keys())
exp = st.session_state["vlab_exp"]

if exp is None:
    st.subheader(t("Choose an Experiment"))
    cols = st.columns(3)
    for col, key in zip(cols, exp_keys):
        info = EXPERIMENTS[key]
        with col:
            with st.container(border=True):
                st.markdown(f"### {info['name']}")
                st.caption(t(info["description"]))
                completed = key in st.session_state["vlab_completed"]
                if completed:
                    st.success(t("✅ Completed"))
                if st.button(
                    t("Start Experiment"),
                    key=f"start_{key}",
                    use_container_width=True,
                    type="primary",
                ):
                    _reset_exp(key)
                    st.rerun()

    st.markdown("---")
    total = st.session_state["vlab_total_score"]
    st.metric(t("🏆 Total Lab Score"), f"{total} / 300")

else:
    info = EXPERIMENTS[exp]
    steps = info["steps"]
    current = st.session_state["vlab_step"]
    score = st.session_state["vlab_score"]
    max_score = len(steps) * info["score_per_step"] + info["bonus"]

    st.subheader(f"{info['name']}")
    st.caption(t(info["description"]))

    # Progress bar
    progress = current / len(steps)
    st.progress(progress, text=t("Step {cur} of {total}", cur=current, total=len(steps)))

    if st.session_state["vlab_failed"]:
        st.error(t("❌ Experiment Failed! You can retry."))
        if st.button(t("🔄 Retry Experiment"), type="primary"):
            _reset_exp(exp)
            st.rerun()
        if st.button(t("← Back to Experiments")):
            st.session_state["vlab_exp"] = None
            st.rerun()
        st.stop()

    if current >= len(steps):
        # Completed!
        score += info["bonus"]
        st.session_state["vlab_score"] = score
        st.balloons()
        st.success(t("🎉 Experiment Complete! Score: {score}/{max}", score=score, max=max_score))
        if exp not in st.session_state["vlab_completed"]:
            st.session_state["vlab_completed"].append(exp)
            st.session_state["vlab_total_score"] += score
        if st.button(t("← Back to Experiments")):
            st.session_state["vlab_exp"] = None
            st.rerun()
        dr_titan_tip(
            f"Great job completing {info['name']}! In a real lab, always wear gloves, "
            "safety goggles, and a lab coat. Protocols matter — precision prevents errors!"
        )
        st.stop()

    # Current step
    step = steps[current]
    st.markdown(f"### {t('Step')} {current + 1}: {t(step['label'])}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("✅ This is the next step"), use_container_width=True, type="primary"):
            st.session_state["vlab_score"] += info["score_per_step"]
            st.session_state["vlab_step"] += 1
            st.rerun()
    with col2:
        if st.button(t("❌ Skip / Wrong step"), use_container_width=True):
            st.session_state["vlab_failed"] = True
            st.rerun()

    # Hint
    with st.expander(t("💡 Hint — what should I do now?")):
        if current == 0:
            st.info(t("Think about what you need BEFORE you can start the experiment."))
        else:
            st.info(t("Review the previous step — what logically comes next in the protocol?"))

    if st.button(t("← Abandon Experiment")):
        st.session_state["vlab_exp"] = None
        st.rerun()

    dr_titan_tip(
        "In a real lab, protocols are your roadmap. Skipping a step can ruin weeks of work. "
        "Always read the full protocol before starting!"
    )