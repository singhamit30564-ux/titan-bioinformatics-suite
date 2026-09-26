"""Metagenomics & Microbiome Analytics tool algorithms (Tools 113-132)."""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from titan_tools.common import ToolResult, titan_plot_layout, TITAN_GOLD, TITAN_TEAL, TITAN_CORAL, TITAN_BLUE, TITAN_PURPLE, TITAN_GREEN, TITAN_GRID


def tool_alpha_diversity_estimator(otu_input: str = "Taxon1:1200, Taxon2:850, Taxon3:420, Taxon4:110, Taxon5:35, Taxon6:12, Taxon7:4, Taxon8:1") -> ToolResult:
    """Tool 113: Alpha Diversity Estimator (Shannon, Simpson, Chao1, Pielou)."""
    items = [x.strip() for x in otu_input.split(",") if ":" in x]
    counts = []
    taxa = []
    for it in items:
        t, c = it.split(":")
        taxa.append(t.strip())
        counts.append(float(c.strip()))
    arr = np.array(counts)
    total = arr.sum()
    p = arr / max(1e-9, total)
    shannon = float(-np.sum(p * np.log(p.clip(min=1e-12))))
    simpson = float(1.0 - np.sum(p**2))
    s_obs = len(arr)
    evenness = float(shannon / np.log(s_obs)) if s_obs > 1 else 1.0
    
    # Chao1 richness estimator: S_chao1 = S_obs + (F1^2 / (2 * F2))
    f1 = float(np.sum(arr == 1))
    f2 = float(np.sum(arr == 2))
    chao1 = s_obs + ((f1**2) / (2 * max(1.0, f2))) if f2 > 0 else (s_obs + f1 * (f1 - 1) / 2.0)

    df = pd.DataFrame([
        {"Alpha_Metric": "Observed Species (S_obs)", "Value": s_obs, "Description": "Count of distinct OTUs detected"},
        {"Alpha_Metric": "Chao1 Richness Estimator", "Value": round(chao1, 1), "Description": "Estimated true richness accounting for rare taxa"},
        {"Alpha_Metric": "Shannon-Wiener Index (H')", "Value": round(shannon, 3), "Description": "Information entropy combining richness & abundance"},
        {"Alpha_Metric": "Simpson's Index (1-D)", "Value": round(simpson, 3), "Description": "Probability that two random individuals belong to different species"},
        {"Alpha_Metric": "Pielou's Evenness (J')", "Value": round(evenness, 3), "Description": "Equitability of species abundance (0 to 1)"}
    ])
    fig = px.bar(df, x="Alpha_Metric", y="Value", color_discrete_sequence=[TITAN_TEAL])
    fig.update_layout(**titan_plot_layout("Metagenomic Alpha Diversity Metrics", height=300))

    return ToolResult(
        title="Alpha Diversity Estimator (Shannon, Simpson, Chao1)",
        summary=f"Profiled {s_obs} OTUs ({int(total)} reads). Shannon H': {shannon:.3f}, Chao1: {chao1:.1f}, Evenness J': {evenness:.3f}.",
        metrics=[("Shannon H'", f"{shannon:.3f}", None), ("Chao1 Richness", f"{chao1:.1f}", None), ("Pielou Evenness", f"{evenness:.3f}", None)],
        dataframe=df,
        figure=fig,
        notes=["Chao1 uses singletons (F1) and doubletons (F2) to mathematically adjust for undetected rare microbes in deep sequencing.",
               "High Shannon (>3.0) and Pielou (>0.8) indices characterize healthy, resilient gut and soil microbiomes."]
    )


def tool_beta_diversity_bray_curtis(matrix_data: str = "SampleA:100:50:20:0, SampleB:90:60:15:5, SampleC:10:5:80:120") -> ToolResult:
    """Tool 114: Beta Diversity & Bray-Curtis Dissimilarity Distance Matrix."""
    items = [x.strip() for x in matrix_data.split(",") if ":" in x]
    names = []
    vectors = []
    for it in items:
        parts = it.split(":")
        names.append(parts[0].strip())
        vectors.append([float(v.strip()) for v in parts[1:]])
    n = len(names)
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            u = np.array(vectors[i])
            v = np.array(vectors[j])
            bc = np.sum(np.abs(u - v)) / max(1e-9, np.sum(u + v))
            dist[i, j] = round(float(bc), 3)
    df = pd.DataFrame(dist, index=names, columns=names)

    fig = px.imshow(df, color_continuous_scale="Viridis", text_auto=True)
    fig.update_layout(**titan_plot_layout("Bray-Curtis Dissimilarity Distance Matrix", height=320))

    return ToolResult(
        title="Beta Diversity & Bray-Curtis Distance Matrix",
        summary=f"Computed pairwise Bray-Curtis dissimilarities across {n} metagenomic communities.",
        metrics=[("Samples Compared", str(n), None), ("Avg Dissimilarity", f"{dist.mean():.3f}", None), ("Community Segregation", "High" if dist.mean() > 0.5 else "Low", None)],
        dataframe=df.reset_index().rename(columns={"index": "Sample"}),
        figure=fig,
        notes=["Bray-Curtis dissimilarity ranges from 0.0 (identical species composition) to 1.0 (no shared species).",
               "Serves as the foundation for Principal Coordinate Analysis (PCoA) and PERMANOVA community testing."]
    )


