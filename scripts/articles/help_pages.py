"""Help routes. Each answer is condensed from the page named in its data record."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path

import facts as F
import brand
import render as R


def answer_values() -> dict:
    price_words = (
        f"{R.SALE_NAME}: {R.FOUNDING_NOW} once, through {R.FOUNDING_END_DAY}. "
        f"From {R.FOUNDING_AFTER_DAY}: {R.LATER_STR}."
        if R.FOUNDING_OPEN else f"{R.PRICE_STR}, paid once."
    )
    return {
        "PRICE_WORDS": price_words,
        "PRICE_CLAIM": price_words if R.FOUNDING_OPEN else f"Docket is {R.PRICE_STR}, paid once",
        "STORE_NOTE": brand.STORE_NOTE,
        "PLATFORMS": R.PLATFORMS,
        "MACOS": R.MACOS,
        "MAC_HW": R.MAC_HW,
        "LICENCE_COVERS": F.licence_covers(),
        "REFUND_DAYS": R.REFUND_DAYS,
        "SUPPORT_EMAIL": R.SUPPORT_EMAIL,
        "N_LANES": R.N_LANES,
        "FREE_LINE": R.FREE_LINE,
    }


def answers() -> list[dict]:
    return json.loads((R.DATA / "help-answers.json").read_text(encoding="utf-8"))


def question_answer(item: dict, *, brief: bool = False) -> tuple[str, str]:
    template = item.get("help_answer", item["answer"]) if brief else item["answer"]
    answer = escape(template.format_map(answer_values()))
    if "{PRICE_WORDS}" in template and R.FOUNDING_OPEN:
        launch = escape(f"{R.SALE_NAME}: {R.FOUNDING_NOW} once, through {R.FOUNDING_END_DAY}.")
        answer = answer.replace(launch, f'<span{R.FOUNDING_UNTIL}>{launch}</span>', 1)
    source = escape(item["source"]["source_path"], quote=True)
    return escape(item["question"]), f'{answer} <a href="{source}">More: full guide</a>'


def help_index() -> Path:
    quick = {item["id"]: item for item in answers()}
    body = """
<p class="lede">Want to run your first audit, unlock the full report or check a finding?
Start with the task below. Each link goes to the guide that explains it.</p>

<h2>Get it running on Mac and Windows</h2>
<ul>
<li><a href="/download/">On a Mac: choose the Mac or Intel download and run your first audit</a>.</li>
<li><a href="/download/">On Windows: get the installer or the Microsoft Store app</a>.</li>
</ul>

<h2>Buy and activate</h2>
<ul>
<li><a href="/pricing/">Check the price and what a purchase includes</a>.</li>
<li><a href="/download/">Find the key on your receipt and paste it into the app</a>.</li>
<li><a href="/legal/terms/">Read the licence rules and how to move to another computer</a>.</li>
<li><a href="/legal/refunds/">Read the refund policy and how to ask</a>.</li>
</ul>

<h2>Read the report</h2>
<ul>
<li><a href="/learn/seo-audit/">Understand what an audit covers and how to read it</a>.</li>
<li><a href="/learn/priority-model/">See how findings are put in order</a>.</li>
<li><a href="/score-card/">Read a score card and see what the full report adds</a>.</li>
<li><a href="/learn/what-docket-checks/">Look up what Docket checks</a>.</li>
</ul>

<h2>Use it with an AI assistant</h2>
<ul>
<li><a href="/how-to/audit-your-site-from-an-ai-assistant/">Set up the local MCP connection on Mac or Windows</a>.</li>
<li><a href="/ai-assistants/">Choose between a single-page check and a whole-site audit</a>.</li>
</ul>

<h2>Fix a problem</h2>
<ul>
<li><a href="/how-to/">Find the fix guide for a problem in your audit</a>.</li>
<li><a href="/contact/">Report a crash, bug or finding you think is wrong</a>.</li>
</ul>
<p>Need to contact us? <a href="/support/">Get help with a purchase or prepare a bug report</a>.</p>
<p>Still deciding, or just installed? <a href="/faq/">Read the buyer and setup questions</a>.</p>
"""
    return R.render(
        cat="help", slug="", title="Docket help: setup, reports and fixes",
        desc="Get help with your Docket site audit on Mac or Windows. Find setup, activation, report guides, AI assistant setup and support.",
        h1="What do you need help with?",
        crumb='<a href="/">Docket</a> / Help', body=body,
        schema_type="CollectionPage",
        faq=[question_answer(quick[key], brief=True) for key in ("try", "price", "activate")],
    )


def support() -> Path:
    body = f"""
