"""Build-time product identity and the installed-app URL exceptions.

The default below is the cutover line: an unset SITE_BRAND builds the Check Engine
identity, and SITE_BRAND=docket still builds the old one. Brand selection does not
rewrite build-id input files.
"""
from __future__ import annotations

from html import escape
from html.parser import HTMLParser
import json
import os
import re
from urllib.parse import urlsplit, urlunsplit


BRANDS = {
    "docket": {
        "NAME": "Docket SEO", "SHORT": "Docket", "HOST": "docketseo.app",
        "CLI": "docket", "TAGLINE": "Docket SEO: SEO audit for Mac and Windows",
        "FORMERLY": "", "STORE_NOTE": "",
    },
    "checkengine": {
        "NAME": "Check Engine SEO", "SHORT": "Check Engine", "HOST": "checkengineseo.com",
        "CLI": "checkengine", "TAGLINE": "Check Engine: SEO audit for Mac and Windows",
        "FORMERLY": "formerly Docket SEO",
        # The Microsoft Store listing keeps its old name (CEO decision 2026-11-09), so say so where the site mentions the Store.
        "STORE_NOTE": ", listed there as Docket SEO",
    },
}
SITE_BRAND = os.environ.get("SITE_BRAND", "checkengine")
if SITE_BRAND not in BRANDS:
    raise ValueError(f"Unknown SITE_BRAND {SITE_BRAND!r}. Choose docket or checkengine.")

NAME = BRANDS[SITE_BRAND]["NAME"]
SHORT = BRANDS[SITE_BRAND]["SHORT"]
HOST = BRANDS[SITE_BRAND]["HOST"]
BASE = "https://" + HOST
CLI = BRANDS[SITE_BRAND]["CLI"]
TAGLINE = BRANDS[SITE_BRAND]["TAGLINE"]
FORMERLY = BRANDS[SITE_BRAND]["FORMERLY"]
STORE_NOTE = BRANDS[SITE_BRAND]["STORE_NOTE"]
LASTMOD_FILE = "page-lastmod.json" if SITE_BRAND == "docket" else "page-lastmod-checkengine.json"
LEGACY_HOST = BRANDS["docket"]["HOST"]
LEGACY_BASE = "https://" + LEGACY_HOST
FORMER_ADDRESS_DESCRIPTION = "this site's address until November 2026"
FORMER_ADDRESS_NOTE = f" ({FORMER_ADDRESS_DESCRIPTION})" if SITE_BRAND == "checkengine" else ""
FORMER_ADDRESS_SENTENCE = (f" The host was {FORMER_ADDRESS_DESCRIPTION}."
                           if SITE_BRAND == "checkengine" else "")
MACHINE_PATHS = ("/updater.json", "/offer.json", "/data/knowledge.json", "/bot/")


def is_machine_path(path: str) -> bool:
    return (path in MACHINE_PATHS or path == "/bot" or path.startswith("/bot/")
            or path == "/assets/docket-sample-report.pdf"
            or path.startswith("/updates/"))  # the updater mirror: installed copies fetch these from the old host


def site_url(value: str, *, page: bool = False) -> str:
    """Move only this site's URLs. Installed-app endpoints stay on the old host."""
    if SITE_BRAND == "docket":
        return value
    if value.startswith("/") and not value.startswith("//"):
        if page:
            return BASE + value
        return LEGACY_BASE + value if is_machine_path(urlsplit(value).path) else value
    parsed = urlsplit(value)
    if parsed.netloc not in (LEGACY_HOST, HOST):
        return value
    host = LEGACY_HOST if is_machine_path(parsed.path) and not page else HOST
    return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))


#: Machine paths that a person also clicks: the crawler's page and the sample report. A link a reader follows goes to this
#: site's own host (asked by the Quality Desk, 10 Nov 2026); installed apps, feeds and user-agent strings keep the old host.
READER_PATHS = ("/bot", "/bot/", "/assets/docket-sample-report.pdf")


