#!/usr/bin/env python3
"""Does the app we ship validate keys from the vendor the site takes money at?

**The failure this exists for very nearly happened on 2026-08-19.** Docket was
rebuilt stamped for Dodo while the site's Buy button still pointed at Polar. The
two states are each fine on their own and lethal together: a customer pays on
Polar, receives a Polar key, and the app they download refuses it, because
`licence._provider()` dispatches on what the BUILD was stamped with and asks
only that vendor.

Nothing would have caught it. The checkout gate proves the button charges the
right price. The download gate proves the DMG is reachable. Neither knows which
vendor the binary behind the link will accept a key from, so both stay green
while the two halves of the money path disagree.

WHAT IT COMPARES

  the site  — the checkout host in the Buy links of the pages about to deploy
  the app   — which vendor the built sidecar names when it rejects a key

WHAT IT DOES NOT

  It reads `dist/` — the build about to be shipped — and NOT the installed copy
  in /Applications. What this machine has installed is not what a customer
  downloads, and letting it decide would block a legitimate site deploy over a
  local experiment. That is exactly what happened the first time this was run.

  It also cannot see a release published from another machine, and it says so
  rather than reporting OK on something it never looked at. A gate that cannot
  see its subject must never print a pass — this codebase has shipped that bug
  twice and written it down both times.

    python3 scripts/verify_vendor_match.py
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
DIST = pathlib.Path.home() / "Projects" / "docket-app" / "dist"

#: Checkout hosts, mapped to the vendor name the sidecar uses in its messages.
_HOSTS = {
    "buy.polar.sh": "polar",
    "polar.sh": "polar",
    "checkout.dodopayments.com": "dodo",
    "dodopayments.com": "dodo",
}

_LINK = re.compile(r'href="https?://([^/"]+)/[^"]*"')


def site_vendor() -> tuple:
    """(vendor, evidence). Reads the built pages, not the live site: this runs
    before publish, and the point is to stop the deploy."""
    found: dict = {}
    for page in sorted(SITE.rglob("*.html")):
        for host in _LINK.findall(page.read_text(encoding="utf-8", errors="replace")):
            vendor = _HOSTS.get(host.lower())
            if vendor:
                found.setdefault(vendor, set()).add(str(page.relative_to(SITE)))
    if not found:
        return "", "no checkout link found on any page"
    if len(found) > 1:
        where = "; ".join(f"{v}: {sorted(p)[0]}" for v, p in found.items())
        return "MIXED", f"the site links BOTH vendors — {where}"
    vendor = next(iter(found))
    pages = found[vendor]
    return vendor, f"{len(pages)} page(s) link {vendor}"


def app_vendor() -> tuple:
    """(vendor, evidence) from the built sidecar, by asking it to reject a key.

    Deliberately behavioural. Reading build_info.py would prove a line exists;
    this proves which vendor the shipped code actually asks, which is the thing
    a customer meets.
    """
    # dist/ ONLY. /Applications is whatever this machine happens to have
    # installed — it is not what a customer downloads, and letting it decide
    # would block a legitimate deploy over a local experiment. dist/ is the
    # build about to be shipped, which is the thing the site has to agree with.
    # is_file() matters: dist/ holds a DIRECTORY called `docket` next to the
    # binary inside it, and globbing without this check hands subprocess a
    # directory and reports "Permission denied" as though the gate were broken.
    # The same confusion shipped once already, as an unhandled traceback when a
    # customer passed `-o <a directory>`.
    binaries = [b for b in sorted(DIST.glob("*/docket")) + sorted(DIST.glob("docket"))
                if b.is_file()]
    if not binaries:
        return "", ("no built sidecar in dist/ — nothing compared, which is not "
                    "a pass. Build before shipping, or run this after a build.")
    # dist/ holds artifacts for more than one platform. A Linux binary cannot
    # exec on macOS, and treating that as a failure made the gate refuse a
    # perfectly good deploy the moment a Linux tarball was built beside the Mac
    # one. Try each candidate and use the first that actually runs; only refuse
    # when NONE do, because "nothing compared" is the one thing that must never
    # print a pass.
    said, binary, skipped = "", None, []
    for candidate in reversed(binaries):
        try:
            r = subprocess.run([str(candidate), "licence", "--key", "VENDOR-MATCH-PROBE-0000"],
                               capture_output=True, text=True, timeout=90)
        except (subprocess.SubprocessError, OSError) as e:
            skipped.append(f"{candidate.parent.name}/{candidate.name} ({type(e).__name__})")
            continue
        said, binary = (r.stdout + r.stderr).lower(), candidate
        break
    if binary is None:
        return "", ("no sidecar in dist/ could be run here" +
                    (f" — skipped {', '.join(skipped)}" if skipped else "") +
                    ". Nothing compared, which is not a pass.")
    if "not licensed" in said:
        return "free", f"{binary.name} is a free build (no entitlement stamp)"
    for vendor in ("dodo", "polar"):
        if vendor in said:
            return vendor, f"{binary.name} names {vendor} when refusing a key"
    return "", f"{binary.name} named no vendor: {said.strip()[:120]!r}"


def site_version() -> str:
    """The version the site is about to advertise."""
    dl = SITE / "download" / "index.html"
    if not dl.is_file():
        return ""
    m = re.search(r"\b(\d+\.\d+\.\d+)\b", dl.read_text(encoding="utf-8", errors="replace"))
    return m.group(1) if m else ""


def dist_version() -> str:
    """The version sitting in dist/, from the DMG filename."""
    for dmg in sorted(DIST.glob("Docket-*.dmg")):
        m = re.search(r"Docket-(\d+\.\d+\.\d+)-", dmg.name)
        if m:
            return m.group(1)
    return ""


def main() -> int:
    sv, se = site_vendor()
    av, ae = app_vendor()
    site_v, dist_v = site_version(), dist_version()
    print(f"  site: {sv or '?':6} — {se}")
    print(f"  app : {av or '?':6} — {ae}")

    if not sv or sv == "MIXED":
        print(f"\nVENDOR FAIL — {se}")
        return 1
    if not av:
        print(f"\nVENDOR FAIL — {ae}. Nothing was compared, which is not a pass.")
        return 1
    if av == "free":
        print("\nVENDOR ok — the app is a free build, so no key is ever asked for "
              "and there is no vendor to disagree about.")
        return 0
    if av != sv and site_v and dist_v and site_v != dist_v:
        # dist/ holds a build the site is not advertising, so these two halves
        # are not being shipped together and this is not the dangerous pair. Say
        # it rather than blocking a site-only deploy over a local experiment —
        # but say it loudly, because it becomes real the moment that build ships.
        print(f"\nVENDOR note — dist/ holds {dist_v} stamped for {av} while the site "
              f"advertises {site_v} on {sv}.")
        print("  Not blocking: these are not being shipped together. It becomes a "
              f"FAIL the moment {dist_v} is released without the Buy links moving.")
        return 0
    if av != sv:
        print(f"\nVENDOR FAIL — the site takes money at {sv} and the app validates "
              f"keys against {av}.")
        print("  A customer pays, receives a "
              f"{sv} key, and the app they download refuses it. Each half is fine "
              "alone; together they are a paid product that cannot be unlocked.")
        print("  Fix by moving BOTH: the Buy links and the build stamp "
              "(DODO_PRODUCT_ID for dodo, unset for polar).")
        return 1
    print(f"\nVENDOR ok — site and app both on {sv}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
