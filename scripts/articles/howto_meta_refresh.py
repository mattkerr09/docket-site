"""Meta refresh: the redirect that answers 200.

Promised on the how-to hub. Sourced from the registered check
`index.meta_refresh` ("Client-side redirects").

Worth a page because the failure is invisibility rather than breakage: the page
answers 200 with a normal body, so status-code tooling reads it as content and
a link pointing at it is not reported as a link to a redirect.

⚠️ The check is a NOTICE on purpose and this page keeps that framing: a static
host often cannot issue a 301 at all, so a refresh stub is sometimes the only
tool available, and calling that an error would be scolding somebody for their
hosting.

⚠️ Deliberately does NOT name or link this site's own rename stub — that URL
must never be submitted for indexing.

No numeric literals and no dates.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def meta_refresh() -> Path:
    body = """
<p class="lede">A meta refresh sends the visitor onward and the browser obeys, so from a chair
it is indistinguishable from a redirect. It is not one. The page answers 200 with a normal body,
which means every tool that reads status codes — including your link checker, including most
audits — sees a page with content on it and moves on.</p>

<h2>What it looks like</h2>

<pre><code>&lt;meta http-equiv="refresh" content="0;url=https://example.com/new-page/"&gt;</code></pre>

<p>A visitor lands, the browser waits the stated interval, and off they go. Nothing is broken.
Nobody complains. That is exactly the problem.</p>

<h2>Why the invisibility is the cost</h2>

<p>A server redirect announces itself in the status line, and everything downstream can act on
it. A meta refresh announces itself only in the body, so:</p>

<ul>
<li><strong>Your link checker says the link is fine.</strong> It is pointing at a 200.</li>
<li><strong>Your redirect report is incomplete</strong>, and you have no way of knowing by how
much — the hops are not in it because they are not hops.</li>
<li><strong>The page is assessed as a destination.</strong> A thin stub with no content gets
judged as a page you wrote badly rather than as a signpost.</li>
</ul>

<p>The damage is not that the visitor fails to arrive. They arrive. It is that your own tooling
quietly stops describing your site accurately, and you keep trusting it.</p>

<h2>The honest caveat, which most advice skips</h2>

<p>Search engines support meta refresh and follow it. A server-side redirect is preferred
because it is faster and unambiguous — but <strong>plenty of hosting cannot issue one</strong>.
Static hosts commonly have no mechanism to return a 301 for a moved page, and on those a refresh
stub is the only tool available.</p>

<p>So this is not a fault to be ashamed of. If you can issue a real redirect, do. If your host
will not let you, a zero-delay refresh stub with a canonical pointing at the new URL is a
reasonable second best, and it is worth knowing that is what you are relying on.</p>

<h2>A delay above zero is a different, worse thing</h2>

<p>Zero means the hop is instant. Anything above it leaves a visitor looking at a page that is
not the page they wanted and is not going to stay — and search engines treat a delayed refresh
as a weaker signal than an immediate one. If you are stuck with a refresh, set it to zero.</p>

<h2>The wrong fixes</h2>

<p><strong>Adding a canonical and considering it handled.</strong> The canonical is worth having
alongside a refresh stub, but it does not make the page a redirect and it does not make the hop
visible to your tooling. Two weak signals are not a strong one.</p>

<p><strong>Swapping it for JavaScript.</strong> A <code>location.replace()</code> in a script
has the same shape and the same invisibility, with the added condition that something has to run
it. If the goal was a redirect a crawler can rely on, this is further from it, not closer.</p>

<h2>Finding them</h2>

<pre><code>curl -s https://example.com/old-page/ | grep -i 'http-equiv'</code></pre>

<p>Check the URLs you moved. Renames and site migrations are where these accumulate, because
each one is created at a moment when somebody is thinking about the new URL rather than about
how the old one will be audited a year later.</p>

<p>If you can replace them with real redirects,
<a href="/how-to/fix-redirect-problems/">the redirect rules are worth getting right too</a>.</p>
"""
    return render(
        cat="how-to", slug="fix-meta-refresh-redirects",
        title="Meta refresh: the redirect your tools cannot see",
        desc=("A meta refresh answers 200, so a link audit reads it as content. What it costs "
              "your site, and when it is the only option your host gives you."),
        h1="Meta refresh: the redirect your tools cannot see",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / meta refresh',
        body=body,
        faq=[
            ("Is a meta refresh bad for SEO?",
             "Search engines support it and follow it, so it is not a broken page. A "
             "server-side redirect is preferred because it is faster and unambiguous. The "
             "bigger cost is that the page answers 200, so link checkers and redirect reports "
             "read it as content and your own tooling stops describing the site accurately."),
            ("Why does my link checker not flag meta refresh redirects?",
             "Because at the HTTP level there is nothing to flag. The page returns 200 with a "
             "normal body; the hop lives in the markup, not the status line."),
            ("What if my host cannot issue a 301?",
             "Then a refresh stub is a reasonable second best, and plenty of static hosting "
             "offers nothing else. Set the delay to zero and add a canonical pointing at the "
             "new URL. It is worth knowing that is what you are relying on."),
            ("Does the delay value matter?",
             "Yes. Zero makes the hop instant. Anything above it leaves the visitor on a page "
             "they did not want, and search engines treat a delayed refresh as a weaker signal "
             "than an immediate one."),
            ("Is a JavaScript redirect better?",
             "No. location.replace has the same shape and the same invisibility to status-code "
             "tooling, and it additionally requires something to run the script. If you want a "
             "redirect a crawler can rely on, that is further away, not closer."),
        ],
    )


if __name__ == "__main__":
    print(meta_refresh())
