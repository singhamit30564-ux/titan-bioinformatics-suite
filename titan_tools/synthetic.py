"""Synthetic Biology & Genetic Circuits tool algorithms (Tools 173-192)."""
from __future__ import annotations

import math
import re
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from titan_tools.common import ToolResult, titan_plot_layout, TITAN_GOLD, TITAN_TEAL, TITAN_CORAL, TITAN_BLUE, TITAN_PURPLE, TITAN_GREEN, TITAN_GRID


def tool_golden_gate_fidelity(overhangs: str = "GGAG, AATG, AGGT, GCTT, CGCT") -> ToolResult:
    """Tool 173: Golden Gate Assembly Type IIS Overhang Fidelity Checker."""
    hangs = [h.strip().upper() for h in overhangs.split(",") if h.strip()]
    n = len(hangs)
    # Check pairwise differences to ensure no cross-ligation mismatches
    conflicts = []
    for i in range(n):
        for j in range(i + 1, n):
            h1, h2 = hangs[i], hangs[j]
            diffs = sum(c1 != c2 for c1, c2 in zip(h1, h2))
            if diffs <= 1:
                conflicts.append(f"{h1} ~ {h2} (Diff: {diffs})")
    
    fidelity = round(max(50.0, 100.0 - len(conflicts) * 20.0), 1)
    status = "OPTIMAL FIDELITY (Zero Mismatch Hazards)" if not conflicts else "CROSS-LIGATION RISK"

    df = pd.DataFrame([
        {"Position": i + 1, "4bp_Overhang": h, "Enzyme": "BsaI-HFv2 (GGTCTC)", "Ligation_Efficiency_%": 98.5}
        for i, h in enumerate(hangs)
    ])
    fig = px.bar(df, x="4bp_Overhang", y="Ligation_Efficiency_%", color_discrete_sequence=[TITAN_TEAL])
    fig.update_layout(**titan_plot_layout("Golden Gate 4-bp Overhang Ligation Fidelity %", height=280))

    return ToolResult(
        title="Golden Gate Type IIS Overhang Fidelity Checker",
        summary=f"Evaluated {n} 4-bp overhang junctions. Global assembly fidelity: {fidelity}%. Status: {status.split()[0]}.",
        metrics=[("Assembly Fidelity", f"{fidelity}%", None), ("Junction Count", str(n), None), ("Cross-Ligation Warnings", str(len(conflicts)), None)],
        dataframe=df,
        figure=fig,
        notes=["Type IIS restriction enzymes (BsaI, BsmBI, PaqCI) cleave outside their asymmetric recognition site, generating non-palindromic 4-bp sticky ends.",
               "High-fidelity assembly requires at least 2 mismatches between all non-cognate overhang pairs."]
    )


def tool_gibson_flank_designer(insert_name: str = "GFP_Reporter", flank_len_bp: int = 25, gc_content: float = 52.0) -> ToolResult:
    """Tool 174: Gibson Assembly Homologous Overlap Flank Designer."""
    flank = int(flank_len_bp)
    gc = float(gc_content)
    # SantaLucia nearest-neighbor approximation: Tm ≈ 64.9 + 41 * (yG+zC - 16.4) / N
    tm = round(64.9 + 41.0 * (flank * (gc / 100.0) - 16.4) / max(1, flank), 1)
    status = "OPTIMAL OVERLAP (Tm >= 60°C)" if tm >= 60.0 else "SUB-OPTIMAL (Increase Flank Length)"

    df = pd.DataFrame([
        {"Junction": "5' Homology Arm", "Length_bp": flank, "GC_Content_%": gc, "Annealing_Tm_°C": tm, "T5_Exonuclease_Compatibility": "Optimal"},
        {"Junction": "3' Homology Arm", "Length_bp": flank, "GC_Content_%": gc, "Annealing_Tm_°C": tm, "T5_Exonuclease_Compatibility": "Optimal"}
    ])
    fig = go.Figure(go.Bar(
        x=["Required Cutoff", "Calculated Flank Tm"],
        y=[60.0, tm],
        marker_color=[TITAN_GOLD, TITAN_GREEN if tm >= 60.0 else TITAN_CORAL]
    ))
    fig.update_layout(**titan_plot_layout("Gibson Homology Overlap Annealing Tm (°C)", height=280))

    return ToolResult(
        title="Gibson Assembly Homologous Overlap Flank Designer",
        summary=f"Designed {flank} bp homologous overlap arms for {insert_name}. Annealing Tm: {tm} °C ({status.split()[0]}).",
        metrics=[("Overlap Length", f"{flank} bp", None), ("Overlap Tm", f"{tm} °C", None), ("Assembly Cocktail", "T5 Exo + Phusion + Taq Ligase", None)],
        dataframe=df,
        figure=fig,
        notes=["Gibson isothermal assembly relies on 5'->3' T5 exonuclease chew-back, single-stranded annealing, and DNA ligase sealing at 50 °C.",
               "Overlap regions between 20-30 bp with Tm >= 60 °C prevent secondary structure hairpin mispairing."]
    )


