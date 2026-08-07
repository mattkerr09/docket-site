#!/usr/bin/env python3
"""Derive site/data/ai-directives-2026-08.json from the raw survey.

    python3 scripts/build_directives.py

Inputs live in data/ compressed, because the raw survey is 8 MB and the point
of publishing a measurement is that someone else can rerun the arithmetic:

    ai-directives-survey-2026-08.json.gz          one record per host
    ai-directives-llms-validation-2026-08.json.gz llms.txt + control fetches
    ai-robots-txt-reference-2026-08.json.gz       the ai.robots.txt token list

Nothing in the article computes anything. Every number on the page is read out
of the output of this file, so there is one place to check.
"""
from __future__ import annotations

import gzip
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "site" / "data" / "ai-directives-2026-08.json"


def _read(name: str):
    return json.loads(gzip.decompress((DATA / name).read_bytes()))


#: Substrings marking a user-agent token as *intended* to address an AI system.
#: Deliberately generous — the point is to catch what site owners meant, and
#: CONVENTIONAL below removes the ones that mean something else.
AI_INTENT = re.compile(
    r"gpt|openai|chatgpt|claude|anthropic|perplexity|gemini|bard|palm|"
    r"llm|\bai\b|-ai$|^ai-|ai-?bot|ai-?crawler|ai-?agent|bytespider|"
    r"meta-external|applebot-extended|cohere|mistral|deepseek|grok|xai|"
    r"youbot|diffbot|ccbot|omgili|img2dataset|timpi|webzio|awario|"
    r"scrapy|firecrawl|exabot|tavily|kagi|copilot|bingai|neeva|you\.com|"
    r"llama|huggingface|laion|common ?crawl|amazonbot|petalbot|notebooklm|"
    r"vertex|dataprovider|iaskspider|phind|writesonic|jasper|quillbot", re.I)

#: Tokens that trip AI_INTENT while addressing something else entirely.
#: Without this, "adsbot-google" and "petalbot" are counted as AI directives.
#: The awario* entries are the ones that mattered: they are the two most common
#: "unmatchable" tokens in the raw data, they are real crawlers for a social
#: listening product, and leaving them in would have inflated the headline by
#: nearly 300 sites on a regex over-reach of ours.
CONVENTIONAL = {
    "*", "petalbot", "applebot", "adsbot", "adsbot-google",
    "adsbot-google-mobile", "adsbot-google-mobile-apps", "exabot", "gigabot",
    "bingbot/2.0", "mail.ru_bot", "grapeshot", "grapeshotcrawler", "scrapy",
    "cliqzbot", "qwantify", "coccocbot", "coccocbot-web",
    "awariosmartbot", "awariorssbot", "awariobot",
}

#: Real, currently-documented crawler tokens that the community ai.robots.txt
#: list does not contain. Naming one of these is correct behaviour, so they must
#: not be counted as dead — the reference list being stale is not the site
#: owner's mistake. Each was read on the vendor's own page on 2026-08-07:
#:
#:   kagibot         kagi.com/bot
#:   webzio          webz.io/bot.html  (the "Webzio Duo" that replaced Omgilibot)
#:   mistralai-*     docs.mistral.ai/robots/
#:   meta-*          developers.facebook.com/docs/sharing/webmasters/web-crawlers/
LIST_GAP = {
    "kagibot", "webzio", "mistralai-index", "mistralai-training",
    "meta-externalads", "meta-webindexer", "coherebot",
}

#: Documented once by the vendor, since superseded. A rule under one of these
#: headings applies to nobody, because the crawler now sends a different name.
#:
#: Read from site/_data/retired-crawlers.csv, exported from the app's
#: `RETIRED_AI_TOKENS`. It used to be a dict literal here, and the app and the
#: site drifted: this file claimed `cohere-ai` was replaced by
#: `cohere-training-data-crawler` — a name nobody had read anywhere — and
#: published it, while the app deliberately refused to flag `cohere-ai` at all
#: for exactly that lack of a source. Two tables, two answers, and the wrong
#: one was the public one. There is one table now.
def _retired() -> dict:
    import csv
    path = ROOT / "site" / "_data" / "retired-crawlers.csv"
    with path.open() as fh:
        rows = list(csv.DictReader(fh))
    out = {}
    for r in rows:
        token = r["token"].strip().lower()
        assert token not in out, f"duplicate retired token: {token}"
        out[token] = (r["owner"], r["replaced_by"])
    return out


