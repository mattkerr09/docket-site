#!/usr/bin/env python3
"""No page links a sibling domain, except /about/.

WHY. outlier.host's Bing impressions went from 45-89 a day to 8 on 2026-09-15
and then 0, within a day of a block of links to every sibling domain reaching
171 of its pages (CEO, 2026-10-13). Bing reads sitewide links between commonly
owned sites as a link scheme, and Bing feeds ChatGPT search. This site carried
the same block in its footer on all 155 pages until that date.

The footer keeps one off-site link, to kerrandcompanyholdings.com, which is the
company that takes the payment. Every other domain we own is named in plain text
or not at all, and linked only from /about/.

What counts as a link: any absolute URL (http, https or protocol-relative) whose
host is a sibling domain or a subdomain of one, anywhere in a built text file:
href, src, content, JSON-LD, llms.txt, sitemaps. Plain text such as the name of
a site is not a link and passes.

Refuses when such a URL appears in any built file other than site/about/index.html.

--self-test plants a sibling link into a copy of a built page and requires the
gate to refuse it, then plants one into /about/ and requires it to pass, then
requires the real site to pass.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

#: Every domain of ours that is not this site and not the company site. The
#: company site is the one link the footer is allowed to carry.
SIBLINGS = (
    "outlier.host",
    "crispvideo.app",
    "adplaybook.app",
    "bookbreaker.bet",
    "builtbykerr.com",
    "matthewkerr.dev",
)
ALLOWED_PAGES = ("about/index.html",)
TEXT_SUFFIXES = {".html", ".txt", ".xml", ".json", ".js", ".css", ".md", ".webmanifest"}

_HOSTS = "|".join(re.escape(h) for h in SIBLINGS)
#: A URL whose host is a sibling, or a subdomain of one. The host has to end at
#: a port, a path, a query, a fragment, a quote, a space or the end, so
#: "builtbykerr.community" is not a match.
_LINK = re.compile(
    r"(?:https?:)?//(?:[a-z0-9-]+\.)*(" + _HOSTS + r")(?=[:/?#\"'\s<>)\]]|$)", re.I)


def offenders(files: dict[str, str]) -> list[tuple[str, str]]:
    """[(relative path, sibling host)] for every disallowed link."""
    out = []
    for rel, text in sorted(files.items()):
        if rel in ALLOWED_PAGES:
            continue
        for host in sorted({m.group(1).lower() for m in _LINK.finditer(text)}):
            out.append((rel, host))
    return out


def read_site() -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(SITE.rglob("*")):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            files[path.relative_to(SITE).as_posix()] = path.read_text(
                encoding="utf-8", errors="ignore")
    return files


def report(found: list[tuple[str, str]]) -> None:
    print(f"  {len(found)} sibling-domain link(s) outside /about/:")
    for rel, host in found[:25]:
        print(f"    {rel}  ->  {host}")
    if len(found) > 25:
        print(f"    ... and {len(found) - 25} more")
    print("  Bing reads sitewide links between commonly owned sites as a link scheme.")
    print("  Name the site in plain text, or link it from /about/ only.")


def self_test() -> int:
    """Plant links into a clean synthetic page, so the real site's state cannot
    make a planted link look refused (or a refusal look like a pass)."""
    clean = {"x/index.html": "<p>Made by <a href=\"https://kerrandcompanyholdings.com/\">K</a></p>",
             "about/index.html": "<p>about</p>"}
    if offenders(clean):
        print("FAIL  self-test: the company link was refused")
        return 1
    for host in SIBLINGS:
        for form in (f'<a href="https://{host}/">x</a>', f'<a href="//www.{host}/p">x</a>',
                     f"https://{host}", f'{{"url":"http://app.{host}:8080/"}}'):
            planted = dict(clean, **{"x/index.html": clean["x/index.html"] + form})
            if ("x/index.html", host) not in offenders(planted):
                print(f"FAIL  self-test: {form!r} was not refused")
                return 1
    near = dict(clean, **{"x/index.html": clean["x/index.html"]
                          + '<a href="https://builtbykerr.community/">x</a> built by builtbykerr.com'})
    if offenders(near):
        print("FAIL  self-test: a lookalike host or a plain-text name was refused")
        return 1
    ok = dict(clean, **{"about/index.html": '<a href="https://outlier.host/">x</a>'})
    if offenders(ok):
        print("FAIL  self-test: a link on /about/ was refused")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    files = read_site()
    if not files:
        print("FAIL  no built site to check; run scripts/build.py first")
        return 1
    if args.self_test and self_test():
        return 1
    found = offenders(files)
    if found:
        print("FAIL  sibling-domain links on the built site")
        report(found)
        return 1
    print(f"  ok: no sibling-domain link outside /about/ across {len(files)} built files"
          + (" (self-test passed)" if args.self_test else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
