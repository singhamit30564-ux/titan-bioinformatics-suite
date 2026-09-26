"""Dr. Titan AI Student Tutor & Interactive Educational Teaching Assistant.

Designed specifically to help and teach students:
- Step-by-step concept explanations with real-world analogies (ELI5).
- Multilingual instruction: English, Hindi, and Hinglish.
- Interactive student quizzes with explanations and instant feedback.
- Python & Biopython code walk-throughs for young bioinformaticians.
- Lab experimental guidance and troubleshooting.
"""
from __future__ import annotations

from typing import Dict, Any
import pandas as pd
import plotly.express as px

from titan_tools.common import (
    ToolResult,
    titan_plot_layout,
    TITAN_GOLD,
    TITAN_TEAL,
    TITAN_CORAL,
    TITAN_BLUE,
    TITAN_PURPLE,
)

# Rich student knowledge base covering foundational to advanced topics
STUDENT_TOPICS: Dict[str, Dict[str, Any]] = {
    "Central Dogma": {
        "title": "Central Dogma of Molecular Biology",
        "analogy": "The Central Dogma is like a Master Kitchen! DNA is the precious Master Recipe Book kept safely in the library office (the nucleus). You cannot take the master book out, so RNA Polymerase creates a photocopied recipe sheet (mRNA = Transcription). The recipe sheet travels to the kitchen counter (Ribosome in the cytoplasm), where the chef reads the recipe in groups of 3 letters (codons) and picks up matching spice packets (tRNA carrying amino acids = Translation) to cook a delicious protein dish!",
        "key_points": [
            "DNA -> RNA is Transcription (carried out by RNA Polymerase).",
            "RNA -> Protein is Translation (carried out by Ribosomes & tRNA).",
            "DNA uses Thymine (T); RNA replaces it with Uracil (U).",
            "Codons are triplets of nucleotides; 64 possible codons code for 20 standard amino acids + 3 stop codons.",
            "Replication makes a copy of DNA before cell division (DNA Polymerase).",
            "Reverse Transcription (RNA -> DNA) happens in retroviruses like HIV and SARS-CoV-2 testing (RT-qPCR) using Reverse Transcriptase."
        ],
        "quiz": [
            {
                "q": "Which enzyme is responsible for transcribing DNA into messenger RNA (mRNA)?",
                "options": ["A) DNA Polymerase", "B) RNA Polymerase", "C) Ribosome", "D) DNA Ligase"],
                "correct": "B",
                "explanation": "RNA Polymerase binds to the gene promoter and synthesizes complementary mRNA from the DNA template strand."
            },
            {
                "q": "What base replaces Thymine (T) in RNA molecules?",
                "options": ["A) Guanine (G)", "B) Cytosine (C)", "C) Uracil (U)", "D) Adenine (A)"],
                "correct": "C",
                "explanation": "Uracil lacks a methyl group compared to Thymine and pairs with Adenine in RNA."
            }
        ],
        "hinglish": "Central Dogma biological information ka one-way highway hai: DNA se RNA banta hai (Transcription) aur RNA se Protein (Translation). DNA nucleus ke andar safe rehta hai jaise original document, aur mRNA uski photocopy bankar ribosome ke paas jata hai protein banane!",
        "hindi": "आणविक जीव विज्ञान का केंद्रीय सिद्धांत (Central Dogma) बताता है कि आनुवंशिक जानकारी DNA से RNA (प्रतिलेखन/Transcription) और फिर RNA से प्रोटीन (अनुवाद/Translation) में प्रवाहित होती है।"
    },
    "DNA vs RNA": {
        "title": "DNA vs. RNA — The Two Genetic Informational Polymers",
        "analogy": "DNA is like an archival hard drive (built for 100-year permanent storage, double-stranded for stability, uses deoxyribose). RNA is like a temporary flash drive or sticky note (flexible, single-stranded, chemically active, uses ribose with a 2'-OH group that makes it more reactive, easily degraded once the job is done).",
        "key_points": [
            "Sugar: DNA has 2'-deoxyribose (missing one oxygen atom); RNA has ribose (has 2'-OH).",
            "Bases: DNA uses A, T, G, C; RNA uses A, U, G, C.",
            "Strandedness: DNA is usually double-stranded (B-form helix); RNA is mostly single-stranded but folds into complex hairpins and tertiary structures.",
            "Function: DNA is long-term genomic storage; RNA functions as mRNA (messenger), tRNA (transfer), rRNA (catalytic ribozyme), miRNA/siRNA (regulation)."
        ],
        "quiz": [
            {
                "q": "Why is RNA generally less chemically stable than DNA in aqueous solution?",
                "options": ["A) Uracil degrades faster", "B) The 2'-hydroxyl (-OH) group on ribose promotes alkaline hydrolysis", "C) RNA has no hydrogen bonds", "D) Single strands are impossible to maintain"],
                "correct": "B",
                "explanation": "The 2'-OH group on ribose acts as an internal nucleophile under alkaline conditions, cleaving the phosphodiester backbone."
            }
        ],
        "hinglish": "DNA permanent hard disk hai jisme 2'-deoxyribose hota hai (oxygen missing, isliye super stable). RNA temporary RAM ya sticky note hai jisme 2'-OH hota hai jo ise reactive aur temporary banata hai.",
        "hindi": "DNA और RNA में मुख्य अंतर शर्करा (डीऑक्सीराइबोज बनाम राइबोज) और थाइमिन के स्थान पर यूरेसिल का होना है।"
    },
    "CRISPR-Cas9": {
        "title": "CRISPR-Cas9 Gene Editing",
        "analogy": "CRISPR-Cas9 is molecular GPS + surgical scissors! The single guide RNA (sgRNA) is the GPS tracking system programmed with a 20-letter sequence coordinate. It searches 3 billion letters of genomic DNA. When it finds the exact target right next to a PAM sequence (NGG), the Cas9 protein acts as sharp scissors, cutting both strands of DNA. The cell then tries to repair the cut, allowing scientists to disable a broken gene or paste in a healthy correction!",
        "key_points": [
            "Originally discovered as a bacterial adaptive immune system against bacteriophages.",
            "Components: Cas9 endonuclease protein + sgRNA (crRNA + tracrRNA chimera).",
            "Targeting requirement: 20-nt guide matching DNA sequence immediately 5' of a Protospacer Adjacent Motif (PAM: 5'-NGG-3' for SpCas9).",
            "Repair pathways: Non-Homologous End Joining (NHEJ, error-prone knockouts) or Homology-Directed Repair (HDR, precise edits with donor template)."
        ],
        "quiz": [
            {
                "q": "What is the critical 3-nucleotide motif required immediately downstream of the target sequence for Streptococcus pyogenes Cas9?",
                "options": ["A) TATA box", "B) PAM sequence (5'-NGG-3')", "C) Poly-A signal", "D) Shine-Dalgarno sequence"],
                "correct": "B",
                "explanation": "SpCas9 strictly requires a 5'-NGG-3' PAM motif to initiate DNA unwinding and target strand interrogation."
            }
        ],
        "hinglish": "CRISPR-Cas9 ek molecular GPS scissors ki tarah hai. Guide RNA (sgRNA) target DNA dhoondhta hai aur Cas9 protein wahan double-strand break karta hai taaki hum disease-causing mutations theek kar sakein!",
        "hindi": "CRISPR-Cas9 एक क्रांतिकारी जीन-संपादन उपकरण है, जिसमें गाइड RNA लक्ष्य DNA को खोजता है और Cas9 एंजाइम उसे सटीक रूप से काटता है।"
    },
    "PCR & Primer Design": {
        "title": "Polymerase Chain Reaction (PCR)",
        "analogy": "PCR is the biological photocopying machine! Starting with just one single microscopic DNA molecule, PCR doubles the copies in each thermal cycle (1 -> 2 -> 4 -> 8 -> 16... after 30 cycles, you have over 1 billion identical copies!). The thermal cycler heats up to 95°C to melt DNA strands apart, cools to ~55-60°C so forward and reverse primers can anneal, and warms to 72°C so heat-stable Taq polymerase can build the new strands.",
        "key_points": [
            "Three temperature phases: Denaturation (94-95°C), Annealing (50-65°C), Extension (72°C for Taq).",
            "Primers: Short single-stranded oligos (18-24 nt) designed complementary to flanking regions on opposing strands.",
            "Melting Temperature (Tm): Temperature at which 50% of primer-template duplex is melted. Forward and reverse primers should have Tm within 1-2°C of each other.",
            "GC Content: Optimal 40-60% with a GC clamp at the 3' end (1-2 G/C bases) to anchor binding.",
            "Exponential amplification formula: Amplified copies = N0 * 2^n (where n is cycle count)."
        ],
        "quiz": [
            {
                "q": "Why is DNA polymerase from Thermus aquaticus (Taq) used in standard PCR instead of human DNA polymerase?",
                "options": ["A) It is cheaper to purify", "B) It survives the repeated 95°C denaturation temperatures without denaturing", "C) It produces fewer errors", "D) It requires no magnesium cofactor"],
                "correct": "B",
                "explanation": "Taq polymerase is thermostable because it originates from a hot-spring bacterium, allowing it to withstand repeated 95°C heating steps without losing enzymatic activity."
            }
        ],
        "hinglish": "PCR ek biological xerox machine hai. 3 steps hote hain: 1) Denaturation (95°C pe strands alag hoti hain), 2) Annealing (55-60°C pe primers bind hote hain), 3) Extension (72°C pe Taq polymerase new strand banata hai). 30 cycles me 1 billion copies ban jaati hain!",
        "hindi": "PCR (पॉलीमरेज़ चेन रिएक्शन) आणविक जीव विज्ञान की एक तकनीक है जिसका उपयोग DNA के विशिष्ट खंड की अरबों प्रतियां बनाने के लिए किया जाता है।"
    },
    "BLAST & Alignment": {
        "title": "BLAST & Sequence Alignment",
        "analogy": "Imagine you found an ancient torn book page in the forest and wanted to know which book in the world library it came from. Comparing letter-by-letter against every book in the world would take years! BLAST is like an intelligent search engine: it first breaks your snippet into short 'words' (k-mers of length 11 for DNA or 3 for protein), looks up indexed locations in the database instantly, and only extends alignments where there is a hot match hit!",
        "key_points": [
            "BLAST = Basic Local Alignment Search Tool (Altschul et al., 1990).",
            "Heuristic algorithm: Much faster than exact Smith-Waterman dynamic programming with minimal loss in sensitivity.",
            "E-value (Expect value): Number of hits expected to be found by pure random chance in a database of that size. Lower E-value (e.g. 1e-50 or 0.0) means higher statistical significance!",
            "Scoring matrices for proteins: BLOSUM62 (default, for moderately divergent proteins), PAM250 (for distant homologs).",
            "BLAST flavors: BLASTn (DNA vs DNA), BLASTp (protein vs protein), BLASTx (translated DNA vs protein), tBLASTn (protein vs translated DNA)."
        ],
        "quiz": [
            {
                "q": "What does a very low BLAST E-value (e.g., 1e-45) indicate about a sequence match?",
                "options": ["A) The match is likely a random artifact", "B) The alignment is extremely statistically significant and unlikely to occur by chance", "C) The query sequence is corrupted", "D) The alignment has zero percent identity"],
                "correct": "B",
                "explanation": "The E-value represents the number of false-positive alignments expected by chance; an E-value near 0 confirms genuine homology."
            }
        ],
        "hinglish": "BLAST Google search engine ki tarah hai genetic sequences ke liye! Ye exact dynamic programming ke bajaye smart heuristic k-mer seeds use karta hai taaki billions of bases me se seconds me matching homologs dhoondh sake. E-value jitna chhota hoga (jaise 1e-30), match utna hi strong aur real hoga!",
        "hindi": "BLAST एक अत्यधिक तेज़ खोज एल्गोरिदम है जो अनुक्रमों के बीच स्थानीय समानता के क्षेत्रों को खोजने के लिए डेटाबेस की खोज करता है।"
    },
    "Protein Structure & AlphaFold": {
        "title": "Protein Folding, Structure & AlphaFold",
        "analogy": "Think of a protein like an intricate origami sculpture made from a 1D strip of paper! The primary sequence (amino acid chain) contains the chemical instructions. Hydrophobic (water-fearing) amino acids curl up tightly into the core, while hydrophilic (water-loving) and charged amino acids stay on the outside facing the cellular water. AlphaFold uses deep neural networks (evoformers + structural modules) trained on all known PDB structures and evolutionary multiple sequence alignments (MSAs) to predict 3D atomic coordinates directly from 1D sequence in seconds!",
        "key_points": [
            "Four levels of protein structure: Primary (amino acid sequence), Secondary (alpha helices & beta sheets via backbone H-bonds), Tertiary (full 3D monomer fold with side-chain interactions), Quaternary (multi-subunit complexes like hemoglobin).",
            "Levinthal's Paradox: A 100-residue protein has ~10^47 possible conformations; random sampling would take longer than the age of the universe, yet proteins fold in milliseconds guided by free energy funnels.",
            "pLDDT score in AlphaFold: Confidence metric per residue from 0 to 100. >90 = very high confidence, 70-90 = confident backbone, <50 = intrinsically disordered region (IDR)."
        ],
        "quiz": [
            {
                "q": "In an AlphaFold structural model, what does a residue pLDDT score below 50 typically indicate?",
                "options": ["A) A tightly packed alpha helix", "B) A crystallographic artifact", "C) An intrinsically disordered, flexible, or unstructured region", "D) A disulfide bridge"],
                "correct": "C",
                "explanation": "Residues with pLDDT < 50 often correspond to intrinsically disordered proteins/regions (IDRs) that lack fixed 3D structures in isolation."
            }
        ],
        "hinglish": "Protein ek origami sculpture jaisa hai jo amino acids ki ladi se fold hota hai. AlphaFold Deep Learning AI use karke 1D amino acid sequence se accurate 3D structure predict karta hai. pLDDT score 90+ ho toh structure super accurate hai, aur <50 ho toh wo region flexible ya intrinsically disordered hai!",
        "hindi": "प्रोटीन संरचना 1D अमीनो एसिड श्रृंखला से जटिल 3D आकार में बदलती है। AlphaFold AI ने इस 50 साल पुरानी जैविक समस्या को हल करने में अभूतपूर्व प्रगति की है।"
    }
}


