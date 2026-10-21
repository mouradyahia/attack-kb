#!/usr/bin/env python3
"""Convert mirrored PortSwigger Web Security Academy HTML (raw/portswigger/pages) to markdown
(raw/portswigger/md). One-off: after conversion the HTML is deleted."""
import html, re, sys
from html.parser import HTMLParser
from pathlib import Path

SKIP = {"nav", "script", "style", "svg", "form", "button", "label", "input"}
BLOCK = {"p": "\n\n", "h1": "\n\n# ", "h2": "\n\n## ", "h3": "\n\n### ", "h4": "\n\n#### ",
         "li": "\n- ", "br": "\n", "tr": "\n", "div": "\n"}


class MD(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.pre = [], 0, 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
        elif not self.skip:
            if tag == "pre" or ("class", "code-scrollable") in attrs:
                self.pre += 1
                self.out.append("\n\n```\n")
            elif tag == "code" and not self.pre:
                self.out.append("`")
            elif tag in BLOCK:
                self.out.append(BLOCK[tag])

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
        elif not self.skip:
            if tag == "pre" or (tag == "code" and self.pre):
                if self.pre:
                    self.pre -= 1
                    self.out.append("\n```\n\n")
            elif tag == "code":
                self.out.append("`")

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d if self.pre else re.sub(r"\s+", " ", d))


def convert(h):
    m = re.search(r"<main>(.*)</main>", h, re.S)
    p = MD()
    p.feed(m.group(1) if m else "")
    t = "".join(p.out)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n(- )?\s*\n(\s*\n)+", "\n\n", t)
    t = t[t.find("# "):] if "# " in t else t  # drop breadcrumb
    t = re.sub(r"\n#### Read more\n(?:- [^\n]*\n?)*", "\n", t)  # link lists, appear mid-page too
    t = re.split(r"\n#### Find [^\n]* using Burp Suite", t)[0]  # trailing Burp ad
    return re.sub(r"\n +", "\n", t).strip() + "\n"


if __name__ == "__main__":
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    for f in src.rglob("*.html"):
        rel = f.relative_to(src).with_suffix(".md")
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        (dst / rel).write_text(convert(f.read_text(errors="ignore")))
