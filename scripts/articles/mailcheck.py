#!/usr/bin/env python3
"""The contact address that cannot receive mail.

Every figure comes from site/_data/mail-2026-08.json through facts.py. The
survey found nothing — no dead address among the large sites that still publish
one — and the article says so, because a survey you only publish when it agrees
with you is not a survey.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import facts as F  # noqa: E402
from render import ISSUES, N_CHECKS, render  # noqa: E402

RFC = "https://www.rfc-editor.org/rfc/rfc5321#section-5.1"


def dead_contact() -> Path:
    body = f"""
<p class="lede">A contact address on a domain with no MX record does not fail loudly — it
bounces, to the sender, and you never learn anyone wrote. We checked the
{F.mail_answered()} sites in the Tranco top {F.mail_attempted()} that answered a request, and
found <strong>{F.mail_publishing()} still publish an email address at all</strong>: every one
of them we could resolve accepts mail.</p>

<p>So this is not an epidemic among large sites. It is the failure we shipped on our own site,
and the more useful finding turned out to be the denominator rather than the numerator.</p>

<h2>What actually breaks</h2>

<p>Delivering mail to a domain means asking DNS for its MX record.
<a href="{RFC}">RFC 5321 §5.1</a> says that when there is no MX, the sender falls back to the
domain's address record and tries SMTP there. On a site hosted by GitHub Pages, Netlify,
Vercel or Cloudflare Pages, that address record points at a machine which serves files and
does not answer on port 25. The message is attempted, refused, and bounced.</p>

<p>The bounce goes to the person who wrote to you. Nothing arrives at your end — not the
message, not a warning, not a record that anyone tried. Your analytics show the contact page
being read. Your inbox shows nothing, which looks exactly like nobody having anything to
say.</p>

<p>This is why it is worse than a broken link, and worth stating plainly: <strong>a 404 tells
the visitor it failed. A dead mailbox tells the visitor it worked.</strong></p>

<h2>We did this</h2>

<p>scoutseo.app carried <code>hello@scoutseo.app</code> in the footer of all 25 of its pages.
The domain has no MX record; it is on GitHub Pages; port 25 is closed there. Every message
anyone sent bounced, and we found out by writing a contact page and checking our own
advertised channel before publishing it.</p>

<p>An SEO audit tool shipping a dead contact address is embarrassing in a specific and useful
way: it is exactly the class of defect that only shows up if something asks the question, and
nothing did, because no tool asks it. That is now check {N_CHECKS} —
<code>cvr.dead_contact</code>.</p>

<h2>What the survey found</h2>

<p>We fetched the homepage of the top {F.mail_attempted()} sites in the Tranco list;
{F.mail_answered()} answered. An address counts as published only where it appears in a
<code>mailto:</code> href — text in prose might be an example, a screenshot caption or
somebody else's. Free-provider addresses and
<a href="https://www.rfc-editor.org/rfc/rfc2606">RFC 2606</a> reserved names are excluded,
because whether gmail.com accepts mail is not a fact about the site quoting it.</p>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th>Result</th><th>Sites</th></tr></thead><tbody>
<tr><td>Answered a homepage request</td><td>{F.mail_answered()}</td></tr>
<tr><td>Publish an email address in a <code>mailto:</code></td>
<td>{F.mail_publishing()} ({F.mail_publishing_pct()}%)</td></tr>
<tr><td>… and the domain accepts mail</td><td>{F.mail_accepts()}</td></tr>
<tr><td>… and the domain conclusively does not</td><td>{F.mail_dead()}</td></tr>
<tr><td>… could not be determined from here</td><td>{F.mail_undetermined()}</td></tr>
</tbody></table></div>

<p>Zero is a real result and it deserves an honest reading rather than a triumphant one. Zero
out of {F.mail_publishing()} is not evidence that the true rate is zero; it is consistent with
anything up to about <strong>{F.mail_upper_bound_pct()}%</strong>, which is what a 95%
interval allows when you observe no events in {F.mail_publishing()} trials. What it does rule
out is the version of this article we expected to write.</p>

