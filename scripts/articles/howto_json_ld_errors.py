"""Read the JSON-LD error, not the guess.

Promised on the how-to hub. Sourced from the registered check `schema.invalid`
in `backend/seo_engine/checks/structured.py`, which carries both halves:

  * THE CHECK ALREADY KNEW AND THEN GUESSED ANYWAY — it parses the block,
    catches the exception, prints it, and then offered a fixed list of three
    likely causes. On a consumer-rights body every page checked failed with
    `Invalid control character`, which is none of the three.
  * IT USED TO STOP AT THE FIRST BROKEN BLOCK PER PAGE — so "they all fail the
    same way" described what had been collected rather than the site. On a
    hardware vendor with two blocks per page, several had both broken with
    DIFFERENT errors.

The seven-entry remedy table below is copied from `_JSON_ERROR_REMEDY` and must
stay in step with it. Nothing here is invented.

⚠️ NO SITE OR VENDOR IS NAMED — third-party gate.

⚠️ MUST NOT CONTRADICT /how-to/fix-structured-data-errors/, whose short section
on this says "validate the rendered output, not the template". That is correct
and this page reinforces it; what it adds is what each message means and why one
fix per page is not a fix.

Body is a raw string so backslash escapes render literally.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def json_ld_errors() -> Path:
    body = r"""
<p class="lede">Invalid JSON-LD is the most expensive structured-data fault there is, because
nothing is partially read: one bad character and the whole block is discarded, so a page with
perfect Product markup is treated exactly like a page with none. The report usually shows you the
parser's own message — and then, underneath, a list of likely causes that may have nothing to do
with it.</p>

<h2>The tool had the answer and printed a guess</h2>

<p>A check that finds invalid JSON-LD has, by definition, just tried to parse it and caught an
exception. It is holding the exact reason. Docket printed that exception and <em>then</em> offered
a fixed list of three usual suspects: a trailing comma, an unescaped quote, HTML entities the CMS
encoded into the block.</p>

<p>On a consumer-rights body's site, every page checked failed with the same message —
<code>Invalid control character</code> — which is none of those three. The real cause was a raw
newline inside a string holding HTML, exactly the shape a CMS produces when it writes a
multi-line field straight into a script block.</p>

<p>So the reader goes hunting for a trailing comma that does not exist, while the message that
would have told them the answer sits above it meaning nothing to anybody who does not write
parsers. <strong>An error message is evidence; a list of likely causes is a guess. Printing the
guess while holding the evidence is the defect.</strong></p>

<h2>What each message actually means</h2>

<p>This is the part worth keeping. These are the messages a JSON parser emits and what each one
means for the person fixing it:</p>

<ul>
<li><strong><code>Invalid control character</code></strong> — a literal newline, tab or carriage
return inside a string value. JSON forbids them unescaped, so write them as <code>\n</code> and
<code>\t</code>, or strip them. Almost always a CMS writing multi-line HTML into a field.</li>
<li><strong><code>Expecting property name enclosed in double quotes</code></strong> — a trailing
comma before a closing brace or bracket, or a key quoted with apostrophes instead of double
quotes.</li>
<li><strong><code>Expecting ',' delimiter</code></strong> — an unescaped double quote inside a
string value. Write it as <code>\"</code>.</li>
<li><strong><code>Expecting value</code></strong> — an empty field emitted with nothing after the
colon, or HTML entities such as <code>&amp;quot;</code> that the CMS encoded into the script
block.</li>
<li><strong><code>Extra data</code></strong> — two JSON documents in one script block. Give each
its own block, or combine them into a single array.</li>
<li><strong><code>Unterminated string starting at</code></strong> — a string that never closes,
usually an unescaped quote or a template cut off mid-render.</li>
<li><strong><code>Invalid \escape</code></strong> — a lone backslash, typically from a Windows
path or a regular expression. Double it.</li>
</ul>

<p>If your tool shows you a message that is not in a list like this, the message is still the
better clue than any generic advice beside it. Search for it exactly.</p>

<h2>Fixing one error per page is not fixing the page</h2>

<p>The second half of this, and the more damaging one.</p>

<p>Docket used to stop at the first broken block on each page. That made its summary sentence
unable to be wrong in the only way that matters: "all of them fail the same way" was a statement
about what the tool had <em>collected</em>, not about the site. The clause that exists to say
"other kinds of error are also present" could never fire, because a second error on an
already-recorded page was never looked at.</p>

