#!/usr/bin/env python3
"""sameAs and entity resolution, from a fresh first-party measurement.

Numbers come from site/data/entity-2026-08.json, collected by fetching each
Index site's homepage once and reading its JSON-LD. The dataset ships with the
article so anyone can re-run it and disagree.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "site" / "data" / "entity-2026-08.json"


def _m() -> dict:
    d = json.loads(DATA.read_text())
    s = d["summary"]
    return {
        "n": s["reachable"],
        "attempted": s["attempted"],
        "org": s["org_schema"],
        "same": s["same_as"],
        "org_no_same": s["org_without_same_as"],
        "pct_same": round(100 * s["same_as"] / s["reachable"]),
        "pct_org": round(100 * s["org_schema"] / s["reachable"]),
        "pct_org_no_same": round(100 * s["org_without_same_as"] / s["org_schema"]),
        "cats": s["by_category"],
        "collected": d["collected"],
    }


def _table(m: dict) -> str:
    order = ["seo-tools", "news", "saas", "local", "ecommerce", "nonprofit", "reference"]
    label = {"seo-tools": "SEO tools", "news": "News &amp; media", "saas": "SaaS",
             "local": "Local business", "ecommerce": "Ecommerce",
             "nonprofit": "Nonprofit", "reference": "Reference"}
    rows = ""
    for key in order:
        c = m["cats"].get(key)
        if not c:
            continue
        rows += (f"<tr><td>{label[key]}</td><td>{c['same_as']} / {c['n']}</td>"
                 f"<td>{c['pct_same_as']:.0f}%</td></tr>")
    return ('<div class="wrap-tbl"><table class="cmp"><thead><tr><th>Category</th>'
            "<th>Declaring <code>sameAs</code></th><th>Share</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>")


def entity_sameas() -> Path:
    m = _m()
    body = f"""
<p class="lede"><code>sameAs</code> is the schema.org property that tells a search engine or
a language model that this website, that LinkedIn page and that Wikipedia entry are all the
same organisation. It is the cheapest entity signal available — a list of URLs you already
own — and <strong>{100 - m['pct_same']}% of the {m['n']} major sites we measured do not have
it.</strong></p>

<p>We fetched the homepage of every site in the Scout Index on {m['collected']}, pulled out
the JSON-LD, and looked for two things: an Organization-family type, and a
<code>sameAs</code> property. {m['org']} sites ({m['pct_org']}%) declare an organisation.
Only {m['same']} ({m['pct_same']}%) declare <code>sameAs</code>.</p>

<p>The gap between those numbers is the interesting part. {m['org_no_same']} sites —
{m['pct_org_no_same']}% of everyone who bothered with Organization schema at all — went to
the trouble of describing themselves as an organisation and then omitted the one property
that connects that description to anything else.</p>

{_table(m)}

<h2>What the property actually does</h2>

<p>A search engine reading your homepage knows a company exists at your domain. It does not
know whether that company is the one with 40,000 LinkedIn followers, the one in a Wikipedia
article, or the one with a Google Business Profile two miles away. Those are four separate
entities until something joins them.</p>

<p><code>sameAs</code> is that something. It is an array of URLs that are you, elsewhere:</p>

<pre><code>{{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Acme Roofing",
  "url": "https://acmeroofing.com",
  "sameAs": [
    "https://www.linkedin.com/company/acme-roofing",
    "https://www.facebook.com/acmeroofing",
    "https://en.wikipedia.org/wiki/Acme_Roofing"
  ]
}}</code></pre>

<p>Two things follow. Knowledge panels get their social links from resolved entity data, and
a language model asked to name a supplier is more likely to reach a business it can pin to a
real organisation than one that is only a domain.</p>

<h2>Why the reference category is at the bottom</h2>

<p>Reference sites came last at {m['cats'].get('reference', {}).get('pct_same_as', 0):.0f}%,
which looks wrong until you think about who they are. Wikipedia and its peers <em>are</em>
the entity graph — they are what everyone else's <code>sameAs</code> points at. They have
less to gain by pointing outward.</p>