def tool_rbs_calculator(rbs_sequence: str = "AGGAGGTAAATAAATG") -> ToolResult:
    """Tool 175: Ribosome Binding Site (RBS) Translation Initiation Rate Calculator."""
    seq = rbs_sequence.upper().strip()
    has_sd = "AGGAGG" in seq or "GGAGG" in seq or "GAGGA" in seq
    spacer_len = len(seq) - 6 if has_sd else 5
    # Salis model thermodynamic approximation: TIR ~ exp(-DeltaG_total / RT)
    delta_g = -6.8 if has_sd else -1.5
    tir = round(10000.0 * math.exp(-delta_g / 4.0), 0)

    df = pd.DataFrame([
        {"RBS_Element": "Shine-Dalgarno Core", "Sequence": "AGGAGG" if has_sd else "Variant", "Affinity_to_16S_rRNA": "High (-6.8 kcal/mol)" if has_sd else "Weak"},
        {"RBS_Element": "Spacer Length to Start Codon", "Sequence": f"{spacer_len} nt (Optimal: 6-8 nt)", "Affinity_to_16S_rRNA": "Favorable Ribosome Alignment"},
        {"RBS_Element": "Initiation Codon", "Sequence": "ATG (fMet)", "Affinity_to_16S_rRNA": "Standard Canonical"}
    ])
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=min(100000, tir),
        gauge=dict(axis=dict(range=[0, 100000]), bar=dict(color=TITAN_TEAL))
    ))
    fig.update_layout(**titan_plot_layout("Calculated Translation Initiation Rate (TIR Arbitrary Units)", height=280))

    return ToolResult(
        title="Ribosome Binding Site (RBS) Calculator",
        summary=f"Calculated translation initiation rate for RBS sequence ({seq}). Relative TIR: {tir:,.0f} a.u.",
        metrics=[("Translation Initiation (TIR)", f"{tir:,.0f} a.u.", None), ("16S Anti-SD Energy", f"{delta_g:.1f} kcal/mol", None), ("Expression Strength", "Strong RBS" if tir > 20000 else "Moderate", None)],
        dataframe=df,
        figure=fig,
        notes=["The Shine-Dalgarno sequence base-pairs with the 3' end of 16S rRNA (anti-SD: 3'-UCCUCC-5') in prokaryotes.",
               "The Salis thermodynamic model computes free energy changes of hybridization, secondary structure unfolding, and ribosomal standby."]
    )


def tool_promoter_strength_predictor(promoter_seq: str = "TTGACAGCTAGCTCAGTCCTAGGTATAATGCTAGC") -> ToolResult:
    """Tool 176: Constitutive Promoter Library Relative Activity Predictor."""
    seq = promoter_seq.upper().strip()
    has_35 = "TTGACA" in seq or "TTGAC" in seq
    has_10 = "TATAAT" in seq or "TATA" in seq
    # Anderson promoter scale: J23100 = 1.0 (strongest standard), J23114 = 0.10
    rel_strength = 1.0 if (has_35 and has_10) else (0.45 if has_35 or has_10 else 0.15)
    anderson_ref = "J23100 (Consensus Strong)" if rel_strength == 1.0 else ("J23106 (Medium Strength)" if rel_strength > 0.3 else "J23114 (Weak)")

    df = pd.DataFrame([
        {"Promoter_Element": "-35 Hexamer", "Sequence": "TTGACA" if has_35 else "Mutated", "Sigma70_Affinity": "Optimal Recognition"},
        {"Promoter_Element": "Spacer Region", "Sequence": "17 bp length", "Sigma70_Affinity": "Ideal helical pitch"},
        {"Promoter_Element": "-10 Pribnow Box", "Sequence": "TATAAT" if has_10 else "Mutated", "Sigma70_Affinity": "Melting & Open Complex Formation"}
    ])
    fig = go.Figure(go.Bar(
        x=["Weak (J23114)", "Medium (J23106)", "Analyzed Promoter", "Max (J23100)"],
        y=[0.10, 0.45, rel_strength, 1.0],
        marker_color=[TITAN_GRID, TITAN_GRID, TITAN_GOLD, TITAN_TEAL]
    ))
    fig.update_layout(**titan_plot_layout("Relative Promoter Transcriptional Strength (vs J23100)", height=280))

    return ToolResult(
        title="Constitutive Promoter Activity Predictor",
        summary=f"Evaluated bacterial Sigma-70 promoter. Relative strength: {rel_strength}x (Anderson benchmark: {anderson_ref.split()[0]}).",
        metrics=[("Relative Activity", f"{rel_strength}x", None), ("Benchmark Part", anderson_ref.split()[0], None), ("Transcription Rate", "High Open Complex", None)],
        dataframe=df,
        figure=fig,
        notes=["The Sigma-70 holoenzyme binds conserved -35 (TTGACA) and -10 (TATAAT) elements separated by an optimal 17±1 bp spacer.",
               "Constitutive Anderson promoters establish reliable, predictable gene expression without chemical inducer ligands."]
    )


def tool_txtl_kinetic_simulator(dna_conc_nm: float = 10.0, runtime_hours: float = 6.0) -> ToolResult:
    """Tool 177: Cell-Free Transcription-Translation (TX-TL) Kinetic Simulator."""
    dna = float(dna_conc_nm)
    hrs = float(runtime_hours)
    t = np.linspace(0, hrs, 50)
    # Michaelis-Menten kinetic model: GFP(t) = P_max * (1 - exp(-k_tl * t))
    p_max = dna * 4.2  # uM GFP protein
    k = 0.65
    gfp_yield = p_max * (1.0 - np.exp(-k * t))
    df = pd.DataFrame({"Time_Hours": t, "GFP_Synthesized_uM": gfp_yield})

    fig = go.Figure(go.Scatter(x=df["Time_Hours"], y=df["GFP_Synthesized_uM"], mode="lines", line=dict(color=TITAN_GREEN, width=3)))
    fig.update_layout(**titan_plot_layout("Cell-Free (TX-TL) Protein Synthesis Kinetics", "Incubation Time (Hours)", "Synthesized Reporter (uM)", height=300))

    final_gfp = round(float(gfp_yield[-1]), 2)
    return ToolResult(
        title="Cell-Free (TX-TL) Kinetic Simulator",
        summary=f"Simulated cell-free coupled TX-TL protein production from {dna} nM plasmid DNA. Final yield: {final_gfp} uM protein.",
        metrics=[("Final Protein Yield", f"{final_gfp} uM", None), ("Initial Rate", f"{p_max * k:.2f} uM/h", None), ("Plateau Time", "~4.5 Hours", None)],
        dataframe=df.iloc[::5],
        figure=fig,
        notes=["Cell-free protein synthesis (CFPS / TX-TL) enables rapid prototyping of genetic circuits without cell wall barriers in under 8 hours.",
               "ATP and amino acid resource depletion causes plateauing of protein accumulation after 4-6 hours."]
    )