<p>On a hardware vendor's site every page carried two JSON-LD blocks, and several had
<strong>both</strong> broken, with different errors. The report named one missing comma. Somebody
fixes the comma, re-tests, and the page is still discarded by the search engine — which is exactly
the outcome the check exists to prevent.</p>

<p><strong>Sampling one instance per page and then summarising across pages produces a claim that
cannot be falsified in the way that matters.</strong> It is a quiet failure mode, because the
summary sounds more confident the less it looked at.</p>

<p>The repair kept the units straight, which is worth copying: the page list stays one entry per
page, so the count and the URLs still mean pages, while the error collection gathers every failure
so the summary describes the site rather than the sample.</p>

<h2>Checking your own markup</h2>

<ul>
<li><strong>Validate the rendered output, not the template.</strong> The commonest cause is a CMS
field interpolated into JSON without escaping, so it breaks only for the products whose
descriptions happen to contain a quote or a line break — which is why it survives
spot-checking.</li>
<li><strong>Fix every block on the page, then re-validate.</strong> One page can carry several,
and a page is discarded if any block it depends on is invalid.</li>
<li><strong>Read the parser message first.</strong> Thirty seconds with the list above beats an
afternoon with a generic checklist.</li>
<li><strong>Check the records most likely to contain punctuation</strong> — product descriptions
with quotation marks, addresses with line breaks, anything pasted from a word processor.</li>
</ul>

<h2>When this matters most, and when it does not</h2>

<p>It matters most on templated pages that carry commercial markup — products, events, recipes,
jobs — because the fault is invisible on the page and total in effect. There is no partial
credit.</p>

<p>It matters least where the block was aspirational: markup added for an entity you were never
going to earn a rich result for costs you an entity signal rather than a search feature. Fix it,
but not first.</p>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Hand-editing the rendered HTML.</strong> The next build overwrites it, and you have
learned nothing about the template that produced it.</li>
<li><strong>Stripping the field that broke.</strong> Removing the description to make the JSON
parse gives you valid markup that describes less than it should.</li>
<li><strong>Escaping by search-and-replace across the template.</strong> Doubling every backslash
or quote without knowing which one broke tends to produce a second, different parse error.</li>
</ul>

<h2>How to make this finding disappear without fixing anything</h2>

<p>Delete the script block. The finding clears, the page becomes one with no structured data at
all, and no tool will complain — because an absent block and a discarded block look identical to
a search engine. That equivalence is the whole reason this fault is worth catching: <strong>you
already have the outcome of deleting it, and you are paying to generate it.</strong></p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>schema.invalid</code>, which covers JSON-LD that does not parse.
For the other structured-data faults — markup contradicting the visible page, required properties
genuinely missing, coverage as a judgement rather than an error — see
<a href="/how-to/fix-structured-data-errors/">how to fix structured data errors &rarr;</a>. For
the case where the block parses perfectly and still resolves to nothing, see
<a href="/how-to/schema-id-references/">an @id is a pointer, not a definition &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="json-ld-parser-errors",
        title="Read the JSON-LD error, not the guess",
        desc=("What each JSON-LD parser message means, and why fixing one error per page can "
              "leave an audit's findings true and a site still broken."),
        h1="Read the JSON-LD error, not the guess",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / JSON-LD errors',
        body=body,
        faq=[
            ("What does Invalid control character mean in JSON-LD?",
             "A literal newline, tab or carriage return inside a string value. JSON forbids them "
             "unescaped, and it is almost always a CMS writing a multi-line HTML field straight "
             "into the script block."),
            ("My audit lists likely causes that do not match my error. Which do I trust?",
             "The error message. The tool parsed your block and caught the exact exception; a "
             "list of usual suspects beside it is a guess that may predate your case."),
            ("If one block on a page is invalid, does the rest still count?",
             "Invalid JSON is not partially read — the whole block is discarded. A page can "
             "carry several blocks, so fix every one and re-validate rather than stopping at the "
             "first."),
            ("Why did fixing the reported error not fix my page?",
             "Because there was more than one. A check that records a single error per page can "
             "report that they all fail the same way when it only ever looked at one of them."),
            ("How do I find which page broke when the template is fine?",
             "Validate the rendered output rather than the template. These faults come from data "
             "interpolated without escaping, so they appear only on the records whose text "
             "happens to contain a quote or a line break."),
        ],
    )


if __name__ == "__main__":
    print(json_ld_errors())
