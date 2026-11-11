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

from brand import SITE_BRAND

ROOT = Path(__file__).resolve().parents[1]
URL = "https://builtbykerr.com/"
HOST = "builtbykerr.com"
SUBJECTS = ["web design", "local seo"]
_URL_RE = re.compile(r"https?://[^\s\"'<>)]+")
DEFAULT_OUT = ROOT / "site" / "assets" / "docket-sample-report.pdf"
COVER = ROOT / "site" / "assets" / "sample-report-cover.webp"
BRANDED_COVER = ROOT / "site" / "assets" / "sample-report-branded-cover.webp"
COVER_WIDTH = 1280
SAMPLE_RUN = ROOT / "data" / "sample-run.json"


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


def _cut_below_facts(im) -> int:
    """Where to end the cover still: the first white band at least 3.5% of the width tall, searched from two
    thirds of the width down. On page 1 that is the gap under the facts strip (pages crawled, checks run, issues
    found, audit time). The gap between the strip's numbers and its labels is about 2%, so it is never taken for
    it; a longer summary only moves the strip, and the band with it."""
    gray = im.convert("L")
    w, h = gray.size
    x0, x1 = int(w * 0.05), int(w * 0.95)
    need, run = int(w * 0.035), 0
    for y in range(int(w * 0.66), int(h * 0.9)):
        row = gray.crop((x0, y, x1, y + 1))
        run = run + 1 if row.getextrema()[0] >= 245 else 0
        if run >= need:
            return y - run + int(w * 0.03)
    raise SystemExit("make_sample_report: no white band under the cover's facts strip; the cover layout changed, "
                     "so look at page 1 and set the cut again")


def _pil():
    """Pillow's Image. This script runs under a temp HOME so the engine never sees the licence, which also hides the
    user site-packages where Pillow is installed. Pillow is not the engine; look for it under the real home."""
    import os
    import pwd
    try:
        from PIL import Image
    except ImportError:
        real = pwd.getpwuid(os.getuid()).pw_dir
        sys.path.append(f"{real}/Library/Python/{sys.version_info[0]}.{sys.version_info[1]}/lib/python/site-packages")
        from PIL import Image
    return Image


def _cover_still(pdf_path: Path):
    """Page 1 of the PDF at `pdf_path`, cut below the facts strip and scaled to COVER_WIDTH."""
    import subprocess
    import tempfile
    Image = _pil()
    with tempfile.TemporaryDirectory() as tmp:
        # Quick Look renders the PDF exactly as Preview shows it: page 1, 2200 px tall.
        subprocess.run(["qlmanage", "-t", "-s", "2200", "-o", tmp, str(pdf_path)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        page = Image.open(Path(tmp) / (pdf_path.name + ".png")).convert("RGB")
    still = page.crop((0, 0, page.width, _cut_below_facts(page)))
    return still.resize((COVER_WIDTH, round(COVER_WIDTH * still.height / still.width)), Image.LANCZOS)


#: The branded variant on /for/agencies/ shows Report branding with a placeholder, never a real agency's name: a
#: picture of a report "prepared by" a firm that did not prepare it would be a testimonial nobody gave.
PLACEHOLDER_NAME = "Your agency name"


def placeholder_brand():
    """A Branding with PLACEHOLDER_NAME and a drawn "YOUR LOGO" JPEG."""
    import io
    from seo_engine import branding
    Image = _pil()
    from PIL import ImageDraw
    im = Image.new("RGB", (420, 140), (236, 238, 242))
    g = ImageDraw.Draw(im)
    g.rectangle((6, 6, 413, 133), outline=(150, 156, 168), width=4)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 54)
    except OSError:
        font = None
    g.text((210, 70), "YOUR LOGO", fill=(90, 96, 110), font=font, anchor="mm")
    out = io.BytesIO()
    im.save(out, "JPEG", quality=90)
    return branding.validate(PLACEHOLDER_NAME, out.getvalue())


def write_sample_run(run: dict, path: Path) -> None:
    """Write the sample metadata with the current site brand last."""
    run = {**run, "site_brand": SITE_BRAND}
    path.write_text(json.dumps(run, indent=1) + "\n", encoding="utf-8")


def write_cover(result, pdf_path: Path, version: str, branded_pdf: bytes = b"") -> None:
    """The home page's 'This is the actual report' image and its caption's figures, from this run.

    That block showed a screenshot of a Docket 1.1.44 report from 17 August (12 pages, 8 seconds, 90/A) under prose
    calling it the file Docket writes, while the build was 1.3.141 and its report a different layout (Matthew's
    full audit, 2026-11-04, row 5). The picture is now page 1 of the PDF this script has just written,
    and data/sample-run.json carries what that page prints, so the caption re-captions itself on every ship and
    verify_recordings_fresh.py refuses it once it falls behind the build."""
    import datetime as dt
    import tempfile
    from seo_engine.words import local_date

    still = _cover_still(pdf_path)
    still.save(COVER, "WEBP", quality=86)
    branded = None
    if branded_pdf:
        with tempfile.TemporaryDirectory() as tmp:
            bp = Path(tmp) / "branded.pdf"
            bp.write_bytes(branded_pdf)
            b = _cover_still(bp)
        b.save(BRANDED_COVER, "WEBP", quality=86)
        branded = {"src": "/assets/" + BRANDED_COVER.name, "width": b.width, "height": b.height,
                   "name": PLACEHOLDER_NAME}
    d = result.score.to_dict()
    projection = getattr(result, "projection", None)
    run = {"engine": version, "recorded": dt.datetime.now(dt.timezone.utc).date().isoformat(),
           "report_date": local_date(result.finished_at), "url": URL,
           "score": round(result.score.overall), "grade": d["grade"], "pages": len(result.crawl.pages),
           "seconds": round(result.duration), "issues": result.score.total_findings,
           "counts": {k: v for k, v in d["counts"].items() if v},
           # The cover's "Fix everything in this report and this becomes {ceiling}/100: {actionable} items".
           "ceiling": round(projection.ceiling) if projection else None,
           "actionable": projection.actionable if projection else None,
           "excluded": projection.blocked if projection else 0,
           "image": {"src": "/assets/" + COVER.name, "width": still.width, "height": still.height},
           # The same report with Report branding set to a placeholder (PLACEHOLDER_NAME), for /for/agencies/.
           "branded_image": branded}
    write_sample_run(run, SAMPLE_RUN)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--engine", required=True, help="the release's backend/ directory")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
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
    default_out = Path(args.out).resolve() == DEFAULT_OUT.resolve()
    try:
        pdf = report_pdf.build(result)
        branded_pdf = report_pdf.build(result, branding=placeholder_brand()) if default_out else b""
    finally:
        report_pdf._draw_cover = draw_cover
    Path(args.out).write_bytes(pdf)
    if default_out:
        write_cover(result, Path(args.out), __version__, branded_pdf)
    summary = {"engine": __version__, "url": URL, "score": round(result.score.overall, 1),
               "grade": result.score.to_dict()["grade"], "pages": len(result.crawl.pages),
               "bytes": len(pdf), "note": note, **facts}
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