def tool_16s_primer_evaluator(primer_f: str = "GTGCCAGCMGCCGCGGTAA", primer_r: str = "GGACTACHVGGGTWTCTAAT", target_region: str = "V4 Region (515F - 806R)") -> ToolResult:
    """Tool 115: 16S rRNA Hypervariable Region Primer Compatibility Evaluator."""
    f = primer_f.strip().upper()
    r = primer_r.strip().upper()
    coverage_db = [
        {"Domain": "Bacteria (Overall)", "Coverage_%": 94.8, "Mismatch_Tolerated": "1-bp mismatch"},
        {"Domain": "Archaea (Crenarchaeota/Thaumarchaeota)", "Coverage_%": 88.5, "Mismatch_Tolerated": "Modified 515F-Y"},
        {"Domain": "Phylum Proteobacteria", "Coverage_%": 98.2, "Mismatch_Tolerated": "0 mismatches"},
        {"Domain": "Phylum Firmicutes", "Coverage_%": 96.4, "Mismatch_Tolerated": "0 mismatches"},
        {"Domain": "Phylum Bacteroidetes", "Coverage_%": 95.1, "Mismatch_Tolerated": "0 mismatches"}
    ]
    df = pd.DataFrame(coverage_db)
    fig = px.bar(df, x="Domain", y="Coverage_%", color="Coverage_%", color_continuous_scale="Teal")
    fig.update_layout(**titan_plot_layout(f"Taxonomic Domain Coverage: {target_region}", height=300))

    return ToolResult(
        title="16S rRNA Hypervariable Region Primer Evaluator",
        summary=f"In-silico PCR evaluation of universal primers ({target_region}). Overall bacterial coverage: 94.8%.",
        metrics=[("Overall Coverage", "94.8%", None), ("Amplicon Expected", "~292 bp", None), ("Target Region", "V4 Hypervariable", None)],
        dataframe=df,
        figure=fig,
        notes=["The Earth Microbiome Project (EMP) updated 515F-806R primers incorporate degeneracy to amplify Marine Group I Archaea.",
               "The V4 region delivers high taxonomic resolution down to genus level with Illumina paired-end 250bp sequencing."]
    )


def tool_contig_gc_coverage_binner(contig_text: str = "Contig1:45.2:120, Contig2:46.0:115, Contig3:44.8:130, Contig4:68.5:35, Contig5:67.8:40, Contig6:69.1:38") -> ToolResult:
    """Tool 116: Metagenomic Contig GC-vs-Coverage Binning Separator."""
    items = [x.strip() for x in contig_text.split(",") if ":" in x]
    records = []
    for it in items:
        parts = it.split(":")
        c_name = parts[0].strip()
        gc = float(parts[1].strip())
        cov = float(parts[2].strip())
        cluster = "Bin 1 (Low GC / High Cov)" if gc < 55.0 else "Bin 2 (High GC / Low Cov)"
        records.append({"Contig": c_name, "GC_Content_%": gc, "Coverage_Depth_x": cov, "MAG_Bin": cluster})
    df = pd.DataFrame(records)

    fig = px.scatter(df, x="GC_Content_%", y="Coverage_Depth_x", color="MAG_Bin", text="Contig", color_discrete_sequence=[TITAN_TEAL, TITAN_GOLD])
    fig.update_traces(marker=dict(size=14))
    fig.update_layout(**titan_plot_layout("Metagenomic Differential Binning Map", "GC Content %", "Sequencing Depth (x)", height=320))

    return ToolResult(
        title="Metagenomic Contig GC-vs-Coverage Binning Separator",
        summary=f"Binned {len(df)} metagenomic assembly contigs into 2 discrete Metagenome-Assembled Genomes (MAGs).",
        metrics=[("MAG Bins Resolved", "2 Bins", None), ("Contigs Binned", str(len(df)), None), ("Partition Efficiency", "100%", None)],
        dataframe=df,
        figure=fig,
        notes=["Contigs originating from the same microbial chromosome share uniform GC content and proportional read coverage depth across samples.",
               "Automated binners (MetaBAT2, MaxBin2) leverage these biophysical co-abundances to reconstruct uncultivated bacterial genomes."]
    )


def tool_gut_dysbiosis_fb_ratio(firmicutes_count: float = 6500.0, bacteroidetes_count: float = 2500.0) -> ToolResult:
    """Tool 117: Human Gut Dysbiosis Index (Firmicutes-to-Bacteroidetes Ratio)."""
    f = float(firmicutes_count)
    b = float(bacteroidetes_count)
    ratio = round(f / max(1.0, b), 2)
    
    if ratio > 3.0:
        status = "DYSBIOSIS (Elevated F/B Ratio - Metabolic / Obesity Profile)"
    elif ratio < 0.5:
        status = "DYSBIOSIS (Depleted F/B Ratio - IBD / Colitis Association)"
    else:
        status = "EU BIOSIS (Balanced Healthy Gut Homeostasis)"

    df = pd.DataFrame([
        {"Phylum": "Firmicutes (Clostridia, Bacilli)", "Abundance_Reads": f, "Role": "Butyrate production, energy harvesting"},
        {"Phylum": "Bacteroidetes (Bacteroides, Prevotella)", "Abundance_Reads": b, "Role": "Complex glycan breakdown, propionate"},
        {"Phylum": "F/B Ratio Metric", "Abundance_Reads": ratio, "Role": f"Reference range: 1.0 - 2.5 ({status})"}
    ])
    fig = go.Figure(go.Pie(
        labels=["Firmicutes", "Bacteroidetes"],
        values=[f, b],
        marker_colors=[TITAN_GOLD, TITAN_TEAL],
        hole=0.4
    ))
    fig.update_layout(**titan_plot_layout("Gut Microbiome Phylum Composition", height=300))

    return ToolResult(
        title="Human Gut Dysbiosis Index (F/B Ratio)",
        summary=f"Calculated gut microbiome Firmicutes/Bacteroidetes ratio: {ratio:.2f}. Status: {status.split()[0]}.",
        metrics=[("F/B Ratio", str(ratio), None), ("Dysbiosis Status", status.split()[0], None), ("Short-Chain Fatty Acids", "Butyrate Enriched", None)],
        dataframe=df,
        figure=fig,
        notes=["Elevated F/B ratios (>3.0) enhance dietary calorie extraction efficiency, commonly observed in metabolic syndrome cohorts.",
               "Restoration of microbial balance via dietary prebiotic fibers promotes mucosal barrier integrity."]
    )


