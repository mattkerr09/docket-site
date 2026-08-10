#!/usr/bin/env python3
"""How to redirect http:// to https:// — written from our own failure.

Every claim here is first-hand. Docket audited docketseo.app on 2026-08-10 and
returned `security.no_http_redirect` at HIGH. Checked by hand: the plain-HTTP
address answered 200 with zero redirects and no HSTS header, GitHub's Pages API
reported `https_enforced: false` with the certificate in state `dns_changed`,
and enabling enforcement was refused with "The certificate has not finished
being issued".

That refusal is the useful part and the reason this page exists. Every guide
says "tick Enforce HTTPS". None of them says what to do when the tick box will
not take, which is the state a real site is actually in.

No numeric literals in the prose: the site's own state is the example, and it
is meant to change. A count typed into a sentence goes stale silently.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def http_to_https() -> Path:
    body = """
<p class="lede">If your site answers on <code>http://</code> without sending the visitor to
<code>https://</code>, you have two problems and only one of them is about ranking. The
ranking one is old news. The other is that a browser now writes "Not secure" next to your
address, and the person reading it has no idea whether that means you are careless or
compromised.</p>

<p>We found this on our own site. Docket audited <code>docketseo.app</code>, returned
<strong>http:// does not redirect to https://</strong> at HIGH, and it was right — the plain
HTTP address answered normally with no redirect at all. A tool that ships this check was
shipping the fault. That is embarrassing in a useful way, because fixing it turned up the part
of this problem nobody writes down.</p>

<h2>First, confirm it rather than assume it</h2>

<p>Type your domain into a browser and you will almost certainly end up on HTTPS, because the
browser upgraded it for you. That tells you nothing about what your server does. Ask the server
directly:</p>

<pre><code>curl -sI http://yourdomain.com/ | head -1</code></pre>

<p>You want a <code>301</code> and a <code>Location:</code> header pointing at the
<code>https://</code> version of the same path. If you get <code>200 OK</code>, your server is
happily serving the insecure version to anyone who asks for it — including any crawler that
does not upgrade, and any visitor following an old link.</p>

<h2>The fix, by where the site is hosted</h2>

<p>On most managed hosts this is one setting, and the setting is usually already there:</p>

<ul>
<li><strong>GitHub Pages</strong> — Settings → Pages → <em>Enforce HTTPS</em>.</li>
<li><strong>Netlify, Vercel, Cloudflare Pages</strong> — on by default; look for "Force HTTPS"
or "Always Use HTTPS" if it is not.</li>
<li><strong>Cloudflare in front of your own server</strong> — SSL/TLS → Edge Certificates →
<em>Always Use HTTPS</em>. Set the encryption mode to Full (strict), not Flexible; Flexible
re-encrypts to your origin over plain HTTP and quietly reintroduces the problem you are
fixing.</li>
<li><strong>Nginx</strong> — a server block on port 80 whose only job is
<code>return 301 https://$host$request_uri;</code>. Return the redirect, do not rewrite: a
rewrite can drop the path and land everyone on the homepage.</li>
<li><strong>Apache</strong> — <code>Redirect permanent / https://yourdomain.com/</code> in the
port-80 virtual host, or the mod_rewrite equivalent if you already use it.</li>
</ul>

<p>Two details that cost people a morning. Use <strong>301</strong>, not 302 — a temporary
redirect tells a search engine to keep the old URL. And preserve the path: a redirect that
sends <code>/pricing</code> to the homepage loses every deep link you have ever earned, which
is a worse outcome than the problem.</p>

<h2>When the setting refuses — the part nobody documents</h2>

<p>This is what actually happened to us. The API refused:</p>

<pre><code>PUT /repos/OWNER/REPO/pages   https_enforced=true
404 — "The certificate has not finished being issued"</code></pre>

<p>HTTPS itself was working. A valid certificate was being served, every page loaded over TLS,
nothing looked broken. What was stuck was the certificate <em>state</em>: GitHub reported
<code>dns_changed</code>, and it will not let you enforce HTTPS while it is re-validating.</p>

<p>The cause was one DNS record we had stopped thinking about. The apex domain was configured
correctly — the right A records, the right CNAME file in the repository. The
<code>www</code> subdomain was not: it still pointed at the registrar's parking service from
before the site existed. A host that issues a certificate covering both the apex and
<code>www</code> cannot finish validating while half of that pair answers to somebody else.</p>

<p>So the check that unblocks the tick box is not on the page you are looking at:</p>

<pre><code>dig +short yourdomain.com A
dig +short www.yourdomain.com CNAME</code></pre>

<p>The apex should return your host's addresses. The <code>www</code> record should point at
your host too — not at a registrar landing page, not at an old server, and not at nothing.
Fix that, and the certificate finishes issuing on its own; the setting then takes normally.</p>

<h2>HSTS is the follow-up, and it is not the same thing</h2>

<p>A redirect fixes the request after it happens. <code>Strict-Transport-Security</code> stops
the insecure request being made at all: once a browser has seen the header, it goes straight to
HTTPS for that domain without asking. Add it after the redirect works, never before — the
header tells browsers to refuse plain HTTP for your domain for its whole
<code>max-age</code>, and if HTTPS is broken when they act on that, they cannot fall back.</p>

<p>Start with a short <code>max-age</code>, confirm nothing broke, then raise it. Treat
<code>preload</code> as close to irreversible: removal from the browser preload lists takes
months.</p>

<h2>What Docket does about it</h2>

<p>It probes the plain-HTTP address directly rather than trusting the browser's upgrade, so it
sees what a crawler sees. It reports the missing redirect and the missing HSTS header as
separate findings, because they are separate jobs and doing the second one first is how sites
break. Both name the change to make.</p>

<p>It found this on the site that sells it. That is the argument for running an audit against
your own work rather than reading about one.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="redirect-http-to-https",
        title="How to redirect http:// to https:// — and when it won't",
        desc=("A 301 from http:// to https://, host by host — plus the certificate state "
              "that blocks the Enforce HTTPS setting, and the DNS record that causes it."),
        h1="How to redirect http:// to https://",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / http to https',
        body=body,
        faq=[
            ("Does a missing HTTPS redirect actually affect ranking?",
             "HTTPS has been a Google ranking signal since 2014, but the redirect matters "
             "more for duplication and trust than for the signal itself: without it the same "
             "page is reachable at two addresses, and browsers label the insecure one "
             "'Not secure' in the address bar."),
            ("Should I use a 301 or a 302?",
             "301. A 302 is a temporary redirect and tells a search engine to keep indexing "
             "the http:// URL, which is the opposite of what you want."),
            ("Why does 'Enforce HTTPS' refuse to turn on?",
             "Usually because the certificate has not finished being issued. On GitHub Pages "
             "the API reports a certificate state such as dns_changed. The common cause is a "
             "DNS record that does not point at the host — often a www subdomain still "
             "pointing at a registrar parking page — because the certificate covers both the "
             "apex and www."),
            ("Should I add HSTS at the same time?",
             "No. Get the redirect working first. HSTS tells browsers to refuse plain HTTP "
             "for your domain for the whole max-age, so if HTTPS is broken when they act on "
             "it there is no fallback. Add it afterwards with a short max-age and raise it "
             "once you are confident."),
        ],
    )


if __name__ == "__main__":
    print(http_to_https())
