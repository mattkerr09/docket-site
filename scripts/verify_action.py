#!/usr/bin/env python3
"""The GitHub Action must be able to install what it says it installs.

Two failures, both live, both found on 2026-08-12:

  * `version` was decorative. The URL path used the input but the DMG filename
    was hardcoded to `Docket-0.1.0-arm64.dmg`, so the default worked and every
    other value fetched an asset that does not exist in that release. Anyone
    who set `version:` exactly as its own description told them to got a 404
    and a failed step.
  * The default was `v0.1.0` — a build from long before the current one, still
    published, so it installed fine and quietly audited with an engine dozens
    of releases old.

Neither is visible by reading the file. The first needs the release listing to
know the asset is absent; the second needs it to know a newer tag exists. So
this asks GitHub.

**Network, and what happens without it.** This reaches api.github.com. When it
cannot — offline, rate-limited, no `gh` — it prints why and returns 0 rather
than failing the deploy, because a gate that blocks shipping whenever the
network hiccups is a gate that gets commented out. The local half — that the
filename is derived from the tag rather than written twice — is checked with no
network at all and always fails hard, because it is the half that made the
input a lie.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTION = ROOT / "action.yml"

REPO = "mattkerr09/docket-site"


def _fail(msg: str) -> int:
    print(f"ACTION FAIL — {msg}", file=sys.stderr)
    return 1


def main() -> int:
    text = ACTION.read_text()

    # Comments are excluded, and the first version of this gate did not do that
    # — it flagged its own explanatory comment quoting the old filename, and
    # failed on a correct file. The scanner has to read what the action runs,
    # not what it says about itself.
    code = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))

    # -- local: the filename must come from the tag ------------------------
    hardcoded = re.findall(r"Docket-\d+\.\d+\.\d+-arm64\.dmg", code)
    if hardcoded:
        return _fail(
            f"action.yml hardcodes a DMG filename ({hardcoded[0]}) while taking "
            f"a `version` input. Any version but that one 404s, which makes the "
            f"input decorative. Derive it: DMG=\"Docket-${{TAG#v}}-arm64.dmg\"")

    if 'DMG="Docket-${TAG#v}-arm64.dmg"' not in code:
        return _fail(
            "action.yml no longer derives the DMG filename from the version "
            "tag, so this gate cannot tell whether the input works")

    match = re.search(r"version:.*?default: '(v[\d.]+)'", text, re.S)
    if not match:
        return _fail("cannot find the `version` input's default in action.yml")
    default = match.group(1)

    # -- network: the default must exist, and be current -------------------
    try:
        out = subprocess.run(
            ["gh", "release", "list", "--repo", REPO, "--limit", "1",
             "--json", "tagName"],
            capture_output=True, text=True, timeout=25)
        latest = json.loads(out.stdout)[0]["tagName"] if out.returncode == 0 else None
    except Exception as e:  # noqa: BLE001 — any failure here means "could not ask"
        latest = None
        print(f"ACTION note — could not reach GitHub ({type(e).__name__}); the "
              f"default tag {default} was not checked against the release list")

    if latest is None:
        print(f"ACTION ok (local only) — filename derived from the tag, "
              f"default {default}. The release list was not reachable, so "
              f"whether {default} is current is unverified.")
        return 0

    if default != latest:
        return _fail(
            f"action.yml installs {default} by default and the latest release "
            f"is {latest}. Every consumer of this action audits with an engine "
            f"that many releases old without being told.")

    print(f"ACTION ok — default {default} is the latest release, and the DMG "
          f"filename is derived from the tag rather than written twice")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
