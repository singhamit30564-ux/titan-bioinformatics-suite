#	File Name	Description	
1	`1_01_DNA_RNA_Conversion.py`	DNA ↔ RNA transcription/back-transcription	
2	`1_02_RNA_Protein_Translation.py`	RNA → Protein with codon table	
3	`1_03_Reverse_Complement_Stats.py`	Reverse complement + full statistics	
4	`1_04_GC_Content_Melting_Temp.py`	GC% + Tm (NN + Wallace) + sliding window plot	
5	`1_05_Mutation_SNP_Detection.py`	Point mutations + Ti/Tv ratio	
6	`1_06_ORF_Finder.py`	Open reading frames + longest ORFs	
7	`1_07_Motif_Pattern_Finder.py`	Pattern search with position highlighting	
8	`1_08_Restriction_Enzyme_Cutter.py`	10 common enzymes + cut frequency chart	
9	`1_09_Codon_Usage_Frequency.py`	Codon counts + frequency chart	
10	`1_10_Hamming_Edit_Distance.py`	Hamming + Levenshtein distance	
11	`1_11_Nucleotide_Frequency_Entropy.py`	Shannon entropy + composition pie chart	
12	`1_12_Central_Dogma_Visualizer.py`	DNA → RNA → Protein step-by-step	
#	File Name	Description	
13	`2_01_Molecular_Weight_Calculator.py`	DNA/RNA/Protein MW in Da and kDa	
14	`2_02_Protein_Isoelectric_Point.py`	pI estimation from acidic/basic residues	
15	`2_03_Hydropathy_Plot_KyteDoolittle.py`	Sliding window hydropathy + TM prediction	
16	`2_04_Alpha_Helix_Beta_Sheet_Predictor.py`	Chou-Fasman propensity prediction	
17	`2_05_Protein_Secondary_Structure.py`	H/E/T/C prediction with colored bars	
18	`2_06_Protein_Domain_Search.py`	Regex motif detection	
19	`2_07_Reverse_Translation.py`	Protein → possible DNA	
20	`2_08_Codon_Optimization_Expression.py`	Optimize for E.coli/Yeast/Human/Mouse	
21	`2_09_Amino_Acid_Property_Analyzer.py`	Charge, polarity, size per residue	
22	`2_10_Disulfide_Bond_Predictor.py`	Cysteine pair bond probability	
23	`2_11_Signal_Peptide_Predictor.py`	N-terminal signal peptide detection	
24	`2_12_DNA_to_ASCII_Art_Generator.py`	Convert DNA to text patterns	
#	File Name	Description	
25	`3_01_FASTA_FASTQ_Parser_QC.py`	File upload + sequence stats	
26	`3_02_Kmer_Frequency.py`	K-mer counting + bar chart	
27	`3_03_Ngrams_Analysis.py`	N-gram patterns + over/under-representation	
28	`3_04_CpG_Island_Detector.py`	Sliding window + O/E ratio	
29	`3_05_Repetitive_Elements_Finder.py`	Tandem repeats + copy number	
30	`3_06_Chaos_Game_Representation.py`	CGR plot	
31	`3_07_DNA_Shape_Analysis.py`	Minor groove + propeller twist	
32	`3_08_Genome_GC_Skew_Plot.py`	(G-C)/(G+C) sliding window	
33	`3_09_VCF_Variant_Viewer.py`	Parse VCF files	
34	`3_10_Read_Quality_Control.py`	Per-base quality scores	
35	`3_11_Gene_Ontology_GO_Enrichment.py`	GO term counter	
36	`3_12_KEGG_Pathway_Mapper.py`	Pathway ID lookup	
#	File Name	Description	
37	`4_01_Pairwise_Alignment.py`	Global/Local/Overlap	
38	`4_02_Local_Alignment_SmithWaterman.py`	Best local alignment	
39	`4_03_Global_Alignment_NeedlemanWunsch.py`	End-to-end alignment	
40	`4_04_Overlap_Alignment.py`	Sequence overlap detection	
41	`4_05_Multiple_Sequence_Alignment_MSA.py`	Simple MSA + conservation plot	
42	`4_06_MSA_ClustalW_Style.py`	ClustalW formatted output	
43	`4_07_Phylogenetic_Tree_Builder.py`	UPGMA dendrogram	
44	`4_08_Distance_Matrix_Calculator.py`	p-distance matrix + heatmap	
45	`4_09_Sequence_Logo_Generator.py`	Position-specific frequency chart	
46	`4_10_Homology_Search.py`	Local similarity search	
47	`4_11_Dot_Plot_Similarity.py`	Matrix dot plot	
48	`4_12_Consensus_Sequence_Generator.py`	Majority-rule consensus	
#	File Name	Description	
49	`5_01_CRISPR_Cas9_gRNA_Designer.py`	PAM search + gRNA matching	
50	`5_02_Primer_Design_Tm_GC_Hairpin.py`	Forward/reverse primers	
51	`5_03_PCR_Primer_Product_Length.py`	Custom positions + product length	
52	`5_04_Oligo_Tm_Annealing_Temp.py`	Multiple Tm methods	
53	`5_05_DNA_Melting_Curve_Simulation.py`	Sigmoid melting curve	
54	`5_06_SNP_Detection_Frequency.py`	SNP finding + frequency	
55	`5_07_InDel_Detection.py`	Insertion/deletion via gaps	
56	`5_08_BLAST_Local_Search_Mock.py`	Exact match search	
57	`5_09_Full_Pipeline_DNA_RNA_Protein_Graph.py`	4-panel dashboard	
58	`5_10_Bio_Formulas_CheatSheet.py`	Reference formulas	
59	`5_11_User_History_Data_Export.py`	Session history + export	
60	`5_12_Admin_Settings_Dashboard.py`	Theme + settings + about	
#	File Name	Description	NCBI API Used	
61	`6_01_NCBI_BLAST_Search.py`	Search NCBI BLAST against nr/nt database	`Bio.Blast.NCBIWWW`	
62	`6_02_NCBI_Gene_Fetch.py`	Fetch gene sequences by Gene ID	`Entrez.efetch`	
63	`6_03_NCBI_PubMed_Search.py`	Search scientific papers by keyword	`Entrez.esearch` + `esummary`	
64	`6_04_NCBI_Taxonomy_Lookup.py`	Get taxonomy lineage for any species	`Entrez.efetch` (taxonomy)	
65	`6_05_NCBI_SNP_Lookup.py`	Look up SNP details by rsID	`Entrez.efetch` (snp)	
### 🌾 **CATEGORY 8: AGRICULTURE BIOINFORMATICS (15 Tools)**
*Focus: Crop improvement, soil health, aur disease resistance.*

