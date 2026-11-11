#!/usr/bin/env python3
"""Offline, aggregate-only crawler pages from the stored October readings.

Naming is an exact, case-insensitive match of the stored user-agent tokens,
with reference aliases merged. Blocking uses access for probes and the stored
ext_blocked_by_name list for other tokens. No robots.txt is parsed here.
"""
from __future__ import annotations

import gzip
import json
import re
import sys
from collections import defaultdict
from functools import lru_cache
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F
from render import render, with_next_step

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "ai-crawler-pages-2026-10.json"
REFERENCE = "https://github.com/ai-robots-txt/ai.robots.txt"
EXISTING = {
    "claudebot": "/learn/what-is-claudebot/",
    "claude-searchbot": "/learn/claude-search-crawlers/",
    "claude-user": "/learn/claude-search-crawlers/",
}


@lru_cache(maxsize=None)
def token_key(token: str) -> str:
    """Only case, trailing versions, and the explicitly identified aliases."""
    key = re.sub(r"(?:/|\s)\d+(?:\.\d+)*$", "", token.casefold())
    return {"terra cotta": "terracotta", "panscient.com": "panscient",
            "quillbot.com": "quillbot"}.get(key, key)


def reference_words(value: str) -> str:
    """Quote reference link labels and retain bare operator identifiers."""
    value = re.sub(r"\[([^]]+)\]\([^\s]+\)", r"\1", value)
    value = re.sub(r"More info can be found at https?://\S+", "", value)
    return value.replace("\u2014", ", ").replace("\u2013", "-").strip()


def _share(count: int, base: int) -> float:
    return round(100 * count / base, 1) if base else 0.0


def _operator_group(operator: str) -> str | None:
    """Group explicit operator wording variants without filling unknown owners."""
    if operator.startswith(("Unclear", "Unknown")):
        return None
    name = re.split(r", | that | to download ", operator, maxsplit=1)[0].casefold()
    return {"mistral ai": "mistral", "meta/facebook": "meta",
            "the chinese company huawei": "huawei"}.get(name, name)


def _counts(records: list[dict], key: str, probes: list[str]) -> dict:
    named = blocked = named_blocked = 0
    for record in records:
        has_name = any(token_key(t) == key for t in record["ua_tokens"])
        is_blocked = (any(record["access"][p] is False for p in probes) if probes else
                      any(token_key(t) == key for t in record["ext_blocked_by_name"]))
        named += has_name
        blocked += is_blocked
        named_blocked += has_name and is_blocked
    base = len(records)
    return {"readable": base, "named": named, "named_pct": _share(named, base),
            "blocked": blocked, "blocked_pct": _share(blocked, base),
            "named_blocked": named_blocked, "named_unblocked": named - named_blocked,
            "blocked_unnamed": blocked - named_blocked,
            "unnamed": base - named, "unblocked": base - blocked}


def _probe_changes(august: dict, october: dict, probes: list[str]) -> dict:
    """Use the published method: saved August-parser access, on a fixed panel.

    October's records already contain the 308 reread replacements. The `was`
    records in its reread log are the superseded readings, not extra samples.
    """
    aug = {r["host"]: r for r in august["records"]}
    oct_ = {r["host"]: r for r in october["records"]}
    if aug.keys() != oct_.keys():
        raise ValueError("August and October must contain the same hosts")
    aug_ok = [r for r in aug.values() if r["state"] == "ok"]
    oct_ok = [r for r in oct_.values() if r["state"] == "ok"]
    panel = [(a, oct_[host]) for host, a in aug.items()
             if a["state"] == "ok" and oct_[host]["state"] == "ok"]
    result = {}
    for bot in probes:
        def blocked(record):
            return (record.get("access") or {}).get(bot) is False

        gained = sum(not blocked(a) and blocked(o) for a, o in panel)
        lost = sum(blocked(a) and not blocked(o) for a, o in panel)
        both = sum(blocked(a) and blocked(o) for a, o in panel)
        result["bot:" + bot] = {
            "gained": gained, "lost": lost, "both": both,
            "neither": len(panel) - gained - lost - both,
            "shares": {
                "aug": sum(blocked(r) for r in aug_ok),
                "oct": sum(blocked(r) for r in oct_ok),
                "aug_panel": sum(blocked(a) for a, _ in panel),
                "oct_panel": sum(blocked(o) for _, o in panel),
                "oct_current_parser": sum(
                    (r.get("access_cur_diff") or {}).get(bot, (r.get("access") or {}).get(bot)) is False
                    for r in oct_ok),
            },
            "panel": len(panel), "aug_readable": len(aug_ok),
        }
    return result


def _published_changes_match(changes: dict, blocking: dict) -> bool:
    """Do not fill any missing comparison unless every published bot matches."""
    for metric, expected in blocking["change"].items():
        if not metric.startswith("bot:"):
            continue
        got = changes.get(metric, {})
        if (any(got.get(field) != value for field, value in expected.items())
                or got.get("shares") != blocking["shares"][metric]
                or got.get("panel") != blocking["panel"]["n"]
                or got.get("aug_readable") != blocking["aug"]["readable"]):
            return False
    return True


