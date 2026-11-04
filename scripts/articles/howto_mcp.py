#!/usr/bin/env python3
"""`docket mcp`. Audit a site from an AI assistant.

⚠️ EVERY COMMAND AND EVERY QUOTED LINE ON THIS PAGE WAS RUN AGAINST THE SHIPPED
BINARY at /Applications/Docket.app/Contents/Resources/docket/docket, installed
from the notarised 1.3.44 DMG on 2026-09-08, not against the source tree, which
behaves differently in the one way that matters most here.

Measured, in that order:

  * `docket mcp` `tools/list` returns exactly two tools: `audit_site`
    (required: url; optional max_pages, max_seconds, offline) and `list_checks`
    (no arguments).
  * `initialize` answers with serverInfo {"name": "docket", "version": "1.3.44"}
    and echoes the client's protocolVersion.
  * `list_checks` on the installed copy returned 97 checks across 13 lanes
    WHEN THIS WAS MEASURED, against the 1.3.44 named two lines above. The
    engine registers 99 as of 2026-09-21 and the rendered page reads that
    from facts rather than from here, so the page is right and this line is
    a record of one run. Left as a record rather than bumped, because
    nobody re-ran `list_checks` today. The count came from the source and
    from the frozen build's own `docket checks`.
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
instinct, but a typed version on a page is what `verify_version_strings`
exists to refuse, and its message is "Derive it, or delete it". Deriving it
from RELEASE would be worse than typing it: at 1.3.45 the page would claim a
measurement against a build nobody ran these commands on, which is the
freshness lie rule 5 catches for competitor prices, pointed at ourselves.

The asymmetry is the way out. **"Last run on 2026-09-08" never becomes false.**
"Measured against 1.3.44" becomes false the moment 1.3.45 ships. So the page
carries the date, which stays true forever, and points the reader at their own
handshake for the version, which is a live product behaviour rather than a
claim about a past run, and is a stronger falsifier than our stamp anyway.

The frozen basis lives here instead, where it cannot mislead a customer:
1.3.44, build 922, measured 2026-09-08.

RE-MEASURED 2026-11-03 on a temp copy of the live v1.3.140 DMG (build d34e7d0, 1459), temp HOME, no key, for the
CEO's order from Matthew ("make sure all of our apps are easily usable by Claude and ChatGPT"):
  * initialize: serverInfo {"name": "docket", "version": "1.3.140"}; tools/list: audit_site (url, max_pages,
    max_seconds, offline) and list_checks.
  * ⚠️ audit_site on the UNACTIVATED copy now returns the free version (score, area counts, one worked fix,
    `free.counts_only` true), not "not activated". The FAQ said it refused, which stopped being true when the free
    version shipped in 1.3.96, while this page's own body already said the free version runs. Fixed here.
  * Windows: the installer puts the engine at %LOCALAPPDATA%\\Docket\\docket\\docket.exe (signed CI run 41709362986,
    "installed to C:\\Users\\runneradmin\\AppData\\Local\\Docket").
  * ChatGPT, from OpenAI's own pages read the same day: on the web, custom MCP connections are for Business and
    Enterprise/Edu workspaces and need "your server's public HTTPS MCP endpoint URL" (help.openai.com 12584461);
    "The ChatGPT desktop app, Codex CLI, and IDE extension support MCP servers", including stdio servers "that run
    as a local process" (learn.chatgpt.com/docs/extend/mcp). So the page says the desktop app can run Docket and
    the web cannot, and claims nothing it has not read.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import N_CHECKS, N_LANES, PRICE_STR, render  # noqa: E402

SIDECAR = "/Applications/Docket.app/Contents/Resources/docket/docket"
#: The engine on Windows, under the per-user install folder. Written with YOU for the account name: the folder is
#: the reader's own AppData, which this page cannot know.
WIN_ENGINE = r"C:\Users\YOU\AppData\Local\Docket\docket\docket.exe"

#: The day these commands were last run against a shipped build. It is a
#: DATE and not a version on purpose — see the module docstring.
MEASURED_HUMAN = "3 November 2026"


def mcp_setup() -> Path:
    body = f"""
