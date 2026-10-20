#!/usr/bin/env python3
"""Derive the August-to-October llms.txt figures from the two raw surveys.

    python3 scripts/build_llms_adoption.py            # writes the two files below
    python3 scripts/build_llms_adoption.py --check    # fails if they are stale

Inputs (data/, compressed, one record per host, already collected: this file
makes no request to anyone):

    ai-directives-survey-2026-08.json.gz            the August run
    ai-directives-survey-2026-10.json.gz            the October re-run, same hosts
    ai-directives-llms-validation-2026-08.json.gz   /llms.txt and control fetches
    ai-directives-llms-validation-2026-10.json.gz   the same, October

Outputs:

    data/llms-adoption-2026-10.json       every number the page quotes. AGGREGATES
                                          ONLY: no host appears in it. facts.py
                                          reads this and nothing else.
    site/data/llms-adoption-2026-10.csv   the summary the page offers as a download.

WHAT "A REAL LLMS.TXT" MEANS, inherited from the August page and not chosen here:

    1. /llms.txt answered 200 (for the validation step's own request),
    2. a made-up path on the same host did NOT also answer 200 (otherwise the
       host answers yes to everything: a catch-all or a soft 404), and
    3. the first bytes are not another kind of file: not XML, JSON, an HTML
       comment or page, a robots.txt or a sitemap, not empty, not compressed
       bytes the survey could not decode.

Rules 2 and 3 are `build_directives.py`'s own code, imported rather than copied,
and applied to both months unchanged. Before it computes anything for October
this file recomputes the August figures the site already publishes
(site/data/ai-directives-2026-08.json) and refuses to continue if they differ:
a comparison against August is only worth making if it reads August the way the
August page did.

WHAT IS NOT LIKE FOR LIKE, stated here once so the page can state it plainly:

  * The survey's first filter (which 200 answers become "candidates") is
    reconstructed for October and unrecoverable for August. The checks that
    follow it are identical. `rule_sensitive` counts the most the difference can
    touch in the same-site comparison.
  * The October collector did not follow an HTTP 308 redirect (Python 3.9's
    urllib does not); the August records hold none. `redirects` counts them.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AUG = DATA / "ai-directives-survey-2026-08.json.gz"
OCT = DATA / "ai-directives-survey-2026-10.json.gz"
VAL_AUG = DATA / "ai-directives-llms-validation-2026-08.json.gz"
VAL_OCT = DATA / "ai-directives-llms-validation-2026-10.json.gz"
AUG_PUBLISHED = ROOT / "site" / "data" / "ai-directives-2026-08.json"
OUT_JSON = DATA / "llms-adoption-2026-10.json"
OUT_CSV = ROOT / "site" / "data" / "llms-adoption-2026-10.csv"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directives as BD  # noqa: E402

CITATION, TRAINING = BD.CITATION, BD.TRAINING
DENIED = BD.DENIED_STATUS
BANDS = BD.RANK_BANDS
#: How much of a file the validation step kept (collect_ai_directives.HEAD_CHARS).
HEAD_CHARS = 300
KB100 = 100 * 1024


def _read(path: Path):
    return json.loads(gzip.decompress(path.read_bytes()))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _strip(head: str) -> str:
    return head.lstrip("﻿ \t\r\n")


def _kind(head: str) -> str:
    """Why a head is not an llms.txt, by the same openings build_directives refuses."""
    h = _strip(head or "").lower()
    if not h:
        return "empty"
    if h.startswith(BD._BINARY):
        return "compressed"
    for opening, name in (("<?xml", "xml"), ("<!--", "html"), ("<!doctype", "html"),
                          ("<html", "html"), ("{", "json"), ("[", "json"),
                          ("user-agent:", "robots"), ("sitemap:", "robots")):
        if h.startswith(opening):
            return name
    return "file"


def confirm(validation: list[dict]) -> dict:
    """The August page's own rule, as a function of one month's validation file."""
    soft = [v for v in validation if v.get("ctrl_status") == 200]
    passed = [v for v in validation
              if v.get("llms_status") == 200 and v.get("ctrl_status") != 200]
    wrong = [v for v in passed if not BD._is_llms_body(v.get("llms_head") or "")]
    wrong_ids = {id(v) for v in wrong}
    confirmed = {v["host"] for v in passed if id(v) not in wrong_ids}
    return {
        "candidates": len(validation), "soft404": len(soft),
        "wrong_kind": len(wrong),
        "wrong_kind_by": dict(sorted(Counter(_kind(v.get("llms_head")) for v in wrong).items())),
        # Candidates the made-up path did not catch and that were not a 200 when the
        # validation step asked again. August only (see the module docstring).
        "not_200_on_recheck": len(validation) - len(soft) - len(passed),
        "confirmed": confirmed,
    }


def answer_class(rec: dict, val: dict | None, confirmed: set) -> str:
    """What one asked host's /llms.txt came to, in one word."""
    if rec["host"] in confirmed:
        return "file"
    status = rec.get("llms_status")
    if status is None:
        return "no_answer"
    if status in (404, 410):
        return "gone"
    if status in DENIED:
        return "refused"
    if 300 <= status < 400:
        return "redirect"
    if status == 200:
        if val is None:
            return "page"                  # 200, and not taken for a text file
        if val.get("ctrl_status") == 200:
            return "soft404"
        if val.get("llms_status") != 200:
            return "unconfirmed"
        return "other_kind"
    return "other"