<h2>The number we did not go looking for</h2>

<p>Only <strong>{F.mail_publishing_pct()}% of the sites that answered publish an email address
at all</strong>. Among the largest sites on the web, the contact address has very nearly
disappeared — replaced by a form, a help centre, or nothing.</p>

<p>That reframes the risk rather than removing it. A dead address is a failure available only
to sites that still publish one, and the sites that still publish one are small: the
independent shop, the two-person consultancy, the practice whose owner wants people to be able
to just write. Those are also the sites least likely to have anyone watching DNS, and most
likely to have moved to a static host in the last few years without thinking about mail. The
population most exposed to this is the population we could not sample by taking the top of a
popularity list.</p>

<p>So we are publishing the finding we got, and saying what it does not cover. A survey of
small business sites would answer the question properly. We have not run one.</p>

<h2>Where another tool is better</h2>

<p>Any mail-focused service does deliverability far more thoroughly than this. <a
href="https://mxtoolbox.com/">MXToolbox</a> and its equivalents will check SPF, DKIM, DMARC,
blacklist status and whether your outbound mail will land in spam — none of which Scout looks
at, and all of which matter more than this check if you are actually sending mail.</p>

<p>The difference is what starts the question. Those tools begin with a domain you already
suspect. This begins with your website, finds the address you are publishing, and asks whether
it works — which is a question nobody thinks to ask about an address they have had for
years.</p>

<h2>Checking your own</h2>

<p>One command, and no tool required:</p>

<pre><code>dig +short MX yourdomain.com</code></pre>

<p>Output means a mail exchanger is published and mail has somewhere to go. Empty output means
there is none, and the next question is whether your address record runs a mail server —
almost certainly not, if your site is on a static host. The fix is to add MX records at your
DNS provider, pointing at whatever mailbox or forwarding service you use.</p>

<p>If you are not going to fix it, delete the address. A visitor who sees no email address
looks for another way to reach you. A visitor who emails a dead one believes they already
have.</p>

<p>Scout runs this as <code>cvr.dead_contact</code> on every audit, and it will not report a
domain it could not resolve — a lookup that failed is not a finding, and a domain with no MX
but a working mail server on its address record is legal and fine.</p>

<p><a class="btn" href="/download/">Download Scout</a></p>
"""
    return render(
        cat="learn", slug="dead-contact-address",
        title="The contact address that bounces every message",
        desc=(f"An address on a domain with no MX record bounces silently. We checked "
              f"{F.mail_answered()} of the Tranco top {F.mail_attempted()}: only "
              f"{F.mail_publishing()} publish one at all."),
        h1="The contact address that cannot receive mail",
        crumb='<a href="/">Scout</a> / <a href="/learn/">Learn</a> / Dead contact addresses',
        body=body,
        published="2026-08-07",
        faq=[
            ("How do I know if my contact email works?",
             "Run dig +short MX yourdomain.com. Any output means a mail exchanger is "
             "published and mail has somewhere to go. Empty output means there is none, and "
             "senders fall back to your address record — which on a static host such as "
             "GitHub Pages or Netlify does not run a mail server, so every message bounces."),
            ("Why does mail bounce silently?",
             "The bounce is delivered to the sender, not to you. Nothing reaches the address "
             "and nothing records the attempt, so an inbox with no messages looks identical "
             "to an audience with nothing to say."),
            ("Is it common for a published address to be dead?",
             f"Not among large sites. Of the {F.mail_answered()} sites in the Tranco top "
             f"{F.mail_attempted()} that answered, {F.mail_publishing()} publish an address "
             f"at all and every one we could resolve accepts mail. The risk sits with "
             f"smaller sites, which are both far more likely to publish an address and far "
             f"less likely to have anyone watching DNS."),
            ("Can a domain receive mail without an MX record?",
             "Yes. RFC 5321 section 5.1 says a sender that finds no MX falls back to the "
             "domain's address record, so a domain whose web server also runs SMTP works "
             "fine. That is why the absence of an MX record is the start of the question "
             "rather than the answer to it."),
        ],
    )


BUILDERS = [dead_contact]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