def tool_dr_titan_ai_student_tutor(
    topic: str = "Central Dogma",
    mode: str = "Teach Concept (ELI5 + Story)",
    language: str = "English",
    custom_question: str = "How do ribosomes read mRNA?"
) -> ToolResult:
    """Interactive AI Student Tutor & Educational Mentor."""
    # Find matching topic or closest fallback
    matched_key = None
    for k in STUDENT_TOPICS:
        if k.lower() in topic.lower() or topic.lower() in k.lower():
            matched_key = k
            break
    if not matched_key:
        matched_key = "Central Dogma"

    data = STUDENT_TOPICS[matched_key]
    title = f"🎓 Dr. Titan Student Tutor: {data['title']}"

    summary_text = (
        f"Lesson generated for topic '{data['title']}' in {language} "
        f"under '{mode}' mode. Designed for students and young researchers."
    )

    # Explanation based on language
    if language == "Hindi":
        explanation = f"### 📖 अवधारणा समझें (Concept Explanation)\n\n{data['hindi']}\n\n**सरल रूपक (Analogy):**\n{data['analogy']}"
    elif language == "Hinglish":
        explanation = f"### 📖 Simple Hinglish Explanation\n\n{data['hinglish']}\n\n**Easy Analogy:**\n{data['analogy']}"
    else:
        explanation = f"### 📖 Concept Explanation\n\n{data['analogy']}"

    key_bullets = "\n".join([f"- {pt}" for pt in data["key_points"]])

    # Quizzes
    quiz_items = []
    for q in data["quiz"]:
        quiz_items.append({
            "Question": q["q"],
            "Options": " | ".join(q["options"]),
            "Correct_Answer": q["correct"],
            "Scientific_Explanation": q["explanation"]
        })
    quiz_df = pd.DataFrame(quiz_items)

    # Custom question response if provided
    custom_ans = ""
    if custom_question and custom_question.strip():
        q_lower = custom_question.lower()
        if "ribosome" in q_lower or "read" in q_lower or "codon" in q_lower:
            custom_ans = (
                f"**Student Question:** *\"{custom_question}\"*\n\n"
                "**Dr. Titan AI Response:** Great question! Ribosomes have two subunits (large and small). "
                "The small subunit binds mRNA, and the ribosome steps along the message 3 bases at a time (one codon). "
                "Inside the ribosome, there are three active sites: A (Aminoacyl - where the new matching tRNA enters), "
                "P (Peptidyl - where the growing peptide chain is attached), and E (Exit - where the spent empty tRNA leaves). "
                "The ribosome's rRNA acts as a ribozyme (peptidyl transferase) to stitch amino acids together with peptide bonds!"
            )
        elif "crispr" in q_lower or "cas9" in q_lower:
            custom_ans = (
                f"**Student Question:** *\"{custom_question}\"*\n\n"
                "**Dr. Titan AI Response:** CRISPR works like search-and-replace in a text document! "
                "The guide RNA (sgRNA) contains 20 letters that match the gene you want to fix. "
                "When Cas9 finds those letters adjacent to a PAM site ('NGG'), it makes a clean cut. "
                "Scientists can provide a repair template with healthy DNA so the cell copies the correct sequence!"
            )
        elif "career" in q_lower or "learn" in q_lower or "start" in q_lower or "road" in q_lower:
            custom_ans = (
                f"**Student Question:** *\"{custom_question}\"*\n\n"
                "**Dr. Titan AI Response:** Here is the golden 4-step roadmap for student bioinformaticians:\n"
                "1. **Learn Python Fundamentals:** Variables, loops, functions, and string slicing.\n"
                "2. **Master Biopython & Pandas:** Parsing FASTA, FASTQ, PDB, and analyzing dataframes.\n"
                "3. **Learn Linux Command Line:** `grep`, `awk`, `samtools`, `bedtools`, and shell scripting.\n"
                "4. **Build Real Projects:** Replicate published papers, build GitHub portfolios, and use Titan!"
            )
        else:
            custom_ans = (
                f"**Student Question:** *\"{custom_question}\"*\n\n"
                f"**Dr. Titan AI Response:** In {data['title']}, the most essential rule is understanding "
                f"structure-function relationships: how sequence dictates structure, and structure dictates biological activity. "
                f"Always remember to verify your inputs with negative and positive controls, check statistical E-values, and validate in-silico findings with wet-lab literature!"
            )

    # Visualization: Student Mastery / Concept Progress Chart
    concept_breakdown = pd.DataFrame([
        {"Concept Component": "Biological Principles", "Mastery_Level": 90, "Domain": "Foundations"},
        {"Concept Component": "Key Formulas & Math", "Mastery_Level": 82, "Domain": "Quantitative"},
        {"Concept Component": "Wet-Lab Context", "Mastery_Level": 78, "Domain": "Laboratory"},
        {"Concept Component": "Bioinformatics Tools", "Mastery_Level": 95, "Domain": "Computational"},
        {"Concept Component": "Real-World Applications", "Mastery_Level": 88, "Domain": "Biotechnology"},
    ])
    fig = px.bar(
        concept_breakdown,
        x="Concept Component",
        y="Mastery_Level",
        color="Domain",
        color_discrete_sequence=[TITAN_TEAL, TITAN_GOLD, TITAN_CORAL, TITAN_BLUE, TITAN_PURPLE],
        text="Mastery_Level"
    )
    fig.update_layout(
        **titan_plot_layout(f"{data['title']} — Student Knowledge Roadmap", height=320),
        yaxis_range=[0, 100],
    )

    metrics = [
        ("Topic", matched_key, None),
        ("Mode", mode.split()[0], None),
        ("Language", language, None),
        ("Learning Level", "All Levels (K-12 to Grad)", None),
    ]

    notes = [
        f"**Core Analogy:** {data['analogy']}",
        f"**Key Concepts:**\n{key_bullets}",
        custom_ans if custom_ans else "Ask any question in the custom question box to get instant Dr. Titan AI teaching assistance!",
        "Tip: Check the quiz below to test your understanding before moving to the next module!"
    ]

    return ToolResult(
        title=title,
        summary=summary_text,
        metrics=metrics,
        dataframe=quiz_df,
        figure=fig,
        notes=notes
    )