def derive_data() -> dict:
    """Rebuild eligible crawler rows deterministically from saved readings."""
    with gzip.open(ROOT / "data" / "ai-directives-survey-2026-10.json.gz", "rt") as handle:
        survey = json.load(handle)
    with gzip.open(ROOT / "data" / "ai-robots-txt-reference-2026-10.json.gz", "rt") as handle:
        reference = json.load(handle)
    blocking = json.loads((ROOT / "data" / "ai-crawler-blocking-2026-10.json").read_text())
    with gzip.open(ROOT / "data" / "ai-directives-survey-2026-08.json.gz", "rt") as handle:
        august = json.load(handle)
    changes = _probe_changes(august, survey, survey["probe_bots"])
    changes_verified = _published_changes_match(changes, blocking)
    groups = defaultdict(list)
    for token in sorted(reference, key=lambda t: (t.casefold(), t)):
        groups[token_key(token)].append(token)
    readable = [r for r in survey["records"] if r["state"] == "ok"]
    top_limit = 1000
    top = [r for r in readable if r["rank"] <= top_limit]
    method = {
        "population": len(survey["records"]), "readable": len(readable),
        "top_limit": top_limit, "top_readable": len(top),
        "collected": survey["collected"], "month": F.blk_month("oct"),
        "collected_day": F.blk_date("oct"),
        "reread_days": sorted({r["at"][:10] for r in survey.get("reread", [])}),
        "parser": survey["method"]["parser"],
        "timeout_s": int(survey["method"]["timeout_s"]),
        "oversize_bytes": survey["method"]["oversize_bytes"],
        "minimum_named": 10,
        "probe_count": len(survey["probe_bots"]),
        "august_changes_verified": changes_verified,
    }
    cloudflare = {token_key(t) for t in survey["method"]["cloudflare_agents"]}
    rows = []
    for key, spellings in sorted(groups.items()):
        probes = [p for p in survey["probe_bots"] if token_key(p) == key]
        # Prefer the unversioned reference spelling and a documented operator.
        canonical = min(spellings, key=lambda t: (bool(re.search(r"(?:/|\s)\d", t)), len(t), t))
        entries = [{"token": t, **{field: reference_words(reference[t][field])
                    for field in ("operator", "function", "frequency", "respect", "description")}}
                   for t in spellings]
        primary = next((e for e in entries if "Unclear at this time" not in e["operator"]), entries[0])
        row = {"token": canonical, "slug": re.sub(r"[^a-z0-9]+", "-", key).strip("-"),
               "spellings": spellings, "operator": primary["operator"],
               "operator_group": _operator_group(primary["operator"]),
               "function": primary["function"], "frequency": primary["frequency"],
               "respect": primary["respect"], "description": primary["description"], "reference_entries": entries,
               "cloudflare_managed": key in cloudflare, "probe_tokens": probes,
               "overall": _counts(readable, key, probes), "top": _counts(top, key, probes),
               "existing_page": EXISTING.get(key), "method": method}
        row["rest"] = {
            name: row["overall"][name] - row["top"][name]
            for name in ("readable", "named", "blocked")}
        for name in ("named", "blocked"):
            row["rest"][name + "_pct"] = _share(row["rest"][name], row["rest"]["readable"])
        row["change"] = None
        if probes:
            metric = "bot:" + probes[0]
            if metric in blocking["change"]:
                row["change"] = {**blocking["change"][metric],
                                 "shares": blocking["shares"][metric],
                                 "panel": blocking["panel"]["n"],
                                 "aug_readable": blocking["aug"]["readable"],
                                 "source": "ai-crawler-blocking-2026-10.json"}
            elif changes_verified:
                row["change"] = {**changes[metric],
                                 "source": "ai-directives-survey-2026-08.json.gz + ai-directives-survey-2026-10.json.gz"}
            if row["change"] is not None:
                row["change"]["net"] = row["change"]["gained"] - row["change"]["lost"]
        row["publish"] = row["overall"]["named"] >= method["minimum_named"] and not row["existing_page"]
        rows.append(row)
    for row in rows:
        row["shared_description_count"] = sum(other is not row and other["description"] == row["description"]
                                               for other in rows)
    rows = [r for r in rows if r["overall"]["named"] >= method["minimum_named"]]
    eligible = sorted(rows, key=lambda r: (-r["overall"]["named"], r["token"].casefold()))
    for position, row in enumerate(eligible, 1):
        row["naming_position"] = position
        row["eligible_count"] = len(eligible)
        # A measured neighbour gives each row context without publishing hosts.
        peer = eligible[position if position < len(eligible) else position - 2]
        row["comparison"] = {"token": peer["token"], "url": _url(peer),
                             "relation": "next" if position < len(eligible) else "previous",
                             "named": peer["overall"]["named"],
                             "blocked": peer["overall"]["blocked"],
                             "blocked_pct": peer["overall"]["blocked_pct"]}
    return {"method": method, "reference_url": REFERENCE, "rows": rows}


def write_data() -> dict:
    data = derive_data()
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    F.ai_crawler_pages.cache_clear()
    return data


def _url(row: dict) -> str:
    return row["existing_page"] or f"/ai-crawlers/{row['slug']}/"


def _n(value: int) -> str:
    return f"{value:,}"


def _ordinal(value: int) -> str:
    suffix = 'th' if 11 <= value % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    return f'{value}{suffix}'


def _files(value: int) -> str:
    return f"{_n(value)} file" + ("" if value == 1 else "s")


def _p(value: float) -> str:
    return f"{value:.1f}%"


def _table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f'<th scope="col">{h}</th>' for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in rows)
    return f'<div class="wrap-tbl"><table class="cmp"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _role(row: dict) -> str:
    purpose = row["function"].lower()
    if row["respect"] == "No":
        return "ignores"
    if "prompt" in row["frequency"].lower() or "user-initiated" in purpose:
        return "user"
    if "search" in purpose or "index" in purpose:
        return "search"
    if "train" in purpose:
        return "training"
    if "assistant" in purpose:
        return "assistant"
    return "other"


def _opening(row: dict) -> str:
    token, operator = escape(row["token"]), escape(row["operator"])
    owner = ("its operator is unclear in the community reference" if "Unclear at this time" in row["operator"]
             else f"the community reference lists its operator as {operator}")
    owner_sentence = owner[0].upper() + owner[1:]
    count, pct = _n(row["overall"]["blocked"]), _p(row["overall"]["blocked_pct"])
    month = row["method"]["month"]
    role = _role(row)
    if role == "ignores":
        return (f'{token} has {count} sites asking it to stay out in {month}, or {pct} of the files we could read. '
                f'However, the reference says it does not obey robots.txt, and {owner}.')
    if row["overall"]["blocked_pct"] > 50:
        return f'Most readable files block {token} in {month}, at {count} sites or {pct}. {owner_sentence}.'
    if role == "user":
        return (f'{token} fetches pages in response to users, according to the reference, and {owner}. '
                f'In {month}, {count} sites block it, or {pct} of readable robots.txt files.')
    if role == "training":
        return (f'{token} collects content for model training, and {owner}. '
                f'Our {month} survey found {count} sites blocking it, or {pct} of the files we could read.')
    if role == "search":
        return (f'{token} is listed as a search crawler, and {owner}. '
                f'In {month}, {count} sites block it, a {pct} share of readable files.')
    if row["overall"]["blocked_pct"] < 1 and row["overall"]["blocked"] > row["overall"]["named"]:
        return (f'{token} has {count} recorded blocks in {month}, or {pct}, '
                f'and {_n(row["overall"]["named"])} files naming it. {owner_sentence}.')
    if row["overall"]["blocked_pct"] < 1:
        return (f'Few readable files block {token} in {month}, at {count} sites or {pct}. '
                f'{owner_sentence}.')
    return (f'{token} is blocked by {count} sites in the {month} survey, or {pct} of readable files. '
            f'{owner_sentence}.')