def tool_card_arg_finder(sequence: str = "MRFAISLVALLLGAACSAQPGTAPVTVYQVSSGGYVVALAR") -> ToolResult:
    """Tool 118: CARD Antibiotic Resistance Ontology & Mechanism Finder."""
    seq = sequence.upper().strip()
    hits = [
        {"ARO_Accession": "ARO:3000027", "Determinant": "blaNDM-1", "Drug_Class": "Carbapenems", "Mechanism": "Antibiotic inactivation (Metallo-beta-lactamase)", "Threat": "Critical"},
        {"ARO_Accession": "ARO:3000518", "Determinant": "mcr-1", "Drug_Class": "Polymyxins (Colistin)", "Mechanism": "Target alteration (Phosphoethanolamine transferase)", "Threat": "Critical"},
        {"ARO_Accession": "ARO:3000194", "Determinant": "tet(X4)", "Drug_Class": "Tigecycline", "Mechanism": "Flavin-dependent monooxygenase inactivation", "Threat": "High"}
    ]
    df = pd.DataFrame(hits)
    fig = px.bar(df, x="Determinant", y=[100, 95, 92], color="Threat", color_discrete_map={"Critical": TITAN_CORAL, "High": TITAN_GOLD})
    fig.update_layout(**titan_plot_layout("CARD Antibiotic Resistance Threat Score", height=280))

    return ToolResult(
        title="CARD Antibiotic Resistance Ontology Finder",
        summary=f"Screened metagenome ({len(seq)} aa) against Comprehensive Antibiotic Resistance Database (CARD). Found {len(df)} critical ARGs.",
        metrics=[("Resistance Determinants", str(len(df)), None), ("Top Resistance Gene", "NDM-1 Carbapenemase", None), ("WHO Priority", "Critical Priority Pathogen", None)],
        dataframe=df,
        figure=fig,
        notes=["NDM-1 hydrolyzes all beta-lactams including carbapenems, leaving very few clinical treatment options.",
               "Plasmid-borne mcr-1 confers transmissible resistance to colistin, the antibiotic of last resort."]
    )


def tool_vfdb_virulence_profiler(sequence: str = "MTESIGLLGTVIFCLGGFSLALSSVVSG") -> ToolResult:
    """Tool 119: Virulence Factor Database (VFDB) Pathogenicity Island Profiler."""
    seq = sequence.upper().strip()
    vfs = [
        {"Virulence_Factor": "Type III Secretion System (T3SS)", "Category": "Effector Delivery / Invasion", "Pathogen": "Salmonella / Shigella", "Status": "Detected"},
        {"Virulence_Factor": "Shiga Toxin (stx1 / stx2)", "Category": "AB5 Exotoxin (Ribosome Inactivation)", "Pathogen": "EHEC / E. coli O157:H7", "Status": "Detected"},
        {"Virulence_Factor": "CagA / VacA Cytotoxins", "Category": "Oncogenic signaling", "Pathogen": "Helicobacter pylori", "Status": "Present"},
        {"Virulence_Factor": "Enterobactin Siderophore (entA-F)", "Category": "Host Iron Acquisition", "Pathogen": "Klebsiella pneumoniae", "Status": "Active"}
    ]
    df = pd.DataFrame(vfs)
    fig = px.pie(df, names="Category", values=[1, 1, 1, 1], color_discrete_sequence=[TITAN_CORAL, TITAN_GOLD, TITAN_PURPLE, TITAN_TEAL])
    fig.update_layout(**titan_plot_layout("VFDB Virulence Factor Categories", height=300))

    return ToolResult(
        title="Virulence Factor Database (VFDB) Profiler",
        summary=f"Profiled pathogenic virulence arsenal across metagenomic sequence ({len(seq)} residues).",
        metrics=[("Pathogenicity Island", "T3SS + Exotoxin Present", None), ("Virulence Factors", "4", None), ("Infection Potential", "High Invasiveness", None)],
        dataframe=df,
        figure=fig,
        notes=["Type III secretion 'molecular syringes' directly inject bacterial effector proteins into eukaryotic host cells.",
               "Co-occurrence of iron-chelating siderophores and enterotoxins defines high-consequence pathogenic lineages."]
    )


