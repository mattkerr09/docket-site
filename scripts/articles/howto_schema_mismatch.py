"""Structured data that says what the page does not.

Promised on the how-to hub. Sourced from two registered checks:
`schema.mismatch` ("Structured data vs visible content") and `schema.price`
("Schema price vs visible price").

The archetype this page exists for: adding markup reads as good practice.
Nobody adds a rating to cheat — a plugin offered, and it filled in a number
from somewhere the page does not show.

⚠️ The self-implicating example is real and is in `schema.price`'s own
docstring: this product's marketing site shipped a price in its markup while
the beta was free and had no checkout. Told without figures, because
verify_numbers rejects typed numbers in prose.

No numeric literals.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def schema_mismatch() -> Path:
    body = """
<p class="lede">Structured data is a set of claims about a page, made in a language only
machines read. When those claims stop matching what the page shows, the risk is not a missing
star rating — it is a manual action that can remove every rich result for the whole site.</p>

<h2>Why it happens to careful people</h2>

<p>Nobody adds markup in order to lie. A plugin offers to handle structured data, it fills in
what it can find, and from then on the markup and the page are two separate things maintained by
two separate processes. One of them gets updated.</p>

<p>This product's own marketing site did it: the JSON-LD advertised a price, with the item marked
in stock, while the thing was free and had no checkout at all. Every page looked perfectly
correct. The markup was the only place the claim existed, and nothing renders it.</p>

<h2>The two shapes it takes</h2>

<p><strong>A rating with nothing to rate.</strong> An aggregate rating in the markup and no
review content anywhere on the page. This is the classic policy breach, and the one most likely
to be treated as deliberate, because a score with no reviews behind it is what a fabricated
rating looks like.</p>

<p><strong>A price the page does not show.</strong> Far more common, and usually accidental: the
price changes in the database and the JSON-LD keeps the old one. The rich result then advertises
a number you will not honour. The visitor arrives expecting it, and nobody finds out until
somebody complains — because the page itself is right.</p>

<h2>What an audit can and cannot tell you</h2>

<p>A check like this compares the page against its own markup. It can say the two disagree. It
<strong>cannot</strong> say which one is correct, and a good one will not pretend to: a shop
showing the same wrong price in the page and the markup agrees with itself and passes, as it
should. No crawler knows what you meant to charge.</p>

<p>It is also worth knowing where the rating rule legitimately does not apply. An app's store
rating declared on software markup is documented and allowed — the number belongs to the app,
not to a review widget the page forgot to draw. A check that fired on that would be wrong, and a
tool that tells you to delete correct markup costs more than it saves.</p>

<h2>The wrong fixes</h2>

<p><strong>Hiding the visible element so it matches.</strong> If the page shows a price and the
markup shows another, the answer is not to remove the price from the page. That leaves the
claim standing with even less to support it.</p>

<p><strong>Deleting the markup instead of correcting it.</strong> Tempting, and it does end the
mismatch. It also ends the rich result you were entitled to. Fix the number.</p>

<p><strong>Marking up reviews collected somewhere else.</strong> Ratings from a third-party
profile are not review content on your page. If you want them represented, put them on the page
where a person can read them, then mark up what is there.</p>

<h2>Checking yours</h2>

<pre><code>curl -s https://example.com/product/ | grep -o '"price":"[^"]*"'</code></pre>

<p>Then look at the page and compare. Do it on a product whose price changed recently — that is
where the two copies separate — and on anything carrying a rating, where the question is simply
whether a reader can see any reviews at all.</p>
"""
    return render(
        cat="how-to", slug="fix-structured-data-that-does-not-match-the-page",
        title="Structured data that says what the page does not",
        desc=("Markup claiming a price or rating your page never shows risks a manual action, "
              "not a lost star. What an audit of your site compares, and cannot."),
        h1="Structured data that says what the page does not",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / schema mismatch',
        body=body,
        faq=[
            ("Can mismatched structured data get my site penalised?",
             "Google's policy requires markup to represent visible page content, and a breach "
             "risks a manual action rather than only the loss of a rich result. That is the "
             "part people underestimate: the downside is not missing stars, it is every rich "
             "result for the site."),
            ("Why do prices in JSON-LD go stale?",
             "Because the markup and the page are maintained by two different processes. The "
             "price changes in the database, the page updates, and the JSON-LD keeps the old "
             "number. Nobody notices, because the page itself looks correct."),
            ("Can an audit tell me which one is right?",
             "No, and it should not claim to. It can only say the page and its markup "
             "disagree. A shop showing the same wrong price in both places agrees with itself "
             "and passes — no crawler knows what you meant to charge."),
            ("Is an app store rating in my markup a violation?",
             "Not when it is declared on software markup. That rating belongs to the app and "
             "is documented as allowed. It is not a review widget the page forgot to render."),
            ("Should I delete markup that does not match?",
             "Correct it instead. Deleting ends the mismatch and also ends the rich result you "
             "were entitled to. Hiding the visible price so it matches is worse again — the "
             "claim then has even less supporting it."),
        ],
    )


if __name__ == "__main__":
    print(schema_mismatch())
