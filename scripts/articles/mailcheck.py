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


def _shape_table() -> str:
    """Rows built from the dataset, so the table cannot disagree with the text."""
    return "".join(
        f"<tr><td>{n}</td><td>{shape}</td></tr>" for n, shape in F.mx_shape_rows()
    )

RFC = "https://www.rfc-editor.org/rfc/rfc5321#section-5.1"


def dead_contact() -> Path:
    body = f"""
<p class="lede">A contact address on a domain with no MX record does not fail loudly — it
bounces, to the sender, and you never learn anyone wrote. We checked the
{F.mail_answered()} sites in the <a href="https://tranco-list.eu/">Tranco top</a> {F.mail_attempted()} that answered a request, and
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

<p>docketseo.app carried <code>hello@docketseo.app</code> in the footer of all 25 of its pages.
The domain had no MX record; it is on GitHub Pages; port 25 is closed there. Every message
anyone sent bounced, and we found out by writing a contact page and checking our own
advertised channel before publishing it.</p>

<p>The domain now publishes MX records, and the address is still not back — which is the
honest end of this story rather than a loose end. An MX record is necessary for delivery and
not sufficient: forwarding is configured per address, and nobody has yet sent a message to one
and had it answered. Re-advertising an address because DNS looks right would be the same
failure this check exists to catch, one layer further in.</p>

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

<h2>So we went and sampled it</h2>

<p>Taking the top of a ranking cannot reach small businesses, so the second survey does not
use a ranking at all. The frame, in one sentence: <strong>every shop in
<a href="https://www.openstreetmap.org/">OpenStreetMap</a> inside the boundaries of
{F.small_cities()} named UK cities that also carries a <code>website</code> tag</strong>,
one entry per domain. Nothing selects individual businesses and nothing weights by size or
traffic; the whole frame is used, so there is no slice to defend. The Overpass query is in
the dataset if you want to re-run it.</p>

<p>{F.small_frame()} distinct domains, {F.small_answered()} of which answered a request. And
the first number is the one that matters:</p>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th></th><th>Tranco top {F.mail_attempted()}</th><th>UK shops in OpenStreetMap</th>
</tr></thead><tbody>
<tr><td>Answered</td><td>{F.mail_answered()}</td><td>{F.small_answered()}</td></tr>
<tr><td>Publish an address in a <code>mailto:</code></td>
<td>{F.mail_publishing()} ({F.mail_publishing_pct()}%)</td>
<td>{F.small_publishing()} ({F.small_publishing_pct()}%)</td></tr>
<tr><td>… and the domain conclusively cannot receive mail</td>
<td>{F.mail_dead()}</td><td>{F.small_dead()}</td></tr>
</tbody></table></div>

<p>Small businesses publish an email address <strong>{F.small_publishing_ratio()} times as
often</strong> — {F.small_publishing_pct()}% against {F.mail_publishing_pct()}%. And unlike
the large sites, some of theirs do not work: <strong>{F.small_dead()} of
{F.small_publishing()}</strong>, or {F.small_dead_pct()}%, with a 95% interval of
{F.small_dead_interval()}. Seven is a small number and the interval says so; what it is not
is zero.</p>

<p>All seven are businesses with a single mapped location — the independents, not the chains.
That split comes from the data rather than from an opinion about which brands count as
chains: a domain appearing at one mapped shop is one business, and at nine is not.</p>

<h2>The two ways they break</h2>

<p>We are not naming them. These are corner shops and locksmiths that never asked to be
audited, and "this named business cannot receive email" is not a thing this site has any
business publishing about them. The failure shapes are the useful part, and there are only
two:</p>

<ul>
<li><strong>The domain in the address does not exist.</strong> Six of the seven. The site is
on one domain and the email address is at another — a near-miss spelling, or a domain that
lapsed — and that second domain has no MX record and no address record at all. Nothing about
the website looks wrong, because nothing about the website <em>is</em> wrong.</li>
<li><strong>An MX record naming a host that does not resolve.</strong> One of the seven, and
the more interesting one. The domain publishes a mail exchanger, so every "do you have an MX
record" test passes. The host it names has no address record — in this case a hosting panel
had pasted the domain into the middle of a template value and left it there. The record looks
completely correct in the zone file and there is nowhere for the mail to go.</li>
</ul>

<p>That second shape is why Docket resolves the exchanger rather than stopping at the record.
An MX-exists check would have called that domain healthy.</p>

<h2>The record that exists and the host that does not</h2>

<p>Everything above is about a domain with no MX record. There is a second
failure underneath it that is harder to see, and we measured that too — same
frame, DNS only, no pages fetched.</p>

<p>Of the {F.mx_publishing()} domains in the frame that publish an MX record at all,
<strong>{F.mx_dead()} name a mail exchanger that does not resolve</strong> — every one of
them, so there is nowhere for the message to go. That is {F.mx_dead_pct()}% of the domains
that look correctly configured. Another {F.mx_partial()} have one dead exchanger and a
working one, so their mail arrives; the finding only speaks when all of them fail.</p>

<p>This is the case that defeats checking. Every "does this domain have an MX record" test
passes. The zone file looks right, the record has a sensible priority, and the hostname reads
like a mail server. It just names a machine that is not there.</p>

<div class="wrap-tbl"><table class="cmp"><thead><tr>
<th>Domains</th><th>What the dead exchanger is</th></tr></thead><tbody>
{_shape_table()}
</tbody></table></div>

<p><strong>{F.mx_top_two()} of the {F.mx_dead()} fall into two shapes.</strong> That is what
makes it worth naming rather than reporting as "the host does not resolve": telling someone
their Microsoft 365 exchanger is missing sends them to the right console, and telling them the
host is unreachable sends them to their DNS panel to look at a record that is fine.</p>

<p>We are not saying <em>why</em>. A tenant hostname that stops resolving could be a lapsed
subscription, a migration someone started and did not finish, or a record left behind after a
move years ago. From outside the domain those look identical, so Docket names the shape and
stops. Guessing the cause would be the kind of confident wrongness that costs more than the
finding is worth.</p>

<p>One of the {F.mx_dead()} is an exchanger under <code>.invalid</code>, which
<a href="https://www.rfc-editor.org/rfc/rfc2606">RFC 2606</a> reserves precisely so that it
can never resolve. As a placeholder in a setup wizard that is correct. As a live MX record it
is a guarantee of failure.</p>

<h2>What this does not cover</h2>

<p>Said plainly, because a frame with unstated limits is worse than no frame. OpenStreetMap
coverage is uneven and who gets mapped is not random — a shop nobody added is not in this
survey. A <code>website</code> tag sometimes points at a social page or a chain's national
site rather than the business's own domain; those are excluded, and the exclusion is a
judgement we made. {F.small_cities()} UK cities is not the world, and shops are not every kind
of small business. The number to take from this is the contrast in the table, not
{F.small_dead_pct()}% as a rate for small businesses everywhere.</p>

<h2>Where another tool is better</h2>

<p>Any mail-focused service does deliverability far more thoroughly than this. <a
href="https://mxtoolbox.com/">MXToolbox</a> and its equivalents will check SPF, DKIM, DMARC,
blacklist status and whether your outbound mail will land in spam — none of which Docket looks
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

<p>Docket runs this as <code>cvr.dead_contact</code> on every audit, and it will not report a
domain it could not resolve — a lookup that failed is not a finding, and a domain with no MX
but a working mail server on its address record is legal and fine.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="learn", slug="dead-contact-address",
        title="The contact address that bounces every message",
        desc=(f"An address on a domain with no MX record bounces silently. Two "
              f"measured surveys: {F.mail_publishing_pct()}% of the Tranco top publish "
              f"one, {F.small_publishing_pct()}% of UK shops do, and "
              f"{F.small_dead()} of those are dead."),
        h1="The contact address that cannot receive mail",
        crumb='<a href="/">Docket</a> / <a href="/learn/">Learn</a> / Dead contact addresses',
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
             f"Not among large sites: of the {F.mail_answered()} in the Tranco top "
             f"{F.mail_attempted()} that answered, {F.mail_publishing()} publish an address "
             f"and every one we could resolve accepts mail. Among {F.small_answered()} UK "
             f"shop websites sampled from OpenStreetMap, {F.small_publishing_pct()}% publish "
             f"an address and {F.small_dead()} of {F.small_publishing()} cannot receive mail "
             f"— about {F.small_dead_pct()}%, with a 95% interval of "
             f"{F.small_dead_interval()}."),
            ("My domain has an MX record — is that enough?",
             f"No. An MX record names a host, and the host has to exist. Of the "
             f"{F.mx_publishing()} domains in our OpenStreetMap sample that publish an MX "
             f"record, {F.mx_dead()} name an exchanger that does not resolve at all, so "
             f"mail bounces while every record-presence check passes. Resolve the hostname "
             f"in the record, not just the record: dig +short A "
             f"the-name-your-mx-points-at."),
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
