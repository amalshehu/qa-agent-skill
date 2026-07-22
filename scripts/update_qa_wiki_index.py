#!/usr/bin/env python3
"""Regenerate the catalog sections of .qa-wiki/index.md from bugs/*.md and
flows/*.md frontmatter, so index.md can't silently drift from the actual
pages. Stdlib only, no dependencies.

Usage: python scripts/update_qa_wiki_index.py [path-to-.qa-wiki]

Rewrites everything from the first "## Open bugs" heading onward; anything
above that line (e.g. a custom intro) is preserved as-is.
"""
import argparse
import re
import sys
from pathlib import Path
from datetime import date

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)


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
        pages[f.stem] = parse_frontmatter(f.read_text())
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wiki_path", nargs="?", default=".qa-wiki")
    args = ap.parse_args()

    root = Path(args.wiki_path)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)

    bugs = load_pages(root / "bugs")
    flows = load_pages(root / "flows")

    open_bugs = sorted(
        ((slug, fm) for slug, fm in bugs.items() if fm.get("status") == "open"),
        key=lambda kv: kv[1].get("severity", "z"),
    )
    fixed_bugs = sorted(
        ((slug, fm) for slug, fm in bugs.items() if fm.get("status") == "fixed"),
        key=lambda kv: kv[1].get("last_seen", ""),
        reverse=True,
    )[:10]
    unverified_bugs = sorted(
        ((slug, fm) for slug, fm in bugs.items() if fm.get("status") == "unverified"),
        key=lambda kv: kv[1].get("last_seen", ""),
    )
    flow_rows = sorted(flows.items(), key=lambda kv: kv[1].get("last_tested", ""), reverse=True)

    lines = ["## Open bugs", ""]
    if open_bugs:
        for slug, fm in open_bugs:
            lines.append(f"- [[{slug}]] — {fm.get('severity', 'unknown')}")
    else:
        lines.append("_None yet._")
    lines += ["", "## Unverified bugs (needs a human look)", ""]
    if unverified_bugs:
        for slug, fm in unverified_bugs:
            lines.append(f"- [[{slug}]] — last attempt {fm.get('last_seen', 'unknown date')}")
    else:
        lines.append("_None yet._")
    lines += ["", "## Fixed bugs (recent)", ""]
    if fixed_bugs:
        for slug, fm in fixed_bugs:
            lines.append(f"- [[{slug}]] — fixed {fm.get('last_seen', 'unknown date')}")
    else:
        lines.append("_None yet._")
    lines += ["", "## Flows tested", ""]
    if flow_rows:
        for slug, fm in flow_rows:
            lines.append(f"- [[{slug}]] — last tested {fm.get('last_tested', 'unknown date')}")
    else:
        lines.append("_None yet._")
    lines.append("")

    index_path = root / "index.md"
    existing = index_path.read_text() if index_path.exists() else "# QA Wiki index\n\nLast tested: —\n"
    header_match = re.search(r"^Last tested:.*$", existing, re.MULTILINE)
    if header_match:
        existing = existing[: header_match.end()] + "\n\n"
    else:
        existing = existing.rstrip() + "\n\n"
    existing = re.sub(r"^Last tested:.*$", f"Last tested: {date.today().isoformat()}", existing, flags=re.MULTILINE)

    intro = existing.split("## Open bugs")[0].rstrip() + "\n\n"
    index_path.write_text(intro + "\n".join(lines))
    print(
        f"wrote {index_path} — {len(open_bugs)} open, {len(unverified_bugs)} unverified, "
        f"{len(fixed_bugs)} fixed shown, {len(flow_rows)} flows"
    )


if __name__ == "__main__":
    main()
