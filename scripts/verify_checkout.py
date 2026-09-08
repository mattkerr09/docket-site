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



def _charges(html: str, cents: str) -> bool:
    """Does the checkout show exactly this amount, as a whole number?

    `cents in html` is a SUBSTRING test, and amounts nest: "9900" sits inside
    "19900". Break-tested 2026-09-08 with the site at $99 against the live $199
    checkout, this gate printed "CHECKOUT ok ... the site says $99" while a buyer
    would have been charged a hundred dollars more. The gate that exists to stop
    exactly that was passing it, and had been since it was written.
    """
    import re as _re
    return _re.search(r"(?<!\d)" + _re.escape(cents) + r"(?!\d)", html) is not None


def _dodo(url: str) -> int:
    """The same question asked of Dodo: does this link still sell the product
    this site advertises, at the price the pages print?

    Dodo renders the product name and the amount in cents into the checkout
    page, so like the Polar path this needs no token. Measured 2026-08-23: the
    page carries "Docket SEO — Lifetime Licence", a License Key benefit, and
    19900.

    Weaker than the Polar path in one stated way — it cannot read back an
    organisation id, so it proves the product and the price and not who is
    paid. Saying so is better than implying a guarantee it does not make.
    """
    import re
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        url, headers={"User-Agent": "docket-build/1.0 (+https://docketseo.app)"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            html = r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as e:
        print(f"CHECKOUT FAIL — could not reach the Dodo checkout ({type(e).__name__}). "
              f"Nothing was compared, which is not a pass.")
        return 1

    cents = str(render.PRICE * 100)
    problems = []
    transition = ""
    if "Docket" not in html:
        problems.append("the checkout does not name Docket at all")
    if not _charges(html, cents):
        # A PRICE RISE LANDS ON THE SITE FIRST, ON PURPOSE.
        #
        # This asserted the site and the checkout were equal, which reads as the
        # safe rule and is not it. The rule a buyer cares about is that the
        # checkout never charges MORE than the page advertises. Equality also
        # made the agreed order unshippable: the site cannot go to $349 while
        # Dodo still says $199, so the deploy would fail until Dodo moved — and
        # moving Dodo first is the one order that overcharges somebody.
        #
        # So an OLD, LOWER price is accepted and announced; anything else fails.
        previous = getattr(render, "PRICE_PREVIOUS", None)
        old_cents = str(previous * 100) if previous else ""
        if previous and previous < render.PRICE and _charges(html, old_cents):
            transition = (
                f"    TRANSITION: the checkout still charges ${previous} while the "
                f"site advertises {render.PRICE_STR}. That is the agreed order — a "
                f"buyer in this window pays LESS than the page showed, never more. "
                f"Clear render.PRICE_PREVIOUS once Dodo reads {cents}.")
        else:
            problems.append(f"the checkout does not charge {render.PRICE_STR} "
                            f"({cents} in cents is absent from the page), and it is "
                            f"not the recorded previous price either. A checkout that "
                            f"charges anything other than the price on the page, or "
                            f"more than it, is the failure this gate exists for.")
    if "License Key" not in html and "license_key" not in html.lower():
        problems.append("no licence-key benefit — a buyer would pay and receive "
                        "no key, and a licensed build would refuse them")
    if problems:
        print("CHECKOUT FAIL — the Dodo checkout does not match what the site sells:")
        for pr in problems:
            print(f"    {pr}")
        return 1
    if transition:
        print(f"CHECKOUT ok (price transition) — the site says {render.PRICE_STR}.")
        print(transition)
        return 0
    print(f"CHECKOUT ok — the Dodo checkout sells Docket at {render.PRICE_STR} "
          f"with a licence key, and the site says {render.PRICE_STR}. "
          f"(Dodo does not expose the organisation, so this proves the product "
          f"and price, not who is paid.)")
    return 0


def main() -> int:
    # The site moved to Dodo on 2026-08-23. The Polar path below still works and
    # is kept for the same reason licence.py keeps its Polar branch: the switch
    # is reversible and a resolver nobody can run is a resolver nobody notices
    # is broken.
    if "dodopayments.com" in render.CHECKOUT:
        return _dodo(render.CHECKOUT)

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