def _measurement(row: dict) -> str:
    token = escape(row["token"])
    all_, top, rest, method = (row[k] for k in ("overall", "top", "rest", "method"))
    # Use several ways to read the figures, including for adjacent tied counts.
    readings = [
        (f'Of {_n(all_["readable"])} robots.txt files we could read, {_n(all_["blocked"])} block '
         f'the whole site with <code>Disallow: /</code>, or {_p(all_["blocked_pct"])}. '
         f'Another way to read the sample is by name, with {_n(all_["named"])} files naming it in a '
         f'<code>User-agent</code> line, or {_p(all_["named_pct"])}. '
         f'The {_n(all_["unblocked"])} remaining files have no recorded whole-site block.'),
        (f'A <code>User-agent</code> line names it in {_n(all_["named"])} files, '
         f'{_p(all_["named_pct"])} of {_n(all_["readable"])} readable files. '
         f'Whole-site bans, written <code>Disallow: /</code>, total {_n(all_["blocked"])}, '
         f'or {_p(all_["blocked_pct"])}. That leaves {_n(all_["unblocked"])} without a recorded ban.'),
        (f'The {_n(all_["blocked"])} files blocking the whole site account for {_p(all_["blocked_pct"])} '
         f'of {_n(all_["readable"])} readable robots.txt files. '
         f'We found its name in {_n(all_["named"])} <code>User-agent</code> lists, a {_p(all_["named_pct"])} share. '
         f'Without a whole-site <code>Disallow: /</code> block, {_n(all_["unblocked"])} files remain.'),
        (f'Instructions to stay out of the whole site appear in {_files(all_["blocked"])}, '
         f'or {_p(all_["blocked_pct"])} of {_n(all_["readable"])} readable files. '
         f'We counted {_n(all_["named"])} with its name in a <code>User-agent</code> line, '
         f'a {_p(all_["named_pct"])} share. Another {_n(all_["unblocked"])} lack a recorded <code>Disallow: /</code> ban.'),
        (f'The name occurs in {_n(all_["named"])} out of {_n(all_["readable"])} readable files, '
         f'a {_p(all_["named_pct"])} share. Across the full sample, the whole-site <code>Disallow: /</code> '
         f'block count is {_n(all_["blocked"])}, or {_p(all_["blocked_pct"])}. '
         f'Files without that ban number {_n(all_["unblocked"])}.'),
        (f'Within {_n(all_["readable"])} readable robots.txt files, the name appears in {_n(all_["named"])}, '
         f'or {_p(all_["named_pct"])}. Instructions blocking every path, <code>Disallow: /</code>, '
         f'appear in {_n(all_["blocked"])}, a {_p(all_["blocked_pct"])} share. '
         f'No whole-site ban is recorded for {_n(all_["unblocked"])} files.'),
        (f'Our readable sample has {_n(all_["blocked"])} whole-site blocks, {_p(all_["blocked_pct"])} '
         f'of {_n(all_["readable"])} files, with <code>Disallow: /</code> as the instruction. '
         f'Of that full sample, {_n(all_["named"])} name this crawler, or {_p(all_["named_pct"])}. '
         f'The count without a whole-site block is {_n(all_["unblocked"])}.'),
    ]
    # Lead with the larger count so naming and blocking stay distinct.
    if all_["named"] > all_["blocked"]:
        readings = [readings[1], readings[4], readings[5]]
    elif all_["blocked"] > all_["named"]:
        readings = [readings[0], readings[2], readings[3], readings[6]]
    scale = readings[(row["naming_position"] + all_["named_unblocked"]) % len(readings)]
    if not all_["blocked"]:
        zero_readings = [
            (f'No whole-site <code>Disallow: /</code> ban was recorded for it among {_n(all_["readable"])} readable files. '
             f'<code>User-agent</code> lines name it in {_n(all_["named"])}, or {_p(all_["named_pct"])}. '
             f'The total without a recorded ban is {_n(all_["unblocked"])}.'),
            (f'A <code>User-agent</code> line mentions it in {_n(all_["named"])} of {_n(all_["readable"])} files, '
             f'or {_p(all_["named_pct"])}. The whole-site <code>Disallow: /</code> block count is {_n(all_["blocked"])}. '
             f'All {_n(all_["unblocked"])} files are therefore without a ban in this measure.'),
            (f'We have {_n(all_["readable"])} readable files for this entry, {_n(all_["named"])} of them naming it, '
             f'a {_p(all_["named_pct"])} share. Whole-site blocks written <code>Disallow: /</code> total {_n(all_["blocked"])}. '
             f'That puts the count without a recorded ban at {_n(all_["unblocked"])}.'),
        ]
        scale = zero_readings[all_["named"] % len(zero_readings)]
    if all_["blocked_pct"] > 50:
        scale += ' These blocks cover a majority of the readable files.'
    if top["blocked_pct"] > all_["blocked_pct"]:
        rank = f'Blocking is more common among the leading sites, at {_p(top["blocked_pct"])}.'
    elif top["blocked_pct"] < all_["blocked_pct"]:
        rank = f'The leading sites have a lower block share, {_p(top["blocked_pct"])}.'
    else:
        rank = f'At {_p(top["blocked_pct"])}, the leading block share equals the rounded overall share.'
    samples = [
        (f'Tranco’s top {_n(method["top_limit"])} sites yielded {_n(top["readable"])} readable files, including '
         f'{_files(top["named"])} with its name, or {_p(top["named_pct"])}, and {_files(top["blocked"])} blocking it. '
         f'{rank} Outside those ranks, {_n(rest["blocked"])} of {_n(rest["readable"])} files block it, '
         f'or {_p(rest["blocked_pct"])}.'),
        (f'Among {_n(top["readable"])} readable files from the top {_n(method["top_limit"])} sites, '
         f'we found {_files(top["named"])} naming it, a {_p(top["named_pct"])} share, '
         f'with {_files(top["blocked"])} blocking the whole site. {rank} '
         f'Outside this group, {_n(rest["readable"])} files contribute {_n(rest["blocked"])} blocks, '
         f'or {_p(rest["blocked_pct"])}.'),
        (f'For the top {_n(method["top_limit"])} ranks, its name appears in {_files(top["named"])} '
         f'out of {_n(top["readable"])}, or {_p(top["named_pct"])}. Whole-site blocks total {_n(top["blocked"])}. '
         f'{rank} Lower in the ranking, blocking reaches {_n(rest["blocked"])} files '
         f'out of {_n(rest["readable"])}, a {_p(rest["blocked_pct"])} share.'),
        (f'Across Tranco’s top {_n(method["top_limit"])} ranks, there were {_n(top["readable"])} readable files. '
         f'Among them, {_files(top["named"])} carry the name, or {_p(top["named_pct"])}, '
         f'with {_files(top["blocked"])} blocking the whole site. {rank} '
         f'Farther down, {_n(rest["blocked"])} of {_n(rest["readable"])} files record a block, '
         f'{_p(rest["blocked_pct"])} of that group.'),
        (f'From the highest {_n(method["top_limit"])} ranks, {_n(top["readable"])} files could be read. '
         f'Its naming count is {_n(top["named"])}, or {_p(top["named_pct"])}, '
         f'and the block count is {_n(top["blocked"])}. {rank} '
         f'Compare {_n(rest["blocked"])} blocks among the {_n(rest["readable"])} readable files below those ranks, '
         f'or {_p(rest["blocked_pct"])}.'),
        (f'At the top {_n(method["top_limit"])} ranks, we could read {_n(top["readable"])} files. '
         f'Naming covers {_n(top["named"])}, a {_p(top["named_pct"])} share, '
         f'and blocking covers {_n(top["blocked"])}. {rank} '
         f'Elsewhere, {_n(rest["readable"])} readable files give {_n(rest["blocked"])} blocks, '
         f'or {_p(rest["blocked_pct"])}.'),
        (f'Breaking out the leading {_n(method["top_limit"])} sites gives {_n(top["readable"])} readable files, '
         f'with {_n(top["named"])} naming the crawler, or {_p(top["named_pct"])}. '
         f'Whole-site blocking appears in {_n(top["blocked"])} of them. {rank} '
         f'Beyond those ranks, {_n(rest["readable"])} files have a blocking total of {_n(rest["blocked"])}, '
         f'{_p(rest["blocked_pct"])} of that sample.'),
    ]
    sample = samples[(row["naming_position"] + top["named"]) % len(samples)]
    if not all_["blocked"]:
        zero_samples = [
            (f'For leading ranks, naming still appears in {_files(top["named"])}, '
             f'{_p(top["named_pct"])} of {_n(top["readable"])} readable files from Tranco’s top {_n(method["top_limit"])}. '
             f'The remaining {_n(rest["named"])} naming files come from {_n(rest["readable"])} readable lower-ranked files, '
             f'a {_p(rest["named_pct"])} share. Neither rank group contributes any recorded blocks.'),
            (f'From the top {_n(method["top_limit"])} sites, {_n(top["readable"])} files could be read, '
             f'and {_n(top["named"])} name it, or {_p(top["named_pct"])}. '
             f'Below them, {_n(rest["named"])} of {_n(rest["readable"])} readable files name it, '
             f'{_p(rest["named_pct"])} of that group. Recorded blocking is absent from both groups.'),
            (f'Among the highest {_n(method["top_limit"])} ranks, {_n(top["named"])} of {_n(top["readable"])} '
             f'readable files name it, a {_p(top["named_pct"])} share. '
             f'Naming in the rest of the survey reaches {_n(rest["named"])} files, '
             f'{_p(rest["named_pct"])} of {_n(rest["readable"])} readable there. These naming totals carry no recorded bans.'),
            (f'Its name appears in {_files(top["named"])} near the top, compared with {_n(rest["named"])} farther down. '
             f'The shares are {_p(top["named_pct"])} of {_n(top["readable"])} readable files in the top {_n(method["top_limit"])}, '
             f'and {_p(rest["named_pct"])} of {_n(rest["readable"])} in remaining ranks. Both samples have no recorded whole-site blocks.'),
        ]
        sample = zero_samples[rest["named"] % len(zero_samples)]
    if row["probe_tokens"]:
        origin = "comes" if all_["blocked_unnamed"] == 1 else "come"
        sources = [
            'Rules for every crawler, written <code>User-agent: *</code>, count here too.',
            'A general <code>User-agent: *</code> ban contributes to this total whenever it applies to this crawler.',
            'These totals cover both groups naming it and rules that apply to every crawler.',
            'The survey includes relevant <code>User-agent: *</code> instructions alongside instructions addressed to this crawler.',
            'Both named groups and general <code>User-agent: *</code> groups can contribute to blocking the whole site.',
            'Counts include a whole-site ban in a <code>User-agent: *</code> group if no named group overrides it.',
        ]
        overlap = (f'Of {_n(all_["blocked"])} blocks, {_n(all_["blocked_unnamed"])} '
                   f'{origin} only from that general rule, without naming this crawler.'
                   if all_["blocked_unnamed"] else '')
    else:
        agreement = "does" if all_["blocked_unnamed"] == 1 else "do"
        sources = [
            'Only whole-site blocks recorded against this crawler’s name count here. Rules addressed to every crawler are outside this count.',
            'This total covers whole-site bans recorded for this name. A blanket <code>User-agent: *</code> rule alone is outside this measure.',
            'For this entry, we counted whole-site bans attached to its own name, leaving general rules for all crawlers out of the total.',
            'Here, the total counts whole-site blocks recorded for this crawler. It leaves out general <code>User-agent: *</code> instructions.',
            'Blocking here counts whole-site bans recorded for it by name. A general ban for all crawlers is excluded.',
            'This is a count of blocks attached to the named crawler, covering the whole site. Blanket rules for every crawler do not enter it.',
        ]
        overlap = (f'Of {_n(all_["blocked"])} blocks, {_n(all_["blocked_unnamed"])} '
                   f'{agreement} not also appear in our count of files naming it.' if all_["blocked_unnamed"] else '')
    source = sources[(row["naming_position"] + all_["named_blocked"]) % len(sources)]
    details = [
        (f'The split among files that name it is {_n(all_["named_blocked"])} with a whole-site block '
         f'and {_n(all_["named_unblocked"])} without one. Its name is absent from {_n(all_["unnamed"])} readable files. '
         'We ignore capitalization and repeated names.'),
        (f'We found {_files(all_["named_blocked"])} naming it and blocking the whole site, '
         f'along with {_files(all_["named_unblocked"])} naming it without that ban. '
         f'Another {_n(all_["unnamed"])} files omit the name. We ignore capitalization and repeated names.'),
        (f'Looking just at named files gives {_n(all_["named_blocked"])} blocks and {_n(all_["named_unblocked"])} '
         f'without a whole-site block. For {_n(all_["unnamed"])} readable files, we found no mention by name. '
         'We ignore capitalization and repeated names.'),
        (f'The naming total includes {_files(all_["named_blocked"])} with a ban on every path '
         f'and {_files(all_["named_unblocked"])} without that ban. Elsewhere, {_n(all_["unnamed"])} files do not name it. '
         'We ignore capitalization and repeated names.'),
        (f'The overlap between naming and blocking is {_files(all_["named_blocked"])}. '
         f'Naming without a whole-site ban accounts for {_n(all_["named_unblocked"])}, '
         f'and {_n(all_["unnamed"])} files never name it. We ignore capitalization and repeated names.'),
        (f'Names and bans overlap in {_files(all_["named_blocked"])}. '
         f'We also found {_files(all_["named_unblocked"])} with a name and no whole-site ban, '
         f'plus {_n(all_["unnamed"])} files omitting the name. Case changes and repeated spellings are merged.'),
        (f'The counted overlap is {_files(all_["named_blocked"])}, with {_files(all_["named_unblocked"])} '
         f'naming it without banning all paths. Missing names account for {_n(all_["unnamed"])} files. '
         'Repeating a name or changing its capitalization does not increase the naming total.'),
    ]
    detail = details[(row["naming_position"] + rest["named"]) % len(details)]
    if not all_["named_unblocked"]:
        named_blocks = [
            (f'All {_n(all_["named"])} files naming it also record a whole-site block. '
             f'The remaining {_n(all_["unnamed"])} files do not name it. '
             'Naming counts ignore capitalization and repeated mentions.'),
            (f'{_n(all_["named"])} files have the name plus a whole-site ban. '
             f'Outside that set, {_n(all_["unnamed"])} files never name it. '
             'Repeated user-agent mentions or capitalization variants are counted once.'),
            (f'Among files listing the crawler, {_n(all_["named"])} record a ban on all paths. '
             f'The number not naming it is {_n(all_["unnamed"])}. '
             'For naming, repeats and different case are merged.'),
        ]
        detail = named_blocks[all_["named"] % len(named_blocks)]
    return f'''<h2>How many sites block it?</h2>
<p>{scale}</p>
<p>{sample}</p>
{_table(["Readable files", "Named by", "Named share", "Blocked by", "Blocked share"], [
    [f"{token}, all ranks", _n(all_["named"]), _p(all_["named_pct"]), _n(all_["blocked"]), _p(all_["blocked_pct"])],
    [f'{token}, top {_n(method["top_limit"])}', _n(top["named"]), _p(top["named_pct"]), _n(top["blocked"]), _p(top["blocked_pct"])],
    [f"{token}, remaining ranks", _n(rest["named"]), _p(rest["named_pct"]), _n(rest["blocked"]), _p(rest["blocked_pct"])],
])}
<p>{source} {overlap} {detail}</p>'''


