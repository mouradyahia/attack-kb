#!/usr/bin/env python3
"""Attack knowledge base: web UI + JSON/markdown API. Stdlib only.
  python3 server.py [port]      (default 8765)   then open http://localhost:8765
Index (push: agents loop over it)       Archive (pull: fetch only when needed)
  GET /api/attacks[?q=&tag=&kind=]        GET /api/archive?q=&attack=&source=&limit=&offset=
  GET /api/attacks/<slug>                 GET /api/archive/<sid>
  GET /api/attacks/<slug>.md"""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

KB = Path(__file__).resolve().parent
ATTACKS = json.loads((KB / "index/attacks.json").read_text())
SLUGS = {a["slug"] for a in ATTACKS}
ARCHIVE = [json.loads(l) for l in open(KB / "archive/items.jsonl")]
BY_SID = {a["sid"]: a for a in ARCHIVE}

API_DOC = {
    "about": "Deduplicated attack index (CWE, CAPEC, OWASP cheat sheets, PortSwigger). "
             "Index = push: loop over /api/attacks and read each page. Archive = pull: HackerOne incidents, "
             "PortSwigger labs, MITRE ATT&CK; query only when an attack page is not enough.",
    "index": {"GET /api/attacks": "list; filters q (name words), tag, kind=attack|guide",
              "GET /api/attacks/<slug>": "full page JSON: sections[{sid,source,title,url,text}], archive_preview",
              "GET /api/attacks/<slug>.md": "same page as markdown (best for LLM agents)"},
    "archive": {"GET /api/archive": "search; q (words in title/text), attack=<slug>, source prefix, limit<=200, offset",
                "GET /api/archive/<sid>": "one archive item with full text"},
    "tags": sorted({t for a in ATTACKS for t in a["tags"]}),
}


def words(q):
    return [w for w in (q or "").lower().split() if w]


def page(slug):
    return json.loads((KB / "index/attacks" / f"{slug}.json").read_text())


def page_md(p):
    out = [f"# {p['name']}", "",
           f"- slug: `{p['slug']}` · kind: {p['kind']} · tags: {', '.join(p['tags'])}",
           f"- popularity: {', '.join(p['popularity']) or 'none'} · HackerOne reports: {p['h1_reports']}", ""]
    for s in p["sections"]:
        out += [f"## [{s['source']}] {s['title']}", f"<{s['url']}> · `{s['sid']}`", "", s["text"], ""]
    out += [f"## Archive (pull on demand): {p['archive_count']} items",
            f"Query: `GET /api/archive?attack={p['slug']}` · item: `GET /api/archive/<sid>`", ""]
    out += [f"- `{a['sid']}` {a['title']} <{a['url']}>" for a in p["archive_preview"]]
    return "\n".join(out) + "\n"


def search_archive(qs):
    q, attack, source = words(qs.get("q", [""])[0]), qs.get("attack", [""])[0], qs.get("source", [""])[0].lower()
    limit = min(int(qs.get("limit", ["50"])[0]), 200)
    offset = int(qs.get("offset", ["0"])[0])
    hits = [a for a in ARCHIVE
            if (not attack or attack in a["attacks"])
            and (not source or a["source"].lower().startswith(source))
            and all(w in (a["title"] + " " + a["text"]).lower() for w in q)]
    hits.sort(key=lambda a: -a["meta"].get("upvotes", 0))
    return {"total": len(hits), "offset": offset,
            "items": [{k: a[k] for k in ("sid", "source", "title", "url", "attacks")} | {"meta": a["meta"]}
                      for a in hits[offset:offset + limit]]}


class Handler(BaseHTTPRequestHandler):
    def send(self, body, ctype="application/json", code=200):
        data = body if isinstance(body, bytes) else (
            body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)).encode()
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        path, qs = unquote(u.path), parse_qs(u.query)
        if path in ("/", "/index.html"):
            return self.send((KB / "web/index.html").read_bytes(), "text/html")
        if path == "/api":
            return self.send(API_DOC)
        if path == "/api/attacks":
            q, tag, kind = words(qs.get("q", [""])[0]), qs.get("tag", [""])[0], qs.get("kind", [""])[0]
            return self.send([a for a in ATTACKS if (not tag or tag in a["tags"]) and (not kind or a["kind"] == kind)
                              and all(w in a["name"].lower() or w in a["slug"] for w in q)])
        if path.startswith("/api/attacks/"):
            slug = path[len("/api/attacks/"):]
            md = slug.endswith(".md")
            slug = slug.removesuffix(".md")
            if slug not in SLUGS:  # whitelist: slug also names a file
                return self.send({"error": "unknown attack"}, code=404)
            p = page(slug)
            return self.send(page_md(p), "text/markdown") if md else self.send(p)
        if path == "/api/archive":
            return self.send(search_archive(qs))
        if path.startswith("/api/archive/"):
            item = BY_SID.get(path[len("/api/archive/"):])
            return self.send(item) if item else self.send({"error": "unknown sid"}, code=404)
        self.send({"error": "not found", "see": "/api"}, code=404)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    print(f"http://localhost:{port}  ({len(ATTACKS)} attacks, {len(ARCHIVE)} archive items)")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
