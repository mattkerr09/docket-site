#!/usr/bin/env python3
"""Offline test of the sample metadata writer."""
import json
from pathlib import Path
import tempfile

import brand
from make_sample_report import write_sample_run


def main():
    run = {"engine": "1.3.1", "counts": {"warning": 2}, "branded_image": None}
    with tempfile.TemporaryDirectory(prefix="test-sample-run-") as temporary:
        path = Path(temporary) / "sample-run.json"
        write_sample_run(run, path)
        raw = path.read_text(encoding="utf-8")
        written = json.loads(raw)
    assert written["site_brand"] == brand.SITE_BRAND, written
    assert {key: written[key] for key in run} == run, written
    assert list(written) == [*run, "site_brand"], written
    assert raw == json.dumps({**run, "site_brand": brand.SITE_BRAND}, indent=1) + "\n"
    print("PASS sample run keeps all supplied keys and writes the current site brand last")
    print("PASS JSON indentation and final newline are unchanged")
    print("SKIP direct verifier brand assertion: the brand rule is inline in main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