<p class="lede">Docket speaks the <strong>Model Context Protocol</strong>, the standard AI
assistants use to reach tools on your own machine. Point an MCP client at the copy of Docket
you already own and you can ask it to audit a site in conversation, and get the findings back
as structured data it can reason about: rather than a screenshot you retype.</p>

<h2>Point your assistant at it</h2>

<p>Docket serves MCP over stdio, so there is no server to run and no port to open. The client
launches Docket itself, with one command and one argument.</p>

<h3>Claude Code</h3>

<p>One line in a terminal:</p>

<pre><code>claude mcp add docket -- {SIDECAR} mcp</code></pre>

<p>On Windows, use the engine inside your install folder instead:
<code>claude mcp add docket -- "{WIN_ENGINE}" mcp</code>, with your own account name in place of
<code>YOU</code>.</p>

<h3>Claude Desktop</h3>

<p>On a Mac, open
<code>~/Library/Application&nbsp;Support/Claude/claude_desktop_config.json</code> and add:</p>

<pre><code>{{
  "mcpServers": {{
    "docket": {{
      "command": "{SIDECAR}",
      "args": ["mcp"]
    }}
  }}
}}</code></pre>

<p>That path is the audit engine inside the installed app, not the app icon you click. On Windows
the file is <code>%APPDATA%\\Claude\\claude_desktop_config.json</code> and the command is
<code>{WIN_ENGINE.replace(chr(92), chr(92) * 2)}</code>, with each backslash doubled because the
file is JSON. Restart the client and Docket appears as a tool. Any MCP client works the same
way: the command and the argument are all it needs.</p>

<h3>ChatGPT</h3>

<p>The ChatGPT desktop app can run it: OpenAI's documentation says the desktop app supports MCP
servers, including ones that run as a local command. Open Settings, then MCP servers, add a
server, choose STDIO, and give it the same command and the argument <code>mcp</code>. ChatGPT
on the web cannot. There, custom connections are for business workspaces and need a public
HTTPS server, and Docket runs on your own computer rather than on the internet.</p>

<p class="note"><strong>Every tool answer on this page was produced by calling a shipped,
notarised build</strong> on {MEASURED_HUMAN} (the handshake, the tool list and what an
unactivated copy returns), not a development checkout, which behaves differently in the one
way that matters most here (see the licence section below). Your own copy reports its version in the MCP handshake, so you can check this
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
ask for is the page budget you get. Docket will not quietly crawl five times more because
the site answered quickly, which is what its own <code>--adaptive</code> default does when a
person is watching. And <code>offline</code> turns off the optional checks (no PageSpeed
call, no DNS lookup of your mail domains) though the link check and rendering still reach
the sites your pages link to or load.</p>

<h2>It is the same engine, and the same licence</h2>

<p>Nothing about this is a cloud service. The crawl runs on your Mac exactly as it does when you
click the button, there is no API key, and there is no per-call charge. Your assistant is
talking to the app you bought, not to us.</p>

<p>Which also means an unactivated copy gives your assistant the free version: the audit runs,
and the result is the overall score, how many problems each area has and the top problem in full, with a note saying
what the paid version adds. <code>list_checks</code> works either way, because it crawls
nothing. Activate once with <code>docket licence --key YOUR-KEY</code>, or in the app, and the
audit tool returns every finding from then on.
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
              "at the app you own and ask it to audit a site: no API key, no cloud."),
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
             "Yes, the free version. The audit runs, and the assistant gets the overall score, how "
             "many problems each area has and the top problem in full with its fix. Activating the "
             "copy, in the app or with docket licence, makes the same tool return every finding."),
            ("Does Docket work with ChatGPT?",
             "In the ChatGPT desktop app, yes: add Docket under Settings, MCP servers, as a STDIO "
             "server with the command above and the argument mcp. ChatGPT on the web cannot run "
             "it, because there custom connections need a public HTTPS server and Docket runs on "
             "your own computer."),
        ],
    )