<p class="lede">Need help with a licence, refund or payment? Email
<a href="mailto:{R.SUPPORT_EMAIL}">{R.SUPPORT_EMAIL}</a>, or reply to your receipt.
Keep those details private. <a href="/contact/">More: contact options</a>.</p>

<h2>A finding looks wrong</h2>
<p>Use the <a href="{R.ISSUES}/new">public issue tracker</a>. Send the details below so
the same crawl can be run and the finding can be checked.</p>
<ul>
<li>The URL you audited.</li>
<li>The check ID printed beside the finding.</li>
<li>What you expected instead, and why. Link to the specification or vendor documentation
if it supports your case.</li>
</ul>
<p><a href="/contact/">More: what a good bug report contains</a>.</p>

<h2>The app crashed or has a bug</h2>
<p><a href="{R.ISSUES}/new">Open an issue</a> and say what you were doing.
For a Mac or Windows report, include your macOS or Windows version.
<a href="/contact/">More: reporting a crash or bug</a>.</p>

<h2>A licence or payment problem</h2>
<p>Email <a href="mailto:{R.SUPPORT_EMAIL}">{R.SUPPORT_EMAIL}</a> or reply to your receipt.
These requests carry a name and order reference, so keep them out of the public tracker.
<a href="/contact/">More: private contact</a>.</p>
<ul>
<li><a href="/legal/terms/">Licence rules, moving computers and a lost or broken computer</a>.</li>
<li><a href="/legal/refunds/">Refund rules, how to ask and what happens to your copy</a>.</li>
</ul>

<h2>A security problem</h2>
<p>Use the <a href="{R.REPO}/security/advisories/new">private security advisory form</a>.
<a href="/contact/">More: reporting a security problem</a>.</p>

<h2>What happens next</h2>
<p>One person reads the inbox and tracker. A report with a URL and check ID gets a specific
answer. If Docket is wrong, the correction is written down where the mistake was made.
<a href="/contact/">More: what to expect back</a>.</p>
<p>For setup or help reading an audit, <a href="/help/">choose a help guide</a>.
For purchase and setup questions, <a href="/faq/">read the FAQ</a>.</p>
"""
    return R.render(
        cat="support", slug="", title="Docket support: licence, billing and bug reports",
        desc="Get Docket support for a licence, payment or site audit finding. Find what to send with a bug report and links to the refund and licence rules.",
        h1="Get help with Docket",
        crumb='<a href="/">Docket</a> / <a href="/help/">Help</a> / Support',
        body=body, schema_type="ContactPage",
    )


def faq() -> Path:
    items = answers()
    # Keep the shared FAQ renderer, including its visible markup and FAQPage schema.
    # Data order puts the buyer questions first, followed by installed-app help.
    body = """
<p class="lede">Can you try Docket before paying, and what happens after you install it?
The answers below cover the purchase, your first audit and where to get help.</p>
<p>Start with trying the app, its price, your computer and the licence. Then read about setup,
reports and problems after installing. Each answer links to the page with the full details.</p>
<p>Want a guide for a task? <a href="/help/">Choose a help guide</a>.
Need to report a problem? <a href="/support/">Contact support</a>.</p>
"""
    return R.render(
        cat="faq", slug="", title="Docket FAQ: buying, setup and your first audit",
        desc="Questions about buying Docket and running a site audit. Read about the free version, price, licence, Mac and Windows setup, reports and support.",
        h1="Before you buy and after you install",
        crumb='<a href="/">Docket</a> / <a href="/help/">Help</a> / FAQ',
        body=body, schema_type="", faq=[question_answer(item) for item in items],
    )


def build_all() -> list[Path]:
    return [help_index(), support(), faq()]