def _change(row: dict) -> str:
    if row["change"] is None:
        return ""
    change = row["change"]
    shares = change["shares"]
    if change["net"] < 0:
        net = f'{_n(abs(change["net"]))} fewer of the same {_n(change["panel"])} sites block it'
    elif change["net"] > 0:
        net = f'{_n(change["net"])} more of the same {_n(change["panel"])} sites block it'
    else:
        net = f'the number blocking it is unchanged across the same {_n(change["panel"])} sites'
    return f'''<h2>Has that changed since August?</h2>
<p>Between August and October, {_n(change["lost"])} sites that had blocked it stopped and {_n(change["gained"])} started,
so {net}. A further {_n(change["both"])} blocked it in both months, and {_n(change["neither"])} did so in neither.
Keeping the sites the same lets us count changes in their rules.</p>
<p>August’s full sample had {_n(shares["aug"])} blocks among {_n(change["aug_readable"])} readable files.
October’s was {_n(shares["oct"])} among {_n(row["overall"]["readable"])}.
Those monthly totals also reflect which files we could read on each visit.</p>
{_table(["August to October", "Files"], [["Started blocking", _n(change["gained"])],
    ["Stopped blocking", _n(change["lost"])], ["Blocked in both", _n(change["both"])],
    ["Blocked in neither", _n(change["neither"])], ["Net change", f'{change["net"]:+,}']])}'''