1. **Crop Disease Resistance (R-Gene) Finder**
2. **Drought Tolerance Marker (SSR/SNP) Analyzer**
3. **Soil Microbiome Diversity Plotter (16S rRNA)**
4. **Nitrogen Fixation Gene (nifH) Identifier**
5. **Pesticide/Herbicide Resistance Mutation Detector**
6. **Photosynthesis Efficiency Gene Analyzer (RuBisCO)**
7. **Seed Storage Protein Profiler**
8. **Plant Transcription Factor (TF) Family Classifier**
9. **GMO (Transgene) Sequence Detector**
10. **Pollen Allergen Protein Predictor**
11. **Post-Harvest Ripening Gene Tracker (Ethylene pathway)**
12. **Phytophthora (Pathogen) Effector Gene Matcher**
13. **Crop Phylogenetic Tree Builder (Variety tracing)**
14. **Plant Promoter Motif (Cis-element) Finder**
15. **Yield Trait GWAS Basic Visualizer**
### 🌊 **CATEGORY 9: MARINE BIOINFORMATICS (15 Tools)**
*Focus: Ocean health, extremophiles, aur marine ecology.*

1. **Marine Metagenome Binner (Basic)**
2. **Coral Bleaching Stress Gene Analyzer**
3. **Deep-Sea Extremophile Protein Predictor (Thermostable)**
4. **Marine Bioluminescence Gene (Luciferase) Finder**
5. **Fish Stock Population Genetics Analyzer (Fst, Heterozygosity)**
6. **Microplastic Ingestion DNA Barcode Matcher**
7. **Algal Bloom Toxin Gene Detector (Cyanotoxins)**
8. **Marine Antibiotic Resistance Gene (ARG) Scanner**
9. **Sponge Secondary Metabolite Pathway Predictor**
10. **Salinity Adaptation Gene Expression Simulator**
11. **Marine Viral Phage Host Predictor**
12. **Ocean Acidification Calcification Gene Tracker**
13. **Marine Invasive Species eDNA Detector**
14. **Fish Sex-Determination Gene Marker Analyzer**
15. **Marine Food Web Trophic Level DNA Analyzer**###
 🌐 **CATEGORY 10: NCBI API SUITE (15 Real-World Database Tools)**
