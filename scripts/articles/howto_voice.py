"""When a site reads as though several people wrote it.

Promised on the how-to hub. Sourced from the registered check
`brand.voice_consistency` ("Writing voice consistency"), which measures the
spread of average sentence length across substantial pages.

⚠️ THE SPINE OF THIS PAGE IS THAT THE MEASURE IS A PROXY AND SAYS SO. Sentence
length is a shadow of voice, not voice. The check is LOW severity precisely
because two registers are often correct — a legal notice should not sound like a
landing page — and the page keeps that framing rather than inflating it.

Complements /learn/brand-consistency/ (why crawlers ignore brand at all) and
/how-to/fix-a-site-that-says-something-different-every-page/ (what you say,
rather than how it sounds).

No numeric literals.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def voice() -> Path:
    body = """
<p class="lede">Open three pages of a site written by three people and you can hear it
immediately, without being able to say what you heard. One is clipped and direct. One winds
through subordinate clauses. One was written by whoever had to write it that week. Nothing is
wrong with any of them.</p>

<h2>What can actually be measured</h2>

<p>Not voice. Sentence length — the average per page, and how far those averages sit apart
across the site.</p>

<p>That is a crude thing to count and it works better than it deserves to, because substantial
pages written by one person, or to one style guide, cluster together. A page of short declarative
sentences sitting beside one of long qualified ones is usually legal copy beside marketing copy,
or an agency's work beside the founder's.</p>

<p><strong>It is a proxy, and it is worth being blunt about that.</strong> Sentence length is a
shadow that voice casts. Two pages can share an average and read nothing alike. What the measure
is good for is noticing that a site has more than one register — not telling you what those
registers are, and not telling you which is better.</p>

<h2>Why this is worth knowing and not worth panicking about</h2>

<p>Several voices are frequently correct. Terms of service should not sound like a pricing page.
A technical reference should not sound like a case study. A finding here is an observation, not
a fault, and a tool that reports it as an error is telling you to flatten writing that is doing
its job.</p>

<p>It matters when the pages are supposed to be doing the <em>same</em> job. Two service pages
that read as though they come from different companies make a visitor moving between them do
work that should not exist. Something summarising your site — a person skimming, or a model
writing a sentence about you — has no consistent register to reproduce, and produces the average
of several, which sounds like nobody.</p>

<h2>The wrong fixes</h2>

<p><strong>Rewriting everything to one sentence length.</strong> That is not a voice, it is a
metronome. The measure would improve and the writing would get worse, which is the clearest sign
you are optimising a proxy rather than the thing it stands for.</p>

<p><strong>Running the site through something that homogenises prose.</strong> You will pass and
you will sound like every other site that did the same. The register you end up with is the
average of the internet.</p>

<p><strong>Making the legal pages match the marketing.</strong> They are a different job. Leave
them alone.</p>

<h2>What to do instead</h2>

<p>Group your pages by the job they do, not by where they sit in the navigation. The ones doing
the same job should cohere: the service pages with each other, the guides with each other.
Anything genuinely doing a different job is allowed to sound different, and should.</p>

<p>Then pick one page in each group that sounds right and use it as the reference. Not a style
guide nobody reads — an actual page somebody already wrote, which is the only kind of standard
that survives contact with a deadline.</p>

<h2>What an audit cannot tell you</h2>

<p>Whether your writing is any good. Whether the difference it found is deliberate. Whether the
voice you settled on is the right one for the people you are selling to. Those are judgements,
and a measurement that claimed to make them would be worth less than one that admits it counts
sentences.</p>

<p>The related questions — whether your site says one consistent <em>thing</em>, and why brand
is invisible to crawlers generally — are
<a href="/how-to/fix-a-site-that-says-something-different-every-page/">a different measurement</a>
and <a href="/learn/brand-consistency/">a longer argument</a>.</p>
"""
    return render(
        cat="how-to", slug="fix-a-site-that-sounds-like-several-companies",
        title="When your site sounds like several companies wrote it",
        desc=("Sentence length across your pages is a proxy for one voice. What an audit of "
              "your site can see, what it refuses to judge, and the wrong fixes."),
        h1="When your site sounds like several companies wrote it",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / writing voice',
        body=body,
        faq=[
            ("Can a tool measure writing voice?",
             "Not directly. It can measure the spread of average sentence length across your "
             "pages, which is a proxy: substantial pages written by one person or to one guide "
             "cluster together. Sentence length is a shadow voice casts, not voice."),
            ("Is having more than one voice always a problem?",
             "No, and a check reporting it as an error is telling you to flatten writing that "
             "is doing its job. Terms of service should not sound like a pricing page. It "
             "matters when pages meant to do the same job read as though they came from "
             "different companies."),
            ("Should I rewrite everything to the same sentence length?",
             "That is not a voice, it is a metronome. The measure would improve and the "
             "writing would get worse, which is the clearest sign of optimising a proxy "
             "instead of the thing it stands for."),
            ("What is the practical fix?",
             "Group pages by the job they do rather than by navigation, and make each group "
             "cohere. Then pick one page in each group that already sounds right and use it as "
             "the reference — an actual page survives a deadline in a way a style guide does "
             "not."),
            ("Can an audit tell me if my writing is good?",
             "No. It cannot tell you whether the difference it found was deliberate, or "
             "whether the voice you chose suits the people you sell to. A measurement claiming "
             "to judge that would be worth less than one that admits it counts sentences."),
        ],
    )


if __name__ == "__main__":
    print(voice())