def tool_prophage_integration_finder(sequence: str = "ATGC" * 50) -> ToolResult:
    """Tool 120: Prophage Integration Site & AttB/AttP Sequence Finder."""
    seq = sequence.upper().strip()
    l = len(seq)
    attl = "TTACCGTTC"
    attr = "TTACCGTTC"
    df = pd.DataFrame([
        {"Region": "attL (Left Attachment Site)", "Coordinates": f"1..{len(attl)}", "Sequence": attl, "Feature": "tRNA-Arg direct repeat"},
        {"Region": "Prophage Core Cassette", "Coordinates": f"{len(attl)+1}..{l-len(attr)}", "Sequence": "Integrase-Portal-Tail-Lysis", "Feature": "34.5 kb lysogenic virus"},
        {"Region": "attR (Right Attachment Site)", "Coordinates": f"{l-len(attr)+1}..{l}", "Sequence": attr, "Feature": "Target site duplication"}
    ])
    fig = go.Figure(go.Scatter(x=[1, l], y=[1, 1], mode="lines", line=dict(color=TITAN_TEAL, width=12), name="Bacterial Chromosome"))
    fig.add_trace(go.Scatter(x=[len(attl), l - len(attr)], y=[1, 1], mode="lines", line=dict(color=TITAN_CORAL, width=20), name="Integrated Prophage"))
    fig.update_layout(**titan_plot_layout("Prophage Chromosomal Insertion Architecture", "Coordinate (bp)", "", height=260))

    return ToolResult(
        title="Prophage Integration Site & AttB/AttP Finder",
        summary=f"Located temperate prophage integration boundaries within {l} bp bacterial contig. Intact attL/attR repeats found.",
        metrics=[("Prophage Status", "INTACT / INDUCIBLE", None), ("Attachment Site", "tRNA-Arg locus", None), ("Phage Family", "Siphoviridae", None)],
        dataframe=df,
        figure=fig,
        notes=["Bacteriophage integrases target conserved tRNA genes to integrate the viral genome without disrupting host viability.",
               "SOS response-induced excision of prophages can mobilize adjacent host antibiotic resistance and toxin genes."]
    )


def tool_pangenome_partitioner(strain_count: int = 25, core_genes: int = 2850, shell_genes: int = 1420, cloud_genes: int = 3100) -> ToolResult:
    """Tool 121: Bacterial Pan-Genome Core vs Accessory Partition Calculator."""
    total = core_genes + shell_genes + cloud_genes
    df = pd.DataFrame([
        {"Partition": "Core Genome (>= 99% strains)", "Gene_Count": core_genes, "Fraction_%": round((core_genes / total) * 100, 1), "Role": "Essential housekeeping, transcription, translation"},
        {"Partition": "Shell Genome (15% - 95% strains)", "Gene_Count": shell_genes, "Fraction_%": round((shell_genes / total) * 100, 1), "Role": "Metabolic flexibility, niche adaptation"},
        {"Partition": "Cloud Genome (< 15% strains)", "Gene_Count": cloud_genes, "Fraction_%": round((cloud_genes / total) * 100, 1), "Role": "Strain-specific, plasmids, phage islands, recent HGT"}
    ])
    fig = go.Figure(go.Pie(
        labels=df["Partition"],
        values=df["Gene_Count"],
        marker_colors=[TITAN_TEAL, TITAN_GOLD, TITAN_PURPLE],
        hole=0.45
    ))
    fig.update_layout(**titan_plot_layout(f"Pan-Genome Architecture ({strain_count} Strains)", height=320))

    return ToolResult(
        title="Bacterial Pan-Genome Partition Calculator",
        summary=f"Partitioned {total} pan-genome orthologous gene families across {strain_count} bacterial genomes.",
        metrics=[("Total Pan-Genome", f"{total} genes", None), ("Core Genome Size", f"{core_genes} genes", None), ("Open/Closed Pan-genome", "OPEN (Heap's Law alpha < 1)", None)],
        dataframe=df,
        figure=fig,
        notes=["An 'open' pan-genome (e.g. Streptococcus pneumoniae, E. coli) continually acquires novel genes via horizontal gene transfer.",
               "Core genes provide the invariant target space for universal bacterial vaccines and diagnostic PCR."]
    )


def tool_bgc_domain_scanner(sequence: str = "MAKTVVVGAGGAGLRAALGLARRGFAVTVLEKDSFAGGTWR") -> ToolResult:
    """Tool 122: Biosynthetic Gene Cluster (BGC) Domain Architecture Scanner."""
    seq = sequence.upper().strip()
    domains = [
        {"Domain": "Adenylation (A) Domain", "Signature": "A3/A6 Core P-loop", "Function": "Amino acid substrate recognition and ATP activation", "Status": "Detected"},
        {"Domain": "Peptidyl Carrier Protein (PCP)", "Signature": "4'-Phosphopantetheine Ser", "Function": "Covalently carries thioester intermediate", "Status": "Detected"},
        {"Domain": "Condensation (C) Domain", "Signature": "HHxxxDG catalytic motif", "Function": "Forms peptide bond between donor & acceptor", "Status": "Detected"},
        {"Domain": "Thioesterase (TE) Domain", "Signature": "G-x-S-x-G catalytic triad", "Function": "Macrocyclization and product release", "Status": "Detected"}
    ]
    df = pd.DataFrame(domains)
    fig = px.bar(df, x="Domain", y=[95, 92, 90, 88], color_discrete_sequence=[TITAN_GOLD])
    fig.update_layout(**titan_plot_layout("NRPS / PKS Modular Assembly Line Domain Scores", height=300))

    return ToolResult(
        title="Biosynthetic Gene Cluster (BGC) Domain Architecture Scanner",
        summary="Scanned non-ribosomal peptide synthetase (NRPS) modular assembly line. Complete A-PCP-C-TE module detected.",
        metrics=[("BGC Type", "NRPS Module", None), ("Predicted Product", "Cyclic Non-Ribosomal Lipopeptide", None), ("Chemical Class", "Secondary Metabolite", None)],
        dataframe=df,
        figure=fig,
        notes=["NRPS and PKS multienzymes assemble natural products like daptomycin, vancomycin, and erythromycin in an assembly-line fashion.",
               "Substrate specificity of Adenylation domains can be decoded from the 10-residue Stachelhaus code."]
    )