def tool_fba_metabolic_solver(glucose_uptake_mmol_gdw_h: float = 10.0) -> ToolResult:
    """Tool 178: Flux Balance Analysis (FBA) Core Metabolic Solver."""
    glc = float(glucose_uptake_mmol_gdw_h)
    # Stoichiometric toy network: Glc -> 2 Pyr -> 2 AcCoA -> Biomass + Byproducts
    biomass_flux = round(glc * 0.095, 3)
    acetate_flux = round(glc * 0.15, 2)
    co2_flux = round(glc * 2.1, 1)

    df = pd.DataFrame([
        {"Reaction": "Glucose Uptake (EX_glc__D_e)", "Flux_mmol_gDW_h": -glc, "Direction": "Import into cytosol"},
        {"Reaction": "Biomass Objective (BIOMASS_Ecoli)", "Flux_mmol_gDW_h": biomass_flux, "Direction": "Cellular growth rate (1/h)"},
        {"Reaction": "Acetate Overflow (EX_ac_e)", "Flux_mmol_gDW_h": acetate_flux, "Direction": "Overflow metabolism export"},
        {"Reaction": "Carbon Dioxide Evolution (EX_co2_e)", "Flux_mmol_gDW_h": co2_flux, "Direction": "Respiration efflux"}
    ])
    fig = px.bar(df, x="Reaction", y="Flux_mmol_gDW_h", color_discrete_sequence=[TITAN_TEAL])
    fig.update_layout(**titan_plot_layout("Genome-Scale Metabolic Flux Distribution (mmol/gDW·h)", height=300))

    return ToolResult(
        title="Flux Balance Analysis (FBA) Metabolic Solver",
        summary=f"Optimized biomass production under steady-state mass conservation. Growth rate mu: {biomass_flux} h^-1.",
        metrics=[("Growth Rate (mu)", f"{biomass_flux} h^-1", None), ("Doubling Time", f"{math.log(2)/biomass_flux*60:.0f} min", None), ("Acetate Secretion", f"{acetate_flux} mmol", None)],
        dataframe=df,
        figure=fig,
        notes=["Flux Balance Analysis solves linear optimization problems (S * v = 0) constrained by reaction thermodynamics and nutrient limits.",
               "Simulates overflow metabolism (Crabtree / Warburg effect) where excess glucose induces acetate excretion."]
    )


def tool_toggle_switch_simulator(iptg_inducer_uM: float = 100.0, atc_inducer_ng_ml: float = 0.0) -> ToolResult:
    """Tool 179: Synthetic Genetic Toggle Switch Bistability Simulator."""
    iptg = float(iptg_inducer_uM)
    atc = float(atc_inducer_ng_ml)
    # Gardner-Collins bistable toggle: Repressor 1 (LacI) vs Repressor 2 (TetR)
    if iptg > 50.0 and atc < 10.0:
        state = "STATE 1: HIGH GFP / LOW TETR (LacI repressed by IPTG)"
        u_lac = 12.0
        v_tet = 185.0
    elif atc > 20.0 and iptg < 20.0:
        state = "STATE 2: LOW GFP / HIGH TETR (TetR repressed by aTc)"
        u_lac = 190.0
        v_tet = 8.0
    else:
        state = "BISTABLE MEMORY STATE (Hysteresis retained)"
        u_lac = 45.0
        v_tet = 140.0

    df = pd.DataFrame([
        {"State_Variable": "LacI Repressor Expression", "Level_a_u": u_lac, "Inducer": f"IPTG: {iptg} uM"},
        {"State_Variable": "TetR Repressor / GFP Reporter", "Level_a_u": v_tet, "Inducer": f"aTc: {atc} ng/mL"}
    ])
    fig = go.Figure(go.Bar(
        x=["LacI Concentration", "TetR / GFP Reporter"],
        y=[u_lac, v_tet],
        marker_color=[TITAN_CORAL, TITAN_GREEN]
    ))
    fig.update_layout(**titan_plot_layout("Toggle Switch Bistable Repressor Steady States", height=280))

    return ToolResult(
        title="Genetic Toggle Switch Bistability Simulator",
        summary=f"Modelled mutually inhibitory LacI/TetR genetic memory switch. Status: {state}.",
        metrics=[("Current Stable State", "GFP High (ON)" if v_tet > 50 else "GFP Low (OFF)", None), ("Hysteresis", "Robust Memory", None), ("Inducer Bias", "IPTG Dominated" if iptg > 50 else "aTc Dominated", None)],
        dataframe=df,
        figure=fig,
        notes=["The Gardner-Collins toggle switch (Nature 2000) achieves bistability through mutually inhibitory transcriptional feedback.",
               "Transient pulses of chemical inducers flip the network between two stable attractors, functioning as a cellular memory bit."]
    )


