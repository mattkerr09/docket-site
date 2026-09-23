"""A caveat is not a gate — findings that fire on pages doing the right thing.

Promised on the how-to hub. Sourced from two registered checks whose docstrings
record the same defect, a week apart, in different lanes:

  * `index.noindex` reported twenty-one of twenty-five crawled pages as blocked
    from indexing, at HIGH — every one a form confirmation under a thank-you
    path, which is exactly where noindex belongs. The finding's own fix text
    already said legitimate noindex targets are fine, and it fired anyway.
  * `local.nap`'s phone branch read one number per branch on a multi-site
    retailer as inconsistency and advised collapsing to one, which would have
    removed the per-branch numbers local ranking depends on. Its own text
    already conceded "separate department or location numbers are fine".

⚠️ THE THIRD CASE IS THE CONTROL AND MUST STAY — the missing-address branch
sits at MEDIUM with its caveat stated, because a service-area business's lack
of a street address genuinely cannot be detected. The page's argument is the
DISTINCTION: gate when the exception is detectable, caveat only when it is not.

⚠️ MUST NOT CONTRADICT /how-to/stop-indexing-site-search-and-cart-pages/, which
tells readers utility pages should NOT be indexable. That is the inverse
problem and the page cross-links it explicitly.

⚠️ NO SITE IS NAMED — third-party gate.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def caveat_gate() -> Path:
    body = """
<p class="lede">An audit flags a page. You read the finding, and halfway down its own advice is a
sentence explaining that your case is probably fine. The tool knew the exception, wrote it down,
and reported you anyway — leaving you to filter its list by hand. <strong>A caveat is not a
gate</strong>, and a finding that needs one has not finished being written.</p>

<h2>Nearly every flagged page was correct</h2>

<p>On an insurer's site, twenty-one of twenty-five crawled pages were reported as blocked from
indexing, at the second-highest severity. Every one was a form confirmation sitting under a
thank-you path — pages that are <em>supposed</em> to carry noindex, because nobody should arrive
at a confirmation from a search result.</p>

<p>The check's fix text already said so, in those words: legitimate noindex targets such as cart,
checkout, thank-you and internal search results are fine. So the tool had the rule. It simply did
not apply it before deciding what to report.</p>

<p>The cost is not the reading time. <strong>Reporting correct pages at high severity teaches
somebody to skip the check</strong> — and a skipped check costs more than the occasional real
noindex it would have caught, because the real one is the whole reason the check exists.</p>

<h2>The advice that would have removed working signals</h2>

<p>A week earlier, in a different part of the same tool, the same defect. A retailer with many
shops publishes a phone number beside each branch address on its store locator. That is correct
practice, and it is how a search engine matches each branch to its listing.</p>

<p>The check counted the numbers, called the site inconsistent, and advised using one number
site-wide. <strong>Following it would have deleted the per-branch numbers that local ranking
depends on.</strong> And once more, the finding's own text had already conceded the case:
separate department or location numbers are fine.</p>

<p>The repair in both places was the same — turn the sentence into a condition. Before reporting a
noindex page, check whether its URL is one of the paths where noindex belongs. Before reporting
several phone numbers, check whether the site has several sets of premises.</p>

<h2>When a caveat is the honest answer</h2>

<p>This is the distinction that makes the rule usable, and it is why "never write a caveat" would
be wrong advice.</p>

<p>The same check reports a local business with no street address at a lower severity, with its
caveat stated plainly — because a service-area business legitimately has no address, and
<em>nothing in the markup can tell the two apart</em>. There is no condition to write. Stating the
limit and lowering the severity is the honest thing to do.</p>

<p>So the test is not whether an exception exists. It is:</p>

<ul>
<li><strong>Can the tool detect the exception?</strong> A URL segment, a store locator, a second
address, a noindex on a checkout path — all detectable. Then it must be a gate, and a finding that
fires anyway is a defect.</li>
<li><strong>Or is the exception invisible from the outside?</strong> Then a stated caveat at a
lower severity is correct, and the reader is the one who can resolve it.</li>
</ul>

<p><strong>A caveat at high severity is the combination that should not exist</strong> — it is a
tool saying "this is urgent, and it may not apply to you" in one breath.</p>

<h2>The detail that makes a gate work or fail</h2>

<p>Worth a paragraph because it is where these fixes usually go wrong. The list of paths where
noindex belongs is matched against whole URL segments, with any file extension stripped first.
Both halves were paid for:</p>