<p>SEO tools came top at {m['cats'].get('seo-tools', {}).get('pct_same_as', 0):.0f}%, which
is the least surprising number in the table and worth stating anyway: the people who sell
advice about this take it.</p>

<h2>Getting it wrong</h2>

<p>Three failure modes, in rough order of frequency.</p>

<p><strong>Linking profiles in the footer and never declaring them.</strong> The commonest by
far. The site links Facebook and Instagram from every page, and the schema mentions neither,
so the evidence is sitting there unused. Scout reports this specifically because the fix is
copying URLs you already have into an array.</p>

<p><strong>Listing pages you do not control.</strong> <code>sameAs</code> means "this is also
me". A news article about you is not you; that is <code>subjectOf</code>. Padding the array
with press mentions weakens the signal rather than strengthening it.</p>

<p><strong>Burying it where nothing looks.</strong> Entity markup belongs on the homepage,
which is what resolves the site's primary entity. Our measurement only read homepages for
exactly this reason — a site declaring <code>sameAs</code> on an About page and nowhere else
counts as absent here, and that is also roughly how it looks to something trying to work out
who owns the domain.</p>

<h2>The other half of the problem</h2>

<p>Machines also learn your name from your title tags, your <code>og:site_name</code> and your
logo's alt text. When those disagree — and they disagree more often than anyone expects,
usually because a tagline crept into one of them — a knowledge panel, a shared link preview
and an AI citation can each show a different name for the same company. <code>sameAs</code>
connects your entity to the world; consistent naming is what makes the entity coherent in the
first place. Scout checks both.</p>

<h2>Where another tool is better</h2>

<p>For validating that one page's markup parses and is eligible for rich results, use
Google's own Rich Results Test. It is authoritative in a way no third-party tool can be,
because it is the parser that actually decides. Scout tells you which pages across a whole
site are missing the markup and what it costs you; it does not adjudicate eligibility, and
anything claiming to is guessing at someone else's parser.</p>

<p>For finding <em>which</em> external profiles and mentions exist to point at in the first
place, <a href="/vs/ahrefs-site-audit-alternative/">Ahrefs</a> has a web-scale index and
Scout does not. That is a genuine difference in kind, not a feature gap we intend to close.</p>

<h2>Checking yours</h2>

<ol>
<li>Open your homepage source and search for <code>sameAs</code>. Absent is the common case.</li>
<li>List every official profile you actually control.</li>
<li>Put them in the array, on the homepage, inside your Organization node.</li>
</ol>

<p>It takes about ten minutes and it is the highest ratio of entity signal to effort available
to a small site. <a href="/data/entity-2026-08.json">The dataset behind this page</a> lists
every site measured, so you can check our arithmetic.</p>

<p><a class="btn" href="/#download">Download Scout</a></p>
"""
    return render(
        cat="learn", slug="sameas-entity-signals",
        title=f"sameAs: the entity signal {100 - m['pct_same']}% of major sites skip",
        desc=(f"sameAs tells search engines and language models that your site, your LinkedIn "
              f"and your Wikipedia entry are one organisation. We measured {m['n']} major "
              f"sites: {m['pct_same']}% declare it. What it does and how to add it."),
        h1="sameAs, and why half the web skips it",
        crumb='<a href="/">Scout</a> / <a href="/learn/">Learn</a> / sameAs and entities',
        body=body,
        faq=[
            ("What does sameAs do in schema.org?",
             "It lists other URLs that represent the same entity — your LinkedIn page, your "
             "Wikipedia article, your Google Business Profile. It lets a search engine or "
             "language model confirm that those accounts and your website are one "
             "organisation rather than several unrelated ones."),
            ("Where should sameAs go?",
             "On the homepage, inside your Organization node. The homepage is what resolves "
             "a site's primary entity, so markup on an About page alone is largely wasted."),
            ("Should I list news articles about my company in sameAs?",
             "No. sameAs means 'this is also me'. An article about you is not you — that is "
             "subjectOf. Padding the array with press mentions weakens the signal."),
        ],
    )


BUILDERS = [entity_sameas]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
