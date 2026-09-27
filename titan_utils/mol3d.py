"""In-browser 3D molecular viewer (3Dmol.js WebGL) for the Titan suite.

Streams PDB text to a browser-side 3Dmol.js canvas rendered with
``st.iframe`` (falls back to ``st.components.v1.html`` on older Streamlit).
Everything runs client-side in WebGL — no coordinates are uploaded or stored
(Zero Data Retention by design).

Supported render styles: **Cartoon**, **Stick**, **Sphere**, **Surface**.
Bundled preset structures (miniature, generated in RAM from ideal geometry):

* ``cas9``  — CRISPR-Cas9 REC lobe alpha-helix bundle (inspired by PDB 5AXW)
* ``hemo``  — Hemoglobin alpha-helical subunit (inspired by PDB 1HHO)
* ``insulin`` — Insulin A + B chains (inspired by PDB 4INS/1TRZ)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

__all__ = [
    "MOL3D_STYLES",
    "Mol3DPreset",
    "MOL3D_PRESETS",
    "list_presets",
    "get_preset",
    "build_helix_pdb",
    "build_preset_pdb",
    "mol3d_viewer_html",
    "render_mol3d_viewer",
    "embed_html",
]

MOL3D_STYLES: Tuple[str, ...] = ("Cartoon", "Stick", "Sphere", "Surface")

# 3Dmol.js build served to the *user's browser* (client-side WebGL).
_3DMOL_CDN = "https://3Dmol.org/build/3Dmol-min.js"

# Chart-friendly coloring per chain (colorblind-safe accents).
_CHAIN_COLORS = {
    "A": "#0072B2",  # Okabe-Ito blue
    "B": "#D55E00",  # vermillion
    "C": "#009E73",  # bluish green
    "D": "#CC79A7",  # reddish purple
}

_AA3 = (
    "ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE "
    "LEU LYS MET PHE PRO SER THR TRP TYR VAL"
).split()


# ─────────────────────────────────────────────────────────────────────────────
# Miniature preset structures (deterministic, generated in RAM)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Mol3DPreset:
    """A bundled molecular structure preset."""

    id: str
    name: str
    description: str
    citation: str
    default_style: str = "Cartoon"
    chains: Tuple[Tuple[str, int, str], ...] = ()  # (chain_id, n_residues, secondary)
    pdb: str = ""

    def as_dict(self) -> Dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "citation": self.citation,
            "default_style": self.default_style,
            "residues": str(self.residue_count),
        }

    @property
    def residue_count(self) -> int:
        return sum(n for _, n, _ in self.chains)


def build_helix_pdb(
    chain_id: str,
    n_residues: int,
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    start_resi: int = 1,
    phase: float = 0.0,
    radius: float = 2.3,
    rise: float = 1.5,
    aa_offset: int = 0,
) -> List[str]:
    """Generate ATOM records for an ideal alpha-helix backbone + CB.

    Geometry: 100 degrees/residue, 1.5 A rise, 2.3 A CA radius (standard
    alpha-helix). Atoms N, CA, C, O, CB make Cartoon / Stick / Sphere /
    Surface styles all render correctly in 3Dmol.js.
    """
    records: List[str] = []
    ox, oy, oz = offset
    for i in range(n_residues):
        resi = start_resi + i
        theta = math.radians(100.0 * i) + phase
        aa = _AA3[(i + aa_offset) % len(_AA3)]
        # Alpha carbon on the helix cylinder.
        ca = (radius * math.cos(theta) + ox, radius * math.sin(theta) + oy, rise * i + oz)
        # Backbone N slightly behind/inside, C ahead/inside, O out+up.
        n = (radius * 0.85 * math.cos(theta - 0.55) + ox,
             radius * 0.85 * math.sin(theta - 0.55) + oy,
             rise * i - 0.55 + oz)
        c = (radius * 0.85 * math.cos(theta + 0.55) + ox,
             radius * 0.85 * math.sin(theta + 0.55) + oy,
             rise * i + 0.62 + oz)
        o = (radius * 1.45 * math.cos(theta + 0.35) + ox,
             radius * 1.45 * math.sin(theta + 0.35) + oy,
             rise * i + 0.42 + oz)
        cb = (radius * 1.55 * math.cos(theta + 0.25) + ox,
              radius * 1.55 * math.sin(theta + 0.25) + oy,
              rise * i - 0.25 + oz)
        atoms = (("N", n), ("CA", ca), ("C", c), ("O", o), ("CB", cb))
        for serial, (name, (x, y, z)) in enumerate(atoms, start=1):
            elem = name[0]
            # wwPDB fixed-column ATOM record (cols 1-78) — 3Dmol.js parses by column.
            records.append(
                f"ATOM  {serial:5d}"          # 1-6 record, 7-11 serial
                f" "                          # 12
                f" {name:<3}"                 # 13-16 atom name
                f" "                          # 17 altLoc
                f"{aa:>3}"                    # 18-20 resName
                f" "                          # 21
                f"{chain_id}"                 # 22 chainID
                f"{resi:4d}"                  # 23-26 resSeq
                f" "                          # 27 iCode
                f"   "                        # 28-30
                f"{x:8.3f}{y:8.3f}{z:8.3f}"   # 31-54 coordinates
                f"{1.00:6.2f}{20.0 + (i % 30):6.2f}"  # 55-66 occ + B-factor
                f"          "                 # 67-76
                f"{elem:>2}"                  # 77-78 element
            )
    return records


def _bundle_pdb(header: Sequence[str], chain_specs: Sequence[Tuple[str, int, Tuple[float, float, float], float]]) -> str:
    """Assemble a PDB text block from helix chain specs + REMARK header."""
    lines: List[str] = list(header)
    serial = 1
    for chain_id, n_res, offset, phase in chain_specs:
        for record in build_helix_pdb(chain_id, n_res, offset=offset, phase=phase):
            lines.append(f"{record[:6]}{serial:5d}{record[11:]}")
            serial += 1
    lines.append("END")
    return "\n".join(lines) + "\n"


def _preset_cas9() -> str:
    return _bundle_pdb(
        [
            "REMARK   1 TITAN MINIATURE STRUCTURE - CRISPR-Cas9 REC LOBE",
            "REMARK   1 INPIRED BY PDB 5AXW (S. PYOGENES CAS9 / SGRNA / DNA)",
            "REMARK   2 IDEALIZED ALPHA-HELICAL BUNDLE FOR EDUCATIONAL VIEWING",
        ],
        [
            ("A", 24, (0.0, 0.0, 0.0), 0.0),
            ("B", 20, (11.0, 2.0, 1.5), 1.1),
            ("C", 18, (5.5, -9.0, 3.0), 2.2),
        ],
    )


def _preset_hemo() -> str:
    return _bundle_pdb(
        [
            "REMARK   1 TITAN MINIATURE STRUCTURE - HEMOGLOBIN ALPHA SUBUNIT",
            "REMARK   1 INSPIRED BY PDB 1HHO (DEOXY HUMAN HEMOGLOBIN)",
            "REMARK   2 A-B-C-D HELIX BUNDLE = GLOBIN FOLD CORE",
        ],
        [
            ("A", 22, (0.0, 0.0, 0.0), 0.3),
            ("B", 21, (9.5, 3.5, 2.0), 1.7),
            ("C", 19, (3.0, -8.5, 0.5), 2.6),
            ("D", 18, (12.5, -5.0, 3.5), 0.9),
        ],
    )


def _preset_insulin() -> str:
    return _bundle_pdb(
        [
            "REMARK   1 TITAN MINIATURE STRUCTURE - INSULIN A + B CHAINS",
            "REMARK   1 INSPIRED BY PDB 4INS (2-ZN BOVINE INSULIN)",
            "REMARK   2 CHAIN A SHORT HELIX, CHAIN B LONG HELIX",
        ],
        [
            ("A", 12, (0.0, 0.0, 0.0), 0.4),
            ("B", 22, (8.0, 4.0, 1.0), 1.9),
        ],
    )


MOL3D_PRESETS: Dict[str, Mol3DPreset] = {
    "cas9": Mol3DPreset(
        id="cas9",
        name="CRISPR-Cas9 (REC lobe)",
        description=(
            "Miniature alpha-helical bundle representing the recognition lobe "
            "of Streptococcus pyogenes Cas9 in complex with sgRNA and target DNA."
        ),
        citation="Inspired by PDB 5AXW (Nishimasu et al., Cell 2014)",
        default_style="Cartoon",
        chains=(("A", 24, "helix"), ("B", 20, "helix"), ("C", 18, "helix")),
        pdb=_preset_cas9(),
    ),
    "hemo": Mol3DPreset(
        id="hemo",
        name="Hemoglobin (alpha subunit)",
        description=(
            "Miniature globin fold: four alpha-helices (A-D) forming the core "
            "of a human hemoglobin subunit surrounding the heme pocket."
        ),
        citation="Inspired by PDB 1HHO (Shaanan, Nature 1983)",
        default_style="Cartoon",
        chains=(("A", 22, "helix"), ("B", 21, "helix"), ("C", 19, "helix"), ("D", 18, "helix")),
        pdb=_preset_hemo(),
    ),
    "insulin": Mol3DPreset(
        id="insulin",
        name="Insulin (A + B chains)",
        description=(
            "Miniature insulin monomer: short A-chain helix and long B-chain "
            "helix, the classic two-chain storage form of the hormone."
        ),
        citation="Inspired by PDB 4INS (Adams et al., Nature 1969)",
        default_style="Cartoon",
        chains=(("A", 12, "helix"), ("B", 22, "helix")),
        pdb=_preset_insulin(),
    ),
}


def list_presets() -> List[Dict[str, str]]:
    """Registry rows for every bundled preset (no PDB payload)."""
    return [p.as_dict() for p in MOL3D_PRESETS.values()]


def get_preset(preset_id: str) -> Mol3DPreset:
    """Look up a preset by id; falls back to CRISPR-Cas9."""
    return MOL3D_PRESETS.get(preset_id, MOL3D_PRESETS["cas9"])


def build_preset_pdb(preset_id: str) -> str:
    """Return the PDB text for a bundled preset (generated in RAM)."""
    return get_preset(preset_id).pdb


# ─────────────────────────────────────────────────────────────────────────────
# HTML / Streamlit rendering
# ─────────────────────────────────────────────────────────────────────────────

def _style_spec_js(style: str) -> str:
    style = style if style in MOL3D_STYLES else "Cartoon"
    return {
        "Cartoon": "{cartoon: {color: 'spectrum'}}",
        "Stick": "{stick: {radius: 0.18, colorscheme: 'Jmol'}}",
        "Sphere": "{sphere: {scale: 0.28, colorscheme: 'Jmol'}}",
        "Surface": "{surface: {opacity: 0.82, colorscheme: 'whiteCarbon'}}",
    }[style]


def mol3d_viewer_html(
    pdb_text: str,
    style: str = "Cartoon",
    height: int = 440,
    background: str = "#0a0e17",
    spin: bool = False,
    show_controls: bool = True,
) -> str:
    """Build the self-contained 3Dmol.js viewer HTML (runs client-side)."""
    style = style if style in MOL3D_STYLES else "Cartoon"
    # Embed PDB safely inside a JS template literal.
    pdb_js = (pdb_text or "").replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    buttons = ""
    if show_controls:
        buttons = "".join(
            f"<button class='m3d-btn' data-style='{s}' "
            f"style='background:{'#d4af37' if s == style else '#222838'}'>{s}</button>"
            for s in MOL3D_STYLES
        )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  html, body {{ margin: 0; padding: 0; background: {background}; }}
  .m3d-wrap {{ font-family: 'Courier New', monospace; color: #e0e0e0; }}
  .m3d-bar {{ display: flex; gap: 6px; padding: 6px 8px; flex-wrap: wrap; }}
  .m3d-btn {{ border: none; border-radius: 6px; color: #e0e0e0; cursor: pointer;
             font-size: 12px; padding: 5px 10px; font-weight: bold; }}
  .m3d-btn:hover {{ filter: brightness(1.15); }}
  .m3d-canvas {{ width: 100%; height: {int(height) - (44 if show_controls else 0)}px; position: relative; }}
  .m3d-foot {{ font-size: 10px; color: #8b9bb4; padding: 2px 8px 6px; }}
</style>
<script src="{_3DMOL_CDN}"></script>
</head>
<body>
<div class="m3d-wrap">
  <div class="m3d-bar">{buttons}</div>
  <div id="m3dviewer" class="m3d-canvas"></div>
  <div class="m3d-foot">3Dmol.js WebGL &middot; style: <b id="m3d-style">{style}</b> &middot; drag to rotate, scroll to zoom</div>
</div>
<script>
  (function () {{
    var pdb = `{pdb_js}`;
    var styleName = "{style}";
    function specFor(name) {{
      return {{
        "Cartoon": {{cartoon: {{color: 'spectrum'}}}},
        "Stick": {{stick: {{radius: 0.18, colorscheme: 'Jmol'}}}},
        "Sphere": {{sphere: {{scale: 0.28, colorscheme: 'Jmol'}}}},
        "Surface": {{surface: {{opacity: 0.82, colorscheme: 'whiteCarbon'}}}}
      }}[name];
    }}
    function boot() {{
      if (typeof $3Dmol === 'undefined') {{
        document.getElementById('m3dviewer').innerHTML =
          '<div style="padding:14px;color:#8b9bb4;font-size:12px">' +
          '3Dmol.js could not be loaded (offline?). Coordinates stay local - ' +
          'no data was uploaded or stored.</div>';
        return;
      }}
      var viewer = $3Dmol.createViewer('m3dviewer', {{backgroundColor: '{background}'}});
      viewer.addModel(pdb, 'pdb');
      viewer.setStyle({{}}, specFor(styleName));
      viewer.zoomTo();
      viewer.render();
      {"viewer.spin('y', 0.6);" if spin else ""}
      document.querySelectorAll('.m3d-btn').forEach(function (btn) {{
        btn.addEventListener('click', function () {{
          styleName = btn.getAttribute('data-style');
          viewer.setStyle({{}}, specFor(styleName));
          viewer.render();
          document.getElementById('m3d-style').textContent = styleName;
          document.querySelectorAll('.m3d-btn').forEach(function (b) {{
            b.style.background = (b === btn) ? '#d4af37' : '#222838';
          }});
        }});
      }});
    }}
    if (typeof $3Dmol !== 'undefined') {{ boot(); }}
    else {{ window.addEventListener('load', boot); }}
  }})();
</script>
</body>
</html>"""


def embed_html(html: str, height: int = 400) -> None:
    """Embed arbitrary HTML/JS in the Streamlit app (iframe-first)."""
    import streamlit as st

    iframe_fn = getattr(st, "iframe", None)
    if iframe_fn is not None:
        iframe_fn(html, height=height)
        return
    import streamlit.components.v1 as components

    components.html(html, height=height)


def render_mol3d_viewer(
    pdb_text: str = "",
    style: str = "Cartoon",
    preset_id: str = "cas9",
    height: int = 440,
    spin: bool = False,
    key: str = "",
) -> None:
    """Render the in-browser 3Dmol.js WebGL viewer in the current Streamlit page."""
    if not pdb_text:
        pdb_text = build_preset_pdb(preset_id)
    embed_html(
        mol3d_viewer_html(pdb_text, style=style, height=height, spin=spin),
        height=height,
    )
    del key  # key reserved for future component identity support
