#!/usr/bin/env python3
"""Measured facts, in one place, for every page that quotes one.

`/index/` published 30% over a 26% dataset, and `/how-to/fix-ai-crawler-access/`
kept saying "roughly three quarters" for a week after that claim was corrected
on two other pages and disproven at scale on a third. Both survived because the
figure was typed into a sentence, and a sentence cannot go stale loudly.

So a page never reads a dataset directly and never types a measurement. It asks
here, and `verify_numbers.py` fails the build on any number in article prose
that is neither derived nor on an explicit allowlist.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CITATION = ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot")
TRAINING = ("GPTBot", "ClaudeBot", "Applebot-Extended", "Bytespider",
            "meta-externalagent", "CCBot")


@lru_cache(maxsize=None)
def directives() -> dict:
    """The Tranco top-10,000 robots.txt survey."""
    return json.loads(
        (ROOT / "site" / "data" / "ai-directives-2026-08.json").read_text())


@lru_cache(maxsize=None)
def index() -> dict:
    """The 110-site Scout Index."""
    return json.loads((ROOT / "data" / "index-2026-08.json").read_text())


@lru_cache(maxsize=None)
def entity() -> dict:
    """The homepage JSON-LD survey."""
    return json.loads(
        (ROOT / "site" / "data" / "entity-2026-08.json").read_text())


# -- the Index, recomputed from records rather than its stored summary ------

@lru_cache(maxsize=None)
def index_live() -> list:
    return [r for r in index()["records"]
            if r.get("reachable") and r.get("has_robots")]


def _blocked(record, group) -> bool:
    return any(record["ai_access"].get(bot) is False for bot in group)


def index_n() -> int:
    return len(index_live())


def index_attempted() -> int:
    return index()["summary"]["attempted"]


def index_citation_pct() -> int:
    live = index_live()
    return round(100 * sum(1 for r in live if _blocked(r, CITATION)) / len(live))


def index_any_ai() -> int:
    return sum(1 for r in index_live()
               if _blocked(r, CITATION) or _blocked(r, TRAINING))


def index_conflated_pct() -> int:
    """Share of Index sites blocking any AI crawler that hit a citation one.

    Kept because it is true of that sample, and always published next to
    `directives_training_only_pct()`, which says the opposite at scale.
    """
    live = index_live()
    hit = sum(1 for r in live if _blocked(r, CITATION))
    return round(100 * hit / index_any_ai()) if index_any_ai() else 0


# -- the directives survey ---------------------------------------------------

def _d() -> dict:
    return directives()["summary"]


def directives_hosts() -> int:
    return _d()["parseable_robots"]


def directives_ai_sites() -> int:
    return _d()["sites_with_ai_directive"]


def directives_dead_sites() -> int:
    return _d()["sites_with_dead_directive"]


def directives_dead_pct() -> float:
    return _d()["pct_dead_of_ai"]


def directives_blocks_any() -> int:
    return _d()["blocks_any"]


def directives_training_only() -> int:
    return _d()["training_only"]


def directives_training_only_pct() -> float:
    return _d()["pct_training_only"]


def directives_edge_denied() -> int:
    return _d()["edge_denied"]


def oai_search_blocked() -> int:
    return _d()["oai_search_blocked"]


def oai_search_and_gptbot() -> int:
    return _d()["oai_search_and_gptbot"]


def oai_search_only() -> int:
    return oai_search_blocked() - oai_search_and_gptbot()


def oai_overlap_pct() -> float:
    return round(100 * oai_search_and_gptbot() / oai_search_blocked(), 1)


def claude_search_blocked() -> int:
    return _d()["claude_search_blocked"]


def claude_search_and_claudebot() -> int:
    return _d()["claude_search_and_claudebot"]


def claude_search_only() -> int:
    return claude_search_blocked() - claude_search_and_claudebot()


def benign_truncations() -> int:
    """Sites an earlier draft of the dead-directive rule would have accused.

    Their tokens truncate to a name a vendor documents, so the rule works.
    """
    return _d()["benign_truncations"]


def token_sites(token: str) -> int:
    return sum(1 for h in directives()["hosts"] if token in h["ai"])


# -- the entity survey -------------------------------------------------------

def entity_n() -> int:
    return entity()["summary"]["reachable"]


def entity_org() -> int:
    return entity()["summary"]["org_schema"]


def entity_same_as() -> int:
    return entity()["summary"]["same_as"]


# -- our own link graph, measured rather than remembered ---------------------
#
# /learn/internal-link-equity/ quoted "18 pages, 242 links" and a download page
# holding 1.25% against a 5.56% average for as long as those numbers were true,
# and then for a while after they were not. The fix it describes worked — the
# download page is in the navigation now — so the article was describing a
# problem the site no longer had, using figures nobody could see were stale.


@lru_cache(maxsize=None)
def equity() -> dict:
    return json.loads((ROOT / "site" / "_data" / "link-equity.json").read_text())


def equity_pages() -> int:
    return equity()["pages"]


def equity_edges() -> int:
    return equity()["edges"]


def equity_average_pct() -> float:
    return equity()["average_share_pct"]


def equity_below_half() -> int:
    return equity()["below_half"]


def equity_node(path: str) -> dict:
    for node in equity()["nodes"]:
        if node["path"] == path:
            return node
    raise KeyError(path)


def equity_weakest(limit: int = 3) -> list:
    return sorted(equity()["nodes"], key=lambda n: n["index"])[:limit]


# -- AI-substitution portfolios, exported from real audits -------------------
#
# /learn/ai-substitution/ typed these: 33 pages, 32 with a transaction, 19 of
# ours, 5.3%. They are measurements of two live sites and they move when those
# sites do — the deli redesigns, we publish. Typed, they would have gone stale
# the way the link-equity graph did, silently and for weeks.


@lru_cache(maxsize=None)
def exposure(slug: str) -> dict:
    return json.loads(
        (ROOT / "site" / "_data" / f"exposure-{slug}.json").read_text())


def exposure_assessed(slug: str) -> int:
    return exposure(slug)["pages_assessed"]


def exposure_substitutable_pct(slug: str) -> str:
    """Formatted, because "0.0%" reads like a rounding artefact and "0%" reads
    like a finding — and the finding is what it is."""
    pct = exposure(slug)["substitutable_pct"]
    return f"{pct:.0f}" if pct == int(pct) else f"{pct:.1f}"


def exposure_band(slug: str, band: str) -> int:
    return exposure(slug)["bands"].get(band, 0)


def exposure_defence(slug: str, fragment: str) -> int:
    """How many pages carry the defence whose description contains `fragment`.

    Matched on a fragment rather than the full sentence so rewording the
    defence text in the app does not silently zero a number on the site.
    """
    for description, count in exposure(slug)["defence_counts"].items():
        if fragment in description:
            return count
    return 0


def exposure_worst(slug: str) -> dict:
    return exposure(slug)["pages"][0]


def exposure_measured(slug: str) -> str:
    return exposure(slug)["measured"]


# -- how close the web sits to Googlebot's 2MB cutoff ------------------------


@lru_cache(maxsize=None)
def page_size() -> dict:
    return json.loads(
        (ROOT / "site" / "_data" / "page-size-2026-08.json").read_text())


def size_fetched() -> int:
    return page_size()["fetched"]


def size_attempted() -> int:
    return page_size()["attempted"]


def size_over_cap() -> int:
    return page_size()["over_cap"]


def size_losing_markup() -> int:
    return page_size()["losing_markup"]


def size_median_kb() -> int:
    return round(page_size()["median_bytes"] / 1024)


def size_p90_kb() -> int:
    return round(page_size()["p90_bytes"] / 1024)


def size_cap_mb() -> int:
    return page_size()["cap_bytes"] // 1024 // 1024


def size_largest() -> dict:
    biggest = page_size()["results"][0]
    return {"host": biggest["host"],
            "mb": round(biggest["bytes"] / 1024 / 1024, 1),
            "times_cap": round(biggest["bytes"] / page_size()["cap_bytes"], 1),
            "critical_kb": round(biggest["last_critical"] / 1024)}


def size_over_list(limit: int = 5) -> list:
    cap = page_size()["cap_bytes"]
    return [{"host": r["host"], "mb": round(r["bytes"] / 1024 / 1024, 1),
             "critical_kb": round(r["last_critical"] / 1024)}
            for r in page_size()["results"] if r["bytes"] > cap][:limit]


# -- can a published contact address receive anything? -----------------------
#
# Written after scoutseo.app spent weeks advertising an address on a domain
# with no MX record. The survey exists because the obvious follow-up question —
# is that unusual? — had no published answer, and guessing was not available.


@lru_cache(maxsize=None)
def mail() -> dict:
    return json.loads((ROOT / "site" / "_data" / "mail-2026-08.json").read_text())


def mail_attempted() -> int:
    return mail()["attempted"]


def mail_answered() -> int:
    return mail()["answered"]


def mail_publishing() -> int:
    return mail()["publishing_mailto"]


def mail_publishing_pct() -> float:
    return round(100 * mail_publishing() / mail_answered(), 1)


def mail_accepts() -> int:
    return mail()["accepts_mail"]


def mail_dead() -> int:
    return mail()["dead_conclusive"]


def mail_undetermined() -> int:
    return mail()["undetermined"]


def mail_upper_bound_pct() -> float:
    """95% upper bound on the dead rate, from a zero count.

    The rule of three: with no events in n trials the 95% confidence interval
    runs from 0 to about 3/n. Quoted instead of "0%" because zero out of 80 is
    not evidence that the true rate is zero, and saying so is the difference
    between a measurement and a claim.
    """
    return round(300.0 / mail_publishing(), 1)


def mail_measured() -> str:
    return mail()["measured"]


# -- the small-business half of the same question ----------------------------
#
# /learn/dead-contact-address/ said in print that the population most exposed
# to a dead contact address is the one a popularity-ranked list cannot reach.
# This is that population, sampled from OpenStreetMap rather than from a
# traffic ranking. See scripts/collect_mail_small.py for the frame.


@lru_cache(maxsize=None)
def mail_small() -> dict:
    return json.loads(
        (ROOT / "site" / "_data" / "mail-small-2026-08.json").read_text())


def small_frame() -> int:
    return mail_small()["frame_size"]


def small_answered() -> int:
    return mail_small()["answered"]


def small_publishing() -> int:
    return mail_small()["publishing_mailto"]


def small_publishing_pct() -> float:
    return round(100 * small_publishing() / small_answered(), 1)


def small_dead() -> int:
    return mail_small()["dead_conclusive"]


def small_dead_pct() -> float:
    return round(100 * small_dead() / small_publishing(), 1)


def small_undetermined() -> int:
    return mail_small()["undetermined"]


def small_publishing_ratio() -> float:
    """How many times more often a small site publishes an address at all."""
    return round(small_publishing_pct() / mail_publishing_pct(), 1)


def small_dead_interval() -> str:
    """Wilson 95% interval for the dead rate, as a formatted range.

    A bare 1.7% invites the reader to treat seven observations as a precise
    rate. Wilson rather than the normal approximation because the count is
    small and the proportion is near zero, where the normal interval runs
    below zero and stops meaning anything.
    """
    import math

    n, k, z = small_publishing(), small_dead(), 1.96
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return f"{100 * (centre - half):.1f}% to {100 * (centre + half):.1f}%"


def small_single_location() -> dict:
    return mail_small()["single_location"]


def small_cities() -> int:
    return len(mail_small()["cities"])


# -- exchangers that do not exist --------------------------------------------
#
# The nastier sibling of the address survey, over the same OpenStreetMap frame:
# of the domains that publish an MX record at all, how many name a host that
# does not resolve? That case passes every "does this domain have an MX record"
# test ever written.


@lru_cache(maxsize=None)
def mx() -> dict:
    return json.loads((ROOT / "site" / "_data" / "mx-2026-08.json").read_text())


def mx_publishing() -> int:
    return mx()["publishing_mx"]


def mx_dead() -> int:
    return mx()["all_exchangers_dead"]


def mx_dead_pct() -> float:
    return round(100 * mx_dead() / mx_publishing(), 1)


def mx_partial() -> int:
    return mx()["partial_failure"]


def mx_shapes() -> dict:
    return mx()["dead_shapes"]


def mx_shape_rows() -> list:
    """(count, shape) worst first, for a table."""
    return [(n, shape) for shape, n in mx_shapes().items()]


def mx_top_two() -> int:
    """How many of the dead fall into the two commonest provider shapes.

    Derived rather than typed: if the distribution changes, so does the claim
    in the article that two providers account for most of them.
    """
    counts = sorted(mx_shapes().values(), reverse=True)
    return sum(counts[:2])


def mx_measured() -> str:
    return mx()["measured"]


# -- what Scout will actually crawl ------------------------------------------
#
# The site never stated a page limit, and silence reads as a small number.
# Generated from the app (seo_engine.crawler.CrawlConfig and the clamp in
# ui/src/app.js) rather than typed here, so the published ceiling cannot drift
# from the shipped one — exporting it immediately exposed the UI defaulting to
# 150 while the CLI defaulted to 200.


@lru_cache(maxsize=None)
def limits() -> dict:
    return json.loads((ROOT / "site" / "_data" / "limits.json").read_text())


def crawl_ceiling() -> int:
    return limits()["max_pages_ceiling"]


def crawl_ceiling_str() -> str:
    return f"{crawl_ceiling():,}"


def crawl_default() -> int:
    return limits()["cli_default_pages"]


def crawl_minutes() -> int:
    return limits()["wall_clock_minutes"]


def crawl_depth() -> int:
    return limits()["max_depth_default"]


# -- what the alternatives cost over time ------------------------------------
#
# Scout is a one-time price against subscriptions, and the page never did the
# arithmetic for the reader. Derived from competitors.csv so a price change
# there moves the published comparison.


def _annual(slug: str) -> tuple:
    """(low, high) annual USD for a competitor, parsed from its price note."""
    import re as _re
    import sys as _sys

    _sys.path.insert(0, str(ROOT / "scripts"))
    from render import COMPETITORS  # noqa: PLC0415 — avoids an import cycle

    note = COMPETITORS[slug]["price_note"]
    nums = [int(n.replace(",", "")) for n in _re.findall(r"\$([\d,]+)", note)]
    if not nums:
        return (0, 0)
    if "/mo" in note:
        return (min(nums) * 12, max(nums) * 12)
    return (min(nums), max(nums))


def rival_annual_low(slug: str) -> int:
    return _annual(slug)[0]


def years_to_match(slug: str) -> float:
    """Years of the cheapest tier of `slug` before it costs more than Scout."""
    import sys as _sys

    _sys.path.insert(0, str(ROOT / "scripts"))
    from render import PRICE  # noqa: PLC0415

    low = rival_annual_low(slug)
    return round(PRICE / low, 1) if low else 0.0


def three_year_cost(slug: str) -> int:
    return rival_annual_low(slug) * 3


# -- how much of the test suite exists because Scout was wrong ---------------
#
# Generated from the app's own tests. The counting rule is deliberately
# conservative and stated in the dataset: a file counts only if it names a
# specific thing Scout got wrong, not merely because it is a test.


@lru_cache(maxsize=None)
def regressions() -> dict:
    return json.loads(
        (ROOT / "site" / "_data" / "regressions.json").read_text())


def test_files() -> int:
    return regressions()["test_files"]


def regression_files() -> int:
    return regressions()["files_pinning_a_past_mistake"]


def regression_pct() -> float:
    return regressions()["pct"]


def tests_total() -> int:
    return regressions()["tests_total"]


# -- the Common Crawl hyperlink graph ----------------------------------------
#
# The homepage published "117.9 million domains" for 117,963,409, which
# truncates rather than rounds. It also carried "14 TiB of archive files" — a
# claim about Common Crawl's storage that nobody here measured, and that was
# deleted from build.py two iterations earlier for exactly that reason without
# anyone sweeping for the second copy.
#
# Both survived because verify_numbers.py only scanned `body = """..."""` and
# home.py returns its sections directly, so the homepage had never been read by
# the gate at all.


@lru_cache(maxsize=None)
def authority() -> dict:
    return json.loads((ROOT / "site" / "_data" / "authority.json").read_text())


def graph_domains() -> int:
    return authority()["domains"]


def graph_domains_m() -> str:
    """Rounded, not truncated."""
    return f"{graph_domains() / 1e6:.1f}"


def graph_release() -> str:
    return authority()["release"]


def graph_example_host() -> str:
    return authority()["example_host"]


def graph_example_referring() -> int:
    """Referring domains for the example host.

    Only written when `complete` is true — a capped scan of the edge file
    undercounts, and an undercount published as a measurement is worse than no
    figure at all. The full read takes about eleven minutes.
    """
    if not authority().get("complete"):
        raise ValueError("authority.json holds an incomplete scan; do not publish it")
    return authority()["example_referring_domains"]


# -- how long an audit takes in a pipeline -----------------------------------
#
# Measured against the frozen CLI out of the shipped bundle, not the source in
# this repo, because those are different programs and only one of them is what
# a reader will run. The figure moves between runs — one site swung fifteen
# seconds across two consecutive passes — so the page must present it as an
# order of magnitude with its date attached, never as a benchmark.
#
# Generated by scripts/collect_ci_timing.py.


@lru_cache(maxsize=None)
def ci_timing() -> dict:
    return json.loads(
        (ROOT / "site" / "_data" / "ci-timing.json").read_text())


def ci_measured() -> str:
    return ci_timing()["measured"]


def ci_page_cap() -> int:
    return ci_timing()["page_cap"]


def ci_sites() -> int:
    return ci_timing()["sites_timed"]


def ci_median_seconds() -> float:
    return ci_timing()["median_seconds"]


def ci_fastest_seconds() -> float:
    return ci_timing()["fastest_seconds"]


def ci_slowest_seconds() -> float:
    return ci_timing()["slowest_seconds"]


def ci_seconds_per_page() -> float:
    return ci_timing()["median_seconds_per_page"]


def ci_overhead_seconds() -> float:
    """Wall-clock minus the engine's own duration: what the process costs."""
    return ci_timing()["process_overhead_seconds"]


