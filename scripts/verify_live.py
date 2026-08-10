#!/usr/bin/env python3
"""Check what the CDN actually serves, after the deploy.

Every other gate reads files on disk before they are published. That misses an
entire class of failure: a page that builds correctly and is then served stale,
404s, loses an asset, or renders differently once a Content-Security-Policy is
applied. "The built file is right" and "the reader gets the right thing" are
different claims and only the second one matters.

The gap was real and observed. Deploying the derived download size produced a
correct local file and a live page still reading "17 MB" for several minutes;
it looked exactly like a third hardcoded copy until the artifact was checked.

Run AFTER ./scripts/deploy.sh. It is not part of the deploy, deliberately: a
propagation delay is normal and should not fail a publish that was correct.

Renders through Docket's own `docket-render`, which is the same WebKit the
product uses — so the site is verified with the tool it sells.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import urllib.request

BASE = "https://docketseo.app"

PAGES = ["/", "/download/", "/learn/", "/for/", "/for/developers/",
         "/for/ecommerce/", "/vs/", "/index/", "/about/", "/how-to/"]

def _homepage_must_say() -> list[str]:
    """Claims that must be true on the live homepage.

    Derived, not typed. The check count was pinned here as the literal string
    "93 checks" — this gate existed to catch a fact that had drifted, and was
    itself a second copy of one. Adding a check would have failed it while the
    site was perfectly correct, which is the failure mode that gets a gate
    switched off rather than fixed.
    """
    import csv
    path = pathlib.Path(__file__).resolve().parent.parent / "site" / "_data" / "checks.csv"
    with path.open() as fh:
        n = sum(1 for _ in csv.DictReader(fh))
    if not n:
        raise SystemExit("checks.csv is empty — refusing to verify against nothing")
    return [f"{n} checks", "$149"]


HOMEPAGE_MUST_SAY = _homepage_must_say()

#: Text that must NOT appear anywhere. The old brand and the old accent are
#: both things a stale deploy would resurrect silently.
#: Regexes, not literals. The list held the exact string "Nothing leaves"
#: and the comparison pages shipped "Never leaves your Mac" for weeks — the
#: same false claim, one word away from the gate.
MUST_NOT_SAY = [
    r"Scout", r"F0800F",
    r"(?i)\b(nothing|no data|never)\s+leaves\b",
    # "The only requests Docket makes are to the site you are auditing"
    # was the same false claim in a wording with no "leaves" in it, so the
    # rule above walked straight past it. Four connectors reach
    # docketseo.app, Google and DNS on a default run.
    #
    # And then the homepage said "the only **network** requests Docket makes",
    # one word inside the phrase this rule was written for, and it walked past
    # that too — in the FAQ and in the FAQPage schema, which is the copy search
    # engines can lift into a result. So the rule now tolerates a couple of
    # words in the middle, and covers the passive form as well.
    r"(?i)only\s+(?:\w+\s+){0,2}requests?\s+(?:Docket|it|the app)\s+makes",
    r"(?i)only\s+(?:\w+\s+){0,2}requests?\s+are\s+to\s+the\s+site",
]

#: Pages allowed to contain a banned phrase, and why.
#:
#: The privacy policy quotes the old sentence in order to correct it — "An
#: earlier version of this policy said the only network requests the app makes
#: are to the website you ask it to audit. That was not accurate" — and a gate
#: that forbade the quotation would force the correction to be deleted to pass,
#: which is the opposite of what it is for.
QUOTED_TO_CORRECT_IT = {
    "/legal/privacy/": (r"(?i)only\s+(?:\w+\s+){0,2}requests?\s+(?:Docket|it|the app)\s+makes",),
}

#: A width where layout breaks, and one where it does not. Both, because a
#: page can be clean at one and broken at the other.
WIDTHS = [375, 1600]

PROBE = """(function(){
  var de = document.documentElement, clipped = [];
  document.querySelectorAll('a,h1,h2,p,li,button').forEach(function(el){
    var r = el.getBoundingClientRect();
    if (r.width > 0 && r.right > de.clientWidth + 1) {
      clipped.push(el.tagName + ':' + (el.innerText||'').trim().slice(0,24));
    }
  });
  var squashed = [];
  document.querySelectorAll('table,pre').forEach(function(t){
    // A scroller is only NEEDED when the content is wider than its box.
    if (t.scrollWidth > t.clientWidth + 1 &&
        getComputedStyle(t.parentElement).overflowX !== 'auto' &&
        getComputedStyle(t).overflowX !== 'auto') squashed.push(t.tagName);
  });
  return {overflow: de.scrollWidth > de.clientWidth + 1,
          clipped: clipped.slice(0,5), squashed: squashed};
})()"""


def _renderer() -> pathlib.Path:
    for candidate in (
        pathlib.Path("/Users/matthewkerr/Downloads/SEO audit app/packaging/render/docket-render"),
        pathlib.Path("/Applications/Docket.app/Contents/Resources/docket/docket-render"),
    ):
        if candidate.is_file():
            return candidate
    raise SystemExit("docket-render not found — build the app first")


def _fetch(path: str) -> tuple[int, str]:
    request = urllib.request.Request(
        BASE + path, headers={"User-Agent": "docketseo-live-gate/1.0",
                              "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except Exception as exc:                              # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


def _download_links(body: str) -> list:
    """Every release-asset URL the page offers."""
    return sorted(set(re.findall(
        r'href="(https://github\.com/[^"]+/releases/download/[^"]+)"', body)))


def _check_downloads(body: str) -> list:
    """Every advertised download must actually be there.

    This project calls a 404 download link the single worst bug a product site
    can have, and nothing checked them. The Linux CLI was described in detail on
    the download page while no Linux asset had been published since 0.1.0 —
    seven releases — because the publish step only ever named the DMG and the
    updater tarball. Nothing failed; the page simply offered a platform that had
    quietly stopped shipping.
    """
    problems = []
    links = _download_links(body)
    if not links:
        return ["the download page offers no release asset at all"]

    # The page documents `shasum -a 256 -c` against a published SHA256SUMS.
    # That command fails for every reader the moment an artifact is published
    # without refreshing the file, so the coverage is checked rather than the
    # file's mere existence. Hashing the artifacts themselves would mean pulling
    # ~31 MB on every deploy; publish_checksums.sh verifies them against dist/
    # at publish time, which is where a mismatch can still be fixed.
    sums_url = next((u for u in links if u.endswith("/SHA256SUMS")), "")
    if not sums_url:
        problems.append("no SHA256SUMS is offered, but the page tells the "
                        "reader to check one")
    else:
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    sums_url, headers={"User-Agent": "docketseo-live-gate/1.0"}),
                    timeout=25) as response:
                sums = response.read().decode("utf-8", "replace")
        except Exception as exc:                              # noqa: BLE001
            sums = ""
            problems.append(f"SHA256SUMS could not be read: {exc}")
        for url in links:
            name = url.rsplit("/", 1)[-1]
            if name != "SHA256SUMS" and sums and name not in sums:
                problems.append(f"{name} is offered for download but is not in "
                                f"SHA256SUMS, so the verification command the "
                                f"page prints fails for it")
    for url in links:
        request = urllib.request.Request(url, method="HEAD", headers={
            "User-Agent": "docketseo-live-gate/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                if response.status != 200:
                    problems.append(f"{url} returned {response.status}")
                elif not int(response.headers.get("Content-Length") or 0):
                    problems.append(f"{url} is zero bytes")
        except Exception as exc:                              # noqa: BLE001
            problems.append(f"{url} → {type(exc).__name__}: {exc}")
    return problems


def main() -> None:
    renderer = _renderer()
    failures: list[str] = []

    for path in PAGES:
        status, body = _fetch(path)
        if status != 200:
            failures.append(f"{path} returned {status or body[:60]}")
            continue
        for bad in MUST_NOT_SAY:
            if bad in QUOTED_TO_CORRECT_IT.get(path, ()):
                continue
            # re.search, not `in`. These became regexes and the substring test
            # was left behind, which would have matched nothing at all — a gate
            # that cannot fail, added in the act of widening it.
            hit = re.search(bad, body)
            if hit:
                failures.append(f"{path} still contains {hit.group(0)!r}")
        if path == "/":
            for claim in HOMEPAGE_MUST_SAY:
                if claim not in body:
                    failures.append(f"homepage no longer says {claim!r}")
        if path == "/download/":
            failures.extend(_check_downloads(body))

    # Rendering is slow, so it runs over a representative few rather than all
    # ten — and says which, because a gate that quietly samples reads as a gate
    # that checked everything.
    rendered = PAGES[:4]
    for path in rendered:
        for width in WIDTHS:
            proc = subprocess.run(
                [str(renderer), BASE + path, "--width", str(width),
                 "--height", "900", "--settle", "1.5", "--probe", PROBE],
                capture_output=True, text=True, timeout=90)
            if proc.returncode != 0:
                failures.append(f"{path}@{width} render failed: {proc.stderr.strip()[:70]}")
                continue
            try:
                data = json.loads(proc.stdout)
            except json.JSONDecodeError:
                failures.append(f"{path}@{width} probe returned no JSON")
                continue
            if data.get("overflow"):
                failures.append(f"{path}@{width} scrolls horizontally")
            if data.get("clipped"):
                failures.append(f"{path}@{width} clipped: {data['clipped']}")
            if data.get("squashed"):
                failures.append(f"{path}@{width} unscrollable wide content: {data['squashed']}")

    if failures:
        print("LIVE FAIL — what the CDN is serving does not match what was built:")
        for failure in failures:
            print(f"  {failure}")
        sys.exit(1)

    print(f"LIVE ok — {len(PAGES)} pages 200 and clean, "
          f"{len(rendered)} rendered at {WIDTHS[0]}px and {WIDTHS[1]}px "
          f"({', '.join(rendered)})")


if __name__ == "__main__":
    main()
