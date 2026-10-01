#!/usr/bin/env python3
"""What this site's scripts may request from our own hosts, and how.

WHY (CEO, 2026-10-01). Between 03:40Z and 04:40Z something fetched 11 of this
site's Buy links and 7 of its Download links through the hub with GET. A GET of
/buy/docket mints a real Dodo checkout session whenever the requester looks
like a browser, and a GET of /dl counts a download. outlier.host's rival-price
gate was doing exactly that. Reading every script here that makes a request
found none that GETs a hub link, but it found two patterns that could, or
already did the same kind of thing elsewhere:

  * The source checkers (verify_claim_sources.py, watch_sources.py) request
    whatever URL is in their list, with a browser user agent and, for the
    first, a GET fallback. A hub link typed into either list would be fetched
    as a browser, which mints a session.
  * urllib follows a redirect by rebuilding the request WITHOUT its method, so
    a HEAD that meets a 302 arrives at the next host as a GET. Read in the
    stdlib of both Pythons used here (3.9.6 and 3.11.16). verify_download_path,
    verify_live and verify_contact all HEAD URLs that redirect, the GitHub
    release links among them, so each "HEAD" fetched the file it pointed at.

The rules, in one place:

  1. A checker of THIRD-PARTY pages never requests one of our own hosts:
     `is_own()`.
  2. A hub link that must be checked gets exactly one HEAD, redirect not
     followed, with the kerr-ops user agent, which the hub never records:
     `head_no_follow()`.
  3. A HEAD that follows redirects stays a HEAD at every hop: `HEAD_OPENER`.

    python3 scripts/own_hosts.py --self-test     # plants a hub link; no network
"""
from __future__ import annotations

import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

#: Hosts that are ours or that act for us at checkout. A suffix matches the
#: host itself and any subdomain. Every *.kerrco.workers.dev Worker is ours
#: (the hub, the lead agent, the subscribe and checker workers).
OWN_HOST_SUFFIXES = (
    "kerrco.workers.dev",
    "dodopayments.com",
    "docketseo.app",
    "outlier.host",
    "crispvideo.app",
    "adplaybook.app",
    "builtbykerr.com",
    "kerrandcompanyholdings.com",
    "matthewkerr.dev",
    "release-assets.githubusercontent.com",
    "objects.githubusercontent.com",
)
#: Our own paths on a shared host: the release downloads and the repos.
OWN_URL_PREFIXES = ("https://github.com/mattkerr09/",)

HUB = "kerr-affiliate-hub.kerrco.workers.dev"


