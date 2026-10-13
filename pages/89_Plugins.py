"""🔌 Plugin System — Community tools loaded from the plugins/ folder.

Auto-discovers .py files with a @tool-decorated function or standard
PLUGIN_NAME / PLUGIN_DESCRIPTION / run() conventions. Displays a safety
warning about third-party plugins.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import streamlit as st

from titan_utils.i18n import t
from titan_utils.ui import dr_titan_tip, titan_title

titan_title(
    "🔌",
    "Plugin System",
    "Extend Titan with community tools! Single-file .py plugins are auto-loaded from the plugins/ folder.",
)

# ── Safety notice ────────────────────────────────────────────────────────────
st.warning(t(
    "⚠️ **Safety Notice:** Third-party plugins run as-is — they execute with full Python "
    "permissions. Only install plugins from sources you trust. Titan does not sandbox plugins."
))

# ── Plugin discovery ─────────────────────────────────────────────────────────
PLUGINS_DIR = pathlib.Path(__file__).resolve().parents[1] / "plugins"


def _discover_plugins(plugins_dir: pathlib.Path) -> list[dict]:
    """Discover valid plugin modules in the plugins directory."""
    discovered = []
    if not plugins_dir.is_dir():
        return discovered
    for py_file in sorted(plugins_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"plugin_{py_file.stem}", str(py_file))
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            name = getattr(module, "PLUGIN_NAME", py_file.stem.replace("_", " ").title())
            desc = getattr(module, "PLUGIN_DESCRIPTION", "No description provided.")
            author = getattr(module, "PLUGIN_AUTHOR", "Community")
            has_run = callable(getattr(module, "run", None))

            discovered.append({
                "name": name,
                "description": desc,
                "author": author,
                "has_run": has_run,
                "module": module,
                "file": py_file.name,
            })
        except Exception as exc:
            discovered.append({
                "name": py_file.stem,
                "description": f"⚠️ Failed to load: {exc}",
                "author": "Unknown",
                "has_run": False,
                "module": None,
                "file": py_file.name,
            })
    return discovered


plugins = _discover_plugins(PLUGINS_DIR)

# ── Display plugins ──────────────────────────────────────────────────────────
if not plugins:
    st.info(t("No plugins found in the `plugins/` folder. Add a .py file to get started!"))
    with st.expander(t("📖 How to write a Titan plugin")):
        st.code('''# plugins/my_tool.py
PLUGIN_NAME = "My Bio Tool"
PLUGIN_DESCRIPTION = "Does something cool with biology."
PLUGIN_AUTHOR = "Your Name"

def run():
    return "Hello from my plugin!"
''', language="python")
else:
    st.subheader(t("🧩 Installed Plugins ({count})", count=len(plugins)))

    for plugin in plugins:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### 🔌 {plugin['name']}")
                st.caption(t("By: {author} | File: `{file}`", author=plugin["author"], file=plugin["file"]))
                st.write(t(plugin["description"]))
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if plugin["has_run"]:
                    if st.button(t("▶️ Run"), key=f"run_{plugin['file']}", use_container_width=True):
                        try:
                            result = plugin["module"].run()
                            st.success(t("✅ Plugin executed successfully!"))
                            if isinstance(result, str):
                                st.code(result)
                            elif isinstance(result, tuple) and len(result) == 3:
                                # Haiku-style: 3 lines
                                st.markdown(f"```\n{chr(10).join(result)}\n```")
                            else:
                                st.write(result)
                        except Exception as exc:
                            st.error(t("❌ Plugin error: {error}", error=str(exc)))
                else:
                    st.caption(t("⚠️ No `run()` function found"))

# ── Plugin format guide ──────────────────────────────────────────────────────
st.markdown("---")
with st.expander(t("📖 Plugin Format Guide")):
    st.markdown(t("""
**To create a plugin:**
1. Create a single `.py` file in the `plugins/` folder
2. Define these module-level attributes:
   - `PLUGIN_NAME` — display name (string)
   - `PLUGIN_DESCRIPTION` — what it does (string)
   - `PLUGIN_AUTHOR` — your name (string)
3. Define a `run()` function — this is the entry point
4. The `run()` function can accept Streamlit context or work standalone

**Example:**
```python
PLUGIN_NAME = "GC Calculator"
PLUGIN_DESCRIPTION = "Calculate GC content of a DNA sequence."
PLUGIN_AUTHOR = "Community"

def run(sequence: str = "ATGCGATCG") -> str:
    gc = (sequence.count("G") + sequence.count("C")) / len(sequence) * 100
    return f"GC Content: {gc:.1f}%"
```
    """))

st.markdown("---")
st.caption(t(
    "ℹ️ Plugins are **auto-loaded** from the `plugins/` directory at page load. "
    "No registration or configuration required."
))

dr_titan_tip(
    "The plugin system lets you extend Titan with your own bioinformatics tools! "
    "Think of it like apps on your phone — each plugin adds a new capability to the suite."
)