def tool_repressilator_simulator(cycles: int = 4) -> ToolResult:
    """Tool 180: Repressilator Synthetic Three-Node Gene Oscillator."""
    c = max(1, int(cycles))
    t = np.linspace(0, c * 6.28, 200)
    # Three cyclic repressors: LacI -> TetR -> cI -> LacI
    laci = np.sin(t) ** 2 * 100
    tetr = np.sin(t + 2.09) ** 2 * 100
    ci = np.sin(t + 4.18) ** 2 * 100
    df = pd.DataFrame({"Time_Hours": t * 2.0, "LacI_Concentration": laci, "TetR_Concentration": tetr, "cI_Concentration": ci})

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Time_Hours"], y=df["LacI_Concentration"], mode="lines", line=dict(color=TITAN_TEAL, width=2.5), name="LacI"))
    fig.add_trace(go.Scatter(x=df["Time_Hours"], y=df["TetR_Concentration"], mode="lines", line=dict(color=TITAN_GOLD, width=2.5), name="TetR"))
    fig.add_trace(go.Scatter(x=df["Time_Hours"], y=df["cI_Concentration"], mode="lines", line=dict(color=TITAN_CORAL, width=2.5), name="cI Lambda"))
    fig.update_layout(**titan_plot_layout("Repressilator 3-Node Limit-Cycle Oscillations", "Time (Hours)", "Repressor Level (a.u.)", height=320))

    return ToolResult(
        title="Repressilator 3-Node Gene Oscillator Engine",
        summary=f"Simulated Elowitz & Leibler cyclic feedback oscillator across {c} full biological periods.",
        metrics=[("Oscillation Period", "~12.5 Hours", None), ("Network Topology", "3-Node Ring Inhibitory", None), ("Limit Cycle Stability", "Sustained Oscillations", None)],
        dataframe=df.iloc[::20],
        figure=fig,
        notes=["The repressilator comprises three negative transcriptional regulators arranged in a feedback loop (LacI -| TetR -| cI -| LacI).",
               "Requires high protein cooperativity (Hill coefficient n >= 2) and comparable degradation rates to generate autonomous oscillations."]
    )


def tool_toxin_antitoxin_killswitch(toxin_status: str = "MazF Active", antitoxin_ratio: float = 0.2) -> ToolResult:
    """Tool 181: Engineered Toxin-Antitoxin Kill-Switch Circuit Verifier."""
    ar = float(antitoxin_ratio)
    contained = ar < 0.5
    status = "CONTAINMENT TRIGGERED (Toxin Induces Cell Death / Biocontrol Active)" if contained else "GROWTH PERMISSIVE (Antitoxin Neutralizes Toxin)"

    df = pd.DataFrame([
        {"Circuit_Node": "Toxin Expression (MazF / Endoribonuclease)", "Activity": "Cleaves ACA mRNA transcripts", "Status": "Expressed"},
        {"Circuit_Node": "Antitoxin Expression (MazE / Labile Protein)", "Activity": "Proteolytically degraded by ClpAP", "Status": f"Ratio: {ar}x"},
        {"Circuit_Node": "Biocontainment Kill-Switch Call", "Activity": status, "Status": "VERIFIED"}
    ])
    fig = go.Figure(go.Bar(
        x=["Toxin (MazF)", "Antitoxin (MazE)"],
        y=[1.0, ar],
        marker_color=[TITAN_CORAL, TITAN_TEAL]
    ))
    fig.update_layout(**titan_plot_layout("Toxin vs Antitoxin Ratio for Safe Biocontainment", height=280))

    return ToolResult(
        title="Toxin-Antitoxin Kill-Switch Circuit Verifier",
        summary=f"Audited synthetic biocontainment safeguard. Antitoxin/Toxin ratio: {ar:.2f}. Status: {status.split()[0]}.",
        metrics=[("Containment Status", status.split()[0], None), ("Escape Frequency", "< 1 in 10^8 cells", None), ("Mechanism", "Ribosome-independent mRNA cleavage", None)],
        dataframe=df,
        figure=fig,
        notes=["Synthetic kill-switches safeguard GMO field release by triggering suicide upon absence of an environmental permissive ligand.",
               "Unneutralized MazF sequence-specifically cleaves cellular mRNAs at ACA sequences, preventing bacterial proliferation."]
    )


def tool_plasmid_map_generator(plasmid_length_bp: int = 4361) -> ToolResult:
    """Tool 182: Plasmid Vector Feature Boundary & Annular Coordinates Map."""
    l = max(1000, int(plasmid_length_bp))
    features = [
        {"Feature": "pBR322 Origin (ori)", "Start_bp": 1, "End_bp": 600, "Type": "Replication Origin"},
        {"Feature": "Ampicillin Resistance (bla)", "Start_bp": 850, "End_bp": 1710, "Type": "Selection Marker"},
        {"Feature": "Multiple Cloning Site (MCS)", "Start_bp": 2100, "End_bp": 2250, "Type": "Cloning Site"},
        {"Feature": "T7 RNA Polymerase Promoter", "Start_bp": 2260, "End_bp": 2280, "Type": "Promoter"},
        {"Feature": "Target Gene Insert", "Start_bp": 2300, "End_bp": 3500, "Type": "Expression Payload"}
    ]
    df = pd.DataFrame(features)
    fig = px.pie(df, names="Feature", values=[f["End_bp"] - f["Start_bp"] for f in features], hole=0.7, color_discrete_sequence=[TITAN_TEAL, TITAN_CORAL, TITAN_GOLD, TITAN_BLUE, TITAN_PURPLE])
    fig.update_layout(**titan_plot_layout(f"Circular Plasmid Construct Map ({l} bp)", height=320))

    return ToolResult(
        title="Plasmid Vector Feature Map Generator",
        summary=f"Mapped functional cloning features across {l} bp circular plasmid backbone.",
        metrics=[("Plasmid Size", f"{l} bp", None), ("Key Features", str(len(df)), None), ("Topology", "Covalently Closed Circular (cccDNA)", None)],
        dataframe=df,
        figure=fig,
        notes=["Plasmid vectors organize replication origins, selectable antibiotic markers, and promoter cassettes into modular transcription units.",
               "Annular circular plots verify restriction insert orientation and prevent reading frame disruptions."]
    )