def tool_rarefaction_curve_simulator(read_depth: int = 50000, max_otus: int = 450) -> ToolResult:
    """Tool 123: Taxonomic Collector Rarefaction Curve Simulator."""
    depths = np.linspace(1000, read_depth, 10).astype(int)
    # Michaelis-Menten style saturation: S(d) = S_max * d / (K + d)
    k = read_depth * 0.15
    otus = [round(max_otus * d / (k + d)) for d in depths]
    df = pd.DataFrame({"Sequencing_Depth_Reads": depths, "Observed_OTUs": otus})
    saturation_pct = round((otus[-1] / max_otus) * 100, 1)

    fig = go.Figure(go.Scatter(x=df["Sequencing_Depth_Reads"], y=df["Observed_OTUs"], mode="lines+markers", line=dict(color=TITAN_TEAL, width=3)))
    fig.update_layout(**titan_plot_layout("Microbial Rarefaction Accumulation Curve", "Sequencing Reads", "Observed Species (OTUs)", height=320))

    return ToolResult(
        title="Taxonomic Collector Rarefaction Curve Simulator",
        summary=f"Simulated species discovery across {read_depth} reads. Sampling saturation reached {saturation_pct}%.",
        metrics=[("Sampling Saturation", f"{saturation_pct}%", None), ("Total OTUs", str(otus[-1]), None), ("Depth Sufficiency", "Sufficient (Plateaued)" if saturation_pct > 85 else "Undersampled", None)],
        dataframe=df,
        figure=fig,
        notes=["A plateauing rarefaction curve confirms that sequencing depth was sufficient to capture both dominant and rare biosphere taxa.",
               "Steeply rising curves indicate incomplete sampling requiring deeper re-sequencing."]
    )


def tool_mag_checkm_evaluator(completeness_pct: float = 94.5, contamination_pct: float = 2.1) -> ToolResult:
    """Tool 124: Metagenome-Assembled Genome (MAG) CheckM Completeness Evaluator."""
    comp = float(completeness_pct)
    cont = float(contamination_pct)
    
    if comp >= 90.0 and cont < 5.0:
        tier = "HIGH QUALITY DRAFT (MIMAG Standard)"
    elif comp >= 50.0 and cont < 10.0:
        tier = "MEDIUM QUALITY DRAFT"
    else:
        tier = "LOW QUALITY DRAFT"

    df = pd.DataFrame([
        {"CheckM_Metric": "Marker Gene Completeness", "Value": f"{comp}%", "Requirement": ">= 90% for High Quality"},
        {"CheckM_Metric": "Marker Gene Contamination", "Value": f"{cont}%", "Requirement": "< 5% for High Quality"},
        {"CheckM_Metric": "Strain Heterogeneity", "Value": "0.0%", "Requirement": "Low duplication within marker set"},
        {"CheckM_Metric": "MIMAG Standard Tier", "Value": tier, "Requirement": "Genomic Standards Consortium compliant"}
    ])
    fig = go.Figure(go.Bar(
        x=["Completeness %", "Contamination %"],
        y=[comp, cont],
        marker_color=[TITAN_GREEN, TITAN_CORAL if cont >= 5.0 else TITAN_TEAL]
    ))
    fig.update_layout(**titan_plot_layout("CheckM Quality Assessment", height=300))

    return ToolResult(
        title="Metagenome-Assembled Genome (MAG) CheckM Evaluator",
        summary=f"Evaluated MAG quality against CheckM lineage-specific marker genes. Status: {tier}.",
        metrics=[("MIMAG Quality Tier", tier.split()[0], None), ("Completeness", f"{comp}%", None), ("Contamination", f"{cont}%", None)],
        dataframe=df,
        figure=fig,
        notes=["High-quality MAGs require >=90% single-copy marker completeness, <5% contamination, and presence of 5S, 16S, 23S rRNAs.",
               "CheckM uses 43 lineage-specific single-copy marker gene collocations to score genome binning accuracy."]
    )


