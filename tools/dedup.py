#!/usr/bin/env python3
"""Parse/validate dedup/decisions.txt and show what is left to classify.
  dedup.py check            validate ids, report duplicates / unknown ids / coverage
  dedup.py set              print current set (slug | name | #members)
  dedup.py pending PREFIX   print unassigned app-tier titles whose sid starts with PREFIX"""
import sys
from collections import Counter
from pathlib import Path

from sources import all_items

DECISIONS = Path(__file__).resolve().parent.parent / "dedup/decisions.txt"


def parse(path=DECISIONS):
    concepts, assign = {}, {}  # slug -> {name, kind, tags}; sid -> slug
    for n, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        head, _, ids = line.partition("::")
        if head.startswith("+"):
            slug, name, kind, tags = [x.strip() for x in head[1:].split("|")]
            assert slug not in concepts, f"line {n}: duplicate slug {slug}"
            assert kind in ("attack", "guide"), f"line {n}: bad kind {kind}"
            concepts[slug] = {"slug": slug, "name": name, "kind": kind,
                              "tags": [t for t in tags.split(",") if t], "order": len(concepts)}
        else:
            slug = head.strip()
            assert slug in concepts, f"line {n}: unknown slug {slug}"
        for sid in ids.split():
            assert sid not in assign, f"line {n}: {sid} already in {assign[sid]}"
            assign[sid] = slug
    return concepts, assign


if __name__ == "__main__":
    concepts, assign = parse()
    app = {i["sid"]: i for i in all_items() if i["tier"] == "app"}
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        unknown = [s for s in assign if s not in app]
        print(f"{len(concepts)} entries, {len(assign)}/{len(app)} items assigned")
        print("unknown ids:", unknown or "none")
        print("empty entries:", [c for c in concepts if c not in set(assign.values())] or "none")
        print("left per prefix:", dict(Counter(s.split(":")[0].split("-")[0][:2] if s[0] == "T" else s.split(":")[0].split("-")[0]
                                            for s in app if s not in assign)))
    elif cmd == "set":
        size = Counter(assign.values())
        for c in concepts.values():
            print(f"{c['slug']} | {c['name']} | {size[c['slug']]}")
    elif cmd == "pending":
        for sid, i in app.items():
            if sid.startswith(sys.argv[2]) and sid not in assign:
                print(f"{sid} | {i['title']}")