# -- what a macOS CI runner costs --------------------------------------------
#
# Quoted from GitHub's published per-minute rates, not measured here, and
# linked in the prose that uses them. They live in facts.py rather than in the
# page for the ordinary reason: the arithmetic downstream of them (per-run and
# per-month cost) was originally written out in words — "six cents", "twelve
# dollars" — where the derived-number gate scans digits and could not see it.
# A gate that covers most of a surface reports clean on the part it cannot
# read, so the words became a calculation.
#
# Source: https://docs.github.com/en/billing/reference/actions-minute-multipliers

_GH_MACOS_PER_MIN = 0.062
_GH_LINUX_PER_MIN = 0.006


def gh_macos_per_min() -> str:
    return f"${_GH_MACOS_PER_MIN:.3f}"


def gh_linux_per_min() -> str:
    return f"${_GH_LINUX_PER_MIN:.3f}"


def gh_macos_multiple() -> int:
    """How many times a macOS minute costs what a Linux one does."""
    return round(_GH_MACOS_PER_MIN / _GH_LINUX_PER_MIN)


def gh_gate_cost_cents() -> int:
    """One gate run. GitHub rounds billed time up to the whole minute, and the
    measured audit is well under one, so a run bills as exactly one minute."""
    return round(_GH_MACOS_PER_MIN * 100)