def is_own(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if any(host == s or host.endswith("." + s) for s in OWN_HOST_SUFFIXES):
        return True
    return url.startswith(OWN_URL_PREFIXES)


def ops_headers(check: str) -> dict:
    """The ops user agent. The hub writes no row for it (CEO, 2026-09-29)."""
    return {"User-Agent": f"kerr-ops/1.0 ({check})"}


class _KeepHead(urllib.request.HTTPRedirectHandler):
    """Follow a redirect with the method the request was made with."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and req.get_method() == "HEAD":
            new.method = "HEAD"
        return new


class _NoFollow(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: D401
        return None


#: For a HEAD that should follow redirects (a GitHub release link: 302 to the
#: asset store) without fetching the file at the end.
HEAD_OPENER = urllib.request.build_opener(_KeepHead)
_NOFOLLOW_OPENER = urllib.request.build_opener(_NoFollow)


def head_no_follow(url: str, check: str, timeout: float = 20) -> tuple:
    """One HEAD, redirect not followed. (status, Location); status 0 = no answer."""
    req = urllib.request.Request(url, method="HEAD", headers=ops_headers(check))
    try:
        with _NOFOLLOW_OPENER.open(req, timeout=timeout) as resp:
            return resp.status, resp.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Location", "") if exc.headers else ""
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


# --------------------------------------------------------------------------
# self-test: a local server only, never the network


class _Log(BaseHTTPRequestHandler):
    seen: list = []

    def _answer(self):
        _Log.seen.append((self.command, self.path, self.headers.get("User-Agent", "")))
        if self.path.startswith("/r"):
            self.send_response(302)
            self.send_header("Location", "/t")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        body = b"x" * 10
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command == "GET":
            self.wfile.write(body)

    do_GET = do_HEAD = _answer

    def log_message(self, *args):  # noqa: D102
        pass


def _self_test() -> int:
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent / "articles"))
    failures: list = []

    server = HTTPServer(("127.0.0.1", 0), _Log)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"

    def methods_at(path):
        return [m for m, p, _ in _Log.seen if p == path]

    # 1. The control: plain urllib turns HEAD into GET at the redirect target.
    #    If it ever stops doing that, this test can no longer see a regression.
    _Log.seen.clear()
    urllib.request.urlopen(urllib.request.Request(base + "/r", method="HEAD"), timeout=5).close()
    if methods_at("/t") != ["GET"]:
        failures.append(f"control: plain urllib HEAD reached the target as {methods_at('/t')}, "
                        "not GET; the HEAD-preservation test below proves nothing")

    # 2. HEAD_OPENER keeps it a HEAD.
    _Log.seen.clear()
    HEAD_OPENER.open(urllib.request.Request(base + "/r", method="HEAD"), timeout=5).close()
    if methods_at("/t") != ["HEAD"]:
        failures.append(f"HEAD_OPENER reached the target as {methods_at('/t')}")

    # 3. head_no_follow: one HEAD, the redirect reported and not followed.
    _Log.seen.clear()
    status, location = head_no_follow(base + "/r", "own_hosts-self-test")
    if (status, location) != (302, "/t") or [m for m, _, _ in _Log.seen] != ["HEAD"] \
            or not _Log.seen[0][2].startswith("kerr-ops/1.0"):
        failures.append(f"head_no_follow: {status} {location!r}, requests {_Log.seen}")

    # 4. Every script that HEADs a redirecting URL keeps it a HEAD.
    import verify_contact
    import verify_download_path
    import verify_live
    for name, call in (
        ("verify_download_path._head", lambda: verify_download_path._head(base + "/r")),
        ("verify_contact.reachable", lambda: verify_contact.reachable(base + "/r")),
        ("verify_live._open_with_retry", lambda: verify_live._open_with_retry(
            urllib.request.Request(base + "/r", method="HEAD")).close()),
    ):
        _Log.seen.clear()
        call()
        if methods_at("/t") != ["HEAD"]:
            failures.append(f"{name} reached the redirect target as {methods_at('/t')}")

    # 5. A hub Buy link planted in each third-party source list is never
    #    requested, and the control (the guard switched off) does request it.
    planted = f"https://{HUB}/buy/docket?src=planted-by-self-test"
    import comparisons
    import verify_claim_sources
    import watch_sources

    requested: list = []
    real_urlopen, real_open = urllib.request.urlopen, urllib.request.OpenerDirector.open

    def record_urlopen(req, *a, **k):
        requested.append(req.full_url if hasattr(req, "full_url") else str(req))
        raise urllib.error.URLError("self-test: no network")

    def record_open(self, req, *a, **k):
        requested.append(req.full_url if hasattr(req, "full_url") else str(req))
        raise urllib.error.URLError("self-test: no network")

    import own_hosts as mod  # the copy the scripts import, not this __main__
    saved_verified, saved_sources = comparisons.VERIFIED, watch_sources.SOURCES
    saved_is_own = mod.is_own
    try:
        urllib.request.urlopen = record_urlopen
        urllib.request.OpenerDirector.open = record_open
        comparisons.VERIFIED = {"planted": [("a planted claim", planted)]}
        watch_sources.SOURCES = {"planted": (planted, "a planted source")}

        def run_both():
            requested.clear()
            verify_claim_sources._status(planted)
            watch_sources.fetch(planted)
            return list(requested)

        guarded = run_both()
        if planted in guarded:
            failures.append(f"a planted hub link was requested {guarded.count(planted)} time(s) "
                            "by the source checkers")
        # control: the same plant with the guard switched off must be requested
        mod.is_own = lambda url: False
        unguarded = run_both()
        if planted not in unguarded:
            failures.append("control: with the guard off the planted link was not requested, "
                            "so this test cannot see the guard fail")
    finally:
        urllib.request.urlopen, urllib.request.OpenerDirector.open = real_urlopen, real_open
        comparisons.VERIFIED, watch_sources.SOURCES = saved_verified, saved_sources
        mod.is_own = saved_is_own
        server.shutdown()

    if failures:
        print("OWN HOSTS FAIL")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("OWN HOSTS ok — HEAD stays HEAD across redirects (control: plain urllib "
          "sends GET); hub links get one unfollowed HEAD as kerr-ops; a planted hub "
          "link is never requested by the source checkers (control: requested "
          "with the guard off)")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    print(__doc__)
