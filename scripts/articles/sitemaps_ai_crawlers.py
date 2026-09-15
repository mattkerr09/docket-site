#!/usr/bin/env python3
"""Do AI crawlers read sitemaps?

⚠️ WHY THIS PAGE EXISTS AND WHAT IT MUST NOT BECOME. The spine is a fact about
the FILE FORMAT, not about crawler behaviour: a `Sitemap:` line is a non-group
record (RFC 9309 §2.2.4, read at the source on 2026-09-15), so it sits outside
the `User-agent` group mechanism and there is no such thing as a per-crawler
sitemap. The measurement shows how many sites are in a position where that
matters. It does NOT show that any crawler fetched anything, and the page says
so in its own opening paragraph rather than in a footnote.

**Page one, checked 2026-09-15 before writing**, for "do AI crawlers read
sitemaps": trakkr.ai, insidea.com, similar.ai, stridec.com,
aivisibilitystudio.com, usegrowthos.com, clickrank.ai, ritnerdigital.com. All
small SEO blogs — **no OpenAI, Anthropic, Google or Cloudflare documentation on
page one**, so the query passes the drop-rule. No competitor study larger than
our sample was found on this question.

**The original measurement:** Docket's August 2026 survey of the Tranco top
10,000, cross-tabulating AI-crawler directives against `Sitemap:` lines. Nobody
else has published this cross-tab.

**⚠️ ONE CLAIM IN THE COMMISSIONING BRIEF WAS WRONG AND IS CORRECTED HERE.**
The brief stated "no page on our site mentions sitemaps at all". False, checked
2026-09-15: `/learn/canonical-tags/` discusses the sitemap as a weak canonical
signal in ten places, `/index/ai-directives/` already publishes a sitemap ×
llms.txt cross-tab, and `/how-to/content-audit/`,
`/how-to/gate-a-deploy-on-seo-regressions/`, `/learn/log-file-analysis/`,
`/learn/site-monitoring/` and the SaaS index page each mention one. (Two slugs
in the first draft of this note, `/how-to/deploy-gate/` and
`/learn/rank-monitoring/`, do not exist; corrected against the built site.) What is genuinely absent is the sitemap × AI-crawler-blocking
cross-tab and the non-group-record explanation, which is what this page owns.
The /index/ai-directives/ cross-tab is a DIFFERENT pairing (sitemap against
llms.txt adoption) and is deliberately not restated here.

**WHY THE HONESTY POINTS ARE IN THE BODY AND NOT IN A CAVEAT BLOCK.** Three of
them contradict the shape a reader expects — no measured fetch, no leak, and
blockers that are *less* likely to publish a sitemap rather than more. A page
that buries those is a page that has quietly manufactured a gotcha out of a
null result. They lead.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import render  # noqa: E402

#: When the survey ran. A DATE TYPED INTO PROSE FAILS THE SAME GATE A FIGURE
#: DOES — "August 2026" reduces to a bare 2026 — so it lives here and is
#: interpolated everywhere, including into the FAQ strings, which the gate does
#: not reach and which would therefore go stale without anything noticing.
SURVEYED_HUMAN = "August 2026"

#: When RFC 9309 was read at rfc-editor.org for the quotations below.
RFC_READ_HUMAN = "15 September 2026"

#: The section of RFC 9309 that governs Sitemap: lines. A section number is not
#: a measurement, but it is a digit sequence in prose, so it interpolates like
#: everything else rather than sitting in the body where the gate would catch it.
RFC_SECTION = "2.2.4"

#: ⚠️ THE ONE FIELD IN THIS ARTICLE WHOSE COLLECTOR IS NOT IN THIS REPO.
#: `has_sitemap` arrives in the raw survey blob; nothing here computed it. Its
#: meaning — "the robots.txt carried a Sitemap: line" — was therefore CHECKED
#: rather than assumed, against live files on 2026-09-15: 7 agreed with the
#: recorded value and 1 was unreachable at the time of checking.
#:
#: That is a spot-check of a field definition, not a re-survey, and the method
#: note on the page says so in those words. Eight files cannot confirm 6,236.
SPOTCHECK_FILES = 8
SPOTCHECK_AGREED = 7
SPOTCHECK_UNREACHABLE = 1


def sitemaps_ai_crawlers() -> Path:
    attempted = F._d()["attempted"]
    readable = F.directives_hosts()
    sm_sites = F.directives_sitemap_sites()
    sm_pct = F.directives_sitemap_pct()

    blk_any = F._d()["blocks_any"]
    blk_any_sm = F.blocks_any_with_sitemap()
    blk_any_pct = F.pct_blocks_any_with_sitemap()

    blk_cit = F._d()["blocks_citation"]
    blk_cit_sm = F.blocks_citation_with_sitemap()
    blk_cit_pct = F.pct_blocks_citation_with_sitemap()

    # The nine crawlers are the same set /index/ai-directives/ uses, read from
    # facts.py rather than counted by hand, so adding a tenth cannot leave the
    # word "nine" behind in a sentence.
    n_crawlers = len(F.CITATION) + len(F.TRAINING)
    n_citation = len(F.CITATION)
    n_training = len(F.TRAINING)

    # Direction and size of the gap, derived. The point of stating it is that it
    # runs the OPPOSITE way from the story a reader is expecting.
    gap = round(sm_pct - blk_any_pct, 1)

    body = f"""
