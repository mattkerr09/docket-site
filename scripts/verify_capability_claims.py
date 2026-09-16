#!/usr/bin/env python3
"""The site must not concede a capability Docket actually ships.

    python3 scripts/verify_capability_claims.py

WHY THIS EXISTS (2026-09-16). The home page FAQ ended: "Screaming Frog renders
JavaScript and supports custom XPath extraction; Docket does not." The XPath
half is true. The rendering half had not been true since `AUTO_RENDER_PAGES`
was added — Docket renders a small sample of EVERY audit automatically, in
WebKit, where the helper is present.

That is the THIRD place one capability change failed to reach the prose
describing it. `renderer.py`'s module docstring said rendering was "off by
default" and `--render`'s help text said "it is off unless asked for"; both were
found and corrected in the app repo. This was the same root cause, on the
highest-traffic page on the site, and it was worse than stale: the page
CONTRADICTED ITSELF. Its own "absent on purpose" list names JavaScript rendering
among the things that came off it, and /vs/screaming-frog-alternative/ says
Docket renders in WebKit and renders a sample by default.

`verify_competitive_claims` passed it before and after the fix, and correctly
so — it polices what the site claims about RIVALS, where an unsourced claim is a
legal and reputational problem. Nothing policed what the site concedes about US.
A conceded capability is the cheap error to make and the expensive one to leave:
it is read as modesty, so nobody questions it, and it talks a reader out of a
feature they were about to pay for.

It is deliberately narrow. It does not read prose for truth — no gate can. It
asserts one thing: that no built page denies Docket runs JavaScript, which is a
capability the shipped CLI documents in `--render`'s own help text.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

#: A denial of rendering, within one sentence. The subject has to be Docket:
#: "Screaming Frog does not render JavaScript" would be a claim about a rival
#: and is `verify_competitive_claims`' business, not this script's.
DENIALS = [
    re.compile(r"Docket[^.]{0,120}?\b(?:does not|doesn't|cannot|can't|will not|won't)\b"
               r"[^.]{0,80}?\b(?:render|renders|rendering|run|runs|execute|executes)\b"
               r"[^.]{0,40}?JavaScript", re.I),
    re.compile(r"\b(?:render|renders|rendering|runs?)\b[^.]{0,60}?JavaScript[^.]{0,120}?;?\s*"
               r"Docket does not", re.I),
    re.compile(r"Docket[^.]{0,60}?\bno\b[^.]{0,40}?JavaScript rendering", re.I),
]


def _text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    # Tag-stripped, because the built page wraps sentences and a raw-HTML grep
    # missed exactly this class of thing once before.
    out = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    out = re.sub(r"(?s)<[^>]+>", " ", out)
    return re.sub(r"\s+", " ", html.unescape(out))


def main() -> int:
    pages = sorted(SITE.rglob("index.html"))
    if not pages:
        print("CAPABILITY stale — no built pages found; run scripts/build.py")
        return 1

    offenders = []
    for page in pages:
        text = _text(page)
        for pattern in DENIALS:
            match = pattern.search(text)
            if match:
                rel = page.relative_to(SITE).parent.as_posix() or "/"
                offenders.append(f"  /{rel}/: …{match.group(0).strip()}…")
                break

    if offenders:
        print(f"FAIL — {len(offenders)} page(s) say Docket does not run JavaScript.")
        print()
        print("Docket renders a sample of every audit automatically where the helper")
        print("is present; `--render 0` turns it off. Conceding a shipped capability")
        print("reads as modesty, so nobody questions it, and it talks a reader out of")
        print("a feature they were about to pay for.")
        print()
        print("\n".join(offenders))
        return 1

    print(f"CAPABILITY ok — {len(pages)} page(s), none denying Docket runs JavaScript")
    return 0


if __name__ == "__main__":
    sys.exit(main())
