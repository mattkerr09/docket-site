#!/usr/bin/env python3
"""Offline November gate for the announced December price. Builds stay in scratch."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

from test_rename_brand import Page, build, json_values
import render

ROOT = Path(__file__).resolve().parent.parent
BASE = "fc90b391ddc9e68c251049509997da5aef943990"
BASE_SOURCES = (
    "scripts/render.py", "scripts/build.py", "scripts/articles/help_pages.py",
    "scripts/articles/corrections.py", "data/corrections.json",
)
LAUNCH = "Launch price: $29.50 once, through 30 November"
DECEMBER = re.compile(r"From 1 December\b[^.!?]*(?:\.|$)")
PAY4 = re.compile(r"four (?:payments|instalments)|(?:4|four)\s*[×x]|Klarna|Afterpay|instalments?", re.I)


def chunks(path):
    """Visible copy, metadata and each JSON-LD string, without joining offers."""
    raw = path.read_text(encoding="utf-8")
    if path.suffix == ".html":
        page = Page(raw)
        yield " ".join(" ".join(page.words).split())
        for block in page.json_ld:
            yield from json_values(block)
    elif path.suffix == ".json":
        yield from json_values(json.loads(raw))
    else:
        yield " ".join(raw.split())


def surfaces(site):
    return sorted(site.rglob("*.html")) + [site / "llms.txt", site / "offer.json"]


def launch_counts(site):
    return {p.relative_to(site): sum(text.count(LAUNCH) for text in chunks(p))
            for p in surfaces(site)}


def check_site(site):
    december = 0
    for path in surfaces(site):
        for text in chunks(path):
            # The bundle has its own price. The newsletter's December date has
            # no price. Neither is a claim about Check Engine's December price.
            for match in DECEMBER.finditer(text):
                sentence = match.group()
                if "$" not in sentence:
                    assert sentence.startswith("From 1 December it offers news"), (path, sentence)
                    continue
                if sentence == "From 1 December it is $99.":
                    assert path == site / "pricing/index.html", path
                    continue
                assert "$59" not in sentence, (path, sentence)
                assert "$39" in sentence, (path, sentence)
                assert not PAY4.search(sentence), (path, sentence)
                december += 1
            # A decimal point inside a price is not a sentence boundary.
            for sentence in re.split(r"(?<!\d)[.!?]\s+|(?<=\d)[.!?](?!\d)\s+", text):
                if re.search(r"\$39(?![\d.])", sentence):
                    assert not PAY4.search(sentence), (path, sentence)
            assert "{LATER_STR}" not in text, path
    assert december > 100, december
    offer = json.loads((site / "offer.json").read_text())
    assert offer["price_cents"] == 5900
    assert offer["founding"]["price_cents"] == 2950
    assert offer["founding"]["instalment_cents"] is None
    assert offer["after_launch"] == {
        "price_cents": 3900, "from": "1 December", "description": "From 1 December: $39."
    }
    # Today's list-price offer and its BNPL data are deliberately unchanged.
    assert offer["instalments"]["cents"] == 1475
    for path in site.rglob("*.html"):
        for block in Page(path.read_text()).json_ld:
            check_offers(block)
    return december


def check_offers(value):
    if isinstance(value, dict):
        if value.get("@type") == "Offer":
            assert str(value.get("price")) in {"0", "59"}, value
        for item in value.values():
            check_offers(item)
    elif isinstance(value, list):
        for item in value:
            check_offers(item)


def check_constants():
    assert render.PRICE == 59
    assert render.LATER_PRICE == 39
    assert render.LATER_STR == "$39"
    assert render.FOUNDING_NOW == "$29.50"
    assert render.founding_price_sentence() == LAUNCH + ". From 1 December: $39."
    note = (ROOT / "docs/DECEMBER_PRICE_FLIP.md").read_text()
    for name in ("PRICE", "LATER_PRICE", "LATER_STR", "FOUNDING_NOW", "FOUNDING_OPEN",
                 "FOUNDING_CODE", "FOUNDING_ENDS_AT", "BNPL_MIN_CENTS", "BNPL_NOTE", "PAY4"):
        assert name in note, name
    # Changing only the future constant must reach the helper and the data FAQ.
    from articles import help_pages
    with patch.object(render, "LATER_STR", "$41"):
        assert "From 1 December: $41." in render.founding_price_sentence()
        assert "From 1 December: $41." in help_pages.answer_values()["PRICE_WORDS"]


def scratch(destination):
    for directory in ("scripts", "data", "site", "docs"):
        shutil.copytree(ROOT / directory, destination / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "*.env"))
    # Only the text-width table is read. write_static also writes a brand
    # module here in scratch, leaving the real worker tree untouched.
    (destination / "workers/ai-crawler-check/src").mkdir(parents=True)
    shutil.copy2(ROOT / "workers/ai-crawler-check/src/page.js",
                 destination / "workers/ai-crawler-check/src/page.js")


def main():
    check_constants()
    with tempfile.TemporaryDirectory(prefix="test-december-price-") as temporary:
        destination = Path(temporary)
        scratch(destination)
        current = {name: (ROOT / name).read_bytes() for name in BASE_SOURCES}
        for name in BASE_SOURCES:
            result = subprocess.run(["git", "show", f"{BASE}:{name}"], cwd=ROOT,
                                    capture_output=True, check=True)
            (destination / name).write_bytes(result.stdout)
        build(destination, "checkengine")
        before = launch_counts(destination / "site")
        assert sum(before.values()) > 100, "baseline must exercise the launch copy"
        for name, source in current.items():
            (destination / name).write_bytes(source)
        build(destination, "checkengine")
        assert launch_counts(destination / "site") == before, "launch copy moved or changed"
        count = check_site(destination / "site")
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SITE_BRAND="checkengine", TZ="UTC")
        for command in (
            ["scripts/verify_price_claims.py"],
            ["scripts/verify_founding_offer.py", "--offline"],
            ["scripts/test_sitewide_copy.py"],
            ["scripts/test_live_site_fixes.py"],
        ):
            result = subprocess.run([sys.executable, *command], cwd=destination,
                                    env=env, capture_output=True, text=True)
            assert result.returncode == 0, " ".join(command) + "\n" + result.stdout + result.stderr
            print(f"PASS {' '.join(command)}")
        build(destination, "docket")
        check_site(destination / "site")
    print(f"PASS {count} December price statements; launch copy matches the base build")
    print("PASS PRICE=59, LATER_PRICE=39, FOUNDING_NOW=$29.50; both brands built in scratch")
    print("SKIP brand image rendering: DOCKET_SKIP_BRAND_ASSETS=1 TZ=UTC")
    print("OK")


if __name__ == "__main__":
    main()