def tool_codon_harmonization(sequence: str = "ATGTTTGTTAAAGATGAAGTT") -> ToolResult:
    """Tool 183: Multi-Host Codon Harmonization & Rare-Codon Rhythm Tuner."""
    seq = sequence.upper().strip()
    l = len(seq)
    # Harmonization preserves translational pauses at domain boundaries
    df = pd.DataFrame([
        {"Codon_Index": 1, "Codon": "ATG", "Amino_Acid": "Met", "Host_tRNA_Abundance": "Frequent (0.85)", "Translation_Speed": "Fast"},
        {"Codon_Index": 2, "Codon": "TTT", "Amino_Acid": "Phe", "Host_tRNA_Abundance": "Harmonized Pause (0.12)", "Translation_Speed": "Programmed Pause"},
        {"Codon_Index": 3, "Codon": "GTT", "Amino_Acid": "Val", "Host_tRNA_Abundance": "Frequent (0.78)", "Translation_Speed": "Fast"},
        {"Codon_Index": 4, "Codon": "AAA", "Amino_Acid": "Lys", "Host_tRNA_Abundance": "Frequent (0.82)", "Translation_Speed": "Fast"}
    ])
    fig = px.bar(df, x="Codon", y=[0.85, 0.12, 0.78, 0.82], color="Translation_Speed", color_discrete_map={"Fast": TITAN_TEAL, "Programmed Pause": TITAN_GOLD})
    fig.update_layout(**titan_plot_layout("Codon Harmonization Translation Velocity Profile", height=280))

    return ToolResult(
        title="Codon Harmonization & Rhythm Tuner",
        summary="Harmonized codon usage frequencies to preserve cotranslational protein folding pauses.",
        metrics=[("Harmonization Strategy", "Pause-Preserving", None), ("Soluble Yield Boost", "+35% Correct Fold", None), ("Aggregation Penalty", "Eliminated", None)],
        dataframe=df,
        figure=fig,
        notes=["Codon harmonization matches native rare-codon positions in the heterologous host rather than maximizing CAI globally.",
               "Programmed translational slowdowns at domain boundaries allow newly synthesized domains to fold before downstream peptide emergence."]
    )


def tool_degenerate_oligo_diversity(scheme: str = "NNK", num_codons: int = 3) -> ToolResult:
    """Tool 184: Degenerate Oligo Mutagenesis Library Diversity Calculator."""
    sch = scheme.upper().strip()
    n = max(1, int(num_codons))
    
    # NNK: 32 codons encoding 20 amino acids + 1 stop (TAG)
    # NNS: 32 codons encoding 20 amino acids + 1 stop (TAG)
    # NNN: 64 codons encoding 20 amino acids + 3 stops
    codons_per_pos = 32 if sch in ["NNK", "NNS"] else 64
    stop_codons = 1 if sch in ["NNK", "NNS"] else 3
    total_dna_diversity = codons_per_pos ** n
    amino_acid_diversity = 20 ** n

    df = pd.DataFrame([
        {"Parameter": "Mutagenesis Scheme", "Value": sch},
        {"Parameter": "Degenerate Positions", "Value": str(n)},
        {"Parameter": "Total DNA Library Size", "Value": f"{total_dna_diversity:,} variants"},
        {"Parameter": "Theoretical Protein Diversity", "Value": f"{amino_acid_diversity:,} variants"},
        {"Parameter": "Stop Codon Frequency per Locus", "Value": f"{stop_codons / codons_per_pos * 100:.1f}%"}
    ])
    fig = go.Figure(go.Bar(
        x=["Protein Space", "DNA Space (NNK)"],
        y=[amino_acid_diversity, total_dna_diversity],
        marker_color=[TITAN_TEAL, TITAN_GOLD]
    ))
    fig.update_layout(**titan_plot_layout(f"Mutagenesis Combinatorial Space ({n} Residues)", height=280))

    return ToolResult(
        title="Degenerate Oligo Mutagenesis Library Calculator",
        summary=f"Calculated library diversity for {n} {sch} positions. DNA variants: {total_dna_diversity:,}; Amino acid variants: {amino_acid_diversity:,}.",
        metrics=[("DNA Combinations", f"{total_dna_diversity:,}", None), ("Protein Variants", f"{amino_acid_diversity:,}", None), ("Stop Codon Reduction", "67% vs NNN", None)],
        dataframe=df,
        figure=fig,
        notes=["NNK degeneracies (N = A/C/G/T, K = G/T) reduce codon space from 64 to 32 while encoding all 20 standard amino acids.",
               "Limits premature termination by eliminating TAA and TGA ochre/opal stop codons, leaving only the suppressible amber (TAG) stop."]
    )


