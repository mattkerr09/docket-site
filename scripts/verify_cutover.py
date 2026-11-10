#!/usr/bin/env python3
"""Read-only cutover checks. --self-test uses only an in-process loopback server."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import html
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
import ssl
import struct
import threading
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import (HTTPRedirectHandler, HTTPSHandler, ProxyHandler,
                            Request, build_opener)
import xml.etree.ElementTree as ET

OLD = "docketseo.app"
NEW = "checkengineseo.com"
MCP = "mcp.docketseo.app"
PHASES = ("passthrough", "fallback", "redirect", "final")
PAGES = ("/", "/learn/", "/download/", "/pricing/", "/faq/", "/help/", "/support/")
# What the OLD host serves today (before the Check Engine site lands): the help, support and FAQ pages exist only in the new build.
OLD_PAGES = ("/", "/learn/", "/download/", "/pricing/")
REDIRECTS = ("/", "/learn/seo-audit/", "/download/?from=old&keep=a%2Fb",
             "/UPPER/Path?keep=%2f", "/updates", "/missing%20page/?q=a+b")
APPS = {"/updater.json": "application/json", "/offer.json": "application/json",
        "/data/knowledge.json": "application/json", "/bot": "text/html",
        "/bot/": "text/html", "/assets/docket-sample-report.pdf": "application/pdf"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


@dataclass
class Response:
    status: int
    headers: dict
    body: bytes = b""
    body_hash: str | None = None

    def __post_init__(self):
        self.headers = {key.lower(): value for key, value in self.headers.items()}

    def text(self):
        return self.body.decode("utf-8")

    def digest(self):
        return self.body_hash or hashlib.sha256(self.body).hexdigest()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def require(condition, message):
    if not condition:
        raise ValueError(message)


def allowed_url(url, old=OLD, new=NEW):
    parsed = urlsplit(url)
    require(parsed.scheme == "https" and parsed.netloc in {old, new, "www." + old, MCP}
            and not parsed.fragment, "URL outside the HTTPS host allowlist: " + url)
    return parsed


class LiveFetch:
    """TLS verification on, proxies and redirects off. Never fetch a third party."""
    def __init__(self, old=OLD, new=NEW, probe_post=False):
        self.old, self.new = old, new
        self.probe_post = probe_post
        self.opener = build_opener(ProxyHandler({}), NoRedirect(),
                                  HTTPSHandler(context=ssl.create_default_context()))

    def __call__(self, url, method="GET", headers=None):
        parsed = allowed_url(url, self.old, self.new)
        require(method in {"GET", "HEAD"} or (
            self.probe_post and method == "POST"
            and url in {"https://" + self.old + "/", "https://" + self.old + "/__redirect-health"}
            and not headers), "Only GET and HEAD are allowed except the two opt-in POST probes")
        # NoRedirect also keeps a POST redirect from silently becoming a GET.
        request = Request(url, method=method,
                          headers={"User-Agent": "kerr-ops/1.0 (verify-cutover)",
                                   "Accept-Encoding": "identity", **(headers or {})})
        try:
            source = self.opener.open(request, timeout=20)
        except HTTPError as error:
            source = error
        with source:
            # Compare whole release files without retaining installers in RAM.
            if method == "GET" and parsed.path.startswith("/updates/") and not (headers or {}).get("Range"):
                digest = hashlib.sha256()
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(chunk)
                return Response(source.code, dict(source.headers), body_hash=digest.hexdigest())
            return Response(source.code, dict(source.headers),
                            source.read() if method != "HEAD" else b"")


def status(response, expected):
    require(response.status == expected, f"status {response.status}, expected {expected}")


def header(response, name, expected):
    actual = response.headers.get(name.lower())
    require(actual == expected, f"{name}: {actual!r}, expected {expected!r}")


def content_type(response, expected):
    actual = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    require(actual == expected, f"Content-Type {actual!r}, expected {expected}")


def served(response, expected_type, mode=None, code=200):
    status(response, code)
    content_type(response, expected_type)
    require("location" not in response.headers, "unexpected Location")
    if mode:
        header(response, "X-Served-By", "docketseo-redirect-" + mode if mode == "fallback"
               else "docketseo-redirect")


def range_response(response, expected_type, mode=None):
    served(response, expected_type, mode, 206)
    require(re.fullmatch(r"bytes 0-0/[1-9][0-9]*", response.headers.get("content-range", "")),
            "expected Content-Range bytes 0-0/total")
    header(response, "Content-Length", "1")
    require(len(response.body) == 1, "Range GET must return one byte")


def release_urls(response, old, new):
    served(response, "application/json")
    manifest = json.loads(response.text())
    version = manifest["version"]
    require(isinstance(version, str) and re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", version),
            "missing or invalid current updater version")
    platforms = manifest["platforms"]
    require(isinstance(platforms, dict) and platforms, "updater has no platforms")
    urls = sorted({entry["url"] for entry in platforms.values()})
    for url in urls:
        parsed = allowed_url(url, old, new)
        require(parsed.netloc in {old, new} and parsed.path.startswith(f"/updates/{version}/")
                and len(parsed.path) > len(f"/updates/{version}/"),
                "updater URL is not a current release on either site: " + url)
    return urls


class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.tags, self.outside_history, self.stack = [], [], []
        self.feed(raw)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        historical = bool(self.stack and self.stack[-1][1]) or "data-brand-history" in attrs
        self.tags.append((tag, attrs))
        if not historical:
            self.outside_history.append(html.unescape(self.get_starttag_text()))
        if tag not in VOID:
            self.stack.append((tag, historical))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if not self.stack or not self.stack[-1][1]:
            self.outside_history.append(data)

    def handle_comment(self, data):
        self.handle_data(data)


def page_metadata(response, new):
    served(response, "text/html")
    tags = Page(response.text()).tags
    groups = [attrs.get("href", "") for tag, attrs in tags
              if tag == "link" and "canonical" in attrs.get("rel", "").split()]
    fields = {"canonical": groups}
    for name in ("og:url", "og:image"):
        fields[name] = [attrs.get("content", "") for tag, attrs in tags
                        if tag == "meta" and attrs.get("property") == name]
    for name, values in fields.items():
        require(len(values) == 1, f"expected one {name}, got {len(values)}")
        require(urlsplit(values[0]).scheme == "https" and urlsplit(values[0]).netloc == new,
                f"{name} uses the wrong host: {values[0]}")


def plausible(response, new):
    served(response, "text/html")
    raw = response.text()
    scripts = [attrs for tag, attrs in Page(raw).tags if tag == "script"
               and urlsplit(attrs.get("src", "")).hostname == "plausible.io"]
    require(len(scripts) == 1, "expected one Plausible loader")
    require(scripts[0].get("src") == "https://plausible.io/js/pa-l5xLCLM0WKYQNcrCFH9qg.js"
            and "async" in scripts[0] and "data-domain" not in scripts[0],
            "expected the site-bound Plausible loader (async, no data-domain): it counts under the docketseo.app site")
    require("plausible.init" in raw and "plausible.q" in raw,
            "the site-bound loader needs the queue stub and the init call")


def old_host_leaks(response, old):
    served(response, "text/html")
    text = "\n".join(Page(response.text()).outside_history)
    # Exact literals only. Do not exempt an arbitrary old-host URL just because
    # its prefix looks like an app path or an email address.
    host = re.escape(old)
    boundary = r"(?=$|[^\w./@%-]|\.(?=$|[^\w./@%-]))"
    text = re.sub(r"(?<![\w.@-])support@" + host + boundary, "", text)
    # The contact page's meta description tells the history of the dead footer address (it never received mail); it names
    # the old domain on purpose and cannot carry a data-brand-history marker.
    text = re.sub(r"(?<![\w.@-])hello@" + host + boundary, "", text)
    text = re.sub(r"(?<![\w.@-])mcp\." + host + r"(?=[:/\s\"'<>]|$|\.(?=\s|$))", "", text)
    machine = (r"/(?:updater\.json|offer\.json|data/knowledge\.json|"
               r"assets/docket-sample-report\.pdf)" + boundary +
               r"|/bot(?:/[^\s\"'<>]*)?(?![\w.%-])|/updates/[^\s\"'<>]+")
    text = re.sub(r"(?<![\w.@-])" + host + r"(?:" + machine + r")", "", text)
    position = text.lower().find(old.lower())
    context = " ".join(text[max(0, position - 30):position + len(old) + 50].split())
    require(position == -1, "old host outside an allowed literal or data-brand-history: " + repr(context))


def sitemap_urls(response, new):
    served(response, "application/xml")
    root = ET.fromstring(response.body)
    require(root.tag.rsplit("}", 1)[-1] == "urlset", "expected a URL sitemap")
    urls = [node.text or "" for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "loc"]
    require(urls, "sitemap is empty")
    for url in urls:
        parsed = urlsplit(url)
        require(parsed.scheme == "https" and parsed.netloc == new, "sitemap URL uses wrong host: " + url)
    return urls


def robots(response, new):
    served(response, "text/plain")
    lines = response.text().splitlines()
    require(lines and lines[0] == "# Check Engine SEO. " + new, "wrong robots.txt first line")
    require([line for line in lines if line.lower().startswith("sitemap:")]
            == [f"Sitemap: https://{new}/sitemap.xml"], "wrong robots.txt Sitemap line")


def og_image(response):
    served(response, "image/png")
    body = response.body
    require(len(body) >= 33 and body[:8] == b"\x89PNG\r\n\x1a\n"
            and body[8:16] == b"\x00\x00\x00\rIHDR", "not a PNG with an IHDR chunk")
    require(struct.unpack(">II", body[16:24]) == (1200, 630), "OG image must be 1200x630")


@dataclass
class Check:
    name: str
    run: object


@dataclass
class Result:
    name: str
    passed: bool
    detail: str


def evaluate(check):
    try:
        check.run()
        return Result(check.name, True, "ok")
    except (OSError, ValueError, KeyError, TypeError, IndexError, ET.ParseError) as error:
        return Result(check.name, False, str(error))


def checks(phase, fetch, old=OLD, new=NEW, probe_post=False):
    """Yield small checks over an injected fetch. Discovery failures are checks too."""
    require(not probe_post or phase in {"fallback", "redirect"},
            "--probe-post requires --phase fallback or --phase redirect")
    def get(host, path, method="GET", headers=None):
        return fetch("https://" + host + path, method, headers)

    def make(name, function):
        return Check(name, function)

    if probe_post:
        for path, allow in (("/", "GET, HEAD"), ("/__redirect-health", "GET")):
            def post(p=path, a=allow):
                response = get(old, p, "POST")
                status(response, 405)
                header(response, "Allow", a)
                require("location" not in response.headers, "unexpected Location on POST")
            yield make(f"POST {path} is refused (405, Allow: {allow})", post)

    hosts = (old,) if phase == "passthrough" else (old, "www." + old)
    if phase == "passthrough":
        for path in OLD_PAGES:
            for method in ("GET", "HEAD"):
                yield make(f"old page {method} {path}",
                           lambda p=path, m=method: served(get(old, p, m), "text/html"))
        for path in ("/", "/download/?from=old&keep=a%2Fb", "/updater.json"):
            def www(p=path):
                response = get("www." + old, p)
                status(response, 301)
                header(response, "Location", "https://" + old + p)
            yield make("www to apex " + path, www)

    if phase in {"passthrough", "fallback", "redirect"}:
        for host in hosts:
            mode = None if phase == "passthrough" else phase
            for path, mime in APPS.items():
                for method in ("GET", "HEAD"):
                    def app(h=host, p=path, t=mime, m=method):
                        response = get(h, p, m)
                        if phase == "passthrough" and p == "/bot":
                            # GitHub Pages itself answers /bot with a 301 to /bot/; passthrough must not change that.
                            status(response, 301)
                            header(response, "Location", "https://" + h + "/bot/")
                            return
                        served(response, t, mode)
                        if phase == "redirect":
                            other = get(new, p, m)
                            served(other, t)
                            if m == "GET":
                                require(response.digest() == other.digest(), "old/new body hashes differ")
                    yield make(f"app {host} {method} {path}", app)

            def discover(h=host):
                return release_urls(get(h, "/updater.json"), old, new)
            yield make("current release URLs " + host, discover)
            try:
                urls = discover()
            except (OSError, ValueError, KeyError, TypeError):
                urls = []
            for url in urls:
                path = urlsplit(url).path
                mime = "application/gzip" if path.endswith((".gz", ".tgz")) else "application/octet-stream"
                def release(h=host, p=path, t=mime):
                    served(get(h, p, "HEAD"), t, mode)
                    response = get(h, p, headers={"Range": "bytes=0-0"})
                    range_response(response, t, mode)
                    if phase == "redirect":
                        other = get(new, p, headers={"Range": "bytes=0-0"})
                        range_response(other, t)
                        require(response.digest() == other.digest(),
                                "old/new release range hashes differ")
                        old_file, new_file = get(h, p), get(new, p)
                        served(old_file, t, mode)
                        served(new_file, t)
                        require(old_file.digest() == new_file.digest(), "old/new full release hashes differ")
                yield make(f"release HEAD and Range {host} {path}", release)

    if phase in {"fallback", "redirect"}:
        for host in hosts:
            def health(h=host):
                response = get(h, "/__redirect-health")
                served(response, "text/plain")
                header(response, "X-Mode", phase)
                require(response.body == b"ok", "health body must be ok")
            yield make("health " + host, health)
            for path in REDIRECTS:
                for method in ("GET", "HEAD"):
                    def page(h=host, p=path, m=method):
                        response = get(h, p, m)
                        if phase == "fallback":
                            status(response, 503)
                            retry = response.headers.get("retry-after", "")
                            require(re.fullmatch(r"[1-9][0-9]*", retry), "missing positive Retry-After seconds")
                            require("location" not in response.headers, "fallback must not redirect")
                        else:
                            status(response, 301)
                            header(response, "Location", "https://" + new + p)
                    yield make(f"{phase} page {host} {method} {path}", page)

    if phase == "final":
        # A successful HTTPS request proves the default context accepted the
        # certificate and hostname. A page status is checked separately.
        for host in (old, new):
            yield make("TLS " + host, lambda h=host: get(h, "/", "HEAD"))
        for path in PAGES:
            yield make("page metadata " + path, lambda p=path: page_metadata(get(new, p), new))
            yield make("Plausible " + path, lambda p=path: plausible(get(new, p), new))
        yield make("sitemap new host", lambda: sitemap_urls(get(new, "/sitemap.xml"), new))
        yield make("robots", lambda: robots(get(new, "/robots.txt"), new))
        yield make("OG PNG", lambda: og_image(get(new, "/og.png")))
        yield make("MCP health", lambda: status(get(MCP, "/health"), 200))
        yield make("updater URLs", lambda: release_urls(get(old, "/updater.json"), old, new))
        try:
            urls = release_urls(get(old, "/updater.json"), old, new)
        except (OSError, ValueError, KeyError, TypeError):
            urls = []
        for url in urls:
            def updater_head(u=url):
                response = fetch(u, "HEAD", {"Range": "bytes=0-0"})
                status(response, 206)
                require(re.fullmatch(r"bytes 0-0/[1-9][0-9]*", response.headers.get("content-range", "")),
                        "release HEAD lacks Content-Range bytes 0-0/total")
                header(response, "Content-Length", "1")
                require("location" not in response.headers, "release URL redirects")
            yield make("updater HEAD Range " + url, updater_head)

        def inventory():
            response = get(new, "/_redirect-map.json")
            served(response, "application/json")
            paths = json.loads(response.text())
            require(isinstance(paths, list) and paths and all(isinstance(p, str) and p.startswith("/")
                    and not p.startswith("//") and not urlsplit(p).query and not urlsplit(p).fragment
                    for p in paths), "invalid redirect inventory")
            require("/index.html" in paths, "inventory lacks home HTML")
            return {path for path in paths if path.endswith(".html")}
        yield make("HTML inventory", inventory)
        page_paths = set(PAGES)
        try:
            page_paths.update(inventory())
            page_paths.update(urlsplit(url).path for url in sitemap_urls(get(new, "/sitemap.xml"), new))
        except (OSError, ValueError, KeyError, TypeError, ET.ParseError):
            pass
        for path in sorted(page_paths):
            yield make("old host scan " + path, lambda p=path: old_host_leaks(get(new, p), old))


def print_results(results):
    print("RESULT  CHECK  DETAIL")
    for result in results:
        print(f"{'PASS' if result.passed else 'FAIL':6}  {result.name}  {result.detail}")
    return 0 if all(result.passed for result in results) else 1


# Offline fixtures use the same URL, method, header and body contract as live
# fetch. Logical HTTPS hosts travel in a test header to a loopback HTTP server.
class Fixture:
    def __init__(self):
        self.phase = "passthrough"
        self.change = None
        self.seen = []

    def response(self, host, path, method, headers):
        self.seen.append((host, path, method, headers))
        response = self.good(host, path, method, headers)
        if self.change:
            changed = self.change(host, path, method, headers, response)
            if changed.body != response.body and changed.headers.get("content-length") == response.headers.get("content-length"):
                changed.headers["content-length"] = str(len(changed.body))
            response = changed
        return response

    def good(self, host, path, method, headers):
        bare = urlsplit(path).path
        if host == OLD and self.phase in {"fallback", "redirect"} and method == "POST":
            return Response(405, {"Allow": "GET" if bare == "/__redirect-health" else "GET, HEAD"})
        if host == MCP:
            return Response(200, {"Content-Type": "application/json"}, b'{"ok":true}')
        if host == "www." + OLD and self.phase == "passthrough":
            return Response(301, {"Location": "https://" + OLD + path})
        if host == OLD and self.phase == "passthrough" and bare == "/bot":
            return Response(301, {"Location": "https://" + OLD + "/bot/"})   # GitHub Pages' own slash redirect
        if host != NEW and self.phase in {"fallback", "redirect"} and bare == "/__redirect-health":
            return Response(200, {"Content-Type": "text/plain", "X-Mode": self.phase}, b"ok")
        is_app = bare in APPS or bare.startswith("/updates/")
        if host != NEW and self.phase in {"fallback", "redirect"} and not is_app:
            if self.phase == "fallback":
                return Response(503, {"Retry-After": "300"})
            return Response(301, {"Location": "https://" + NEW + path})
        mime, body = "text/html", self.page(bare)
        if bare == "/updater.json":
            mime = "application/json"
            body = json.dumps({"version": "1.2.3", "platforms": {"test": {
                "url": "https://" + OLD + "/updates/1.2.3/Docket.app.tar.gz"}}}).encode()
        elif bare == "/_redirect-map.json":
            mime, body = "application/json", b'["/index.html", "/learn/index.html", "/extra/index.html"]'
        elif bare in {"/offer.json", "/data/knowledge.json"}:
            mime, body = "application/json", b"{}"
        elif bare.endswith(".pdf"):
            mime, body = "application/pdf", b"%PDF fixture"
        elif bare.startswith("/updates/"):
            mime, body = "application/gzip", b"release fixture"
        elif bare == "/robots.txt":
            mime, body = "text/plain", (f"# Check Engine SEO. {NEW}\nSitemap: https://{NEW}/sitemap.xml\n").encode()
        elif bare == "/sitemap.xml":
            mime, body = "application/xml", (f'<urlset><url><loc>https://{NEW}/</loc></url></urlset>').encode()
        elif bare == "/og.png":
            # Header fixture only; production checks read the PNG's IHDR size.
            mime = "image/png"
            body = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + struct.pack(">II", 1200, 630) + b"\x08\x02\x00\x00\x00" + b"\x00" * 4
        result_headers = {"Content-Type": mime, "Content-Length": str(len(body))}
        if host != NEW and self.phase in {"fallback", "redirect"} and is_app:
            result_headers["X-Served-By"] = ("docketseo-redirect-fallback" if self.phase == "fallback"
                                             else "docketseo-redirect")
        if headers.get("Range") == "bytes=0-0" and bare.startswith("/updates/"):
            result_headers.update({"Content-Range": f"bytes 0-0/{len(body)}", "Content-Length": "1"})
            return Response(206, result_headers, body[:1])
        return Response(200, result_headers, body)

    @staticmethod
    def page(path):
        return (f'<link rel="canonical" href="https://{NEW}{path}">'
                f'<meta property="og:url" content="https://{NEW}{path}">'
                f'<meta property="og:image" content="https://{NEW}/og.png">'
                f'<script async src="https://plausible.io/js/pa-l5xLCLM0WKYQNcrCFH9qg.js"></script>'
                '<script>window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},plausible.init=plausible.init||function(i){plausible.o=i||{}};plausible.init()</script>'
                f'<p>support@{OLD} https://{MCP}/mcp https://{OLD}/updater.json</p>'
                f'<section data-brand-history><p>https://{OLD}/past/</p></section>').encode()


def self_test():
    fixture = Fixture()

    class Handler(BaseHTTPRequestHandler):
        def answer(self):
            if self.command == "POST":
                require(self.headers.get("Content-Length", "0") == "0"
                        and not any(self.headers.get(name) for name in
                                    ("Transfer-Encoding", "Cookie", "Authorization", "Proxy-Authorization")),
                        "POST must have no body, cookies or credentials")
            response = fixture.response(self.headers["X-Test-Host"], self.path, self.command,
                                        {"Range": self.headers.get("Range", "")})
            self.send_response(response.status)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(response.body)

        do_GET = do_HEAD = do_POST = answer

        def log_message(self, *args):
            pass

    ports_file = Path(__file__).resolve().parent.parent / "docs/PORTS.md"
    reserved = set(re.findall(r"\b89[5-9][0-9]\b", ports_file.read_text())) if ports_file.exists() else set()
    server = None
    for port in range(8950, 9000):
        if str(port) in reserved:
            continue
        try:
            server = HTTPServer(("127.0.0.1", port), Handler)
            break
        except PermissionError as error:
            raise ValueError("sandbox blocks the required loopback server: " + str(error)) from error
        except OSError:
            continue
    require(server is not None, "no spare loopback port in 8950-8999")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    opener = build_opener(ProxyHandler({}), NoRedirect())

    class LoopbackOpener:
        def open(self, request, timeout):
            parsed = allowed_url(request.full_url)
            target = f"http://127.0.0.1:{server.server_port}{parsed.path}"
            if parsed.query:
                target += "?" + parsed.query
            if request.get_method() == "POST":
                require(request.data is None, "POST request must have no body")
            local = Request(target, data=request.data, method=request.get_method(),
                            headers={**dict(request.header_items()), "X-Test-Host": parsed.netloc})
            return opener.open(local, timeout=timeout)

    fetch = LiveFetch(probe_post=True)
    fetch.opener = LoopbackOpener()

    try:
        total = exercise_fixture(fixture, fetch)
        print(f"PASS offline self-test: {total} checks; loopback port {server.server_port}; no live requests")
        if not ports_file.exists():
            print("NOTE docs/PORTS.md does not exist; the test selects a spare port in 8950-8999.")
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def exercise_fixture(fixture, fetch):
    total = 0
    for phase in PHASES:
        fixture.phase = phase
        fixture.seen.clear()
        cases = list(checks(phase, fetch))
        results = [evaluate(check) for check in cases]
        require(all(result.passed for result in results), repr([r for r in results if not r.passed]))
        require(all(m in {"GET", "HEAD"} for h, p, m, q in fixture.seen),
                "default phase sent a method other than GET or HEAD")
        for case in cases:
            if case.name.startswith("TLS "):
                def broken(url, method="GET", headers=None):
                    raise ssl.SSLCertVerificationError("planted invalid TLS certificate")
                bad_case = next(c for c in checks(phase, broken) if c.name == case.name)
                require(not evaluate(bad_case).passed, case.name + " accepted bad TLS")
            else:
                fixture.change = lambda h, p, m, q, r: Response(418, r.headers, r.body)
                require(not evaluate(case).passed, case.name + " accepted wrong status")
                fixture.change = None
        total += len(cases)
        print(f"PASS {phase}: {len(cases)} checks and planted status failures")
    targeted_self_tests(fixture, fetch)
    total += post_self_tests(fixture, fetch)
    safety_self_tests()
    return total


def post_self_tests(fixture, fetch):
    total = 0
    for phase in ("fallback", "redirect"):
        fixture.phase, fixture.change = phase, None
        fixture.seen.clear()
        cases = list(checks(phase, fetch, probe_post=True))
        results = [evaluate(case) for case in cases]
        require(all(result.passed for result in results), repr([r for r in results if not r.passed]))
        posts = [(h, p) for h, p, m, q in fixture.seen if m == "POST"]
        require(posts == [(OLD, "/"), (OLD, "/__redirect-health")], "expected exactly two apex POSTs")
        total += 2
        print(f"PASS {phase} POST probes: 2 checks; exactly two empty POST requests")
        for case in cases[:2]:
            for label, code, changes, reason in (
                ("status 200", 200, {}, "status 200"),
                ("redirect 301", 301, {"location": "https://" + NEW + "/"}, "status 301"),
                ("missing Allow", 405, {"allow": None}, "Allow"),
                ("wrong Allow", 405, {"allow": "POST"}, "Allow"),
                ("Location on 405", 405, {"location": "https://" + NEW + "/"}, "Location"),
            ):
                def mutate(h, p, m, q, r, code=code, changes=changes):
                    headers = {**r.headers, **changes}
                    return Response(code, {k: v for k, v in headers.items() if v is not None})
                fixture.change = mutate
                fixture.seen.clear()
                result = evaluate(case)
                require(not result.passed and reason in result.detail, repr(result))
                require(len(fixture.seen) == 1 and fixture.seen[0][2] == "POST",
                        "POST probe followed a redirect or sent extra requests")
                total += 1
                print(f"PASS {phase} {case.name} rejects {label}: {result.detail}")
        fixture.change = None
    for phase in ("passthrough", "final"):
        fixture.seen.clear()
        try:
            list(checks(phase, fetch, probe_post=True))
        except ValueError as error:
            require("--probe-post requires" in str(error) and not fixture.seen,
                    "invalid POST phase sent requests")
        else:
            raise ValueError("POST probe accepted phase " + phase)
    return total


def targeted_self_tests(fixture, fetch):
    """Wrong values with successful status must fail for the named reason."""
    def refuse(phase, name, mutate, reason):
        fixture.phase, fixture.change = phase, None
        case = next(case for case in checks(phase, fetch) if case.name == name)
        fixture.change = mutate
        result = evaluate(case)
        fixture.change = None
        require(not result.passed and reason in result.detail, f"planted {name}: {result}")

    def headers(**changes):
        return lambda h, p, m, q, r: Response(r.status, {**r.headers, **changes}, r.body)

    refuse("passthrough", "www to apex /", headers(location="https://example.invalid/"), "Location")
    refuse("fallback", "app " + OLD + " GET /offer.json", headers(**{"x-served-by": "wrong"}), "X-Served-By")
    refuse("fallback", "app " + OLD + " GET /offer.json", headers(**{"content-type": "text/plain"}), "Content-Type")
    refuse("fallback", "fallback page " + OLD + " GET /", headers(**{"retry-after": ""}), "Retry-After")
    refuse("redirect", "health " + OLD, headers(**{"x-mode": "fallback"}), "X-Mode")
    refuse("redirect", "health " + OLD,
           lambda h, p, m, q, r: Response(r.status, r.headers, b"wrong"), "health body")
    refuse("redirect", "redirect page " + OLD + " GET " + REDIRECTS[3],
           headers(location="https://" + NEW + "/upper/path?keep=/"), "Location")
    refuse("redirect", "app " + OLD + " GET /offer.json",
           lambda h, p, m, q, r: Response(r.status, r.headers, b"changed") if h == OLD else r, "hashes differ")
    release_name = "release HEAD and Range " + OLD + " /updates/1.2.3/Docket.app.tar.gz"
    refuse("fallback", release_name, headers(**{"content-range": "bytes 1-1/100"}), "Content-Range")
    refuse("fallback", release_name,
           lambda h, p, m, q, r: Response(r.status, r.headers, b"xx") if q.get("Range") else r, "Content-Length")
    refuse("redirect", release_name,
           lambda h, p, m, q, r: Response(r.status, r.headers, r.body + b"wrong")
           if h == OLD and m == "GET" and not q.get("Range") else r, "full release hashes differ")
    for old_value, new_value, name, reason in (
        (b'rel="canonical" href="https://' + NEW.encode(), b'rel="canonical" href="https://' + OLD.encode(), "page metadata /", "canonical"),
        (b'property="og:url" content="https://' + NEW.encode(), b'property="og:url" content="https://' + OLD.encode(), "page metadata /", "og:url"),
        (b'property="og:image" content="https://' + NEW.encode(), b'property="og:image" content="https://' + OLD.encode(), "page metadata /", "og:image"),
        (b"pa-l5xLCLM0WKYQNcrCFH9qg.js", b"script.js", "Plausible /", "site-bound Plausible loader"),
        (b"plausible.q", b"plausible.z", "Plausible /", "queue stub"),
        (NEW.encode(), OLD.encode(), "sitemap new host", "wrong host"),
        (b"# Check Engine SEO.", b"# Docket SEO.", "robots", "first line"),
        (b"Sitemap: https://" + NEW.encode(), b"Sitemap: https://" + OLD.encode(), "robots", "Sitemap line"),
    ):
        refuse("final", name, lambda h, p, m, q, r, a=old_value, b=new_value:
               Response(r.status, r.headers, r.body.replace(a, b)), reason)
    refuse("final", "OG PNG", lambda h, p, m, q, r:
           Response(r.status, r.headers, r.body[:16] + struct.pack(">II", 800, 400) + r.body[24:]), "1200x630")
    refuse("final", "updater URLs", lambda h, p, m, q, r:
           Response(r.status, r.headers, r.body.replace(OLD.encode(), b"third-party.invalid")), "allowlist")
    refuse("final", "updater HEAD Range https://" + OLD + "/updates/1.2.3/Docket.app.tar.gz",
           headers(**{"content-range": ""}), "Content-Range")
    refuse("final", "HTML inventory", lambda h, p, m, q, r:
           Response(r.status, r.headers, b'[]'), "invalid redirect inventory")
    for leak in (OLD, "https://" + OLD + "/pricing/", "other@" + OLD,
                 "https://" + OLD + "/updater.json.evil", "mcp." + OLD + ".evil",
                 "support@" + OLD + ".evil", "https://" + OLD + "/bot.evil",
                 f'<span data-brand-history>past</span>{OLD}'):
        refuse("final", "old host scan /extra/index.html", lambda h, p, m, q, r, value=leak:
               Response(r.status, r.headers, r.body + value.encode()), "old host outside")
    fixture.phase, fixture.change = "final", None
    for allowed in ("support@" + OLD, "support@" + OLD + ".", "hello@" + OLD, "https://" + MCP + "/mcp",
                    OLD + "/data/knowledge.json. Offline mode.",
                    *("https://" + OLD + p for p in APPS),
                    "https://" + OLD + "/updates/1.2.3/file.exe",
                    f'<section data-brand-history><p>{OLD}</p></section>',
                    f'<img data-brand-history alt="{OLD}">'):
        old_host_leaks(Response(200, {"Content-Type": "text/html"}, allowed.encode()), OLD)
    print("PASS planted header, body, metadata, URL, image and old-host failures")


def safety_self_tests():
    live = LiveFetch()
    for url in ("http://" + OLD, "https://" + OLD + ".evil/", "https://user@" + OLD + "/",
                "https://" + OLD + ":443/", "https://example.invalid/", "https://" + OLD + "/#fragment"):
        try:
            live(url)
        except ValueError:
            pass
        else:
            raise ValueError("unsafe URL accepted: " + url)
    try:
        live("https://" + OLD + "/updater.json", "POST")
    except ValueError:
        pass
    else:
        raise ValueError("POST accepted")
    # Every case must fail before reaching the opener, even with POST enabled.
    live = LiveFetch(probe_post=True)
    for url, method, headers in (
        ("https://" + OLD + "/updater.json", "POST", None),
        ("https://www." + OLD + "/", "POST", None),
        ("https://" + NEW + "/", "POST", None),
        ("https://" + OLD + "/?probe=1", "POST", None),
        ("https://" + OLD + "/", "PUT", None),
        ("https://" + OLD + "/", "POST", {"Cookie": "test=1"}),
        ("https://" + OLD + "/", "POST", {"Authorization": "test"}),
    ):
        try:
            live(url, method, headers)
        except ValueError:
            pass
        else:
            raise ValueError("unsafe opt-in method or URL accepted: " + method + " " + url)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=PHASES)
    parser.add_argument("--old", default=OLD, choices=(OLD,))
    parser.add_argument("--new", default=NEW, choices=(NEW,))
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--probe-post", action="store_true",
                        help="send two empty POST probes in fallback or redirect mode")
    args = parser.parse_args()
    if args.probe_post and args.phase not in {"fallback", "redirect"}:
        parser.error("--probe-post requires --phase fallback or --phase redirect")
    if args.self_test:
        return self_test()
    if not args.phase:
        parser.error("--phase is required unless --self-test is used")
    return print_results([evaluate(case) for case in checks(
        args.phase, LiveFetch(args.old, args.new, args.probe_post),
        args.old, args.new, args.probe_post)])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        print("FAIL " + str(error))
        raise SystemExit(1)
