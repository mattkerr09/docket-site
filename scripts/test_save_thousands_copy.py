#!/usr/bin/env python3
"""Offline market-price copy gate. All generated pages stay in scratch."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

sys.dont_write_bytecode = True

import render as R
import verify_competitive_claims as competitive
from test_launch_price_copy import scratch
from test_rename_brand import Page, build
import comparisons

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "audit-agency-prices-home": "index.html",
    "audit-agency-prices-pricing": "pricing/index.html",
    "audit-agency-prices-checker": "tools/ai-crawler-checker/index.html",
}
SOURCES = (
    "https://seoprofy.com/blog/seo-audit-pricing/",
    "https://www.webfx.com/seo/pricing/how-much-does-seo-audit-cost/",
    "https://ahrefs.com/blog/seo-pricing/",
)
HOME = ("Save thousands by doing it yourself. Agencies average $3,209 a month for SEO (Ahrefs) "
        "and one audit is quoted at $500 to $5,000 (SEOProfy).")
CHECKER = ("Save thousands by doing it yourself: an audit is quoted at $500 to $5,000 "
           "(SEOProfy, read 12 November 2026).")
PRICING = (
    "SEOProfy quotes an SEO audit at $500 to $5,000, read 12 November 2026.",
    "WebFX's survey says most businesses, 43%, pay $101 to $750 for an audit, read 12 November 2026.",
    "Ahrefs says agencies charge $3,209 a month on average for SEO, read 12 November 2026.",
    "Check Engine finds and ranks what is wrong and shows the fix. It does not do the fixing for you.",
)


def visible(raw):
    return " ".join("".join(Page(raw).words).split())


def check_pages(site, price):
    notes = {}
    for key, relative in PAGES.items():
        raw = (site / relative).read_text()
        note = re.search(r'<p class="verified-note">.*?</p>', raw, re.S)
        assert note, (relative, "dated source note missing")
        assert "Checked 12 November 2026." in visible(note[0]), relative
        assert "read 12 November 2026" in visible(note[0]), relative
        if relative == "index.html":
            expected = ("Ahrefs", "SEOProfy")
            section = re.search(r'<p class="hero-sub">(.*?)</p>', raw, re.S)[0]
            added = section[section.index("Save thousands"):]
            assert HOME in visible(added), visible(added)
            h1 = '<h1 class="hero-h1">Can ChatGPT, Claude and Perplexity <em>read your site?</em></h1>'
            assert h1 in raw
        elif relative == "pricing/index.html":
            expected = ("SEOProfy", "WebFX", "Ahrefs")
            section = raw.split("<h2>What an audit costs elsewhere</h2>", 1)[1].split("<h2>What you get</h2>", 1)[0]
            added = section
            for sentence in PRICING:
                assert sentence in visible(section), visible(section)
            assert "Save thousands" not in section
        else:
            expected = ("SEOProfy",)
            section = raw.split('<div class="checker-next" id="checker-next" hidden>', 1)[1].split("<h2>", 1)[0]
            added = re.search(r"<p>Save thousands.*?</p>", section, re.S)[0]
            assert CHECKER in visible(added), visible(added)
            assert "That was one file, read for one page." in visible(section)
            # Removing the additions must recover the shared result block, buttons included.
            if price == R.PRICE_COMPACT:
                import brand
                from articles.tools_free import audit_next
                original = R.nofollow_hub_links(brand.html(audit_next("tools-checker-result", what="one file, read for one page")))
                opening = '<div class="checker-next" id="checker-next" hidden>'
                restored = opening + section.replace(added, "", 1).replace(note[0], "", 1)
                assert " ".join(restored.split()) == " ".join(original.split())
        text = visible(added)
        assert f"Check Engine is {price}." in text, text
        assert "once once" not in text
        new_text = text + " " + visible(note[0])
        assert not re.search(r"[\u2013\u2014]", new_text), new_text
        assert not re.search(r"\b(?:guarantee|instant|accurate)\b|100%", new_text, re.I), new_text
        assert not competitive.COMPARATIVE.search(new_text), new_text
        for figure in ("$3,209", "$500 to $5,000", "$101 to $750"):
            assert figure in visible(section + note[0]), (relative, figure)
        for source in SOURCES:
            links = [attrs for tag, attrs in Page(note[0]).tags if tag == "a" and attrs.get("href") == source]
            assert links and all(set(link["rel"].split()) == {"nofollow", "noopener"} for link in links), (relative, source)
        # Inline citations must name their source, as well as the note's links.
        named = [visible(match[0]) for match in re.finditer(r"<a\b[^>]*>.*?</a>", section, re.S)
                 if any(f'href="{source}"' in match[0] for source in SOURCES)]
        assert all(name in named for name in expected), (relative, named)
        notes[relative] = (raw, note[0])
    print(f"PASS three built surfaces, sourced figures, read dates and helper price {price}")
    return notes


def check_registration(site, notes):
    recorded = competitive._verified_at((ROOT / competitive.CLAIMS_SOURCE).read_text())
    for key, relative in PAGES.items():
        assert comparisons.CHECKED_ISO[key] == "2026-11-12"
        assert comparisons.CHECKED_HUMAN[key] == "12 November 2026"
        assert tuple(source for _, source in comparisons.VERIFIED[key]) == SOURCES
        assert recorded[key] == comparisons.VERIFIED[key]
        assert competitive.VERIFIED_PAGES[key] == relative
    # Real git history, scratch HTML, as in the MCP claim test.
    with patch.object(competitive, "SITE", site):
        assert competitive.main() == 0, "scratch site failed competitive claims"
        for relative, (raw, note) in notes.items():
            mutations = [
                (raw.replace(note, "", 1), "requires a VERIFIED note dated"),
                (raw.replace(note, note.replace("12 November 2026", "11 November 2026"), 1),
                 "requires a VERIFIED note dated"),
            ]
            mutations.extend((raw.replace(note, note.replace(f'href="{source}"', 'href="/"'), 1),
                              "VERIFIED note is missing source") for source in SOURCES)
            page = site / relative
            try:
                for changed, expected in mutations:
                    page.write_text(changed)
                    output = io.StringIO()
                    with redirect_stdout(output), redirect_stderr(output):
                        code = competitive.main()
                    assert code == 1 and expected in output.getvalue(), output.getvalue()
            finally:
                page.write_text(raw)
    print("PASS competitive gate rejects missing notes, wrong dates and each missing source on all three pages")


def check_december(destination, env):
    source = """
