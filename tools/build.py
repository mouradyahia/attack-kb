#!/usr/bin/env python3
"""Build the two tiers from raw/ + dedup/decisions.txt.
  index/attacks.json          compact list of attacks (what agents loop over)
  index/attacks/<slug>.json   one attack page: sections = {source title, source, url, text}
  archive/items.jsonl         incidents, labs, ATT&CK: pull on demand, linked to attacks
Usage: python3 tools/build.py"""
import json, shutil
from collections import Counter, defaultdict

from dedup import parse
from sources import KB, all_items

SOURCE_ORDER = ["PortSwigger", "OWASP", "MITRE CAPEC", "MITRE CWE"]
ARCHIVE_PREVIEW = 25  # archive links embedded per attack page; the rest via /api/archive?attack=


def rank(item):
    return next(i for i, s in enumerate(SOURCE_ORDER) if item["source"].startswith(s))


def main():
    concepts, assign = parse()
    items = all_items()
    app = [i for i in items if i["tier"] == "app"]
    archive = [i for i in items if i["tier"] == "archive"]
    missing = [i["sid"] for i in app if i["sid"] not in assign]
    assert not missing, f"unassigned app items, run tools/dedup.py pending: {missing[:5]}"

    # --- link archive items to attacks ---
    # ATT&CK no longer cites CAPEC; CAPEC cites ATT&CK, so invert it (sub-technique falls back to parent)
    t2slug = defaultdict(set)
    for i in app:
        for t in i["meta"].get("attack", []):
            t2slug[t].add(assign[i["sid"]])
    for a in archive:
        m, links = a["meta"], set()
        if a["sid"].startswith("H1:") and m.get("cwe") in assign:
            links.add(assign[m["cwe"]])
        elif a["sid"].startswith("PS:"):  # lab -> nearest assigned parent article
            parts = a["sid"][3:].split("/")[:-1]
            while parts and f"PS:{'/'.join(parts)}" not in assign:
                parts.pop()
            if parts:
                links.add(assign[f"PS:{'/'.join(parts)}"])
        else:  # ATT&CK technique -> attacks whose CAPEC entries map to it
            links |= t2slug.get(a["sid"]) or t2slug.get(a["sid"].split(".")[0], set())
        a["attacks"] = sorted(links)

    by_attack = defaultdict(list)
    for a in archive:
        for slug in a["attacks"]:
            by_attack[slug].append(a)
    sections = defaultdict(list)
    for i in app:
        sections[assign[i["sid"]]].append(i)

    # --- write index ---
    out_i, out_a = KB / "index", KB / "archive"
    for d in (out_i, out_a):
        shutil.rmtree(d, ignore_errors=True)
    (out_i / "attacks").mkdir(parents=True)
    out_a.mkdir()
    summary = []
    for slug, c in sorted(concepts.items(), key=lambda kv: kv[1]["order"]):
        secs = sorted(sections[slug], key=lambda i: (rank(i), i["sid"]))
        arch = sorted(by_attack[slug], key=lambda a: -a["meta"].get("upvotes", 0))
        popularity = sorted({p for s in secs for p in s["meta"].get("popularity", [])})
        h1 = sum(1 for a in arch if a["sid"].startswith("H1:"))
        words = sum(len(s["text"].split()) for s in secs)
        head = {**{k: c[k] for k in ("slug", "name", "kind", "tags")}, "popularity": popularity,
                "h1_reports": h1, "sources": dict(Counter(s["source"] for s in secs)), "words": words,
                "archive_count": len(arch)}
        page = {**head,
                "sections": [{k: s[k] for k in ("sid", "source", "title", "url", "text")} for s in secs],
                "archive_preview": [{"sid": a["sid"], "source": a["source"], "title": a["title"], "url": a["url"]}
                                    for a in arch[:ARCHIVE_PREVIEW]]}
        (out_i / "attacks" / f"{slug}.json").write_text(json.dumps(page, ensure_ascii=False))
        summary.append(head)
    (out_i / "attacks.json").write_text(json.dumps(summary, ensure_ascii=False))

    # --- write archive ---
    with open(out_a / "items.jsonl", "w") as fh:
        for a in archive:
            fh.write(json.dumps({k: a[k] for k in ("sid", "source", "title", "url", "text", "meta", "attacks")},
                                ensure_ascii=False) + "\n")

    size = lambda p: sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / 1e6
    print(f"index:   {len(summary)} attacks, {len(app)} sections, {size(out_i):.1f} MB")
    print(f"archive: {len(archive)} items ({sum(1 for a in archive if a['attacks'])} linked), {size(out_a):.1f} MB")
    return summary, archive


if __name__ == "__main__":
    summary, archive = main()
    # self-check: every attack has sections, key cross-source merges happened
    assert all(s["words"] > 0 for s in summary)
    page = json.loads((KB / "index/attacks/sqli.json").read_text())
    srcs = {s["source"] for s in page["sections"]}
    assert {"PortSwigger Web Security Academy", "OWASP Cheat Sheet Series", "MITRE CAPEC", "MITRE CWE"} <= srcs, srcs
    assert page["h1_reports"] > 100 and "CWE-Top25-2025" in page["popularity"]
    print("self-check ok")
