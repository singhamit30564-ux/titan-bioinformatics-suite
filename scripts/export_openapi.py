"""Export the FastAPI OpenAPI schema for the web/ TypeScript client.

Run:  .venv/bin/python scripts/export_openapi.py
Output: web/openapi.json (consumed by openapi-typescript -> web/src/api/schema.d.ts).
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from titan_utils.api import app

    schema = app.openapi()
    out = ROOT / "web" / "openapi.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(schema.get('paths', {}))} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