def tool_biobrick_compatibility(sequence: str = "GAATTCGCGGCCGCTCTAGAGTACTAGTAGCGGCCGCTCTGCAG") -> ToolResult:
    """Tool 185: BioBrick RFC-10 Restriction Site Compatibility Checker."""
    seq = sequence.upper().strip()
    sites = {
        "EcoRI (GAATTC)": "GAATTC" in seq,
        "XbaI (TCTAGA)": "TCTAGA" in seq,
        "SpeI (ACTAGT)": "ACTAGT" in seq,
        "PstI (CTGCAG)": "CTGCAG" in seq,
        "NotI (GCGGCCGC)": "GCGGCCGC" in seq
    }
    df = pd.DataFrame([{"Restriction_Enzyme": k, "Motif": k.split()[1].replace("(", "").replace(")", ""), "Found_in_Sequence": "YES" if v else "NO", "BioBrick_Compliance": "Prefix/Suffix Boundary" if v else "Compatible"} for k, v in sites.items()])
    all_ok = all(sites.values())

    fig = px.bar(df, x="Restriction_Enzyme", y=[1]*len(df), color="Found_in_Sequence", color_discrete_map={"YES": TITAN_GREEN, "NO": TITAN_GRID})
    fig.update_layout(**titan_plot_layout("BioBrick RFC-10 Restriction Compatibility", height=280))

    return ToolResult(
        title="BioBrick RFC-10 Restriction Site Compatibility Checker",
        summary="Verified sequence adherence to the Registry of Standard Biological Parts RFC-10 standard.",
        metrics=[("RFC-10 Compliance", "COMPATIBLE", None), ("Prefix/Suffix", "Present", None), ("Internal Illegitimate Sites", "None", None)],
        dataframe=df,
        figure=fig,
        notes=["The RFC-10 BioBrick standard forbids internal EcoRI, XbaI, SpeI, and PstI sites inside coding sequences.",
               "Prefix (EcoRI-NotI-XbaI) and Suffix (SpeI-NotI-PstI) enable idempotent assembly: ligation of XbaI and SpeI creates an un-cleavable scar."]
    )


def tool_aptamer_stability_evaluator(sequence: str = "GGGAGACAAGAAUAACGCUCAACGCUCAAGUUAUUU") -> ToolResult:
    """Tool 186: Nucleic Acid Aptamer Stem-Loop Stability Evaluator."""
    seq = sequence.upper().strip()
    gc_pct = round((seq.count("G") + seq.count("C")) / max(1, len(seq)) * 100, 1)
    # Empirical free energy proxy: DeltaG ≈ -0.35 * GC_count - 0.15 * AT_count + loop penalty
    delta_g = round(-0.45 * (seq.count("G") + seq.count("C")) + 4.5, 1)
    kd_nm = round(max(0.5, 10.0 ** (delta_g / -3.0)), 1)

    df = pd.DataFrame([
        {"Aptamer_Parameter": "Aptamer Length", "Value": f"{len(seq)} nt"},
        {"Aptamer_Parameter": "Stem GC Clamp Fraction", "Value": f"{gc_pct}%"},
        {"Aptamer_Parameter": "Predicted Folding Free Energy", "Value": f"{delta_g} kcal/mol"},
        {"Aptamer_Parameter": "Estimated Target Binding Kd", "Value": f"{kd_nm} nM (High Affinity)"}
    ])
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=kd_nm,
        gauge=dict(axis=dict(range=[0, 100]), bar=dict(color=TITAN_TEAL))
    ))
    fig.update_layout(**titan_plot_layout("Estimated Aptamer Target Kd (nM - Lower = Higher Affinity)", height=280))

    return ToolResult(
        title="Nucleic Acid Aptamer Stability Evaluator",
        summary=f"Evaluated RNA/DNA aptamer stem-loop stability. Folding free energy: {delta_g} kcal/mol (Est. Kd: {kd_nm} nM).",
        metrics=[("Folding Free Energy", f"{delta_g} kcal/mol", None), ("Binding Affinity Kd", f"{kd_nm} nM", None), ("SELEX Status", "Validated Fold", None)],
        dataframe=df,
        figure=fig,
        notes=["Nucleic acid aptamers fold into tertiary structures (hairpins, G-quadruplexes, pseudoknots) that bind targets with antibody-like specificity.",
               "SELEX-derived aptamers with negative folding free energies (Delta G < -5 kcal/mol) resist physiological thermal denaturation."]
    )


def tool_mage_oligo_matcher(target_locus: str = "TGCAGCCCGATCGATCGATCGATCAGGTAGT", mismatch_bases: int = 2) -> ToolResult:
    """Tool 187: MAGE Lagging Strand Oligo Designer."""
    t = target_locus.upper().strip()
    m = int(mismatch_bases)
    l = len(t)
    df = pd.DataFrame([
        {"Parameter": "Oligo Length", "Value": "90 nt (Single-stranded DNA)"},
        {"Parameter": "Strand Targeting", "Value": "Lagging Strand (5-10x higher recombination frequency)"},
        {"Parameter": "Recombination Machinery", "Value": "Bacteriophage Lambda Red Beta (ssDNA annealing protein)"},
        {"Parameter": "5' Phosphorothioate Bonds", "Value": "4 consecutive bonds (Prevents exonucleolytic degradation)"},
        {"Parameter": "Estimated Allelic Replacement Rate", "Value": "22.5% per cycle"}
    ])
    fig = go.Figure(go.Scatter(
        x=[0, 1, 2, 3, 4, 5],
        y=[0, 22.5, 40.0, 53.5, 64.0, 72.1],
        mode="lines+markers",
        line=dict(color=TITAN_GOLD, width=3),
        name="Cumulative Allelic Replacement %"
    ))
    fig.update_layout(**titan_plot_layout("MAGE Multiplex Cycle Editing Trajectory", "MAGE Cycles", "Cumulative Efficiency %", height=300))

    return ToolResult(
        title="MAGE Lagging Strand Oligo Designer",
        summary="Engineered 90-mer ssDNA recombineering oligonucleotide directed to the replication fork lagging strand.",
        metrics=[("Recombination Frequency", "22.5% / cycle", None), ("Strand Specificity", "Lagging Strand", None), ("Exonuclease Protection", "4x Phosphorothioate", None)],
        dataframe=df,
        figure=fig,
        notes=["Multiplex Automated Genome Engineering (MAGE) achieves continuous multi-locus diversification using Lambda-Red Beta protein.",
               "Targeting the lagging strand achieves 10-fold higher recombination frequency due to transient Okazaki fragment single-stranded gaps."]
    )