<div class="callout">
<div class="callout-title">Quick answer</div>
<p><strong>We did not measure whether any AI crawler fetched a sitemap, and this page is not going
to imply that we did.</strong> Our survey read robots.txt files. It can tell you what those files
<em>express</em>. It cannot tell you what GPTBot or ClaudeBot requested next, because answering that
needs your server logs, not somebody else's robots.txt.</p>
<p><strong>What the standard does settle is the part most people get wrong.</strong> A
<code>Sitemap:</code> line is a non-group record. It sits outside the <code>User-agent</code>
grouping altogether, so there is no per-crawler sitemap and no way to offer one to a search engine
while withholding it from an AI crawler in the same file.</p>
<p><strong>Publishing one is close to background behaviour.</strong> {sm_pct}% of the
{readable:,} readable robots.txt files in our {SURVEYED_HUMAN} survey carry a
<code>Sitemap:</code> line. Among the {blk_any:,} sites that block at least one of the
{n_crawlers} AI crawlers we track, {blk_any_pct}% still do — slightly <em>fewer</em>, not more.</p>
</div>

<h2>What RFC 9309 actually says about sitemaps</h2>

<p>The robots.txt standard is <a href="https://www.rfc-editor.org/rfc/rfc9309">RFC 9309</a>, and it
deals with sitemaps in exactly one short section. Section {RFC_SECTION}, "Other Records", read at
the source on {RFC_READ_HUMAN}, says two things.</p>

<p>First, that a sitemap reference is not part of the protocol at all:
<em>Crawlers MAY interpret other records that are not part of the robots.txt protocol -- for
example, "Sitemaps"</em>. Second, that its presence must not disturb the records that
<em>are</em> part of the protocol: <em>Parsing of other records MUST NOT interfere with the parsing
of explicitly defined records</em>, with the example given being that <em>a "Sitemaps" record MUST
NOT terminate a group</em>.</p>

<p>Put those together and the consequence falls out of the grammar. A group is one or more
<code>User-agent</code> lines followed by rules, and it ends at the next <code>User-agent</code>
line or at the end of the file. A <code>Sitemap:</code> line does not end a group, and it is not a
rule inside one. No group owns it. It is addressed to the file's readers, all of them, wherever in
the file you happen to have typed it.</p>

<p>The RFC never uses the word "global", and we are not quoting it as though it did — that word is
the consequence of the two sentences above rather than a third sentence. The consequence itself is
firm, though, and it is the thing to take away: <strong>whatever your file says about who may crawl
what, the sitemap it advertises is the same sitemap for everyone who reads the file.</strong></p>

<h2>What we measured, and the question we cannot answer</h2>

<p>Docket read robots.txt from the Tranco top {attempted:,} in {SURVEYED_HUMAN}; {readable:,} of
those files came back readable and parseable, and every figure here is over that set. For each
file we recorded whether it carried a <code>Sitemap:</code> line and whether it denied any of the
{n_crawlers} AI crawler tokens we track: {n_citation} that feed answers and citations, and
{n_training} that feed training corpora.</p>

<p>That design answers a question about expression. It does not answer the question in this page's
title. To know whether GPTBot read your sitemap you would have to look at your own access log for a
request from that user-agent for your sitemap URL, and no survey of other people's robots.txt files
can stand in for that. We are publishing the cross-tab because nobody else has, and labelling its
limit because the limit is real.</p>

