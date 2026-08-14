#!/usr/bin/env python3
"""The Buy button must still sell the product this site advertises.

    python3 scripts/verify_checkout.py

Every "Buy Docket · $79 once" button on this site points at one Polar checkout
link. Nothing checked that the link still exists, still belongs to the right
organisation, still sells the right product, or still charges $79 — the price is
printed in prose on fifty-one pages and not one of them asks Polar.

**Why it lives here and not in the app build.** The app's build-time guard
refuses to *stamp* a licensed build against the wrong organisation, and no build
is stamped yet, so wiring it into every app build would block releases for no
benefit and make them depend on Polar being up. This site is where the button
is. If the checkout moves, breaks or reprices, the page advertising it is what
becomes wrong, and this is the deploy that should stop.

**It reads a public page.** Polar renders the organisation, product id and price
into the checkout inline, so this needs no token — which is the whole reason it
can run at all. The equivalent API call needs a token this machine has never
had, and the guard that depended on it sat unexercised for a week and was
*wrong* the whole time: it expected `kerr-and-company-llc` and the organisation
taking the money is `docketseo`. A guard nobody can run is a guard nobody
notices is broken.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import app_path  # noqa: E402
import render  # noqa: E402

app = app_path.find()
sys.path.insert(0, str(app / "backend"))
sys.path.insert(0, str(app / "scripts"))

import resolve_polar_org as resolver  # noqa: E402


def main() -> int:
    if render.CHECKOUT != resolver.CHECKOUT:
        print("CHECKOUT FAIL — the site and the app disagree about the link")
        print(f"  site: {render.CHECKOUT}")
        print(f"  app:  {resolver.CHECKOUT}")
        print("  One of them is pointing customers somewhere the other does "
              "not verify.")
        return 1

    try:
        got = resolver.resolve_from_checkout(render.CHECKOUT)
    except resolver.Refused as exc:
        print(f"CHECKOUT FAIL — {exc}")
        return 1

    # The price the pages print, against the price the checkout charges. Both
    # are already compared inside `resolve_from_checkout`; this states the pair
    # in the output so a passing run says what it actually confirmed.
    print(f"CHECKOUT ok — {got['org']} sells {got['product']} at "
          f"${got['amount'] / 100:.0f}, and the site says {render.PRICE_STR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
