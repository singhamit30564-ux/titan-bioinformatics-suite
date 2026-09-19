"""Static navigation regression tests; no Streamlit server is required.

Run with: python -m unittest discover -s tests -v
"""

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = [
    "Home",
    "Category 1: DNA/RNA Basics",
    "Category 2: Protein Analysis",
    "Category 3: Genomics & QC",
    "Category 4: Alignment & Phylogeny",
    "Category 5: Lab & Pipeline",
]
REPAIRED_ROUTES = {
    "1️ DNA ↔ RNA Converter": "pages/1_DNA_RNA_Conversion.py",
    "3️⃣ Reverse Complement": "pages/1_03_Reverse_Complement_Stats.py",
    "4️⃣ GC Content Advanced": "pages/1_04_GC_Content_Melting_Temp.py",
    "5️⃣ Mutation Simulator": "pages/1_05_Mutation_SNP_Detection.py",
    "7️ Motif Pattern Search": "pages/1_07_Motif_Pattern_Finder.py",
    "8️⃣ Restriction Enzyme Analyzer": "pages/1_08_Restriction_Enzyme_Cutter.py",
    "9️ Codon Usage Table": "pages/1_09_Codon_Usage_Frequency.py",
    "🔟 Hamming Distance": "pages/1_10_Hamming_Edit_Distance.py",
    "1️⃣1️ Nucleotide Frequency": "pages/1_11_Nucleotide_Frequency_Entropy.py",
    "1️⃣2️ Central Dogma Visualizer": "pages/1_12_Central_Dogma_Visualizer.py",
    "3_01 FASTA/FASTQ Parser": "pages/3_01_FASTA_FASTQ_Parser_QC.py",
}


def is_streamlit_call(node, name):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "st"
        and node.func.attr == name
    )


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
        cls.switches = [
            node for node in ast.walk(cls.tree)
            if is_streamlit_call(node, "switch_page")
        ]

    def test_category_labels_and_order_are_preserved(self):
        menus = [
            node for node in ast.walk(self.tree)
            if is_streamlit_call(node, "radio")
        ]
        self.assertEqual(len(menus), 1)
        self.assertEqual(ast.literal_eval(menus[0].args[1]), CATEGORIES)

    def test_all_42_targets_exist_and_are_unique(self):
        self.assertEqual(len(self.switches), 42)
        targets = []
        for call in self.switches:
            with self.subTest(line=call.lineno):
                self.assertEqual(len(call.args), 1)
                target = ast.literal_eval(call.args[0])
                self.assertIsInstance(target, str)
                path = Path(target)
                self.assertFalse(path.is_absolute())
                self.assertEqual(path.parent, Path("pages"))
                self.assertEqual(path.suffix, ".py")
                self.assertTrue((ROOT / path).is_file(), f"Missing page: {target}")
                targets.append(target)
        self.assertEqual(len(set(targets)), 42)

    def test_each_route_remains_attached_to_a_unique_button(self):
        routes = self.button_routes()
        self.assertEqual(len(routes), 42)

    def test_repaired_buttons_open_the_intended_pages(self):
        routes = self.button_routes()
        for label, target in REPAIRED_ROUTES.items():
            with self.subTest(button=label):
                self.assertEqual(routes.get(label), target)

    def button_routes(self):
        routes = {}
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.If) or not is_streamlit_call(node.test, "button"):
                continue
            calls = [
                child for statement in node.body for child in ast.walk(statement)
                if is_streamlit_call(child, "switch_page")
            ]
            self.assertEqual(len(calls), 1)
            label = ast.literal_eval(node.test.args[0])
            self.assertNotIn(label, routes)
            routes[label] = ast.literal_eval(calls[0].args[0])
        return routes


if __name__ == "__main__":
    unittest.main()
