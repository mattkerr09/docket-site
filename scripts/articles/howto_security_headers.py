#!/usr/bin/env python3
"""Security headers — the last uncovered check from the gap analysis.

Written as a self-audit, because running the shipped 1.1.16 binary against
docketseo.app on 2026-08-14 produced three security findings on this site,
including a HIGH. Verified by hand with curl before writing a word: the apex
really does answer 200 over plain http.

A page about security headers that only showed sites getting it right would be
an advertisement. This one leads with the fact that the site hosting it cannot
set a single one of these headers, because GitHub Pages does not offer the
ability, and says what that means rather than implying otherwise.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def security_headers() -> Path:
    body = """
<p class="lede">Security headers are response headers that tell a browser how carefully to
treat your site. They cost nothing, they are set once at the server or CDN, and most sites
have none of them — including, at the time of writing, this one.</p>

<h2>What an audit of this site returns</h2>

<pre><code>high     security.no_http_redirect    http://docketseo.app does not redirect to https://
low      security.no_hsts             No HSTS header
notice   security.missing_headers     Missing 2 baseline security headers</code></pre>

<p>All three are true. We checked the first by hand before believing it, which is the rule
we apply to findings about anybody else's site:</p>

<pre><code>$ curl -sI http://docketseo.app/
HTTP/1.1 200 OK
Server: GitHub.com</code></pre>

<p>Two hundred, over plain http, with no redirect. The <code>www</code> host redirects
correctly; the apex does not — which is the same half-configured shape Docket found on a
French bakery chain the same week, and the reason its redirect finding now names the exact
host it probed instead of saying "http://".</p>

<h2>The three headers worth having</h2>

<p><strong>Strict-Transport-Security.</strong> Tells the browser to use https for this site
from now on, so a visitor who types the bare domain never makes the plain-http request at
all. Start with a short max-age, confirm nothing breaks, then raise it:</p>

<pre><code>Strict-Transport-Security: max-age=31536000; includeSubDomains</code></pre>

<p><strong>X-Content-Type-Options: nosniff.</strong> Stops the browser guessing that
something you served as text is really a script. One line, no trade-offs.</p>

<p><strong>Referrer-Policy.</strong> Controls how much of the current URL is passed to sites
you link to. <code>strict-origin-when-cross-origin</code> sends the full path within your
own site and only the origin to anyone else — which matters if your URLs contain anything
you would not print on a postcard.</p>

<pre><code>X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin</code></pre>

<h2>Why we have not fixed ours</h2>

<p>Because we cannot. This site is served by GitHub Pages, which does not let you set
response headers. There is no configuration file for it, no setting, and no supported
workaround short of putting a CDN in front of the whole site.</p>

<p>That is a real trade-off and it is the honest reason, not an excuse. Static hosting that
costs nothing and cannot go down in an interesting way is worth a great deal, and the
headers it cannot set are worth less than that. If this site accepted logins or took
payments the calculation would be different and we would be on something else.</p>

<p>The http redirect is a separate matter and it is a hosting setting rather than a header,
so it is fixable. It is on the list.</p>

<h2>Where to actually set them</h2>

<ul>
<li><strong>Cloudflare, Fastly, or any CDN</strong> — a rule at the edge, applied to every
response, no deploy needed.</li>
<li><strong>Nginx</strong> — <code>add_header</code> in the server block.</li>
<li><strong>Apache</strong> — <code>Header set</code> in the vhost or .htaccess.</li>
<li><strong>Netlify, Vercel</strong> — a headers file in the repository.</li>
<li><strong>GitHub Pages</strong> — not possible, as above.</li>
</ul>

<h2>How much does this matter for SEO</h2>

<p>Directly, almost nothing. Google has said https is a lightweight ranking signal and has
never suggested these headers are. Anyone selling you security headers as a ranking factor
is guessing.</p>

<p>Indirectly it matters more than the ranking question. A page reachable over plain http
can be modified between the server and the reader — and on this site, one of those pages
tells people how to verify a signed and notarised binary. Instructions for checking a
signature are exactly the instructions worth tampering with. That is the argument for the
redirect, and it has nothing to do with rankings.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-missing-security-headers",
        title="Fix missing security headers",
        desc=("HSTS, nosniff and Referrer-Policy: what each one does, where to set "
              "it, and why this site fails two of the three checks it is "
              "describing."),
        h1="How to fix missing security headers",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Security headers',
        body=body,
        faq=[
            ("Do security headers help SEO?",
             "Directly, almost nothing. Google treats https as a lightweight ranking "
             "signal and has never suggested these headers are one. The real argument "
             "is that a page reachable over plain http can be modified in transit, "
             "which matters most on pages that tell people how to verify something."),
            ("What is the minimum set of security headers?",
             "Strict-Transport-Security so browsers stop making plain-http requests, "
             "X-Content-Type-Options: nosniff so the browser does not guess content "
             "types, and Referrer-Policy: strict-origin-when-cross-origin so your full "
             "URLs are not handed to every site you link to."),
            ("Can I set security headers on GitHub Pages?",
             "No. GitHub Pages does not support custom response headers and there is no "
             "configuration file for them. The supported route is putting a CDN in "
             "front of the site. This site runs on GitHub Pages and therefore fails "
             "two of these checks itself."),
            ("Should HSTS max-age start high?",
             "No. Start with a short max-age, confirm nothing on the site breaks over "
             "https, and raise it afterwards. A long max-age set before you are certain "
             "commits every returning browser to https for that period."),
        ],
    )


BUILDERS = [security_headers]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
