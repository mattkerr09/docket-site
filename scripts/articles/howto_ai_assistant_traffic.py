#!/usr/bin/env python3
"""Find assistant link traffic without treating crawler requests as people."""
from __future__ import annotations

from pathlib import Path

from comparisons import source_link
from render import render

READ = "20 November 2026"
PUBLISHED = "2026-11-20"
SEARCH_HOURS = "24"
SLUG = "see-ai-assistant-traffic-in-analytics"
CHANNELS = "https://support.google.com/analytics/answer/9756891?hl=en"
ACQUISITION = "https://support.google.com/analytics/answer/12923437?hl=en"
REFERRALS = "https://support.google.com/analytics/answer/10327750?hl=en"
OPENAI = "https://developers.openai.com/api/docs/bots"
PERPLEXITY = "https://docs.perplexity.ai/docs/resources/perplexity-crawlers"


def source_note(company: str, *sources: tuple[str, str]) -> str:
    links = ', '.join(source_link(label, url) for label, url in sources)
    return (f'<p class="verified-note">Sources read {READ} on {company}\'s own pages: '
            f'{links}.</p>')


def bot_note() -> str:
    return (f'<p class="verified-note">Sources read {READ}: '
            f'{source_link("OpenAI crawler guide", OPENAI)} on OpenAI\'s own site; '
            f'{source_link("Perplexity crawler guide", PERPLEXITY)} on Perplexity\'s own site.</p>')


def faq_source(text: str, company: str, label: str, url: str) -> str:
    return f'{text} Source: {source_link(company + " " + label, url)}, read {READ}.'