*Focus: Direct connection to the world's largest biological databases.*

1. **NCBI Nucleotide Search & Fetcher** (Entrez API)
2. **NCBI Protein Sequence Fetcher** (Entrez API)
3. **NCBI Gene ID to Sequence Mapper** (Entrez API)
4. **NCBI Taxonomy Lineage Browser** (Species evolution tree)
5. **NCBI 3D Structure (MMDB) Viewer** (Protein structures)
6. **NCBI PubMed Literature Search** (Research papers by keyword)
7. **NCBI ClinVar Variant Fetcher** (Disease mutations)
8. **NCBI dbSNP (rsID) Lookup** (Single nucleotide polymorphisms)
9. **NCBI BLASTn Search** (DNA vs DNA database)
10. **NCBI BLASTp Search** (Protein vs Protein database)
11. **NCBI BLASTx Search** (Translated DNA vs Protein)
12. **NCBI tBLASTn Search** (Protein vs Translated DNA)
13. **NCBI GEO Data Fetcher** (Gene expression datasets)
14. **NCBI SRA Metadata Extractor** (Next-Gen Sequencing runs)
15. **NCBI OMIM Disease-Gene Linker** (Medical genetics)
### 🤖 **CATEGORY 11: AI & AUTOMATION SUITE (15 Gemini-Powered Tools)**
*Focus: Making complex biology easy, fast, and intelligent.*

1. **Dr. Titan: Sequence Explainer** (Hindi/English mein DNA/RNA ka matlab samjhaye)
2. **Protein Function Predictor** (AI based on amino acid properties)
3. **Mutation Pathogenicity Scorer** (AI predicts if a mutation is harmful)
4. **Primer Design Optimizer** (AI suggests best primer pairs)
5. **CRISPR gRNA Efficiency Predictor** (AI scores cut efficiency)
6. **Literature Review Summarizer** (PubMed abstracts ko 1 page mein summarize kare)
7. **Lab Protocol Generator** (AI writes step-by-step PCR/Cloning protocol)
8. **Gene Nomenclature Resolver** (Confused by gene names? AI finds the official symbol)
9. **Biological Pathway Explainer** (AI text-to-diagram for KEGG pathways)
10. **Codon Optimization Recommender** (AI suggests best codons for E.coli/Human expression)
11. **3D Protein Structure Explainer** (AI explains what a PDB file means)
12. **Bioinformatics Career/Course Recommender** (AI guides students)
13. **Lab Error Troubleshooter** ("Mera PCR fail ho gaya, kyun?" - AI answers)
14. **Research Hypothesis Generator** (AI suggests new experiment ideas based on data)
15. **"Explain Like I'm 5" (ELI5) Concept Generator** (Complex biology to simple analogies)
