#!/usr/bin/env python3
"""Brand consistency — the question no crawler asks.

The brand lane is the most differentiated thing in the product and had no page
at all. Every figure comes from site/_data/brand.json via facts.py, generated
by scripts/collect_brand.py against real companies.

This page previously withheld the typeface median, because Docket read inline
`<style>` only and the count was structurally zero on 9 of 16 sites — a median
across a sample where the question could not be asked reports blindness as
tidiness. Docket now fetches linked stylesheets and the CSS is readable on all
16, so the figure is published and the section says what replaced the old
colour-count rule and why it died.
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
design review. Docket has a whole lane for it, and on
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
<li><strong>Typography and colour</strong> — how many typefaces the pages ship, and which
colours in your CSS are indistinguishable from each other.</li>
<li><strong>Positioning</strong> — whether the pages make a consistent claim about what the
company does, or a different one each time.</li>
<li><strong>Voice</strong> — whether the reading level and sentence length hold steady across
the site or lurch between pages written years apart.</li>
<li><strong>Social consistency</strong> — the <code>sameAs</code> finding above.</li>
</ul>

<p>The lane is weighted lightly in the score on purpose. An inconsistent wordmark is a real
problem and it is not a <code>noindex</code>; it should never dominate a grade.</p>

<h2>Two colours nobody can tell apart</h2>

<p>Docket fetches the stylesheets your pages link, deduplicated across the crawl, and counts
the typefaces and colours they actually declare. The median site in this sample ships
{F.brand_median_typefaces():.0f} typefaces; the widest ships {F.brand_max_typefaces()}.</p>

<p>What it reports about colour is not palette size. It used to be — anything over 24 distinct
values — and that rule died the moment Docket could see real stylesheets, because one very
well-run site came back with 485. Every shade ramp, every semantic token, every dark-mode
pair. The old finding claimed a wide palette meant colours were being written as literals
instead of referenced from a shared set, and the data says the reverse: a centralised design
system declares <em>more</em> values precisely because it is centralised.</p>

<p>So the count is gone rather than re-tuned, because raising a threshold until the false
positives stop is fitting the rule to the sample. What Docket reports instead is groups of
colours no visitor could tell apart, defined separately — <code>#005fcc</code> and
<code>#0066cc</code> in the same stylesheet. That is what drift actually looks like: a value
gets copied and nudged rather than referenced, and a year later the brand blue has four
spellings. It does not care how big your palette is.
{F.brand_with_drift()} of the {F.brand_drift_frame()} sites had at least one such group.</p>

<p>Getting that right took two corrections worth repeating, because both produced confident
nonsense first. Ignoring the alpha channel made every opacity variant of one colour look like
drift — <code>rgba(0,0,0,.1)</code> is a hairline and <code>rgba(0,0,0,.5)</code> is a scrim,
and treating them as the same put 49 "near-identical pairs" on a 26-colour palette. And
grouping colours by chaining — A is close to B, B to C — walked from a pale lavender to a grey
one indistinguishable step at a time and called them one colour. Every member of a group now
has to be indistinguishable from every other member.</p>

<h2>Where other tools are better than this</h2>

<p>If typography and colour governance is the actual problem you have, a design-system tool
beats an SEO crawler at it and it is not close. Figma's published libraries, a token pipeline,
or a linter running against your own stylesheets all read the source of truth rather than
inferring it from shipped pages, and they catch a drifting value before it is deployed rather
than after. Docket is looking at the outside of the building.</p>

<p>Equally, if you want to know what people are <em>saying</em> about your brand, this is the
wrong category of tool entirely — Docket reads your site and nothing else. It has no mention
tracking, no share-of-voice, no sentiment.</p>

<p>What is genuinely unusual here is only that a technical SEO audit asks the question at all.
<a href="/vs/screaming-frog-alternative/">Screaming Frog</a> and
<a href="/vs/sitebulb-alternative/">Sitebulb</a> are both better crawlers than Docket by several
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

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="brand-consistency",
        title="Brand consistency: the question no SEO crawler asks",
        desc=(f"Of {F.brand_social_frame()} company sites linking social profiles, "
              f"{F.brand_social_undeclared()} declared none in schema. What a brand "
              f"consistency audit checks, and where design tools do it better."),
        h1="Brand consistency: the question no crawler asks",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Brand consistency',
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
             "the page. Docket runs six brand checks as one of its lanes. If typography and "
             "colour governance is your real problem, though, a design-system tool reads your "
             "tokens directly and will beat any crawler at it."),
            ("Why does my audit say typefaces were not measured?",
             "Docket fetches the stylesheets your pages link, so this is now uncommon. It "
             "happens when the sheets could not be fetched, or when you ran with --offline, "
             "which deliberately makes no third-party calls and so skips styles served from "
             "an asset domain. The notice says which, and exists so a silent check is not "
             "mistaken for a clean one — it is a gap in the tool, not a finding about you."),
            ("What is brand colour drift?",
             "Two colours close enough that nobody could tell them apart, defined separately "
             "in your CSS — #005fcc and #0066cc, say. It happens when a value is copied and "
             "nudged rather than referenced from a shared custom property, and it compounds. "
             "Palette size is not the issue: a design system legitimately defines hundreds of "
             "values, and two of them being the same colour is still a mistake."),
        ],
    )


BUILDERS = [brand_consistency]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
