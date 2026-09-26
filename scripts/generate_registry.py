"""Script to build titan_utils/registry.py for all 260 tools."""
import inspect
import json
import re
from pathlib import Path
import titan_tools as tt

def main():
    content = Path("Home.py").read_text()
    legacy_categories = [
        ("cat1_dna", "DNA / RNA Basics", "Basic DNA/RNA"),
        ("cat2_prot", "Protein Analysis", "Protein Analysis"),
        ("cat3_genome", "Genomics & QC", "Genomics & QC"),
        ("cat4_align", "Alignment & Phylogeny", "Alignment & Phylogeny"),
        ("cat5_lab", "Lab & Molecular Biology", "Lab & Molecular Biology"),
    ]

    legacy_tools = []
    tool_id_counter = 1

    for cat_var, cat_name, domain_name in legacy_categories:
        m = re.search(cat_var + r'\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if m:
            files = re.findall(r'\"(\d+_[^\"]+\.py)\"', m.group(1))
            for fname in files:
                stem = fname.replace(".py", "")
                if "_" in stem and stem[:2].isdigit():
                    stem = stem.split("_", 1)[1]
                title = stem.replace("_", " ").replace("and", "&").title()
                for k, v in [
                    ("Dna", "DNA"), ("Rna", "RNA"), ("Gc", "GC"), ("Tm", "Tm"), ("Crispr", "CRISPR"),
                    ("Pcr", "PCR"), ("Blast", "BLAST"), ("Fasta", "FASTA"), ("Fastq", "FASTQ"),
                    ("Qc", "QC"), ("Ms A", "MSA"), ("Vcf", "VCF"), ("Cgr", "CGR"), ("Orf", "ORF"),
                    ("Grna", "gRNA"), ("Cas9", "Cas9"), ("Snp", "SNP"), ("Indel", "InDel"),
                    ("Kegg", "KEGG"), ("Go", "GO"), ("Pi", "pI"), ("Mw", "MW")
                ]:
                    title = title.replace(k, v)
                
                hname = "tool_legacy_dna_rna_convert" if tool_id_counter == 1 else ("tool_legacy_revcomp" if tool_id_counter == 2 else "tool_legacy_generic")
                legacy_tools.append({
                    "id": tool_id_counter,
                    "name": title,
                    "domain": domain_name,
                    "category_id": cat_var,
                    "category_name": cat_name,
                    "description": f"Foundational {domain_name} analysis module with validated Biopython algorithms.",
                    "console_page": fname,
                    "inputs": [
                        {"id": "sequence", "label": "Input Sequence / Data", "type": "textarea", "default": "ATGCGATCGATCGATCGATCGATC", "help": "Enter biological sequence or data"}
                    ],
                    "handler_name": hname,
                    "student_tip": f"{title} teaches core principles of molecular biology, sequence structure, and computational algorithms."
                })
                tool_id_counter += 1

    print(f"Generated {len(legacy_tools)} legacy tools.")

    # New domains mapping
    import titan_tools.agriculture as m_agri
    import titan_tools.marine as m_marine
    import titan_tools.clinical as m_clin
    import titan_tools.metagenomics as m_meta
    import titan_tools.structural as m_struct
    import titan_tools.epigenetics as m_epi
    import titan_tools.synthetic as m_syn
    import titan_tools.population as m_pop
    import titan_tools.ncbi_db as m_ncbi
    import titan_tools.dr_titan as m_dr

    domain_configs = [
        ("agri", "Agriculture & Plant Genomics", "65_Agriculture_and_Plant_Genomics.py", m_agri, 20),
        ("marine", "Marine & Extremophile Genomics", "66_Marine_and_Extremophile_Genomics.py", m_marine, 20),
        ("clinical", "Clinical Genomics & Precision Medicine", "67_Clinical_Genomics_Precision_Medicine.py", m_clin, 20),
        ("metagenomics", "Metagenomics & Microbiome", "68_Metagenomics_and_Microbiome.py", m_meta, 20),
        ("structural", "Structural Biology & Biophysics", "69_Structural_Biology_and_Biophysics.py", m_struct, 20),
        ("epigenetics", "Epigenetics & Epitranscriptomics", "70_Epigenetics_and_Epitranscriptomics.py", m_epi, 20),
        ("synthetic", "Synthetic Biology & Metabolic Engineering", "71_Synthetic_Biology_Metabolic_Eng.py", m_syn, 20),
        ("population", "Population Genetics & Evolutionary Dynamics", "72_Population_Genetics_Evolution.py", m_pop, 20),
        ("ncbi", "NCBI & Global Bioinformatics APIs", "73_NCBI_and_Global_Bioinformatics_APIs.py", m_ncbi, 20),
        ("dr_titan", "Dr. Titan AI & Bio-Copilot", "74_Dr_Titan_AI_Bio_Copilot.py", m_dr, 28),
    ]

    all_tools = list(legacy_tools)
    current_id = 53

    for cat_id, d_name, c_page, mod, expected_count in domain_configs:
        # Get all functions starting with tool_ in module in definition order
        func_names = [f for f in dir(mod) if f.startswith("tool_") and callable(getattr(mod, f))]
        # Sort or maintain order
        # Let's inspect line numbers to preserve source order
        func_names.sort(key=lambda fn: getattr(mod, fn).__code__.co_firstlineno)
        print(f"Module {cat_id}: found {len(func_names)} tools (expected {expected_count})")
        assert len(func_names) == expected_count, f"Mismatch in {cat_id}: {len(func_names)} != {expected_count}"

        for hname in func_names:
            func = getattr(mod, hname)
            doc = (func.__doc__ or "").strip()
            # Clean title from doc or function name
            first_line = doc.split("\n")[0] if doc else hname
            if ":" in first_line:
                first_line = first_line.split(":", 1)[1].strip()
            tool_title = first_line.rstrip(".") if first_line else hname.replace("tool_", "").replace("_", " ").title()

            sig = inspect.signature(func)
            inputs = []
            for p_name, param in sig.parameters.items():
                p_def = param.default if param.default != inspect.Parameter.empty else ""
                if isinstance(p_def, (int, float)):
                    itype = "number"
                elif isinstance(p_def, str) and (len(p_def) > 40 or "\n" in p_def):
                    itype = "textarea"
                else:
                    itype = "text"
                inputs.append({
                    "id": p_name,
                    "label": p_name.replace("_", " ").title(),
                    "type": itype,
                    "default": p_def,
                    "help": f"Input for {p_name.replace('_', ' ')}"
                })

            all_tools.append({
                "id": current_id,
                "name": tool_title,
                "domain": d_name,
                "category_id": cat_id,
                "category_name": d_name,
                "description": doc or f"Advanced {d_name} analytical tool.",
                "console_page": c_page,
                "inputs": inputs,
                "handler_name": hname,
                "student_tip": f"Tool #{current_id} ({tool_title}) demonstrates critical applied computational techniques in {d_name}."
            })
            current_id += 1

    print(f"Total tools across suite: {len(all_tools)}")
    assert len(all_tools) == 260, f"Expected exactly 260 tools, got {len(all_tools)}"

    # Generate Python code
    lines = [
        '"""Master Registry for the 260 tools in the Titan Bioinformatics Suite.',
        '',
        'Provides structured metadata, category mappings, input specifications,',
        'and handler dispatch for both legacy tools (1-52) and advanced tools (53-260).',
        '"""',
        'from __future__ import annotations',
        '',
        'from dataclasses import dataclass, field',
        'from typing import Any, Callable, Dict, List, Optional',
        'import titan_tools',
        '',
        '',
        '@dataclass',
        'class ToolInputSpec:',
        '    id: str',
        '    label: str',
        '    type: str  # "text", "textarea", "number", "select"',
        '    default: Any',
        '    options: List[str] = field(default_factory=list)',
        '    help: str = ""',
        '',
        '',
        '@dataclass',
        'class ToolSpec:',
        '    id: int',
        '    name: str',
        '    domain: str',
        '    category_id: str',
        '    category_name: str',
        '    description: str',
        '    console_page: str',
        '    inputs: List[ToolInputSpec]',
        '    handler_name: str',
        '    student_tip: str = ""',
        '',
        '    def get_handler(self) -> Optional[Callable[..., Any]]:',
        '        return getattr(titan_tools, self.handler_name, None)',
        '',
        '',
        'CATEGORIES = [',
        '    ("cat1_dna", "🧬 1 · DNA / RNA Basics", "01_DNA_RNA_Conversion.py"),',
        '    ("cat2_prot", "🥩 2 · Protein Analysis", "12_DNA_to_Protein_Translator.py"),',
        '    ("cat3_genome", "🧪 3 · Genomics & QC", "20_FASTA_FASTQ_Parser_QC.py"),',
        '    ("cat4_align", "🔄 4 · Alignment & Phylogeny", "40_Pairwise_Alignment.py"),',
        '    ("cat5_lab", "🧫 5 · Lab & Pipeline", "55_CRISPR_Cas9_gRNA_Designer.py"),',
        '    ("agri", "🌾 6 · Agriculture & Plant Genomics", "65_Agriculture_and_Plant_Genomics.py"),',
        '    ("marine", "🌊 7 · Marine & Extremophile Genomics", "66_Marine_and_Extremophile_Genomics.py"),',
        '    ("clinical", "🩺 8 · Clinical Genomics & Precision Med", "67_Clinical_Genomics_Precision_Medicine.py"),',
        '    ("metagenomics", "🦠 9 · Metagenomics & Microbiome", "68_Metagenomics_and_Microbiome.py"),',
        '    ("structural", "📐 10 · Structural Biology & Biophysics", "69_Structural_Biology_and_Biophysics.py"),',
        '    ("epigenetics", "🧬 11 · Epigenetics & Epitranscriptomics", "70_Epigenetics_and_Epitranscriptomics.py"),',
        '    ("synthetic", "⚙️ 12 · Synthetic Biology & Metabolic Eng", "71_Synthetic_Biology_Metabolic_Eng.py"),',
        '    ("population", "👥 13 · Population Genetics & Evolution", "72_Population_Genetics_Evolution.py"),',
        '    ("ncbi", "🌐 14 · NCBI & Global Bioinformatics APIs", "73_NCBI_and_Global_Bioinformatics_APIs.py"),',
        '    ("dr_titan", "🤖 15 · Dr. Titan AI & Bio-Copilot", "74_Dr_Titan_AI_Bio_Copilot.py"),',
        ']',
        '',
        'MASTER_REGISTRY: List[ToolSpec] = [',
    ]

    for t in all_tools:
        inputs_code = []
        for inp in t["inputs"]:
            inputs_code.append(
                f"        ToolInputSpec(id={repr(inp['id'])}, label={repr(inp['label'])}, type={repr(inp['type'])}, default={repr(inp['default'])}, help={repr(inp.get('help', ''))})"
            )
        inputs_block = "[\n" + ",\n".join(inputs_code) + "\n    ]" if inputs_code else "[]"
        lines.append(f"    ToolSpec(")
        lines.append(f"        id={t['id']},")
        lines.append(f"        name={repr(t['name'])},")
        lines.append(f"        domain={repr(t['domain'])},")
        lines.append(f"        category_id={repr(t['category_id'])},")
        lines.append(f"        category_name={repr(t['category_name'])},")
        lines.append(f"        description={repr(t['description'])},")
        lines.append(f"        console_page={repr(t['console_page'])},")
        lines.append(f"        inputs={inputs_block},")
        lines.append(f"        handler_name={repr(t['handler_name'])},")
        lines.append(f"        student_tip={repr(t['student_tip'])},")
        lines.append(f"    ),")

    lines.extend([
        ']',
        '',
        'REGISTRY_BY_ID: Dict[int, ToolSpec] = {t.id: t for t in MASTER_REGISTRY}',
        '',
        'REGISTRY_BY_CATEGORY: Dict[str, List[ToolSpec]] = {}',
        'for t in MASTER_REGISTRY:',
        '    REGISTRY_BY_CATEGORY.setdefault(t.category_id, []).append(t)',
        '',
        '',
        'def get_all_tools() -> List[ToolSpec]:',
        '    """Return all 260 registered tools."""',
        '    return MASTER_REGISTRY',
        '',
        '',
        'def get_tool_by_id(tool_id: int) -> Optional[ToolSpec]:',
        '    """Look up a tool specification by integer ID."""',
        '    return REGISTRY_BY_ID.get(tool_id)',
        '',
        '',
        'def get_tools_by_category(category_id: str) -> List[ToolSpec]:',
        '    """Get all tools belonging to a category slug."""',
        '    return REGISTRY_BY_CATEGORY.get(category_id, [])',
        '',
        '',
        'def search_tools(query: str = "", category_id: Optional[str] = None) -> List[ToolSpec]:',
        '    """Search tools by name, description, or domain."""',
        '    results = MASTER_REGISTRY',
        '    if category_id and category_id != "all":',
        '        results = [t for t in results if t.category_id == category_id]',
        '    if query and query.strip():',
        '        q = query.lower().strip()',
        '        results = [',
        '            t for t in results',
        '            if q in t.name.lower() or q in t.description.lower() or q in t.domain.lower() or q in str(t.id)',
        '        ]',
        '    return results',
        '',
    ])

    Path("titan_utils/registry.py").write_text("\n".join(lines))
    print("Wrote titan_utils/registry.py successfully!")

if __name__ == "__main__":
    main()