def _rate(group: list[dict], bots) -> float:
    return round(100 * sum(1 for r in group if any(
        (r.get("access") or {}).get(b) is False for b in bots)) / len(group), 2)


def _risk_ratio(exposed: list[dict], control: list[dict], bots) -> dict:
    """Katz log-method risk ratio, build_directives.risk_ratio's formula."""
    def hit(r):
        return any((r.get("access") or {}).get(b) is False for b in bots)
    a, b = sum(1 for r in exposed if hit(r)), sum(1 for r in control if hit(r))
    rr = (a / len(exposed)) / (b / len(control))
    se = math.sqrt(1 / a - 1 / len(exposed) + 1 / b - 1 / len(control))
    return {"rr": round(rr, 3), "events_exposed": a, "events_control": b,
            "lo": round(rr * math.exp(-1.96 * se), 2),
            "hi": round(rr * math.exp(1.96 * se), 2)}


def month(recs: dict, validation: list[dict]) -> tuple:
    """Every per-month figure the page quotes, from one survey and its validation."""
    ok = [r for r in recs.values() if r["state"] == "ok"]
    asked = [r for r in ok if r.get("llms_allowed_for_us")]
    c = confirm(validation)
    confirmed = c.pop("confirmed")
    val = {v["host"]: v for v in validation}
    if len(val) != len(validation):
        raise SystemExit("build: a host appears twice in a validation file")
    n200 = [r for r in asked if r.get("llms_status") == 200]

    answers = {
        "gone": sum(1 for r in asked if r.get("llms_status") in (404, 410)),
        "ok_200": len(n200),
        "refused": sum(1 for r in asked if r.get("llms_status") in DENIED),
        "redirect": sum(1 for r in asked if 300 <= (r.get("llms_status") or 0) < 400),
        "no_answer": sum(1 for r in asked if r.get("llms_status") is None),
    }
    answers["other"] = len(asked) - sum(answers.values())

    # What the 200 answers were, as far as the survey kept it.
    html_200 = sum(1 for r in n200 if not r.get("llms_present")
                   and (r.get("llms_ctype") or "").split(";")[0].strip() == "text/html")
    empty_200 = sum(1 for r in n200 if not r.get("llms_present") and not r.get("llms_bytes"))

    bands = []
    for lo, hi in BANDS:
        grp = [r for r in ok if lo <= r["rank"] <= hi]
        got = sum(1 for r in grp if r["host"] in confirmed)
        bands.append({"from": lo, "to": hi, "readable": len(grp), "confirmed": got,
                      "pct": round(100 * got / len(grp), 2)})

    conf = [recs[h] for h in confirmed]
    heads = [_strip(val[h].get("llms_head") or "") for h in confirmed]
    h1 = [x for x in heads if x.startswith("# ")]

    def blockquote_next(head: str) -> bool:
        for line in head.split("\n")[1:]:
            if line.strip():
                return line.lstrip().startswith(">")
        return False

    sizes = sorted(r["llms_bytes"] for r in conf)
    ctypes = Counter((r.get("llms_ctype") or "").split(";")[0].strip() for r in conf)
    files = {
        "confirmed": len(conf), "h1": len(h1),
        "h1_blockquote": sum(1 for x in h1 if blockquote_next(x)),
        "text_plain": ctypes.get("text/plain", 0),
        "text_markdown": ctypes.get("text/markdown", 0),
        "other_type": len(conf) - ctypes.get("text/plain", 0) - ctypes.get("text/markdown", 0),
        "median_bytes": int(statistics.median(sizes)),
        "over_100kb": sum(1 for s in sizes if s >= KB100),
        "under_1kb": sum(1 for s in sizes if s < 1024),
    }

    with_f = [r for r in asked if r["host"] in confirmed]
    without = [r for r in asked if r["host"] not in confirmed]
    blocking = {
        "with": len(with_f), "without": len(without),
        "search_with": sum(1 for r in with_f if any(
            (r.get("access") or {}).get(b) is False for b in CITATION)),
        "search_without": sum(1 for r in without if any(
            (r.get("access") or {}).get(b) is False for b in CITATION)),
        "training_with": sum(1 for r in with_f if any(
            (r.get("access") or {}).get(b) is False for b in TRAINING)),
        "training_without": sum(1 for r in without if any(
            (r.get("access") or {}).get(b) is False for b in TRAINING)),
        "search_rate_with": _rate(with_f, CITATION), "search_rate_without": _rate(without, CITATION),
        "training_rate_with": _rate(with_f, TRAINING), "training_rate_without": _rate(without, TRAINING),
        "rr_search": _risk_ratio(with_f, without, CITATION),
        "rr_training": _risk_ratio(with_f, without, TRAINING),
    }

    out = {
        "readable": len(ok), "asked": len(asked),
        "not_asked_disallowed": len(ok) - len(asked),
        "answered_200": len(n200), "answered_200_html": html_200,
        "answered_200_empty": empty_200,
        **c,
        "confirmed": len(confirmed),
        "pct_of_readable": round(100 * len(confirmed) / len(ok), 2),
        "pct_of_asked": round(100 * len(confirmed) / len(asked), 2),
        "pct_of_200": round(100 * len(confirmed) / len(n200), 2),
        "answers": answers, "bands": bands, "files": files, "blocking": blocking,
        "refused_pct": round(100 * answers["refused"] / len(asked), 2),
        "gone_pct": round(100 * answers["gone"] / len(asked), 2),
    }
    return out, confirmed, asked


