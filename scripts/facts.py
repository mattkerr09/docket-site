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
