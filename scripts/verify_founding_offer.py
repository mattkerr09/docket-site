#!/usr/bin/env python3
"""The founding price may only be shown while the founding offer is open.

    python3 scripts/verify_founding_offer.py              # the built site (deploy.sh runs it)
    python3 scripts/verify_founding_offer.py --self-test

WHY. CEO, 21 October 2026: FOUNDINGDOCKET (50% off, limit 25) expires at 2026-11-25T01:26:53Z, and every
founding-price line on the site, the auto-applied code and the ads must switch off by then. render.py builds the
founding lines only while founding_open(), and the page removes its own at the moment. This is the other half: a
deploy that would still show the founding price once the code has expired, or once Dodo's times_used has reached its
usage_limit, fails. A checkout charging $349 under a page that promises $174.50 is a price claim a buyer can prove
wrong.

WHAT FAILS, on the built site:
  - it shows the founding offer (the founding price, the code or the words "founding price" in a page's visible
    text or a .txt file, the bar's mount, or a founding block in offer.json) and
      - now is at or past the code's expires_at (Dodo's; render.FOUNDING_ENDS_AT when Dodo can't be read), or
      - Dodo says times_used has reached usage_limit (then set render.FOUNDING_SOLD_OUT = True and rebuild), or
      - Dodo has no such code;
  - render.FOUNDING_ENDS_AT is later than Dodo's expires_at, so the page's own switch would fire late.
Dodo unreadable (no key, no network): the date check still runs on FOUNDING_ENDS_AT, the seat check is reported as
not measured, and the deploy goes on; the bar and the checkout read Dodo live. The key comes from
~/.dodo/secrets.env or DODO_API_KEY and is never printed.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "scripts"))

MOUNT = re.compile(r"<div\s+data-founding(?=[\s>])")


def when(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def visible(page: str) -> str:
    page = re.sub(r"<(script|style|template|noscript)\b[^>]*>.*?</\1>", " ", page, flags=re.S | re.I)
    page = re.sub(r"<!--.*?-->", " ", page, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", page))


def shows_founding(name: str, text: str, price: str, code: str) -> str:
    """Why this built file shows the founding offer, or ''."""
    if name.endswith(".html"):
        if MOUNT.search(text):
            return "the founding bar's mount"
        seen = visible(text)
    elif name.endswith("offer.json"):
        return "a founding block in offer.json" if (json.loads(text) or {}).get("founding") else ""
    elif name.endswith(".txt"):
        seen = text
    else:
        return ""
    for needle in (code, price):
        if needle in seen:
            return f"{needle!r} in its text"
    # The bundle's "while founding prices last" and any other founding-price sentence without the figure.
    if re.search(r"founding price", seen, flags=re.I):
        return "'founding price' in its text"
    return ""


def problems(files: dict, dodo, now: dt.datetime, ends_at: str, price: str, code: str) -> tuple[list, list]:
    """(failures, notes). `dodo` is the code's Dodo record, "missing" for a 404, or None when it can't be read."""
    fails, notes = [], []
    shown = [(n, why) for n, t in sorted(files.items()) if (why := shows_founding(n, t, price, code))]
    expires = when(ends_at)
    if isinstance(dodo, dict):
        if dodo.get("expires_at"):
            theirs = when(dodo["expires_at"])
            if expires > theirs:
                fails.append(f"FOUNDING_ENDS_AT {ends_at} is later than Dodo's expires_at {dodo['expires_at']}: "
                             "the page's own switch would fire after the code stops working")
            expires = min(expires, theirs)
        used, limit = dodo.get("times_used") or 0, dodo.get("usage_limit")
        notes.append(f"Dodo: {code} {used} of {limit if limit is not None else 'unlimited'} used, "
                     f"expires {dodo.get('expires_at') or 'never'}")
        sold_out = limit is not None and used >= limit
    elif dodo == "missing":
        sold_out = None
        if shown:
            fails.append(f"Dodo has no discount {code}, so no checkout can honour it")
    else:
        sold_out = None
        notes.append(f"Dodo not read: the seat count is not measured, only the date ({ends_at})")
    if not shown:
        return fails, notes + ["the built site shows no founding offer"]
    over = []
    if now >= expires:
        over.append(f"the code expired at {expires.isoformat().replace('+00:00', 'Z')}")
    if sold_out:
        over.append("Dodo's times_used has reached usage_limit (set render.FOUNDING_SOLD_OUT = True and rebuild)")
    for reason in over:
        fails.append(f"{len(shown)} built file(s) still show the founding offer, and {reason}; first: "
                     + "; ".join(f"/{n} ({why})" for n, why in shown[:5]))
    if not over:
        notes.append(f"{len(shown)} built file(s) show the founding offer, which is open")
    return fails, notes


def dodo_key() -> str:
    env = Path.home() / ".dodo" / "secrets.env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("DODO_API_KEY="):
                return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("DODO_API_KEY", "")


def read_dodo(code: str):
    key = dodo_key()
    if not key:
        return None
    req = urllib.request.Request(f"https://live.dodopayments.com/discounts/code/{code}",
                                 headers={"Authorization": f"Bearer {key}", "User-Agent": "docket-site-founding-gate/1"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except urllib.error.HTTPError as exc:
        return "missing" if exc.code == 404 else None
    except (OSError, ValueError):
        return None


def self_test() -> int:
    price, code, ends = "$174.50", "FOUNDINGDOCKET", "2026-11-25T01:26:53Z"
    before, after = when("2026-11-24T12:00:00Z"), when("2026-11-25T01:26:53Z")
    page = ('<html><body><p class="founding-note" data-founding-until="x">Founding price <strong>$174.50 once</strong>'
            '</p><div data-founding data-now="$174.50" hidden></div></body></html>')
    plain = "<html><body><p>Docket is $349 once.</p><script>// was recorded at $349 while paying $174.50.</script></body></html>"
    open_rec = {"code": code, "usage_limit": 25, "times_used": 3, "expires_at": ends}
    full_rec = dict(open_rec, times_used=25)

    def fails(files, dodo, now, ends_at=ends):
        return problems(files, dodo, now, ends_at, price, code)[0]

    assert fails({"index.html": page}, open_rec, before) == [], "open offer, before the moment"
    assert any("expired" in f for f in fails({"index.html": page}, open_rec, after)), "shown at the moment"
    assert any("usage_limit" in f for f in fails({"index.html": page}, full_rec, before)), "shown when sold out"
    assert any("expired" in f for f in fails({"index.html": page}, None, after)), "date check without Dodo"
    assert fails({"index.html": page}, None, before) == [], "Dodo unreadable before the moment is not a failure"
    assert any("no discount" in f for f in fails({"index.html": page}, "missing", before)), "code deleted in Dodo"
    assert fails({"index.html": plain}, full_rec, after) == [], "a price inside a script comment is not shown"
    mount_only = '<html><body><div data-founding data-was="$349" hidden></div></body></html>'
    assert fails({"a/index.html": mount_only}, open_rec, after), "the bar's mount alone counts"
    until_only = '<html><body><p data-founding-until="2026">Docket is $349 once.</p></body></html>'
    assert fails({"a/index.html": until_only}, open_rec, after) == [], "data-founding-until is not the mount"
    assert fails({"llms.txt": "- Founding price $174.50 once"}, open_rec, after), "llms.txt counts"
    bundle = "<html><body><p>All three apps for $299 once while founding prices last.</p></body></html>"
    assert fails({"pricing/index.html": bundle}, open_rec, after), "the bundle's founding sentence counts"
    assert fails({"offer.json": json.dumps({"founding": {"code": code}})}, open_rec, after), "offer.json counts"
    assert fails({"offer.json": json.dumps({"founding": None})}, open_rec, after) == [], "a null founding is closed"
    late = dict(open_rec, expires_at="2026-11-24T00:00:00Z")
    assert any("later than Dodo" in f for f in fails({"index.html": plain}, late, before)), "a late switch fails"
    print("FOUNDING OFFER self-test ok")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    import render as R
    files = {p.relative_to(SITE).as_posix(): p.read_text(errors="ignore")
             for p in sorted(SITE.rglob("*")) if p.is_file() and p.suffix in (".html", ".txt", ".json")
             and (p.suffix != ".json" or p.name == "offer.json")}
    dodo = read_dodo(R.FOUNDING_CODE)
    fails, notes = problems(files, dodo, dt.datetime.now(dt.timezone.utc), R.FOUNDING_ENDS_AT,
                            R.FOUNDING_NOW, R.FOUNDING_CODE)
    for n in notes:
        print(f"  {n}")
    for f in fails:
        print(f"  FAIL  {f}")
    if fails:
        print("FOUNDING OFFER: the founding price must not be shown after the code ends or sells out; rebuild "
              "(render.founding_open() drops it) and deploy again.")
        return 1
    print("FOUNDING OFFER ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