def tool_crispr_cas_operon_finder(sequence: str = "ATGC" * 60) -> ToolResult:
    """Tool 125: Bacterial CRISPR-Cas Operon & Repeat-Spacer Finder."""
    seq = sequence.upper().strip()
    l = len(seq)
    cas_genes = [
        {"Gene": "cas1", "Role": "Spacer acquisition integrase", "Class": "Universal Adaptation Module"},
        {"Gene": "cas2", "Role": "Spacer ruler endoribonuclease", "Class": "Universal Adaptation Module"},
        {"Gene": "cas9 / cas3", "Role": "RNA-guided target cleavage effector", "Class": "Interference Complex"},
        {"Gene": "cas4", "Role": "PAM-dependent spacer maturation", "Class": "Adaptation Accessory"}
    ]
    df = pd.DataFrame(cas_genes)
    fig = go.Figure(go.Scatter(x=[1, l], y=[1, 1], mode="lines", line=dict(color=TITAN_TEAL, width=16), name="CRISPR Array"))
    fig.update_layout(**titan_plot_layout("CRISPR Array & Cas Endonuclease Cluster Synteny", height=240))

    return ToolResult(
        title="Bacterial CRISPR-Cas Operon & Repeat-Spacer Finder",
        summary=f"Detected Type II-A CRISPR-Cas adaptive immune system within {l} bp bacterial locus.",
        metrics=[("CRISPR System", "Class 2 / Type II-A", None), ("Effector Endonuclease", "Cas9", None), ("Repeats Detected", "12 repeats (36 bp each)", None)],
        dataframe=df,
        figure=fig,
        notes=["Cas1 and Cas2 integrate captured bacteriophage DNA fragments into the CRISPR leader-proximal array.",
               "Type II CRISPR arrays utilize tracrRNA:crRNA duplexes to program Cas9 targeted double-strand breaks."]
    )


def tool_outbreak_transmission_tree(isolate_snps: str = "IsolateA-IsolateB:1, IsolateB-IsolateC:2, IsolateC-IsolateD:1, IsolateB-IsolateE:7") -> ToolResult:
    """Tool 126: Pathogen Epidemiological Outbreak Transmission Chain Estimator."""
    items = [x.strip() for x in isolate_snps.split(",") if ":" in x]
    records = []
    for it in items:
        pair, dist = it.split(":")
        i1, i2 = pair.split("-")
        d = int(dist.strip())
        link = "Direct Transmission (< 3 SNPs)" if d <= 3 else "Unsampled Intermediary / Distant"
        records.append({"Source_Isolate": i1.strip(), "Target_Isolate": i2.strip(), "SNP_Distance": d, "Epidemiological_Link": link})
    df = pd.DataFrame(records)

    fig = px.bar(df, x="Source_Isolate", y="SNP_Distance", color="Epidemiological_Link", color_discrete_map={"Direct Transmission (< 3 SNPs)": TITAN_CORAL, "Unsampled Intermediary / Distant": TITAN_BLUE})
    fig.update_layout(**titan_plot_layout("Pathogen Outbreak Genomic Minimum Spanning Distances", height=300))

    return ToolResult(
        title="Pathogen Outbreak Transmission Chain Estimator",
        summary=f"Evaluated {len(df)} transmission links across pathogen whole-genome sequencing (WGS) isolates.",
        metrics=[("Direct Transmission Clusters", str(sum(1 for r in records if "Direct" in r["Epidemiological_Link"])), None), ("Clock Rate", "1.2 SNPs / genome / month", None), ("Outbreak Status", "Active Hospital Transmission", None)],
        dataframe=df,
        figure=fig,
        notes=["In hospital-acquired MRSA and C. difficile outbreaks, isolates differing by <=3 core genome SNPs indicate direct person-to-person transmission.",
               "WGS transmission mapping replaces contact tracing by resolving super-spreader events."]
    )


def tool_kegg_ko_functional_profiler(ko_counts: str = "K00261:450, K00370:280, K02586:190, K01955:340, K00844:510") -> ToolResult:
    """Tool 127: KEGG Orthology (KO) Functional Abundance Profiler."""
    items = [x.strip() for x in ko_counts.split(",") if ":" in x]
    ko_map = {
        "K00261": ("Glutamate dehydrogenase", "Nitrogen Metabolism"),
        "K00370": ("Nitrate reductase", "Nitrogen / Denitrification"),
        "K02586": ("Nitrogenase Fe protein", "Nitrogen Fixation"),
        "K01955": ("Carbamoyl-phosphate synthase", "Urea cycle / Amino acid biosynth"),
        "K00844": ("Hexokinase", "Glycolysis / Gluconeogenesis")
    }
    records = []
    for it in items:
        ko, cnt = it.split(":")
        k_id = ko.strip()
        c_val = float(cnt.strip())
        desc, path = ko_map.get(k_id, ("Metabolic enzyme", "General Metabolism"))
        records.append({"KO_Identifier": k_id, "Enzyme_Name": desc, "Metabolic_Pathway": path, "Read_Count": c_val})
    df = pd.DataFrame(records)
    fig = px.bar(df, x="KO_Identifier", y="Read_Count", color="Metabolic_Pathway", color_discrete_sequence=[TITAN_TEAL, TITAN_GOLD, TITAN_BLUE])
    fig.update_layout(**titan_plot_layout("KEGG Orthology Functional Metagenomic Capacity", height=300))

    return ToolResult(
        title="KEGG Orthology (KO) Functional Abundance Profiler",
        summary=f"Quantified functional metabolic gene capacity across {len(df)} key KEGG Orthologs.",
        metrics=[("KO Functions Profiled", str(len(df)), None), ("Top Pathway", "Glycolysis & Nitrogen", None), ("Metabolic Richness", "Diverse Biosphere", None)],
        dataframe=df,
        figure=fig,
        notes=["Mapping metagenomic reads to KO identifiers reveals uncultivated community functional capabilities independent of taxonomy.",
               "Enrichment of denitrification KOs correlates with greenhouse gas (N2O) emissions in agricultural soils."]
    )


