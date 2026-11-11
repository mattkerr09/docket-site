#!/usr/bin/env python3
"""Offline rename regression gate. All builds write into temporary repo copies.

Brand images use DOCKET_SKIP_BRAND_ASSETS=1. The baseline gets the identical
skip at its renderer entry point because main predates that flag. No browser,
network, installed binary or real build-id anchor is used by this test.
"""
from __future__ import annotations

import ast
import csv
import datetime
import hashlib
import html
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent


def vs_run_phrase():
    # The SE Ranking page's recorded audit of our own (old) host. Derived from the run's data, so a re-recording moves it.
    run = json.loads((ROOT / "data/vs-run.json").read_text())
    day = datetime.date.fromisoformat(run["date"])
    return f"real audit of docketseo.app on {day.day} {day.strftime('%B %Y')}: {run['pages']} pages"
SAMPLES = ("index.html", "download/index.html", "vs/screaming-frog-alternative/index.html",
           "learn/seo-audit/index.html", "ai-assistants/index.html",
           "how-to/write-title-tags-that-fit/index.html", "legal/privacy/index.html",
           "about/index.html", "for/developers/index.html")
NEW_HOST = "checkengineseo.com"
OLD_HOST = "docketseo.app"
MACHINE = ("/updater.json", "/offer.json", "/data/knowledge.json", "/bot/",
           "/assets/docket-sample-report.pdf")


class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.words = []
        self.tags = []
        self.json_ld = []
        self.hidden = ""
        self.is_json = False
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag in {"script", "style"}:
            self.hidden = tag
            self.is_json = attrs.get("type") == "application/ld+json"
        for key in ("title", "alt", "aria-label"):
            if key in attrs:
                self.words.append(attrs[key])
        if tag == "meta" and (attrs.get("name") in {"description", "twitter:title", "twitter:description"}
                              or attrs.get("property") in {"og:title", "og:description", "og:site_name"}):
            self.words.append(attrs.get("content", ""))

    def handle_endtag(self, tag):
        if tag == self.hidden:
            self.hidden = ""
            self.is_json = False

    def handle_data(self, data):
        if self.is_json:
            self.json_ld.append(json.loads(data))
        elif not self.hidden:
            self.words.append(data)


def json_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from json_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from json_values(item)
    elif isinstance(value, str):
        yield value


def words(raw):
    value = " ".join(" ".join(Page(raw).words).split())
    return re.sub(r"\s+([.,:;!?])", r"\1", value)


def check_history(site):
    historical = {
        "contact": ("advertised, docketseo.app had none.", "docketseo.app now has MX records"),
        "learn/dead-contact-address": ("docketseo.app carried hello@docketseo.app",),
        "how-to/fix-missing-security-headers": (
            "security.no_http_redirect http://docketseo.app does not redirect",
            "$ curl -sI http://docketseo.app/ HTTP/1.1 200 OK Server: GitHub.com"),
        "how-to/redirect-http-to-https": ("audited docketseo.app",),
        "how-to/outrank-a-bigger-competitor": (
            "$ docket attack https://docketseo.app https://www.screamingfrog.co.uk/seo-spider/",
            "you: docketseo.app was not found"),
        "vs/se-ranking-vs-screaming-frog": (
            vs_run_phrase(),),
        "learn/ai-substitution": ("Run against docketseo.app it assessed",),
        "learn/internal-link-equity": ("crawled docketseo.app, built the internal link graph",),
        "how-to/sitemap-urls-that-are-not-stale": ("Auditing docketseo.app, the host answered",),
    }
    # The AI assistants run was re-measured on 10 Nov 2026 against the new host, so it reads as this site, not as history.
    assistants = words((site / "ai-assistants" / "index.html").read_text())
    assert "audit checkengineseo.com, this site." in assistants
    assert "this site's address until November 2026" not in assistants
    for route, phrases in historical.items():
        raw = (site / route / "index.html").read_text()
        for phrase in phrases:
            assert phrase in words(raw), (route, phrase)
        assert f'href="https://{NEW_HOST}/{route}/"' in raw, route

    # These describe today's file and site, rather than a recorded audit.
    llms_page = (site / "learn/what-is-llms-txt/index.html").read_text()
    assert f'<a href="/llms.txt">{NEW_HOST}/llms.txt</a>' in llms_page
    substitution = words((site / "learn/ai-substitution/index.html").read_text())
    assert f"On {NEW_HOST} it is the defence holding most of the site up." in substitution
    assistants = words((site / "ai-assistants/index.html").read_text())
    assert f"Check {NEW_HOST}/pricing/ for SEO problems" in assistants
    for route in ("vs/ahrefs-site-audit-alternative", "vs/seoptimer-alternative"):
        assert "after auditing docketseo.app:" in words((site / route / "index.html").read_text())
    home = Page((site / "index.html").read_text())
    assert "auditing this site, recorded" not in " ".join(home.words)
    descriptions = [attrs.get("alt", attrs.get("aria-label", "")) for tag, attrs in home.tags
                    if tag in {"img", "video"}]
    recorded = [value for value in descriptions if OLD_HOST in value]
    assert len(recorded) == 3, recorded
    assert not any(NEW_HOST in value for value in descriptions)
    card = words((site / "score-card/index.html").read_text())
    assert "a short link to the score card page at the foot" in card


