"""Deciding which of the addresses on your pages is actually yours.

Promised on the how-to hub. Sourced from `conversion.py`, registered check
`cvr.dead_contact`, three failures with one spine:

  * ⚠️ AN ADDRESS AT SOMEBODY ELSE'S DOMAIN IS NOT YOURS TO FIX. A software
    forum's how-to about configuring mailboxes carries placeholder addresses at
    a documentation domain; they were reported as the site's dead contact
    channel with the remedy "add MX records for <that domain>", which the site
    cannot publish. The guard meant to prevent it — only `mailto:` links count,
    because prose may hold an example — IS DEFEATED BY ANY PLATFORM WHOSE
    MARKDOWN AUTO-LINKS BARE ADDRESSES, which every forum does. The tool cannot
    tell documentation from a real address; it CAN tell whose domain it is.
    Matched on label boundaries so one domain is not read as a suffix of
    another.
  * ⚠️ A STRING THAT IS NOT A DOMAIN IS NOT A DEAD MAILBOX. `check_domain`
    returns a negative with the reason "not a syntactically valid domain", and
    the branch tested only the negative — SO THE VERDICT WRITTEN TO SAY THE
    TOOL COULD NOT JUDGE THE STRING BECAME A FINDING ABOUT THE READER'S CONTACT
    CHANNEL. Measured on a law firm whose share-by-email widget has a
    deliberately empty recipient. Skipped rather than re-reported as a broken
    link: that would be the same false positive in a new coat.
  * ⚠️ NOT `looks_like_ip`. An address at a bare IP really is a dead mailbox
    and is reported deliberately; skipping on domain validity alone would have
    silenced it. Caught by a test. ONE SENTENCE ONLY — 539 owns that lesson.

⚠️ NO SITE, VENDOR OR ADDRESS IS NAMED — third-party gate. The forum, the law
firm and every measured address stay out; the widget is described by shape.

⚠️ /learn/dead-contact-address/ is the SURVEY (MX records, the two DNS failure
shapes, what the frame does not cover). This page is about WHOSE ADDRESS IT IS
and cross-links there rather than restating any of it.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def whose_address() -> Path:
    body = """
<p class="lede">A check that finds published email addresses and tests whether they can receive
mail has one job that sounds trivial and is not: deciding which of the addresses on your pages is
<em>yours</em>. Get that wrong and you hand somebody a real defect they cannot repair, or a repair
for something that was never broken.</p>

<h2>Publish DNS for a domain you do not own</h2>

<p>A software forum runs a how-to about configuring mailboxes. Like every such document it contains
example addresses at a documentation domain — placeholder words where a real mailbox name would
go.</p>

<p>Those were reported as the site's dead contact channel, with the remedy: add mail records for
that domain, pointing at a mail host. The site cannot publish DNS for a domain it does not own.
<strong>The finding was true and the instruction was impossible.</strong></p>

<p>The guard that was supposed to prevent this is sensible and is written down: only
<code>mailto:</code> links count, because an address sitting in prose may be an example, a
customer's, or a fax number's neighbour. It stopped working for a reason nobody chose —
<strong>any platform whose markdown auto-links bare addresses turns every example in every
document into a link</strong>, and every forum does that.</p>

<p>It is worth sitting with as a general shape. A rule that depends on authors not linking
something stops working the moment the platform links it for them, and nothing about the site
changed.</p>

<h2>What the tool could actually tell</h2>

<p>It cannot distinguish documentation from a real address. That is a judgement about intent and it
is not in the page.</p>

<p>It <em>can</em> tell whose domain the address is at. So the remedy is now offered only for a
domain the reader can publish records for, matched on label boundaries so one domain is never read
as a suffix of a similarly spelled one.</p>

<p><strong>The finding was right; only the instruction changed.</strong> That distinction is most
of what separates a report somebody acts on from one they dismiss — a reader who is told to do
something impossible does not conclude the tool was half-right.</p>

<h2>The verdict that meant "I cannot judge this"</h2>

<p>The second failure is the one worth borrowing, because the mechanism shows up everywhere.</p>

<p>The domain checker answers with a verdict and a reason. For anything that is not a domain at
all, it answers <em>no</em>, with the reason "not a syntactically valid domain". The branch above
it tested the verdict and not the reason. <strong>So the sentence written to say the tool could not
judge the string became a finding about the reader's contact channel.</strong></p>

<p>A law firm's site carries a share-by-email button on every page. Its recipient is deliberately
empty, so a reader's mail client opens with a blank To: field and a subject already filled in —
they type the address of whoever they are sharing with. Perfectly ordinary, working exactly as
designed.</p>

<p>The report said that address could not receive mail, and that anyone writing to it would get a
bounce. Nobody writes to it. It is not an address.</p>

<h2>And it was skipped, not renamed</h2>

<p>There is a tempting second move here: stop calling it a dead mailbox and start calling it a
broken link. It is still a finding, it is still technically defensible, and the reader is still
being shown a working button and told it is broken.</p>