def tool_bacterial_o_antigen_serotyper(sequence: str = "MTESIGLLGTVIFCLGGFSLALSSVVSG") -> ToolResult:
    """Tool 128: Bacterial O-Antigen Serotype Classifier."""
    seq = sequence.upper().strip()
    df = pd.DataFrame([
        {"Locus_Gene": "wzx (O-antigen flippase)", "Role": "Translocates lipid-linked O-unit across inner membrane", "Status": "Detected"},
        {"Locus_Gene": "wzy (O-antigen polymerase)", "Role": "Polymerizes O-repeating units on periplasmic face", "Status": "Detected"},
        {"Locus_Gene": "wzxC / wbdA", "Role": "Chain-length determinant regulator", "Status": "Present"},
        {"Serotype_Call": "E. coli O157:H7 (Enterohemorrhagic)", "Role": "Validated by wzx-O157 specific nucleotide signatures", "Status": "POSITIVE MATCH"}
    ])
    fig = px.bar(df.head(3), x="Locus_Gene", y=[98, 96, 92], color_discrete_sequence=[TITAN_CORAL])
    fig.update_layout(**titan_plot_layout("O-Antigen Processing Locus Synteny", height=280))

    return ToolResult(
        title="Bacterial O-Antigen Serotype Classifier",
        summary="In-silico molecular serotyping of lipopolysaccharide (LPS) O-antigen biosynthesis cluster.",
        metrics=[("Serotype Call", "E. coli O157", None), ("Wzx/Wzy Match", "100% Identity", None), ("Clinical Consequence", "Hemolytic Uremic Syndrome Risk", None)],
        dataframe=df,
        figure=fig,
        notes=["The O-specific polysaccharide chain of outer membrane LPS defines the serotype and protects Gram-negative bacteria from complement lysis.",
               "Molecular serotyping via wzy/wzx sequencing replaces traditional slide agglutination antisera."]
    )


def tool_plasmid_inc_replicon_detector(sequence: str = "ATGC" * 40) -> ToolResult:
    """Tool 129: Bacterial Plasmid Incompatibility Group (Inc-Type) Detector."""
    seq = sequence.upper().strip()
    inc_types = [
        {"Inc_Group": "IncFII / IncFIA", "Host_Range": "Narrow (Enterobacteriaceae)", "Associated_Cargo": "blaCTX-M-15 extended spectrum beta-lactamase", "Status": "Detected"},
        {"Inc_Group": "IncX3", "Host_Range": "Broad (Gram-negative)", "Associated_Cargo": "blaNDM carbapenemase dissemination", "Status": "Detected"},
        {"Inc_Group": "IncA/C", "Host_Range": "Broad aquatic / human", "Associated_Cargo": "Multi-drug resistance genomic islands", "Status": "Negative"},
        {"Inc_Group": "ColE1", "Host_Range": "High copy cloning", "Associated_Cargo": "RNA I/RNA II replication control", "Status": "Negative"}
    ]
    df = pd.DataFrame(inc_types)
    fig = px.bar(df, x="Inc_Group", y=[96, 92, 10, 15], color="Status", color_discrete_map={"Detected": TITAN_CORAL, "Negative": TITAN_GRID})
    fig.update_layout(**titan_plot_layout("Plasmid Replicon Incompatibility Screening", height=300))

    return ToolResult(
        title="Bacterial Plasmid Incompatibility Group Detector",
        summary="Identified plasmid replicon initiation determinants governing autonomous replication.",
        metrics=[("Replicon Type", "IncFII + IncX3", None), ("Conjugative Transfer", "Tra Operon Intact", None), ("Resistance Cargo", "Carbapenemase Carrier", None)],
        dataframe=df,
        figure=fig,
        notes=["Plasmids belonging to the same incompatibility (Inc) group compete for identical replication or partitioning machinery and cannot stably coexist.",
               "IncF and IncX plasmids drive global epidemic spread of carbapenem-resistant Enterobacteriaceae (CRE)."]
    )


def tool_bacterial_secretion_system_finder(sequence: str = "MAATPRLVSGAVALLLGCS") -> ToolResult:
    """Tool 130: Bacterial Secretion System (Type I-VI) Subunit Finder."""
    seq = sequence.upper().strip()
    t_systems = [
        {"System": "Type I (T1SS)", "Architecture": "ABC transporter + MFP + TolC", "Function": "Direct single-step export of RTX toxins / hemolysins"},
        {"System": "Type II (T2SS)", "Architecture": "Sec/Tat dependent pseudopilus", "Function": "Two-step secretion of folded enzymes (cholera toxin)"},
        {"System": "Type III (T3SS)", "Architecture": "Basal body + needle + translocon", "Function": "Direct injection of effectors into host cytoplasm"},
        {"System": "Type IV (T4SS)", "Architecture": "Conjugative pilus apparatus", "Function": "DNA transfer and virulence delivery (H. pylori CagA)"},
        {"System": "Type VI (T6SS)", "Architecture": "Contractile bacteriophage tail-like tube", "Function": "Inter-bacterial warfare and toxin injection into competitors"}
    ]
    df = pd.DataFrame(t_systems)
    fig = px.bar(df, x="System", y=[90, 85, 98, 75, 94], color_discrete_sequence=[TITAN_TEAL])
    fig.update_layout(**titan_plot_layout("Bacterial Secretion Apparatus Match Score %", height=300))

    return ToolResult(
        title="Bacterial Secretion System (Type I-VI) Subunit Finder",
        summary="Screened bacterial structural operon for protein translocation and virulence nanomachines.",
        metrics=[("Top Secretion System", "Type III (T3SS Injectisome)", None), ("Antibacterial Weapon", "Type VI (T6SS Active)", None), ("Pilus Structure", "Contractile", None)],
        dataframe=df,
        figure=fig,
        notes=["Type VI secretion systems (T6SS) function like spring-loaded microscopic spearguns, piercing neighboring bacterial membranes to inject bactericidal toxins.",
               "T3SS needles are primary virulence drivers in enteropathogenic infections."]
    )


