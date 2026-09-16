#!/usr/bin/env python3
"""Write `data/licence.json` from Dodo's product record, so no seat count is typed.

Docket's terms said "up to three machines" in one paragraph and "any machine you
own or control" two paragraphs later. The second was unbounded, older, and left
standing when the limit was introduced. Both are now interpolated, but a single
interpolated number is only worth as much as its source — and until this script
existed the number was COPIED from a message into a file, which passes a drift
gate while being exactly as stale as the string it replaced.

The source is `~/ops/launch/dodo-facts.json`, written by `ops/bin/dodo-facts.py`
from Dodo's own product records and re-run on each CEO self-check. It carries no
secret, which is why this repo may read it: the Products API answers 403 to the
key on this machine, so the read happens where the credential works and the
result travels as a file. That is the same shape as every other collector here —
`collect_updater.py` reads the published release, `collect_regressions.py` reads
the suite — and it keeps the build hermetic: `build.py` never reaches outside the
repo, it reads `data/`.

⚠️ IT FAILS RATHER THAN KEEPING THE OLD VALUE. A collector that shrugs at a
missing source and leaves yesterday's number in place is the drift this whole
exercise is about. Missing file, missing product, disagreeing limits, or a
non-integer all raise.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRODUCT_ID = "pdt_0Nlgdu6xbdzeG5tDAWx79"
SOURCE = pathlib.Path(
    os.environ.get("DODO_FACTS", pathlib.Path.home() / "ops" / "launch" / "dodo-facts.json"))


def main() -> int:
    if not SOURCE.is_file():
        print(f"collect_licence: no source at {SOURCE} — run ops/bin/dodo-facts.py first",
              file=sys.stderr)
        return 1
    facts = json.loads(SOURCE.read_text())
    product = (facts.get("products") or {}).get(PRODUCT_ID)
    if not product:
        print(f"collect_licence: {PRODUCT_ID} is not in {SOURCE}", file=sys.stderr)
        return 1

    # ⚠️ THE TWO LIMITS ARE READ SEPARATELY AND COMPARED. The defect that started
    # this was a product field and a customer-facing message disagreeing — 3
    # against "up to 5 machines" — for three weeks. If Dodo's own two numbers
    # ever diverge again, this stops rather than picking one.
    at_product = product.get("activations_limit_product")
    at_entitlement = product.get("activations_limit_entitlement")
    if at_product != at_entitlement:
        print(f"collect_licence: Dodo disagrees with itself — product says "
              f"{at_product!r}, entitlement says {at_entitlement!r}", file=sys.stderr)
        return 1
    seats = product.get("seats", at_product)
    if not isinstance(seats, int) or seats < 1:
        print(f"collect_licence: seat count is {seats!r}, which is not a count",
              file=sys.stderr)
        return 1

    out = {
        "activations_limit": seats,
        "product_id": PRODUCT_ID,
        "product_name": product.get("name", ""),
        "read_at": facts.get("read_at", ""),
        "source": facts.get("source", ""),
        "collected_by": "scripts/collect_licence.py from ops/launch/dodo-facts.json",
        "note": "Generated. Do not edit by hand — re-run the collector. The seat count "
                "appears in prose only through facts.licence_activations().",
    }
    path = ROOT / "data" / "licence.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"LICENCE ok — {seats} activation(s) for {out['product_name']}, "
          f"read {out['read_at']}; written {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
