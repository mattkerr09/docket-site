# Page anatomy — the house standard for docketseo.app

Written 2026-09-16 because three writers now work in parallel and a standard
held in one session's head is a standard that dies with the session. Nothing
here is new: it is what the shipped pages already do, written down so a writer
can match it without reading sixty of them.

## The shape

Every page is a Python function in `scripts/articles/<module>.py` returning
`render(...)`. Registered in `scripts/build.py` in **two** places — the import
and `pages += [...]` — **plus its hub list entry**, which is the third place and
the one that gets forgotten. Six pages shipped on 2026-09-15 and all six were
missing from the `/learn/` hub; five survived on contextual links somebody
remembered to write, so only the sixth surfaced as an orphan.

```python
render(
    cat="learn", slug="thing-that-is-wrong",
    title="…",           # ≤60 characters. The quality gate fails the build.
    desc="…",            # ≤165 characters.
    h1="…",              # NOT the title. The title is for the result page.
    crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Thing',
    body=body,           # authored HTML, never generated
    faq=[(q, a), …],     # optional
    schema_type="Article",
)
```

⚠️ **Bodies are f-strings in most modules — escape every literal `{` and `}` as
`{{` `}}`.** The `/best/` hub body is a plain string; check the module you are
editing rather than assuming either way.

⚠️ **The lint gate reads `{...}` in rendered HTML as an unrendered placeholder**
and fails the build. If you need braces in visible prose, they must survive both
the f-string and the gate.

## What a page is made of

1. **A lede that states the question**, not the topic. "Which tool to use, by
   the job you are actually doing" — not "About SEO tools".
2. **The answer, early.** The reader who leaves after two paragraphs should
   still have got the thing they came for.
3. **What Docket actually checks**, read from the check's source — its
   thresholds, its severity, the wording of its own fix text. Not from the
   check's name and not from memory.
4. **What it cannot tell you.** Every page that has one. This is the house
   voice, not modesty: `/vs/lighthouse-alternative/` leads with what Lighthouse
   does better, `/vs/scrutiny-alternative/` says plainly that Scrutiny is
   cheaper, and both are more persuasive for it.
5. **A dated source for every external claim** — the vendor's own documentation
   or specification, linked, with the date it was read.
6. **A link out to the pages that are the next question**, and an inbound link
   from a page that is already indexed.

## The nine-section brief every writer gets

Section 9 has caught an overclaim on five consecutive pages, which is no longer
luck. Its wording matters:

> **If a fact's definition in the repo is narrower than my gloss, use the
> repo's and tell me.**

The other eight: the question the page answers; who is asking it; what is
measured and where the number comes from (accessor, never a literal); what is
NOT measured; the do-not-duplicate list built **from the sitemap, not memory**;
the links this page must carry; the limits to state plainly; and the house
voice.

Two rules that are written on the brief because they have each been broken:

- **Never state a count of a list, or the length of a string, that you also
  print.** Four failures: "the five 09-09-changed pages" over an unlisted set,
  "Four limits" over five bullets, three character counts all wrong, and a
  writer catching itself writing "Three things" above four items.
- **Name no shape a small sample cannot support.** A per-host distribution of
  `[1, 1, 4, 24, 25, 25]` was called bimodal in a brief. Six observations cannot
  establish a distribution's shape. The writer refused the word and was right.

## The positioning words, and why this keeps failing the build

`verify_positioning` runs the shipped `brand.positioning` check against our own
descriptions, and it has now failed on three consecutive batches — not because
anything regressed, but because **every new page dilutes the share**. The check
wants at least two non-brand words each appearing on 30% of described pages, and
30% of a growing number is a moving target: a word on 23 pages passes at 70
pages and fails at 81.

So a description is not finished until it carries the positioning vocabulary
**where that word is true of the page**. The sentence is *Docket audits your
site on your own Mac*, and in practice the two load-bearing words are `audit`
and `site`.

⚠️ **NOT EVERY PAGE, AND NEVER WHERE IT IS FALSE.** The check's own fix text
says "this is not keyword stuffing — it is having a position", and a description
that says "audit" about a page that is not about auditing is worse than failing
the gate. Where the word does not belong, leave it out and let another page
carry the share.

Run `python3 scripts/verify_positioning.py` **before** committing, not after the
deploy starts.

## Numbers

**Accessors, never literals.** Every published figure comes from
`scripts/facts.py`, which reads the dataset. The derived-number gate rejects a
typed figure **and a typed date** in prose — though it does not reach FAQ
strings, so those are checked by eye.

A number that is not in a dataset does not go on a page. "Never invent findings
or statistics" is not a style note; it is the only thing this site is selling.

## The two-sided test, before a writer is briefed

A page is written when there is a question a reader actually has **and** an
honest answer we can source. Both sides. Crisp has 121 pages with 19 indexed,
which is what volume without winnability buys.

A measurement kills a candidate more cheaply than writing one does: publish-dates
died at 32 of 36 hosts clean, and the AI-crawler cluster at 0 of 6 passing.

**A check-explainer page does not need a new survey.** The check itself is the
measurement, its source is the citation, and the comments above it usually
record the mistake it was written to stop. That is the whole point of section 9.

## Shipping

The sequence, and `$?` is checked after the build:

1. Module written; imported and appended in `scripts/build.py`; **hub list entry
   added**.
2. `python3 scripts/build.py` — docket-site has **no `.venv`**, use `python3`.
3. `python3 scripts/collect_page_dates.py`
4. `python3 scripts/verify_link_graph.py --write --date <today>`
5. Rebuild, commit by path, `bash scripts/deploy.sh` (**exceeds 120 s —
   background it**).
6. Grep the log, then **fetch the live URL to prove it**.
7. IndexNow: `indexnow-submit.py --changed docketseo.app --sitemap-file
   "$PWD/site/sitemap.xml"`, with `--url` for a same-day second edit.
8. Grep the **live** sitemap.
9. Full `-n 0` audit of our own site. Never `-n 10`: a partial crawl makes
   `index.orphan_pages` decline, and **a decline reads like a pass**.

`/learn/what-scout-checks/` and `/thank-you/` are `noindex` and are never
submitted for indexing.