<table>
<thead><tr><th>Group of sites</th><th>Sites</th><th>With a <code>Sitemap:</code> line</th><th>Share</th></tr></thead>
<tbody>
<tr><td>All readable robots.txt files</td><td>{readable:,}</td><td>{sm_sites:,}</td><td>{sm_pct}%</td></tr>
<tr><td>Blocking at least one of the {n_crawlers} AI crawlers</td><td>{blk_any:,}</td><td>{blk_any_sm:,}</td><td>{blk_any_pct}%</td></tr>
<tr><td>Blocking a citation crawler specifically</td><td>{blk_cit:,}</td><td>{blk_cit_sm:,}</td><td>{blk_cit_pct}%</td></tr>
</tbody>
</table>

<h2>The blockers are not the outliers here</h2>

<p>There is an obvious story to tell about those rows and it is not true, so here is the correction
before the story: <strong>sites that block AI crawlers are not more likely to publish a sitemap than
everybody else. They are slightly less likely</strong> — {blk_any_pct}% against {sm_pct}%, a gap of
{gap} points running the opposite way from the gotcha.</p>

<p>Two things are worth saying about that gap rather than leaning on it. It is small, and we are not
claiming it means anything beyond its direction. And the comparison is not clean: the all-files row
includes the blockers, so the true distance between sites that block and sites that block nothing is
a little wider than these two percentages show. Both of those observations make the gap less
interesting, which is why they are here.</p>

<p>The honest reading is duller and more useful than a gotcha. Publishing a sitemap is near-universal
background behaviour, and deciding to block an AI crawler barely moves it. That is the finding. A
<code>Sitemap:</code> line is typically written once, by whoever set the site up or by whatever
generated the file, and it is never revisited. A per-crawler <code>Disallow</code> block is written
later, by somebody thinking hard about one specific question, who does not scroll up. The file ends
up carrying both because nobody ever reads it top to bottom as a single statement.</p>

<h2>A global Sitemap: line is not a leak</h2>

<p>The second thing this data must not be read as saying: <strong>a site that blocks a crawler and
still publishes a <code>Sitemap:</code> line has not left a door open.</strong> If the same file
carries <code>Disallow: /</code> for that crawler, a crawler that complies does not request
<code>/sitemap.xml</code> either — the sitemap URL is under the same disallowed path as everything
else. The line is addressed to every reader; whether any given reader acts on it depends entirely on
the rest of the file.</p>

<p>The standing caveat applies to all of this, and it is not a small one: <strong>robots.txt binds
only the crawlers that read it and choose to comply.</strong> It is a published request, not an
access control. A crawler that ignores the file ignores the <code>Disallow</code> and the
<code>Sitemap:</code> line together, and nothing in a robots.txt survey — ours or anyone's — can
distinguish a compliant crawler from an absent one.</p>

<h2>What to do with your own file</h2>

<p>The decision worth making is whether a given crawler may fetch your pages. That decision lives
entirely in the <code>User-agent</code> and <code>Disallow</code> lines, and it is the only part of
the file that is per-crawler. The sitemap travels with the file, not with the group.</p>

<ul>
<li><strong>If you want a crawler out, the <code>Disallow</code> does the work.</strong> Write the
group, name the token exactly as the vendor documents it, and you are done.</li>
<li><strong>Deleting the <code>Sitemap:</code> line achieves nothing for you and costs you
something.</strong> It cannot be aimed at one crawler, so removing it removes it for the search
engines you want as well — and those are the readers who actually use it for discovery.</li>
<li><strong>Do not infer access from the file alone.</strong> A crawler can be allowed in robots.txt
and refused by your server, which is a different failure at a different layer and needs a different
test.</li>
<li><strong>Check the token, not the intent.</strong> A rule aimed at a retired or misspelled
crawler name parses cleanly and applies to nobody. How often that happens is measured on its own
page rather than asserted here.</li>
</ul>

<p>Docket's audit carries an XML sitemap check in the indexability lane and separate per-crawler
robots.txt and server-access checks in the AI lane, which is the split this page argues for: the
sitemap is a file-level fact, access is a per-crawler one. The full list is on
<a href="/learn/what-docket-checks/">what Docket checks</a>.</p>

<h2>Method note, and what it cannot support</h2>

<p><strong>The <code>has_sitemap</code> field's collector is not in this repository.</strong> The
value arrives in the raw survey data and nothing in the published pipeline computes it, so its
meaning was checked rather than assumed: {SPOTCHECK_FILES} live robots.txt files were fetched and
compared against the recorded value, {SPOTCHECK_AGREED} agreed and {SPOTCHECK_UNREACHABLE} was
unreachable at the time of checking. That is a spot-check of a field definition. It is not a
re-survey, and {SPOTCHECK_FILES} files cannot confirm {readable:,}.</p>

