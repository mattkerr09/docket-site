#!/usr/bin/env python3
"""The agency batch-edition page test (CEO, 24 Nov 2026): /for/agencies/ says plainly what exists today, then offers a
clearly labelled "tell me when it's ready" list. No price, nothing promised as available, one source of its own,
disclosed on the privacy page. Offline: reads the helper and the page source, and the built page when site/ exists."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "articles"))

import render as R  # noqa: E402

SECTION_START = "What exists today, and what does not yet"
SECTION_END = "interest-agency"


def main() -> int:
    # 1. The form helper: own source, plain address form, visible to everyone, a honeypot, no price.
    form = R.interest_form(R.AGENCY_WAIT_SOURCE, "agency", "Ask.", "Tell me", "Done.")
    assert R.AGENCY_WAIT_SOURCE == "checkengine-agency"
    assert 'value="checkengine-agency"' in form and 'data-source="checkengine-agency"' in form
    assert 'action="https://kerr-subscribe.kerrco.workers.dev"' in form
    assert re.search(r'<form[^>]*\bhidden\b', form) is None, "the interest form must be shown to every visitor"
    assert 'type="email"' in form and 'name="website"' in form and 'tabindex="-1"' in form
    assert "$" not in form and "%" not in form
    assert "fetch(" in form and "data-interest" in form
    # nothing fires on page load: the only request is inside the submit handler
    assert form.index("addEventListener('submit'") < form.index("fetch(")

    # 2. The page copy in the source: plain, labelled, no price, nothing promised.
    src = (ROOT / "scripts" / "articles" / "pages.py").read_text(encoding="utf-8")
    assert SECTION_START in src
    assert "Agency batch edition: tell me when it&rsquo;s ready" in src
    block = src[src.index(SECTION_START):src.index("__AGENCY_FORM__")]
    block = " ".join(block.split())  # the source wraps its lines
    assert "one site at a time" in block and "name and logo go on the client PDF" in block
    assert "It is not built, it has no price, and nothing on this page promises it will be" in block
    assert "never send email" in block
    assert "$" not in block, "the batch edition has no price"
    for banned in ("unlock", "seamless", "supercharge", "effortless", "game-changer", "coming soon", "available now"):
        assert banned not in block.lower(), banned
    assert "_agency_form_privacy()" in src and "kerr-subscribe.kerrco.workers.dev" in src[src.index("def _agency_form_privacy"):]

    # 3. The built page, when there is a build in this checkout.
    page = ROOT / "site" / "for" / "agencies" / "index.html"
    # a build older than the source is not read: it would fail for the wrong reason
    fresh = page.exists() and page.stat().st_mtime >= (ROOT / "scripts" / "articles" / "pages.py").stat().st_mtime
    if fresh:
        raw = page.read_text(encoding="utf-8")
        assert raw.count('data-source="checkengine-agency"') == 1, "exactly one agency form"
        assert "__AGENCY_FORM__" not in raw
        assert SECTION_START in raw
        privacy = (ROOT / "site" / "legal" / "privacy" / "index.html").read_text(encoding="utf-8")
        assert "hear if a batch edition is ever built" in privacy
        print("AGENCY INTEREST FORM ok: helper, page copy, privacy paragraph, built page")
    else:
        print("AGENCY INTEREST FORM ok: helper, page copy, privacy paragraph (no build here, built page not read)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
