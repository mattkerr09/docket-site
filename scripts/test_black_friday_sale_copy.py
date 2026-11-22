#!/usr/bin/env python3
"""Offline sale regression: full scratch builds before and after the expiry."""
from __future__ import annotations

import ast
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import render as R
from test_measured_answers import Visible
from test_launch_price_copy import scratch, stale_promo
from test_sitewide_copy import sale_comparison
from test_thank_you_review_ask import sale_copy_allowance
from test_rename_brand import Page, build
from verify_founding_offer import visible
from verify_structured_data_matches_page import blocks

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = "Black Friday sale: $19.99 once through December 2. Then $39."
PRICE = re.compile(r"\$(?:39|29\.50|19\.99)(?!\d|\.\d)")
BANNED = re.compile(r"\bfounding\b|FOUNDINGDOCKET", re.I)


def words(raw):
    return " ".join(visible(raw).split())


def offers(value):
    if isinstance(value, dict):
        if value.get("@type") == "Offer":
            yield value
        for child in value.values():
            yield from offers(child)
    elif isinstance(value, list):
        for child in value:
            yield from offers(child)


def check_constants():
    assert R.founding_price_sentence() == EXPECTED
    assert R.price_sentence() == EXPECTED
    assert R.NOVEMBER_PRICE_STR == "$29.50"
    assert R.NOVEMBER_PRICE_CENTS == R.PRICE * 100 - R.NOVEMBER_OFF_CENTS
    assignments = {node.targets[0].id: node.value for node in ast.parse((ROOT / "scripts/render.py").read_text()).body
                   if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
    for name in ("FOUNDING_NOW", "FOUNDING_END_DAY_US"):
        assert not isinstance(assignments[name], ast.Constant), name
    assert R.PRICE_COMPACT == "$19.99 once through December 2, then $39"
    assert not R.founding_open(dt.datetime.fromisoformat(R.FOUNDING_ENDS_AT.replace("Z", "+00:00")))
    for text in (EXPECTED.replace("once through", "once, 32% off through"), EXPECTED + " Black Friday", "sale price", "launch price", "half price", "Black Friday sale soon"):
        assert stale_promo(text), text
    assert not stale_promo(EXPECTED)


def check_replay_allowances():
    old = "Black Friday sale: $19.99 once, 32% off our November price of $29.50, through December 2. Then $39."
    assert sale_copy_allowance(EXPECTED) == old
    current = "$34.99 once through December 2. Then $79.</a>"
    for previous in ("$34.99 once through December 2, then $79.</a>",
                     "$34.99 once through December 2.</a> From 3 December it is $79."):
        assert sale_copy_allowance(previous) == current
    total = '<p class="hero-note" id="bundle-sum">$46.97 bought apart, $34.99 together.</p>\n'
    assert sale_copy_allowance(total) == ""
    for changed in (EXPECTED.replace("$19.99", "$19.98"), EXPECTED.replace("$39", "$41"),
                    EXPECTED.replace("December 2", "December 3")):
        assert sale_copy_allowance(changed) != old
    assert sale_copy_allowance(total.replace("$46.97", "$46.96")) != ""


def check_site(site, opened, before_pages=None):
    for route in ("pricing", "download"):
        # Read inline links as browser text, with no added space before punctuation.
        raw = (site / route / "index.html").read_text()
        text = Visible(raw).text()
        expected = ("$34.99 once through December 2. Then $79." if opened else "$79 once")
        assert expected in text, (route, expected)
        assert "$59" not in text, route
        assert "bought apart" not in text, route
        assert "$46.97" not in text and "$107" not in text, route
    thanks = words((site / "thank-you/index.html").read_text())
    sister_prices = (("$9.99 through December 2, then $29", "$16.99 through December 2, then $39")
                     if opened else ("$29 once", "$39 once"))
    for expected in sister_prices:
        assert expected in thanks, expected
    privacy = words((site / "legal/privacy/index.html").read_text())
    sale_bar = ("The third is the sale bar across the top of every page except the page shown after a purchase, "
                "loaded from")
    if opened:
        assert sale_bar in privacy and "runs four third-party scripts" in privacy
    else:
        # The sale bar's script is not built after the sale, so the page stops describing it (3 December price-flip review).
        # The page's history paragraph still says the sale bar was once missed from the count: that is a dated correction,
        # not a description of what the page loads, so only the description (the paragraph and its place in the count) is checked.
        assert sale_bar not in privacy and "across the top of every page" not in privacy, "closed state still describes the sale bar"
        assert "runs three third-party scripts" in privacy and "The third is on every page" in privacy
        assert "The fourth is" not in privacy
    priced = []
    paid_count = 0
    sale_pages = 0
    mount_count = 0
    for path in sorted(site.rglob("*")):
        if path.suffix not in (".html", ".txt", ".json"):
            continue
        raw = path.read_text()
        text = words(raw)
        name = path.relative_to(site).as_posix()
        assert not sale_comparison(raw, name), (name, "sale comparison remains")
        if path.suffix == ".json":
            continue
        assert not BANNED.search(text), name
        promo_copy = " ".join(re.sub(r"(?m)^> ?", "", visible(raw)).split())
        assert not stale_promo(promo_copy), name
        if R.founding_price_sentence() in text:
            sale_pages += 1
        # Sister offers now share Check Engine's later price. They have their
        # own exact assertions above and do not offer Check Engine again.
        price_text = text
        if name == "thank-you/index.html":
            for expected in sister_prices:
                price_text = price_text.replace(expected, "")
        if PRICE.search(price_text):
            priced.append(name)
            assert (EXPECTED in text) if opened else ("$39" in text), name
        if not opened:
            # 20 Nov 2026 (batch 3): a rival plugin's own plan price may equal ours ("PRO $19.99 a month, purchased annually");
            # only that exact dated rival phrase is let through, so a leftover sale price of ours is still caught.
            assert not re.search(r"\$19\.99|Black Friday sale", text.replace("PRO $19.99 a month, purchased annually", ""), re.I), name
            if before_pages and name in before_pages:
                assert "$39" in text, (name, "priced page lost its list price")
        if path.suffix == ".html":
            for tag, attrs in Page(raw).tags:
                if "data-founding" in attrs:
                    mount_count += 1
                    assert opened, (name, "sale mount remains after expiry")
                    assert attrs.get("data-ref") != "$39", name
                    assert "data-ref" not in attrs, name
                    assert attrs.get("data-now") == "$19.99", name
                    assert attrs.get("data-was") == "$39", name
                    assert "hidden" in attrs, name
            for block in blocks(raw):
                for offer in offers(block):
                    # Free score/report offers remain free in both states.
                    if str(offer.get("price")) == "0":
                        continue
                    assert name != "thank-you/index.html", "sister price emitted a Check Engine Offer"
                    paid_count += 1
                    if not opened:
                        assert offer["price"] == "39.00", (name, offer)
                        assert "priceValidUntil" not in offer and "validFrom" not in offer, (name, offer)
                    elif offer["price"] == "19.99":
                        assert offer.get("priceValidUntil") == "2026-12-02", (name, offer)
                        assert "validFrom" not in offer, (name, offer)
                    else:
                        # DEC-3 price sweep row 53: the list price from the day after the sale, stated now.
                        assert offer["price"] == "39.00", (name, offer)
                        assert offer.get("validFrom") == "2026-12-03", (name, offer)
                        assert "priceValidUntil" not in offer, (name, offer)
    assert len(priced) > 400, len(priced)
    assert paid_count > 400, paid_count
    if opened:
        assert mount_count > 400, mount_count
        assert len(priced) == sale_pages, (len(priced), sale_pages)
    else:
        assert not sale_pages
        offer = json.loads((site / "offer.json").read_text())
        assert offer["founding"] is offer["after_launch"] is None
        assert offer["checkout_price_cents"] == 3900
    return priced, paid_count


def build_after(destination, brand="checkengine"):
    source = '''
import datetime
import runpy
import sys
from unittest.mock import patch
sys.path.insert(0, 'scripts')
class AfterSale(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 12, 3, 8, tzinfo=datetime.timezone.utc).astimezone(tz)
with patch('datetime.datetime', AfterSale):
    runpy.run_path('scripts/build.py', run_name='__main__')
'''
    env = dict(os.environ, DOCKET_SKIP_BRAND_ASSETS="1", PYTHONDONTWRITEBYTECODE="1",
               SITE_BRAND=brand, TZ="UTC")
    env.pop("DOCKET_DEPLOY", None)
    result = subprocess.run([sys.executable, "-c", source], cwd=destination, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def run_gate(destination, *argv):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SITE_BRAND="checkengine", TZ="UTC")
    result = subprocess.run([sys.executable, *argv], cwd=destination, env=env, capture_output=True, text=True)
    assert result.returncode == 0, (argv, (result.stdout + result.stderr)[-1800:])


FOUNDING_AFTER_THE_END = '''
import datetime as dt, sys
sys.path.insert(0, "scripts")
import render as R, verify_founding_offer as V
files = {p.relative_to(V.SITE).as_posix(): p.read_text(errors="ignore") for p in sorted(V.SITE.rglob("*"))
         if p.is_file() and p.suffix in (".html", ".txt", ".json") and (p.suffix != ".json" or p.name == "offer.json")}
fails, _notes = V.problems(files, None, dt.datetime(2026, 12, 3, 8, tzinfo=dt.timezone.utc), R.FOUNDING_ENDS_AT,
                           R.FOUNDING_NOW, R.FOUNDING_CODE, R.FOUNDING_END_DAY_US, R.FOUNDING_AFTER_DAY)
for f in fails:
    print("FAIL", f)
sys.exit(1 if fails else 0)
'''


def check_closed_build_gates(destination):
    """The gates deploy.sh runs, on the build made at 3 December 08:00 UTC (the 3 December runbook, step 1): the first
    run of any of them on the closed state must not be the real deploy. verify_founding_offer is read with its clock
    set to after the end, because it compares the build with the real clock."""
    for argv in (("scripts/verify_numbers.py",), ("scripts/lint.py", "site"),
                 ("scripts/verify_structured_data_matches_page.py",), ("scripts/verify_price_claims.py",),
                 ("scripts/verify_privacy_scripts.py",), ("-c", FOUNDING_AFTER_THE_END)):
        run_gate(destination, *argv)


def main():
    check_constants()
    check_replay_allowances()
    with tempfile.TemporaryDirectory(prefix="test-black-friday-") as temporary:
        destination = Path(temporary)
        scratch(destination)
        build(destination, "checkengine")
        priced, count = check_site(destination / "site", True)
        build_after(destination)
        after, after_count = check_site(destination / "site", False, set(priced))
        assert set(priced) == set(after), (set(priced) ^ set(after))
        check_closed_build_gates(destination)
        # While the sale is open a priced page states two Offers (the sale and the list price from 3 December, DEC-3 row 53);
        # after it, one.
        assert count == 2 * after_count, (count, after_count)
    print(f"PASS exact computed sale sentence; {len(priced)} priced HTML/TXT files carry it; {count} paid Offers (two a page: the sale, then the list price from 3 December) become {after_count} (one a page)")
    print("PASS sale mounts carry no reference price, $19.99 now and $39 later; every mount stays hidden")
    print("PASS full 3 December scratch build: priced pages show $39; no sale mount, sale price, sale name or visible FOUNDING")
    print("PASS comparison ban in HTML, metadata, alt text, JSON-LD, TXT and JSON before and after expiry")
    print("PASS visible code ban; only the exact helper-built sentence permits Black Friday copy")
    print("PASS the numbers, lint, structured-data, price-claims, privacy-scripts and founding-offer gates on the 3 December build")


if __name__ == "__main__":
    main()
