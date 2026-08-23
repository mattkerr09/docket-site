#!/usr/bin/env python3
"""Have the primary sources moved since the knowledge feed was last compiled?

`publish_knowledge.py` says the honest thing: *"The judgement in keeping this
current is not automatable — deciding that a newly announced crawler matters, or
that a piece of advice has been superseded, means reading primary sources and
thinking."* That is true and this does not pretend otherwise.

What IS automatable is the part that actually fails: **noticing**. The feed was
compiled 2026-08-07 and the deploy gate has been printing "unchanged since
2026-08-07" ever since, as a note, while passing. A staleness signal nobody is
obliged to act on is how a product that sells being current stops being current.

So this watches the sources the feed itself cites, and turns "someone must
remember to go and look" into "the loop is handed a list".

WHAT IT REPORTS

    NEW          never seen before — record it and read it
    CHANGED      the page moved since the last run; a summary of how much
    UNREACHABLE  not the same as unchanged, and never counted as one
    same         no visible change

WHAT IT CANNOT DO, and this is the limit that matters

  **It detects change, not significance.** A layout tweak on Google's blog is a
  change; so is a new ranking update. It cannot tell them apart and does not
  try. What it buys is that nobody has to remember to look — the reading is
  still a person's job, which is the same division `publish_knowledge.py` draws.

  It also cannot see a change that leaves the text identical, and it hashes
  visible text rather than raw HTML on purpose: raw HTML changes on every
  deploy of someone else's site, and a watcher that cries wolf daily gets
  ignored, which is worse than not having one.

    python3 scripts/watch_sources.py              # report, exit 1 if action is due
    python3 scripts/watch_sources.py --record     # accept the current state
    python3 scripts/watch_sources.py --self-test  # prove it can see a change
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
FEED = HERE.parent / "site" / "data" / "knowledge.json"
STATE = HERE.parent / "data" / "source-watch.json"

#: How long a feed may sit untouched while its sources move before this stops
#: being a note and starts being a failure. Deliberately not zero: sources
#: change cosmetically all the time and a gate that fires every day is one
#: nobody reads.
STALE_DAYS = 21

#: The sources the feed's own `sources` block names, as URLs. Each says what it
#: governs, so a report tells the reader which part of the feed to revisit.
SOURCES = {
    "google-ranking-updates": (
        "https://developers.google.com/search/updates/ranking",
        "algorithm_notes — the Search Status ranking-update history"),
    "google-search-central-blog": (
        "https://developers.google.com/search/blog",
        "algorithm_notes — announcements before they reach the dashboard"),
    "google-crawlers": (
        "https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers",
        "ai_crawlers — Googlebot and Google-Extended user agents"),
    "web-vitals-thresholds": (
        "https://web.dev/articles/vitals",
        "web_vitals — the metric set and its thresholds"),
    "openai-crawlers": (
        "https://platform.openai.com/docs/bots",
        "ai_crawlers — GPTBot, OAI-SearchBot, ChatGPT-User"),
    "anthropic-crawlers": (
        "https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler",
        "ai_crawlers — ClaudeBot and friends"),
    "perplexity-crawlers": (
        "https://docs.perplexity.ai/guides/bots",
        "ai_crawlers — PerplexityBot"),
}

_TAGS = re.compile(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>")
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def visible_text(html: str) -> str:
    """Text a reader sees. Raw HTML churns on every unrelated deploy."""
    body = _TAGS.sub(" ", html)
    return " ".join(re.sub(r"<[^>]+>", " ", body).split())


class _Follow308(urllib.request.HTTPRedirectHandler):
    """urllib follows 301/302/303/307 and NOT 308.

    Perplexity's bot docs answer 308, so the first run of this watcher reported
    them UNREACHABLE — which reads as "the source is gone" when it had simply
    moved. An unreachable source is a real signal here, so a false one is
    expensive.
    """

    def http_error_308(self, req, fp, code, msg, headers):  # noqa: D102
        return self.http_error_301(req, fp, 301, msg, headers)


_OPENER = urllib.request.build_opener(_Follow308)


def fetch(url: str) -> tuple:
    """(text, error). An error is never treated as 'unchanged'."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA,
                                               "Accept": "text/html,*/*"})
    try:
        with _OPENER.open(req, timeout=30) as r:
            return visible_text(r.read().decode("utf-8", "replace")), None
    except urllib.error.HTTPError as e:
        return "", f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return "", type(e).__name__