def _reference(row: dict) -> str:
    token = escape(row["token"])
    fields = [("operator", "Operator"), ("function", "Purpose"),
              ("respect", f"Does {token} obey robots.txt?"), ("frequency", "Frequency")]
    rows = [[label, ' / '.join(dict.fromkeys('“' + escape(e[field]) + '”' for e in row["reference_entries"]))]
            for field, label in fields]
    rows.append([f"Cloudflare managed list for {token}", "Yes" if row["cloudflare_managed"] else "No"])
    if row["description"].startswith("Description unavailable"):
        description = ''
    elif row["shared_description_count"]:
        entry = "entry" if row["shared_description_count"] == 1 else "entries"
        description = (f'<p>A matching description is used for {_n(row["shared_description_count"])} other {entry}. '
                       'Counts below are specific to this crawler.</p>')
    elif row["slug"] == "amazon-kendra":
        description = ('<p>The reference describes a search service for unstructured data. '
                       'It says the service returns specific answers, works with AWS services such as '
                       'Amazon S3 and Amazon Lex, and offers enterprise-grade security.</p>')
    else:
        # Contact requests in the community reference address its maintainers.
        description_text = row["description"].split(" If you think", 1)[0]
        description = f'<blockquote><p>“{escape(description_text)}”</p></blockquote>'
    role = _role(row)
    purpose = {
        "training": 'Model training is this crawler’s listed use.',
        "search": 'The listed use here is search.',
        "user": 'Here, the reference describes visits triggered by a user.',
        "assistant": 'The stated role here is an AI assistant.',
        "ignores": 'The reference says this crawler ignores robots.txt.',
        "other": 'This entry’s stated use is quoted above.',
    }[role]
    if role == "other":
        purpose = {
            "AI Data Providers": 'Its listed role is supplying data for AI tools.',
            "AI Data Scrapers": 'This entry is classed as a crawler collecting data for AI.',
            "AI Coding Agents": 'The listed coding role concerns tools that help with software work.',
            "AI Agents": 'The reference places this crawler among AI agents.',
            "Undocumented AI Agents": 'The reference leaves this agent’s purpose undocumented.',
        }.get(row["function"], purpose)
        if "Firebase" in row["function"]:
            purpose = 'Here, the listed use is supporting AI apps developed with Firebase.'
    choices = [
        'An owner may want search visitors and answers that link back to a page while keeping its text out of model-training datasets.',
        'Helping people find a page through search is a different use from using its contents to train a model, so owners may allow those visits separately.',
        'A site can welcome a page fetch prompted by a person while declining the collection of that text to build future models.',
        'Indexing helps readers find pages, and a user’s request can fetch one. Training reuses the material in models, which an owner may choose to block.',
        'An owner may allow a search crawler to list a page or an assistant to retrieve it for someone, yet decline to supply the text for training.',
        'Allowing people to find and read a page need not include permission to gather it for model training. Owners can express those choices in crawler-specific groups.',
        'An owner who wants search traffic may allow indexing and visits requested by users, yet decline to have the same content gathered for training datasets.',
        'Someone asking an assistant to open a page is using it for an immediate answer. An owner may permit that request and block automatic training collection.',
        'Search indexing is aimed at helping people find pages. Feeding text into model training is another use an owner may decline.',
        'A requested page visit can answer a person now, whereas training collects material for a model. Owners may apply different access rules.',
        'Keeping a site available to readers may include allowing search and requested fetches. An owner may still keep the text out of training collections.',
        'An owner may permit an assistant to read a page for someone and deny bulk collection that would use it as training material.',
        'Using a page as a search result can send people to it. Training models uses its contents for another purpose, which an owner may refuse.',
        'An owner may want a page included in search and available on request without offering its contents for future model development.',
        'Reading a page to answer a user has a different purpose from building a model with it. Owners may allow the requested visit.',
        'Search referrals or a user’s question can give an owner a reason to allow access while declining collection of page text for training.',
    ]
    explanation = choices[(row["naming_position"] + row["overall"]["blocked"] + row["overall"]["named"]) % len(choices)]
    return f'''<h2>Who runs {token}?</h2>
{_table(["Fact", f"{token} reference entry"], rows)}
<p class="table-note">These facts quote the stored community <a href="{REFERENCE}">ai.robots.txt reference</a>.</p>
{description}
<p>{purpose} {explanation}</p>'''