RETIRED = _retired()

#: The crawlers that decide whether a site can appear in an AI answer, and the
#: ones that only decide whether it becomes training data. Keeping these apart
#: is the whole point; the survey exists because most robots.txt files do not.
#: Mirrors `RobotsMatcher::ExtractUserAgent` in Google's open-source robots.txt
#: parser (google/robotstxt, read 2026-08-07):
#:
#:     // Allowed characters in user-agent are [a-zA-Z_-].
#:     while (absl::ascii_isalpha(*end) || *end == '-' || *end == '_') ++end;
#:
#: and `HandleUserAgent` applies it to the value written in the FILE, not only
#: to the crawler's own string. So a written token is silently cut short, and
#: the group addresses whatever survives. This one line is the difference
#: between `ChatGPT-User/2.0` being broken and being fine — it truncates to
#: `ChatGPT-User` and works. An earlier version of this page said otherwise.
_TOKEN_CHARS = re.compile(r"[A-Za-z_-]*")


def truncate_user_agent(token: str) -> str:
    return _TOKEN_CHARS.match((token or "").strip()).group(0)


CITATION = ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot")
TRAINING = ("GPTBot", "ClaudeBot", "Applebot-Extended", "Bytespider",
            "meta-externalagent", "CCBot")

RANK_BANDS = ((1, 1000), (1001, 3000), (3001, 6000), (6001, 9000), (9001, 10000))
DENIED_STATUS = (401, 403, 406, 429, 503)


#: Openings that prove the body at /llms.txt is some other file. A control
#: fetch catches servers that answer 200 to everything; it does not catch a
#: server that answers 200 with a sitemap, its robots.txt, or a JSON blob —
#: and several do. Anything undecodable is excluded too: five hosts returned
#: gzip bytes under `text/plain`, which may well be a real llms.txt, but we
#: could not read it and will not count what we did not see.
_NOT_LLMS = (
    "<?xml", "<!--", "<!doctype", "<html", "{", "[",
    "user-agent:", "sitemap:",
)
#: gzip magic. The survey decoded bodies as text, so the second magic byte
#: (0x8b) arrives as U+FFFD and only the leading 0x1f is reliable.
_BINARY = "\x1f"


def _is_llms_body(head: str) -> bool:
    h = head.lstrip("﻿ \t\r\n").lower()
    return bool(h) and not h.startswith(_NOT_LLMS) and not h.startswith(_BINARY)