def feed_date() -> str:
    if not FEED.is_file():
        return ""
    try:
        return json.loads(FEED.read_text()).get("compiled", "")
    except Exception:  # noqa: BLE001
        return ""


def load_state() -> dict:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text())
        except Exception:  # noqa: BLE001
            return {}
    return {}


def scan() -> tuple:
    """(rows, changed_names, unreachable_names)."""
    state = load_state()
    rows, changed, unreachable = [], [], []
    for name, (url, governs) in sorted(SOURCES.items()):
        text, error = fetch(url)
        if error:
            rows.append((name, "UNREACHABLE", error, governs))
            unreachable.append(name)
            continue
        digest = hashlib.sha256(text.encode()).hexdigest()
        previous = state.get(name, {})
        if not previous:
            rows.append((name, "NEW", f"{len(text)} chars", governs))
            changed.append(name)
        elif previous.get("sha256") != digest:
            before = previous.get("length", 0)
            delta = len(text) - before
            rows.append((name, "CHANGED", f"{delta:+d} chars since {previous.get('seen','?')}",
                         governs))
            changed.append(name)
        else:
            rows.append((name, "same", f"since {previous.get('seen','?')}", governs))
    return rows, changed, unreachable


def record() -> int:
    state = load_state()
    today = dt.date.today().isoformat()
    wrote = 0
    for name, (url, _governs) in sorted(SOURCES.items()):
        text, error = fetch(url)
        if error:
            print(f"  {name}: {error} — NOT recorded, because an unreachable source "
                  f"must not be written down as a known state")
            continue
        state[name] = {"url": url, "sha256": hashlib.sha256(text.encode()).hexdigest(),
                       "length": len(text), "seen": today}
        wrote += 1
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    print(f"  recorded {wrote} source(s) as of {today} in {STATE.relative_to(HERE.parent)}")
    return 0


def self_test() -> int:
    """Prove it can see a change, by corrupting the RECORDED state rather than
    the checker's expectations — a control has to exercise the path it claims
    to."""
    state = load_state()
    if not state:
        print("  self-test SKIPPED: nothing recorded yet; run --record first")
        return 0
    name = sorted(state)[0]
    original = json.dumps(state, indent=2, sort_keys=True) + "\n"
    try:
        state[name]["sha256"] = "0" * 64
        STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        _rows, changed, unreachable = scan()
        if name in unreachable:
            print(f"  self-test INCONCLUSIVE: {name} was unreachable this run")
            return 0
        if name not in changed:
            print(f"  SELF-TEST FAILED — {name} was given a zeroed digest and still "
                  f"reported unchanged. The watcher cannot see a change.")
            return 1
        print(f"  self-test ok — a zeroed digest for {name} was reported as CHANGED")
        return 0
    finally:
        STATE.write_text(original)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true", help="accept the current state as seen")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    compiled = feed_date()
    print(f"  knowledge feed compiled: {compiled or 'unknown'}")

    if args.record:
        return record()
    if args.self_test:
        return self_test()

    rows, changed, unreachable = scan()
    width = max(len(n) for n, *_ in rows)
    for name, status, detail, governs in rows:
        print(f"  {status:12} {name:{width}}  {detail}")
        if status in ("NEW", "CHANGED"):
            print(f"  {'':12} {'':{width}}  -> {governs}")

    age = None
    if compiled:
        try:
            age = (dt.date.today() - dt.date.fromisoformat(compiled)).days
        except ValueError:
            age = None

    print()
    if unreachable:
        print(f"  {len(unreachable)} source(s) unreachable — that is not 'unchanged', "
              f"and nothing about them was recorded.")
    if not changed:
        print("  SOURCES ok — nothing the feed cites has visibly moved.")
        return 1 if unreachable else 0

    print(f"  {len(changed)} source(s) moved since the feed was compiled"
          + (f", which was {age} days ago" if age is not None else ""))
    if age is not None and age >= STALE_DAYS:
        print(f"  ACTION DUE — the feed has been untouched for {age} days (limit "
              f"{STALE_DAYS}) while its sources changed. Read the pages above, decide "
              f"what matters, and update site/data/knowledge.json.")
        return 1
    print("  Read them when convenient; the feed is still inside its window. "
          "Run --record once the change has been read and judged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