def _rules(row: dict) -> str:
    token = escape(row["token"])
    agents = "\n".join("User-agent: " + escape(t) for t in row["spellings"])
    note = ('The examples include the spelling variants counted together here. ' if len(row["spellings"]) > 1 else '')
    standard = '<a href="https://www.rfc-editor.org/rfc/rfc9309#section-2.2.1">robots.txt standard</a>'
    locations = [
        'Put these in robots.txt at the site root.',
        'Edit the root robots.txt file on your site.',
        'Use your site’s root file, robots.txt.',
        'These lines go in robots.txt at the root.',
        'Place the group in your root robots.txt file.',
        'Add these lines to robots.txt at your site root.',
    ]
    precedence = [
        f'Per the {standard}, a group naming {token} takes precedence over <code>User-agent: *</code>.',
        f'The {standard} gives a {token} group precedence over <code>User-agent: *</code> for this crawler.',
        f'Specific groups for {token} take precedence over <code>User-agent: *</code>, according to the {standard}.',
        f'<code>User-agent: *</code> yields to a group naming {token} under the {standard}.',
        f'Per the {standard}, a named group for {token} overrides <code>User-agent: *</code>.',
        f'For {token}, the {standard} gives a named group priority over <code>User-agent: *</code>.',
    ]
    variant = (row["naming_position"] + len(row["spellings"])) % len(locations)
    return f'''<h2>How to block or allow it</h2>
<p>{note}{locations[variant]} {precedence[variant]}</p>
<h3>Block the whole site</h3><pre><code>{agents}
Disallow: /</code></pre>
<h3>Allow access</h3><pre><code>{agents}
Allow: /</code></pre>'''


