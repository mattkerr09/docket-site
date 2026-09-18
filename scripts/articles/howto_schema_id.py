"""An @id is a pointer, not a definition.

Promised on the how-to hub. Sourced from the registered check
`schema.incomplete` in `backend/seo_engine/checks/structured.py`, whose
docstrings record both halves of this:

  * the FALSE POSITIVE — Docket read each `@id` stub as its own incomplete
    entity, so a graph that defines an Organization AND references it by typed
    `@id` produced a multi-page "incomplete Organization markup" finding. That
    idiom is what the most widely used SEO plugins emit.
  * the REAL problem it was hiding — when every block of a type on a page is a
    bare reference and nothing on that page defines the target, "add the
    missing properties" is the wrong repair, because nobody forgot a property.

⚠️ VENDORS ARE NOT NAMED. The docstring names two plugin vendors as emitters;
the page says "the most widely used SEO plugins" instead. Nothing is lost and
the third-party gate is not tested.

⚠️ THE SCOPING SENTENCE MUST SURVIVE: Docket reads each page's markup on its
own, exactly as Google does, so it can say the target is absent HERE without
claiming it is absent everywhere.

Numerals: none. Quantities spelled as words.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402


def schema_id() -> Path:
    body = """
<p class="lede">An audit reports that several of your pages have incomplete Organization markup.
You open one and the Organization is right there — name, URL, logo, all of it. The blocks the tool
is complaining about are not incomplete entities. They are references to that one.</p>

<h2>What an @id actually does</h2>

<p>In JSON-LD, two nodes that share an <code>@id</code> <strong>are one node</strong>. That is the
whole point of the identifier, and it is what makes the common <code>@graph</code> pattern work:
define your company once, then point at it from everywhere else.</p>

<p>The pointer looks like this, and it is complete as written:</p>

<pre><code>"publisher": {
  "@type": "Organization",
  "@id": "https://example.com/#organization"
}</code></pre>

<p>It carries no properties <em>by design</em>. Nobody forgot anything. And because this is what
the most widely used SEO plugins and CMS platforms emit by default, a check that reads each stub
as its own half-finished entity will fire on an enormous share of the web — including sites whose
structured data is exactly right.</p>

<h2>The false positive, reproduced on purpose</h2>

<p>This one was not found on somebody's site and guessed at. It was reproduced with a controlled
input: a graph that <em>defines</em> an Organization with name, URL and logo, and also
<em>references</em> it by a typed <code>@id</code>. The result was a finding across several pages
saying the Organization markup was incomplete. Nothing was incomplete. The reference was being
counted as a second, worse copy of the thing it pointed at.</p>

<p>If your report says this about a site using a mainstream plugin, check the graph before you
touch anything. <strong>The stub is not the error; reading it as a definition is.</strong></p>

<h2>The real problem underneath, with the opposite fix</h2>

<p>Here is why this is worth more than "your tool was wrong". There is a genuine defect that looks
identical from the outside, and it is common.</p>

<p><strong>Structured data is read one page at a time.</strong> A search engine parsing your
product page does not go and fetch your homepage to resolve an identifier. So if every block of a
type on a page is a bare <code>@id</code> reference, and nothing on <em>that page</em> says what
the identifier refers to, the reference resolves to nothing.</p>

<p>And "add the missing properties" is precisely the wrong instruction, because it misdescribes
what happened. Nobody forgot a property. Somebody wrote a reference, deliberately, believing the
definition exists somewhere — which it may well do, on a different page, where it cannot help.
Telling them to add a name to each stub asks them to duplicate a definition they think they
already have.</p>

<p>The two repairs that are actually available:</p>

<ul>
<li><strong>Define the entity on every page that references it.</strong> This is what plugins do
when configured properly, and it is why their output repeats the Organization block everywhere.</li>
<li><strong>Remove the stub.</strong> If you are not going to define it, the pointer is doing
nothing for you.</li>
</ul>

<h2>Why nothing catches this</h2>

<p>A dangling <code>@id</code> produces <strong>neither a rich result nor an error</strong>, which
is the most useful sentence on this page.</p>

<ul>
<li><strong>A JSON-LD validator</strong> sees syntactically valid JSON-LD with a valid identifier,
and passes it.</li>
<li><strong>A rich-results test</strong> finds no eligible entity and reports that nothing was
detected — which reads like "you have no markup" rather than "you have a pointer to nowhere", and
sends you off to add markup you already wrote.</li>
<li><strong>Your CMS</strong> renders exactly what you configured.</li>
</ul>