def verify_august(a: dict) -> dict:
    """Recompute what the site already publishes about August; refuse on a mismatch."""
    pub = json.loads(AUG_PUBLISHED.read_text())
    s = pub["summary"]
    got = {
        "llms_candidates": a["candidates"], "llms_soft404": a["soft404"],
        "llms_wrong_kind": a["wrong_kind"],
        "llms_false_positive": a["soft404"] + a["wrong_kind"],
        "llms_confirmed": a["confirmed"], "pct_llms_adoption": a["pct_of_readable"],
        "probed_for_llms": a["asked"],
        "llms_edge_denied": a["answers"]["refused"],
        "pct_llms_edge_denied": a["refused_pct"],
        "cit_rate_llms": a["blocking"]["search_rate_with"],
        "cit_rate_no_llms": a["blocking"]["search_rate_without"],
        "train_rate_llms": a["blocking"]["training_rate_with"],
        "train_rate_no_llms": a["blocking"]["training_rate_without"],
        "rr_citation_llms": a["blocking"]["rr_search"],
        "rr_training_llms": a["blocking"]["rr_training"],
    }
    bad = {k: (got[k], s[k]) for k in got if got[k] != s[k]}
    bands = [{"from": b["from"], "to": b["to"], "n": b["readable"], "llms": b["confirmed"],
              "pct": b["pct"]} for b in a["bands"]]
    if bands != [{k: v for k, v in b.items()} for b in pub["llms_by_rank"]]:
        bad["llms_by_rank"] = (bands, pub["llms_by_rank"])
    if bad:
        raise SystemExit(f"build: cannot reproduce the August llms.txt figures the site "
                         f"already publishes: {bad} (ours, theirs). A comparison against "
                         f"August would not be reading August the way August was read.")
    return {k: got[k] for k in got if not isinstance(got[k], dict)}


