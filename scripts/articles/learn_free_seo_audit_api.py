#!/usr/bin/env python3
"""Free API choices grounded in a saved quota response and local CLI help."""
from __future__ import annotations

from pathlib import Path

from learn_seo_audit_report import fact, note, quote, source
from render import render


def build() -> Path:
    failure = source('psi-checkengineseo-mobile.json')['error']
    body = f"""
<p class="lede">For a free SEO audit API, decide whether you need a web page performance result, a report for a script or an audit an AI assistant can read. Google's PageSpeed Insights API and a local site auditor answer different parts of that request.</p>
<p>Google's docs allow trial calls without a key. Below is what happened when we tried, followed by the command-line, local API and assistant options in Check Engine.</p>

<h2>What Google's API promises</h2>
<p>The PageSpeed Insights documentation describes web page performance checks and improvement suggestions using Lighthouse. It says the response includes performance scores, user experience metrics and Lighthouse audit results in JSON. That is a useful performance input when you are writing a script to review pages.</p>
<p>On keys, the documentation we read says:
{quote('To use it, an API key is optional for trial runs, but needed for automated multiple queries.', 'psi-doc-sentences.txt')}</p>
<p>Use a key if your script will keep asking for results. Keyless capacity can run out, as our request below shows.</p>
<p>Read the <a href="https://developers.google.com/speed/docs/insights/v5/get-started">PageSpeed Insights getting-started guide</a> and the <a href="https://developers.google.com/speed/docs/insights/rest/v5/pagespeedapi/runpagespeed">request reference</a> for Google's instructions.</p>

<h2>Our keyless request returned a quota error</h2>
<p>We made a keyless mobile request for checkengineseo.com. It returned
{fact('HTTP status', failure['code'], 'psi-checkengineseo-mobile.json', '/error/code')}.
The response says {quote("Quota exceeded for quota metric 'Queries' and limit 'Queries per day'", 'psi-checkengineseo-mobile.json')}.</p>
<p>The shared keyless daily quota was exhausted, so this call returned no Lighthouse score. We did not test a request with a key.</p>
<p>Keep an error response separate from the audit result your script expects. If you turn a failed request into an empty list of problems, the next person may read that as a clean result. For this request the honest output is that the service could not supply the measurement.</p>

<h2>A report for a script: the audit command</h2>
<p>If you want a site audit on your own computer, the local command-line help lists JSON, CSV, SARIF and JUnit among its output choices. You do not have to run a web service just to ask the command for a result. An example command using the JSON choice is:</p>
<pre><code>checkengine audit https://example.com -f json</code></pre>
<p>This example shows the command shape. We ran the help commands for this article; we did not run this example audit. Use the URL you intend to inspect, and decide how much of the site your review needs to cover before relying on its result.</p>
<p>Use <code>-f csv</code> if your next step works with CSV. The help describes <code>-f sarif</code> for systems that list findings as alerts, and <code>-f junit</code> for a test-report panel. Pick the format your next tool can read. The licence limits are below.</p>

<h2>A local API: keep it on this machine</h2>
<p><code>checkengine serve</code> runs the local API used by the desktop app. The help lists
{quote('default 127.0.0.1', 'cli-serve-help.txt')}. This is the loopback address, for access from the same computer.</p>
<pre><code>checkengine serve</code></pre>
<p>The help says the API has no authentication because it is only meant to be reachable from this machine. Its warning about changing the host is explicit:</p>
<blockquote><p>{quote('Binding it anywhere else exposes audit control and results to whoever can reach that address.', 'cli-serve-help.txt')}</p></blockquote>
<p>Keep your script and the API on the same computer. Use the loopback address when setting up the connection. We read the help without starting an API server.</p>

<h2>For an AI assistant: use MCP</h2>
<p><code>checkengine mcp</code> is the assistant route. The top-level command description says it serves the engine to an AI assistant over MCP using stdio. That means the assistant starts a local process and talks through that process's input and output.</p>
<pre><code>checkengine mcp</code></pre>
<p>Choose this when your next step is a conversation about the audit rather than a script making web requests. The existing developer guide says an unactivated copy returns the free result, while a licensed copy returns every finding and the ranked plan. See the <a href="/for/developers/#mcp">local MCP setup guide</a> for the configuration.</p>

<h2>Which results are free?</h2>
<p>The site's free-result description gives you the score, problem counts by category and the top problem in full with its fix. The paid version adds the rest of the problems, the ranked fix plan and markup to paste.</p>
<p>The developer guide says full findings and SARIF and JUnit files need a licence key. Choosing JSON leaves those licence limits in place. The help gives no full list of free CSV or local API results, so check access before building a workflow around them.</p>
<p>That leaves a practical choice. Try Google's service for the performance result its docs describe. Use the local audit command when you want script output from the installed app. Use the local API when your code needs to talk to that running app, or MCP when an assistant is doing the reading. In each case, decide what result you need before treating free as a description of the whole workflow.</p>

<h2>Source note</h2>
{note('psi_docs_read')}
{note('psi_call')}
"""
    return render(
        cat="learn", slug="free-seo-audit-api",
        title="Free SEO audit API: Google and local audit options",
        desc="See Google's key rules and our keyless quota error, then compare local JSON reports, the desktop API and MCP, with clear limits on free results.",
        h1="Free SEO audit API: what you can ask for",
        crumb='<a href="/learn/">Learn</a> / Free SEO audit API',
        body=body, published="2026-11-11",
        faq=[
            ("What should an automated audit do when no result comes back?",
             "Record that the measurement is unavailable and keep the error for review. Let the person using the report decide whether to retry or continue without that check."),
            ("Do I need to start the local API to request JSON?",
             "The audit command accepts a format choice on its own. Use the running API when your application needs a connection to the local app."),
            ("Can a hosted assistant reach my computer's loopback API?",
             "Loopback refers to the computer where the request runs. Use a supported local assistant connection rather than assuming a remote service can reach your installed app."),
            ("Does an API quota error describe my site's SEO health?",
             "It describes a failure to obtain that service's measurement. Keep it out of the site's pass and fail totals until there is an actual result to assess."),
        ],
    )


def build_all() -> list[Path]:
    return [build()]