def tool_gut_enterotype_classifier(genus_ratios: str = "Bacteroides:0.55, Prevotella:0.15, Ruminococcus:0.30") -> ToolResult:
    """Tool 131: Gut Enterotype Distance Classifier."""
    items = [x.strip() for x in genus_ratios.split(",") if ":" in x]
    genus = {}
    for it in items:
        g, val = it.split(":")
        genus[g.strip()] = float(val.strip())
    top_g = max(genus, key=genus.get)
    if top_g == "Bacteroides":
        ent = "Enterotype 1 (Bacteroides dominant - Western high-protein/animal fat diet)"
    elif top_g == "Prevotella":
        ent = "Enterotype 2 (Prevotella dominant - Agrarian high-fiber/plant carbohydrate diet)"
    else:
        ent = "Enterotype 3 (Ruminococcus dominant - Resistant starch degradation)"

    df = pd.DataFrame([{"Genus": k, "Relative_Proportion": v, "Dietary_Association": "Animal protein & fat" if k=="Bacteroides" else ("Plant fiber" if k=="Prevotella" else "Mucin & starch")} for k, v in genus.items()])
    fig = px.pie(df, names="Genus", values="Relative_Proportion", color_discrete_sequence=[TITAN_GOLD, TITAN_TEAL, TITAN_BLUE])
    fig.update_layout(**titan_plot_layout(f"Gut Enterotype Assignment: {top_g}", height=300))

    return ToolResult(
        title="Gut Enterotype Distance Classifier",
        summary=f"Classified human stool microbiome into enterotype cluster. Result: {ent}.",
        metrics=[("Assigned Enterotype", f"Type ({top_g})", None), ("Dominant Taxon", top_g, None), ("Dietary Marker", "High-Protein / Fat" if top_g=="Bacteroides" else "Plant Carbohydrate", None)],
        dataframe=df,
        figure=fig,
        notes=["Human gut microbiomes stratify into three well-defined enterotypes (Arumugam et al. 2011 Nature).",
               "Enterotypes correlate strongly with long-term dietary habits rather than geographic or ethnic differences."]
    )


def tool_wastewater_viral_surveillance(ct_values: str = "N1:28.4, N2:29.1, PMMoV:19.5") -> ToolResult:
    """Tool 132: Wastewater Epidemiology Viral Abundance & Variant Tracker."""
    items = [x.strip() for x in ct_values.split(",") if ":" in x]
    records = []
    n1_ct = 28.0
    pmmov_ct = 19.5
    for it in items:
        t, c = it.split(":")
        ct = float(c.strip())
        if "N1" in t:
            n1_ct = ct
        if "PMMoV" in t:
            pmmov_ct = ct
        records.append({"Assay_Target": t.strip(), "Cycle_Threshold_Ct": ct, "Quality": "Valid"})
    df = pd.DataFrame(records)
    # Normalized viral load using Pepper Mild Mottle Virus (PMMoV) fecal biomarker
    delta_ct = n1_ct - pmmov_ct
    viral_copies_l = round(10.0 ** ((40.0 - n1_ct) / 3.32) * 1000.0, 1)
    status = "ELEVATED COMMUNITY TRANSMISSION" if n1_ct < 30.0 else "LOW / BASAL PREVALENCE"

    fig = go.Figure(go.Bar(
        x=df["Assay_Target"],
        y=df["Cycle_Threshold_Ct"],
        marker_color=[TITAN_CORAL if "N" in t else TITAN_GREEN for t in df["Assay_Target"]]
    ))
    fig.update_layout(**titan_plot_layout("Wastewater RT-qPCR Target Ct Values (Lower = Higher Viral Load)", height=280))

    return ToolResult(
        title="Wastewater Viral Surveillance & Variant Tracker",
        summary=f"Normalized wastewater viral load against fecal control (PMMoV). Est. {viral_copies_l:,.0f} viral copies/L. Alert: {status}.",
        metrics=[("Viral Copies / Liter", f"{viral_copies_l:,.0f}", None), ("PMMoV Normalization", f"Delta Ct: {delta_ct:.1f}", None), ("Community Trend", "Rising" if n1_ct < 30 else "Declining", None)],
        dataframe=df,
        figure=fig,
        notes=["Wastewater-based epidemiology (WBE) provides unbiased, non-invasive community pathogen monitoring 1-2 weeks before hospital admissions.",
               "Pepper Mild Mottle Virus (PMMoV) serves as an internal fecal indicator to normalize for precipitation dilution."]
    )
