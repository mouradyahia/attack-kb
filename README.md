# Attack KB

A deduplicated catalog of attacks: one entry per attack, with every source's text about it as sections. It's built for checking an app against each attack, one at a time.

```
python3 server.py            # http://localhost:8765  (UI + API, stdlib only)
python3 tools/build.py       # rebuild index/ and archive/ after changing raw/ or dedup/
```

## Two tiers, kept separate

| | **Index** (`index/`, ~7 MB) | **Archive** (`archive/`, ~7 MB) |
|---|---|---|
| What | 136 attacks (plus guides), each with blog-length sections from CWE, CAPEC, OWASP cheat sheets and PortSwigger articles | 14,972 HackerOne reports, 270 PortSwigger labs, 918 MITRE ATT&CK techniques |
| How agents use it | **Push**: loop over `/api/attacks` and read each page | **Pull**: query only when a page isn't enough |
| API | `GET /api/attacks[?tag=&kind=&q=]` · `GET /api/attacks/<slug>` · `GET /api/attacks/<slug>.md` | `GET /api/archive?q=&attack=&source=&limit=&offset=` · `GET /api/archive/<sid>` |

`GET /api` describes all of this as JSON. For an audit, skip `kind=guide`, and use tags (`web api auth mobile infra …`) to drop attacks that can't apply to your app (`hardware`, `ics`, `lowlevel`).

## Layout
- `raw/`: source text, 14 MB (CWE/CAPEC CSV, trimmed ATT&CK JSON, cheat-sheet and PortSwigger markdown, HackerOne CSV).
- `dedup/decisions.txt`: the semantic deduplication log, built from titles only. It's append-only and processed top to bottom: `+slug | name | kind | tags :: ids` creates an attack, `slug :: ids` adds items to one.
- `tools/sources.py`: loads every source as `{sid, source, title, url, text, tier}`.
- `tools/dedup.py check|set|pending PREFIX`: validates the log and lists items not yet filed.
- `tools/build.py`: writes `index/` and `archive/`. Archive items are linked to attacks by CWE (HackerOne), parent article (labs) or CAPEC→ATT&CK mapping.
- `web/index.html`: the UI. Markdown is rendered through DOMPurify (loaded from a CDN); offline it falls back to plain text.

## Adding a source
Add a loader to `sources.py`, run `tools/dedup.py pending <PREFIX>`, add decisions for each title (new attack or existing slug), then run `tools/build.py`.