def build() -> Path:
    survey = _read("ai-directives-survey-2026-08.json.gz")
    validation = _read("ai-directives-llms-validation-2026-08.json.gz")
    known = {k.strip().lower()
             for k in _read("ai-robots-txt-reference-2026-08.json.gz")}

    recs = survey["records"]
    ok = [r for r in recs if r.get("state") == "ok"]
    n = len(ok)

    # A 200 for /llms.txt only counts where the control path — which cannot
    # exist — did not also return 200. Without that second fetch, every
    # catch-all handler on the web reports an llms.txt it does not have.
    soft404 = sum(1 for v in validation if v.get("ctrl_status") == 200)
    passed = [v for v in validation
              if v.get("llms_status") == 200 and v.get("ctrl_status") != 200]
    wrong_kind = [v for v in passed if not _is_llms_body(v.get("llms_head") or "")]
    confirmed = {v["host"] for v in passed if v not in wrong_kind}

    def ai_tokens(r):
        toks = {t.strip().lower() for t in (r.get("ua_tokens") or [])}
        return sorted(t for t in toks
                      if t and t not in CONVENTIONAL and AI_INTENT.search(t))

    def blocked(r, bot):
        return (r.get("access") or {}).get(bot) is False

    # Every token anyone documents: the community list plus the six vendor
    # tokens it is missing. A truncation that lands on one of these is fine.
    documented = known | LIST_GAP

    def is_truncated(tok):
        """Provably broken: what the parser keeps is not a crawler name."""
        kept = truncate_user_agent(tok).lower()
        return kept != tok.lower() and kept not in documented

    hosts, unk_c, ret_c, tr_c = [], Counter(), Counter(), Counter()
    sites_ai = sites_unk = sites_ret = sites_dead = sites_tr = sites_prov = 0
    for r in ok:
        ai = ai_tokens(r)
        ret = [t for t in ai if t in RETIRED]
        tr = [t for t in ai if t not in RETIRED and is_truncated(t)]
        # Not in the community list and not provably broken. Reported as its own
        # tier because we cannot show these do nothing — only that nobody has
        # documented them where site owners look.
        unk = [t for t in ai if t not in known and t not in LIST_GAP]
        if ai:
            sites_ai += 1
            if unk:
                sites_unk += 1
                unk_c.update(unk)
            if ret:
                sites_ret += 1
                ret_c.update(ret)
            if tr:
                sites_tr += 1
                tr_c.update(tr)
            if unk or ret:
                sites_dead += 1
            # What Scout's shipped check flags: only what we can prove.
            if ret or tr:
                sites_prov += 1
        hosts.append({
            "h": r["host"], "r": r["rank"], "ai": ai,
            "dead": sorted(set(unk) | set(ret)),
            "blk": sorted(b for b in CITATION + TRAINING if blocked(r, b)),
            "llms": r["host"] in confirmed,
            "probed": bool(r.get("llms_allowed_for_us")),
            "edge_denied_llms": r.get("llms_status") in DENIED_STATUS,
            "sm": bool(r.get("has_sitemap")),
            "cs": bool(r.get("content_signal")),
        })

    any_cit = [h for h in hosts if any(b in CITATION for b in h["blk"])]
    any_tr = [h for h in hosts if any(b in TRAINING for b in h["blk"])]
    any_ai = [h for h in hosts if h["blk"]]
    tr_only = [h for h in any_ai if not any(b in CITATION for b in h["blk"])]

    # The llms.txt probe only ran where robots.txt permitted our own user-agent.
    # Hosts that denied us were never tested, and they are exactly the hosts
    # most likely to block crawlers — comparing against them would build the
    # association we are testing for into the sampling.
    probed = [h for h in hosts if h["probed"]]
    llms = [h for h in probed if h["llms"]]
    no_llms = [h for h in probed if not h["llms"]]

    def rate(group, bots):
        if not group:
            return 0.0
        return round(100 * sum(1 for h in group
                               if any(b in bots for b in h["blk"])) / len(group), 2)

    def risk_ratio(exposed, control, bots):
        """Katz log-method risk ratio with a 95% interval.

        Reported with the interval because a ratio from 9 events in one arm
        looks far more precise than it is.
        """
        a = sum(1 for h in exposed if any(b in bots for b in h["blk"]))
        b = sum(1 for h in control if any(b in bots for b in h["blk"]))
        if not a or not b:
            return None
        rr = (a / len(exposed)) / (b / len(control))
        se = math.sqrt(1 / a - 1 / len(exposed) + 1 / b - 1 / len(control))
        return {"rr": round(rr, 3), "events_exposed": a, "events_control": b,
                "lo": round(rr * math.exp(-1.96 * se), 2),
                "hi": round(rr * math.exp(1.96 * se), 2)}

    def share(group, key):
        return round(100 * sum(1 for h in group if h[key]) / len(group), 2)

    summary = {
        "attempted": len(recs),
        "parseable_robots": n,
        "edge_denied": sum(1 for r in recs
                           if r.get("robots_status") in DENIED_STATUS),
        "sites_with_ai_directive": sites_ai,
        "sites_with_unmatchable": sites_unk,
        "sites_with_retired": sites_ret,
        "sites_with_dead_directive": sites_dead,
        "sites_with_truncated": sites_tr,
        "sites_provably_broken": sites_prov,
        "pct_provably_broken_of_ai": round(100 * sites_prov / sites_ai, 1),
        "pct_ai_directive": round(100 * sites_ai / n, 1),
        "pct_dead_of_ai": round(100 * sites_dead / sites_ai, 1),
        "blocks_citation": len(any_cit),
        "blocks_training": len(any_tr),
        "blocks_any": len(any_ai),
        "training_only": len(tr_only),
        "pct_training_only": round(100 * len(tr_only) / len(any_ai), 1),
        "llms_candidates": len(validation),
        "llms_soft404": soft404,
        "llms_wrong_kind": len(wrong_kind),
        "llms_false_positive": soft404 + len(wrong_kind),
        "pct_llms_false_positive": round(
            100 * (soft404 + len(wrong_kind)) / len(validation), 1),
        "llms_confirmed": len(llms),
        "pct_llms_soft404": round(100 * soft404 / len(validation), 1),
        "pct_llms_adoption": round(100 * len(llms) / n, 2),
        "llms_group_n": len(llms),
        "no_llms_group_n": len(no_llms),
        "content_signal": sum(1 for h in hosts if h["cs"]),
        "probed_for_llms": len(probed),
        "llms_edge_denied": sum(1 for h in probed if h["edge_denied_llms"]),
        "pct_llms_edge_denied": share(probed, "edge_denied_llms"),
        "sitemap_with_llms": share(llms, "sm"),
        "sitemap_without_llms": share(no_llms, "sm"),
        "cit_rate_llms": rate(llms, CITATION),
        "cit_rate_no_llms": rate(no_llms, CITATION),
        "train_rate_llms": rate(llms, TRAINING),
        "train_rate_no_llms": rate(no_llms, TRAINING),
        # Pair asymmetry, so the article stops typing these by hand.
        "oai_search_blocked": sum(1 for h in hosts if "OAI-SearchBot" in h["blk"]),
        "oai_search_and_gptbot": sum(1 for h in hosts if "OAI-SearchBot" in h["blk"]
                                     and "GPTBot" in h["blk"]),
        "claude_search_blocked": sum(1 for h in hosts if "Claude-SearchBot" in h["blk"]),
        "claude_search_and_claudebot": sum(1 for h in hosts
                                           if "Claude-SearchBot" in h["blk"]
                                           and "ClaudeBot" in h["blk"]),
        # Tokens the parser truncates to a documented name, i.e. the ones an
        # earlier version of this check would have flagged wrongly.
        "benign_truncations": sum(
            1 for h in hosts
            if any(truncate_user_agent(t).lower() != t.lower()
                   and truncate_user_agent(t).lower() in (known | LIST_GAP)
                   for t in h["ai"])),
        "rr_citation_llms": risk_ratio(llms, no_llms, CITATION),
        "rr_training_llms": risk_ratio(llms, no_llms, TRAINING),
    }

    bands = []
    for lo, hi in RANK_BANDS:
        grp = [h for h in hosts if lo <= h["r"] <= hi]
        if grp:
            got = sum(1 for h in grp if h["llms"])
            bands.append({"from": lo, "to": hi, "n": len(grp), "llms": got,
                          "pct": round(100 * got / len(grp), 2)})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "collected": survey["collected"],
        "population": survey["population"],
        "duration_s": survey["duration_s"],
        "method": (
            "One request for /robots.txt per host, parsed with Scout's own "
            "RobotsTxt class. A second request for /llms.txt only where the "
            "robots.txt we had just read permitted our own user-agent, plus a "
            "control request for a path that cannot exist, to catch handlers "
            "that answer 200 to anything. Self-identifying user-agent with a "
            "contact address, 8s timeout, no retries. No vendor crawler was "
            "impersonated."),
        "reference_list": (
            "ai.robots.txt (https://github.com/ai-robots-txt/ai.robots.txt), "
            f"{len(known)} tokens, plus {len(LIST_GAP)} vendor-documented "
            "tokens it is missing"),
        "list_gap": sorted(LIST_GAP),
        "summary": summary,
        "llms_by_rank": bands,
        "retired_tokens": {t: {"count": c, "vendor": RETIRED[t][0],
                               "replaced_by": RETIRED[t][1]}
                           for t, c in ret_c.most_common()},
        "unmatchable_tokens": dict(unk_c.most_common(60)),
        "truncated_tokens": {t: {"count": c, "kept": truncate_user_agent(t)}
                             for t, c in tr_c.most_common(40)},
        "hosts": hosts,
    }, separators=(",", ":")))
    return OUT


if __name__ == "__main__":
    p = build()
    d = json.loads(p.read_text())
    for k, v in d["summary"].items():
        print(f"{k:26s} {v}")
    print(f"\nwrote {p}  {p.stat().st_size / 1024:.0f} KB")