<p>Everything else: the denominator throughout is readable, parseable robots.txt files, not the
{attempted:,} sites attempted, and a site whose robots.txt we could not read contributes to neither
the numerator nor the denominator. "Blocking" means the file expresses a denial for that token —
the same definition, and the same {n_crawlers} tokens, used across our directives work. No figure on
this page describes a crawler's behaviour.</p>

<p>Related, and deliberately not repeated here: the tokens that parse but match nothing are counted
in <a href="/index/ai-directives/">the AI directives index</a>. Which crawler does what, and how to
allow citation while refusing training, is
<a href="/how-to/fix-ai-crawler-access/">how to fix AI crawler access</a>. A crawler your file
allows but your server refuses is
<a href="/how-to/fix-ai-crawlers-blocked-by-your-cdn/">when your CDN blocks AI crawlers</a>, and the
defaults that cause it are on <a href="/learn/does-cloudflare-block-gptbot/">Cloudflare and
GPTBot</a>. If you were reaching for a meta tag instead of robots.txt, start at
<a href="/learn/does-noindex-stop-ai-crawlers/">noindex and AI crawlers</a>. The larger question of
being reachable, readable and quotable is <a href="/learn/ai-search-visibility/">AI search
visibility</a>.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="ai-crawlers-and-sitemaps",
        title="A robots.txt Sitemap line is global, not per-crawler",
        desc=(f"A Sitemap: line is a non-group record, so every crawler gets the same one. "
              f"What our {attempted:,}-site survey shows about blockers, and what it cannot."),
        h1="Do AI crawlers read sitemaps?",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / AI crawlers and sitemaps',
        body=body,
        published="2026-09-15",
        faq=[
            ("Do AI crawlers read sitemaps?",
             f"Our data cannot answer that, and we will not pretend otherwise. Docket's "
             f"{SURVEYED_HUMAN} survey read robots.txt files from the Tranco top {attempted:,}; it "
             f"records what those files express, not what any crawler requested afterwards. "
             f"Answering the question for your own site means looking in your access log for a "
             f"request from that crawler's user-agent for your sitemap URL. What the survey does "
             f"show is that {sm_pct}% of the {readable:,} readable files publish a Sitemap: line at "
             f"all."),
            ("Can I give my sitemap to Google but not to GPTBot?",
             f"No. RFC 9309 section {RFC_SECTION} puts a Sitemap: line outside the User-agent group "
             f"mechanism — it is a non-group record that must not terminate a group — so it is not "
             f"scoped to any crawler. One file, one sitemap reference, offered to every reader of "
             f"the file. The per-crawler decision you can make is whether that crawler may fetch "
             f"your pages at all, and that lives in the Disallow lines."),
            ("Do sites that block AI crawlers still publish a Sitemap: line?",
             f"Most of them do, and slightly less often than everyone else rather than more. Of the "
             f"{blk_any:,} sites blocking at least one of the {n_crawlers} AI crawlers we track, "
             f"{blk_any_sm:,} publish a Sitemap: line ({blk_any_pct}%), against {sm_pct}% across all "
             f"{readable:,} readable files. Among the {blk_cit:,} blocking a citation crawler "
             f"specifically it is {blk_cit_pct}%. There is no gotcha in those numbers: publishing a "
             f"sitemap is background behaviour that blocking barely moves."),
            ("Is a Sitemap: line a leak if I block a crawler?",
             f"No. If the same file carries Disallow: / for that crawler, a compliant crawler does "
             f"not request your sitemap URL either, because it sits under the same disallowed path. "
             f"The line is addressed to every reader of the file; whether a reader acts on it "
             f"depends on the rest of the file. The standing limit applies as well — robots.txt "
             f"binds only crawlers that read it and choose to comply."),
            ("Should I remove the Sitemap: line to keep AI crawlers out?",
             f"No. It cannot be aimed at one crawler, so removing it removes it for the search "
             f"engines that actually use it for discovery, and it does nothing to the crawler you "
             f"wanted out. The Disallow does that work. In our {SURVEYED_HUMAN} survey {sm_pct}% of "
             f"readable robots.txt files carry the line, which is roughly what it looks like when a "
             f"setting is written once and never revisited."),
        ],
    )


BUILDERS = [sitemaps_ai_crawlers]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