def _not_asked_why(recs: dict, host: str) -> str:
    r = recs[host]
    if r["state"] == "ok":
        return "disallows_our_agent"
    if r.get("robots_status") in DENIED:
        return "refused"
    if r.get("robots_status") == 308:
        return "robots_308"
    return {"unreachable": "unreachable", "oversize": "oversize"}.get(r["state"], "no_robots")


def build() -> dict:
    aug_raw, oct_raw = _read(AUG), _read(OCT)
    val_a, val_o = _read(VAL_AUG), _read(VAL_OCT)
    A = {r["host"]: r for r in aug_raw["records"]}
    O = {r["host"]: r for r in oct_raw["records"]}
    if set(A) != set(O):
        raise SystemExit("build: the two surveys are not on the same host list")

    aug, conf_a, asked_a = month(A, val_a)
    reproduced = verify_august(aug)
    oct_, conf_o, asked_o = month(O, val_o)

    # -- the same sites: asked in both months -------------------------------
    ask_a = {r["host"] for r in asked_a}
    ask_o = {r["host"] for r in asked_o}
    panel = sorted(ask_a & ask_o)
    va = {v["host"]: v for v in val_a}
    vo = {v["host"]: v for v in val_o}
    both = [h for h in panel if h in conf_a and h in conf_o]
    started = [h for h in panel if h not in conf_a and h in conf_o]
    stopped = [h for h in panel if h in conf_a and h not in conf_o]
    stopped_to = Counter(answer_class(O[h], vo.get(h), conf_o) for h in stopped)
    started_from = Counter(answer_class(A[h], va.get(h), conf_a) for h in started)
    # A 200 that one month's first filter set aside: the only place the two
    # months' reconstructed candidate rules could have produced a change.
    rule_sensitive = {
        "started": sum(1 for h in started if answer_class(A[h], va.get(h), conf_a) == "page"),
        "stopped": sum(1 for h in stopped if answer_class(O[h], vo.get(h), conf_o) == "page"),
    }

    left_out_a = [h for h in conf_a if h not in ask_o]
    left_out_o = [h for h in conf_o if h not in ask_a]
    why_a = Counter(_not_asked_why(O, h) for h in left_out_a)
    why_o = Counter(_not_asked_why(A, h) for h in left_out_o)
    reasons = ("robots_308", "refused", "unreachable", "oversize", "no_robots",
               "disallows_our_agent")

    pband = []
    for lo, hi in BANDS:
        grp = [h for h in panel if lo <= A[h]["rank"] <= hi]
        pband.append({"from": lo, "to": hi, "asked": len(grp),
                      "aug": sum(1 for h in grp if h in conf_a),
                      "oct": sum(1 for h in grp if h in conf_o)})

    panel_d = {
        "asked_both": len(panel), "both": len(both), "started": len(started),
        "stopped": len(stopped),
        "neither": len(panel) - len(both) - len(started) - len(stopped),
        "aug_total": len(both) + len(stopped), "oct_total": len(both) + len(started),
        "started_from": dict(sorted(started_from.items())),
        "stopped_to": dict(sorted(stopped_to.items())),
        "rule_sensitive": rule_sensitive, "bands": pband,
    }
    reconcile = {
        "aug_confirmed": aug["confirmed"], "oct_confirmed": oct_["confirmed"],
        "aug_not_asked_in_oct": len(left_out_a), "oct_not_asked_in_aug": len(left_out_o),
        "aug_left_out_why": {k: why_a.get(k, 0) for k in reasons},
        "oct_new_left_out_why": {k: why_o.get(k, 0) for k in reasons},
    }
    if (panel_d["aug_total"] + reconcile["aug_not_asked_in_oct"] != aug["confirmed"]
            or panel_d["oct_total"] + reconcile["oct_not_asked_in_aug"] != oct_["confirmed"]):
        raise SystemExit("build: the same-site comparison does not add up to the totals")

    # -- the October re-reads (collect_ai_directives.py --reread) ------------------
    #
    # The main October run did not follow an HTTP 308 and could not connect to some
    # hosts under its older Python and TLS library; those hosts were read again, and
    # the survey keeps the record each re-read replaced. Everything above already
    # reads the merged records. These counts say how much of it came from re-reads.
    passes = oct_raw.get("reread", [])
    p308 = next((p for p in passes if p["kind"] == "308"), None)
    pconn = next((p for p in passes if p["kind"] == "connect"), None)
    reread_hosts = {h["host"] for p in passes for h in p["hosts"]}
    was308 = [h for p in passes for h in p["hosts"] if h["was"].get("robots_status") == 308]
    redirects = {
        "robots_308_aug": sum(1 for r in A.values() if r.get("robots_status") == 308),
        "robots_308_oct": sum(1 for r in O.values() if r.get("robots_status") == 308),
        "llms_308_oct": sum(1 for r in asked_o if r.get("llms_status") == 308),
    }
    http_ok = [r for r in O.values() if r["state"] == "ok" and r.get("scheme") == "http"]
    sensitivity = {"http_read": {
        "readable": len(http_ok),
        "confirmed": sum(1 for r in http_ok if r["host"] in conf_o),
        "readable_total": oct_["readable"], "confirmed_total": oct_["confirmed"]}}
    reread = {
        "hosts": len(reread_hosts),
        "date": max((p["at"][:10] for p in passes), default=""),
        "was_robots_308": len(was308),
        "was_llms_308": sum(1 for p in passes for h in p["hosts"]
                            if h["was"].get("llms_status") == 308),
        "connect_hosts": len(pconn["hosts"]) if pconn else 0,
        "python_major_minor": ".".join(passes[0]["python"].split(".")[:2]) if passes else "",
        "robots_308_readable_in_aug": sum(1 for h in was308 if A[h["host"]]["state"] == "ok"),
        "robots_308_aug_confirmed": sum(1 for h in was308 if h["host"] in conf_a),
        "confirmed_among": sum(1 for h in reread_hosts if h in conf_o),
        "became_readable": sum(1 for p in passes for h in p["hosts"]
                               if h["was"]["state"] != "ok" and O[h["host"]]["state"] == "ok"),
    }

    return {
        "meta": {
            "aug_collected": aug_raw["collected"], "oct_collected": oct_raw["collected"],
            "oct_finished": oct_raw.get("finished"),
            "population": oct_raw["population"], "hosts": len(A),
            "user_agent": oct_raw["method"]["user_agent"],
            "timeout_s": oct_raw["method"]["timeout_s"],
            "head_chars": HEAD_CHARS,
            "inputs": {"aug": _sha(AUG), "oct": _sha(OCT),
                       "aug_validation": _sha(VAL_AUG), "oct_validation": _sha(VAL_OCT)},
        },
        "aug": aug, "oct": oct_, "august_reproduced": reproduced,
        "panel": panel_d, "reconcile": reconcile, "redirects": redirects, "reread": reread,
        "sensitivity": sensitivity,
    }