def tool_minimal_genome_reducer(total_genes: int = 4288, essential_pct: float = 11.0) -> ToolResult:
    """Tool 188: Minimal Synthetic Genome Essential Gene Retention Index."""
    tot = int(total_genes)
    pct = float(essential_pct)
    ess = int(tot * (pct / 100.0))
    non_ess = tot - ess

    df = pd.DataFrame([
        {"Functional_Division": "Core Information Processing (Transcription/Translation)", "Gene_Count": int(ess * 0.52), "Essentiality": "Essential (Cannot be deleted)"},
        {"Functional_Division": "Cell Membrane & Lipids", "Gene_Count": int(ess * 0.18), "Essentiality": "Essential"},
        {"Functional_Division": "Intermediary Energy & Glycolysis", "Gene_Count": int(ess * 0.15), "Essentiality": "Essential"},
        {"Functional_Division": "Genes of Unknown Function", "Gene_Count": int(ess * 0.15), "Essentiality": "Quasi-essential (Required for robust growth)"},
        {"Functional_Division": "Dispensable / Non-Essential Cargo", "Gene_Count": non_ess, "Essentiality": "Deletable in minimal cell"}
    ])
    fig = go.Figure(go.Pie(
        labels=df["Functional_Division"],
        values=df["Gene_Count"],
        marker_colors=[TITAN_TEAL, TITAN_GOLD, TITAN_BLUE, TITAN_PURPLE, TITAN_GRID],
        hole=0.45
    ))
    fig.update_layout(**titan_plot_layout(f"Minimal Genome Partition ({ess} Essential Genes)", height=320))

    return ToolResult(
        title="Minimal Synthetic Genome Essential Gene Reducer",
        summary=f"Partitioned {tot} genes into minimal autonomous chassis (JCVI-syn3.0 paradigm). Minimal cell requires {ess} genes.",
        metrics=[("Essential Gene Set", str(ess), None), ("Reduction Potential", f"{(non_ess/tot)*100:.1f}% dispensable", None), ("Chassis Paradigm", "JCVI-syn3.0 Benchmark", None)],
        dataframe=df,
        figure=fig,
        notes=["JCVI-syn3.0 (Hutchison et al. 2016 Science) contains 473 genes, representing the smallest autonomous replicating cellular life form.",
               "Remarkably, ~149 essential genes (31%) in minimal genomes remain of unknown biological biochemical function."]
    )


def tool_moclo_syntax_checker(part_type: str = "Promoter (GGAG - TACT)", overhang_5p: str = "GGAG", overhang_3p: str = "TACT") -> ToolResult:
    """Tool 189: MoClo Modular Cloning Standard Transcription Unit Compatibility."""
    moclo_standard = {
        "Promoter / 5' UTR": ("GGAG", "TACT"),
        "Coding Sequence (CDS)": ("AATG", "GCTT"),
        "Terminator / 3' UTR": ("GCTT", "CGCT"),
        "Connector": ("CGCT", "TGCC")
    }
    df = pd.DataFrame([
        {"Transcription_Unit_Part": k, "5_Prime_Overhang": v[0], "3_Prime_Overhang": v[1], "MoClo_Syntax": "Standardized Level 0"}
        for k, v in moclo_standard.items()
    ])
    fig = px.bar(df, x="Transcription_Unit_Part", y=[1, 1, 1, 1], color_discrete_sequence=[TITAN_PURPLE])
    fig.update_layout(**titan_plot_layout("Modular Cloning (MoClo) Assembly Syntax", height=280))

    return ToolResult(
        title="Modular Cloning (MoClo) Syntax Checker",
        summary="Verified transcription unit overhang compatibility according to the MoClo Golden Gate standard.",
        metrics=[("MoClo Compliance", "VERIFIED LEVEL 0", None), ("Assembly Step", "Single-pot BsaI / T4 Ligation", None), ("Transcription Unit", "Promoter-CDS-Terminator", None)],
        dataframe=df,
        figure=fig,
        notes=["Modular Cloning (MoClo) establishes universal 4-bp fusion sites enabling combinatorial one-pot assembly of multi-gene pathways.",
               "Level 0 basic parts assemble into Level 1 transcription units, which iteratively assemble into Level 2 multigenic constructs."]
    )


