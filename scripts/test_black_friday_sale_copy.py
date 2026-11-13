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
from test_launch_price_copy import scratch, stale_promo
from test_rename_brand import build
from verify_founding_offer import visible
from verify_structured_data_matches_page import blocks

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = "Black Friday sale: $19.99 once, 32% off our November price of $29.50, through December 2. Then $39."
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
    assert R.SALE_PERCENT_OFF == round((R.NOVEMBER_PRICE_CENTS - (R.PRICE * 100 - R.FOUNDING_OFF_CENTS))
                                      / R.NOVEMBER_PRICE_CENTS * 100) == 32
    assignments = {node.targets[0].id: node.value for node in ast.parse((ROOT / "scripts/render.py").read_text()).body
                   if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}
    percent = assignments["SALE_PERCENT_OFF"]
    assert isinstance(percent, ast.Call) and percent.func.id == "round", ast.dump(percent)
    assert {node.id for node in ast.walk(percent) if isinstance(node, ast.Name)} >= {
        "FOUNDING_OFF_CENTS", "NOVEMBER_OFF_CENTS", "NOVEMBER_PRICE_CENTS"}
    for name in ("FOUNDING_NOW", "NOVEMBER_PRICE_STR", "FOUNDING_END_DAY_US"):
        assert not isinstance(assignments[name], ast.Constant), name
    assert R.PRICE_COMPACT == "$19.99 once through December 2, then $39"
    assert not R.founding_open(dt.datetime.fromisoformat(R.FOUNDING_ENDS_AT.replace("Z", "+00:00")))
    for text in (EXPECTED.replace("32%", "50%"), EXPECTED + " Black Friday", "sale price", "launch price", "half price", "Black Friday sale soon"):
        assert stale_promo(text), text
    assert not stale_promo(EXPECTED)


def check_site(site, opened, before_pages=None):
    priced = []
    paid_count = 0
    sale_pages = 0
    for path in sorted(site.rglob("*")):
        if path.suffix not in (".html", ".txt"):
            continue
        raw = path.read_text()
        text = words(raw)
        name = path.relative_to(site).as_posix()
        assert not BANNED.search(text), name
        promo_copy = " ".join(re.sub(r"(?m)^> ?", "", visible(raw)).split())
        assert not stale_promo(promo_copy), name
        if R.founding_price_sentence() in text:
            sale_pages += 1
        if PRICE.search(text):
            priced.append(name)
            assert (EXPECTED in text) if opened else ("$39" in text), name
        if not opened:
            assert not re.search(r"\$19\.99|Black Friday sale", text, re.I), name
            if before_pages and name in before_pages:
                assert "$39" in text, (name, "priced page lost its list price")
        if path.suffix == ".html":
            for block in blocks(raw):
                for offer in offers(block):
                    # Free score/report offers remain free in both states.
                    if str(offer.get("price")) == "0":
                        continue
                    paid_count += 1
                    assert offer["price"] == ("19.99" if opened else "39.00"), (name, offer)
                    if opened:
                        assert offer.get("priceValidUntil") == "2026-12-02", (name, offer)
                    else:
                        assert "priceValidUntil" not in offer, (name, offer)
                    assert "validFrom" not in offer, (name, offer)
    assert len(priced) > 400, len(priced)
    assert paid_count > 400, paid_count
    if opened:
        assert len(priced) == sale_pages, (len(priced), sale_pages)
    else:
        assert not sale_pages
        offer = json.loads((site / "offer.json").read_text())
        assert offer["founding"] is offer["after_launch"] is None
        assert offer["checkout_price_cents"] == 3900
    return priced, paid_count


def build_after(destination):
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
               SITE_BRAND="checkengine", TZ="UTC")
    env.pop("DOCKET_DEPLOY", None)
    result = subprocess.run([sys.executable, "-c", source], cwd=destination, env=env,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def main():
    check_constants()
    with tempfile.TemporaryDirectory(prefix="test-black-friday-") as temporary:
        destination = Path(temporary)
        scratch(destination)
        build(destination, "checkengine")
        priced, count = check_site(destination / "site", True)
        build_after(destination)
        after, after_count = check_site(destination / "site", False, set(priced))
        assert set(priced) == set(after), (set(priced) ^ set(after))
        assert count == after_count, (count, after_count)
    print(f"PASS exact computed sale sentence; {len(priced)} priced HTML/TXT files carry it; {count} paid Offers agree")
    print("PASS full 3 December scratch build: priced pages show $39; no sale price, sale name or visible FOUNDING")
    print("PASS visible code ban; only the exact helper-built sentence permits Black Friday copy")


if __name__ == "__main__":
    main()
