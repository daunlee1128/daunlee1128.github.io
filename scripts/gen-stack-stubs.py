#!/usr/bin/env python3
"""_data/stacks.yml → stack/<slug>.md stub 생성. yml에 없는 stub은 삭제. 멱등.

usage: python3 scripts/gen-stack-stubs.py [--root DIR]
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

SLUG = re.compile(r"^[a-z0-9-]+$")
TEMPLATE = "---\nlayout: stack\nstack: {slug}\ntitle: {name}\npermalink: /stack/{slug}/\n---\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=Path(__file__).resolve().parents[1], type=Path)
    root = ap.parse_args().root
    groups = yaml.safe_load((root / "_data" / "stacks.yml").read_text(encoding="utf-8"))
    items = [it for g in groups for it in g["items"]]
    for it in items:
        if not SLUG.match(str(it["slug"])):
            print(f"error: slug must be ASCII [a-z0-9-]: {it['slug']!r}", file=sys.stderr)
            return 1
    out = root / "stack"
    out.mkdir(exist_ok=True)
    wanted = {it["slug"]: TEMPLATE.format(slug=it["slug"], name=it["name"]) for it in items}
    wrote = removed = 0
    for slug, body in wanted.items():
        p = out / f"{slug}.md"
        if not p.exists() or p.read_text(encoding="utf-8") != body:
            p.write_text(body, encoding="utf-8")
            wrote += 1
    for p in out.glob("*.md"):
        if p.stem not in wanted:
            p.unlink()
            removed += 1
    print(f"wrote {wrote}, removed {removed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
