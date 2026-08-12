#!/usr/bin/env python3
"""Every contact channel this site advertises must actually accept a message.

The footer of all 25 pages offered `hello@docketseo.app`. The domain has no MX
record. Under RFC 5321 §5.1 a sender that finds none falls back to the domain's
address record, which for this site is GitHub Pages, and nothing answers there
on port 25. So every message anyone sent bounced — to them, silently, with
nobody here ever learning a message had been attempted.

That is a nastier shape than a broken link. A 404 tells the visitor it failed.
A dead mailbox tells the visitor it worked.

Two rules, both about the same thing — a channel is only a channel if something
is listening at the other end:

  * Every `mailto:` domain must publish an MX record.
  * Every URL the site presents as a way to reach us must answer 2xx.

Usage:  python3 scripts/verify_contact.py
"""
from __future__ import annotations

import re
import subprocess
import sys
import urllib.error
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

MAILTO = re.compile(r'href="mailto:([^"?]+)')
HREF = re.compile(r'href="(https?://[^"]+)"')

#: Hosts whose URLs are contact channels rather than citations. A link to a
#: specification is a reference and may reasonably rot; a link that says "tell
#: us here" is a promise.
CONTACT_HOSTS = ("github.com/mattkerr09",)

#: A domain that genuinely accepts mail on its address record is legal under
#: RFC 5321 §5.1 and would fail the MX rule wrongly. Add it here with the
#: reason, the same way verify_numbers.py takes a constant with a reason —
#: an exception you have to write a sentence for is one you have thought about.
MX_EXEMPT: dict[str, str] = {}


def addresses() -> dict[str, set[str]]:
    """mailto domain -> the pages advertising it."""
    found: dict[str, set[str]] = {}
    for page in SITE.rglob("*.html"):
        rel = str(page.relative_to(SITE))
        for addr in MAILTO.findall(page.read_text()):
            domain = addr.rpartition("@")[2].lower().strip()
            if domain:
                found.setdefault(domain, set()).add(rel)
    return found


def contact_urls() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for page in SITE.rglob("*.html"):
        rel = str(page.relative_to(SITE))
        for url in HREF.findall(page.read_text()):
            if any(h in url for h in CONTACT_HOSTS):
                found.setdefault(url, set()).add(rel)
    return found


def has_mx(domain: str) -> tuple[bool, str]:
    """(accepts_mail, explanation). DNS failure is a failure, not a pass."""
    try:
        out = subprocess.run(["dig", "+short", "+time=3", "+tries=2", "MX", domain],
                             capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"could not query DNS ({exc}); re-run rather than deploy blind"
    if out.returncode != 0:
        return False, f"dig failed: {out.stderr.strip() or 'no output'}"
    records = [ln for ln in out.stdout.splitlines() if ln.strip()]
    if records:
        return True, f"{len(records)} MX record(s)"
    return False, ("no MX record — senders fall back to the address record per "
                   "RFC 5321 §5.1, which for a static-hosted domain does not "
                   "answer SMTP, so mail bounces")


#: Errors that mean "the network hiccuped", not "this channel is dead". GitHub
#: closes connections under a burst of HEADs, and a single one blocked a deploy
#: twice in a row here - naming three DIFFERENT dead URLs across two runs, which
#: is the signature of flakiness rather than breakage. Every URL it accused
#: returned 200 when checked by hand seconds later.
#:
#: A gate that fails on a transient error is worse than no gate: it gets
#: overridden, and then it is not a gate at all.
_TRANSIENT = (
    "RemoteDisconnected", "IncompleteRead", "ConnectionResetError",
    "TimeoutError", "socket.timeout", "URLError", "BadStatusLine",
)


def reachable(url: str, attempts: int = 3) -> tuple[bool, str]:
    """HEAD the URL, retrying transient failures with a growing pause.

    A real 404 or 410 is returned immediately - those are not flaky and
    retrying them only slows the deploy down.
    """
    last = ""
    for attempt in range(attempts):
        req = urllib.request.Request(url, method="HEAD",
                                     headers={"User-Agent": "docketseo-deploy-gate/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.status
        except urllib.error.HTTPError as exc:
            # An HTTP status is a real answer from a live server. Believe it.
            return (200 <= exc.code < 300), f"HTTP {exc.code}"
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
            if not any(t in last for t in _TRANSIENT) or attempt == attempts - 1:
                break
            time.sleep(1.5 * (attempt + 1))
            continue
        return (200 <= code < 300), f"HTTP {code}"
    return False, f"{last} (after {attempts} attempts)"


def main() -> int:
    problems: list[str] = []
    checked = 0

    for domain, pages in sorted(addresses().items()):
        checked += 1
        if domain in MX_EXEMPT:
            print(f"  {domain}: exempt — {MX_EXEMPT[domain]}")
            continue
        ok, why = has_mx(domain)
        if not ok:
            problems.append(f"mailto @{domain} on {len(pages)} page(s): {why}")
        else:
            print(f"  {domain}: {why}")

    for url, pages in sorted(contact_urls().items()):
        checked += 1
        ok, why = reachable(url)
        if not ok:
            problems.append(f"{url} on {len(pages)} page(s): {why}")

    if problems:
        print(f"CONTACT: {len(problems)} advertised channel(s) cannot receive anything")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"CONTACT ok — {checked} advertised channel(s), all reachable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
