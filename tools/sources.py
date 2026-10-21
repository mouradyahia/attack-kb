"""Load every raw source as uniform items: {sid, source, title, url, text, tier, meta}.
tier "app"     -> blog-post-sized articles shown on attack pages (pushed to agents)
tier "archive" -> incidents, labs and ATT&CK techniques, pulled on demand only"""
import csv, json, re, sys
from pathlib import Path

csv.field_size_limit(sys.maxsize)
KB = Path(__file__).resolve().parent.parent
RAW = KB / "raw"

# PortSwigger pages that are site chrome, not attack content
PS_SKIP = {"", "all-labs", "all-materials", "all-topics", "certification", "credits", "getting-started",
           "learning-paths", "video-guidelines", "mystery-lab-challenge", "lab-telemetry-privacy-notice",
           "web-application-hackers-handbook", "essential-skills"}

# HackerOne weakness names that are not literal CWE names -> CWE id
H1_ALIASES = {
    "information disclosure": 200, "improper authentication - generic": 287,
    "improper access control - generic": 284, "privilege escalation": 269,
    "insecure direct object reference (idor)": 639, "open redirect": 601, "code injection": 94,
    "memory corruption - generic": 119, "sql injection": 89, "path traversal": 22,
    "command injection - generic": 77, "ui redressing (clickjacking)": 1021,
    "improper restriction of authentication attempts": 307, "privacy violation": 359,
    "http request smuggling": 444, "crlf injection": 93, "os command injection": 78,
    "classic buffer overflow": 120, "heap overflow": 122, "stack overflow": 121,
    "information exposure through an error message": 209, "xml external entities (xxe)": 611,
    "information exposure through directory listing": 548, "resource injection": 99,
    "information exposure through debug information": 215, "man-in-the-middle": 300,
    "integer overflow": 190, "information exposure through sent data": 201,
    "http response splitting": 113, "denial of service": 400, "remote file inclusion": 98,
    "array index underflow": 129, "forced browsing": 425, "missing required cryptographic step": 325,
    "file and directory information exposure": 538, "weak cryptography for passwords": 261,
}


def _mitre_field(s):
    """CWE/CAPEC CSV packs lists as '::KEY:val:KEY:val::' -> markdown bullets."""
    items = [x for x in (s or "").split("::") if x.strip()]
    out = []
    for it in items:
        parts = re.split(r"(?:^|:)(PHASE|STRATEGY|DESCRIPTION|EFFECTIVENESS|EFFECTIVENESS NOTES|METHOD|"
                         r"SCOPE|IMPACT|NOTE|LIKELIHOOD|STEP|TECHNIQUE|REFERENCE|CONTEXT|ORDINALITY):", it)
        if len(parts) == 1:
            out.append(f"- {it.strip()}")
            continue
        kv = dict(zip(parts[1::2], (p.strip() for p in parts[2::2])))
        head = " · ".join(kv[k] for k in ("STEP", "PHASE", "SCOPE", "METHOD", "STRATEGY", "IMPACT") if kv.get(k))
        body = kv.get("DESCRIPTION") or kv.get("NOTE") or ""
        tech = "".join(f"\n  - {kv['TECHNIQUE']}" for _ in [0] if kv.get("TECHNIQUE"))
        out.append(f"- **{head}**: {body}{tech}" if head else f"- {body}{tech}")
    return "\n".join(out)


def _sections(pairs):
    return "\n\n".join(f"### {k}\n{v.strip()}" for k, v in pairs if v and v.strip())


def cwe():
    pop = json.load(open(RAW / "mitre/cwe_popularity.json"))
    for r in csv.DictReader(open(RAW / "mitre/cwe.csv")):
        sid = f"CWE-{r['CWE-ID']}"
        text = _sections([
            ("Description", r["Description"]), ("Details", r["Extended Description"]),
            ("Consequences", _mitre_field(r["Common Consequences"])),
            ("Mitigations", _mitre_field(r["Potential Mitigations"])),
            ("Detection", _mitre_field(r["Detection Methods"]))])
        yield dict(sid=sid, source="MITRE CWE", title=r["Name"], tier="app", text=text,
                   url=f"https://cwe.mitre.org/data/definitions/{r['CWE-ID']}.html",
                   meta={"popularity": pop.get(sid, []), "status": r["Status"],
                         "capec": [f"CAPEC-{n}" for n in re.findall(r"::(\d+)", r["Related Attack Patterns"])]})