<ul>
<li><strong>Substring matching is too greedy.</strong> Matching path fragments anywhere in a URL
put six local-business findings on a video editing site, because the fragments appeared inside
longer words.</li>
<li><strong>Extensions hide the segment.</strong> A path ending in <code>.html</code> is not the
word before it until the extension comes off, which only surfaced when a test served a real file
rather than a tidy path.</li>
</ul>

<h2>Reading this on your own report</h2>

<ul>
<li><strong>Read the fix text before the headline.</strong> If it contains "are fine",
"legitimate", "unless" or "separate … are fine", check whether your case is the one it names. If
it is, the finding is wrong and no work is owed.</li>
<li><strong>Look at what fraction of the flagged pages are exceptions.</strong> When nearly all
of them are, the finding is describing your site's design rather than a fault in it.</li>
<li><strong>Do not silence the check — check the residue.</strong> In the insurer's case four
pages were not confirmations, and those four were the only ones worth a minute.</li>
</ul>

<h2>When the finding is real and urgent</h2>

<p>Keep the severity in view. A noindex on a page that should rank is one of the most expensive
single defects there is, because the page is invisible while looking perfectly healthy to a
visitor. The cases that matter:</p>

<ul>
<li><strong>Noindex on a product, service or article page</strong> — usually left over from a
staging environment.</li>
<li><strong>Noindex on a whole section</strong>, which is a template-level mistake and therefore
one edit. For why the count in that finding is not the number of fixes, see
<a href="/how-to/read-findings-that-blame-the-whole-site/">when a finding blames the whole
site &rarr;</a>.</li>
</ul>

<p>And the opposite problem is real too: utility pages that are <em>missing</em> their noindex and
end up competing with your own content —
<a href="/how-to/stop-indexing-site-search-and-cart-pages/">stop indexing site search and cart
pages &rarr;</a>. Both pages are about the same set of URLs; the question is only which way round
yours are wrong.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Removing noindex from confirmation pages to clear the finding.</strong> You have
added a set of thin, duplicate, un-navigable pages to the index to satisfy a false positive.</li>
<li><strong>Collapsing branch phone numbers to one.</strong> The finding was wrong and the fix is
subtractive — see also
<a href="/how-to/sitemap-urls-that-are-not-stale/">when "regenerate your sitemap" is
wrong &rarr;</a>.</li>
<li><strong>Turning the check off.</strong> Which is what the tool is training you to do, and the
reason this defect is worth naming rather than tolerating.</li>
</ul>

<h2>Where this sits in an audit</h2>

<p>The registered checks are <code>index.noindex</code>, which covers pages blocked from indexing,
and <code>local.nap</code>, which covers name, address and phone consistency. Both now gate on
the exception their own advice describes.</p>
"""
    return render(
        cat="how-to", slug="findings-that-flag-correct-pages",
        title="A caveat is not a gate: findings that flag correct pages",
        desc=("When an audit's own advice says your case is fine, the finding should not have "
              "fired. Two cases where a site was flagged for being right."),
        h1="A caveat is not a gate",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / False positives',
        body=body,
        faq=[
            ("My audit flags my thank-you pages as blocked from indexing. Is that a problem?",
             "No. Confirmation, cart, checkout and internal search pages are supposed to carry "
             "noindex. A tool that reports them has not applied the exception its own advice "
             "describes."),
            ("Should a multi-branch business use one phone number everywhere?",
             "No. A number beside each branch address is correct practice and is how each "
             "location gets matched to its listing. Collapsing them to one removes a signal "
             "rather than tidying it."),
            ("Is it ever right for a finding to state a caveat instead of filtering?",
             "Yes, when the exception cannot be detected from the outside — a service-area "
             "business with no street address, for example. Then the honest form is a stated "
             "limit at a lower severity."),
            ("How do I tell a false positive from a real noindex problem?",
             "Look at what kind of page it is. Confirmation and utility paths are correct; a "
             "product, service or article page carrying noindex is one of the most expensive "
             "defects there is."),
            ("Should I turn off a check that keeps flagging correct pages?",
             "No, but do not work through its list either. Read the residue — the flagged pages "
             "that are not exceptions — because those are the only ones the check was really "
             "for."),
        ],
    )


if __name__ == "__main__":
    print(caveat_gate())
