#!/usr/bin/env python3
"""The vendor-match gate must still know which vendor a build asks, now that the
customer-facing refusal names none (2026-11-20), and must never pass on nothing.

Each case builds a stand-in sidecar in a temporary dist/ and asks the gate what
it sees. Offline: the only network is a listener on 127.0.0.1.
"""
from __future__ import annotations

import pathlib
import stat
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_vendor_match as gate

PLAIN_REFUSAL = "that licence key was not recognised. copy the whole key again from your receipt email"


def sidecar(directory: pathlib.Path, body: str) -> None:
    path = directory / "docket"
    path.write_text(f"#!{sys.executable}\n{body}\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


class VendorProbe(unittest.TestCase):
    def ask(self, body: str) -> tuple:
        with tempfile.TemporaryDirectory(prefix="vendor-probe-dist.") as tmp:
            dist = pathlib.Path(tmp)
            sidecar(dist, body)
            old = gate.DIST
            gate.DIST = dist
            try:
                return gate.app_vendor()
            finally:
                gate.DIST = old

    def test_a_refusal_that_names_dodo_still_counts(self):
        vendor, _ = self.ask('print("That licence key was not accepted by Dodo.")')
        self.assertEqual(vendor, "dodo")

    def test_a_vendor_free_refusal_is_read_from_where_the_request_goes(self):
        vendor, why = self.ask(
            "import os, urllib.request, urllib.error\n"
            "req = urllib.request.Request(os.environ['DOCKET_DODO_API_BASE'] + '/licenses/activate',"
            " data=b'{}', method='POST')\n"
            "try:\n    urllib.request.urlopen(req, timeout=10)\nexcept urllib.error.URLError:\n    pass\n"
            f"print({PLAIN_REFUSAL!r})"
        )
        self.assertEqual(vendor, "dodo", why)

    def test_a_vendor_free_refusal_that_asks_nobody_is_not_a_pass(self):
        vendor, why = self.ask(f"print({PLAIN_REFUSAL!r})")
        self.assertEqual(vendor, "", "nothing was compared, so it must not name a vendor")
        self.assertIn("sent no request", why)

    def test_the_probe_never_touches_the_real_home(self):
        # The stand-in writes where HOME points; the real HOME must stay clean.
        marker = pathlib.Path.home() / ".vendor-match-probe-marker"
        marker.unlink(missing_ok=True)
        self.ask("import pathlib\n(pathlib.Path.home() / '.vendor-match-probe-marker').write_text('x')\n"
                 f"print({PLAIN_REFUSAL!r})")
        self.assertFalse(marker.exists(), "the probe wrote into the real HOME")


if __name__ == "__main__":
    unittest.main()