def capec():
    for r in csv.DictReader(open(RAW / "mitre/capec.csv", encoding="utf-8-sig")):
        if r["Status"] == "Deprecated":
            continue
        rid = r.get("'ID") or r.get("ID")
        text = _sections([
            ("Description", r["Description"]),
            ("Likelihood / severity", " / ".join(x for x in (r["Likelihood Of Attack"], r["Typical Severity"]) if x)),
            ("Prerequisites", _mitre_field(r["Prerequisites"])), ("Execution flow", _mitre_field(r["Execution Flow"])),
            ("Skills required", _mitre_field(r["Skills Required"])), ("Indicators", _mitre_field(r["Indicators"])),
            ("Consequences", _mitre_field(r["Consequences"])), ("Mitigations", _mitre_field(r["Mitigations"])),
            ("Examples", _mitre_field(r["Example Instances"]))])
        yield dict(sid=f"CAPEC-{rid}", source="MITRE CAPEC", title=r["Name"], tier="app", text=text,
                   url=f"https://capec.mitre.org/data/definitions/{rid}.html",
                   meta={"cwe": [f"CWE-{n}" for n in re.findall(r"::(\d+)", r["Related Weaknesses"])],
                         "attack": [f"T{n}" for n in re.findall(r"TAXONOMY NAME:ATTACK:ENTRY ID:([\d.]+)", r["Taxonomy Mappings"])]})


def _uncite(s):
    return re.sub(r"\(Citation: [^)]*\)", "", s or "").strip()


def attack():
    for t in json.load(open(RAW / "mitre/attack_techniques.json")):
        text = _sections([("Description", _uncite(t["description"])), ("Detection", _uncite(t["detection"]))])
        yield dict(sid=t["id"], source=f"MITRE ATT&CK ({t['domain']})", title=t["name"], tier="archive", text=text,
                   url=t["url"], meta={"tactics": t["tactics"], "platforms": t["platforms"], "capec": t["capec"]})


def owasp():
    for f in sorted((RAW / "owasp/cheatsheets").glob("*.md")):
        md = f.read_text()
        m = re.search(r"^#\s+(.+)$", md, re.M)
        yield dict(sid=f"OWASP:{f.stem}", source="OWASP Cheat Sheet Series",
                   title=m.group(1).strip() if m else f.stem.replace("_", " "), tier="app",
                   text=md[m.end():].strip() if m else md,
                   url=f"https://cheatsheetseries.owasp.org/cheatsheets/{f.stem}.html",
                   meta={"cwe": sorted(set(re.findall(r"CWE-\d+", md)))})


def portswigger():
    root = RAW / "portswigger/md"
    for f in sorted(root.rglob("*.md")):
        path = str(f.relative_to(root).with_suffix(""))
        parts = path.split("/")
        if (parts[1] if len(parts) > 1 else "") in PS_SKIP:
            continue
        md = f.read_text()
        m = re.search(r"^#\s+(.+)$", md, re.M)
        lab = parts[-1].startswith("lab-")
        yield dict(sid=f"PS:{'/'.join(parts[1:])}", source="PortSwigger Web Security Academy",
                   title=m.group(1).strip() if m else parts[-1], tier="archive" if lab else "app",
                   text=md[m.end():].strip() if m else md, url=f"https://portswigger.net/{path}",
                   meta={"topic": parts[1], "kind": "lab" if lab else "article"})


def hackerone(cwe_names):
    for r in csv.DictReader(open(RAW / "hackerone/reports.csv")):
        v = r["vuln_type"].lower()
        cid = cwe_names.get(v) or (f"CWE-{H1_ALIASES[v]}" if v in H1_ALIASES else None)
        if not cid and v.startswith("cross-site scripting (xss)"):
            cid = "CWE-79"
        yield dict(sid="H1:" + r["link"].rsplit("/", 1)[-1], source="HackerOne disclosed report", title=r["title"],
                   tier="archive", text="", url="https://" + r["link"],
                   meta={"program": r["program"], "vuln_type": r["vuln_type"], "upvotes": int(r["upvotes"] or 0),
                         "bounty": float(r["bounty"] or 0), "cwe": cid})


def all_items():
    items = [*cwe(), *capec(), *attack(), *owasp(), *portswigger()]
    names = {i["title"].lower(): i["sid"] for i in items if i["source"] == "MITRE CWE"}
    return items + list(hackerone(names))
