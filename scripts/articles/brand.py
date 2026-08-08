#!/usr/bin/env python3
"""Brand consistency — the question no crawler asks.

The brand lane is the most differentiated thing in the product and had no page
at all. Every figure comes from site/_data/brand.json via facts.py, generated
by scripts/collect_brand.py against real companies.

One figure is deliberately absent. Scout reads typefaces from inline `<style>`
only, so on a site serving linked stylesheets the count is structurally zero
rather than genuinely low. A median across a sample where the question could
not be asked would report blindness as tidiness, so the article publishes how
often it could be asked instead, and says why.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import N_LANES, render  # noqa: E402


def brand_consistency() -> Path:
    body = f"""
<p class="lede">A crawler asks whether a machine can read your page. None of them ask whether
a person moving between your pages sees the same company each time — which is the question a
brand owner actually has, and it falls straight down the gap between the SEO tool and the
design review. Scout has a whole lane for it, and on
<strong>{F.brand_social_undeclared()} of {F.brand_social_frame()}</strong> real company sites
we measured, the machine-readable version of "this is us" was simply missing.</p>

<h2>The finding that is not a matter of taste</h2>

<p>Most brand questions are judgement calls. This one is not: either your
<code>Organization</code> schema declares your social profiles in <code>sameAs</code> or it
does not.</p>

<p>Of {F.brand_sites()} sites measured on {F.brand_measured()},
{F.brand_social_frame()} linked at least one social profile in their footer — the only ones
that <em>can</em> fail this, since a site linking none cannot fail to declare them. Of those,
{F.brand_social_undeclared()} declared none of them in schema. That is
{F.brand_social_pct()}%, and with a denominator of {F.brand_social_frame()} the honest range is
<strong>{F.brand_social_interval()}</strong> — wide, because eleven is not many. Treat it as
"most of them", not as a rate.</p>

<p>Why it matters is specific rather than vague. <code>sameAs</code> is how you tell Google
that the Instagram account, the LinkedIn page and the Wikipedia entry are all the same entity
as the website. It is a
<a href="https://developers.google.com/search/docs/appearance/structured-data/organization">documented
Organization property</a>, and it is one of the inputs to a knowledge panel. Linking a profile
in your footer says it to a human. Declaring it in schema says it to the machine that decides
whether you are an entity at all.</p>

<p>It is also about ten minutes of work, which is the interesting part: this is not a hard
problem that companies have weighed and deprioritised. It is a cheap one nobody's tool
mentioned.</p>

<h2>What the lane actually checks</h2>

<p>Six checks, one of {N_LANES} lanes. Each is a counted fact rather than an opinion, because
"four typefaces across nine pages" is something you can verify and "the typography is
inconsistent" is something you can only agree or disagree with.</p>

<ul>
<li><strong>Name consistency</strong> — whether your title tags, <code>og:site_name</code>,
<code>Organization</code> schema and logo alt text call the company the same thing.</li>
<li><strong>Logo</strong> — whether the logo's alt text names the company.
{F.brand_logo_unnamed()} of the sites we measured had a logo whose alt text did not.</li>
<li><strong>Typography and colour</strong> — how many typefaces and brand colours the pages
ship. See the limitation below; it is a real one.</li>
<li><strong>Positioning</strong> — whether the pages make a consistent claim about what the
company does, or a different one each time.</li>
<li><strong>Voice</strong> — whether the reading level and sentence length hold steady across
the site or lurch between pages written years apart.</li>
<li><strong>Social consistency</strong> — the <code>sameAs</code> finding above.</li>
</ul>

<p>The lane is weighted lightly in the score on purpose. An inconsistent wordmark is a real
problem and it is not a <code>noindex</code>; it should never dominate a grade.</p>

<h2>Where this is weak, and it is weak</h2>

<p>Scout counts typefaces and colours from CSS written inline in the page. It does not fetch
linked stylesheets. On {F.brand_sites()} real companies it could read the CSS on
<strong>{F.brand_css_readable()}</strong> of them — the rest serve their styles from
<code>.css</code> files, which is the normal and correct way to build a site, and Scout
therefore has nothing at all to look at.</p>

