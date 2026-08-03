#!/usr/bin/env python3
"""Recover the Sentinel Ultra Hub's collapsible panels into docs/hub-scrape/.

The hub is a client-side React app: the HTML scrape captures `<details>` panels as
empty headers, so the Guidelines tables (environment fixes, git fixes, oracle rules,
verifiability) never made it into guide.txt. The prose lives in the app bundle, which
is served without auth — the email gate is enforced in JS.

Usage:
    python3 scripts/fetch-hub-panels.py [--bundle PATH] [--out PATH]

Code blocks come through lossy (JSX strips them to concatenated fragments); prose and
tables are faithful. Cross-check anything surprising against the live site.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

HUB = "https://snorkel-ai.github.io/Sentinel_Ultra_Hub/"
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "docs" / "hub-scrape" / "guide-panels.txt"

TAG_PREFIX = {
    "summary": "\n\n## ",
    "h2": "\n\n# ",
    "h3": "\n\n## ",
    "h4": "\n\n### ",
    "li": "\n- ",
    "p": "\n\n",
    "tr": "\n",
    "td": " | ",
    "th": " | ",
    "table": "\n",
    "div": "\n",
    "pre": "\n\n",
    "br": "\n",
    "ul": "\n",
    "ol": "\n",
}

SKIP_ATTRS = {
    "className", "id", "href", "src", "alt", "target", "rel", "style",
    "key", "type", "name", "htmlFor", "width", "height", "aria-hidden",
}

TOKEN = re.compile(
    r'c\.jsxs?\("(?P<tag>[a-zA-Z0-9]+)"'
    r'|(?:(?P<attr>[A-Za-z_$][\w$]*)\s*:\s*)?"(?P<dstr>(?:[^"\\]|\\.)*)"'
    r"|(?:(?P<attr2>[A-Za-z_$][\w$]*)\s*:\s*)?'(?P<sstr>(?:[^'\\]|\\.)*)'"
)


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def bundle_url() -> str:
    index = fetch(HUB)
    m = re.search(r'src="([^"]*assets/index-[^"]*\.js)"', index)
    if not m:
        raise SystemExit("could not find the app bundle in the hub index page")
    return urllib.parse.urljoin(HUB, m.group(1))


def match_call(text: str, start: int) -> str:
    """Return the full `c.jsx(...)` call beginning at `start`, respecting strings."""
    i = text.index("(", start)
    depth = 0
    quote = None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'`":
            quote = ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
    return text[start:]


def unescape(s: str) -> str:
    for a, b in (("\\n", "\n"), ("\\t", "\t"), ('\\"', '"'), ("\\'", "'"), ("\\\\", "\\")):
        s = s.replace(a, b)
    return s


def to_text(chunk: str) -> str:
    out: list[str] = []
    for m in TOKEN.finditer(chunk):
        if tag := m.group("tag"):
            out.append(TAG_PREFIX.get(tag, ""))
            continue
        attr = m.group("attr") or m.group("attr2")
        s = m.group("dstr")
        if s is None:
            s = m.group("sstr")
        if s is None or attr in SKIP_ATTRS:
            continue
        s = unescape(s)
        if s.strip():
            out.append(s)
    text = "".join(out)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n \|", "\n|", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, help="use a local bundle copy instead of fetching")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if args.bundle:
        src = args.bundle.read_text(encoding="utf-8", errors="replace")
        origin = str(args.bundle)
    else:
        url = bundle_url()
        src = fetch(url)
        origin = url

    panels: list[tuple[str, str]] = []
    seen: set[str] = set()
    for m in re.finditer(r'c\.jsxs?\("details",\{className:"accordion"', src):
        call = match_call(src, m.start())
        pid = re.search(r'id:"([^"]+)"', call[:200])
        text = to_text(call)
        if not text or text in seen:
            continue
        seen.add(text)
        panels.append((pid.group(1) if pid else "unknown", text))

    if not panels:
        print("ERROR: no accordion panels found — the bundle format changed", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        fh.write("Sentinel Ultra Hub — collapsible panels\n\n")
        fh.write(f"Extracted {dt.date.today().isoformat()} from {origin}\n")
        fh.write("via scripts/fetch-hub-panels.py.\n\n")
        fh.write("The HTML scrape in guide.txt records these <details> sections as empty\n")
        fh.write("headers, so this file is the only local source for the environment,\n")
        fh.write("git, oracle, and verifiability tables. Prose and tables are faithful;\n")
        fh.write("fenced code blocks come through lossy.\n")
        for pid, text in panels:
            fh.write(f"\n\n{'=' * 78}\n[panel: {pid}]\n{'=' * 78}\n\n{text}\n")

    print(f"Wrote {args.out} ({len(panels)} panels)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
