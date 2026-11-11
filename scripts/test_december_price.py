#!/usr/bin/env python3
"""Offline November gate for the announced December price. Builds stay in scratch."""
from __future__ import annotations

import datetime
import json
from pathlib import Path
import runpy
import tempfile
from unittest.mock import patch

import render

ROOT = Path(__file__).resolve().parent.parent


def check_constants():
    assert render.PRICE == 39
    assert render.LATER_PRICE == 39
    assert render.LATER_STR == "$39"
    assert render.FOUNDING_NOW == "$29.50"
    assert render.FOUNDING_OFF_CENTS == 950
    assert render.FOUNDING_NOW == f"${render.PRICE - render.FOUNDING_OFF_CENTS / 100:.2f}"
    assert render.founding_price_sentence() == "Launch price: $29.50 once, through 30 November. From 1 December: $39."
    note = (ROOT / "docs/DECEMBER_PRICE_FLIP.md").read_text()
    for name in ("PRICE", "LATER_PRICE", "LATER_STR", "FOUNDING_NOW", "FOUNDING_OPEN",
                 "FOUNDING_CODE", "FOUNDING_OFF_CENTS", "FOUNDING_ENDS_AT", "APP_LIST_PRICE_CENTS",
                 "BNPL_MIN_CENTS", "BNPL_NOTE", "PAY4"):
        assert name in note, name
    # Changing only the future constant must reach the helper and the data FAQ.
    from articles import help_pages
    with patch.object(render, "LATER_STR", "$41"):
        assert "From 1 December: $41." in render.founding_price_sentence()
        assert "From 1 December: $41." in help_pages.answer_values()["PRICE_WORDS"]


def check_expiry():
    class DecemberClock(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 12, 1, 8, tzinfo=datetime.timezone.utc).astimezone(tz)

    with patch("datetime.datetime", DecemberClock):
        closed = runpy.run_path(str(ROOT / "scripts/render.py"))
    assert not closed["FOUNDING_OPEN"]
    assert closed["PRICE_TODAY"] == 39
    assert closed["founding_price_sentence"]() == ""
    assert closed["price_sentence"]() == "$39 once."
    for name in ("CHECKOUT_HELP", "FOUNDING_LINE", "FOUNDING_MOUNT", "PAY4", "PAY4_BUY",
                 "PAY4_FOUNDING", "BNPL_NOTE", "BNPL_NOTE_HTML"):
        assert closed[name] == "", name
    paid = [offer for offer in closed["_price_offers"](False) if offer["price"] != "0"]
    assert len(paid) == 1, paid
    assert paid[0]["price"] == "39.00", paid
    assert "priceValidUntil" not in paid[0], paid

    import build
    with tempfile.TemporaryDirectory(prefix="test-december-offer-") as temporary:
        destination = Path(temporary)
        with patch.object(build, "SITE", destination), patch.object(render, "FOUNDING_OPEN", False):
            build.write_offer()
        offer = json.loads((destination / "offer.json").read_text())
    assert offer["price_cents"] == build.APP_LIST_PRICE_CENTS == 5900
    assert offer["checkout_price_cents"] == 3900
    assert offer["founding"] is None
    assert offer["after_launch"] is None
    assert offer["instalments"] is None
    print("PASS December clock removes launch copy and Offer; offer.json founding=null and instalments=null")


def main():
    check_constants()
    check_expiry()
    # The November launch-copy gate now owns the scratch build and dated Offers.
    from test_launch_price_copy import main as launch_main
    launch_main()


if __name__ == "__main__":
    main()
