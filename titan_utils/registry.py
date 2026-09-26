"""Master Registry for the 260 tools in the Titan Bioinformatics Suite.

Provides structured metadata, category mappings, input specifications,
and handler dispatch for both legacy tools (1-52) and advanced tools (53-260).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
import titan_tools


@dataclass
class ToolInputSpec:
    id: str
    label: str
    type: str  # "text", "textarea", "number", "select"
    default: Any
    options: List[str] = field(default_factory=list)
    help: str = ""


@dataclass
class ToolSpec:
    id: int
    name: str
    domain: str
    category_id: str
    category_name: str
    description: str
    console_page: str
    inputs: List[ToolInputSpec]
    handler_name: str
    student_tip: str = ""

    def get_handler(self) -> Optional[Callable[..., Any]]:
        return getattr(titan_tools, self.handler_name, None)


CATEGORIES = [
    ("cat1_dna", "🧬 1 · DNA / RNA Basics", "01_DNA_RNA_Conversion.py"),
    ("cat2_prot", "🥩 2 · Protein Analysis", "12_DNA_to_Protein_Translator.py"),
    ("cat3_genome", "🧪 3 · Genomics & QC", "20_FASTA_FASTQ_Parser_QC.py"),
    ("cat4_align", "🔄 4 · Alignment & Phylogeny", "40_Pairwise_Alignment.py"),
    ("cat5_lab", "🧫 5 · Lab & Pipeline", "55_CRISPR_Cas9_gRNA_Designer.py"),
    ("agri", "🌾 6 · Agriculture & Plant Genomics", "65_Agriculture_and_Plant_Genomics.py"),
    ("marine", "🌊 7 · Marine & Extremophile Genomics", "66_Marine_and_Extremophile_Genomics.py"),
    ("clinical", "🩺 8 · Clinical Genomics & Precision Med", "67_Clinical_Genomics_Precision_Medicine.py"),
    ("metagenomics", "🦠 9 · Metagenomics & Microbiome", "68_Metagenomics_and_Microbiome.py"),
    ("structural", "📐 10 · Structural Biology & Biophysics", "69_Structural_Biology_and_Biophysics.py"),
    ("epigenetics", "🧬 11 · Epigenetics & Epitranscriptomics", "70_Epigenetics_and_Epitranscriptomics.py"),
    ("synthetic", "⚙️ 12 · Synthetic Biology & Metabolic Eng", "71_Synthetic_Biology_Metabolic_Eng.py"),
    ("population", "👥 13 · Population Genetics & Evolution", "72_Population_Genetics_Evolution.py"),
    ("ncbi", "🌐 14 · NCBI & Global Bioinformatics APIs", "73_NCBI_and_Global_Bioinformatics_APIs.py"),
    ("dr_titan", "🤖 15 · Dr. Titan AI & Bio-Copilot", "74_Dr_Titan_AI_Bio_Copilot.py"),
]

MASTER_REGISTRY: List[ToolSpec] = [
    ToolSpec(
        id=1,
        name='DNA RNA Conversion',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='01_DNA_RNA_Conversion.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_dna_rna_convert',
        student_tip='DNA RNA Conversion teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=2,
        name='Reverse Complement Stats',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='02_Reverse_Complement_Stats.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_revcomp',
        student_tip='Reverse Complement Stats teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=3,
        name='GC Content Melting Temp',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='03_GC_Content_Melting_Temp.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='GC Content Melting Temp teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=4,
        name='Mutation SNP Detection',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='04_Mutation_SNP_Detection.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Mutation SNP Detection teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=5,
        name='ORF Finder',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='05_ORF_Finder.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='ORF Finder teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=6,
        name='Motif Pattern Finder',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='06_Motif_Pattern_Finder.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Motif Pattern Finder teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=7,
        name='Restriction Enzyme Cutter',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='07_Restriction_Enzyme_Cutter.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Restriction Enzyme Cutter teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=8,
        name='Codon Usage Frequency',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='08_Codon_Usage_Frequency.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Codon Usage Frequency teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=9,
        name='Hamming Edit Distance',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='09_Hamming_Edit_Distance.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Hamming Edit Distance teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=10,
        name='Nucleotide Frequency Entropy',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='10_Nucleotide_Frequency_Entropy.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Nucleotide Frequency Entropy teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=11,
        name='Central Dogma Visualizer',
        domain='Basic DNA/RNA',
        category_id='cat1_dna',
        category_name='DNA / RNA Basics',
        description='Foundational Basic DNA/RNA analysis module with validated Biopython algorithms.',
        console_page='11_Central_Dogma_Visualizer.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Central Dogma Visualizer teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=12,
        name='DNA To Protein Translator',
        domain='Protein Analysis',
        category_id='cat2_prot',
        category_name='Protein Analysis',
        description='Foundational Protein Analysis analysis module with validated Biopython algorithms.',
        console_page='12_DNA_to_Protein_Translator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='DNA To Protein Translator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=13,
        name='Molecular Weight Calculator',
        domain='Protein Analysis',
        category_id='cat2_prot',
        category_name='Protein Analysis',
        description='Foundational Protein Analysis analysis module with validated Biopython algorithms.',
        console_page='13_Molecular_Weight_Calculator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Molecular Weight Calculator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=14,
        name='Protein To DNA Backtranslator',
        domain='Protein Analysis',
        category_id='cat2_prot',
        category_name='Protein Analysis',
        description='Foundational Protein Analysis analysis module with validated Biopython algorithms.',
        console_page='14_Protein_to_DNA_BackTranslator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Protein To DNA Backtranslator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=15,
        name='In Silico Mutagenesis',
        domain='Protein Analysis',
        category_id='cat2_prot',
        category_name='Protein Analysis',
        description='Foundational Protein Analysis analysis module with validated Biopython algorithms.',
        console_page='15_In_Silico_Mutagenesis.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='In Silico Mutagenesis teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=16,
        name='Protein pI Estimator',
        domain='Protein Analysis',
        category_id='cat2_prot',
        category_name='Protein Analysis',
        description='Foundational Protein Analysis analysis module with validated Biopython algorithms.',
        console_page='16_Protein_pI_Estimator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Protein pI Estimator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=17,
        name='Hydropathy Plot',
        domain='Protein Analysis',
        category_id='cat2_prot',
        category_name='Protein Analysis',
        description='Foundational Protein Analysis analysis module with validated Biopython algorithms.',
        console_page='17_Hydropathy_Plot.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Hydropathy Plot teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=18,
        name='FASTA FASTQ Parser QC',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='20_FASTA_FASTQ_Parser_QC.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='FASTA FASTQ Parser QC teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=19,
        name='Kmer Frequency',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='21_Kmer_Frequency.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Kmer Frequency teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=20,
        name='Ngrams Analysis',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='22_Ngrams_Analysis.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Ngrams Analysis teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=21,
        name='Primer Design Advanced',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='23_Primer_Design_Advanced.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Primer Design Advanced teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=22,
        name='Cpg Isl& Detector',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='24_CpG_Island_Detector.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Cpg Isl& Detector teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=23,
        name='Chaos Game Representation',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='25_Chaos_Game_Representation.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Chaos Game Representation teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=24,
        name='DNA Shape Analysis',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='26_DNA_Shape_Analysis.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='DNA Shape Analysis teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=25,
        name='VCF Variant Viewer',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='27_VCF_Variant_Viewer.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='VCF Variant Viewer teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=26,
        name='Read Quality Control',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='28_Read_Quality_Control.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Read Quality Control teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=27,
        name='Gene Ontology GO Enrichment',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='29_Gene_Ontology_GO_Enrichment.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Gene Ontology GO Enrichment teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=28,
        name='T&Em Repeat Finder',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='30_Tandem_Repeat_Finder.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='T&Em Repeat Finder teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=29,
        name='GC Skew Plotter',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='31_GC_Skew_Plotter.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='GC Skew Plotter teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=30,
        name='KEGG Pathway Mapper',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='32_KEGG_Pathway_Mapper.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='KEGG Pathway Mapper teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=31,
        name='Advanced Tm Calculator',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='33_Advanced_Tm_Calculator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Advanced Tm Calculator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=32,
        name='Bulk Reverse Complement',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='34_Bulk_Reverse_Complement.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Bulk Reverse Complement teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=33,
        name='R&Om DNA Generator',
        domain='Genomics & QC',
        category_id='cat3_genome',
        category_name='Genomics & QC',
        description='Foundational Genomics & QC analysis module with validated Biopython algorithms.',
        console_page='35_Random_DNA_Generator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='R&Om DNA Generator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=34,
        name='Pairwise Alignment',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='40_Pairwise_Alignment.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Pairwise Alignment teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=35,
        name='Local Alignment Smithwaterman',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='41_Local_Alignment_SmithWaterman.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Local Alignment Smithwaterman teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=36,
        name='Global Alignment Needlemanwunsch',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='42_Global_Alignment_NeedlemanWunsch.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Global Alignment Needlemanwunsch teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=37,
        name='Overlap Alignment',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='43_Overlap_Alignment.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Overlap Alignment teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=38,
        name='Multiple Sequence Alignment',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='44_Multiple_Sequence_Alignment.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Multiple Sequence Alignment teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=39,
        name='Msa Clustalw Format',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='45_MSA_ClustalW_Format.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Msa Clustalw Format teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=40,
        name='Phylogenetic Tree Builder',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='46_Phylogenetic_Tree_Builder.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Phylogenetic Tree Builder teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=41,
        name='Distance Matrix Calculator',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='47_Distance_Matrix_Calculator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Distance Matrix Calculator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=42,
        name='Sequence Logo Generator',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='48_Sequence_Logo_Generator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Sequence Logo Generator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=43,
        name='Dot Plot Similarity',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='49_Dot_Plot_Similarity.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Dot Plot Similarity teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=44,
        name='Consensus Sequence Generator',
        domain='Alignment & Phylogeny',
        category_id='cat4_align',
        category_name='Alignment & Phylogeny',
        description='Foundational Alignment & Phylogeny analysis module with validated Biopython algorithms.',
        console_page='50_Consensus_Sequence_Generator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Consensus Sequence Generator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=45,
        name='CRISPR Cas9 gRNA Designer',
        domain='Lab & Molecular Biology',
        category_id='cat5_lab',
        category_name='Lab & Molecular Biology',
        description='Foundational Lab & Molecular Biology analysis module with validated Biopython algorithms.',
        console_page='55_CRISPR_Cas9_gRNA_Designer.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='CRISPR Cas9 gRNA Designer teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=46,
        name='PCR Product Length Calculator',
        domain='Lab & Molecular Biology',
        category_id='cat5_lab',
        category_name='Lab & Molecular Biology',
        description='Foundational Lab & Molecular Biology analysis module with validated Biopython algorithms.',
        console_page='56_PCR_Product_Length_Calculator.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='PCR Product Length Calculator teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=47,
        name='Oligo Tm Annealing Temp',
        domain='Lab & Molecular Biology',
        category_id='cat5_lab',
        category_name='Lab & Molecular Biology',
        description='Foundational Lab & Molecular Biology analysis module with validated Biopython algorithms.',
        console_page='57_Oligo_Tm_Annealing_Temp.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Oligo Tm Annealing Temp teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=48,
        name='DNA Melting Curve Simulation',
        domain='Lab & Molecular Biology',
        category_id='cat5_lab',
        category_name='Lab & Molecular Biology',
        description='Foundational Lab & Molecular Biology analysis module with validated Biopython algorithms.',
        console_page='58_DNA_Melting_Curve_Simulation.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='DNA Melting Curve Simulation teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=49,
        name='InDel Detection',
        domain='Lab & Molecular Biology',
        category_id='cat5_lab',
        category_name='Lab & Molecular Biology',
        description='Foundational Lab & Molecular Biology analysis module with validated Biopython algorithms.',
        console_page='59_InDel_Detection.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='InDel Detection teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=50,
        name='BLAST Local Search',
        domain='Lab & Molecular Biology',
        category_id='cat5_lab',
        category_name='Lab & Molecular Biology',
        description='Foundational Lab & Molecular Biology analysis module with validated Biopython algorithms.',
        console_page='60_BLAST_Local_Search.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='BLAST Local Search teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=51,
        name='Full pIpeline Dashboard',
        domain='Lab & Molecular Biology',
        category_id='cat5_lab',
        category_name='Lab & Molecular Biology',
        description='Foundational Lab & Molecular Biology analysis module with validated Biopython algorithms.',
        console_page='61_Full_Pipeline_Dashboard.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Full pIpeline Dashboard teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=52,
        name='Codon Optimizer',
        domain='Lab & Molecular Biology',
        category_id='cat5_lab',
        category_name='Lab & Molecular Biology',
        description='Foundational Lab & Molecular Biology analysis module with validated Biopython algorithms.',
        console_page='62_Codon_Optimizer.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Input Sequence / Data', type='textarea', default='ATGCGATCGATCGATCGATCGATC', help='Enter biological sequence or data')
    ],
        handler_name='tool_legacy_generic',
        student_tip='Codon Optimizer teaches core principles of molecular biology, sequence structure, and computational algorithms.',
    ),
    ToolSpec(
        id=53,
        name='Crop Disease Resistance (R-Gene NBS-LRR) Scanner',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 53: Crop Disease Resistance (R-Gene NBS-LRR) Scanner.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MEGIGGKGSTVLLVLDDVWEKLRALGLPLALTVLKLLKLLK', help='Input for sequence')
    ],
        handler_name='tool_r_gene_finder',
        student_tip='Tool #53 (Crop Disease Resistance (R-Gene NBS-LRR) Scanner) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=54,
        name='Drought Tolerance Marker (SSR/Microsatellite) Analyzer',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 54: Drought Tolerance Marker (SSR/Microsatellite) Analyzer.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='ATATATATATATGCGCGCGCAAGAAGAAGAAGCTTCTTCTT', help='Input for sequence')
    ],
        handler_name='tool_drought_tolerance_ssr',
        student_tip='Tool #54 (Drought Tolerance Marker (SSR/Microsatellite) Analyzer) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=55,
        name='Soil Microbiome 16S Diversity Estimator',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 55: Soil Microbiome 16S Diversity Estimator.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='otu_text', label='Otu Text', type='textarea', default='Bacillus:450, Pseudomonas:320, Rhizobium:280, Streptomyces:190, Bradyrhizobium:150, Nitrosomonas:90, Acidobacteria:60', help='Input for otu text')
    ],
        handler_name='tool_soil_microbiome_diversity',
        student_tip='Tool #55 (Soil Microbiome 16S Diversity Estimator) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=56,
        name='Nitrogen Fixation Gene (nifH / nod) Identifier',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 56: Nitrogen Fixation Gene (nifH / nod) Identifier.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MARTLMAYAAGIKGAGGKSTTCSGSCVRILADAGYREVIVED', help='Input for sequence')
    ],
        handler_name='tool_nitrogen_fixation_nifh',
        student_tip='Tool #56 (Nitrogen Fixation Gene (nifH / nod) Identifier) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=57,
        name='Herbicide Target Mutation Detector (EPSPS / ALS / ACCase)',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 57: Herbicide Target Mutation Detector (EPSPS / ALS / ACCase).',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MSSSLATKAATAPSIAFAGAKPLVTAPRRVASSSLPKAVKPSSS', help='Input for sequence')
    ],
        handler_name='tool_herbicide_resistance',
        student_tip='Tool #57 (Herbicide Target Mutation Detector (EPSPS / ALS / ACCase)) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=58,
        name='Photosynthesis RuBisCO (rbcL) Catalytic Efficiency Analyzer',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 58: Photosynthesis RuBisCO (rbcL) Catalytic Efficiency Analyzer.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MVPQTETKASVGFKAGVKEYKLTYYTPEYETKDTDILAAFRVTPQPGVPPEEAGAAVAAESSTGTWTTVWTDGLTSLDRYKGRCYHIEPVAGEENQYICYVAYPLDLFEEGSVTNMFTSI', help='Input for sequence')
    ],
        handler_name='tool_rubisco_efficiency',
        student_tip='Tool #58 (Photosynthesis RuBisCO (rbcL) Catalytic Efficiency Analyzer) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=59,
        name='Seed Storage Protein (Prolamin / Globulin) Profiler',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 59: Seed Storage Protein (Prolamin / Globulin) Profiler.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MAQIPQQPFPPQQPYPQQPYPQQPFPPQQPFPQQPYPQQPFPQPQQPFRQQPYPQQPF', help='Input for sequence')
    ],
        handler_name='tool_seed_storage_protein',
        student_tip='Tool #59 (Seed Storage Protein (Prolamin / Globulin) Profiler) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=60,
        name='Plant Transcription Factor Family Classifier',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 60: Plant Transcription Factor Family Classifier.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MDDWRKYGQKVIKGSPYPRGYYKCSSVRGCPARKHVERCRDDPSS', help='Input for sequence')
    ],
        handler_name='tool_plant_tf_classifier',
        student_tip='Tool #60 (Plant Transcription Factor Family Classifier) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=61,
        name='Transgenic GMO Marker & Vector Feature Screener',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 61: Transgenic GMO Marker & Vector Feature Screener.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='AGCTCAGCTACATACATGGAGTCAAAGATTCAAATAGAGGACCTAACAGAACTCGCCGTAAAGACTGGCGAACAGTTCATACAGAGTCTCTTACGAC', help='Input for sequence')
    ],
        handler_name='tool_gmo_transgene_detector',
        student_tip='Tool #61 (Transgenic GMO Marker & Vector Feature Screener) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=62,
        name='Pollen Allergen Epitope & Cross-Reactivity Predictor',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 62: Pollen Allergen Epitope & Cross-Reactivity Predictor.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MGVFNYETETTSVIPAARLFKAFILDGDNLFPKVAPQAISSVENIEGNGGPGTIKKISFPEGFPFKYVKDRVDEVDHTNFKYNYSVIEGGPIGDTLEKISNEIKIVATPDGGSILKISNKYHTKGDHEVKAEQVKASKEMGETLLRAVESYLLAHSDAYN', help='Input for sequence')
    ],
        handler_name='tool_pollen_allergen_predictor',
        student_tip='Tool #62 (Pollen Allergen Epitope & Cross-Reactivity Predictor) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=63,
        name='Post-Harvest Fruit Ripening Ethylene Pathway Tracker',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 63: Post-Harvest Fruit Ripening Ethylene Pathway Tracker.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MKLSNLRLVDGWRAETDPYNLKRFKDRVLELIGEYKPDLILVDVGAG', help='Input for sequence')
    ],
        handler_name='tool_ethylene_ripening_tracker',
        student_tip='Tool #63 (Post-Harvest Fruit Ripening Ethylene Pathway Tracker) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=64,
        name='Oomycete Pathogen (Phytophthora) RXLR Effector Detector',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 64: Oomycete Pathogen (Phytophthora) RXLR Effector Detector.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MKLLFTLALALAVCGAASARXLRDEERFLSVKDALEKWKNDL', help='Input for sequence')
    ],
        handler_name='tool_phytophthora_rxlr_effector',
        student_tip='Tool #64 (Oomycete Pathogen (Phytophthora) RXLR Effector Detector) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=65,
        name='Crop Cultivar Identity & Variety Fingerprinting',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 65: Crop Cultivar Identity & Variety Fingerprinting.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='markers_csv', label='Markers Csv', type='textarea', default='Cultivar,SSR1,SSR2,SSR3,SNP1,SNP2\nIR64,12,24,18,A,C\nBasmati,16,28,18,G,T\nSwarna,12,24,20,A,C\nSamba,14,24,18,A,T', help='Input for markers csv')
    ],
        handler_name='tool_crop_cultivar_fingerprint',
        student_tip='Tool #65 (Crop Cultivar Identity & Variety Fingerprinting) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=66,
        name='Plant Cis-Regulatory Element (CARE) Promoter Motif Scanner',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 66: Plant Cis-Regulatory Element (CARE) Promoter Motif Scanner.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='TATAAAACGTGACCGTCAGCCGACATTTGACCTATAAAGGATCGTG', help='Input for sequence')
    ],
        handler_name='tool_plant_promoter_care_scanner',
        student_tip='Tool #66 (Plant Cis-Regulatory Element (CARE) Promoter Motif Scanner) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=67,
        name='Plant Yield Trait QTL / GWAS Marker Visualizer',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 67: Plant Yield Trait QTL / GWAS Marker Visualizer.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='gwas_input', label='Gwas Input', type='textarea', default='Chr1:1.2e-6, Chr1:4.5e-4, Chr2:8.1e-9, Chr2:2.3e-3, Chr3:5.6e-8, Chr4:1.1e-2, Chr5:3.4e-10', help='Input for gwas input')
    ],
        handler_name='tool_plant_yield_gwas_visualizer',
        student_tip='Tool #67 (Plant Yield Trait QTL / GWAS Marker Visualizer) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=68,
        name='Chloroplast Inverted Repeat (IR) Junction Boundary Mapper',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 68: Chloroplast Inverted Repeat (IR) Junction Boundary Mapper.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC', help='Input for sequence')
    ],
        handler_name='tool_chloroplast_ir_junction_mapper',
        student_tip='Tool #68 (Chloroplast Inverted Repeat (IR) Junction Boundary Mapper) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=69,
        name='Plant Secondary Metabolite Terpenoid / Flavonoid Cluster Finder',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 69: Plant Secondary Metabolite Terpenoid / Flavonoid Cluster Finder.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MDDFFDDXXDMKLSNFLLGXXXCXGATCTCGATC', help='Input for sequence')
    ],
        handler_name='tool_plant_secondary_metabolite_cluster',
        student_tip='Tool #69 (Plant Secondary Metabolite Terpenoid / Flavonoid Cluster Finder) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=70,
        name='Chilling & Cold-Shock Response Element (CBF/DREB) Profiler',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 70: Chilling & Cold-Shock Response Element (CBF/DREB) Profiler.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MGEVRGPRRGYRGVRQRPWGKWAAEIRDPRKGVTWLGTFETAEEAA', help='Input for sequence')
    ],
        handler_name='tool_cold_shock_cbf_dreb',
        student_tip='Tool #70 (Chilling & Cold-Shock Response Element (CBF/DREB) Profiler) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=71,
        name='Salinity Tolerance Ion Transporter (HKT / NHX) Classifier',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 71: Salinity Tolerance Ion Transporter (HKT / NHX) Classifier.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MTESIGLLGTVIFCLGGFSLALSSVVSG', help='Input for sequence')
    ],
        handler_name='tool_salinity_tolerance_transporter',
        student_tip='Tool #71 (Salinity Tolerance Ion Transporter (HKT / NHX) Classifier) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=72,
        name='Plant miRNA Target Site Complementarity Evaluator',
        domain='Agriculture & Plant Genomics',
        category_id='agri',
        category_name='Agriculture & Plant Genomics',
        description='Tool 72: Plant miRNA Target Site Complementarity Evaluator.',
        console_page='65_Agriculture_and_Plant_Genomics.py',
        inputs=[
        ToolInputSpec(id='mirna_seq', label='Mirna Seq', type='text', default='UGGAGAAGCAGGGCACGUGCA', help='Input for mirna seq'),
        ToolInputSpec(id='target_seq', label='Target Seq', type='text', default='TGCACGTGCCCTGCTTCTCCA', help='Input for target seq')
    ],
        handler_name='tool_plant_mirna_target_finder',
        student_tip='Tool #72 (Plant miRNA Target Site Complementarity Evaluator) demonstrates critical applied computational techniques in Agriculture & Plant Genomics.',
    ),
    ToolSpec(
        id=73,
        name='Coral Bleaching Heat-Stress Gene Analyzer',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 73: Coral Bleaching Heat-Stress Gene Analyzer.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MAKAAAIGIDLGTTYSCVGVFQHGKVEIIANDQGNRTTPSYVAFTDTERLIGDAAKNQVAMNPTNTVFDAKRLIGRRFDDAVVQSDMKHWPFMVVNDAGRPKVQVEYKGETKSFYPEEISS', help='Input for sequence')
    ],
        handler_name='tool_coral_bleaching_stress',
        student_tip='Tool #73 (Coral Bleaching Heat-Stress Gene Analyzer) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=74,
        name='Deep-Sea Thermophile & Piezophile Adaptation Index',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 74: Deep-Sea Thermophile & Piezophile Adaptation Index.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MRKVRVRKEEKEERKKVLIILLVVILLVVLRKRKEEKK', help='Input for sequence')
    ],
        handler_name='tool_deep_sea_adaptation',
        student_tip='Tool #74 (Deep-Sea Thermophile & Piezophile Adaptation Index) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=75,
        name='Marine Bioluminescence Luciferase (lux / luc) Operon Detector',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 75: Marine Bioluminescence Luciferase (lux / luc) Operon Detector.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MKFGNFLLTYQPPELSQTEVMKRLVNLGKASEGCGFDTVWLLEHHFTEFGLLGNPYVAA', help='Input for sequence')
    ],
        handler_name='tool_marine_bioluminescence_lux',
        student_tip='Tool #75 (Marine Bioluminescence Luciferase (lux / luc) Operon Detector) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=76,
        name='Fish Stock Population Structure & Fst Fixation Estimator',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 76: Fish Stock Population Structure & Fst Fixation Estimator.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='marker_counts', label='Marker Counts', type='textarea', default='Atlantic:0.45:0.55, Pacific:0.62:0.38, Indian:0.51:0.49, Southern:0.80:0.20', help='Input for marker counts')
    ],
        handler_name='tool_fish_stock_fst',
        student_tip='Tool #76 (Fish Stock Population Structure & Fst Fixation Estimator) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=77,
        name='Microplastic Ingestion eDNA Barcode Classifier (COI / 18S)',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 77: Microplastic Ingestion eDNA Barcode Classifier (COI / 18S).',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='ACTTTATATTTTATTTTTGGAGCATGAGCCGGAATAGTGGGTACTTCATTAAGTTTATTAATTCGAGCAGAATTAGGAAACCCAGGATCTTTAATTGG', help='Input for sequence')
    ],
        handler_name='tool_microplastic_dna_barcode',
        student_tip='Tool #77 (Microplastic Ingestion eDNA Barcode Classifier (COI / 18S)) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=78,
        name='Harmful Algal Bloom Cyanotoxin Gene Scanner (Microcystin mcyA)',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 78: Harmful Algal Bloom Cyanotoxin Gene Scanner (Microcystin mcyA).',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MATLNRIVIAEQGYPLGLAAVVRNLEPDKVLLGTPAGVGG', help='Input for sequence')
    ],
        handler_name='tool_harmful_algal_bloom_cyanotoxin',
        student_tip='Tool #78 (Harmful Algal Bloom Cyanotoxin Gene Scanner (Microcystin mcyA)) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=79,
        name='Marine Resistome Antibiotic Resistance Gene (ARG) Scanner',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 79: Marine Resistome Antibiotic Resistance Gene (ARG) Scanner.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MKKITLALSALLASVPAGAMAHISGQSVVDALAAKLAP', help='Input for sequence')
    ],
        handler_name='tool_marine_resistome_arg',
        student_tip='Tool #79 (Marine Resistome Antibiotic Resistance Gene (ARG) Scanner) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=80,
        name='Marine Sponge Secondary Metabolite Biosynthetic Cluster Profiler',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 80: Marine Sponge Secondary Metabolite Biosynthetic Cluster Profiler.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MNKLRLLFASLVLCSCSAELLVLDDDGFWREILG', help='Input for sequence')
    ],
        handler_name='tool_marine_sponge_bgc',
        student_tip='Tool #80 (Marine Sponge Secondary Metabolite Biosynthetic Cluster Profiler) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=81,
        name='Marine Phage-to-Host CRISPR Spacer Matcher',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 81: Marine Phage-to-Host CRISPR Spacer Matcher.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='crispr_spacers', label='Crispr Spacers', type='textarea', default='TGCACGTGCCCTGCTTCTCCA, ACTTTATATTTTATTTTTGGA, GGAGCATGAGCCGGAATAGTG', help='Input for crispr spacers'),
        ToolInputSpec(id='phage_seq', label='Phage Seq', type='text', default='TGCACGTGCCCTGCTTCTCCAAATTTTT', help='Input for phage seq')
    ],
        handler_name='tool_marine_phage_spacer_matcher',
        student_tip='Tool #81 (Marine Phage-to-Host CRISPR Spacer Matcher) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=82,
        name='Ocean Acidification Shell Calcification Gene Tracker',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 82: Ocean Acidification Shell Calcification Gene Tracker.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MHHSGKWGGEHNNEPDWAVVGFNYEVEGKGSKSS', help='Input for sequence')
    ],
        handler_name='tool_ocean_acidification_calcification',
        student_tip='Tool #82 (Ocean Acidification Shell Calcification Gene Tracker) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=83,
        name='Marine Invasive Alien Species eDNA Biosurveillance Screen',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 83: Marine Invasive Alien Species eDNA Biosurveillance Screen.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='GGTCAACAAATCATAAAGATATTGGAACCCTTTATTTTATTTTTGGTGCATGAGCAGGAATAGTGGGTACTTCATTAAGTTTATTAATTCGAGCAGAATTAGGAAACCCAGGATCTTTA', help='Input for sequence')
    ],
        handler_name='tool_marine_invasive_edna_screen',
        student_tip='Tool #83 (Marine Invasive Alien Species eDNA Biosurveillance Screen) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=84,
        name='Marine Teleost Fish Sex-Determination Locus Analyzer',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 84: Marine Teleost Fish Sex-Determination Locus Analyzer.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MRKVRVRKEEKEERKKVLIILLVVILLVVLRKRKEEKK', help='Input for sequence')
    ],
        handler_name='tool_fish_sex_determination_locus',
        student_tip='Tool #84 (Marine Teleost Fish Sex-Determination Locus Analyzer) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=85,
        name='Marine Food Web Trophic Position Metabarcode Linker',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 85: Marine Food Web Trophic Position Metabarcode Linker.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='diet_table', label='Diet Table', type='textarea', default='Phytoplankton:0.05, Zooplankton:0.35, Small_Pelagic_Fish:0.40, Squid:0.20', help='Input for diet table')
    ],
        handler_name='tool_marine_food_web_trophic_position',
        student_tip='Tool #85 (Marine Food Web Trophic Position Metabarcode Linker) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=86,
        name='Hydrothermal Vent Chemolithoautotroph Sulfur Operon (soxB) Profiler',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 86: Hydrothermal Vent Chemolithoautotroph Sulfur Operon (soxB) Profiler.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MAKTVVVGAGGAGLRAALGLARRGFAVTVLEKDSFAGGTWR', help='Input for sequence')
    ],
        handler_name='tool_hydrothermal_vent_sulfur_soxb',
        student_tip='Tool #86 (Hydrothermal Vent Chemolithoautotroph Sulfur Operon (soxB) Profiler) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=87,
        name='Marine Microbial Biofilm Quorum Sensing Autoinducer Scanner',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 87: Marine Microbial Biofilm Quorum Sensing Autoinducer Scanner.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MPLLESFTVDHTRMEAPAVRVAKTMNTPHGDAITVFDLRFCVPNKEVM', help='Input for sequence')
    ],
        handler_name='tool_marine_quorum_sensing_luxs',
        student_tip='Tool #87 (Marine Microbial Biofilm Quorum Sensing Autoinducer Scanner) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=88,
        name='Halophilic Archaea Light-Driven Rhodopsin Proton Pump Identifier',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 88: Halophilic Archaea Light-Driven Rhodopsin Proton Pump Identifier.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MDPIALQAGYDLLGDGVPLLTNYLFWLGAMGFGFLTGLYGVTRWL', help='Input for sequence')
    ],
        handler_name='tool_halophilic_rhodopsin_pump',
        student_tip='Tool #88 (Halophilic Archaea Light-Driven Rhodopsin Proton Pump Identifier) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=89,
        name='Antarctic Teleost Antifreeze Glycoprotein (AFGP) Repeat Counter',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 89: Antarctic Teleost Antifreeze Glycoprotein (AFGP) Repeat Counter.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='AATPAATAATAATAATPAATAATAATAATPAATAAT', help='Input for sequence')
    ],
        handler_name='tool_antifreeze_glycoprotein_afgp',
        student_tip='Tool #89 (Antarctic Teleost Antifreeze Glycoprotein (AFGP) Repeat Counter) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=90,
        name='Deep-Diving Cetacean Myoglobin Oxygen-Storage Charge Analyzer',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 90: Deep-Diving Cetacean Myoglobin Oxygen-Storage Charge Analyzer.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MGLSDGEWQLVLNVWGKVEADIPGHGQEVLIRLFKGHPETLEKFDKFKHLKSEDEMKASEDLKKHGATVLTALGGILKKKGHHEAEIKPLAQSHATKHKIPVKYLEFISECIIQVLQSKHPGDFGADAQGAMNKALELFRKDMASNYKELGFQG', help='Input for sequence')
    ],
        handler_name='tool_cetacean_myoglobin_charge',
        student_tip='Tool #90 (Deep-Diving Cetacean Myoglobin Oxygen-Storage Charge Analyzer) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=91,
        name='Marine Heavy Metal Bioremediation Operon Detector',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 91: Marine Heavy Metal Bioremediation Operon Detector.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MTTLKIANGSFDLVLAAVGAPRKEILKLAP', help='Input for sequence')
    ],
        handler_name='tool_marine_metal_bioremediation',
        student_tip='Tool #91 (Marine Heavy Metal Bioremediation Operon Detector) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=92,
        name='Marine Plastic-Degrading Hydrolase (PETase / MHETase) Screener',
        domain='Marine & Extremophile Genomics',
        category_id='marine',
        category_name='Marine & Extremophile Genomics',
        description='Tool 92: Marine Plastic-Degrading Hydrolase (PETase / MHETase) Screener.',
        console_page='66_Marine_and_Extremophile_Genomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MNFPRASRLMQAAVLGGLMAVSAAATAQTNPYARGPNPTAASLEASAGPFTVRSFTVSRPSGYGAGTVYYPTNAGGTVGAIAIVPGYTARQSSIKWWGPRLASHGFVVITIDTNSTLDQPSSRSSQQMAALRQVASLNGTSSSPIYGKVDTARMGVMGWSMGGGGSLISAANNPSLKAAAPQAPWDSSTNFSSVTVPTLIFACENDSIAPVNSSALPIYDSMSRNAKQFLEINGGSHSCANSGNSNQALIGKKGVAWMKRFMDNDTRYSTFACENPNSTRVSDFRTANCS', help='Input for sequence')
    ],
        handler_name='tool_marine_plastic_hydrolase',
        student_tip='Tool #92 (Marine Plastic-Degrading Hydrolase (PETase / MHETase) Screener) demonstrates critical applied computational techniques in Marine & Extremophile Genomics.',
    ),
    ToolSpec(
        id=93,
        name='ACMG / AMP Clinical Variant Pathogenicity Tier Classifier',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 93: ACMG / AMP Clinical Variant Pathogenicity Tier Classifier.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='criteria', label='Criteria', type='text', default='PVS1, PM2, PP3', help='Input for criteria')
    ],
        handler_name='tool_acmg_pathogenicity_classifier',
        student_tip='Tool #93 (ACMG / AMP Clinical Variant Pathogenicity Tier Classifier) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=94,
        name='Somatic Cancer Hotspot Driver Mutation Checker',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 94: Somatic Cancer Hotspot Driver Mutation Checker.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='gene_variant', label='Gene Variant', type='text', default='BRAF:V600E', help='Input for gene variant')
    ],
        handler_name='tool_cancer_hotspot_checker',
        student_tip='Tool #94 (Somatic Cancer Hotspot Driver Mutation Checker) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=95,
        name='Pharmacogenomics (PGx) Star-Allele & Drug Metabolizer Caller',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 95: Pharmacogenomics (PGx) Star-Allele & Drug Metabolizer Caller.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='cyp_star', label='Cyp Star', type='text', default='CYP2D6:*1/*4', help='Input for cyp star')
    ],
        handler_name='tool_pgx_metabolizer_caller',
        student_tip='Tool #95 (Pharmacogenomics (PGx) Star-Allele & Drug Metabolizer Caller) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=96,
        name='Somatic vs Germline Variant Allele Frequency (VAF) Classifier',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 96: Somatic vs Germline Variant Allele Frequency (VAF) Classifier.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='vaf_percent', label='Vaf Percent', type='number', default=48.5, help='Input for vaf percent'),
        ToolInputSpec(id='coverage', label='Coverage', type='number', default=150, help='Input for coverage')
    ],
        handler_name='tool_vaf_somatic_germline',
        student_tip='Tool #96 (Somatic vs Germline Variant Allele Frequency (VAF) Classifier) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=97,
        name='Gene Loss-of-Function Intolerance (pLI & LOEUF) Calculator',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 97: Gene Loss-of-Function Intolerance (pLI & LOEUF) Calculator.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='gene_symbol', label='Gene Symbol', type='text', default='BRCA1', help='Input for gene symbol')
    ],
        handler_name='tool_gene_lof_intolerance',
        student_tip='Tool #97 (Gene Loss-of-Function Intolerance (pLI & LOEUF) Calculator) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=98,
        name='Tumor Mutational Burden (TMB) Clinical Stratifier',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 98: Tumor Mutational Burden (TMB) Clinical Stratifier.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='mutation_count', label='Mutation Count', type='number', default=14, help='Input for mutation count'),
        ToolInputSpec(id='exome_mb', label='Exome Mb', type='number', default=1.1, help='Input for exome mb')
    ],
        handler_name='tool_tumor_mutational_burden',
        student_tip='Tool #98 (Tumor Mutational Burden (TMB) Clinical Stratifier) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=99,
        name='Microsatellite Instability (MSI) Mononucleotide Marker Evaluator',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 99: Microsatellite Instability (MSI) Mononucleotide Marker Evaluator.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='panel_data', label='Panel Data', type='textarea', default='BAT-25:Unstable, BAT-26:Unstable, NR-21:Stable, NR-24:Unstable, MONO-27:Stable', help='Input for panel data')
    ],
        handler_name='tool_msi_evaluator',
        student_tip='Tool #99 (Microsatellite Instability (MSI) Mononucleotide Marker Evaluator) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=100,
        name='ClinVar Variant Evidence & Review Status Cross-Referencer',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 100: ClinVar Variant Evidence & Review Status Cross-Referencer.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='rsid_or_variant', label='Rsid Or Variant', type='text', default='rs28934578', help='Input for rsid or variant')
    ],
        handler_name='tool_clinvar_cross_referencer',
        student_tip='Tool #100 (ClinVar Variant Evidence & Review Status Cross-Referencer) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=101,
        name='Hereditary Cancer Gene Panel Screener',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 101: Hereditary Cancer Gene Panel Screener.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='gene_symbol', label='Gene Symbol', type='text', default='BRCA1', help='Input for gene symbol')
    ],
        handler_name='tool_hereditary_cancer_panel',
        student_tip='Tool #101 (Hereditary Cancer Gene Panel Screener) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=102,
        name='Pediatric Rare Disease Compound Heterozygous Variant Filter',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 102: Pediatric Rare Disease Compound Heterozygous Variant Filter.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='variant_list', label='Variant List', type='textarea', default='Chr1:12345:G>A:Maternal, Chr1:12980:C>T:Paternal, Chr2:56789:A>G:DeNovo', help='Input for variant list')
    ],
        handler_name='tool_compound_heterozygous_filter',
        student_tip='Tool #102 (Pediatric Rare Disease Compound Heterozygous Variant Filter) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=103,
        name='HLA-A/B Allele Typing & Peptide MHC-I Binding Affinity Estimator',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 103: HLA-A/B Allele Typing & Peptide MHC-I Binding Affinity Estimator.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='hla_allele', label='Hla Allele', type='text', default='HLA-A*02:01', help='Input for hla allele'),
        ToolInputSpec(id='peptide_seq', label='Peptide Seq', type='text', default='NLVPMVATV', help='Input for peptide seq')
    ],
        handler_name='tool_hla_mhc_binding_affinity',
        student_tip='Tool #103 (HLA-A/B Allele Typing & Peptide MHC-I Binding Affinity Estimator) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=104,
        name='Canonical Splice Donor/Acceptor Dinucleotide Disruption Scorer',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 104: Canonical Splice Donor/Acceptor Dinucleotide Disruption Scorer.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='exon_intron_junction', label='Exon Intron Junction', type='text', default='CAGGTAAGT', help='Input for exon intron junction')
    ],
        handler_name='tool_splice_site_disruption',
        student_tip='Tool #104 (Canonical Splice Donor/Acceptor Dinucleotide Disruption Scorer) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=105,
        name='Copy Number Alteration (CNA) Log2 Ratio Segmenter',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 105: Copy Number Alteration (CNA) Log2 Ratio Segmenter.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='log2_ratio_input', label='Log2 Ratio Input', type='textarea', default='Chr1:0.02, Chr2:-0.52, Chr3:0.01, Chr7:0.95, Chr8:1.15, Chr17:-1.45', help='Input for log2 ratio input')
    ],
        handler_name='tool_cna_log2_segmenter',
        student_tip='Tool #105 (Copy Number Alteration (CNA) Log2 Ratio Segmenter) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=106,
        name='Mitochondrial DNA Heteroplasmy & Pathogenic Variant Caller',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 106: Mitochondrial DNA Heteroplasmy & Pathogenic Variant Caller.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='allele_depths', label='Allele Depths', type='textarea', default='m.3243A>G:Ref=1200:Alt=650, m.8344A>G:Ref=1800:Alt=40', help='Input for allele depths')
    ],
        handler_name='tool_mtdna_heteroplasmy_caller',
        student_tip='Tool #106 (Mitochondrial DNA Heteroplasmy & Pathogenic Variant Caller) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=107,
        name='Polygenic Risk Score (PRS) Additive Allele Effect Calculator',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 107: Polygenic Risk Score (PRS) Additive Allele Effect Calculator.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='snp_weights', label='Snp Weights', type='textarea', default='rs10455872:0.42:2, rs3798220:0.35:1, rs11591147:-0.28:0, rs6025:0.51:1', help='Input for snp weights')
    ],
        handler_name='tool_polygenic_risk_score',
        student_tip='Tool #107 (Polygenic Risk Score (PRS) Additive Allele Effect Calculator) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=108,
        name='Circulating Tumor DNA (ctDNA) Liquid Biopsy Minimal Residue Evaluator',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 108: Circulating Tumor DNA (ctDNA) Liquid Biopsy Minimal Residue Evaluator.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='ctdna_vaf', label='Ctdna Vaf', type='number', default=0.45, help='Input for ctdna vaf'),
        ToolInputSpec(id='total_cfdna_ng', label='Total Cfdna Ng', type='number', default=25.0, help='Input for total cfdna ng')
    ],
        handler_name='tool_ctdna_liquid_biopsy',
        student_tip='Tool #108 (Circulating Tumor DNA (ctDNA) Liquid Biopsy Minimal Residue Evaluator) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=109,
        name='Long QT Cardiac Channelopathy (KCNQ1 / SCN5A) Variant Scorer',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 109: Long QT Cardiac Channelopathy (KCNQ1 / SCN5A) Variant Scorer.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='seq_variant', label='Seq Variant', type='text', default='KCNQ1:c.1022C>T:p.Thr341Ile', help='Input for seq variant')
    ],
        handler_name='tool_cardiac_channelopathy_scorer',
        student_tip='Tool #109 (Long QT Cardiac Channelopathy (KCNQ1 / SCN5A) Variant Scorer) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=110,
        name='Trinucleotide Repeat Expansion Neurodegenerative Scorer',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 110: Trinucleotide Repeat Expansion Neurodegenerative Scorer.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='repeat_count', label='Repeat Count', type='number', default=44, help='Input for repeat count'),
        ToolInputSpec(id='locus_name', label='Locus Name', type='text', default='HTT (Huntington Disease)', help='Input for locus name')
    ],
        handler_name='tool_neurodegenerative_repeat_expansion',
        student_tip='Tool #110 (Trinucleotide Repeat Expansion Neurodegenerative Scorer) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=111,
        name='Viral Drug Resistance Mutation Profiler',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 111: Viral Drug Resistance Mutation Profiler.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='target_gene', label='Target Gene', type='text', default='HIV-1 Reverse Transcriptase', help='Input for target gene'),
        ToolInputSpec(id='mutation', label='Mutation', type='text', default='M184V, K103N', help='Input for mutation')
    ],
        handler_name='tool_viral_drug_resistance_profiler',
        student_tip='Tool #111 (Viral Drug Resistance Mutation Profiler) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=112,
        name='Clinical Exome Target Coverage & Diagnostic Completeness Auditor',
        domain='Clinical Genomics & Precision Medicine',
        category_id='clinical',
        category_name='Clinical Genomics & Precision Medicine',
        description='Tool 112: Clinical Exome Target Coverage & Diagnostic Completeness Auditor.',
        console_page='67_Clinical_Genomics_Precision_Medicine.py',
        inputs=[
        ToolInputSpec(id='coverage_data', label='Coverage Data', type='textarea', default='>=10x:99.2, >=20x:96.8, >=50x:88.4, >=100x:68.2', help='Input for coverage data')
    ],
        handler_name='tool_exome_coverage_auditor',
        student_tip='Tool #112 (Clinical Exome Target Coverage & Diagnostic Completeness Auditor) demonstrates critical applied computational techniques in Clinical Genomics & Precision Medicine.',
    ),
    ToolSpec(
        id=113,
        name='Alpha Diversity Estimator (Shannon, Simpson, Chao1, Pielou)',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 113: Alpha Diversity Estimator (Shannon, Simpson, Chao1, Pielou).',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='otu_input', label='Otu Input', type='textarea', default='Taxon1:1200, Taxon2:850, Taxon3:420, Taxon4:110, Taxon5:35, Taxon6:12, Taxon7:4, Taxon8:1', help='Input for otu input')
    ],
        handler_name='tool_alpha_diversity_estimator',
        student_tip='Tool #113 (Alpha Diversity Estimator (Shannon, Simpson, Chao1, Pielou)) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=114,
        name='Beta Diversity & Bray-Curtis Dissimilarity Distance Matrix',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 114: Beta Diversity & Bray-Curtis Dissimilarity Distance Matrix.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='matrix_data', label='Matrix Data', type='textarea', default='SampleA:100:50:20:0, SampleB:90:60:15:5, SampleC:10:5:80:120', help='Input for matrix data')
    ],
        handler_name='tool_beta_diversity_bray_curtis',
        student_tip='Tool #114 (Beta Diversity & Bray-Curtis Dissimilarity Distance Matrix) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=115,
        name='16S rRNA Hypervariable Region Primer Compatibility Evaluator',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 115: 16S rRNA Hypervariable Region Primer Compatibility Evaluator.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='primer_f', label='Primer F', type='text', default='GTGCCAGCMGCCGCGGTAA', help='Input for primer f'),
        ToolInputSpec(id='primer_r', label='Primer R', type='text', default='GGACTACHVGGGTWTCTAAT', help='Input for primer r'),
        ToolInputSpec(id='target_region', label='Target Region', type='text', default='V4 Region (515F - 806R)', help='Input for target region')
    ],
        handler_name='tool_16s_primer_evaluator',
        student_tip='Tool #115 (16S rRNA Hypervariable Region Primer Compatibility Evaluator) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=116,
        name='Metagenomic Contig GC-vs-Coverage Binning Separator',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 116: Metagenomic Contig GC-vs-Coverage Binning Separator.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='contig_text', label='Contig Text', type='textarea', default='Contig1:45.2:120, Contig2:46.0:115, Contig3:44.8:130, Contig4:68.5:35, Contig5:67.8:40, Contig6:69.1:38', help='Input for contig text')
    ],
        handler_name='tool_contig_gc_coverage_binner',
        student_tip='Tool #116 (Metagenomic Contig GC-vs-Coverage Binning Separator) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=117,
        name='Human Gut Dysbiosis Index (Firmicutes-to-Bacteroidetes Ratio)',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 117: Human Gut Dysbiosis Index (Firmicutes-to-Bacteroidetes Ratio).',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='firmicutes_count', label='Firmicutes Count', type='number', default=6500.0, help='Input for firmicutes count'),
        ToolInputSpec(id='bacteroidetes_count', label='Bacteroidetes Count', type='number', default=2500.0, help='Input for bacteroidetes count')
    ],
        handler_name='tool_gut_dysbiosis_fb_ratio',
        student_tip='Tool #117 (Human Gut Dysbiosis Index (Firmicutes-to-Bacteroidetes Ratio)) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=118,
        name='CARD Antibiotic Resistance Ontology & Mechanism Finder',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 118: CARD Antibiotic Resistance Ontology & Mechanism Finder.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MRFAISLVALLLGAACSAQPGTAPVTVYQVSSGGYVVALAR', help='Input for sequence')
    ],
        handler_name='tool_card_arg_finder',
        student_tip='Tool #118 (CARD Antibiotic Resistance Ontology & Mechanism Finder) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=119,
        name='Virulence Factor Database (VFDB) Pathogenicity Island Profiler',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 119: Virulence Factor Database (VFDB) Pathogenicity Island Profiler.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MTESIGLLGTVIFCLGGFSLALSSVVSG', help='Input for sequence')
    ],
        handler_name='tool_vfdb_virulence_profiler',
        student_tip='Tool #119 (Virulence Factor Database (VFDB) Pathogenicity Island Profiler) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=120,
        name='Prophage Integration Site & AttB/AttP Sequence Finder',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 120: Prophage Integration Site & AttB/AttP Sequence Finder.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC', help='Input for sequence')
    ],
        handler_name='tool_prophage_integration_finder',
        student_tip='Tool #120 (Prophage Integration Site & AttB/AttP Sequence Finder) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=121,
        name='Bacterial Pan-Genome Core vs Accessory Partition Calculator',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 121: Bacterial Pan-Genome Core vs Accessory Partition Calculator.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='strain_count', label='Strain Count', type='number', default=25, help='Input for strain count'),
        ToolInputSpec(id='core_genes', label='Core Genes', type='number', default=2850, help='Input for core genes'),
        ToolInputSpec(id='shell_genes', label='Shell Genes', type='number', default=1420, help='Input for shell genes'),
        ToolInputSpec(id='cloud_genes', label='Cloud Genes', type='number', default=3100, help='Input for cloud genes')
    ],
        handler_name='tool_pangenome_partitioner',
        student_tip='Tool #121 (Bacterial Pan-Genome Core vs Accessory Partition Calculator) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=122,
        name='Biosynthetic Gene Cluster (BGC) Domain Architecture Scanner',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 122: Biosynthetic Gene Cluster (BGC) Domain Architecture Scanner.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MAKTVVVGAGGAGLRAALGLARRGFAVTVLEKDSFAGGTWR', help='Input for sequence')
    ],
        handler_name='tool_bgc_domain_scanner',
        student_tip='Tool #122 (Biosynthetic Gene Cluster (BGC) Domain Architecture Scanner) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=123,
        name='Taxonomic Collector Rarefaction Curve Simulator',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 123: Taxonomic Collector Rarefaction Curve Simulator.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='read_depth', label='Read Depth', type='number', default=50000, help='Input for read depth'),
        ToolInputSpec(id='max_otus', label='Max Otus', type='number', default=450, help='Input for max otus')
    ],
        handler_name='tool_rarefaction_curve_simulator',
        student_tip='Tool #123 (Taxonomic Collector Rarefaction Curve Simulator) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=124,
        name='Metagenome-Assembled Genome (MAG) CheckM Completeness Evaluator',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 124: Metagenome-Assembled Genome (MAG) CheckM Completeness Evaluator.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='completeness_pct', label='Completeness Pct', type='number', default=94.5, help='Input for completeness pct'),
        ToolInputSpec(id='contamination_pct', label='Contamination Pct', type='number', default=2.1, help='Input for contamination pct')
    ],
        handler_name='tool_mag_checkm_evaluator',
        student_tip='Tool #124 (Metagenome-Assembled Genome (MAG) CheckM Completeness Evaluator) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=125,
        name='Bacterial CRISPR-Cas Operon & Repeat-Spacer Finder',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 125: Bacterial CRISPR-Cas Operon & Repeat-Spacer Finder.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC', help='Input for sequence')
    ],
        handler_name='tool_crispr_cas_operon_finder',
        student_tip='Tool #125 (Bacterial CRISPR-Cas Operon & Repeat-Spacer Finder) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=126,
        name='Pathogen Epidemiological Outbreak Transmission Chain Estimator',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 126: Pathogen Epidemiological Outbreak Transmission Chain Estimator.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='isolate_snps', label='Isolate Snps', type='textarea', default='IsolateA-IsolateB:1, IsolateB-IsolateC:2, IsolateC-IsolateD:1, IsolateB-IsolateE:7', help='Input for isolate snps')
    ],
        handler_name='tool_outbreak_transmission_tree',
        student_tip='Tool #126 (Pathogen Epidemiological Outbreak Transmission Chain Estimator) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=127,
        name='KEGG Orthology (KO) Functional Abundance Profiler',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 127: KEGG Orthology (KO) Functional Abundance Profiler.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='ko_counts', label='Ko Counts', type='textarea', default='K00261:450, K00370:280, K02586:190, K01955:340, K00844:510', help='Input for ko counts')
    ],
        handler_name='tool_kegg_ko_functional_profiler',
        student_tip='Tool #127 (KEGG Orthology (KO) Functional Abundance Profiler) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=128,
        name='Bacterial O-Antigen Serotype Classifier',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 128: Bacterial O-Antigen Serotype Classifier.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MTESIGLLGTVIFCLGGFSLALSSVVSG', help='Input for sequence')
    ],
        handler_name='tool_bacterial_o_antigen_serotyper',
        student_tip='Tool #128 (Bacterial O-Antigen Serotype Classifier) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=129,
        name='Bacterial Plasmid Incompatibility Group (Inc-Type) Detector',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 129: Bacterial Plasmid Incompatibility Group (Inc-Type) Detector.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='ATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC', help='Input for sequence')
    ],
        handler_name='tool_plasmid_inc_replicon_detector',
        student_tip='Tool #129 (Bacterial Plasmid Incompatibility Group (Inc-Type) Detector) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=130,
        name='Bacterial Secretion System (Type I-VI) Subunit Finder',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 130: Bacterial Secretion System (Type I-VI) Subunit Finder.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='MAATPRLVSGAVALLLGCS', help='Input for sequence')
    ],
        handler_name='tool_bacterial_secretion_system_finder',
        student_tip='Tool #130 (Bacterial Secretion System (Type I-VI) Subunit Finder) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=131,
        name='Gut Enterotype Distance Classifier',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 131: Gut Enterotype Distance Classifier.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='genus_ratios', label='Genus Ratios', type='textarea', default='Bacteroides:0.55, Prevotella:0.15, Ruminococcus:0.30', help='Input for genus ratios')
    ],
        handler_name='tool_gut_enterotype_classifier',
        student_tip='Tool #131 (Gut Enterotype Distance Classifier) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=132,
        name='Wastewater Epidemiology Viral Abundance & Variant Tracker',
        domain='Metagenomics & Microbiome',
        category_id='metagenomics',
        category_name='Metagenomics & Microbiome',
        description='Tool 132: Wastewater Epidemiology Viral Abundance & Variant Tracker.',
        console_page='68_Metagenomics_and_Microbiome.py',
        inputs=[
        ToolInputSpec(id='ct_values', label='Ct Values', type='text', default='N1:28.4, N2:29.1, PMMoV:19.5', help='Input for ct values')
    ],
        handler_name='tool_wastewater_viral_surveillance',
        student_tip='Tool #132 (Wastewater Epidemiology Viral Abundance & Variant Tracker) demonstrates critical applied computational techniques in Metagenomics & Microbiome.',
    ),
    ToolSpec(
        id=133,
        name='PDB Atomic Coordinate & ATOM Record Structural Parser',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 133: PDB Atomic Coordinate & ATOM Record Structural Parser.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='pdb_text', label='Pdb Text', type='textarea', default='ATOM      1  N   ALA A   1      11.104  13.201  10.324  1.00 20.00           N\nATOM      2  CA  ALA A   1      12.560  13.450  10.120  1.00 21.00           C\nATOM      3  C   ALA A   1      13.200  12.300  10.800  1.00 22.00           C\nATOM      4  O   ALA A   1      14.300  12.400  11.300  1.00 23.00           O', help='Input for pdb text')
    ],
        handler_name='tool_pdb_parser',
        student_tip='Tool #133 (PDB Atomic Coordinate & ATOM Record Structural Parser) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=134,
        name='Ramachandran Backbone Torsion Angle (Phi/Psi) Validator',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 134: Ramachandran Backbone Torsion Angle (Phi/Psi) Validator.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='phi_psi_data', label='Phi Psi Data', type='textarea', default='-57:-47, -60:-50, -120:130, -140:150, 60:40, -90:0', help='Input for phi psi data')
    ],
        handler_name='tool_ramachandran_validator',
        student_tip='Tool #134 (Ramachandran Backbone Torsion Angle (Phi/Psi) Validator) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=135,
        name='Residue Contact Map & C-alpha Distance Matrix',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 135: Residue Contact Map & C-alpha Distance Matrix.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='length', label='Length', type='number', default=25, help='Input for length')
    ],
        handler_name='tool_residue_contact_map',
        student_tip='Tool #135 (Residue Contact Map & C-alpha Distance Matrix) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=136,
        name='Crystallographic B-Factor Local Flexibility & Disorder Analyzer',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 136: Crystallographic B-Factor Local Flexibility & Disorder Analyzer.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='bfactor_string', label='Bfactor String', type='textarea', default='18.2, 19.5, 21.0, 35.4, 48.2, 52.1, 28.3, 20.1, 17.5', help='Input for bfactor string')
    ],
        handler_name='tool_bfactor_flexibility',
        student_tip='Tool #136 (Crystallographic B-Factor Local Flexibility & Disorder Analyzer) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=137,
        name='Protein Salt Bridge & Ionic Charge Network Identifier',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 137: Protein Salt Bridge & Ionic Charge Network Identifier.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='pairs', label='Pairs', type='textarea', default='Asp12-Arg85:2.8, Glu45-Lys102:3.2, Asp90-His112:3.8, Glu15-Lys19:5.5', help='Input for pairs')
    ],
        handler_name='tool_salt_bridge_finder',
        student_tip='Tool #137 (Protein Salt Bridge & Ionic Charge Network Identifier) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=138,
        name='Ligand Binding Pocket Geometry & Cavity Volume Estimator',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 138: Ligand Binding Pocket Geometry & Cavity Volume Estimator.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='length_x', label='Length X', type='number', default=12.0, help='Input for length x'),
        ToolInputSpec(id='width_y', label='Width Y', type='number', default=10.5, help='Input for width y'),
        ToolInputSpec(id='depth_z', label='Depth Z', type='number', default=8.0, help='Input for depth z')
    ],
        handler_name='tool_pocket_volume_estimator',
        student_tip='Tool #138 (Ligand Binding Pocket Geometry & Cavity Volume Estimator) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=139,
        name='Residue Solvent Accessible Surface Area (SASA) Model',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 139: Residue Solvent Accessible Surface Area (SASA) Model.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='MAKAAAIGIDLGTTYSCVGVFQHGKVEIIANDQGNRTTPSYVAFTD', help='Input for sequence')
    ],
        handler_name='tool_sasa_calculator',
        student_tip='Tool #139 (Residue Solvent Accessible Surface Area (SASA) Model) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=140,
        name='AlphaFold pLDDT Confidence Profile & Disorder Predictor',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 140: AlphaFold pLDDT Confidence Profile & Disorder Predictor.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='plddt_values', label='Plddt Values', type='textarea', default='94.2, 95.1, 92.0, 88.5, 78.2, 62.1, 45.0, 38.2, 42.1, 85.0, 91.5', help='Input for plddt values')
    ],
        handler_name='tool_alphafold_plddt_analyzer',
        student_tip='Tool #140 (AlphaFold pLDDT Confidence Profile & Disorder Predictor) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=141,
        name='Protein Oligomeric Quaternary Complex Buried Surface Area (BSA)',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 141: Protein Oligomeric Quaternary Complex Buried Surface Area (BSA).',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='monomer_a_sasa', label='Monomer A Sasa', type='number', default=8500.0, help='Input for monomer a sasa'),
        ToolInputSpec(id='monomer_b_sasa', label='Monomer B Sasa', type='number', default=8200.0, help='Input for monomer b sasa'),
        ToolInputSpec(id='dimer_complex_sasa', label='Dimer Complex Sasa', type='number', default=14800.0, help='Input for dimer complex sasa')
    ],
        handler_name='tool_buried_surface_area',
        student_tip='Tool #141 (Protein Oligomeric Quaternary Complex Buried Surface Area (BSA)) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=142,
        name='Beta-Turn & Tight-Loop Structural Conformation Classifier',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 142: Beta-Turn & Tight-Loop Structural Conformation Classifier.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='phi2', label='Phi2', type='number', default=-60.0, help='Input for phi2'),
        ToolInputSpec(id='psi2', label='Psi2', type='number', default=-30.0, help='Input for psi2'),
        ToolInputSpec(id='phi3', label='Phi3', type='number', default=-90.0, help='Input for phi3'),
        ToolInputSpec(id='psi3', label='Psi3', type='number', default=0.0, help='Input for psi3')
    ],
        handler_name='tool_beta_turn_classifier',
        student_tip='Tool #142 (Beta-Turn & Tight-Loop Structural Conformation Classifier) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=143,
        name='Alpha-Helix Net Dipole Moment & Charge Neutralization',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 143: Alpha-Helix Net Dipole Moment & Charge Neutralization.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='helix_length_residues', label='Helix Length Residues', type='number', default=15, help='Input for helix length residues')
    ],
        handler_name='tool_helix_dipole_moment',
        student_tip='Tool #143 (Alpha-Helix Net Dipole Moment & Charge Neutralization) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=144,
        name='Transmembrane Segment Hydrophobic Moment Predictor',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 144: Transmembrane Segment Hydrophobic Moment Predictor.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='LALLVLALLLALLVLLALLL', help='Input for sequence')
    ],
        handler_name='tool_transmembrane_hydrophobic_moment',
        student_tip='Tool #144 (Transmembrane Segment Hydrophobic Moment Predictor) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=145,
        name='Protein Radius of Gyration (Rg) & Compactness Index',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 145: Protein Radius of Gyration (Rg) & Compactness Index.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='num_residues', label='Num Residues', type='number', default=150, help='Input for num residues')
    ],
        handler_name='tool_radius_of_gyration',
        student_tip='Tool #145 (Protein Radius of Gyration (Rg) & Compactness Index) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=146,
        name='Disulfide Crosslink Geometrical Distance & Pairing Matcher',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 146: Disulfide Crosslink Geometrical Distance & Pairing Matcher.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='cys_pairs', label='Cys Pairs', type='textarea', default='Cys12-Cys65:2.04:95.4, Cys34-Cys88:2.06:-88.2, Cys50-Cys110:3.80:15.0', help='Input for cys pairs')
    ],
        handler_name='tool_disulfide_geometry_matcher',
        student_tip='Tool #146 (Disulfide Crosslink Geometrical Distance & Pairing Matcher) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=147,
        name='Protein Residue Interaction Network Betweenness Centrality',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 147: Protein Residue Interaction Network Betweenness Centrality.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='n_nodes', label='N Nodes', type='number', default=12, help='Input for n nodes')
    ],
        handler_name='tool_residue_network_centrality',
        student_tip='Tool #147 (Protein Residue Interaction Network Betweenness Centrality) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=148,
        name='Amyloid Fibril & Beta-Sheet Aggregation Propensity Predictor',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 148: Amyloid Fibril & Beta-Sheet Aggregation Propensity Predictor.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='KLVFFAGVGGSGAAV', help='Input for sequence')
    ],
        handler_name='tool_amyloid_aggregation_propensity',
        student_tip='Tool #148 (Amyloid Fibril & Beta-Sheet Aggregation Propensity Predictor) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=149,
        name='Protein Secondary Structure DSSP Hydrogen Bond Matcher',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 149: Protein Secondary Structure DSSP Hydrogen Bond Matcher.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='hbond_energy_kcal_mol', label='Hbond Energy Kcal Mol', type='number', default=-2.4, help='Input for hbond energy kcal mol')
    ],
        handler_name='tool_dssp_hydrogen_bond_matcher',
        student_tip='Tool #149 (Protein Secondary Structure DSSP Hydrogen Bond Matcher) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=150,
        name='Cryo-EM Fourier Shell Correlation (FSC) Resolution Estimator',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 150: Cryo-EM Fourier Shell Correlation (FSC) Resolution Estimator.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='fsc_data', label='Fsc Data', type='textarea', default='0.10:0.98, 0.20:0.95, 0.30:0.82, 0.40:0.55, 0.45:0.143, 0.50:0.04', help='Input for fsc data')
    ],
        handler_name='tool_cryoem_fsc_resolution',
        student_tip='Tool #150 (Cryo-EM Fourier Shell Correlation (FSC) Resolution Estimator) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=151,
        name='Molecular Docking Empirical Binding Free Energy Calculator',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 151: Molecular Docking Empirical Binding Free Energy Calculator.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='contacts', label='Contacts', type='textarea', default='H-Bonds:3:-2.1, Hydrophobic:6:-1.8, Pi-Pi:2:-1.2, Salt-Bridge:1:-3.0', help='Input for contacts')
    ],
        handler_name='tool_docking_binding_energy',
        student_tip='Tool #151 (Molecular Docking Empirical Binding Free Energy Calculator) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=152,
        name='Metal Ion Coordination Sphere & Zinc-Finger Geometry Scanner',
        domain='Structural Biology & Biophysics',
        category_id='structural',
        category_name='Structural Biology & Biophysics',
        description='Tool 152: Metal Ion Coordination Sphere & Zinc-Finger Geometry Scanner.',
        console_page='69_Structural_Biology_and_Biophysics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='KPFACPECGKSFSQKSDLVKHQRTHTG', help='Input for sequence')
    ],
        handler_name='tool_zinc_finger_coordination',
        student_tip='Tool #152 (Metal Ion Coordination Sphere & Zinc-Finger Geometry Scanner) demonstrates critical applied computational techniques in Structural Biology & Biophysics.',
    ),
    ToolSpec(
        id=153,
        name='Bisulfite Sequencing C-to-T Conversion Rate Scorer',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 153: Bisulfite Sequencing C-to-T Conversion Rate Scorer.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='TTCGTTTTTGTTTTTTTCGTTGTTTT', help='Input for sequence')
    ],
        handler_name='tool_bisulfite_conversion_rate',
        student_tip='Tool #153 (Bisulfite Sequencing C-to-T Conversion Rate Scorer) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=154,
        name='Differentially Methylated Region (DMR) Sliding Window Detector',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 154: Differentially Methylated Region (DMR) Sliding Window Detector.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='window_data', label='Window Data', type='textarea', default='Win1:0.12:0.85, Win2:0.15:0.78, Win3:0.45:0.50, Win4:0.80:0.82', help='Input for window data')
    ],
        handler_name='tool_dmr_sliding_window',
        student_tip='Tool #154 (Differentially Methylated Region (DMR) Sliding Window Detector) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=155,
        name='Histone Mark (ChIP-seq) Peak Height & Significance Estimator',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 155: Histone Mark (ChIP-seq) Peak Height & Significance Estimator.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='pileup_data', label='Pileup Data', type='textarea', default='Peak1:120:15, Peak2:85:12, Peak3:35:30, Peak4:240:18', help='Input for pileup data')
    ],
        handler_name='tool_chip_seq_peak_caller',
        student_tip='Tool #155 (Histone Mark (ChIP-seq) Peak Height & Significance Estimator) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=156,
        name='RNA-seq Differential Expression Volcano Plot Engine',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 156: RNA-seq Differential Expression Volcano Plot Engine.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='genes_input', label='Genes Input', type='textarea', default='MYC:2.4:1e-8, TP53:-1.8:2e-5, GAPDH:0.1:0.65, ACTB:-0.05:0.80, EGFR:3.1:1e-12, VEGFA:1.9:4e-6', help='Input for genes input')
    ],
        handler_name='tool_rna_seq_volcano_plot',
        student_tip='Tool #156 (RNA-seq Differential Expression Volcano Plot Engine) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=157,
        name='Nussinov Dynamic Programming RNA Secondary Structure Predictor',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 157: Nussinov Dynamic Programming RNA Secondary Structure Predictor.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='rna_seq', label='Rna Seq', type='text', default='GGGAAACCC', help='Input for rna seq')
    ],
        handler_name='tool_nussinov_rna_folding',
        student_tip='Tool #157 (Nussinov Dynamic Programming RNA Secondary Structure Predictor) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=158,
        name='Alternative Splicing Event Classifier',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 158: Alternative Splicing Event Classifier.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='junction_reads', label='Junction Reads', type='textarea', default='SE:ExonSkipping:450:80, RI:IntronRetention:65:12, A5SS:Alt5Splice:120:45, A3SS:Alt3Splice:95:30', help='Input for junction reads')
    ],
        handler_name='tool_alternative_splicing_classifier',
        student_tip='Tool #158 (Alternative Splicing Event Classifier) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=159,
        name="MicroRNA 5' Seed Complementary Target Matcher",
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description="Tool 159: MicroRNA 5' Seed Complementary Target Matcher.",
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='mirna_seed', label='Mirna Seed', type='text', default='GAGCAGA', help='Input for mirna seed'),
        ToolInputSpec(id='target_utr', label='Target Utr', type='text', default='ACGTGCCTGCTGCTCCATCGTATAA', help='Input for target utr')
    ],
        handler_name='tool_microrna_seed_matcher',
        student_tip="Tool #159 (MicroRNA 5' Seed Complementary Target Matcher) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.",
    ),
    ToolSpec(
        id=160,
        name='Long Non-Coding RNA (lncRNA) Coding Potential Calculator',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 160: Long Non-Coding RNA (lncRNA) Coding Potential Calculator.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='ATGCGTAGTCTAGCTAGCTGATCGATCGATCGATCGATCGATCGATCG', help='Input for sequence')
    ],
        handler_name='tool_lncrna_coding_potential',
        student_tip='Tool #160 (Long Non-Coding RNA (lncRNA) Coding Potential Calculator) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=161,
        name='R-Loop (RNA:DNA Hybrid) Formation Propensity Scanner',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 161: R-Loop (RNA:DNA Hybrid) Formation Propensity Scanner.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='GGGGATCGGGGATCGGGGATCGCGCGCGATCGATCGATC', help='Input for sequence')
    ],
        handler_name='tool_rloop_propensity_scanner',
        student_tip='Tool #161 (R-Loop (RNA:DNA Hybrid) Formation Propensity Scanner) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=162,
        name='Circular RNA (circRNA) Back-Splice Junction Detector',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 162: Circular RNA (circRNA) Back-Splice Junction Detector.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='junction_seq', label='Junction Seq', type='text', default='TGCAGCCCGATCGATCGATCGATCAGGTAGT', help='Input for junction seq')
    ],
        handler_name='tool_circrna_backsplice_finder',
        student_tip='Tool #162 (Circular RNA (circRNA) Back-Splice Junction Detector) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=163,
        name='Chimeric Gene Fusion Transcript Breakpoint Identifier',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 163: Chimeric Gene Fusion Transcript Breakpoint Identifier.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='fusion_name', label='Fusion Name', type='text', default='BCR-ABL1 (Philadelphia Chromosome)', help='Input for fusion name')
    ],
        handler_name='tool_fusion_gene_breakpoint',
        student_tip='Tool #163 (Chimeric Gene Fusion Transcript Breakpoint Identifier) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=164,
        name='Ribosome Profiling (Ribo-seq) Translation Efficiency Ratio',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 164: Ribosome Profiling (Ribo-seq) Translation Efficiency Ratio.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='ribo_fpkm', label='Ribo Fpkm', type='number', default=85.0, help='Input for ribo fpkm'),
        ToolInputSpec(id='rna_fpkm', label='Rna Fpkm', type='number', default=34.0, help='Input for rna fpkm')
    ],
        handler_name='tool_ribo_seq_translation_efficiency',
        student_tip='Tool #164 (Ribosome Profiling (Ribo-seq) Translation Efficiency Ratio) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=165,
        name='Position Weight Matrix (PWM) TFBS Scanner',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 165: Position Weight Matrix (PWM) TFBS Scanner.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='TATGCAATCGGGTAATTGACCTAGCGTAC', help='Input for sequence')
    ],
        handler_name='tool_pwm_tfbs_scanner',
        student_tip='Tool #165 (Position Weight Matrix (PWM) TFBS Scanner) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=166,
        name='Post-Transcriptional RNA Editing (A-to-I) Candidate Detector',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 166: Post-Transcriptional RNA Editing (A-to-I) Candidate Detector.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='GGATACGATCGACCCGTAGTCGTAG', help='Input for sequence')
    ],
        handler_name='tool_rna_editing_a_to_i',
        student_tip='Tool #166 (Post-Transcriptional RNA Editing (A-to-I) Candidate Detector) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=167,
        name='Single-Cell RNA-seq Marker Gene Gini Specificity Score',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 167: Single-Cell RNA-seq Marker Gene Gini Specificity Score.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='expression_profile', label='Expression Profile', type='textarea', default='CellType1:125.0, CellType2:0.2, CellType3:0.0, CellType4:1.1', help='Input for expression profile')
    ],
        handler_name='tool_single_cell_gini_marker',
        student_tip='Tool #167 (Single-Cell RNA-seq Marker Gene Gini Specificity Score) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=168,
        name='Cleavage & Polyadenylation Signal (PAS) Locator',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 168: Cleavage & Polyadenylation Signal (PAS) Locator.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='ATGCGTAGTCAATAAATTTTTATTAAAGCTAGCTAG', help='Input for sequence')
    ],
        handler_name='tool_polyadenylation_signal_finder',
        student_tip='Tool #168 (Cleavage & Polyadenylation Signal (PAS) Locator) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=169,
        name='ATAC-seq Fragment Length & Nucleosome Phasing Engine',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 169: ATAC-seq Fragment Length & Nucleosome Phasing Engine.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='mode_mono', label='Mode Mono', type='number', default=147, help='Input for mode mono'),
        ToolInputSpec(id='mode_di', label='Mode Di', type='number', default=294, help='Input for mode di')
    ],
        handler_name='tool_atac_seq_fragment_length',
        student_tip='Tool #169 (ATAC-seq Fragment Length & Nucleosome Phasing Engine) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=170,
        name='Chromatin Enhancer-Promoter Contact Probability Decay',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 170: Chromatin Enhancer-Promoter Contact Probability Decay.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='distance_kb', label='Distance Kb', type='number', default=45.0, help='Input for distance kb')
    ],
        handler_name='tool_enhancer_promoter_looping',
        student_tip='Tool #170 (Chromatin Enhancer-Promoter Contact Probability Decay) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=171,
        name='N6-Methyladenosine (m6A) Consensus Motif (DRACH) Predictor',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 171: N6-Methyladenosine (m6A) Consensus Motif (DRACH) Predictor.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='ATGGAACTGGAGACTGCAGACT', help='Input for sequence')
    ],
        handler_name='tool_m6a_drach_motif_finder',
        student_tip='Tool #171 (N6-Methyladenosine (m6A) Consensus Motif (DRACH) Predictor) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=172,
        name='Percent Spliced In (PSI) Exon Inclusion Metric Calculator',
        domain='Epigenetics & Epitranscriptomics',
        category_id='epigenetics',
        category_name='Epigenetics & Epitranscriptomics',
        description='Tool 172: Percent Spliced In (PSI) Exon Inclusion Metric Calculator.',
        console_page='70_Epigenetics_and_Epitranscriptomics.py',
        inputs=[
        ToolInputSpec(id='inclusion_reads', label='Inclusion Reads', type='number', default=145, help='Input for inclusion reads'),
        ToolInputSpec(id='exclusion_reads', label='Exclusion Reads', type='number', default=25, help='Input for exclusion reads')
    ],
        handler_name='tool_psi_exon_inclusion',
        student_tip='Tool #172 (Percent Spliced In (PSI) Exon Inclusion Metric Calculator) demonstrates critical applied computational techniques in Epigenetics & Epitranscriptomics.',
    ),
    ToolSpec(
        id=173,
        name='Golden Gate Assembly Type IIS Overhang Fidelity Checker',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 173: Golden Gate Assembly Type IIS Overhang Fidelity Checker.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='overhangs', label='Overhangs', type='text', default='GGAG, AATG, AGGT, GCTT, CGCT', help='Input for overhangs')
    ],
        handler_name='tool_golden_gate_fidelity',
        student_tip='Tool #173 (Golden Gate Assembly Type IIS Overhang Fidelity Checker) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=174,
        name='Gibson Assembly Homologous Overlap Flank Designer',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 174: Gibson Assembly Homologous Overlap Flank Designer.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='insert_name', label='Insert Name', type='text', default='GFP_Reporter', help='Input for insert name'),
        ToolInputSpec(id='flank_len_bp', label='Flank Len Bp', type='number', default=25, help='Input for flank len bp'),
        ToolInputSpec(id='gc_content', label='Gc Content', type='number', default=52.0, help='Input for gc content')
    ],
        handler_name='tool_gibson_flank_designer',
        student_tip='Tool #174 (Gibson Assembly Homologous Overlap Flank Designer) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=175,
        name='Ribosome Binding Site (RBS) Translation Initiation Rate Calculator',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 175: Ribosome Binding Site (RBS) Translation Initiation Rate Calculator.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='rbs_sequence', label='Rbs Sequence', type='text', default='AGGAGGTAAATAAATG', help='Input for rbs sequence')
    ],
        handler_name='tool_rbs_calculator',
        student_tip='Tool #175 (Ribosome Binding Site (RBS) Translation Initiation Rate Calculator) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=176,
        name='Constitutive Promoter Library Relative Activity Predictor',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 176: Constitutive Promoter Library Relative Activity Predictor.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='promoter_seq', label='Promoter Seq', type='text', default='TTGACAGCTAGCTCAGTCCTAGGTATAATGCTAGC', help='Input for promoter seq')
    ],
        handler_name='tool_promoter_strength_predictor',
        student_tip='Tool #176 (Constitutive Promoter Library Relative Activity Predictor) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=177,
        name='Cell-Free Transcription-Translation (TX-TL) Kinetic Simulator',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 177: Cell-Free Transcription-Translation (TX-TL) Kinetic Simulator.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='dna_conc_nm', label='Dna Conc Nm', type='number', default=10.0, help='Input for dna conc nm'),
        ToolInputSpec(id='runtime_hours', label='Runtime Hours', type='number', default=6.0, help='Input for runtime hours')
    ],
        handler_name='tool_txtl_kinetic_simulator',
        student_tip='Tool #177 (Cell-Free Transcription-Translation (TX-TL) Kinetic Simulator) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=178,
        name='Flux Balance Analysis (FBA) Core Metabolic Solver',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 178: Flux Balance Analysis (FBA) Core Metabolic Solver.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='glucose_uptake_mmol_gdw_h', label='Glucose Uptake Mmol Gdw H', type='number', default=10.0, help='Input for glucose uptake mmol gdw h')
    ],
        handler_name='tool_fba_metabolic_solver',
        student_tip='Tool #178 (Flux Balance Analysis (FBA) Core Metabolic Solver) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=179,
        name='Synthetic Genetic Toggle Switch Bistability Simulator',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 179: Synthetic Genetic Toggle Switch Bistability Simulator.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='iptg_inducer_uM', label='Iptg Inducer Um', type='number', default=100.0, help='Input for iptg inducer uM'),
        ToolInputSpec(id='atc_inducer_ng_ml', label='Atc Inducer Ng Ml', type='number', default=0.0, help='Input for atc inducer ng ml')
    ],
        handler_name='tool_toggle_switch_simulator',
        student_tip='Tool #179 (Synthetic Genetic Toggle Switch Bistability Simulator) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=180,
        name='Repressilator Synthetic Three-Node Gene Oscillator',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 180: Repressilator Synthetic Three-Node Gene Oscillator.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='cycles', label='Cycles', type='number', default=4, help='Input for cycles')
    ],
        handler_name='tool_repressilator_simulator',
        student_tip='Tool #180 (Repressilator Synthetic Three-Node Gene Oscillator) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=181,
        name='Engineered Toxin-Antitoxin Kill-Switch Circuit Verifier',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 181: Engineered Toxin-Antitoxin Kill-Switch Circuit Verifier.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='toxin_status', label='Toxin Status', type='text', default='MazF Active', help='Input for toxin status'),
        ToolInputSpec(id='antitoxin_ratio', label='Antitoxin Ratio', type='number', default=0.2, help='Input for antitoxin ratio')
    ],
        handler_name='tool_toxin_antitoxin_killswitch',
        student_tip='Tool #181 (Engineered Toxin-Antitoxin Kill-Switch Circuit Verifier) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=182,
        name='Plasmid Vector Feature Boundary & Annular Coordinates Map',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 182: Plasmid Vector Feature Boundary & Annular Coordinates Map.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='plasmid_length_bp', label='Plasmid Length Bp', type='number', default=4361, help='Input for plasmid length bp')
    ],
        handler_name='tool_plasmid_map_generator',
        student_tip='Tool #182 (Plasmid Vector Feature Boundary & Annular Coordinates Map) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=183,
        name='Multi-Host Codon Harmonization & Rare-Codon Rhythm Tuner',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 183: Multi-Host Codon Harmonization & Rare-Codon Rhythm Tuner.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='ATGTTTGTTAAAGATGAAGTT', help='Input for sequence')
    ],
        handler_name='tool_codon_harmonization',
        student_tip='Tool #183 (Multi-Host Codon Harmonization & Rare-Codon Rhythm Tuner) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=184,
        name='Degenerate Oligo Mutagenesis Library Diversity Calculator',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 184: Degenerate Oligo Mutagenesis Library Diversity Calculator.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='scheme', label='Scheme', type='text', default='NNK', help='Input for scheme'),
        ToolInputSpec(id='num_codons', label='Num Codons', type='number', default=3, help='Input for num codons')
    ],
        handler_name='tool_degenerate_oligo_diversity',
        student_tip='Tool #184 (Degenerate Oligo Mutagenesis Library Diversity Calculator) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=185,
        name='BioBrick RFC-10 Restriction Site Compatibility Checker',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 185: BioBrick RFC-10 Restriction Site Compatibility Checker.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='textarea', default='GAATTCGCGGCCGCTCTAGAGTACTAGTAGCGGCCGCTCTGCAG', help='Input for sequence')
    ],
        handler_name='tool_biobrick_compatibility',
        student_tip='Tool #185 (BioBrick RFC-10 Restriction Site Compatibility Checker) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=186,
        name='Nucleic Acid Aptamer Stem-Loop Stability Evaluator',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 186: Nucleic Acid Aptamer Stem-Loop Stability Evaluator.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='GGGAGACAAGAAUAACGCUCAACGCUCAAGUUAUUU', help='Input for sequence')
    ],
        handler_name='tool_aptamer_stability_evaluator',
        student_tip='Tool #186 (Nucleic Acid Aptamer Stem-Loop Stability Evaluator) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=187,
        name='MAGE Lagging Strand Oligo Designer',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 187: MAGE Lagging Strand Oligo Designer.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='target_locus', label='Target Locus', type='text', default='TGCAGCCCGATCGATCGATCGATCAGGTAGT', help='Input for target locus'),
        ToolInputSpec(id='mismatch_bases', label='Mismatch Bases', type='number', default=2, help='Input for mismatch bases')
    ],
        handler_name='tool_mage_oligo_matcher',
        student_tip='Tool #187 (MAGE Lagging Strand Oligo Designer) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=188,
        name='Minimal Synthetic Genome Essential Gene Retention Index',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 188: Minimal Synthetic Genome Essential Gene Retention Index.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='total_genes', label='Total Genes', type='number', default=4288, help='Input for total genes'),
        ToolInputSpec(id='essential_pct', label='Essential Pct', type='number', default=11.0, help='Input for essential pct')
    ],
        handler_name='tool_minimal_genome_reducer',
        student_tip='Tool #188 (Minimal Synthetic Genome Essential Gene Retention Index) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=189,
        name='MoClo Modular Cloning Standard Transcription Unit Compatibility',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 189: MoClo Modular Cloning Standard Transcription Unit Compatibility.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='part_type', label='Part Type', type='text', default='Promoter (GGAG - TACT)', help='Input for part type'),
        ToolInputSpec(id='overhang_5p', label='Overhang 5P', type='text', default='GGAG', help='Input for overhang 5p'),
        ToolInputSpec(id='overhang_3p', label='Overhang 3P', type='text', default='TACT', help='Input for overhang 3p')
    ],
        handler_name='tool_moclo_syntax_checker',
        student_tip='Tool #189 (MoClo Modular Cloning Standard Transcription Unit Compatibility) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=190,
        name='Multi-Enzyme Pathway Stoichiometric Bottleneck Balancer',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 190: Multi-Enzyme Pathway Stoichiometric Bottleneck Balancer.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='enzyme_kcats', label='Enzyme Kcats', type='textarea', default='Enzyme1:450:0.12, Enzyme2:12:0.02, Enzyme3:180:0.45, Enzyme4:320:0.80', help='Input for enzyme kcats')
    ],
        handler_name='tool_pathway_bottleneck_balancer',
        student_tip='Tool #190 (Multi-Enzyme Pathway Stoichiometric Bottleneck Balancer) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=191,
        name='DNA Origami Staple Strand Scaffold Crossover Scheduler',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 191: DNA Origami Staple Strand Scaffold Crossover Scheduler.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='scaffold_length_bp', label='Scaffold Length Bp', type='number', default=7249, help='Input for scaffold length bp')
    ],
        handler_name='tool_dna_origami_staple_scheduler',
        student_tip='Tool #191 (DNA Origami Staple Strand Scaffold Crossover Scheduler) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=192,
        name='Amber Codon (UAG) Suppression Orthogonal tRNA Checker',
        domain='Synthetic Biology & Metabolic Engineering',
        category_id='synthetic',
        category_name='Synthetic Biology & Metabolic Engineering',
        description='Tool 192: Amber Codon (UAG) Suppression Orthogonal tRNA Checker.',
        console_page='71_Synthetic_Biology_Metabolic_Eng.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='ATGTTTTAGAAAGATTAGTAA', help='Input for sequence'),
        ToolInputSpec(id='trna_type', label='Trna Type', type='text', default='PylRS-tRNA_Pyl (Pyrrolysyl)', help='Input for trna type')
    ],
        handler_name='tool_amber_suppression_checker',
        student_tip='Tool #192 (Amber Codon (UAG) Suppression Orthogonal tRNA Checker) demonstrates critical applied computational techniques in Synthetic Biology & Metabolic Engineering.',
    ),
    ToolSpec(
        id=193,
        name='Hardy-Weinberg Equilibrium Chi-Square & Exact Test',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 193: Hardy-Weinberg Equilibrium Chi-Square & Exact Test.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='n_aa', label='N Aa', type='number', default=180, help='Input for n aa'),
        ToolInputSpec(id='n_ab', label='N Ab', type='number', default=240, help='Input for n ab'),
        ToolInputSpec(id='n_bb', label='N Bb', type='number', default=80, help='Input for n bb')
    ],
        handler_name='tool_hardy_weinberg_exact',
        student_tip='Tool #193 (Hardy-Weinberg Equilibrium Chi-Square & Exact Test) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=194,
        name="Tajima's D Neutrality Statistic & Selection Direction Evaluator",
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description="Tool 194: Tajima's D Neutrality Statistic & Selection Direction Evaluator.",
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='sample_size_n', label='Sample Size N', type='number', default=15, help='Input for sample size n'),
        ToolInputSpec(id='num_segregating_s', label='Num Segregating S', type='number', default=12, help='Input for num segregating s'),
        ToolInputSpec(id='pi_val', label='Pi Val', type='number', default=3.2, help='Input for pi val')
    ],
        handler_name='tool_tajimas_d_neutrality',
        student_tip="Tool #194 (Tajima's D Neutrality Statistic & Selection Direction Evaluator) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.",
    ),
    ToolSpec(
        id=195,
        name="Wright's Fixation Index (Fst) Multi-Subpopulation Estimator",
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description="Tool 195: Wright's Fixation Index (Fst) Multi-Subpopulation Estimator.",
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='pop_freqs', label='Pop Freqs', type='textarea', default='PopA:0.25:0.75, PopB:0.85:0.15, PopC:0.50:0.50', help='Input for pop freqs')
    ],
        handler_name='tool_fst_multilocus',
        student_tip="Tool #195 (Wright's Fixation Index (Fst) Multi-Subpopulation Estimator) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.",
    ),
    ToolSpec(
        id=196,
        name='Nucleotide Diversity (Pi) Pairwise Differences Per Site',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 196: Nucleotide Diversity (Pi) Pairwise Differences Per Site.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='sequences', label='Sequences', type='text', default='ATGCATGC, ATGCATGA, ATGGATGC, ATACATGC', help='Input for sequences')
    ],
        handler_name='tool_nucleotide_diversity_pi',
        student_tip='Tool #196 (Nucleotide Diversity (Pi) Pairwise Differences Per Site) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=197,
        name="Watterson's Theta (Theta-W) Finite Sites Mutation Rate Estimator",
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description="Tool 197: Watterson's Theta (Theta-W) Finite Sites Mutation Rate Estimator.",
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='num_segregating_sites', label='Num Segregating Sites', type='number', default=18, help='Input for num segregating sites'),
        ToolInputSpec(id='sample_size', label='Sample Size', type='number', default=20, help='Input for sample size'),
        ToolInputSpec(id='seq_length_bp', label='Seq Length Bp', type='number', default=1000, help='Input for seq length bp')
    ],
        handler_name='tool_wattersons_theta',
        student_tip="Tool #197 (Watterson's Theta (Theta-W) Finite Sites Mutation Rate Estimator) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.",
    ),
    ToolSpec(
        id=198,
        name="Linkage Disequilibrium Matrix (D, D', r²)",
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description="Tool 198: Linkage Disequilibrium Matrix (D, D', r²).",
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='p_ab', label='P Ab', type='number', default=0.35, help='Input for p ab'),
        ToolInputSpec(id='p_a', label='P A', type='number', default=0.5, help='Input for p a'),
        ToolInputSpec(id='p_b', label='P B', type='number', default=0.5, help='Input for p b')
    ],
        handler_name='tool_linkage_disequilibrium_matrix',
        student_tip="Tool #198 (Linkage Disequilibrium Matrix (D, D', r²)) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.",
    ),
    ToolSpec(
        id=199,
        name='Extended Haplotype Homozygosity (EHH) Selective Sweep Detector',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 199: Extended Haplotype Homozygosity (EHH) Selective Sweep Detector.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='decay_distances_kb', label='Decay Distances Kb', type='textarea', default='0:1.0, 20:0.85, 50:0.65, 100:0.42, 200:0.18, 500:0.04', help='Input for decay distances kb')
    ],
        handler_name='tool_ehh_selective_sweep',
        student_tip='Tool #199 (Extended Haplotype Homozygosity (EHH) Selective Sweep Detector) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=200,
        name="Kingman's Coalescent Tree & TMRCA Estimator",
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description="Tool 200: Kingman's Coalescent Tree & TMRCA Estimator.",
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='sample_size_n', label='Sample Size N', type='number', default=10, help='Input for sample size n'),
        ToolInputSpec(id='pop_size_ne', label='Pop Size Ne', type='number', default=10000, help='Input for pop size ne')
    ],
        handler_name='tool_coalescent_simulation',
        student_tip="Tool #200 (Kingman's Coalescent Tree & TMRCA Estimator) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.",
    ),
    ToolSpec(
        id=201,
        name='Inbreeding Coefficient (F) & Heterozygosity Deficit',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 201: Inbreeding Coefficient (F) & Heterozygosity Deficit.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='obs_heterozygotes', label='Obs Heterozygotes', type='number', default=35, help='Input for obs heterozygotes'),
        ToolInputSpec(id='exp_heterozygotes', label='Exp Heterozygotes', type='number', default=50, help='Input for exp heterozygotes')
    ],
        handler_name='tool_inbreeding_coefficient_f',
        student_tip='Tool #201 (Inbreeding Coefficient (F) & Heterozygosity Deficit) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=202,
        name='McDonald-Kreitman Test for Adaptive Protein Evolution',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 202: McDonald-Kreitman Test for Adaptive Protein Evolution.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='dn', label='Dn', type='number', default=24, help='Input for dn'),
        ToolInputSpec(id='ds', label='Ds', type='number', default=18, help='Input for ds'),
        ToolInputSpec(id='pn', label='Pn', type='number', default=8, help='Input for pn'),
        ToolInputSpec(id='ps', label='Ps', type='number', default=32, help='Input for ps')
    ],
        handler_name='tool_mcdonald_kreitman_test',
        student_tip='Tool #202 (McDonald-Kreitman Test for Adaptive Protein Evolution) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=203,
        name='Population Genotype Principal Component Analysis (PCA)',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 203: Population Genotype Principal Component Analysis (PCA).',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='sample_count', label='Sample Count', type='number', default=12, help='Input for sample count')
    ],
        handler_name='tool_genotype_pca',
        student_tip='Tool #203 (Population Genotype Principal Component Analysis (PCA)) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=204,
        name='Effective Population Size (Ne) Temporal Variance Estimator',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 204: Effective Population Size (Ne) Temporal Variance Estimator.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='temporal_freqs', label='Temporal Freqs', type='text', default='T0:0.42, T5:0.48, T10:0.56, T15:0.65', help='Input for temporal freqs')
    ],
        handler_name='tool_effective_pop_size_ne',
        student_tip='Tool #204 (Effective Population Size (Ne) Temporal Variance Estimator) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=205,
        name='Wright-Fisher Stochastic Genetic Drift Simulator',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 205: Wright-Fisher Stochastic Genetic Drift Simulator.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='initial_p', label='Initial P', type='number', default=0.5, help='Input for initial p'),
        ToolInputSpec(id='n_e', label='N E', type='number', default=50, help='Input for n e'),
        ToolInputSpec(id='generations', label='Generations', type='number', default=40, help='Input for generations')
    ],
        handler_name='tool_genetic_drift_wright_fisher',
        student_tip='Tool #205 (Wright-Fisher Stochastic Genetic Drift Simulator) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=206,
        name="Patterson's f3 / f4 Admixture Statistic Estimator",
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description="Tool 206: Patterson's f3 / f4 Admixture Statistic Estimator.",
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='f3_input', label='F3 Input', type='textarea', default='Target:French, Source1:Yoruba, Source2:Neanderthal, f3_Stat:-0.012', help='Input for f3 input')
    ],
        handler_name='tool_admixture_f_statistics',
        student_tip="Tool #206 (Patterson's f3 / f4 Admixture Statistic Estimator) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.",
    ),
    ToolSpec(
        id=207,
        name='Non-Synonymous to Synonymous Substitution Ratio (dN/dS)',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 207: Non-Synonymous to Synonymous Substitution Ratio (dN/dS).',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='nonsyn_muts', label='Nonsyn Muts', type='number', default=42, help='Input for nonsyn muts'),
        ToolInputSpec(id='syn_muts', label='Syn Muts', type='number', default=18, help='Input for syn muts'),
        ToolInputSpec(id='nonsyn_sites', label='Nonsyn Sites', type='number', default=700, help='Input for nonsyn sites'),
        ToolInputSpec(id='syn_sites', label='Syn Sites', type='number', default=300, help='Input for syn sites')
    ],
        handler_name='tool_dnds_kaks_ratio',
        student_tip='Tool #207 (Non-Synonymous to Synonymous Substitution Ratio (dN/dS)) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=208,
        name='Isolation by Distance (Mantel Test) Correlation',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 208: Isolation by Distance (Mantel Test) Correlation.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='n_points', label='N Points', type='number', default=10, help='Input for n points')
    ],
        handler_name='tool_isolation_by_distance_mantel',
        student_tip='Tool #208 (Isolation by Distance (Mantel Test) Correlation) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=209,
        name='Ewens-Watterson Neutral Allele Frequency Test',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 209: Ewens-Watterson Neutral Allele Frequency Test.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='allele_counts', label='Allele Counts', type='textarea', default='A1:45, A2:28, A3:12, A4:8, A5:4, A6:2, A7:1', help='Input for allele counts')
    ],
        handler_name='tool_ewens_watterson_neutrality',
        student_tip='Tool #209 (Ewens-Watterson Neutral Allele Frequency Test) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=210,
        name='Site Frequency Spectrum (SFS) Histogram Engine',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 210: Site Frequency Spectrum (SFS) Histogram Engine.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='max_k', label='Max K', type='number', default=10, help='Input for max k')
    ],
        handler_name='tool_site_frequency_spectrum_sfs',
        student_tip='Tool #210 (Site Frequency Spectrum (SFS) Histogram Engine) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=211,
        name="Patterson's D (ABBA-BABA) Archaic Introgression Test",
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description="Tool 211: Patterson's D (ABBA-BABA) Archaic Introgression Test.",
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='abba_count', label='Abba Count', type='number', default=1420, help='Input for abba count'),
        ToolInputSpec(id='baba_count', label='Baba Count', type='number', default=1150, help='Input for baba count')
    ],
        handler_name='tool_abba_baba_pattersons_d',
        student_tip="Tool #211 (Patterson's D (ABBA-BABA) Archaic Introgression Test) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.",
    ),
    ToolSpec(
        id=212,
        name='Molecular Evolutionary Clock Divergence Time Estimator',
        domain='Population Genetics & Evolutionary Dynamics',
        category_id='population',
        category_name='Population Genetics & Evolutionary Dynamics',
        description='Tool 212: Molecular Evolutionary Clock Divergence Time Estimator.',
        console_page='72_Population_Genetics_Evolution.py',
        inputs=[
        ToolInputSpec(id='substitutions_per_site', label='Substitutions Per Site', type='number', default=0.045, help='Input for substitutions per site'),
        ToolInputSpec(id='rate_per_site_per_year', label='Rate Per Site Per Year', type='number', default=1.2e-09, help='Input for rate per site per year')
    ],
        handler_name='tool_molecular_clock_divergence',
        student_tip='Tool #212 (Molecular Evolutionary Clock Divergence Time Estimator) demonstrates critical applied computational techniques in Population Genetics & Evolutionary Dynamics.',
    ),
    ToolSpec(
        id=213,
        name='NCBI Nucleotide (GenBank) Fetch & Accession Parser',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 213: NCBI Nucleotide (GenBank) Fetch & Accession Parser.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='accession_id', label='Accession Id', type='text', default='NC_005816', help='Input for accession id')
    ],
        handler_name='tool_ncbi_nucleotide_fetch',
        student_tip='Tool #213 (NCBI Nucleotide (GenBank) Fetch & Accession Parser) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=214,
        name='NCBI Protein (RefSeq) Fast Fetch & Sequence Inspector',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 214: NCBI Protein (RefSeq) Fast Fetch & Sequence Inspector.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='accession_id', label='Accession Id', type='text', default='NP_000537', help='Input for accession id')
    ],
        handler_name='tool_ncbi_protein_fetch',
        student_tip='Tool #214 (NCBI Protein (RefSeq) Fast Fetch & Sequence Inspector) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=215,
        name='NCBI Gene ID to Genomic Locus & Exon Coordinate Mapper',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 215: NCBI Gene ID to Genomic Locus & Exon Coordinate Mapper.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='gene_id', label='Gene Id', type='text', default='7157', help='Input for gene id')
    ],
        handler_name='tool_ncbi_gene_id_mapper',
        student_tip='Tool #215 (NCBI Gene ID to Genomic Locus & Exon Coordinate Mapper) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=216,
        name='NCBI Taxonomy Scientific Lineage & Cladistic Browser',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 216: NCBI Taxonomy Scientific Lineage & Cladistic Browser.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='species_name', label='Species Name', type='text', default='Homo sapiens', help='Input for species name')
    ],
        handler_name='tool_ncbi_taxonomy_browser',
        student_tip='Tool #216 (NCBI Taxonomy Scientific Lineage & Cladistic Browser) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=217,
        name='NCBI dbSNP Clinical & Minor Allele Frequency Query',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 217: NCBI dbSNP Clinical & Minor Allele Frequency Query.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='rsid', label='Rsid', type='text', default='rs80357906', help='Input for rsid')
    ],
        handler_name='tool_ncbi_dbsnp_lookup',
        student_tip='Tool #217 (NCBI dbSNP Clinical & Minor Allele Frequency Query) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=218,
        name='NCBI PubMed Literature Search & Abstract Retriever',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 218: NCBI PubMed Literature Search & Abstract Retriever.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='query_keyword', label='Query Keyword', type='text', default='CRISPR Cas9 cancer immunotherapy', help='Input for query keyword')
    ],
        handler_name='tool_ncbi_pubmed_search',
        student_tip='Tool #218 (NCBI PubMed Literature Search & Abstract Retriever) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=219,
        name='NCBI ClinVar Variant Assertion & Review Status',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 219: NCBI ClinVar Variant Assertion & Review Status.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='variant_id', label='Variant Id', type='text', default='VCV000012345', help='Input for variant id')
    ],
        handler_name='tool_ncbi_clinvar_lookup',
        student_tip='Tool #219 (NCBI ClinVar Variant Assertion & Review Status) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=220,
        name='Remote NCBI BLASTn Nucleotide Similarity Search',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 220: Remote NCBI BLASTn Nucleotide Similarity Search.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='query_seq', label='Query Seq', type='text', default='TGCACGTGCCCTGCTTCTCCA', help='Input for query seq')
    ],
        handler_name='tool_remote_blastn_search',
        student_tip='Tool #220 (Remote NCBI BLASTn Nucleotide Similarity Search) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=221,
        name='Remote NCBI BLASTp Protein Homology Search',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 221: Remote NCBI BLASTp Protein Homology Search.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='protein_seq', label='Protein Seq', type='text', default='MEEPQSDPSVEPPLSQETFSDLWKLLPEN', help='Input for protein seq')
    ],
        handler_name='tool_remote_blastp_search',
        student_tip='Tool #221 (Remote NCBI BLASTp Protein Homology Search) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=222,
        name='NCBI Gene Expression Omnibus (GEO) Meta-Profiler',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 222: NCBI Gene Expression Omnibus (GEO) Meta-Profiler.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='gse_accession', label='Gse Accession', type='text', default='GSE12345', help='Input for gse accession')
    ],
        handler_name='tool_ncbi_geo_dataset_fetch',
        student_tip='Tool #222 (NCBI Gene Expression Omnibus (GEO) Meta-Profiler) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=223,
        name='NCBI Sequence Read Archive (SRA) Run Inspector',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 223: NCBI Sequence Read Archive (SRA) Run Inspector.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='srr_accession', label='Srr Accession', type='text', default='SRR11412227', help='Input for srr accession')
    ],
        handler_name='tool_ncbi_sra_run_inspector',
        student_tip='Tool #223 (NCBI Sequence Read Archive (SRA) Run Inspector) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=224,
        name='NCBI MMDB Macromolecular 3D Structure Record Summarizer',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 224: NCBI MMDB Macromolecular 3D Structure Record Summarizer.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='pdb_id', label='Pdb Id', type='text', default='1TUP', help='Input for pdb id')
    ],
        handler_name='tool_ncbi_mmdb_structure_fetch',
        student_tip='Tool #224 (NCBI MMDB Macromolecular 3D Structure Record Summarizer) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=225,
        name='OMIM Morbid Map & Hereditary Disease Phenotype Linker',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 225: OMIM Morbid Map & Hereditary Disease Phenotype Linker.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='mim_number', label='Mim Number', type='text', default='191170', help='Input for mim number')
    ],
        handler_name='tool_omim_phenotype_linker',
        student_tip='Tool #225 (OMIM Morbid Map & Hereditary Disease Phenotype Linker) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=226,
        name='UniProtKB Protein Knowledgebase Functional Annotator',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 226: UniProtKB Protein Knowledgebase Functional Annotator.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='uniprot_id', label='Uniprot Id', type='text', default='P04637', help='Input for uniprot id')
    ],
        handler_name='tool_uniprot_functional_annotator',
        student_tip='Tool #226 (UniProtKB Protein Knowledgebase Functional Annotator) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=227,
        name='Ensembl Gene Symbol to Canonical ID Resolver',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 227: Ensembl Gene Symbol to Canonical ID Resolver.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='gene_symbol', label='Gene Symbol', type='text', default='EGFR', help='Input for gene symbol')
    ],
        handler_name='tool_ensembl_id_resolver',
        student_tip='Tool #227 (Ensembl Gene Symbol to Canonical ID Resolver) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=228,
        name='PubChem Chemical Compound CID Properties & SMILES Fetcher',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 228: PubChem Chemical Compound CID Properties & SMILES Fetcher.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='compound_query', label='Compound Query', type='text', default='Aspirin', help='Input for compound query')
    ],
        handler_name='tool_pubchem_compound_fetch',
        student_tip='Tool #228 (PubChem Chemical Compound CID Properties & SMILES Fetcher) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=229,
        name='Worldwide PDB (wwPDB) Quality Validation Metric Fetcher',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 229: Worldwide PDB (wwPDB) Quality Validation Metric Fetcher.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='pdb_id', label='Pdb Id', type='text', default='4HHB', help='Input for pdb id')
    ],
        handler_name='tool_wwpdb_validation_report',
        student_tip='Tool #229 (Worldwide PDB (wwPDB) Quality Validation Metric Fetcher) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=230,
        name='KEGG Pathway REST API Entry Extractor',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 230: KEGG Pathway REST API Entry Extractor.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='pathway_id', label='Pathway Id', type='text', default='hsa00010', help='Input for pathway id')
    ],
        handler_name='tool_kegg_rest_pathway_fetch',
        student_tip='Tool #230 (KEGG Pathway REST API Entry Extractor) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=231,
        name='Reactome Biological Pathway Hierarchy Event Inspector',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 231: Reactome Biological Pathway Hierarchy Event Inspector.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='pathway_id', label='Pathway Id', type='text', default='R-HSA-69278', help='Input for pathway id')
    ],
        handler_name='tool_reactome_pathway_hierarchy',
        student_tip='Tool #231 (Reactome Biological Pathway Hierarchy Event Inspector) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=232,
        name='STRING Protein-Protein Interaction Network Interactor Matcher',
        domain='NCBI & Global Bioinformatics APIs',
        category_id='ncbi',
        category_name='NCBI & Global Bioinformatics APIs',
        description='Tool 232: STRING Protein-Protein Interaction Network Interactor Matcher.',
        console_page='73_NCBI_and_Global_Bioinformatics_APIs.py',
        inputs=[
        ToolInputSpec(id='protein_name', label='Protein Name', type='text', default='TP53', help='Input for protein name')
    ],
        handler_name='tool_string_ppi_network_fetch',
        student_tip='Tool #232 (STRING Protein-Protein Interaction Network Interactor Matcher) demonstrates critical applied computational techniques in NCBI & Global Bioinformatics APIs.',
    ),
    ToolSpec(
        id=233,
        name='Dr. Titan Plain-Language Sequence Explainer',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 233: Dr. Titan Plain-Language Sequence Explainer.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='sequence', label='Sequence', type='text', default='ATGCGTAGTCTAGCTAGCTAG', help='Input for sequence'),
        ToolInputSpec(id='language', label='Language', type='text', default='English', help='Input for language')
    ],
        handler_name='tool_dr_titan_sequence_explainer',
        student_tip='Tool #233 (Dr. Titan Plain-Language Sequence Explainer) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=234,
        name='Dr. Titan Variant Pathogenicity Advisor',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 234: Dr. Titan Variant Pathogenicity Advisor.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='variant', label='Variant', type='text', default='BRAF:c.1799T>A:p.V600E', help='Input for variant')
    ],
        handler_name='tool_dr_titan_variant_pathogenicity',
        student_tip='Tool #234 (Dr. Titan Variant Pathogenicity Advisor) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=235,
        name='Dr. Titan Primer Troubleshooting Consultant',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 235: Dr. Titan Primer Troubleshooting Consultant.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='tm_forward', label='Tm Forward', type='number', default=60.5, help='Input for tm forward'),
        ToolInputSpec(id='tm_reverse', label='Tm Reverse', type='number', default=52.0, help='Input for tm reverse')
    ],
        handler_name='tool_dr_titan_primer_troubleshooter',
        student_tip='Tool #235 (Dr. Titan Primer Troubleshooting Consultant) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=236,
        name='Dr. Titan CRISPR gRNA Efficiency Auditor',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 236: Dr. Titan CRISPR gRNA Efficiency Auditor.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='pam', label='Pam', type='text', default='NGG', help='Input for pam'),
        ToolInputSpec(id='gc_content', label='Gc Content', type='number', default=55.0, help='Input for gc content')
    ],
        handler_name='tool_dr_titan_crispr_advisor',
        student_tip='Tool #236 (Dr. Titan CRISPR gRNA Efficiency Auditor) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=237,
        name='Dr. Titan PubMed Abstract 3-Bullet Synthesizer',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 237: Dr. Titan PubMed Abstract 3-Bullet Synthesizer.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='abstract_text', label='Abstract Text', type='textarea', default='Targeted genome editing using CRISPR-Cas9 has revolutionized molecular therapeutics. Here we show that base editing corrects sickle cell mutation in human hematopoietic stem cells with 80% efficiency and minimal indels.', help='Input for abstract text')
    ],
        handler_name='tool_dr_titan_pubmed_synthesizer',
        student_tip='Tool #237 (Dr. Titan PubMed Abstract 3-Bullet Synthesizer) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=238,
        name='Dr. Titan Step-by-Step Protocol Generator',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 238: Dr. Titan Step-by-Step Protocol Generator.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='assay_type', label='Assay Type', type='textarea', default='PCR Amplification (Phusion High-Fidelity)', help='Input for assay type')
    ],
        handler_name='tool_dr_titan_protocol_generator',
        student_tip='Tool #238 (Dr. Titan Step-by-Step Protocol Generator) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=239,
        name='Dr. Titan HGNC Gene Nomenclature Resolver',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 239: Dr. Titan HGNC Gene Nomenclature Resolver.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='gene_alias', label='Gene Alias', type='text', default='HER2', help='Input for gene alias')
    ],
        handler_name='tool_dr_titan_gene_nomenclature',
        student_tip='Tool #239 (Dr. Titan HGNC Gene Nomenclature Resolver) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=240,
        name='Dr. Titan Metabolic Pathway Flow Explainer',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 240: Dr. Titan Metabolic Pathway Flow Explainer.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='pathway_name', label='Pathway Name', type='text', default='Glycolysis', help='Input for pathway name')
    ],
        handler_name='tool_dr_titan_pathway_explainer',
        student_tip='Tool #240 (Dr. Titan Metabolic Pathway Flow Explainer) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=241,
        name='Dr. Titan Host Codon Optimization Strategist',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 241: Dr. Titan Host Codon Optimization Strategist.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='host_organism', label='Host Organism', type='text', default='Escherichia coli BL21(DE3)', help='Input for host organism')
    ],
        handler_name='tool_dr_titan_codon_strategist',
        student_tip='Tool #241 (Dr. Titan Host Codon Optimization Strategist) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=242,
        name='Dr. Titan PDB Structural Domain Interpreter',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 242: Dr. Titan PDB Structural Domain Interpreter.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='pdb_id', label='Pdb Id', type='text', default='1BNA', help='Input for pdb id')
    ],
        handler_name='tool_dr_titan_pdb_interpreter',
        student_tip='Tool #242 (Dr. Titan PDB Structural Domain Interpreter) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=243,
        name='Dr. Titan Bioinformatics Career Roadmap Guide',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 243: Dr. Titan Bioinformatics Career Roadmap Guide.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='target_role', label='Target Role', type='text', default='Computational Biologist', help='Input for target role')
    ],
        handler_name='tool_dr_titan_career_mentor',
        student_tip='Tool #243 (Dr. Titan Bioinformatics Career Roadmap Guide) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=244,
        name='Dr. Titan Laboratory Diagnostic Troubleshooter',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 244: Dr. Titan Laboratory Diagnostic Troubleshooter.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='symptom', label='Symptom', type='text', default='No PCR band on agarose gel', help='Input for symptom')
    ],
        handler_name='tool_dr_titan_lab_troubleshooter',
        student_tip='Tool #244 (Dr. Titan Laboratory Diagnostic Troubleshooter) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=245,
        name='Dr. Titan In-Silico Cloning & Restriction Problem Solver',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 245: Dr. Titan In-Silico Cloning & Restriction Problem Solver.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='enzymes', label='Enzymes', type='text', default='EcoRI + BamHI', help='Input for enzymes')
    ],
        handler_name='tool_dr_titan_cloning_solver',
        student_tip='Tool #245 (Dr. Titan In-Silico Cloning & Restriction Problem Solver) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=246,
        name='Dr. Titan Multi-Omics Data Synthesis & Hypothesis Generator',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 246: Dr. Titan Multi-Omics Data Synthesis & Hypothesis Generator.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='target_phenotype', label='Target Phenotype', type='text', default='Thermotolerant drought-resistant crop', help='Input for target phenotype')
    ],
        handler_name='tool_dr_titan_hypothesis_generator',
        student_tip='Tool #246 (Dr. Titan Multi-Omics Data Synthesis & Hypothesis Generator) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=247,
        name="Dr. Titan 'Explain Like I'm 5' Analogy Engine",
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description="Tool 247: Dr. Titan 'Explain Like I'm 5' Analogy Engine.",
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='concept', label='Concept', type='text', default='CRISPR-Cas9 Gene Editing', help='Input for concept')
    ],
        handler_name='tool_dr_titan_eli5_generator',
        student_tip="Tool #247 (Dr. Titan 'Explain Like I'm 5' Analogy Engine) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.",
    ),
    ToolSpec(
        id=248,
        name='Dr. Titan Single-Cell Cluster Marker Interpreter',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 248: Dr. Titan Single-Cell Cluster Marker Interpreter.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='markers', label='Markers', type='text', default='CD3D, CD4, IL7R, FOXP3', help='Input for markers')
    ],
        handler_name='tool_dr_titan_sc_rna_marker_interpreter',
        student_tip='Tool #248 (Dr. Titan Single-Cell Cluster Marker Interpreter) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=249,
        name='Dr. Titan Antimicrobial Resistance Mechanism Explainer',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 249: Dr. Titan Antimicrobial Resistance Mechanism Explainer.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='drug_class', label='Drug Class', type='text', default='Beta-Lactams (Penicillins & Carbapenems)', help='Input for drug class')
    ],
        handler_name='tool_dr_titan_amr_mechanism',
        student_tip='Tool #249 (Dr. Titan Antimicrobial Resistance Mechanism Explainer) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=250,
        name='Dr. Titan Vaccine Antigen Epitope Design Advisor',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 250: Dr. Titan Vaccine Antigen Epitope Design Advisor.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='protein_target', label='Protein Target', type='text', default='Viral Surface Spike Glycoprotein', help='Input for protein target')
    ],
        handler_name='tool_dr_titan_vaccine_epitope_advisor',
        student_tip='Tool #250 (Dr. Titan Vaccine Antigen Epitope Design Advisor) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=251,
        name='Dr. Titan Synthetic Biology Gene Circuit Design Checker',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 251: Dr. Titan Synthetic Biology Gene Circuit Design Checker.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='circuit_design', label='Circuit Design', type='text', default='NOT-Gate Inverter (TetR -> pTet -> GFP)', help='Input for circuit design')
    ],
        handler_name='tool_dr_titan_synthetic_circuit_checker',
        student_tip='Tool #251 (Dr. Titan Synthetic Biology Gene Circuit Design Checker) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=252,
        name='Dr. Titan Epigenetic Methylation & Histone Code Tutor',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 252: Dr. Titan Epigenetic Methylation & Histone Code Tutor.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='modification', label='Modification', type='textarea', default='H3K27me3 (Histone H3 Lysine 27 Trimethylation)', help='Input for modification')
    ],
        handler_name='tool_dr_titan_epigenetics_tutor',
        student_tip='Tool #252 (Dr. Titan Epigenetic Methylation & Histone Code Tutor) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=253,
        name='Dr. Titan Forensic DNA Fingerprinting Explainer',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 253: Dr. Titan Forensic DNA Fingerprinting Explainer.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='str_loci', label='Str Loci', type='textarea', default='D3S1358:15/16, vWA:17/18, FGA:21/22, D8S1179:13/14', help='Input for str loci')
    ],
        handler_name='tool_dr_titan_forensic_dna_explainer',
        student_tip='Tool #253 (Dr. Titan Forensic DNA Fingerprinting Explainer) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=254,
        name='Dr. Titan Metagenomic Dysbiosis & Probiotic Advisor',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 254: Dr. Titan Metagenomic Dysbiosis & Probiotic Advisor.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='fb_ratio', label='Fb Ratio', type='number', default=3.8, help='Input for fb ratio')
    ],
        handler_name='tool_dr_titan_gut_dysbiosis_advisor',
        student_tip='Tool #254 (Dr. Titan Metagenomic Dysbiosis & Probiotic Advisor) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=255,
        name='Dr. Titan Plant Breeding & Introgression Consultant',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 255: Dr. Titan Plant Breeding & Introgression Consultant.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='target_crop', label='Target Crop', type='text', default='Rice (Oryza sativa)', help='Input for target crop')
    ],
        handler_name='tool_dr_titan_plant_breeding_consultant',
        student_tip='Tool #255 (Dr. Titan Plant Breeding & Introgression Consultant) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=256,
        name='Dr. Titan Marine Metabarcode & eDNA Guide',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 256: Dr. Titan Marine Metabarcode & eDNA Guide.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='water_volume_liters', label='Water Volume Liters', type='number', default=2.0, help='Input for water volume liters')
    ],
        handler_name='tool_dr_titan_marine_edna_guide',
        student_tip='Tool #256 (Dr. Titan Marine Metabarcode & eDNA Guide) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=257,
        name='Dr. Titan Proteomics Mass-Spectrometry Charge & Peak Advisor',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 257: Dr. Titan Proteomics Mass-Spectrometry Charge & Peak Advisor.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='monoisotopic_mw', label='Monoisotopic Mw', type='number', default=1250.6, help='Input for monoisotopic mw')
    ],
        handler_name='tool_dr_titan_mass_spec_advisor',
        student_tip='Tool #257 (Dr. Titan Proteomics Mass-Spectrometry Charge & Peak Advisor) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=258,
        name='Dr. Titan NGS Sequencing Coverage Depth Estimator',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 258: Dr. Titan NGS Sequencing Coverage Depth Estimator.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='genome_size_mb', label='Genome Size Mb', type='number', default=3200.0, help='Input for genome size mb'),
        ToolInputSpec(id='desired_depth_x', label='Desired Depth X', type='number', default=30, help='Input for desired depth x')
    ],
        handler_name='tool_dr_titan_ngs_depth_estimator',
        student_tip='Tool #258 (Dr. Titan NGS Sequencing Coverage Depth Estimator) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=259,
        name='Dr. Titan Laboratory Reagent & Buffer Recipe Calculator',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 259: Dr. Titan Laboratory Reagent & Buffer Recipe Calculator.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='buffer_type', label='Buffer Type', type='text', default='50x TAE Buffer', help='Input for buffer type'),
        ToolInputSpec(id='final_volume_ml', label='Final Volume Ml', type='number', default=1000.0, help='Input for final volume ml')
    ],
        handler_name='tool_dr_titan_buffer_recipe_calculator',
        student_tip='Tool #259 (Dr. Titan Laboratory Reagent & Buffer Recipe Calculator) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
    ToolSpec(
        id=260,
        name='Dr. Titan Comprehensive Bio-Project Readiness Audit',
        domain='Dr. Titan AI & Bio-Copilot',
        category_id='dr_titan',
        category_name='Dr. Titan AI & Bio-Copilot',
        description='Tool 260: Dr. Titan Comprehensive Bio-Project Readiness Audit.',
        console_page='74_Dr_Titan_AI_Bio_Copilot.py',
        inputs=[
        ToolInputSpec(id='checks', label='Checks', type='textarea', default='Reagents:Passed, Primers:Validated, DNA_Integrity:Verified, Controls:Included', help='Input for checks')
    ],
        handler_name='tool_dr_titan_project_readiness_audit',
        student_tip='Tool #260 (Dr. Titan Comprehensive Bio-Project Readiness Audit) demonstrates critical applied computational techniques in Dr. Titan AI & Bio-Copilot.',
    ),
]

REGISTRY_BY_ID: Dict[int, ToolSpec] = {t.id: t for t in MASTER_REGISTRY}

REGISTRY_BY_CATEGORY: Dict[str, List[ToolSpec]] = {}
for t in MASTER_REGISTRY:
    REGISTRY_BY_CATEGORY.setdefault(t.category_id, []).append(t)


def get_all_tools() -> List[ToolSpec]:
    """Return all 260 registered tools."""
    return MASTER_REGISTRY


def get_tool_by_id(tool_id: int) -> Optional[ToolSpec]:
    """Look up a tool specification by integer ID."""
    return REGISTRY_BY_ID.get(tool_id)


def get_tools_by_category(category_id: str) -> List[ToolSpec]:
    """Get all tools belonging to a category slug."""
    return REGISTRY_BY_CATEGORY.get(category_id, [])


def search_tools(query: str = "", category_id: Optional[str] = None) -> List[ToolSpec]:
    """Search tools by name, description, or domain."""
    results = MASTER_REGISTRY
    if category_id and category_id != "all":
        results = [t for t in results if t.category_id == category_id]
    if query and query.strip():
        q = query.lower().strip()
        results = [
            t for t in results
            if q in t.name.lower() or q in t.description.lower() or q in t.domain.lower() or q in str(t.id)
        ]
    return results
