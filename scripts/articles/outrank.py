#!/usr/bin/env python3
"""How to find where a bigger competitor is actually beatable.

The page exists because two of Docket's features were effectively invisible.
`docket attack` and its `--demand` flag were named once each in a feature grid
on the homepage and nowhere else — no page, no output, no explanation of what
the numbers mean or where they come from. A feature nobody can find is a feature
nobody buys.

Every figure in the output block is from one real run on 2026-08-11, quoted
verbatim inside <code> so it is evidence rather than a claim. The competitor is
Screaming Frog, which this site already compares itself to on its own page, and
whose real strength is conceded in the copy.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def outrank() -> Path:
    body = """
<p class="lede">Every SEO tool will tell you a competitor is ahead. That is the part you already
knew. The useful question is narrower and almost nobody answers it: <strong>given that they have
years and links you cannot match this quarter, where does none of that help them?</strong></p>

<p>That is a different question from "who is winning", and it has a different answer. Authority
is bought with time. Some ranking surfaces are not sold that way at all, and those are the ones
worth your afternoon.</p>

<h2>Run it</h2>

<pre><code>docket attack https://yoursite.com https://theircompetitor.com \\
      --name "Their Brand" --demand</code></pre>

<p>Docket crawls both sites, reads the link graph from
<a href="https://commoncrawl.org/" rel="noopener">Common Crawl</a>, asks Google's public
autocomplete what people actually search for in your subject, and returns the openings ranked by
<strong>winnability</strong> — how little each one depends on authority you do not have.</p>

<h2>What it says first</h2>

<p>It opens by telling you the gap is real, because a tool that flatters you is no use. From a
run against Screaming Frog, dated in the block below:</p>

<pre><code>$ docket attack https://docketseo.app https://www.screamingfrog.co.uk/seo-spider/
# measured 2026-08-11

Link authority
  you:  docketseo.app was not found in the part of the graph scanned.
        It is outside the top ranks rather than absent.
  them: www.screamingfrog.co.uk/seo-spider ranks 2,661 of 117,963,409 domains
        by harmonic centrality — the top 0.002% of the crawled web.

  Their links are a real advantage and not one you close this quarter —
  which is exactly why the openings below avoid competing on it.</code></pre>

<p>Screaming Frog is genuinely one of the best crawlers ever written, it has been trusted for
over a decade, and its link profile reflects that. If what you need is a desktop crawler for a
large site, buy it. None of what follows is an argument that they are weak.</p>

<h2>What it finds instead</h2>

<p>Three kinds of opening, each measured on the two sites rather than inferred:</p>

<pre><code>1. [strong] 1 search they answer and you do not
     Real queries where they have a page and you have none:
     "how to boost seo for free".
     Why winnable: you are competing against a single URL, not their
     whole site. Page-level quality is winnable; domain-level is not.

2. [strong] 9 real searches neither of you answers
     From Google's public autocomplete, so these are queries people
     actually type: free seo checker; where can i find keywords for
     seo for free; what is the best free seo plugin for wordpress …
     Why winnable: nobody has to be displaced on a query nobody has
     answered. Their authority is irrelevant to it.

3. [worth taking] 4 of their pages contain no figures of their own
     No percentages, sample sizes or counts — the copy asserts rather
     than measures.
     Why winnable: assistants quote specific claims. A site with
     nothing quotable cannot be quoted, however authoritative.</code></pre>

<h2>Where the searches come from</h2>

<p>Google's autocomplete endpoint publishes real queries, ordered by how commonly they are
typed. No key, no account, no index. Docket infers your subject from your own pages, expands it
through question and commercial framings, and then checks which of those questions your site
answers, which theirs does, and which neither does.</p>

<p>The requests are capped, serialised and delayed between calls. It is somebody else's public
endpoint and the run finishes in about a minute without registering as load anywhere.</p>

<h2>What this deliberately does not do</h2>

<p>Docket has no index of the web, and this feature is built so that it never needs to pretend
otherwise.</p>

<ul>
<li><strong>No rankings.</strong> It does not know where either site ranks for anything and will
not guess. Every opening is a structural difference measured on the two sites.</li>
<li><strong>No search volumes.</strong> Autocomplete gives ordering, not counts. Docket reports
the rank a query sat at and stops there — a monthly volume is a number it does not have, and
printing one anyway is how this category of tool loses its credibility. Ahrefs and Semrush sell
volumes; theirs come from clickstream panels Docket has no access to.</li>
<li><strong>No traffic or revenue projection.</strong> Docket projects its own score and nothing
else.</li>
<li><strong>No completion that merely shares letters with your subject.</strong> Autocomplete
matches substrings, so a site about SEO gets offered queries about Seoul. Those are dropped, and
the run tells you how many it dropped rather than quietly shortening the list.</li>
</ul>

<h2>What to do with the output</h2>

<p>Work the list top-down and stop when the winnability score falls off. The third kind of
opening is usually the highest-scoring and the least obvious: publishing one page of numbers
only you have — your own testing, your own customers, your own measurements — earns more
citation in AI answers than ten pages summarising what everyone already wrote.</p>

<p>The second kind is the cheapest ground on the board and the easiest to act on this week.
Write the page, put the question in the heading, answer it in the first paragraph.</p>
"""
    return render(
        cat="how-to",
        slug="outrank-a-bigger-competitor",
        title="How to find where a bigger competitor is beatable",
        desc=("Authority is bought with time. Some ranking surfaces are not sold that way — "
              "how to find the ones a bigger competitor's links do not help them win."),
        h1="How to find where a bigger competitor is beatable",
        crumb="How to",
        body=body,
        published="2026-08-11",
        faq=[
            ("Can Docket tell me where a competitor ranks?",
             "No. Docket has no index of the web, so it does not know either site's rankings "
             "and will not guess at them. Every opening it reports is a structural difference "
             "measured by crawling both sites — a rich result they cannot win, a crawler they "
             "have blocked, a question neither of you answers."),
            ("Where do the searches come from?",
             "Google's public autocomplete, which publishes real queries ordered by how "
             "commonly they are typed. That ordering is a popularity signal, not a search "
             "volume. Docket reports the rank a query sat at and does not print a monthly "
             "volume, because it does not have one."),
            ("Does it need an API key or an account?",
             "No. The link-authority comparison reads the Common Crawl hyperlink graph and the "
             "query discovery uses Google's public autocomplete endpoint. Neither needs a key. "
             "Both are capped and rate-limited so a run does not register as load."),
            ("Is this an argument that the competitor is bad?",
             "No, and Docket opens by saying so. It reports the size of their link advantage "
             "first, in a number, precisely so the openings underneath are read as places their "
             "authority does not apply rather than as weaknesses. If their product fits your "
             "job better, buy theirs."),
        ],
    )
