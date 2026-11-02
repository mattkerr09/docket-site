#!/usr/bin/env python3
"""Audit real public small-business sites with the SHIPPED Docket and keep the numbers, never the sites.

Matthew, 2026-11-02, via the CEO: pages that earn clicks carry numbers we measured ourselves (a median of 4 on the
company's earning pages; Docket's median page had none). This runs the engine from a release's own DMG (served on a
port by the caller, with a throwaway HOME and no key, so it is exactly a customer's free audit) against a private
list of sites, and writes data/field-audits.json:

  * per site: the kind of business (never its address), the platform Docket named, pages read, seconds taken, the
    score and grade, and how many problems in each area;
  * the engine version and build, the date, and the settings, so every number on a page can say what it was.

The list of sites lives outside this repo (~/ops/research/docket-field-sites-<date>.txt: url, a tab, the kind of
business). verify_no_named_third_parties.py keeps a domain from ever reaching the site.

    python3 scripts/collect_field_audits.py --port 8834 --sites ~/ops/research/docket-field-sites-2026-11-02.txt
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import statistics
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "field-audits.json"


def _call(port: int, method: str, path: str, body=None, timeout: float = 30):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method,
                                 headers={"content-type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read() or b"{}")


def audit(port: int, url: str, deadline_s: int) -> dict:
    job = _call(port, "POST", "/audits", {"url": url, "offline": True})
    jid = job.get("id") or job.get("audit_id")
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        state = _call(port, "GET", f"/audits/{jid}")
        if state.get("status") in ("done", "error", "cancelled"):
            if state.get("status") != "done" or not state.get("result"):
                raise RuntimeError(f"audit ended {state.get('status')}: {str(state.get('error', ''))[:200]}")
            return state["result"]
        time.sleep(3)
    raise TimeoutError(f"no result in {deadline_s}s")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--sites", type=pathlib.Path, required=True)
    ap.add_argument("--deadline", type=int, default=1500)
    args = ap.parse_args(argv)

    health = _call(args.port, "GET", "/health")
    sites = [line.split("\t", 1) for line in args.sites.read_text().splitlines()
             if line.strip() and not line.startswith("#")]
    rows, failed = [], 0
    for url, kind in sites:
        try:
            result = audit(args.port, url.strip(), args.deadline)
        except Exception as exc:  # noqa: BLE001 — one unreachable site is a gap, not a stop
            print(f"  skip  {kind}: {type(exc).__name__}: {str(exc)[:120]}")
            failed += 1
            continue
        free = result.get("free") or {}
        rows.append({
            "kind": kind.strip(),
            "platform": (result.get("site") or {}).get("cms") or "",
            "pages": (result.get("stats") or {}).get("pages_crawled", 0),
            "seconds": round(result.get("duration", 0.0), 1),
            "score": (result.get("score") or {}).get("overall"),
            "grade": (result.get("score") or {}).get("grade"),
            "problems": free.get("problems", 0),
            "by_area": {c["label"]: c["problems"] for c in free.get("categories", []) if c.get("applicable")},
        })
        print(f"  ok    {kind}: {rows[-1]['pages']} pages, {rows[-1]['seconds']}s, {rows[-1]['problems']} problems")
    if not rows:
        print("FIELD AUDITS FAIL: no site produced a result")
        return 1
    out = {
        "date": dt.datetime.now(dt.timezone.utc).date().isoformat(),
        "engine": health.get("version"),
        "build": (health.get("build") or {}).get("sha"),
        "settings": "the app's default scope (200 pages, growing to at most 1,000 while a larger site answers quickly), with the network checks off",
        "sites": len(rows),
        "unreachable": failed,
        "median": {
            "pages": statistics.median(r["pages"] for r in rows),
            "seconds": statistics.median(r["seconds"] for r in rows),
            "problems": statistics.median(r["problems"] for r in rows),
            "score": statistics.median(r["score"] for r in rows if r["score"] is not None),
        },
        "audits": rows,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(f"FIELD AUDITS ok — {len(rows)} sites with Docket {out['engine']} ({out['build']}), {failed} unreachable")
    print(f"  written: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