def build() -> Path:
    body = f"""
<p id="measured-answer">Google Analytics has a default channel called AI Assistant:
{source_link("Google's examples", CHANNELS)} name ChatGPT, Gemini, Deepseek, Copilot and Grok,
and exclude Google's AI Overviews and AI Mode.
Open Reports, then Acquisition, then Traffic acquisition and look for AI Assistant.
Then check Session source for <code>perplexity.ai</code> and <code>chatgpt.com</code>;
Google's examples do not name Perplexity, so check the source rather than assuming its channel.</p>
{source_note("Google", ("Google default channel group", CHANNELS), ("Google Traffic acquisition report", ACQUISITION))}

<h2>Find the AI Assistant channel</h2>
<ol>
<li>Open your site's Google Analytics property and select <strong>Reports</strong>.</li>
<li>Select <strong>Acquisition</strong>, then <strong>Traffic acquisition</strong>.</li>
<li>In the table, use <strong>Session default channel group</strong> and look for
<strong>AI Assistant</strong>.</li>
</ol>
<p>Use Traffic acquisition to look at where new and returning users came from.
User acquisition covers new users only. If Traffic acquisition is missing, Google says
it may have been removed or may not be in your default view. Ask someone with editor
access or above to add it back.</p>
<p>The channel follows a rule, not a guess based on a site's name. Google says that when
the referrer matches its list of AI assistants, the medium is set to
<code>ai-assistant</code> and the campaign to <code>(ai-assistant)</code>.
The channel condition is that the medium exactly matches <code>ai-assistant</code>.</p>
{source_note("Google", ("Google Traffic acquisition report", ACQUISITION), ("Google default channel group", CHANNELS))}

<h2>Check the sources one by one</h2>
<p>A channel groups traffic. A source tells you where it came from. In Traffic acquisition,
change the table dimension to <strong>Session source / medium</strong> to read the source
beside its medium. Use <strong>Session source</strong> when you want just the source name.</p>
<ol>
<li>Choose <strong>Session source</strong> and search the table for
<code>perplexity.ai</code>. Note any matching rows.</li>
<li>Replace that search with <code>chatgpt.com</code> and note those rows too.</li>
<li>Use <strong>Session source / medium</strong> to check the medium next to each source.
Keep the same date range while comparing the views.</li>
</ol>
<p>A referral is a visit referred by another site. Google says Analytics shows those
sites' domain names as referral sources. Its Referral channel accepts the mediums
<code>referral</code>, <code>app</code> and <code>link</code>.</p>
<p>An assistant source may appear under Referral instead of AI Assistant because the
AI Assistant rule depends on Google's list of referrers. Google's examples do not name
Perplexity. That does not tell you whether it is in the list: check your own Session
source rows for <code>perplexity.ai</code>.</p>
<p>If you have set up unwanted referrals, review those conditions too. Google says a
match adds <code>ignore_referrer=true</code> to matching events. A source excluded that
way can disappear from referrals, so do not use that setting just to tidy the report.</p>
{source_note("Google", ("Google Traffic acquisition report", ACQUISITION), ("Google default channel group", CHANNELS), ("Google unwanted referrals guide", REFERRALS))}

<h2>Crawler visits are not visitors</h2>
<p>A request from a bot is not a person clicking a link. Server logs record requests.
Page-tag analytics records events when the page's analytics tag runs. A bot that does
not run that tag does not create a tagged page visit. Read crawler visits in server
logs, separately from people arriving through assistant links.</p>
<ul>
<li><strong>PerplexityBot</strong> is designed to surface and link websites in
Perplexity search results. Perplexity says it is not used to crawl content for AI
foundation models.</li>
<li><strong>Perplexity-User</strong> may visit a page when someone asks a question,
to help answer it and include a link. Perplexity says it generally ignores robots.txt
rules for these user requests.</li>
<li><strong>OAI-SearchBot</strong> is OpenAI's search crawler. OpenAI says you can
allow it for search results while blocking <strong>GPTBot</strong> for training.
Those settings are independent.</li>
<li><strong>ChatGPT-User</strong> visits pages for questions from ChatGPT or custom
GPT users. OpenAI says it is not an automatic web crawler and robots.txt rules may
not apply.</li>
</ul>
<p>For the crawler access checks, read our
<a href="/ai-crawlers/perplexitybot/">PerplexityBot guide</a> and
<a href="/ai-crawlers/chatgpt-user/">ChatGPT-User guide</a>.
Seeing any of these bot names in a log does not show that a person followed a link.</p>
{bot_note()}

<h2>If you see no AI traffic at all</h2>
<p>Start with access. Check whether your robots.txt rules or server block
<strong>OAI-SearchBot</strong> or <strong>PerplexityBot</strong> on the pages you want
people to find. OpenAI describes allowing OAI-SearchBot for search results;
Perplexity describes PerplexityBot as surfacing and linking websites in its results.
Keep the separate GPTBot training choice separate from search access.</p>
<p>After a robots.txt change, allow time for it to be picked up. OpenAI says its search
systems can take about {SEARCH_HOURS} hours to adjust. That is a note about its search
systems after the change, not a deadline for visits to appear.</p>
<p>Then check the page a visitor would reach. Is the analytics tag there, and does it
run? A page tag cannot record a page visit if it never runs. Use the
<a href="/how-to/analytics-findings-name-the-tag/">guide to finding the analytics tag</a>
to inspect the tag on that page.</p>
<p>Keep the checks separate: access, the tag, and the source rows.
A check cannot make an assistant cite you. Allowing a crawler does not promise a link,
a visitor or a ranking.</p>
{bot_note()}

<h2>Choose the next check</h2>
<p>Try the <a href="/tools/seo-checker/">free SEO checker</a> on the page you expect
visitors to reach. Use the full app below if you need to check across your site.
Return to the source rows to see whether people actually arrived.</p>
"""
    return render(
        cat="how-to", slug=SLUG,
        title="See ChatGPT and Perplexity traffic in Google Analytics",
        desc="Find the AI Assistant channel, check Perplexity and ChatGPT session sources, and keep crawler requests separate from people clicking assistant links.",
        h1="How to see ChatGPT and Perplexity visitors in Google Analytics",
        crumb='<a href="/">Check Engine</a> / <a href="/how-to/">Fix it</a> / AI assistant traffic',
        body=body, published=PUBLISHED, modified=PUBLISHED,
        faq=[
            ("Does Google Analytics count Google's AI Overviews as AI Assistant traffic?", faq_source(
                "No. Google's default channel guide excludes AI Overviews and AI Mode from the AI Assistant channel.",
                "Google", "default channel guide", CHANNELS)),
            ("Why might perplexity.ai appear as Referral rather than AI Assistant?", faq_source(
                "The AI Assistant rule depends on Google's list of referrers. Its examples do not name Perplexity, which does not establish whether it is in that list. Check Session source / medium for perplexity.ai in your own report.",
                "Google", "default channel guide", CHANNELS)),
            ("Does a ChatGPT-User request in my log prove someone clicked through?", faq_source(
                "No. ChatGPT-User can visit a page to help answer a user's question. That request is separate from a person following a link and running your page's analytics tag.",
                "OpenAI", "crawler guide", OPENAI)),
            ("Where should I look if the AI Assistant row is empty?", faq_source(
                "Check Session source for perplexity.ai and chatgpt.com before concluding that no assistant visitors arrived. Traffic acquisition lets you inspect Session source and Session source / medium as well as channels.",
                "Google", "Traffic acquisition report", ACQUISITION)),
        ],
    )