def check_home_knowledge(site):
    raw = (site / "index.html").read_text()
    sentence = "The knowledge refresh fetches docketseo.app/data/knowledge.json."
    assert sentence in words(raw)
    faq = next(block for block in Page(raw).json_ld if block.get("@type") == "FAQPage")
    answer = next(item["acceptedAnswer"]["text"] for item in faq["mainEntity"]
                  if "send my site data" in item["name"])
    assert sentence in answer
    assert "refresh from this site" not in answer
    for route in ("download", "about"):
        assert "crawler knowledge file from docketseo.app/data/knowledge.json" in words(
            (site / route / "index.html").read_text())


def check_cli_context(site):
    for route in ("download", "for/developers"):
        raw = (site / route / "index.html").read_text()
        assert "command still works as an alias" not in raw, route
        alias = '<code>checkengine</code> (the old name, <code>docket</code>, still works)'
        assert raw.count(alias) == 1, route
        # Download introduces the CLI in its command-line section. Developers starts with it.
        if route == "for/developers":
            assert alias in re.search(r'<p class="lede">.*?</p>', raw, re.S)[0]
        else:
            assert f"The same engine ships as a CLI, {alias}, inside the app bundle." in raw
            body = raw[raw.index('<main id="main">'):]
            paragraphs = re.findall(r"<p\b[^>]*>.*?</p>", body, re.S)
            first_cli = next(paragraph for paragraph in paragraphs if "CLI" in words(paragraph))
            assert alias in first_cli


def check_favicon_copy(site, name):
    favicon = (site / "how-to/fix-favicon-not-showing-in-search/index.html").read_text()
    assert "<h2>What the audit checks</h2>" in favicon
    assert "<p>The tool opens your home page" in favicon
    broken_links = (site / "how-to/fix-broken-outbound-links/index.html").read_text()
    assert "Does the audit check every outbound link on my site?" in words(broken_links)
    assert name in words(favicon)


