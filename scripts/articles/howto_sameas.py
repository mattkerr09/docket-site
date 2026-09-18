"""Not every social link on a site belongs to the site.

Promised on the how-to hub. Sourced from the registered check
`brand.social_consistency`, whose docstring records the miss this is built on:
on a newsroom, every social link found was a reporter's own account or a cited
source, and the finding told the organisation to declare them as its own
identity — with a pasteable snippet naming a private individual's profile.

⚠️ THE NEWSROOM IS NOT NAMED. The deploy's third-party gate refuses pages
naming sites measured without asking, and the lesson does not need it.

⚠️ The engineering detail is the best part and belongs in the page: filtering
by chrome tags was tried first and fails, because author cards can sit in a
`<footer>` nested inside an `<article>`. Repetition separates them; position
does not.

No numeric literals.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def sameas() -> Path:
    body = """
<p class="lede"><code>sameAs</code> is how you tell a search engine that this website, that
LinkedIn page and that Instagram account are one organisation. It is an identity claim, not a
list of links you happen to have — and the difference matters, because the wrong entry is worse
than a missing one.</p>

<h2>The advice that would have caused harm</h2>

<p>A tool crawls a newsroom, collects every social link it finds, and reports that those
profiles are missing from the organisation's <code>sameAs</code>. Reasonable-sounding, and
completely wrong: on that site the social links were reporters' own accounts and links to cited
sources. The suggested markup — ready to paste — would have declared a named journalist's
personal profile, and somebody else's video, as the publisher's own identity.</p>

<p>That is not a tidy-up gone slightly astray. A missing <code>sameAs</code> costs you a little
entity evidence. A wrong one asserts that a company and a private individual are the same thing,
in machine-readable form, on the company's own site.</p>

<h2>The two rules that keep the claim honest</h2>

<p><strong>A content permalink is not a profile.</strong> A comment thread, a short video, a
status post — these live on a social host and identify no account. They are things somebody
published, not somebody's identity. Only a profile URL can be a <code>sameAs</code>.</p>

<p><strong>A profile you own appears across the site, because it sits in the template.</strong>
Your accounts are in the footer, so they turn up on every page crawled. A reporter's account
appears on that reporter's articles. A cited source appears once. The ones that belong to the
organisation are the ones that repeat.</p>

<h2>Why position does not work and repetition does</h2>

<p>The obvious filter is structural: ignore links inside the header and footer, keep the rest —
or the reverse. It fails on real sites. That newsroom nests its author cards inside a
<code>&lt;footer&gt;</code> element that sits within each <code>&lt;article&gt;</code>, so the
byline links are inside a boilerplate tag and survive any filter keyed on position.</p>

<p><strong>Repetition separates them and position does not.</strong> It is worth knowing as a
general habit: when you need to tell a site's own furniture from its content, count how often
something appears rather than reasoning about where it sits. Markup is a weaker signal of intent
than frequency, because the markup is whatever the theme author chose and the frequency is what
the site actually does.</p>

<h2>Checking yours</h2>

<p>Look at the <code>sameAs</code> block in your organisation markup and ask of each entry:
is this a profile, and is it ours? Then look at what you are <em>missing</em> — the accounts in
your own footer that never made it into the markup are the ones worth adding, and they are
usually the whole answer.</p>

<h2>What an audit cannot settle</h2>

<p>Whether an account belongs to you. A crawler sees a URL on a page; it does not know your org
chart, your agency relationships, or which of two similarly-named accounts is the real one. A
tool can tell you which links repeat across the site, and that is a strong hint — it is not
ownership, and anything that presents it as ownership is inviting you to publish a claim about
somebody else.</p>

<p>This check was wrong in exactly that direction before the two rules above were added. A page
citing a check is worth more for saying so than for implying the check has always been right.</p>
"""
    return render(
        cat="how-to", slug="fix-sameas-that-claims-the-wrong-accounts",
        title="Not every social link on your site is yours",
        desc=("A wrong sameAs entry is worse than a missing one. What an audit of your site "
              "can tell you about social profiles, and what it must not claim."),
        h1="Not every social link on your site is yours",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / sameAs',
        body=body,
        faq=[
            ("What is sameAs for?",
             "It tells search engines that a website and a set of social profiles are one "
             "organisation. It is an identity claim rather than a list of links you happen to "
             "have on the page."),
            ("Is a missing sameAs worse than a wrong one?",
             "No — the other way round. A missing entry costs a little entity evidence. A "
             "wrong one asserts in machine-readable form that your company and somebody else, "
             "possibly a private individual, are the same thing."),
            ("Can I use a link to a post or a video?",
             "No. A comment thread, a short video or a status post lives on a social host and "
             "identifies no account. It is something somebody published, not somebody's "
             "identity. Only profile URLs belong in sameAs."),
            ("How do I tell my own accounts from other people's?",
             "Count how often each appears. Your accounts sit in the template, so they turn up "
             "across the crawl; an author's account appears on that author's articles and a "
             "cited source appears once."),
            ("Why not just ignore links in the header and footer?",
             "Because position is unreliable. Author cards are sometimes nested in a footer "
             "element inside each article, so byline links sit inside a boilerplate tag and "
             "survive that filter. Repetition separates them; position does not."),
        ],
    )


if __name__ == "__main__":
    print(sameas())