def _context(row: dict, rows: list[dict]) -> str:
    method = row["method"]
    position = row["naming_position"]
    rank = '' if position == 1 else _ordinal(position) + ' '
    siblings = [r for r in rows if r["operator_group"] == row["operator_group"] and r is not row
                and (r["publish"] or r["existing_page"])] if row["operator_group"] else []
    links = "".join(f'<li><a href="{_url(r)}">{escape(r["token"])}</a></li>' for r in siblings)
    related = f'<h2>Which other crawlers does this operator run?</h2><ul>{links}</ul>' if siblings else ''
    collections = [
        f'We surveyed Tranco’s top {_n(method["population"])} sites on {method["collected_day"]}.',
        f'On {method["collected_day"]}, we requested robots.txt from Tranco’s top {_n(method["population"])} sites.',
        f'The survey covered {_n(method["population"])} top Tranco sites, collected on {method["collected_day"]}.',
        f'Our {method["collected_day"]} collection used Tranco’s top {_n(method["population"])} sites.',
    ]
    limits = [
        f'Files had an {method["timeout_s"]}-second timeout and a {_n(method["oversize_bytes"])}-byte limit.',
        f'An {method["timeout_s"]}-second wait or a file over {_n(method["oversize_bytes"])} bytes ended a read.',
        f'Requests could run for {method["timeout_s"]} seconds, with a {_n(method["oversize_bytes"])}-byte file limit.',
        f'Each file had {method["timeout_s"]} seconds to arrive, up to {_n(method["oversize_bytes"])} bytes.',
        f'A request timed out after {method["timeout_s"]} seconds, with files capped at {_n(method["oversize_bytes"])} bytes.',
    ]
    exclusions = [
        'Shares exclude unreachable, unavailable and oversized files.',
        'Only available files we could read enter the percentages.',
        'Missing, unreachable and oversized files do not contribute to these shares.',
    ]
    parser = f'<code>{escape(method["parser"])}</code>'
    readings = [
        f'Repeat readings are included, using {parser}.',
        f'Parsing includes files read again, through {parser}.',
        f'{parser} parsed both initial and repeat readings.',
        f'The file readings, including repeats, use {parser}.',
        f'Later readings are included in results from {parser}.',
        f'Reading files again used {parser} as well.',
        f'Collection and repeat readings used {parser}.',
    ]
    method_text = ' '.join([collections[(position + row["overall"]["blocked"]) % len(collections)],
                            limits[(position + row["top"]["named"] + row["top"]["blocked"]) % len(limits)],
                            exclusions[(position + row["rest"]["blocked"]) % len(exclusions)],
                            readings[(position + row["overall"]["named"]) % len(readings)]])
    return f'''<p>It's the {rank}most-named crawler of the {_n(row["eligible_count"])} we counted in the <a href="/ai-crawlers/">crawler index</a>.</p>
{related}
<h2>How we counted</h2>
<p>For {escape(row["token"])}, {method_text[0].lower() + method_text[1:]} See the <a href="/learn/ai-crawler-directives/">full survey method</a>.</p>'''


def _faq(row: dict) -> list[tuple[str, str]]:
    overall, top, peer = row["overall"], row["top"], row["comparison"]
    named = _n(overall["named"])
    if overall["named_unblocked"]:
        naming = [
            f'We found {_files(overall["named_unblocked"])} without a whole-site ban among {named} that name it.',
            f'The {named} files naming it include {_files(overall["named_unblocked"])} without a whole-site ban.',
            f'This survey includes {_files(overall["named_unblocked"])} with the name and no whole-site ban, out of {named} naming files.',
            f'The {named} files that mention its name do not all record a whole-site ban. Those without one total {_n(overall["named_unblocked"])}.',
            (f'A name identifies the crawler addressed by a group. The survey found {_files(overall["named_unblocked"])} '
             f'with that name and no recorded whole-site ban, out of {named}.'),
        ]
    else:
        naming = [
            f'Here, all {named} files that name it also contain a whole-site ban.',
            f'In the {named} files naming this crawler, every one also blocks the whole site.',
            f'The {named} files with its name all deny whole-site access in these readings.',
            f'Every one of the {named} files naming it also has a whole-site ban.',
            f'A ban accompanies each appearance of the name across {named} files.',
        ]
    questions = [
        ('Does a User-agent line mean it is blocked?', 'What do the top-ranked sites show?', 'Which nearby entry can I compare?'),
        ('What does naming this crawler tell me?', 'Are leading sites different?', 'How does the nearby crawler compare?'),
        ('Can a file name it and still allow it?', 'How do the shares compare by rank?', 'What other entry is close in the index?'),
    ]
    ranks = [
        (f'At the top of the ranking, {_p(top["named_pct"])} of readable files name it '
         f'and {_p(top["blocked_pct"])} block it. Across all ranks, those shares are '
         f'{_p(overall["named_pct"])} and {_p(overall["blocked_pct"])}.'),
        (f'For naming rules, {_p(top["named_pct"])} of the leading sample mentions it, '
         f'compared with {_p(overall["named_pct"])} overall. Whole-site blocking is '
         f'{_p(top["blocked_pct"])} at leading ranks and {_p(overall["blocked_pct"])} across the full sample.'),
        (f'Its name appears in {_p(top["named_pct"])} of readable leading files and {_p(overall["named_pct"])} overall. '
         f'Blocking affects {_p(top["blocked_pct"])} in the leading group and {_p(overall["blocked_pct"])} in all ranks.'),
        (f'Leading files record {_p(top["named_pct"])} with the name and {_p(top["blocked_pct"])} blocking it. '
         f'Across all readable files, the corresponding shares are {_p(overall["named_pct"])} '
         f'and {_p(overall["blocked_pct"])}.'),
        (f'Within readable robots.txt files near the top of the ranking, {_p(top["named_pct"])} name it '
         f'and {_p(top["blocked_pct"])} block it. Overall, naming reaches {_p(overall["named_pct"])} '
         f'and blocking {_p(overall["blocked_pct"])}.'),
    ]
    peer_token = escape(peer["token"])
    comparisons = [
        (f'{peer_token} is named by {_n(peer["named"])} files and blocked by {_n(peer["blocked"])}, '
         f'or {_p(peer["blocked_pct"])}. For this crawler, {named} files name it '
         f'and {_n(overall["blocked"])} block it, a {_p(overall["blocked_pct"])} share.'),
        (f'For comparison, {peer_token} has {_n(peer["named"])} files naming it and {_n(peer["blocked"])} blocks, '
         f'or {_p(peer["blocked_pct"])}. Our counts for this entry are {named} files with the name '
         f'and {_n(overall["blocked"])} blocking the whole site, or {_p(overall["blocked_pct"])}.'),
        (f'The nearby {peer_token} entry reports {_n(peer["named"])} files that name it and '
         f'{_n(peer["blocked"])} whole-site blocks, {_p(peer["blocked_pct"])} of readable files. '
         f'Here, {named} files mention the name and {_n(overall["blocked"])} block access, or {_p(overall["blocked_pct"])}.'),
    ]
    variant = (row["naming_position"] + overall["blocked_unnamed"]) % len(questions)
    answers = [naming[(row["naming_position"] + overall["named_blocked"]) % len(naming)],
               ranks[(row["naming_position"] + top["blocked"]) % len(ranks)],
               comparisons[(row["naming_position"] + peer["named"]) % len(comparisons)]]
    return list(zip(questions[variant], answers))


