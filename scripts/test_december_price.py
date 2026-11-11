#!/usr/bin/env python3
"""Offline November gate for the announced December price. Builds stay in scratch."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import render

ROOT = Path(__file__).resolve().parent.parent


def check_constants():
    assert render.PRICE == 59
    assert render.LATER_PRICE == 39
    assert render.LATER_STR == "$39"
    assert render.FOUNDING_NOW == "$29.50"
    assert render.founding_price_sentence() == "Launch price: $29.50 once, through 30 November. From 1 December: $39."
    note = (ROOT / "docs/DECEMBER_PRICE_FLIP.md").read_text()
    for name in ("PRICE", "LATER_PRICE", "LATER_STR", "FOUNDING_NOW", "FOUNDING_OPEN",
                 "FOUNDING_CODE", "FOUNDING_ENDS_AT", "BNPL_MIN_CENTS", "BNPL_NOTE", "PAY4"):
        assert name in note, name
    # Changing only the future constant must reach the helper and the data FAQ.
    from articles import help_pages
    with patch.object(render, "LATER_STR", "$41"):
        assert "From 1 December: $41." in render.founding_price_sentence()
        assert "From 1 December: $41." in help_pages.answer_values()["PRICE_WORDS"]


def main():
    check_constants()
    # The November launch-copy gate now owns the scratch build and dated Offers.
    from test_launch_price_copy import main as launch_main
    launch_main()


if __name__ == "__main__":
    main()