<p>It is a failure of resolution, not of syntax, and syntax is what most tooling checks.</p>

<h2>What a tool can honestly say about it</h2>

<p>Worth stating because it bounds the finding. A crawler reads each page's markup on its own,
exactly as a search engine does. So it can tell you the target is <strong>absent here</strong>. It
cannot tell you the target is absent everywhere, because it is not resolving your graph across
your whole site — and neither is the search engine, which is the entire reason this matters.</p>

<h2>Checking your own markup in five minutes</h2>

<ul>
<li><strong>View source on a page that was flagged</strong> and search for the identifier from the
finding. If it appears twice — once as a definition with properties, once as a reference — your
markup is fine and the finding is wrong.</li>
<li><strong>If it appears only as a reference</strong>, the page genuinely defines nothing. That is
the real version of this problem.</li>
<li><strong>Check the type matches.</strong> A stub typed <code>Organization</code> pointing at a
node defined as something else is a third failure, and a quieter one.</li>
<li><strong>Check the identifier is stable.</strong> An <code>@id</code> that changes between
pages defeats the purpose — the nodes stop being one node.</li>
</ul>

<h2>When this does not matter</h2>

<p>Two cases where a bare reference is fine as it stands:</p>

<ul>
<li><strong>The definition is on the same page, further down the graph.</strong> Order does not
matter within a document.</li>
<li><strong>The entity is not one you are seeking a rich result for.</strong> A pointer that
resolves to nothing costs you an entity signal, not a search feature, and if the block was
aspirational rather than load-bearing you can simply delete it.</li>
</ul>

<h2>The fixes that make it worse</h2>

<ul>
<li><strong>Adding a name to every stub.</strong> You now have several partial definitions of one
entity instead of one good one, which is worse than either the pointer or the definition alone.</li>
<li><strong>Deleting the <code>@graph</code>.</strong> The graph is not the problem and it is the
structure that makes references work at all.</li>
<li><strong>Pointing the <code>@id</code> at a page URL.</strong> An identifier is not a link. It
does not get fetched, and a URL that happens to exist does not make the node resolve.</li>
</ul>

<h2>How to clear this finding without improving anything</h2>

<p>Delete the reference blocks. The finding goes away, and so does any chance of the entity being
understood — you have removed the evidence of an intention rather than completing it. Worth
knowing, because "it went green" and "it got better" are different outcomes and only one of them
is visible in a report.</p>

<h2>Where this sits in an audit</h2>

<p>The registered check is <code>schema.incomplete</code>, which covers incomplete structured data
in the structured data area. For the other ways JSON-LD goes wrong — blocks that do not parse,
markup contradicting the visible page, required properties genuinely missing — see
<a href="/how-to/fix-structured-data-errors/">how to fix structured data errors &rarr;</a>.</p>

<p>And for the general habit this page is an instance of — a finding whose own advice does not fit
the case it fired on — see <a href="/how-to/findings-that-flag-correct-pages/">a caveat is not a
gate &rarr;</a>.</p>
"""
    return render(
        cat="how-to", slug="schema-id-references",
        title="An @id is a pointer, not a definition",
        desc=("Two schema blocks sharing an @id are one node. Why an audit calls valid markup "
              "incomplete, and when a pointer on a site resolves to nothing."),
        h1="An @id is a pointer, not a definition",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / Schema references',
        body=body,
        faq=[
            ("What does @id mean in JSON-LD?",
             "It identifies a node. Two blocks sharing an @id are the same node, which is what "
             "lets you define an entity once and reference it from elsewhere in the same "
             "document."),
            ("My audit says my Organization markup is incomplete but it looks fine. Why?",
             "Probably because the blocks it flagged are @id references to a definition "
             "elsewhere in the graph. A reference carries no properties by design, and a tool "
             "reading it as its own entity will call it incomplete."),
            ("Can an @id point at a definition on another page?",
             "No, not usefully. Structured data is read one page at a time, so a reference to a "
             "node defined on a different page resolves to nothing on the page that carries the "
             "reference."),
            ("Why does no validator catch a dangling @id?",
             "Because it is valid JSON-LD. Validators check syntax; this is a failure of "
             "resolution. A rich-results test reports that nothing was found, which reads like "
             "missing markup rather than a pointer to nowhere."),
            ("Should I add the missing properties to each reference block?",
             "No. That duplicates a definition rather than fixing one. Either define the entity "
             "on each page that references it, or remove the stub — as it stands it produces "
             "neither a rich result nor an error."),
        ],
    )


if __name__ == "__main__":
    print(schema_id())