def csv_rows(d: dict) -> list[list]:
    """The download: aggregates only. No host appears in it."""
    a, o, p = d["aug"], d["oct"], d["panel"]
    rows = [["section", "measure", "august", "october", "same_sites"]]

    def add(section, measure, av="", ov="", sv=""):
        rows.append([section, measure, av, ov, sv])

    add("Sample", "Sites in the list", d["meta"]["hosts"], d["meta"]["hosts"])
    add("Sample", "Sites with a readable robots.txt (the base of the headline share)",
        a["readable"], o["readable"])
    add("Sample", "Sites whose robots.txt let our bot ask for /llms.txt", a["asked"], o["asked"])
    add("Headline", "Sites with a real llms.txt", a["confirmed"], o["confirmed"])
    add("Headline", "Share of readable robots.txt files (percent)",
        f"{a['pct_of_readable']:.2f}", f"{o['pct_of_readable']:.2f}")
    add("Headline", "Share of sites we could ask (percent)",
        f"{a['pct_of_asked']:.2f}", f"{o['pct_of_asked']:.2f}")
    add("Funnel", "Answered 200 at /llms.txt", a["answered_200"], o["answered_200"])
    add("Funnel", "Candidates kept by the survey's first filter", a["candidates"], o["candidates"])
    add("Funnel", "Made-up path also answered 200 (soft 404)", a["soft404"], o["soft404"])
    add("Funnel", "Another kind of file (XML, JSON, robots.txt, HTML, compressed, empty)",
        a["wrong_kind"], o["wrong_kind"])
    add("Funnel", "Did not answer 200 when asked again", a["not_200_on_recheck"],
        o["not_200_on_recheck"])
    add("Funnel", "Real llms.txt", a["confirmed"], o["confirmed"])
    for key, label in (("gone", "Answered 404 or 410"), ("ok_200", "Answered 200"),
                       ("refused", "Refused (401, 403, 406, 429 or 503)"),
                       ("redirect", "Redirect not completed (3xx)"),
                       ("no_answer", "No answer (error or timeout)"),
                       ("other", "Any other status")):
        add("What /llms.txt answered", label, a["answers"][key], o["answers"][key])
    for ba, bo in zip(a["bands"], o["bands"]):
        add("By Tranco rank", f"Ranks {ba['from']} to {ba['to']}: readable robots.txt",
            ba["readable"], bo["readable"])
        add("By Tranco rank", f"Ranks {ba['from']} to {ba['to']}: real llms.txt",
            ba["confirmed"], bo["confirmed"])
        add("By Tranco rank", f"Ranks {ba['from']} to {ba['to']}: share (percent)",
            f"{ba['pct']:.2f}", f"{bo['pct']:.2f}")
    add("Same sites", "Sites asked in both months", p["asked_both"], p["asked_both"], p["asked_both"])
    add("Same sites", "Real llms.txt, same sites", p["aug_total"], p["oct_total"])
    add("Same sites", "Had one in both months", "", "", p["both"])
    add("Same sites", "Started having one", "", "", p["started"])
    add("Same sites", "Stopped having one", "", "", p["stopped"])
    add("Same sites", "Had neither time", "", "", p["neither"])
    add("Files", "Opens with a Markdown H1", a["files"]["h1"], o["files"]["h1"])
    add("Files", "H1 followed by a blockquote summary", a["files"]["h1_blockquote"],
        o["files"]["h1_blockquote"])
    add("Files", "Served as text/plain", a["files"]["text_plain"], o["files"]["text_plain"])
    add("Files", "Served as text/markdown", a["files"]["text_markdown"],
        o["files"]["text_markdown"])
    add("Files", "Median size in bytes", a["files"]["median_bytes"], o["files"]["median_bytes"])
    add("Files", "Larger than 100 KB", a["files"]["over_100kb"], o["files"]["over_100kb"])
    add("Blocking", "Sites with a real llms.txt, among those we could ask",
        a["blocking"]["with"], o["blocking"]["with"])
    add("Blocking", "Sites without one, among those we could ask",
        a["blocking"]["without"], o["blocking"]["without"])
    for key, label in (("search", "blocks an AI search crawler"),
                       ("training", "blocks an AI training crawler")):
        add("Blocking", f"With a real llms.txt: {label}", a["blocking"][f"{key}_with"],
            o["blocking"][f"{key}_with"])
        add("Blocking", f"Without one: {label}", a["blocking"][f"{key}_without"],
            o["blocking"][f"{key}_without"])
    return rows


def write(d: dict) -> None:
    OUT_JSON.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        csv.writer(fh, lineterminator="\n").writerows(csv_rows(d))


def main() -> int:
    d = build()
    text = json.dumps(d, indent=1, sort_keys=True) + "\n"
    if "--check" in sys.argv:
        if not OUT_JSON.exists() or OUT_JSON.read_text() != text:
            print(f"STALE  {OUT_JSON.name} is not what the raw surveys derive to")
            return 1
        print("llms-adoption derived data ok")
        return 0
    write(d)
    print(json.dumps({k: d[k] for k in ("panel", "reconcile", "redirects", "reread")}, indent=1))
    for m in ("aug", "oct"):
        print(m, {k: d[m][k] for k in ("readable", "asked", "answered_200", "candidates",
                                        "soft404", "wrong_kind", "confirmed",
                                        "pct_of_readable")})
    print(f"wrote {OUT_JSON} and {OUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
