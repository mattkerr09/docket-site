#!/usr/bin/env python3
"""`docket mcp` — audit a site from an AI assistant.

⚠️ EVERY COMMAND AND EVERY QUOTED LINE ON THIS PAGE WAS RUN AGAINST THE SHIPPED
BINARY at /Applications/Docket.app/Contents/Resources/docket/docket, installed
from the notarised 1.3.44 DMG on 2026-09-08 — not against the source tree, which
behaves differently in the one way that matters most here.

Measured, in that order:

  * `docket mcp` `tools/list` returns exactly two tools: `audit_site`
    (required: url; optional max_pages, max_seconds, offline) and `list_checks`
    (no arguments).
  * `initialize` answers with serverInfo {"name": "docket", "version": "1.3.44"}
    and echoes the client's protocolVersion.
  * `list_checks` on the installed copy returns 97 checks across 13 lanes.
  * ⚠️ AND THE ONE THE SOURCE TREE WOULD HAVE HIDDEN: an unactivated copy
    REFUSES `audit_site` with "This copy of Docket is not activated", while
    `list_checks` still answers. Run from source, `licence.mode()` is "free" and
    the gate is inert, so a page written from a source-tree run would have told
    customers the audit works before activation. It does not. The shipped
    binary is stamped, and the gate that stops it is the same one `run_audit`
    applies to the CLI and the app.

The config path is stated rather than written by us: `claude_desktop_config.json`
exists at the documented location on this machine, so the path is confirmed, but
editing a customer's assistant config is theirs to do.

⚠️ THE PROVENANCE LINE ON THE PAGE CARRIES A DATE AND NO VERSION NUMBER, AND
THAT IS THE WHOLE DESIGN. The CEO session asked for "measured against 1.3.44
(build 922) on 2026-09-08" so the page is falsifiable, which is the right
instinct — but a typed version on a page is what `verify_version_strings`
exists to refuse, and its message is "Derive it, or delete it". Deriving it
from RELEASE would be worse than typing it: at 1.3.45 the page would claim a
measurement against a build nobody ran these commands on, which is the
freshness lie rule 5 catches for competitor prices, pointed at ourselves.

The asymmetry is the way out. **"Last run on 2026-09-08" never becomes false.**
"Measured against 1.3.44" becomes false the moment 1.3.45 ships. So the page
carries the date, which stays true forever, and points the reader at their own
handshake for the version — which is a live product behaviour rather than a
claim about a past run, and is a stronger falsifier than our stamp anyway.

The frozen basis lives here instead, where it cannot mislead a customer:
1.3.44, build 922, measured 2026-09-08.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import N_CHECKS, N_LANES, PRICE_STR, render  # noqa: E402

SIDECAR = "/Applications/Docket.app/Contents/Resources/docket/docket"

#: The day these commands were last run against a shipped build. It is a
#: DATE and not a version on purpose — see the module docstring.
MEASURED_HUMAN = "8 September 2026"


def mcp_setup() -> Path:
    body = f"""
<p class="lede">Docket speaks the <strong>Model Context Protocol</strong>, the standard AI
assistants use to reach tools on your own machine. Point an MCP client at the copy of Docket
you already own and you can ask it to audit a site in conversation, and get the findings back
as structured data it can reason about &mdash; rather than a screenshot you retype.</p>

<h2>Point your assistant at it</h2>

<p>Docket serves MCP over stdio, so there is no server to run and no port to open. The client
launches Docket itself. In Claude Desktop, open
<code>~/Library/Application&nbsp;Support/Claude/claude_desktop_config.json</code> and add:</p>

<pre><code>{{
  "mcpServers": {{
    "docket": {{
      "command": "{SIDECAR}",
      "args": ["mcp"]
    }}
  }}
}}</code></pre>

<p>That path is the audit engine inside the installed app, not the app icon you click. Restart
the client and Docket appears as a tool. Any MCP client works the same way &mdash; the command
and the argument are all it needs.</p>

<p class="note"><strong>Every answer on this page was produced by running these commands</strong>
against a shipped, notarised build on {MEASURED_HUMAN} &mdash; not against a development
checkout, which behaves differently in the one way that matters most here (see the licence
section below). Your own copy reports its version in the MCP handshake, so you can check this
page against what you actually have; if it disagrees, the page is wrong and we want to hear
about it.</p>

<h2>The two tools</h2>

<p><code>audit_site</code> crawls a site and returns the score and every finding: how bad it is,
which pages it affects, how long the fix takes and the change to make. It takes a
<code>url</code>, and optionally <code>max_pages</code>, <code>max_seconds</code> and
<code>offline</code>.</p>

<p><code>list_checks</code> takes no arguments and answers &ldquo;what does Docket actually
check?&rdquo; without crawling anything. On this copy it returns all {N_CHECKS} checks
across {N_LANES} areas.</p>

<p>Two details worth knowing, because they are choices rather than accidents. The page budget you
ask for is the page budget you get &mdash; Docket will not quietly crawl five times more because
the site answered quickly, which is what its own <code>--adaptive</code> default does when a
person is watching. And <code>offline</code> keeps a run entirely local: no PageSpeed call, no
DNS lookup, nothing leaving the machine.</p>

<h2>It is the same engine, and the same licence</h2>

<p>Nothing about this is a cloud service. The crawl runs on your Mac exactly as it does when you
click the button, there is no API key, and there is no per-call charge &mdash; your assistant is
talking to the app you bought, not to us.</p>

<p>Which also means an unactivated copy will not audit. Ask it to and it answers:</p>

<pre><code>This copy of Docket is not activated. Enter your licence key to run an
audit — you can find it in the email from your purchase.</code></pre>

<p><code>list_checks</code> still works, because it crawls nothing. Activate once with
<code>docket licence --key YOUR-KEY</code>, or in the app, and the audit tool works from then on.
Docket is {PRICE_STR} once, so there is no seat to add for the assistant.</p>

<h2>What it does not do</h2>

<p>The MCP surface is deliberately small: two tools, not a wrapper around every command. It does
not schedule audits, compare two crawls the way <code>docket diff</code> does, or expose the
site-history features. If you want those, they are in the app and the CLI, and the honest answer
is that nobody has yet asked for them through an assistant.</p>
"""
    return render(
        cat="how-to", slug="audit-your-site-from-an-ai-assistant",
        title="Audit your site from an AI assistant",
        desc=("Docket speaks the Model Context Protocol over stdio. Point Claude Desktop "
              "at the app you own and ask it to audit a site — no API key, no cloud."),
        h1="How to audit your site from an AI assistant",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / MCP',
        body=body,
        faq=[
            ("Does Docket work with Claude Desktop?",
             "Yes. Add Docket to mcpServers in claude_desktop_config.json with the command "
             f"{SIDECAR} and the argument mcp, then restart the client. Any MCP client works "
             "the same way, because Docket speaks the protocol over stdio."),
            ("Does using Docket through MCP cost extra?",
             "No. There is no API key and no per-call charge. The crawl runs on your own Mac, "
             "the assistant is talking to the copy of Docket you bought, and the licence is "
             "the same one-time purchase."),
            ("Can an assistant audit a site if Docket is not activated?",
             "No. Asking it to audit returns 'This copy of Docket is not activated'. Listing "
             "the checks still works, because that crawls nothing. The licence gate is the "
             "same one the app and the command line use, so MCP is not a way around it."),
        ],
    )