<p>That was worse than it sounds until recently, because the check simply said nothing in that
case, and a silent check reads exactly like a clean one. It now reports that the count could
not be taken, at NOTICE, and says the gap is the tool's rather than the site's. Fetching
stylesheets properly is the actual fix and it is not built yet.</p>

<p>So the numbers that survive from that check are only about the sites where it could see:
the widest was {F.brand_max_typefaces()} typefaces, and one site shipped
{F.brand_max_colours()} distinct colour values. Both are counts of what was served, not
verdicts — a site with six typefaces may have meant every one of them.</p>

<h2>Where other tools are better than this</h2>

<p>If typography and colour governance is the actual problem you have, a design-system tool
beats an SEO crawler at it and it is not close. Figma's published libraries, a token pipeline,
or a linter running against your own stylesheets all read the source of truth rather than
inferring it from shipped pages, and they catch a drifting value before it is deployed rather
than after. Scout is looking at the outside of the building.</p>

<p>Equally, if you want to know what people are <em>saying</em> about your brand, this is the
wrong category of tool entirely — Scout reads your site and nothing else. It has no mention
tracking, no share-of-voice, no sentiment.</p>

<p>What is genuinely unusual here is only that a technical SEO audit asks the question at all.
<a href="/vs/screaming-frog-alternative/">Screaming Frog</a> and
<a href="/vs/sitebulb-alternative/">Sitebulb</a> are both better crawlers than Scout by several
measures, and neither will tell you your logo alt text does not name your company.</p>

<h2>The one to fix this afternoon</h2>

<p>Take the social links out of your footer, and put them in your
<code>Organization</code> schema:</p>

<pre><code>{{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Your Company",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "sameAs": [
    "https://www.linkedin.com/company/yourcompany",
    "https://www.instagram.com/yourcompany",
    "https://en.wikipedia.org/wiki/Your_Company"
  ]
}}</code></pre>

<p>Then check the alt text on your logo actually says your company's name. Between them that is
most of an afternoon's worth of the findings above, and both are the kind of thing that stays
broken for years because no tool was looking.</p>

<p><a class="btn" href="/download/">Download Scout</a></p>
"""
    return render(
        cat="learn", slug="brand-consistency",
        title="Brand consistency: the question no SEO crawler asks",
        desc=(f"Of {F.brand_social_frame()} company sites linking social profiles, "
              f"{F.brand_social_undeclared()} declared none in schema. What a brand "
              f"consistency audit checks, and where design tools do it better."),
        h1="Brand consistency: the question no crawler asks",
        crumb='<a href="/">Scout</a> / <a href="/learn/">Learn</a> / Brand consistency',
        body=body,
        published="2026-08-07",
        faq=[
            ("What is a brand consistency audit?",
             "A check of whether a site presents one company rather than several: the same "
             "name in its titles, its Organization schema, its og:site_name and its logo alt "
             "text; a consistent claim about what the business does; and social profiles "
             "declared in schema rather than only linked in the footer. It is a different "
             "question from whether a crawler can read the page, which is what SEO tools "
             "normally check."),
            ("What is sameAs in schema markup?",
             "A property of Organization schema listing the other places on the web that are "
             "the same entity — your LinkedIn, Instagram, Wikipedia entry. It is how a search "
             "engine knows those accounts and your website are one organisation, and it is an "
             "input to knowledge panels. Linking a profile in your footer tells a human; "
             "sameAs tells the machine."),
            ("Do SEO tools check brand consistency?",
             "Crawlers generally do not — they answer whether a machine can read and index "
             "the page. Scout runs six brand checks as one of its lanes. If typography and "
             "colour governance is your real problem, though, a design-system tool reads your "
             "tokens directly and will beat any crawler at it."),
            ("Why does my audit say typefaces were not measured?",
             "Because Scout reads typefaces from CSS written inline in the page and does not "
             "fetch linked stylesheets, so on most sites it has nothing to look at. That "
             "notice exists so a silent check is not mistaken for a clean one — it is a gap "
             "in the tool, not a finding about your site."),
        ],
    )


BUILDERS = [brand_consistency]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
