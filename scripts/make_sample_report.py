#!/usr/bin/env python3
"""Make the public sample report: a real Docket audit of builtbykerr.com.

WHY THIS FILE EXISTS. The sample was made by a script in a session scratchpad,
and the power cut of 2026-09-29 erased it. The sample is the first thing a
doubter reads, so the way it is made lives here now, with the site.

THE RULE IT KEEPS (CEO, 2026-10-01): the site's sample must never show what the
shipped app would not produce. Run it with the engine of the release the site
is about to describe (`--engine` points at that checkout's backend/), and only
when that release ships.

What it changes in the engine's result, and says so on page 1 of the PDF:
  * the cookie-consent finding is left out: adding a banner is the owner's
    decision, and this site does not urge consent banners;
  * the addresses of links to other sites are removed, because this public
    site never names a third-party site.
Nothing else. The score, the counts and the order are the engine's, and the
cover's "issues found" is the full audit's count, which the note states.

The site's subjects are given, as a customer would give them, so the topic
suggestions are for what the business sells rather than a guess.

    HOME=$(mktemp -d) ../docket-app/.venv/bin/python scripts/make_sample_report.py \\
        --engine ../docket-app/backend [--out site/assets/docket-sample-report.pdf]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
URL = "https://builtbykerr.com/"
HOST = "builtbykerr.com"
SUBJECTS = ["web design", "local seo"]
_URL_RE = re.compile(r"https?://[^\s\"'<>)]+")


def _own(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host == HOST or host.endswith("." + HOST)


def public_copy(result):
    """The engine's result with the two stated edits, and the note saying so."""
    consent = [f for f in result.findings if "consent" in f.check_id]
    result.findings = [f for f in result.findings if f not in consent]
    result.plan = [i for i in result.plan if i.finding not in consent]
    # The engine's own headline builder, on the findings that remain, so the
    # cover still lists the five that matter most rather than four.
    from seo_engine.scoring import summarize
    result.headlines = summarize(result.findings, result.score)

    removed = set()
    for f in result.findings:
        keep = []
        for u in f.urls:
            if _own(u):
                keep.append(u)
            else:
                removed.add(u)
        f.urls = keep
        for attr in ("detail", "fix", "snippet"):
            text = getattr(f, attr) or ""

            def scrub(m):
                if _own(m.group(0)):
                    return m.group(0)
                removed.add(m.group(0))
                return "(another site's address)"
            setattr(f, attr, _URL_RE.sub(scrub, text))

    total = result.score.total_findings
    parts = []
    if consent:
        sev = consent[0].severity.name.lower()
        parts.append(f"{'one' if len(consent) == 1 else len(consent)} {sev} finding"
                     f"{'' if len(consent) == 1 else 's'}, about this site's cookie consent, "
                     "because that change is the owner's decision")
    if removed:
        parts.append(f"the addresses of {len(removed)} link{'' if len(removed) == 1 else 's'} "
                     "to other sites")
    note = ("This public copy leaves out " + ", and ".join(parts) +
            f"; the full audit had {total} findings.") if parts else (
            f"This public copy is the audit exactly as Docket produced it: {total} findings.")
    return result, note, {"consent_left_out": len(consent), "addresses_removed": len(removed),
                          "full_findings": total}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--engine", required=True, help="the release's backend/ directory")
    ap.add_argument("--out", default=str(ROOT / "site" / "assets" / "docket-sample-report.pdf"))
    args = ap.parse_args()
    sys.path.insert(0, str(Path(args.engine).resolve()))

    from seo_engine import __version__, connectors, report_pdf
    from seo_engine.audit import run_audit

    result = run_audit(URL, connector_settings=connectors.ConnectorSettings(topics=SUBJECTS))
    result, note, facts = public_copy(result)

    draw_cover = report_pdf._draw_cover

    def cover_with_note(layout):
        draw_cover(layout)
        layout.eyebrow("About this copy")
        layout.paragraph(note)

    report_pdf._draw_cover = cover_with_note
    try:
        pdf = report_pdf.build(result)
    finally:
        report_pdf._draw_cover = draw_cover
    Path(args.out).write_bytes(pdf)
    summary = {"engine": __version__, "url": URL, "score": round(result.score.overall, 1),
               "grade": result.score.to_dict()["grade"], "pages": len(result.crawl.pages),
               "bytes": len(pdf), "note": note, **facts}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
