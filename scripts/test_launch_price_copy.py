#!/usr/bin/env python3
"""Offline launch-copy gate. Generated files and worker build output stay in scratch."""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

import render as R
from build import APP_LIST_PRICE_CENTS
from test_rename_brand import Page, build, json_values
from verify_structured_data_matches_page import visible, blocks as schema_blocks

ROOT = Path(__file__).resolve().parent.parent
BASE = "31f4693d7f73a39d7dc155f5d544ef62bb486132"
# Keep recorded image-compression ranges and decimal research figures.
STALE_PROMO = re.compile(r"(?<![\d.\u2013-])50%|50%\s*off|Black Friday|\bsale price\b", re.I)
PAY4 = re.compile(r"Klarna|Afterpay|four payments|pay in four|instalment|(?:4|four)\s*[×x]\s*\$", re.I)


def scratch(destination):
    for directory in ("scripts", "data", "site", "docs"):
        shutil.copytree(ROOT / directory, destination / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "*.env"))
    target = destination / "workers/ai-crawler-check/src"
    target.mkdir(parents=True)
    shutil.copy2(ROOT / "workers/ai-crawler-check/src/page.js", target / "page.js")


def baseline(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def current_copy(raw, path):
    # The job explicitly preserves the corrections page's historical records.
    # Remove only those exact rendered sections, after checking their contents.
    if path.as_posix().endswith("learn/what-docket-got-wrong/index.html"):
        from articles import corrections
        import brand
        for entry in corrections.load():
            section = brand.html(corrections._entry(entry))
            assert section in raw, (path, entry["release"])
            raw = raw.replace(section, "", 1)
    page = Page(raw)
    return " ".join(" ".join(page.words).split()), page.json_ld


def check_site(site):
    launch = R.founding_price_sentence()
    help_line = " ".join(html.unescape(re.sub(r"<[^>]+>", "", R.CHECKOUT_HELP)).split())
    assert help_line == (f"Buy applies the code {R.FOUNDING_CODE} for you; if the checkout shows {R.PRICE_STR}, "
                         "enter it under ‘Have a discount code?’."), help_line
    assert "$59" not in help_line
    price_pages = heroes = fallback_count = 0
    for path in sorted(site.rglob("*.html")):
        raw = path.read_text()
        text, blocks = current_copy(raw, path)
        for tag, attrs in Page(raw).tags:
            if "data-founding" in attrs:
                assert attrs["data-was"] == R.LATER_STR, path
                assert attrs["data-now"] == R.FOUNDING_NOW, path
                assert "data-pay4" not in attrs, path
        fallback_count += text.count(help_line)
        assert not re.search(r"(?<!SEOptimer Max )\$59(?![\d.])(?! a month)(?!/mo)", text), path
        assert not STALE_PROMO.search(text), path
        assert not PAY4.search(text), (path, PAY4.search(text))
        for block in blocks:
            for value in json_values(block):
                assert not re.search(r"(?<!SEOptimer Max )\$59(?![\d.])(?! a month)(?!/mo)", value), (path, value)
                assert not STALE_PROMO.search(value), (path, value)
                assert not PAY4.search(value), (path, value)
        if R.FOUNDING_NOW in text or R.LATER_STR in text:
            assert launch in text, (path, "price without full launch sentence")
            app = next((item for item in schema_blocks(raw)
                        if item.get("@type") == "SoftwareApplication"), None)
            assert app and app.get("offers"), (path, "price without SoftwareApplication offers")
            paid = [offer for offer in app["offers"] if offer["price"] != "0"]
            assert [(offer["price"], offer.get("priceValidUntil"), offer.get("validFrom"))
                    for offer in paid] == [(R.FOUNDING_NOW.lstrip("$"), "2026-11-30", None),
                                          (f"{R.LATER_PRICE:.2f}", None, "2026-12-01")], (path, paid)
            price_pages += 1
        for hero in re.findall(r'<p class="price-line"[^>]*>(.*?)</p>', raw, re.S):
            assert visible(hero) == launch.lower(), (path, hero)
            heroes += 1
    assert heroes > 100, heroes
    assert price_pages > 400, price_pages
    llms = " ".join((site / "llms.txt").read_text().split())
    assert launch in llms
    assert help_line in llms
    assert not re.search(r"(?<!SEOptimer Max )\$59(?![\d.])(?! a month)(?!/mo)", llms)
    assert not STALE_PROMO.search(llms)
    assert not PAY4.search(llms)
    fallback_count += llms.count(help_line)
    offer = json.loads((site / "offer.json").read_text())
    before = json.loads(baseline("site/offer.json"))
    expected = dict(before, instalments=None, checkout_price_cents=R.PRICE * 100)
    assert offer == expected, offer
    assert offer["price_cents"] == APP_LIST_PRICE_CENTS == 5900
    assert offer["checkout_price_cents"] == 3900
    assert offer["instalments"] is None
    assert offer["founding"]["price_cents"] == R.PRICE * 100 - R.FOUNDING_OFF_CENTS == 2950
    assert offer["founding"]["instalment_cents"] is None
    assert offer["later_price_cents"] == R.LATER_PRICE * 100
    assert offer["later_from"] == "2026-12-01"
    for key, value in offer.items():
        for text in json_values(value):
            assert not re.search(r"(?<!SEOptimer Max )\$59(?![\d.])(?! a month)(?!/mo)", text), (key, text)
            assert not STALE_PROMO.search(text), (key, text)
            assert not PAY4.search(text), (key, text)
    return price_pages, heroes, fallback_count


def check_comparisons(site):
    from articles import comparisons as C, pages, mac_options as M, white_label as W
    import facts as F
    assert pages._SF_MONTHS == -(-R.LATER_PRICE * 12 // F.rival_annual_low("screaming-frog"))
    assert C._SEM_WEEKS == round(R.LATER_PRICE / (int(C._SEM_LO) * 12 / 52))
    assert C._months_past_docket(C._SEOPT_LO) == R.LATER_PRICE // C._SEOPT_LO + 1
    assert M._more_than_docket(1000) == f"at least {M._usd(1000 - R.LATER_PRICE)} more"
    with patch.object(W, "render", side_effect=lambda **kwargs: kwargs):
        body = W.white_label_tools()["body"]
    assert W._usd(min(W._T["netpeak-spider"]["monthly"] * 12,
                          W._T["seoptimer"]["monthly"] * 12,
                          W._T["sitebulb"]["annual"], W._T["seo-powersuite"]["annual"]) - R.LATER_PRICE) in body
    download = visible((site / "download/index.html").read_text())
    assert f"less than {pages._SF_MONTHS} months of screaming frog" in download
    semrush = visible((site / "vs/semrush-site-audit-alternative/index.html").read_text())
    assert f"roughly {C._SEM_WEEKS} week" in semrush
    seoptimer = visible((site / "vs/seoptimer-alternative/index.html").read_text())
    assert f"from month {C._months_past_docket(C._SEOPT_LO)} it has cost more" in seoptimer
    home = visible((site / "index.html").read_text())
    assert f"at least {R.agency_multiple('webfx-audit')} check engine licences" in home
    mac = visible((site / "mac-seo-audit-tool/index.html").read_text())
    for _, _, _, _, saving in M._cost_rows():
        if saving.startswith("at least"):
            assert saving.lower() in mac, saving
    # Changing checkout PRICE must never move the comparison arithmetic.
    with patch.object(R, "PRICE", 79):
        assert R.agency_multiple("webfx-audit") == int(R.AGENCIES["webfx-audit"]["amount"]) // R.LATER_PRICE


def main():
    assert R.PRICE == 39
    assert R.LATER_PRICE == 39
    assert R.FOUNDING_OFF_CENTS == 950
    assert R.FOUNDING_NOW == "$29.50"
    assert R.FOUNDING_NOW == f"${R.PRICE - R.FOUNDING_OFF_CENTS / 100:.2f}"
    assert R.PRICE_TODAY == 29.5
    assert not R.BNPL_FOUNDING_OK
    for name in ("PAY4", "PAY4_BUY", "PAY4_FOUNDING", "BNPL_NOTE", "BNPL_NOTE_HTML"):
        assert getattr(R, name) == "", name
    assert "data-pay4" not in R.FOUNDING_MOUNT
    assert R.founding_price_sentence() == "Launch price: $29.50 once, through 30 November. From 1 December: $39."
    assert (ROOT / "data/corrections.json").read_bytes() == baseline("data/corrections.json")
    assert (ROOT / "scripts/articles/corrections.py").read_bytes() == baseline("scripts/articles/corrections.py")
    with tempfile.TemporaryDirectory(prefix="test-launch-price-") as temporary:
        destination = Path(temporary)
        scratch(destination)
        build(destination, "checkengine")
        counts = check_site(destination / "site")
        check_comparisons(destination / "site")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SITE_BRAND="checkengine", TZ="UTC")
        for script, args in (
            ("verify_price_claims.py", []),
            ("verify_founding_offer.py", ["--offline"]),
            ("verify_structured_data_matches_page.py", []),
            ("verify_numbers.py", []),
            ("test_sitewide_copy.py", []),
            ("test_live_site_fixes.py", []),
            ("lint.py", ["site"]),
        ):
            result = subprocess.run([sys.executable, "scripts/" + script, *args], cwd=destination,
                                    env=env, capture_output=True, text=True)
            assert result.returncode == 0, script + "\n" + result.stdout + result.stderr
            print(f"PASS python3 scripts/{script}" + (" " + " ".join(args) if args else ""))
    print(f"PASS {counts[0]} priced pages, {counts[1]} hero price blocks, {counts[2]} checkout-help copies of {R.PRICE_STR}")
    print("PASS offer.json price_cents=5900, checkout_price_cents=3900, instalments=null; all other fields match base")
    print("PASS historical corrections preserved; current price copy has no instalment claims")
    print("PASS PRICE=39, LATER_PRICE=39, FOUNDING_OFF_CENTS=950, FOUNDING_NOW=$29.50; comparisons use LATER_PRICE")
    print("SKIP brand image rendering: DOCKET_SKIP_BRAND_ASSETS=1 TZ=UTC")
    print("OK")


if __name__ == "__main__":
    main()