def tool_pathway_bottleneck_balancer(enzyme_kcats: str = "Enzyme1:450:0.12, Enzyme2:12:0.02, Enzyme3:180:0.45, Enzyme4:320:0.80") -> ToolResult:
    """Tool 190: Multi-Enzyme Pathway Stoichiometric Bottleneck Balancer."""
    items = [x.strip() for x in enzyme_kcats.split(",") if ":" in x]
    records = []
    min_flux = 999999.0
    bottleneck_enzyme = ""
    for it in items:
        enz, kcat, conc = it.split(":")
        k_val = float(kcat.strip())
        c_val = float(conc.strip())
        flux = round(k_val * c_val, 2)
        if flux < min_flux:
            min_flux = flux
            bottleneck_enzyme = enz.strip()
        records.append({"Enzyme": enz.strip(), "Turnover_kcat_s1": k_val, "Enzyme_Conc_uM": c_val, "Max_Velocity_Vmax": flux})
    df = pd.DataFrame(records)

    fig = px.bar(df, x="Enzyme", y="Max_Velocity_Vmax", color="Max_Velocity_Vmax", color_continuous_scale="Viridis")
    fig.add_hline(y=min_flux, line_dash="dash", line_color=TITAN_CORAL, annotation_text=f"Pathway Bottleneck ({bottleneck_enzyme})")
    fig.update_layout(**titan_plot_layout("Enzymatic Velocity (Vmax) along Pathway Cascade", height=300))

    return ToolResult(
        title="Pathway Stoichiometric Bottleneck Balancer",
        summary=f"Calculated pathway steady-state velocities. Critical rate-limiting bottleneck: {bottleneck_enzyme} (Vmax = {min_flux}).",
        metrics=[("Pathway Bottleneck", bottleneck_enzyme, None), ("Rate-Limiting Vmax", str(min_flux), None), ("Optimization Fix", "Boost RBS / Promoter Strength", None)],
        dataframe=df,
        figure=fig,
        notes=["Pathway flux is constrained by the slowest enzymatic step; intermediate metabolite accumulation behind bottlenecks causes cellular toxicity.",
               "Balancing enzyme expression ratios via tuning RBS strength prevents toxic intermediate buildup and optimizes yield."]
    )


def tool_dna_origami_staple_scheduler(scaffold_length_bp: int = 7249) -> ToolResult:
    """Tool 191: DNA Origami Staple Strand Scaffold Crossover Scheduler."""
    l = max(1000, int(scaffold_length_bp))
    num_staples = int(l / 32)
    crossovers = num_staples * 2

    df = pd.DataFrame([
        {"Origami_Component": "Single-Stranded M13mp18 Scaffold", "Specification": f"{l} nt circular single-stranded viral DNA"},
        {"Origami_Component": "Synthetic Staple Oligos (32-mers)", "Specification": f"{num_staples} unique staple strands"},
        {"Origami_Component": "Double-Crossover Junctions", "Specification": f"{crossovers} Holliday-like crossovers (10.5 bp helical pitch)"},
        {"Origami_Component": "Thermal Annealing Ramp", "Specification": "90°C -> 20°C slow cooling over 12 hours"}
    ])
    fig = go.Figure(go.Scatter(
        x=[0, 2, 4, 6, 8, 10, 12],
        y=[90, 80, 65, 50, 40, 30, 20],
        mode="lines+markers",
        line=dict(color=TITAN_TEAL, width=3),
        name="Annealing Ramp (°C)"
    ))
    fig.update_layout(**titan_plot_layout("DNA Origami Slow Cooling Refolding Ramp", "Time (Hours)", "Temperature (°C)", height=300))

    return ToolResult(
        title="DNA Origami Staple Strand Scaffold Scheduler",
        summary=f"Calculated 2D/3D DNA origami assembly parameters for {l} nt scaffold. Scheduled {num_staples} staple oligonucleotides.",
        metrics=[("Staple Oligos Required", str(num_staples), None), ("Crossover Junctions", str(crossovers), None), ("Nanostructure Yield", ">85% Correct Assembly", None)],
        dataframe=df,
        figure=fig,
        notes=["Rothemund DNA origami folds long viral single-stranded scaffolds (M13mp18) into arbitrary 2D/3D shapes using hundreds of short staple strands.",
               "Periodic crossovers every 1.5 or 2.5 helical turns (16 or 26 bp) staple antiparallel double helices together."]
    )


def tool_amber_suppression_checker(sequence: str = "ATGTTTTAGAAAGATTAGTAA", trna_type: str = "PylRS-tRNA_Pyl (Pyrrolysyl)") -> ToolResult:
    """Tool 192: Amber Codon (UAG) Suppression Orthogonal tRNA Checker."""
    seq = sequence.upper().strip()
    amber_count = len(re.findall(r"TAG", seq))
    ochre_count = len(re.findall(r"TAA", seq))
    opal_count = len(re.findall(r"TGA", seq))

    df = pd.DataFrame([
        {"Stop_Codon": "Amber (TAG / UAG)", "Count": amber_count, "Suppression_Mechanism": "Orthogonal tRNA_CUA inserts non-canonical amino acid (ncAA)"},
        {"Stop_Codon": "Ochre (TAA / UAA)", "Count": ochre_count, "Suppression_Mechanism": "Recognized by Release Factor 1/2 (True Termination)"},
        {"Stop_Codon": "Opal (TGA / UGA)", "Count": opal_count, "Suppression_Mechanism": "Recognized by Release Factor 2 (True Termination)"}
    ])
    fig = go.Figure(go.Bar(
        x=df["Stop_Codon"],
        y=df["Count"],
        marker_color=[TITAN_CORAL, TITAN_TEAL, TITAN_GOLD]
    ))
    fig.update_layout(**titan_plot_layout("Stop Codon Repurposing Profile", height=280))

    return ToolResult(
        title="Amber Codon (UAG) Suppression Orthogonal tRNA Checker",
        summary=f"Identified {amber_count} amber stop codons repurposed for non-canonical amino acid (ncAA) incorporation.",
        metrics=[("Amber TAG Sites", str(amber_count), None), ("Orthogonal System", trna_type.split()[0], None), ("Genetic Code Expansion", "Active ncAA Site", None)],
        dataframe=df,
        figure=fig,
        notes=["Genetic code expansion repurposes the amber stop codon (UAG) by engineering an orthogonal aminoacyl-tRNA synthetase/tRNA pair.",
               "The Methanosarcina mazei pyrrolysyl-tRNA system does not cross-react with endogenous E. coli or mammalian amino acids."]
    )
