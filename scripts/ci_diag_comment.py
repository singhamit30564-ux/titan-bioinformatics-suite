#!/usr/bin/env python3
"""Post (or refresh) a CI diagnostics comment on the active pull request.

Used by .github/workflows/ci.yml when a job fails: the full tool output is
attached to the PR as one bot comment (replacing the previous one carrying the
same marker), so failures are diagnosable from the PR itself.

Usage (CI only):
    python3 scripts/ci_diag_comment.py --marker "<!-- x -->" --title "..." \
        --file /tmp/fmt.log [--file ...] [--note "..."]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

MAX_BODY = 60_000  # GitHub comment body limit is 65536; leave headroom


def gh(args: list[str], input_text: str | None = None) -> str:
    env = dict(os.environ)
    result = subprocess.run(
        ["gh", *args],
        input=input_text,
        capture_output=True,
        text=True,
        env=env,
        shell=False,
    )
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--marker", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("no GH_TOKEN — skipping diagnostics comment", file=sys.stderr)
        return 0

    ref = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        print("no GITHUB_REPOSITORY — skipping", file=sys.stderr)
        return 0

    pr_number = ""
    listed = gh(["pr", "list", "--head", ref, "--state", "open", "--json", "number", "--limit", "1"])
    try:
        import json

        parsed = json.loads(listed or "[]")
        if parsed:
            pr_number = str(parsed[0]["number"])
    except Exception:
        pr_number = ""
    if not pr_number:
        print(f"no open PR for head '{ref}' — skipping diagnostics comment", file=sys.stderr)
        return 0

    sections: list[str] = [f"{args.marker}", f"## {args.title}", ""]
    if args.note:
        sections += [f"> {args.note}", ""]
    for path in args.file:
        p = Path(path)
        sections.append(f"<details><summary><code>{path}</code></summary>")
        sections.append("")
        if p.is_file():
            import re

            text = p.read_text(errors="replace") or "(empty)"
            text = text.replace("\r\n", "\n")
            text = re.sub(r"\x1b\[[0-9;]*m", "", text)
            # Diagnostics live at the END of tool logs (heads are download noise).
            chunk = "\n".join(text.splitlines()[-250:])
            sections.append("```text")
            sections.append(chunk[:MAX_BODY])
            if len(chunk) > MAX_BODY:
                sections.append(f"... truncated ({len(chunk) - MAX_BODY} more chars)")
            sections.append("```")
        else:
            sections.append("(file not produced — step failed before writing it)")
        sections.append("</details>")
        sections.append("")
    body = "\n".join(sections)[:MAX_BODY]

    # Replace an earlier diagnostics comment (same marker) to avoid spam.
    existing = gh(
        ["api", f"repos/{repo}/issues/{pr_number}/comments", "--paginate"],
    )
    try:
        import json

        for comment in json.loads(existing or "[]"):
            if isinstance(comment, dict) and args.marker in str(comment.get("body", "")):
                gh(["api", "-X", "DELETE", f"repos/{repo}/issues/comments/{comment['id']}"])
    except Exception:
        pass

    gh(["pr", "comment", pr_number, "--body-file", "-"], input_text=body)
    print(f"posted diagnostics comment on #{pr_number}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