def gh_monthly_cost(runs: int) -> str:
    return f"${_GH_MACOS_PER_MIN * runs:.2f}"


# -- the brand lane, measured on real companies ------------------------------
#
# Six checks asking whether a site looks and sounds like one company. No
# competitor's crawler asks it, which made it the most differentiated thing in
# the product and, for a long time, the least evidenced.
#
# One figure here is deliberately NOT published as a rate. Scout reads
# typefaces from inline <style> only and does not fetch linked stylesheets, so
# on most sites the count is structurally absent rather than low. Publishing a
# median across sites where the question was never answerable would report
# blindness as tidiness. `brand_css_readable()` is the honest version of it.
#
# Generated by scripts/collect_brand.py.


@lru_cache(maxsize=None)
def brand() -> dict:
    return json.loads(
        (ROOT / "site" / "_data" / "brand.json").read_text())


def brand_measured() -> str:
    return brand()["measured"]


def brand_sites() -> int:
    return brand()["sites_measured"]


def brand_page_cap() -> int:
    return brand()["page_cap"]


def brand_css_readable() -> int:
    """Sites where the typeface question could be answered at all."""
    return brand()["css_readable"]


def brand_social_frame() -> int:
    """Sites linking at least one social profile — the only ones that can fail."""
    return brand()["social_frame"]


def brand_social_undeclared() -> int:
    return brand()["social_undeclared"]


def brand_social_pct() -> float:
    return round(100 * brand_social_undeclared() / brand_social_frame(), 1)


def brand_social_interval() -> str:
    """Wilson 95% interval. n is 11, so a bare percentage would overstate it."""
    import math

    n, k, z = brand_social_frame(), brand_social_undeclared(), 1.96
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return f"{100 * (centre - half):.0f}% to {100 * (centre + half):.0f}%"


def brand_max_typefaces() -> int:
    return brand()["max_typefaces"]


def brand_max_colours() -> int:
    return brand()["max_colours"]


def brand_logo_unnamed() -> int:
    return brand()["logo_unnamed"]