import datetime
import json
from pathlib import Path
import sys
from unittest.mock import patch
sys.path[:0] = ['scripts', 'scripts/articles']
class DecemberClock(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 12, 1, 8, tzinfo=datetime.timezone.utc).astimezone(tz)
with patch('datetime.datetime', DecemberClock):
    import build as B
    import render as R
    import home
    import tool_ai_crawlers
    R.SITE = B.SITE = Path('december-site')
    home.build()
    B.pricing_page()
    tool_ai_crawlers.checker()
    assert not R.FOUNDING_OPEN
    print(json.dumps(R.PRICE_COMPACT))
"""
    result = subprocess.run([sys.executable, "-c", source], cwd=destination, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    price = json.loads(result.stdout)
    assert price == f"{R.PRICE_STR} once", price
    check_pages(destination / "december-site", price)
    print("PASS normal page builders after the 1 December price change")


def main():
    # Source read dates and scratch builds use UTC, including near local midnight.
    os.environ["TZ"] = "UTC"
    time.tzset()
    protected = {path: (ROOT / path).read_bytes() for path in (
        "data/build-id.txt", "scripts/render.py", "scripts/articles/hero_check.py",
        "scripts/articles/crawler_fix.py",
    )}
    with tempfile.TemporaryDirectory(prefix="test-save-thousands-") as temporary:
        destination = Path(temporary)
        scratch(destination)
        build(destination, "checkengine")
        site = destination / "site"
        notes = check_pages(site, R.PRICE_COMPACT)
        check_registration(site, notes)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SITE_BRAND="checkengine", TZ="UTC")
        check_december(destination, env)
        for script, args in (
            ("lint.py", ["site"]),
            ("verify_numbers.py", []),
            ("verify_datelines.py", []),
            ("verify_structured_data_matches_page.py", []),
            ("verify_price_claims.py", []),
            ("verify_version_strings.py", []),
        ):
            result = subprocess.run([sys.executable, "scripts/" + script, *args], cwd=destination,
                                    env=env, capture_output=True, text=True)
            print(f"COMMAND python3 scripts/{script}" + (" " + " ".join(args) if args else ""))
            print(result.stdout + result.stderr, end="")
            print(f"EXIT {result.returncode}", flush=True)
            assert result.returncode == 0, script
    for path, before in protected.items():
        assert (ROOT / path).read_bytes() == before, path
    print("OK")


if __name__ == "__main__":
    main()
