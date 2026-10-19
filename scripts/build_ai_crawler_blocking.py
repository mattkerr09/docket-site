#!/usr/bin/env python3
"""Derive the August-to-October AI-crawler blocking figures from the two raw surveys.

    python3 scripts/build_ai_crawler_blocking.py            # writes the two files below
    python3 scripts/build_ai_crawler_blocking.py --check    # fails if they are stale

Inputs (data/, compressed, one record per host):

    ai-directives-survey-2026-08.json.gz     the August run
    ai-directives-survey-2026-10.json.gz     the October re-run, same hosts
    ai-robots-txt-reference-2026-10.json.gz  the ai.robots.txt list as fetched in October

Outputs:

    data/ai-crawler-blocking-2026-10.json      every number the page quotes. AGGREGATES
                                               ONLY: no host appears in it. facts.py
                                               reads this and nothing else.
    site/data/ai-crawler-blocking-2026-10.csv  the summary the page offers as a download.

Nothing on the page computes anything. Before it writes a figure, this file
recomputes the August ones it can check against what the site already published
(site/data/ai-directives-2026-08.json) and refuses to continue if they differ:
a comparison against August is only worth making if this code reads August the
way the August run did.

DEFINITIONS, all inherited from the August page rather than chosen here:

  training crawler   GPTBot, ClaudeBot, Applebot-Extended, Bytespider,
                     meta-externalagent, CCBot            (facts.TRAINING)
  search crawler     OAI-SearchBot, PerplexityBot, Claude-SearchBot
                     (facts.CITATION; the site's word for "decides whether you
                     can be cited in an AI answer")
  Google-Extended    counted on its own. Google documents it as controlling
                     Gemini training and grounding, not AI Overviews.
  blocked            robots.txt disallows "/" for that token. A statement about
                     what the file asks, never about what a crawler did.
  readable           HTTP 200, within the size limit. A 200 that is not really a
                     robots.txt (an HTML page, an empty body) is readable and
                     blocks nothing, exactly as in August.
  same sites         readable in BOTH months. Changes are counted on these only,
                     so a site that merely became unreachable is not a change.

Every access figure uses the robots.txt parser as it stood in August. The
current parser, which fixed three August-era mistakes, is applied to the same
October text and the difference is reported separately.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
AUG = DATA / "ai-directives-survey-2026-08.json.gz"
OCT = DATA / "ai-directives-survey-2026-10.json.gz"
REF = DATA / "ai-robots-txt-reference-2026-10.json.gz"
AUG_DERIVED = ROOT / "site" / "data" / "ai-directives-2026-08.json"
RECHECK = DATA / "ai-directives-recheck-2026-10.json"
OUT_JSON = DATA / "ai-crawler-blocking-2026-10.json"
OUT_CSV = ROOT / "site" / "data" / "ai-crawler-blocking-2026-10.csv"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import facts as F  # noqa: E402

TRAINING = tuple(F.TRAINING)
SEARCH = tuple(F.CITATION)
GOOGLE_EXTENDED = "Google-Extended"
NINE = TRAINING + SEARCH
#: Cloudflare's managed block names these eight (developers.cloudflare.com, page
#: dated 2026-10-08); the same tuple the collector matches the text against.
CF_EIGHT = ("Amazonbot", "Applebot-Extended", "Bytespider", "CCBot", "ClaudeBot",
            "Google-Extended", "GPTBot", "meta-externalagent")
#: The crawlers shown one by one: the nine, Google-Extended, and the one other
#: crawler in Cloudflare's block.
#: Read by hand from Cloudflare's own page on the day of the survey. The page
#: prints "Last updated Oct 8, 2026" under its title. Recorded here, once, so no
#: page types a date: it comes out of the derived file like every other number.
CLOUDFLARE_DOC = {
    "url": "https://developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/",
    "page_dated": "2026-10-08",
    "read": "2026-10-19",
    "begin_marker": "# BEGIN Cloudflare Managed content",
    "end_marker": "# END Cloudflare Managed Content",
}
SHOWN = ("GPTBot", "ClaudeBot", "CCBot", "Applebot-Extended", "Bytespider",
         "meta-externalagent", "Amazonbot", GOOGLE_EXTENDED,
         "OAI-SearchBot", "PerplexityBot", "Claude-SearchBot")


def _read(path: Path):
    return json.loads(gzip.decompress(path.read_bytes()))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def blocked(rec: dict, bot: str) -> bool:
    return (rec.get("access") or {}).get(bot) is False


def blocked_cur(rec: dict, bot: str) -> bool:
    """The same file read by the current parser (October only)."""
    diff = rec.get("access_cur_diff") or {}
    if bot in diff:
        return diff[bot] is False
    return blocked(rec, bot)


def any_of(rec: dict, bots, fn=blocked) -> bool:
    return any(fn(rec, b) for b in bots)


METRICS = {
    "training": lambda r, fn=blocked: any_of(r, TRAINING, fn),
    "search": lambda r, fn=blocked: any_of(r, SEARCH, fn),
    "google_extended": lambda r, fn=blocked: fn(r, GOOGLE_EXTENDED),
    "any_of_nine": lambda r, fn=blocked: any_of(r, NINE, fn),
    "training_only": lambda r, fn=blocked: any_of(r, TRAINING, fn) and not any_of(r, SEARCH, fn),
    "search_and_training": lambda r, fn=blocked: any_of(r, TRAINING, fn) and any_of(r, SEARCH, fn),
    **{f"bot:{b}": (lambda r, fn=blocked, b=b: fn(r, b)) for b in SHOWN},
}


def _sig8(rec: dict) -> bool:
    """Parsed-data signature of Cloudflare's block: a Content-signal line and all
    eight of its crawlers disallowed. Available for both months, because the
    survey kept the parsed result of every file; it is a pattern, not proof."""
    return bool(rec.get("content_signal")) and all(blocked(rec, b) for b in CF_EIGHT)


def population(recs: list[dict]) -> dict:
    c = Counter(r["state"] for r in recs)
    return {"attempted": len(recs), "readable": c["ok"], "unreachable": c["unreachable"],
            "no_robots": c["no_robots"], "oversize": c["oversize"],
            "refused": sum(1 for r in recs if r.get("robots_status") in (401, 403, 406, 429, 503))}


def verify_august(aug_ok: list[dict]) -> dict:
    """Recompute what the site already published about August; refuse on a mismatch."""
    pub = json.loads(AUG_DERIVED.read_text())["summary"]
    got = {
        "parseable_robots": len(aug_ok),
        "blocks_training": sum(1 for r in aug_ok if METRICS["training"](r)),
        "blocks_citation": sum(1 for r in aug_ok if METRICS["search"](r)),
        "blocks_any": sum(1 for r in aug_ok if METRICS["any_of_nine"](r)),
        "training_only": sum(1 for r in aug_ok if METRICS["training_only"](r)),
        "oai_search_blocked": sum(1 for r in aug_ok if blocked(r, "OAI-SearchBot")),
        "claude_search_blocked": sum(1 for r in aug_ok if blocked(r, "Claude-SearchBot")),
    }
    bad = {k: (got[k], pub[k]) for k in got if got[k] != pub[k]}
    if bad:
        raise SystemExit(f"build: cannot reproduce the August figures the site already "
                         f"publishes: {bad} (ours, theirs). A comparison against August "
                         f"would not be reading August the way August was read.")
    return {k: got[k] for k in got}


def build() -> dict:
    aug_raw, oct_raw, ref = _read(AUG), _read(OCT), _read(REF)
    A = {r["host"]: r for r in aug_raw["records"]}
    O = {r["host"]: r for r in oct_raw["records"]}
    if set(A) != set(O):
        raise SystemExit("build: the two surveys are not on the same host list")
    aug_ok = [r for r in A.values() if r["state"] == "ok"]
    oct_ok = [r for r in O.values() if r["state"] == "ok"]
    reproduced = verify_august(aug_ok)

    panel = [h for h in A if A[h]["state"] == "ok" and O[h]["state"] == "ok"]
    aug_only = [h for h in A if A[h]["state"] == "ok" and O[h]["state"] != "ok"]
    oct_only = [h for h in A if A[h]["state"] != "ok" and O[h]["state"] == "ok"]

    def count(group, fn):
        return sum(1 for r in group if fn(r))

    shares, change = {}, {}
    p_a = [A[h] for h in panel]
    p_o = [O[h] for h in panel]
    for name, fn in METRICS.items():
        gained = lost = both = 0
        for a, o in zip(p_a, p_o):
            x, y = fn(a), fn(o)
            gained += (not x) and y
            lost += x and (not y)
            both += x and y
        shares[name] = {
            "aug": count(aug_ok, fn), "oct": count(oct_ok, fn),
            "aug_panel": count(p_a, fn), "oct_panel": count(p_o, fn),
            "oct_current_parser": count(oct_ok, lambda r, fn=fn: fn(r, blocked_cur)),
        }
        change[name] = {"gained": gained, "lost": lost, "both": both,
                        "neither": len(panel) - gained - lost - both}

    # Any movement at all in which of the 40 probed crawlers a file blocks.
    def blockset(r):
        return frozenset(b for b, v in (r.get("access") or {}).items() if v is False)

    more = fewer = mixed = same = 0
    for a, o in zip(p_a, p_o):
        x, y = blockset(a), blockset(o)
        if x == y:
            same += 1
        elif x < y:
            more += 1
        elif y < x:
            fewer += 1
        else:
            mixed += 1
    movement = {"same": same, "more_blocked": more, "fewer_blocked": fewer, "mixed": mixed}

    # -- Cloudflare ---------------------------------------------------------
    #
    # Two kinds of evidence, kept apart because they are not equally strong:
    #
    #   marker     October only. The robots.txt text itself carries Cloudflare's
    #              own BEGIN marker comment. The collector read the text; the
    #              August survey kept only what the parser made of it.
    #   signature  Both months. A Content-signal line plus a Disallow for all
    #              eight crawlers in Cloudflare's documented block. A pattern in
    #              parsed data, which anyone could also write by hand.
    #
    # The August signature is backed by something stronger than the pattern: the
    # largest group of August files with the same signature is byte-for-byte the
    # same length with the same user-agent lines (see `august.largest_cluster`).
    eight = {a.lower() for a in CF_EIGHT}
    cf_rec = {h: O[h].get("cf") or {} for h in O if O[h]["state"] == "ok"}
    marker = {h for h, c in cf_rec.items() if c.get("marker")}

    def kind(c: dict) -> str:
        agents = set(c.get("agents", []))
        if agents == eight:
            return "eight"
        if agents == eight | {"cloudflarebrowserrenderingcrawler"}:
            return "eight_plus_rendering"
        return "longer" if agents > eight else "other"

    kinds = Counter(kind(cf_rec[h]) for h in marker)
    verbatim = {h for h in marker if cf_rec[h].get("exact")}
    policy_only = {h for h, c in cf_rec.items() if c.get("policy") and not c.get("marker")}
    sig_aug_all = {h for h, r in A.items() if r["state"] == "ok" and _sig8(r)}
    sig_oct_all = {h for h, r in O.items() if r["state"] == "ok" and _sig8(r)}
    pset = set(panel)
    sig_a, sig_o = sig_aug_all & pset, sig_oct_all & pset

    def largest_cluster(rows, key):
        c = Counter(key(r) for r in rows)
        if not c:
            return {"files": 0, "bytes": 0}
        k, n = c.most_common(1)[0]
        first = next(r for r in rows if key(r) == k)
        names = sorted({t for t in first["ua_tokens"] if t != "*"} - eight)
        return {"files": n, "bytes": first["robots_bytes"],
                "user_agent_lines": len(first["ua_tokens"]),
                "names_beyond_the_documented_eight": names}

    aug_cluster = largest_cluster([A[h] for h in sig_aug_all],
                                  lambda r: (r["robots_bytes"], tuple(r["ua_tokens"])))
    oct_cluster = largest_cluster([O[h] for h in marker],
                                  lambda r: r["robots_hash"])

    # Where the August signature went, for every host that showed it.
    left = {"kept": len(sig_a & sig_o), "gone_still_readable": len(sig_a - sig_o),
            "gone_unreachable": 0, "gone_refused": 0, "gone_no_robots_other": 0,
            "gone_oversize": 0}
    for h in sig_aug_all - pset:
        st = O[h]["state"]
        if st == "no_robots":
            st = "refused" if O[h].get("robots_status") in (401, 403, 406, 429, 503) \
                else "no_robots_other"
        left["gone_" + st] += 1
    left["gone_still_readable_no_marker"] = sum(
        1 for h in sig_a - sig_o if not (O[h].get("cf") or {}).get("marker"))
    appeared = {"gained_signature": len(sig_o - sig_a)}

    def effect(metric: str) -> dict:
        fn = METRICS[metric]
        gained = {h for h in panel if (not fn(A[h])) and fn(O[h])}
        lost = {h for h in panel if fn(A[h]) and (not fn(O[h]))}
        cf_on = marker | sig_oct_all
        return {
            "gained": len(gained), "lost": len(lost),
            "gained_with_marker": len(gained & marker),
            "gained_with_marker_or_signature": len(gained & cf_on),
            "gained_without": len(gained - cf_on),
            "lost_with_august_signature": len(lost & sig_aug_all),
            "lost_without": len(lost - sig_aug_all),
            "net": len(gained) - len(lost),
            "net_without_cloudflare": len(gained - cf_on) - len(lost - sig_aug_all),
        }

    cloudflare = {
        "august": {"signature_all": len(sig_aug_all), "signature_panel": len(sig_a),
                   "largest_cluster": aug_cluster,
                   "content_signal_all": count(aug_ok, lambda r: r.get("content_signal"))},
        "october": {"marker_all": len(marker), "kinds": dict(kinds),
                    "verbatim_documented": len(verbatim), "policy_comment_only": len(policy_only),
                    "signature_all": len(sig_oct_all), "signature_panel": len(sig_o),
                    "largest_cluster": oct_cluster,
                    "agents_in_block": dict(sorted(Counter(
                        len(cf_rec[h].get("agents", [])) for h in marker).items())),
                    "signals": dict(Counter(str(cf_rec[h].get("signal")) for h in marker)),
                    "content_signal_all": count(oct_ok, lambda r: r.get("content_signal"))},
        "signature_flow": {**left, **appeared},
        "effect": {m: effect(m) for m in ("training", "google_extended", "search", "any_of_nine")},
        "documented_agents": list(CF_EIGHT),
        "doc": CLOUDFLARE_DOC,
    }
    sizes = Counter(len(cf_rec[h].get("agents", [])) for h in marker)
    size, files = sizes.most_common(1)[0]
    cloudflare["october"]["modal_block"] = {"crawlers": size, "files": files}

    # -- refusals at the server, which a robots.txt reading cannot see ---------
    D = (401, 403, 406, 429, 503)
    refused_o = {h for h, r in O.items() if r.get("robots_status") in D}
    refused_a = {h for h, r in A.items() if r.get("robots_status") in D}
    ok_a = {h for h, r in A.items() if r["state"] == "ok"}
    to_refused = ok_a & refused_o
    refusal = {
        "aug": len(refused_a), "oct": len(refused_o),
        "readable_aug_now_refused": len(to_refused),
        "signature_hosts_now_refused": len(sig_aug_all & refused_o),
        "other_readable_now_refused": len((ok_a - sig_aug_all) & refused_o),
        "other_readable": len(ok_a - sig_aug_all),
        "refused_aug_now_readable": len(refused_a & {h for h, r in O.items() if r["state"] == "ok"}),
        "refused_403_oct": sum(1 for r in O.values() if r.get("robots_status") == 403),
        "refused_403_aug": sum(1 for r in A.values() if r.get("robots_status") == 403),
    }
    recheck = json.loads(RECHECK.read_text())

    # -- parser effect ------------------------------------------------------
    differs = [r for r in oct_ok if r.get("access_cur_diff")]
    parser = {
        "files_read_differently": len(differs),
        "training_aug_parser": shares["training"]["oct"],
        "training_current_parser": shares["training"]["oct_current_parser"],
        "search_aug_parser": shares["search"]["oct"],
        "search_current_parser": shares["search"]["oct_current_parser"],
        "any_aug_parser": shares["any_of_nine"]["oct"],
        "any_current_parser": shares["any_of_nine"]["oct_current_parser"],
        "files_with_bom": sum(1 for r in oct_ok if r.get("bom")),
    }

    # -- naming (not blocking) any token on today's reference list ----------
    known = {k.lower() for k in ref}
    for b in oct_raw["probe_bots"] + oct_raw["ext_bots"]:
        known.add(b.lower())

    def names_ai(r):
        return any(t in known for t in (r.get("ua_tokens") or []))

    naming = {"reference_tokens": len(known),
              "aug": count(aug_ok, names_ai), "oct": count(oct_ok, names_ai),
              "aug_panel": count(p_a, names_ai), "oct_panel": count(p_o, names_ai)}

    # -- oversize threshold sensitivity ------------------------------------
    sizes_ok = sorted(r["robots_bytes"] for r in oct_ok)
    oversize = [r["robots_bytes"] for r in O.values() if r["state"] == "oversize"]
    size = {"largest_readable_oct": sizes_ok[-1], "largest_readable_aug": max(
        r["robots_bytes"] for r in aug_ok),
        "oversize_oct": len(oversize), "smallest_oversize_oct": min(oversize) if oversize else None}

    llms_a = sum(1 for r in aug_ok if r.get("llms_present"))
    llms_o = sum(1 for r in oct_ok if r.get("llms_present"))

    def transitions():
        t = Counter((A[h]["state"], O[h]["state"]) for h in A)
        return {f"{a}>{o}": n for (a, o), n in sorted(t.items())}

    return {
        "meta": {
            "aug_collected": aug_raw["collected"], "oct_collected": oct_raw["collected"],
            "oct_finished": oct_raw.get("finished"), "oct_duration_s": oct_raw["duration_s"],
            "aug_duration_s": aug_raw["duration_s"],
            "population": oct_raw["population"],
            "hosts": len(A), "aug_input": _sha(AUG), "oct_input": _sha(OCT),
            "user_agent": oct_raw["method"]["user_agent"],
            "timeout_s": oct_raw["method"]["timeout_s"],
            "oversize_bytes": oct_raw["method"]["oversize_bytes"],
            "workers": 16,
            "probed_crawlers": len(oct_raw["probe_bots"]),
        },
        "aug": population(list(A.values())), "oct": population(list(O.values())),
        "state_transitions": transitions(),
        "panel": {"n": len(panel), "readable_aug_only": len(aug_only),
                  "readable_oct_only": len(oct_only)},
        "august_reproduced": reproduced,
        "shares": shares, "change": change, "movement": movement,
        "cloudflare": cloudflare, "refusal": refusal, "recheck": recheck, "parser": parser, "naming": naming, "size": size,
        "llms": {"present_aug": llms_a, "present_oct": llms_o},
        "crawlers": {"training": list(TRAINING), "search": list(SEARCH),
                     "shown": list(SHOWN), "cloudflare_eight": list(CF_EIGHT)},
    }


def csv_rows(d: dict) -> list[list]:
    """The download: aggregates only. No host appears in it."""
    n = d["panel"]["n"]
    ra, ro = d["aug"]["readable"], d["oct"]["readable"]
    rows = [["measure", "august_sites", "august_pct", "october_sites", "october_pct",
             "same_sites_august", "same_sites_october", "started_blocking",
             "stopped_blocking"],
            ["Sites in the list", d["aug"]["attempted"], "", d["oct"]["attempted"],
             "", "", "", "", ""],
            ["Sites with a readable robots.txt (the base of every percentage)",
             ra, "", ro, "", n, n, "", ""],
            ["Sites that refused our bot before any robots.txt rule applied",
             d["aug"]["refused"], "", d["oct"]["refused"], "", "", "", "", ""]]
    labels = [
        ("training", "Blocks at least one AI training crawler"),
        ("search", "Blocks at least one AI search crawler"),
        ("google_extended", "Blocks Google-Extended"),
        ("any_of_nine", "Blocks at least one of the nine AI crawlers"),
        ("training_only", "Blocks a training crawler and no search crawler"),
        *[(f"bot:{b}", f"Blocks {b}") for b in SHOWN if b != GOOGLE_EXTENDED],
    ]
    for key, label in labels:
        s, c = d["shares"][key], d["change"][key]
        rows.append([label, s["aug"], f"{100 * s['aug'] / ra:.2f}",
                     s["oct"], f"{100 * s['oct'] / ro:.2f}",
                     s["aug_panel"], s["oct_panel"], c["gained"], c["lost"]])
    cf = d["cloudflare"]
    rows += [
        ["Files with Cloudflare's BEGIN marker (October text)", "", "",
         cf["october"]["marker_all"], f"{100 * cf['october']['marker_all'] / ro:.2f}",
         "", "", "", ""],
        ["Files matching the August Cloudflare pattern (Content-signal plus all eight "
         "documented crawlers disallowed)", cf["august"]["signature_all"],
         f"{100 * cf['august']['signature_all'] / ra:.2f}", cf["october"]["signature_all"],
         f"{100 * cf['october']['signature_all'] / ro:.2f}", cf["august"]["signature_panel"],
         cf["october"]["signature_panel"], cf["signature_flow"]["gained_signature"],
         cf["signature_flow"]["gone_still_readable"]],
    ]
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
        print("ai-crawler-blocking derived data ok")
        return 0
    write(d)
    print(json.dumps({k: d[k] for k in ("panel", "movement", "parser")}, indent=1))
    for k in ("training", "search", "google_extended", "any_of_nine"):
        print(k, d["shares"][k], d["change"][k])
    print("cloudflare", json.dumps(d["cloudflare"], indent=1))
    print(f"wrote {OUT_JSON} and {OUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
