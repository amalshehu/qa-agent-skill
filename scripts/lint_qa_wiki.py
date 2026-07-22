#!/usr/bin/env python3
"""Health check for a .qa-wiki/ directory. Stdlib only, no dependencies.

Usage: python scripts/lint_qa_wiki.py [path-to-.qa-wiki]

Flags:
- orphan bug pages: not linked from any flows/*.md
- stale open bugs: status: open but last_seen older than --stale-days (default 30)
- broken links: flows/*.md references a bug slug with no bugs/<slug>.md file
- index.md drift: bugs/flows on disk that aren't listed in index.md's catalog
"""
import argparse
import re
import sys
from pathlib import Path
from datetime import date

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([a-z0-9-]+)\]\]")


def parse_frontmatter(text):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fields = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def load_pages(dirpath):
    pages = {}
    if not dirpath.is_dir():
        return pages
    for f in sorted(dirpath.glob("*.md")):
        pages[f.stem] = {"path": f, "text": f.read_text(), "frontmatter": {}}
        pages[f.stem]["frontmatter"] = parse_frontmatter(pages[f.stem]["text"])
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wiki_path", nargs="?", default=".qa-wiki")
    ap.add_argument("--stale-days", type=int, default=30)
    args = ap.parse_args()

    root = Path(args.wiki_path)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    bugs = load_pages(root / "bugs")
    flows = load_pages(root / "flows")
    index_text = (root / "index.md").read_text() if (root / "index.md").exists() else ""

    issues = []

    linked_bugs = set()
    for slug, flow in flows.items():
        for ref in WIKILINK_RE.findall(flow["text"]):
            linked_bugs.add(ref)
            if ref not in bugs:
                issues.append(f"broken link: flows/{slug}.md references [[{ref}]] but bugs/{ref}.md doesn't exist")

    for slug, bug in bugs.items():
        if slug not in linked_bugs:
            issues.append(f"orphan bug: bugs/{slug}.md isn't linked from any flow page")

        fm = bug["frontmatter"]
        if fm.get("status") == "unverified":
            issues.append(
                f"needs a decision: bugs/{slug}.md is unverified — couldn't be reproduced "
                f"after repeated attempts, a human should confirm fixed or still-broken"
            )
        if fm.get("status") == "open" and fm.get("last_seen"):
            try:
                last_seen = date.fromisoformat(fm["last_seen"])
                age_days = (date.today() - last_seen).days
                if age_days > args.stale_days:
                    issues.append(
                        f"stale open bug: bugs/{slug}.md last verified {fm['last_seen']} "
                        f"({age_days} days ago) — re-verify it's still broken"
                    )
            except ValueError:
                issues.append(f"malformed date: bugs/{slug}.md has last_seen={fm['last_seen']!r}")

    for slug in bugs:
        if f"[[{slug}]]" not in index_text:
            issues.append(f"index drift: bugs/{slug}.md exists but isn't referenced in index.md")
    for slug in flows:
        if f"[[{slug}]]" not in index_text:
            issues.append(f"index drift: flows/{slug}.md exists but isn't referenced in index.md")

    if not issues:
        print(f"OK — {len(bugs)} bug page(s), {len(flows)} flow page(s), no issues found.")
        return

    print(f"{len(issues)} issue(s) found:\n")
    for i in issues:
        print(f"- {i}")
    sys.exit(1)


if __name__ == "__main__":
    main()