<p>A <code>mailto:</code> with no recipient and a prefilled subject is the ordinary shape of a
share widget. Reporting it under a different name would be <strong>the same false positive in a new
coat</strong> — which is worth watching for whenever a tool "addresses" a complaint about a finding
and the finding is still there under a different heading.</p>

<h2>The one that must still fire</h2>

<p>Not every unusual address is innocent. An address whose domain part is a bare server address —
digits and dots, or a block of hexadecimal — is a genuinely dead mailbox, because no mail records
can ever be published for it. It is the residue of a site being moved between servers while the old
host stayed written into the content.</p>

<p>Skipping everything that fails a domain-validity test would have silenced exactly that case
while fixing the two above. A test caught it, which is the usual way —
<a href="/how-to/when-a-fix-creates-a-false-negative/">a guard that quietens one false positive can
silence a true finding &rarr;</a>.</p>

<h2>Reading this on your own report</h2>

<ol>
<li><strong>Check the domain in the address against your own.</strong> If it is not yours, no
instruction about mail records applies to you, whatever the finding says.</li>
<li><strong>Ask where the address appears.</strong> A code sample, a support document or a
quoted message is somebody else's address that your platform turned into a link.</li>
<li><strong>Look for an empty recipient.</strong> A share button has no address in it at all,
and it is not a contact channel.</li>
<li><strong>If it is your domain, test it in one command.</strong> The survey behind this check —
<a href="/learn/dead-contact-address/">what a dead contact address actually is &rarr;</a> — has
the command and the two ways mail configuration fails.</li>
</ol>

<h2>When it is real, and why it is worse than it looks</h2>

<p>Keep the severity where it belongs. A published address at a domain that cannot receive mail
means every enquiry bounces — <strong>and you get no record that anyone tried.</strong> That last
part is what makes it different from a broken form or a dead link: there is no error you will ever
see, no entry in any log of yours, and no angry follow-up. The people who wrote to you simply
conclude you did not reply.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Chasing DNS for a domain that is not yours.</strong> You cannot, and an hour spent
finding that out is the cost of the false positive.</li>
<li><strong>Deleting the examples from your documentation.</strong> They are doing their job. The
tool was reading them wrongly.</li>
<li><strong>Removing the share button.</strong> It works. Nothing about it needs fixing.</li>
<li><strong>Adding a working address and leaving the broken one.</strong> The dead address stays
on the pages that carry it, and those are the pages people will use.</li>
</ul>

<h2>How to pass this check while staying unreachable</h2>

<p>Publish your address as plain text without a <code>mailto:</code> link. Only linked addresses
are checked — because an unlinked one might be an example — so the finding disappears and the
mailbox is exactly as broken as it was.</p>

<p><strong>A check that must avoid other people's examples can only see the addresses you chose to
link</strong>, and that boundary is visible from outside. It is the honest limit of this kind of
check, and it is why the survey behind it starts from DNS rather than from pages.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>cvr.dead_contact</code>, which tests whether published email
addresses can receive mail. For what actually breaks in mail configuration, and the measurement
behind it, see <a href="/learn/dead-contact-address/">a dead contact address &rarr;</a>. For the
same question one channel over, see <a href="/how-to/fix-phone-links-that-will-not-dial/">phone
links that will not dial &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="addresses-on-your-site-that-are-not-yours",
        title="Not every address on your site is yours",
        desc=("An audit told a forum to publish mail records for a domain it does not own, and "
              "called a share button on a site a dead mailbox. Which address is actually yours."),
        h1="Not every address on your site is yours",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Whose address',
        body=body,
        faq=[
            ("An audit says an email address on my site is dead, but it is not my address. Why?",
             "Because a check that finds published addresses cannot tell documentation from a "
             "real contact address — that is a judgement about intent and it is not in the page. "
             "It can tell whose domain the address is at, which is enough to stop offering you a "
             "repair you have no access to."),
            ("Why would example addresses in my documentation get reported at all?",
             "The usual guard is that only linked addresses count, because prose may hold an "
             "example. Platforms that auto-link bare addresses in markdown turn every example "
             "into a link, so the guard stops working without anything on the site changing."),
            ("My share-by-email button was reported as a dead mailbox. Is something wrong?",
             "No. A share widget has a deliberately empty recipient so the reader types an "
             "address, and nothing about it is a contact channel. Renaming that finding to "
             "'broken link' would be the same false positive under a different heading."),
            ("Is an email address at a bare IP address a real problem?",
             "Yes. Mail records cannot be published for a server address, so nothing can ever be "
             "delivered. It is usually left behind when a site moves servers and the old host "
             "stays written into the content."),
            ("What does a dead contact address actually cost?",
             "Every enquiry bounces and you get no record that anyone tried. Unlike a broken "
             "form there is no error you will see and no log of yours to check — the people who "
             "wrote to you conclude you did not reply."),
        ],
    )


if __name__ == "__main__":
    print(whose_address())
