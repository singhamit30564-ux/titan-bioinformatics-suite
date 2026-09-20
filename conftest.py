"""Pytest bootstrap.

Puts the repository root on ``sys.path`` so that ``import titan_utils`` works
both for plain unit tests and for ``streamlit.testing`` AppTest runs (AppTest
executes each page as a script, so the root must be importable from it too).
"""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