def check_kept_slugs(site, name):
    routes = {"/learn/what-docket-got-wrong/", "/learn/what-docket-checks/"}
    targets = {}
    for route in routes:
        raw = (site / route.lstrip("/") / "index.html").read_text()
        for pattern in (r"<title>(.*?)</title>", r"<h1\b[^>]*>(.*?)</h1>",
                        r'<meta name="description" content="(.*?)"'):
            assert name in html.unescape(re.search(pattern, raw, re.S)[1]), (route, pattern)
        targets[route] = {attrs["id"] for tag, attrs in Page(raw).tags if "id" in attrs}
    links = 0
    for page in site.rglob("*.html"):
        for tag, attrs in Page(page.read_text()).tags:
            target = urlsplit(attrs.get("href", ""))
            if target.path in routes and target.hostname in {None, OLD_HOST, NEW_HOST}:
                links += 1
                assert not target.fragment or target.fragment in targets[target.path], (page, target)
    assert links > 16
    stubs = json.loads((site.parent / "data/redirect-pages.json").read_text())
    assert len(stubs) == 16
    for relative, source in stubs.items():
        raw = (site / relative).read_text()
        assert "<title>Moved:" in raw
        refresh = re.search(r'content="0; url=([^"]+)"', raw)[1]
        assert urlsplit(refresh).path in routes, relative
        # The rename may change prose and the canonical host. Routes and fragments stay exact.
        for pattern in (r'content="0; url=([^"]+)"', r'<a href="(/[^"]+)"'):
            assert re.findall(pattern, raw) == re.findall(pattern, source), relative


def no_old_product(text, where):
    # Independently listed technical literals. These keep their shipped names.
    text = text.replace("formerly Docket SEO", "")
    # The Microsoft Store listing keeps its name (CEO decision 2026-11-09); the site says so (brand.STORE_NOTE).
    text = text.replace("listed there as Docket SEO", "")
    text = re.sub(r'(?:/Applications/|/Volumes/|[A-Z]:\\+)[^\n"<>]*', "", text)
    text = re.sub(r"Docket(?:-SEO-Audit(?:-Survey)?(?:/[^\s]+)?|-\d[\w.-]*\.(?:dmg|exe))", "", text)
    assert "Docket" not in text, f"{where}: old product word in {text!r}"
    assert "Check Engine Check Engine" not in text, where
    assert "Check Engine SEO SEO" not in text, where
    assert not re.search(r"\ban Check Engine\b", text), where


def snapshot_main(destination):
    archive = subprocess.check_output(
        ["git", "archive", "main", "--", "scripts", "data", "site", "workers", "action.yml", "ACTION.md", "README.md"],
        cwd=ROOT,
    )
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source.getmembers():
            assert not member.issym() and not member.islnk() and ".." not in Path(member.name).parts
            assert not member.name.endswith(".env")
        source.extractall(destination)


