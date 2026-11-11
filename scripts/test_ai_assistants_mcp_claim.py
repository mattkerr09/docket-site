#!/usr/bin/env python3
"""Offline MCP claim gate. Build output stays in a temporary repo copy."""
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
from unittest.mock import patch

sys.dont_write_bytecode = True

import render as R
import verify_competitive_claims as competitive
from test_launch_price_copy import scratch
from test_rename_brand import Page, build, words
import comparisons

ROOT = Path(__file__).resolve().parent.parent
KEY = "ai-assistants-mcp"
SOURCES = ("https://www.screamingfrog.co.uk/seo-spider/pricing/", "https://sitebulb.com/pricing/")
MCP_SENTENCE = "Check Engine's MCP server runs the free audit with no licence key."
RIVAL_SENTENCE = ("Screaming Frog lists its MCP Server as a paid feature, and Sitebulb lists MCP access "
                  "on its paid plans and offers a trial.")


def check_page(site):
    raw = (site / "ai-assistants/index.html").read_text()
    section = re.search(r"<h2>Audits through MCP</h2>(.*?)<h2>", raw, re.S)
    assert section, "MCP section missing"
    text = words(section.group(1))
    assert MCP_SENTENCE in text, text
    assert RIVAL_SENTENCE in text, text
    assert R.FREE_LINE in text, "shared free and Pro result description missing"
    assert not competitive.COMPARATIVE.search(text), text
    note = re.search(r'<p class="verified-note">.*?</p>', section.group(1), re.S)
    assert note, "dated source note missing"
    assert "Checked 11 November 2026." in words(note.group(0))
    assert "Screaming Frog's pricing page" in words(note.group(0))
    assert "Sitebulb's pricing page" in words(note.group(0))
    assert "14 day trial" in words(note.group(0))
    links = [attrs["href"] for tag, attrs in Page(note.group(0)).tags if tag == "a"]
    assert all(source in links for source in SOURCES), links
    assert comparisons.CHECKED_ISO[KEY] == "2026-11-11"
    assert comparisons.CHECKED_HUMAN[KEY] == "11 November 2026"
    assert [source for _, source in comparisons.VERIFIED[KEY]] == list(SOURCES)
    # The history gate reads this literal with ast.literal_eval.
    recorded = competitive._verified_at((ROOT / competitive.CLAIMS_SOURCE).read_text())
    assert recorded[KEY] == comparisons.VERIFIED[KEY]
    page_schema = next(block for block in Page(raw).json_ld if block.get("@type") == "WebPage")
    assert page_schema["dateModified"] == "2026-11-11", page_schema
    run = json.loads((ROOT / "data/ai-assistants-run.json").read_text())
    assert f"released {run['release']} Mac extension" in words(raw)
    assert run["top_title"] in words(raw)
    print("PASS MCP claim, shared free and Pro wording, both named pricing sources and dates")
    print(MCP_SENTENCE)
    print(RIVAL_SENTENCE)
    return raw, note.group(0)


def check_competitive_gate(site, raw, note):
    # Keep ROOT on the real checkout so the gate can read actual git history.
    # SITE points at the scratch build, the HTML a reader would receive.
    page = site / "ai-assistants/index.html"
    with patch.object(competitive, "SITE", site):
        assert competitive.main() == 0, "scratch site failed competitive claims"
        mutations = (
            (raw.replace(note, "", 1), "requires a VERIFIED note dated"),
            (raw.replace(note, note.replace("11 November 2026", "10 November 2026"), 1),
             "requires a VERIFIED note dated"),
        )
        mutations += tuple(
            (raw.replace(note, note.replace(f'href="{source}"', 'href="/"'), 1),
             "VERIFIED note is missing source")
            for source in SOURCES
        )
        try:
            for changed, expected in mutations:
                page.write_text(changed)
                output = io.StringIO()
                with redirect_stdout(output), redirect_stderr(output):
                    code = competitive.main()
                assert code == 1 and expected in output.getvalue(), output.getvalue()
        finally:
            page.write_text(raw)
    print("PASS competitive gate rejects missing notes, wrong dates and either missing source")


def main():
    protected = {path: (ROOT / path).read_bytes()
                 for path in ("data/ai-assistants-run.json", "data/build-id.txt")}
    with tempfile.TemporaryDirectory(prefix="test-ai-assistants-mcp-") as temporary:
        destination = Path(temporary)
        scratch(destination)
        build(destination, "checkengine")
        print("PASS scratch build with DOCKET_SKIP_BRAND_ASSETS=1 TZ=UTC")
        site = destination / "site"
        raw, note = check_page(site)
        check_competitive_gate(site, raw, note)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SITE_BRAND="checkengine", TZ="UTC")
        failures = []
        for script, args in (
            ("lint.py", ["site"]),
            ("verify_numbers.py", []),
            ("verify_datelines.py", []),
            ("verify_structured_data_matches_page.py", []),
            ("verify_price_claims.py", []),
            ("verify_version_strings.py", []),
        ):
            command = [sys.executable, "scripts/" + script, *args]
            result = subprocess.run(command, cwd=destination, env=env, capture_output=True, text=True)
            print("COMMAND python3 scripts/" + script + (" " + " ".join(args) if args else ""))
            print(result.stdout + result.stderr, end="")
            print(f"EXIT {result.returncode}", flush=True)
            if result.returncode:
                failures.append(script)
        assert not failures, failures
    for path, before in protected.items():
        assert (ROOT / path).read_bytes() == before, path
    print("OK")


if __name__ == "__main__":
    main()
