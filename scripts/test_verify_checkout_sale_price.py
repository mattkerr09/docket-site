#!/usr/bin/env python3
"""The checkout gate accepts the sale price with no code, only while the sale runs, and never a dearer price.

From the 22 Nov 2026 switch the Dodo product itself is priced at the sale price (PRICE less FOUNDING_OFF_CENTS), so
the plain checkout link charges $19.99 until FOUNDING_ENDS_AT and $39 after it. Offline: the checkout page and the
clock flag are stood in for.
"""
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import render
import verify_checkout


class _Page:
    def __init__(self, cents: str):
        self.body = f"<html>Docket SEO Lifetime Licence License Key {cents} USD</html>".encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self.body


def run_gate(cents: str, open_: bool) -> tuple[int, str]:
    out = io.StringIO()
    with mock.patch("urllib.request.urlopen", lambda *a, **k: _Page(cents)), \
            mock.patch.object(render, "FOUNDING_OPEN", open_), contextlib.redirect_stdout(out):
        code = verify_checkout._dodo("https://checkout.dodopayments.com/buy/pdt_test")
    return code, out.getvalue()


class SalePrice(unittest.TestCase):
    LIST = str(render.PRICE * 100)
    SALE = str(render.PRICE * 100 - render.FOUNDING_OFF_CENTS)

    def test_the_list_price_always_passes(self):
        for open_ in (True, False):
            self.assertEqual(run_gate(self.LIST, open_)[0], 0)

    def test_the_sale_price_passes_while_the_sale_runs(self):
        code, text = run_gate(self.SALE, True)
        self.assertEqual(code, 0, text)
        self.assertIn("SALE PRICE, NO CODE", text)

    def test_the_sale_price_fails_after_the_sale_ends(self):
        code, text = run_gate(self.SALE, False)
        self.assertEqual(code, 1, text)

    def test_a_dearer_price_fails_in_both_states(self):
        for cents in (str(render.PRICE * 100 + 1000), "5900"):
            for open_ in (True, False):
                self.assertEqual(run_gate(cents, open_)[0], 1, (cents, open_))

    def test_a_longer_number_containing_the_sale_price_is_not_the_sale_price(self):
        self.assertEqual(run_gate("1" + self.SALE, True)[0], 1)
        self.assertEqual(run_gate(self.SALE + "0", True)[0], 1)

    def test_the_sale_price_is_the_documented_one(self):
        self.assertEqual(self.SALE, "1999")


if __name__ == "__main__":
    unittest.main()
