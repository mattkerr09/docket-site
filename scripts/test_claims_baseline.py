#!/usr/bin/env python3
"""Fact sets built at import time are dated by their recorded wording fingerprint, and a changed wording is an edit today.

Before this, sf-alternatives, wl-tools and wordpress-compared (built from best_compared_sources.py) had no revision the gate
could read, so it called them "edited today" on every day after their read date and refused every deploy.
"""
from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brand, render, build  # noqa: E401,F401
sys.path.insert(1, str(HERE / "articles"))
import comparisons as C  # noqa: E402
import verify_competitive_claims as V  # noqa: E402

KEYS = ("sf-alternatives", "wl-tools", "wordpress-compared")


class Baseline(unittest.TestCase):
    def test_unchanged_wording_keeps_its_recorded_day(self):
        edits, _, _ = V._facts_last_edited(C.VERIFIED, C.DATA_CLAIM_SETS)
        for key in KEYS:
            self.assertEqual(edits[key], "2026-11-20", key)

    def test_changed_wording_is_an_edit_today(self):
        changed = {k: list(v) for k, v in C.VERIFIED.items()}
        changed["wl-tools"][0] = (changed["wl-tools"][0][0] + " and one more claim", changed["wl-tools"][0][1])
        edits, _, _ = V._facts_last_edited(changed, C.DATA_CLAIM_SETS)
        self.assertEqual(edits["wl-tools"], date.today().isoformat())
        self.assertEqual(edits["sf-alternatives"], "2026-11-20")

    def test_a_set_missing_from_the_baseline_is_still_an_edit_today(self):
        with mock.patch.object(V, "WORDING_BASELINE", Path("/nonexistent/claims-wording-baseline.json")):
            edits, _, _ = V._facts_last_edited(C.VERIFIED, C.DATA_CLAIM_SETS)
        self.assertEqual(edits["wordpress-compared"], date.today().isoformat())


if __name__ == "__main__":
    unittest.main()