def _reader_page(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.path in READER_PATHS and parsed.netloc in ("", LEGACY_HOST, HOST)


def machine_link(path: str) -> str:
    """Keep the original code label by default and link the retained feed after rename."""
    label = LEGACY_HOST + path
    if SITE_BRAND == "docket":
        return label
    return f'<a href="{LEGACY_BASE}{path}">{label}</a>'


# Protect URLs, addresses, paths and filenames before changing product words.
# The URL callback still moves our own prose links, using the same exceptions.
_LITERAL = re.compile(
    r"(?:https?://|//)[^\s<>\"'`]+"
    r"|[\w.+-]+@[\w.-]+"
    r"|(?:[A-Za-z]:\\|[~/%]|[\w.-]+/)[^\s<>\"'`]+"
    r"|\b[\w.-]*[Dd]ocket[\w.-]*\.[\w.-]+"
    r"|\blisted there as Docket SEO\b"
    # The crawler's robots.txt product token is what it sends, so a rename must not touch it.
    r"|\bDocket-SEO-Audit(?:-Survey)?\b"
    r"|\bmcp\.docketseo\.app\b"
    r"|\bdocketseo\.app(?:/[^\s<>\"'`]*)?"
)
_COMMAND = re.compile(r"(?<![\w./\\-])docket(?=\s+(?:audit|diff|logs|attack|backlinks|checks|serve|mcp|licence|version)\b)")


def text(value: str, *, historical: bool = False) -> str:
    """Brand prose and command examples, preserving technical literals."""
    if SITE_BRAND == "docket":
        return value
    literals = []

    def protect(match):
        literal = match.group()
        suffix = literal[len(literal.rstrip(".,;:!?)]}")):]
        literal = literal[:len(literal) - len(suffix)] if suffix else literal
        if not historical and literal.startswith(LEGACY_HOST):
            literal = site_url("https://" + literal).removeprefix("https://")
        elif not historical and literal.startswith(("http://", "https://", "//")):
            literal = site_url(literal)
        literals.append(literal + suffix)
        return f"\x00{len(literals) - 1}\x00"

    value = _LITERAL.sub(protect, value)
    value = re.sub(r"\bDocket SEO\b", NAME, value)
    value = re.sub(r"\bDocket\b", SHORT, value)
    if not historical:
        value = _COMMAND.sub(CLI, value)
    value = re.sub(r"\ban (?=Check Engine\b)", "a ", value)
    value = re.sub(r"\bAn (?=Check Engine\b)", "A ", value)
    return re.sub(r"\x00(\d+)\x00", lambda m: literals[int(m[1])], value)


def _json_strings(value, key=""):
    if isinstance(value, dict):
        return {key: _json_strings(item, key) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_strings(item, key) for item in value]
    if isinstance(value, str) and key in {"url", "@id", "mainEntityOfPage"}:
        return site_url(value, page=True)
    return text(value) if isinstance(value, str) else value


class _BrandHTML(HTMLParser):
    """Preserve original markup and entities, editing only text and known attributes."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts = []
        self.raw_tag = ""
        self.json_ld = False
        # Source elements marked data-brand-history keep recorded hosts and CLI
        # commands. Product words still follow the selected brand. Markers also
        # preserve recorded hosts in image and video labels.
        self.elements = []

    def historical(self):
        return bool(self.elements and self.elements[-1][1])

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        raw = self.get_starttag_text()
        historical = self.historical() or "data-brand-history" in attributes

        def attribute(match):
            name, before, quote, value = match.groups()
            key = name.lower()
            if key in {"href", "src", "action", "poster"}:
                reader = tag == "a" and key == "href" and _reader_page(value)
                if reader and value.startswith("/") and not value.startswith("//"):
                    pass  # a root-relative link a reader follows already means this site's own host
                else:
                    value = site_url(value, page=(tag == "link" and attributes.get("rel") == "canonical") or reader)
            elif key in {"title", "alt", "aria-label", "placeholder"}:
                value = text(value, historical=historical)
            elif tag == "meta" and key == "content":
                if attributes.get("property") in {"og:url", "og:image"} or attributes.get("name") == "twitter:image":
                    value = site_url(value, page=attributes.get("property") == "og:url")
                elif attributes.get("name") in {"description", "twitter:title", "twitter:description"} or attributes.get("property") in {"og:title", "og:description", "og:site_name"}:
                    value = text(value, historical=historical)
            return name + before + quote + value + quote

        raw = re.sub(r"([\w:-]+)(\s*=\s*)([\"'])(.*?)\3", attribute, raw, flags=re.S)
        self.parts.append(raw)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
                       "meta", "param", "source", "track", "wbr"}:
            self.elements.append((tag, historical))
        if tag in {"script", "style"}:
            self.raw_tag = tag
            self.json_ld = tag == "script" and attributes.get("type") == "application/ld+json"

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.elements and self.elements[-1][0] == tag:
            self.elements.pop()

    def handle_endtag(self, tag):
        self.parts.append(f"</{tag}>")
        for index in range(len(self.elements) - 1, -1, -1):
            if self.elements[index][0] == tag:
                del self.elements[index:]
                break
        if tag == self.raw_tag:
            self.raw_tag = ""
            self.json_ld = False

    def handle_data(self, data):
        if self.json_ld:
            data = json.dumps(_json_strings(json.loads(data)), ensure_ascii=False).replace("</", "<\\/")
        elif not self.raw_tag:
            data = text(data, historical=self.historical())
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.parts.append(f"<!{decl}>")


def html(value: str) -> str:
    if SITE_BRAND == "docket":
        return value
    parser = _BrandHTML()
    parser.feed(value)
    parser.close()
    return "".join(parser.parts)


def formerly_note() -> str:
    return f'<p class="hero-note">{escape(FORMERLY)}</p>' if FORMERLY else ""


def worker_module() -> str:
    """The checker's build input, generated from this same identity."""
    values = {"SITE_BRAND": SITE_BRAND, "NAME": NAME, "HOST": HOST, "BASE": BASE}
    return ("// Generated from scripts/brand.py by scripts/build.py.\n"
            + "".join(f"export const {key} = {json.dumps(value)}\n" for key, value in values.items()))