def build(destination, brand, baseline=False):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", DOCKET_SKIP_BRAND_ASSETS="1", TZ="UTC")
    env.pop("DOCKET_DEPLOY", None)
    env.pop("SITE_BRAND", None)
    if brand:
        env["SITE_BRAND"] = brand
    command = [sys.executable, "scripts/build.py"]
    if baseline:
        bootstrap = ("import runpy, sys; sys.path.insert(0, 'scripts'); "
                     "import render_brand_assets; render_brand_assets.render = lambda site: None; "
                     "runpy.run_path('scripts/build.py', run_name='__main__')")
        command = [sys.executable, "-c", bootstrap]
    anchor = (destination / "data/build-id.txt").read_bytes()
    result = subprocess.run(command, cwd=destination, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (destination / "data/build-id.txt").read_bytes() == anchor, "build changed its real anchor"


def check_site(site):
    assert (site / "CNAME").read_text() == NEW_HOST + "\n"
    sitemap = (site / "sitemap.xml").read_text()
    assert OLD_HOST not in sitemap
    assert all(urlsplit(url).hostname == NEW_HOST for url in re.findall(r"<loc>(.*?)</loc>", sitemap))
    assert (site / "robots.txt").read_text().splitlines()[0] == "# Check Engine SEO. checkengineseo.com"
    assert f"Sitemap: https://{NEW_HOST}/sitemap.xml" in (site / "robots.txt").read_text()
    no_old_product((site / "robots.txt").read_text(), "robots.txt")
    assert OLD_HOST not in (site / "NOTICES.txt").read_text()
    # The crawler's robots.txt token is what it sends; the rename must not turn it into a name with a space in it.
    bot = (site / "bot/index.html").read_text()
    assert "User-agent: Docket-SEO-Audit" in bot and "Check Engine-SEO-Audit" not in bot
    for rel in ("for/agencies/index.html", "index/ai-directives/index.html", "index/llms-txt-adoption-2026-10/index.html"):
        assert "Check Engine-SEO-Audit" not in (site / rel).read_text(), rel
    llms = (site / "llms.txt").read_text()
    no_old_product(llms, "llms.txt")
    assert "`checkengine audit`" in llms
    for machine in MACHINE[:3]:
        assert f"https://{OLD_HOST}{machine}" in llms, machine
    assert f"https://{NEW_HOST}/assets/docket-sample-report.pdf" in llms
    assert f"https://{NEW_HOST}/bot/" in llms
    assert json.loads((site / "offer.json").read_text())["sample_report_url"] == f"https://{OLD_HOST}/assets/docket-sample-report.pdf"

    for rel in SAMPLES:
        assert (site / rel).is_file(), rel

    for path in site.rglob("*.html"):
        raw = path.read_text()
        parsed = Page(raw)
        where = str(path.relative_to(site))
        for words in parsed.words:
            no_old_product(words, where)
        for block in parsed.json_ld:
            for words in json_values(block):
                no_old_product(words, where + " JSON-LD")
        for tag, attrs in parsed.tags:
            if tag == "link" and attrs.get("rel") == "canonical":
                assert urlsplit(attrs["href"]).hostname == NEW_HOST, where
            if tag == "meta" and attrs.get("property") == "og:url":
                assert urlsplit(attrs["content"]).hostname == NEW_HOST, where
            for key in ("href", "src", "poster", "action"):
                url = urlsplit(attrs.get(key, ""))
                if url.hostname == OLD_HOST:
                    assert url.path in MACHINE or url.path == "/bot", (where, url.geturl())
        title = re.search(r"<title>(.*?)</title>", raw, re.S)
        desc = re.search(r'<meta name="description" content="(.*?)"', raw, re.S)
        if title:
            assert len(html.unescape(title[1])) <= 60, (where, title[1])
        if desc:
            assert len(html.unescape(desc[1])) <= 165, (where, desc[1])

    preview = (site / "tools/serp-preview/index.html").read_text()
    assert "Fits Check Engine\\'s range" in preview
    checker = (site / "tools/ai-crawler-checker/index.html").read_text()
    assert "AI crawler access checked with Check Engine</a>" in checker
    assert "navigator.share({title:'Check Engine SEO for Mac'" in (site / "index.html").read_text()

    for rel, count in (("index.html", 2), ("about/index.html", 2), ("download/index.html", 1)):
        assert (site / rel).read_text().count("formerly Docket SEO") == count, rel
    for rel in ("download/index.html", "for/developers/index.html"):
        raw = (site / rel).read_text()
        assert "checkengine audit" in raw, rel
        assert not re.search(r"(?<![/\w])docket audit\b", raw), rel
    for machine in MACHINE:
        assert (site / machine.lstrip("/")).exists(), machine
    home = (site / "index.html").read_text()
    # A link a reader follows goes to this site's host; the user-agent string and app feeds keep the old one.
    assert 'href="/bot/"' in home and f'href="https://{OLD_HOST}/bot/"' not in home
    assert f'href="https://{OLD_HOST}/assets/docket-sample-report.pdf"' not in home
    privacy = (site / "legal/privacy/index.html").read_text()
    for machine in MACHINE[:3]:
        assert f'href="https://{OLD_HOST}{machine}"' in privacy, machine
    assert 'href="mailto:support@docketseo.app"' in privacy

    manifest = json.loads((site / "_redirect-map.json").read_text())
    expected = {"/" + p.relative_to(site).as_posix() for p in site.rglob("*") if p.is_file()}
    expected.update(path.removesuffix("index.html") for path in tuple(expected) if path.endswith("/index.html"))
    assert manifest == sorted(expected), "redirect inventory differs from built files"
    check_history(site)
    check_home_knowledge(site)
    check_cli_context(site)
    check_favicon_copy(site, "Check Engine")
    check_kept_slugs(site, "Check Engine")


def check_transform(destination):
    # Exercise the pass through its public functions with planted traps.
    probe = r'''import brand
assert brand.NAME == "Check Engine SEO"
assert brand.text("an Docket audit and Docket's report") == "a Check Engine audit and Check Engine's report"
assert brand.text("Docket SEO") == "Check Engine SEO"
assert brand.text("docket audit example.com") == "checkengine audit example.com"
assert brand.text("~/.docket/ docket.sarif /Applications/Docket.app/Contents/Resources/docket/docket") == "~/.docket/ docket.sarif /Applications/Docket.app/Contents/Resources/docket/docket"
raw = '<a id="Docket" class="Docket" data-ev="Docket" href="https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket">Docket SEO</a><img src="/assets/docket.webp" alt="Docket audit"><pre><code>docket audit example.com</code></pre><script>const Docket = "docket";</script>'
out = brand.html(raw)
assert 'id="Docket" class="Docket" data-ev="Docket"' in out
assert 'href="https://kerr-affiliate-hub.kerrco.workers.dev/buy/docket"' in out
assert 'src="/assets/docket.webp" alt="Check Engine audit"' in out
assert '<code>checkengine audit example.com</code>' in out
assert '<script>const Docket = "docket";</script>' in out
history = '<pre data-brand-history><code>$ docket attack https://docketseo.app</code></pre>'
assert '$ docket attack https://docketseo.app' in brand.html(history)
out = brand.html('<p data-brand-history>Docket audited <code>docketseo.app</code>.</p><p>docket audit docketseo.app</p>')
assert '<code>docketseo.app</code>' in out and 'Check Engine audited' in out
assert '<p>checkengine audit checkengineseo.com</p>' in out
out = brand.html('<section data-brand-history><p>docket audit docketseo.app</p><p><span>docketseo.app</span></p></section><p>docket audit docketseo.app</p>')
assert '<p>docket audit docketseo.app</p>' in out
assert '<p><span>docketseo.app</span></p>' in out
assert out.endswith('<p>checkengine audit checkengineseo.com</p>')
out = brand.html('<span data-brand-history/>docket audit docketseo.app')
assert out.endswith('checkengine audit checkengineseo.com')
out = brand.html('<img data-brand-history alt="Docket auditing docketseo.app"><p>docket audit docketseo.app</p>')
assert 'alt="Check Engine auditing docketseo.app"' in out
assert '<p>checkengine audit checkengineseo.com</p>' in out
for path in brand.MACHINE_PATHS + ("/assets/docket-sample-report.pdf",):
    assert brand.site_url(brand.BASE + path) == brand.LEGACY_BASE + path
assert brand.site_url(brand.BASE + '/updates/1.3.159/Docket.app.tar.gz') == brand.LEGACY_BASE + '/updates/1.3.159/Docket.app.tar.gz'
assert brand.is_machine_path('/updates/1.3.158/Docket-1.3.158-x64-setup.exe') and not brand.is_machine_path('/updates')
assert brand.site_url(brand.LEGACY_BASE + '/pricing/?x=docket#Docket') == brand.BASE + '/pricing/?x=docket#Docket'
import own_hosts
assert own_hosts.is_own(brand.BASE)
assert own_hosts.is_own(brand.LEGACY_BASE)
assert not own_hosts.is_own(brand.BASE + '.example.invalid/')
import verify_contact
from unittest.mock import patch
assert brand.BASE + '/contact/' in verify_contact.contact_urls()
with patch.object(verify_contact.own_hosts.HEAD_OPENER, 'open', side_effect=AssertionError('network')):
    ok, why = verify_contact.reachable(brand.BASE + '/contact/')
    assert ok and why.startswith('SKIP new host')
'''
    env = dict(os.environ, SITE_BRAND="checkengine", PYTHONDONTWRITEBYTECODE="1")
    env.pop("DOCKET_CHECK_NEW_HOST", None)
    result = subprocess.run([sys.executable, "-c", probe], cwd=destination / "scripts", env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    invalid_env = dict(env, SITE_BRAND="unknown-brand")
    invalid = subprocess.run([sys.executable, "-c", "import brand"], cwd=destination / "scripts",
                             env=invalid_env, capture_output=True, text=True)
    assert invalid.returncode != 0 and "Unknown SITE_BRAND" in invalid.stderr
    churn = subprocess.run([sys.executable, "scripts/test_release_churn_gate.py"], cwd=destination,
                           env=env, capture_output=True, text=True)
    assert churn.returncode == 0, churn.stdout + churn.stderr


# Pages whose copy was deliberately rewritten after main (gap-query pass, 2026-11-09), plus the review fixes.
# Only used while the default build is still Docket; after the default flips the main comparison is skipped.
CONTENT_UPDATED = {Path(route) / "index.html" for route in (
    "",
    "best/free-seo-audit-tools",
    "best/screaming-frog-alternatives",
    "how-to/fix-paginated-pages-that-canonicalise-to-page-1",
    "learn/seo-audit",
    "legal/privacy",
    "legal/refunds",
    "legal/terms",
    "tools/robots-txt-tester",
    "vs/se-ranking-vs-screaming-frog",
    "vs/screaming-frog-alternative",
    "vs/sitebulb-alternative",
    "vs/semrush-site-audit-alternative",
    "vs/lighthouse-alternative",
    "vs/google-search-console",
    "vs/scrutiny-alternative",
    "vs/seoptimer-alternative",
    "vs/sitechecker-alternative",
    "vs/profound-alternative",
    "vs/jetoctopus-alternative",
    "vs/crawlraven-alternative",
    "vs/crawler-sh-alternative",
)}


def compare_default(site, baseline):
    previous = {p.relative_to(baseline) for p in baseline.rglob("*") if p.is_file()}
    current = {p.relative_to(site) for p in site.rglob("*") if p.is_file()}
    help_pages = {Path(route) / "index.html" for route in ("help", "support", "faq")}
    assert current == previous | help_pages | {Path("_redirect-map.json")}, "unexpected output paths"
    with (ROOT / "data/checks.csv").open() as source:
        checks = sum(1 for row in csv.DictReader(source))
    # These requested source-copy fixes also improve the Docket build. Keep the
    # byte comparison against main, allowing only these exact changes.
    copy_changes = {
        "contact/index.html": [
            ("which for this site is GitHub Pages, whose servers do not answer on port 25.",
             "which for that address was GitHub Pages, whose servers did not answer on port 25."),
            ("on this domain reaches a mailbox anyone reads:",
             "on that domain reaches a mailbox anyone reads:"),
        ],
        "download/index.html": [
            ("timing the CLI out of", "timing the engine out of"),
            ("The same engine ships as a CLI inside the app bundle.",
             "The same engine ships as a CLI, <code>docket</code>, inside the app bundle."),
            ("crawler knowledge file\nfrom this site,", "crawler knowledge file from\ndocketseo.app,"),
        ],
        "for/developers/index.html": [
            ('<p class="lede">Docket\'s CLI exits',
             '<p class="lede">Docket\'s CLI, <code>docket</code>, exits'),
        ],
        "how-to/fix-broken-outbound-links/index.html": [
            ("Does Docket check every outbound link on my site?",
             "Does the audit check every outbound link on my site?"),
        ],
        "how-to/fix-favicon-not-showing-in-search/index.html": [
            ("<h2>What Docket checks</h2>", "<h2>What the audit checks</h2>"),
            ("<p>Docket opens your home page,", "<p>The tool opens your home page,"),
        ],
        "how-to/fix-missing-security-headers/index.html": [
            ("<h2>What an audit of this site returns</h2>",
             "<h2>What the audit returned</h2>\n\n"
             "<p>We audited docketseo.app on 14 August 2026. These were the findings.</p>"),
            ("<p>All three are true.", "<p>All three were true."),
            ("The <code>www</code> host redirects\ncorrectly; the apex does not,",
             "The <code>www</code> host redirected\ncorrectly. The apex did not,"),
        ],
        "index.html": [
            ("Docket auditing this site, recorded", "Docket auditing docketseo.app, recorded"),
            ("  this site.</figcaption>", "  docketseo.app.</figcaption>"),
        ],
        "learn/dead-contact-address/index.html": [
            ("The domain had no MX record; it is on GitHub Pages; port 25 is closed there.",
             "The domain had no MX record. It was on GitHub Pages, whose servers did not answer on port 25."),
        ],
        "learn/what-docket-checks/index.html": [
            (f"SEO audit checklist: all {checks} checks by area (2026)",
             f"Docket SEO audit checklist: all {checks} checks"),
            (f"All {checks} checks, by area", f"All {checks} Docket checks, by area"),
        ],
        "robots.txt": [("# Docket. Docketseo.app", "# Docket SEO. docketseo.app")],
    }

    def unchanged_content(raw, relative, *, current=False):
        if relative.suffix == ".html":
            # The help job adds footer links on rendered pages and a computed
            # bundle sum on pricing. All other default copy must stay identical.
            if current:
                raw = re.sub(rb'<span data-brand-history>(.*?)</span>', rb'\1', raw)
                raw = raw.replace(b" data-brand-history", b"")
                raw = raw.replace(
                    b'<a href="/help/">Help</a><a href="/support/">Support</a><a href="/faq/">FAQ</a>\n',
                    b"",
                )
                if relative == Path("pricing/index.html"):
                    raw, count = re.subn(rb'<p class="hero-note" id="bundle-sum">.*?</p>\n', b"", raw)
                    assert count == 1, "pricing must have exactly one bundle sum"
            # Adding pages changes the tree hash stamped into every HTML head.
            raw = re.sub(rb'(<meta name="build-id" content=")[a-f0-9]{12}(">)', rb'\1BUILD_ID\2', raw)
        elif current and relative == Path("sitemap.xml"):
            for route in ("help", "support", "faq"):
                raw, count = re.subn(
                    rb'  <url><loc>https://docketseo.app/' + route.encode() + rb'/</loc>.*?</url>\n', b"", raw)
                assert count == 1, f"sitemap must list /{route}/ once"
        if relative == Path("sitemap.xml"):
            # Contact, terms and refunds have no explicit modified date. Their corrected source copy
            # advances the generated lastmod on the day this build runs.
            for route in (b"contact", b"legal/terms", b"legal/refunds"):
                raw = re.sub(rb'(<loc>https://docketseo.app/' + route + rb'/</loc><lastmod>)[^<]+',
                             rb'\1COPY_DATE', raw)
        if relative == Path("llms.txt"):
            # FAQ prose is wrapped to a fixed line width in this text file.
            raw = b" ".join(raw.split())
        if not current:
            changes = list(copy_changes.get(relative.as_posix(), []))
            if relative in {Path("index.html"), Path("llms.txt")}:
                changes += [
                    ("a knowledge refresh from this site;", "a knowledge refresh;"),
                    ("which is sent your site's topic words. Offline",
                     "which is sent your site's topic words. The knowledge refresh fetches "
                     "docketseo.app/data/knowledge.json. Offline"),
                ]
            for old, new in changes:
                assert old.encode() in raw, (relative, old)
                raw = raw.replace(old.encode(), new.encode())
        return raw

    for relative in previous:
        if relative == Path("learn/internal-link-equity/index.html"):
            # Its figures and example list are generated from data/link-equity.json, which the three new pages and their
            # footer links changed (scripts/verify_link_graph.py pins that file to the site). Check it prints the measurement.
            measured = json.loads((Path(__file__).resolve().parent.parent / "data" / "link-equity.json").read_text())
            article = (site / relative).read_text(encoding="utf-8")
            assert f"{measured['pages']} pages and {measured['edges']} links" in article, str(relative)
            continue
        if relative in CONTENT_UPDATED:
            # These pages have requested copy changes. Main cannot be their baseline,
            # so check they still build and that the Docket build carries none of the new name.
            assert b"Check Engine" not in (site / relative).read_bytes(), str(relative)
            continue
        old = hashlib.sha256(unchanged_content((baseline / relative).read_bytes(), relative)).digest()
        new = hashlib.sha256(unchanged_content((site / relative).read_bytes(), relative, current=True)).digest()
        assert new == old, str(relative)


def default_brand():
    # Read the source, independent of SITE_BRAND in the test runner's shell.
    tree = ast.parse((ROOT / "scripts/brand.py").read_text())
    setting = next(node.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == "SITE_BRAND"
                           for target in node.targets))
    assert isinstance(setting, ast.Call) and ast.literal_eval(setting.args[0]) == "SITE_BRAND"
    value = ast.literal_eval(setting.args[1])
    assert value in {"docket", "checkengine"}, value
    return value


def check_analytics(docket, checkengine):
    # CEO 2026-11-10: the Check Engine build keeps the SITE-BOUND Plausible loader, so it counts under the docketseo.app site
    # (Docket's history) whatever the host; the checkengineseo.com Plausible site was repurposed, so no classic data-domain loader.
    loader = '<script async src="https://plausible.io/js/pa-l5xLCLM0WKYQNcrCFH9qg.js"></script>'
    count = 0
    for page in docket.rglob("*.html"):
        before = page.read_text()
        after = (checkengine / page.relative_to(docket)).read_text()
        assert "data-domain" not in after and "plausible.io/js/script.js" not in after, page
        if loader not in before:
            assert loader not in after, page
            continue
        count += 1
        assert before.count(loader) == after.count(loader) == 1, page
        # The inline stub and delegated listener are byte-identical in both brands.
        assert before.split(loader + "\n<script>\n", 1)[1].split("</script>", 1)[0] == \
            after.split(loader + "\n<script>\n", 1)[1].split("</script>", 1)[0], page
    assert count > 150, count


def check_privacy(destination, mode):
    result = subprocess.run([sys.executable, "scripts/verify_privacy_scripts.py", "--self-test"],
                            cwd=destination, env=dict(os.environ, SITE_BRAND=mode),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def main():
    anchor = (ROOT / "data/build-id.txt").read_bytes()
    default = default_brand()
    with tempfile.TemporaryDirectory(prefix="test-rename-brand-") as temporary:
        temporary = Path(temporary)
        baseline = temporary / "main"
        if default == "docket":
            snapshot_main(baseline)
            build(baseline, "docket", baseline=True)
        else:
            print("SKIP main snapshot: the default is Check Engine, so main is no longer a Docket baseline.")
        for mode in ("docket", "checkengine"):
            destination = temporary / mode
            for directory in ("scripts", "data", "site", "workers"):
                shutil.copytree(ROOT / directory, destination / directory,
                                ignore=shutil.ignore_patterns("__pycache__", "*.env"))
            build(destination, mode)
            if mode == "checkengine":
                check_transform(destination)
                check_site(destination / "site")
                previous_paths = temporary / "docket/site/_redirect-map.json"
                assert (destination / "site/_redirect-map.json").read_bytes() == previous_paths.read_bytes()
                check_analytics(temporary / "docket/site", destination / "site")
            else:
                if default == "docket":
                    compare_default(destination / "site", baseline / "site")
                check_favicon_copy(destination / "site", "Docket")
                check_kept_slugs(destination / "site", "Docket")
            check_privacy(destination, mode)
        # Switching the same output tree back must restore the default too.
        build(destination, None)
        if default == "docket":
            compare_default(destination / "site", baseline / "site")
        else:
            check_site(destination / "site")
        assert (ROOT / "data/build-id.txt").read_bytes() == anchor
    print("SKIP brand image rendering in scratch builds: DOCKET_SKIP_BRAND_ASSETS=1")
    print("OK")


if __name__ == "__main__":
    main()