def _next_step(src: str) -> str:
    block = with_next_step("", src)
    block = block.replace("&ndash;", "-").replace("&mdash;", ", ")
    block = block.replace("\u2013", "-").replace("\u2014", ", ")
    return '<footer aria-label="Next step">' + block + '</footer>'


def _title(token: str) -> str:
    """First requested form that fits lint's decoded 60-character title limit.

    render() writes this title as supplied, without a brand suffix.
    """
    for title in (f'{token}: who runs it and how many sites block it',
                  f'{token}: who runs it and who blocks it',
                  f'{token} crawler: operator and block rate',
                  f'{token}: AI crawler facts'):
        if len(title) <= 60:
            return title
    raise ValueError(f"Crawler token cannot fit a title: {token}")


def _page(row: dict, rows: list[dict]) -> Path:
    token, month = escape(row["token"]), row["method"]["month"]
    body = (f'<p class="lede">{_opening(row)}</p>' + _reference(row) + _measurement(row)
            + _change(row) + _rules(row) + _context(row, rows))
    return render(cat="ai-crawlers", slug=row["slug"],
                  title=escape(_title(row["token"])),
                  h1=token, desc=f'{row["token"]} in the {month} robots.txt survey. Operator, purpose, named and blocked counts, and rules to allow or block it.',
                  crumb=f'<a href="/ai-crawlers/">AI crawlers</a> / {token}',
                  body=body, faq=_faq(row),
                  closer=_next_step("ai-crawlers-" + row["slug"]))


SORT_SCRIPT = '''<script>
document.querySelectorAll('[data-crawler-sort]').forEach(function (button) {
  button.addEventListener('click', function () {
    const table = button.closest('table');
    const column = Number(button.dataset.crawlerSort);
    const ascending = button.getAttribute('aria-pressed') !== 'true';
    const rows = Array.from(table.tBodies[0].rows);
    rows.sort(function (a, b) {
      const left = (a.cells[column].querySelector('.crawler-operator') || a.cells[column]).textContent.trim();
      const right = (b.cells[column].querySelector('.crawler-operator') || b.cells[column]).textContent.trim();
      return (column >= 3 ? Number(left.replaceAll(',', '')) - Number(right.replaceAll(',', '')) : left.localeCompare(right)) * (ascending ? 1 : -1);
    });
    table.querySelectorAll('th').forEach(function (header) { header.removeAttribute('aria-sort'); });
    table.querySelectorAll('[data-crawler-sort]').forEach(function (control) {
      control.setAttribute('aria-pressed', 'false');
    });
    button.closest('th').setAttribute('aria-sort', ascending ? 'ascending' : 'descending');
    button.setAttribute('aria-pressed', String(ascending));
    rows.forEach(function (row) { table.tBodies[0].appendChild(row); });
  });
});
</script>'''


INDEX_STYLE = '''<style>
.crawler-index .crawler-counts { display: none; }
@media (max-width: 639px) {
  .crawler-index .wrap-tbl { overflow: visible; }
  .crawler-index table, .crawler-index tbody, .crawler-index tr { display: block; width: 100%; min-width: 0; }
  .crawler-index thead, .crawler-index table.cmp td:nth-child(n+3) { display: none; }
  .crawler-index tr { padding: .6rem 0; border-bottom: 1px solid var(--border); }
  .crawler-index table.cmp td { display: block; padding: 0; border: 0; }
  .crawler-index td:first-child { overflow-wrap: anywhere; }
  .crawler-index table.cmp td:nth-child(2) { display: flex; gap: .25em; font-size: .75rem; white-space: nowrap; }
  .crawler-index .crawler-operator { overflow: hidden; text-overflow: ellipsis; }
  .crawler-index .crawler-counts { display: inline; flex-shrink: 0; }
}
</style>'''


def _index(rows: list[dict], method: dict) -> Path:
    eligible = [r for r in rows if r["overall"]["named"] >= method["minimum_named"]]
    headers = [f'<button type="button" data-crawler-sort="{i}" aria-pressed="false">{label}</button>'
               for i, label in enumerate(["Token", "Operator", "Purpose", "Named by", "Blocked by"])]
    table = _table(headers, [[f'<a href="{_url(r)}">{escape(r["token"])}</a>',
                             f'<span class="crawler-operator" title="{escape(r["operator"])}">{escape(r["operator"])}</span>'
                             f'<span class="crawler-counts">· named by {_n(r["overall"]["named"])} ({_p(r["overall"]["named_pct"])}) '
                             f'· blocked by {_n(r["overall"]["blocked"])} ({_p(r["overall"]["blocked_pct"])})</span>',
                             escape(r["function"]), _n(r["overall"]["named"]), _n(r["overall"]["blocked"])] for r in eligible])
    body = f'''{INDEX_STYLE}<p class="lede">AI crawler rules in the {method["month"]} survey of Tranco’s top {_n(method["population"])} sites,
with counts from {_n(method["readable"])} readable robots.txt files.</p>
<p>Select a column heading to sort. Each row merges case and version spellings and needs at least {_n(method["minimum_named"])}
files naming it. Existing crawler articles are linked at their current addresses. Purpose and operator are quoted from
the saved community <a href="{REFERENCE}">ai.robots.txt reference</a>.</p><div class="crawler-index">{table}</div>
<p>Named by counts files naming the crawler in a User-agent line. Blocked by counts instructions to stay out of the whole site.
Some totals include rules for every crawler, while others count named rules alone. Each linked page explains which count it uses,
how many files we could read, and how the leading sites compare.
<a href="/learn/ai-crawler-directives/">Read the survey method</a>.</p>{SORT_SCRIPT}'''
    return render(cat="ai-crawlers", slug="", title=f'AI crawler index, {method["month"]}',
                  desc='Compare AI crawler operators, purposes and measured robots.txt naming and blocking counts from the October survey.',
                  h1="AI crawler index", crumb="AI crawlers", body=body,
                  closer=_next_step("ai-crawlers-index"))


def build_all() -> list[Path]:
    write_data()
    data = F.ai_crawler_pages()
    pages = [_page(row, data["rows"]) for row in data["rows"] if row["publish"]]
    return [_index(data["rows"], data["method"]), *pages]


if __name__ == "__main__":
    for path in build_all():
        print(path)
