#!/usr/bin/env python3
"""/ai-assistants/: Docket SEO in Claude Desktop, Claude Code and ChatGPT, with what the free version returns.

Matthew, 2026-11-07 00:1xZ via the CEO: "make sure we're seen by Claude ... on there too and indexed and everything"
(~/ops/launch/MOMENTUM-PLAN-2026-11-06.md section 5). /ai-assistants/ answered 404. Bookbreaker's page of the same
name is the format: one short block per assistant, the exact command, then what comes back and how it was tested.

The reference page with every tool's arguments stays /how-to/audit-your-site-from-an-ai-assistant/; this one is the
front door, so it gives the install steps and the free result and links there for the detail.

EVERY RESULT IS MEASURED. data/ai-assistants-run.json holds one run of the released bundle, started the way Claude
Desktop starts it, with the key left empty and a temporary home. The Claude Code and Claude Desktop steps are from
Anthropic's own pages, read the same day, because this Mac has no Claude Code install and nobody here operates the
Claude app; the page says which is which.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import N_CHECKS, REPO, RELEASE, buy_block, download_url, render  # noqa: E402
from render import ISSUES, PRICE_COMPACT, FOUNDING_LINE, FREE_LINE, price_sentence  # noqa: E402
from brand import SITE_BRAND
from comparisons import _verified_note  # noqa: E402
from pages import email_box, free_result_figure  # noqa: E402

RUN = json.loads((Path(__file__).resolve().parents[2] / "data" / "ai-assistants-run.json").read_text())
ENGINE_MAC = "/Applications/Docket.app/Contents/Resources/docket/docket"
ENGINE_WIN = r"C:\Users\YOU\AppData\Local\Docket\docket\docket.exe"
CLAUDE_DESKTOP_HELP = ("https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-"
                       "on-claude-desktop")
CLAUDE_CODE_DOCS = "https://code.claude.com/docs/en/mcp"
#: The connector's listing in Claude's directory, published 2026-11-07 (loads in a browser; bots get a 403).
CLAUDE_DIRECTORY = "https://claude.ai/directory/docket-seo"
REMOTE = "https://mcp.docketseo.app/mcp"


def _install_links() -> tuple[str, str]:
    """One-click installs, in the format each editor documents (read 2026-11-07): VS Code's
    vscode:mcp/install?{url-encoded JSON} (code.visualstudio.com/api/extension-guides/ai/mcp) and Cursor's
    cursor://anysphere.cursor-deeplink/mcp/install?name=...&config={base64 JSON} (cursor.com/docs/mcp/install-links)."""
    import base64
    import urllib.parse
    vscode = "vscode:mcp/install?" + urllib.parse.quote(json.dumps({"name": "docket-seo", "type": "http", "url": REMOTE},
                                                                   separators=(",", ":")))
    cursor = ("cursor://anysphere.cursor-deeplink/mcp/install?name=docket-seo&config="
              + urllib.parse.quote(base64.b64encode(json.dumps({"url": REMOTE}, separators=(",", ":")).encode()).decode()))
    return vscode, cursor


def _day(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


def _bundle(platform: str) -> str:
    version = RELEASE.lstrip("v")
    return f"{REPO}/releases/download/{RELEASE}/Docket-{version}-{platform}.mcpb"


#: The bundles go through the hub's /dl counter like every other download, src ai-assistants-<os>. For a few hours on
#: 2026-11-06 they linked straight to the release, because the counter then forwarded only the DMGs and the installer
#: (verify_download_path.py caught it); the hub accepts .mcpb since worker version 53a39145 (CEO, 2026-11-07).
def ai_assistants() -> Path:
    when = _day(RUN["measured"])
    # The run audited whichever host RUN["site"] names: the old address reads as history, the current one as this site.
    site_description = ("this site's address until November 2026"
                        if SITE_BRAND == "checkengine" and RUN["site"] == "docketseo.app" else "this site")
    vscode_link, cursor_link = _install_links()
    purchase = (buy_block("ai-assistants", try_app="ai-assistants-try-free")
                .replace(' dl-mac', '').replace(' dl-win', '')
                .replace('>Try it free</a>', '>Try it free for Mac</a>'))
    links = " · ".join(
        f'<a href="{download_url("ai-assistants-" + key.split("-")[0], to=_bundle(key))}" data-ev="Download" '
        f'data-ev-button="ai-assistants-{key.split("-")[0]}">{label}</a>'
        for key, label in (("macos", "Mac"), ("windows-x64", "Windows"), ("linux-x86_64", "Linux")))
    body = f"""
<p class="lede">The Docket SEO connector checks one page at a time, free, with nothing to install.
To check every page of a site, run Docket SEO on your Mac or PC. The free version crawls the whole site
and shows your score, how many problems each area has, and the worst one in full with its fix.</p>
{purchase}
{email_box()}
<p class="hero-note">Checked {_day(RUN["measured"])}.</p>

<h2>From one page to the whole site</h2>
<div class="wrap-tbl"><table class="cmp">
<caption>What the connector and the desktop app check</caption>
<thead><tr><th scope="col"> </th><th scope="col">The connector in Claude</th>
<th scope="col">Docket, free</th><th scope="col">Docket, with a licence</th></tr></thead>
<tbody>
<tr><th scope="row">Pages</th><td>One per check</td><td>The whole site</td><td>The whole site</td></tr>
<tr><th scope="row">What it shows</th><td>Score, the problems on that page, the first fix</td>
<td>Score, problem count per area, the worst problem with its fix</td>
<td>Every finding, ranked, with the markup to paste</td></tr>
<tr><th scope="row">Runs on</th><td>Our server</td><td>Your computer</td><td>Your computer</td></tr>
<tr><th scope="row">Works in</th><td>claude.ai, Claude Desktop, mobile, Claude Code</td>
<td>The app, Claude Desktop extension, Claude Code</td><td>The same</td></tr>
<tr><th scope="row">Price</th><td>Free</td><td>Free</td><td>{PRICE_COMPACT}. See the
<a href="#licence">licence and current price</a> below.</td></tr>
</tbody></table></div>
{free_result_figure()}

<h2>Audits through MCP</h2>
<p>Docket's MCP server runs the free audit with no licence key. {FREE_LINE}</p>
<p>Screaming Frog lists its MCP Server as a paid feature, and Sitebulb lists MCP access on its paid plans
and offers a trial.</p>
{_verified_note("ai-assistants-mcp", closing="")}

<h2>Claude Desktop: install the extension</h2>
<p>Download the extension for your computer: {links}. Then, in Claude Desktop, open Settings, choose
Extensions under Desktop app in the newer layout, click Advanced settings and then Install Extension, and
pick the file. Leave the licence key setting empty for the free version, or paste the key from your Docket
receipt for every finding. These steps are from <a href="{CLAUDE_DESKTOP_HELP}" rel="nofollow noopener">Anthropic&rsquo;s
help page</a>, read {when}.</p>

<h2>Claude: add the connector, nothing to install</h2>
<p>Docket SEO&rsquo;s free checks also run as a connector on our server, so Claude can use them in a chat with
nothing installed. It is listed in <a href="{CLAUDE_DIRECTORY}" rel="noopener">Claude&rsquo;s connector directory</a>;
add it from there, or as a custom connector with this address:</p>
<pre><code>{REMOTE}</code></pre>
<p>The same address works in other editors that speak MCP:
<a class="btn-ghost" href="{vscode_link}" data-ev="Install" data-ev-button="ai-assistants-vscode">Add to VS Code</a>
<a class="btn-ghost" href="{cursor_link}" data-ev="Install" data-ev-button="ai-assistants-cursor">Add to Cursor</a></p>
<p>It needs no account and no key. Its five tools are read-only: a one-page SEO check with a score and the
first fix, which AI crawlers robots.txt lets in, a redirect trace, an HTTP header check, and a search snippet
preview. Try asking:</p>
<ul>
<li>&ldquo;Check docketseo.app/pricing/ for SEO problems and tell me what to fix first.&rdquo;</li>
<li>&ldquo;Which AI crawlers can read my site, and is anything blocking Claude or ChatGPT search?&rdquo;</li>
<li>&ldquo;Trace the redirects from http://example.com and check its security headers.&rdquo;</li>
<li>&ldquo;Will this title get cut off in Google: &lsquo;Emergency plumber in Grand Rapids, open 24 hours a day&rsquo;?&rdquo;</li>
</ul>
<p>The connector checks one page at a time. For a whole site, use the desktop app. What it sends and keeps
is on the <a href="/legal/privacy/">privacy page</a>; questions go to
<a href="mailto:support@docketseo.app">support@docketseo.app</a>.</p>

<h2>Claude Code: one line</h2>
<p>With the Docket app installed, run this in a terminal:</p>
<pre><code>claude mcp add --transport stdio docket -- {ENGINE_MAC} mcp</code></pre>
<p>On Windows the engine is <code>{ENGINE_WIN}</code>, with your own account name for <code>YOU</code>. The
syntax is from <a href="{CLAUDE_CODE_DOCS}" rel="nofollow noopener">Claude Code&rsquo;s MCP documentation</a>,
read {when}: everything after <code>--</code> is the command that starts the server.</p>

<h2>ChatGPT: the desktop app</h2>
<p>The ChatGPT desktop app can start a local MCP server. Add one, choose STDIO, and give it the same engine
path with the argument <code>mcp</code>. This local setup does not work in ChatGPT on the web, which only
reaches servers on the internet. The <a href="/how-to/audit-your-site-from-an-ai-assistant/">full
setup guide</a> has OpenAI&rsquo;s wording and every tool&rsquo;s options.</p>

<h2>What the free version returns</h2>
<p>On {when} we took the released {RUN["release"]} Mac extension, started it the way Claude Desktop does
with the key setting empty and a fresh home folder, and asked it to audit <span data-brand-history>{RUN["site"]}</span>, {site_description}. It
answered in {RUN["seconds"]:g} seconds with a score of {RUN["score"]:g} ({RUN["grade"]}),
{RUN["problems"]} problems across {RUN["areas"]} areas, and the top one in full: &ldquo;{RUN["top_title"]}&rdquo;,
with where it is and the change to make. Its tool list also offers
{", ".join(f"<code>{t}</code>" for t in RUN["tools"][1:])}; the three that read kept audits have nothing to
read until a copy is activated, because a free audit is not kept.</p>
<p>With a key, the same question returns every finding, ranked, with the markup to paste, from the same
{N_CHECKS} checks the app runs.</p>

<h2>How it was tested</h2>
<ul>
<li><strong>Claude Desktop&rsquo;s extension:</strong> the released file, started exactly as its manifest
tells Claude Desktop to start it, on this Mac on {when}, and on a clean Windows machine when it shipped. The
clicks inside the Claude app are Anthropic&rsquo;s.</li>
<li><strong>Claude Code and ChatGPT:</strong> the command is the one the extension runs. The client syntax is
from each maker&rsquo;s documentation, not run here.</li>
<li><strong>Local audits stay on your computer.</strong> The app and extension do not upload them to us. The
remote connector runs its checks on our server. What
an audit does contact, and how to turn the optional parts off, is on the
<a href="/legal/privacy/">privacy page</a>.</li>
</ul>

<h2 id="licence">What a Docket SEO licence includes</h2>
<p>A licence unlocks every finding from the app&rsquo;s {N_CHECKS} checks, ranked, with the markup to paste.
It also unlocks the full result in the Claude Desktop extension and the local engine used by Claude Code.
Those audits run on your computer. The remote connector&rsquo;s five free checks need no licence.</p>
<p>{price_sentence()} No subscription. {FOUNDING_LINE}</p>

<h2>Missing a check?</h2>
<p><a href="{ISSUES}" rel="noopener">Ask for it on the public issue tracker</a>, or report a problem there.
Please leave private site details out of a public issue.</p>

<h2>Related</h2>
<ul>
<li><a href="/how-to/audit-your-site-from-an-ai-assistant/">Every tool and option, in full</a></li>
<li><a href="/learn/claude-search-crawlers/">Which crawlers feed Claude&rsquo;s web search?</a></li>
<li><a href="/tools/seo-checker/">Free SEO checker, in your browser</a></li>
</ul>
"""
    return render(
        cat="ai-assistants", slug="",
        title="Docket SEO in Claude and ChatGPT",
        desc=("Check one page free with the Docket SEO connector in Claude. "
              "Crawl the whole site on your Mac or PC, free, then unlock every finding with a licence."),
        h1="Docket SEO in Claude and ChatGPT",
        crumb='<a href="/">Docket</a> / AI assistants',
        body=body,
        published="2026-11-06",   # first published; the run below it is re-made each release
        modified="2026-11-11",
        schema_type="WebPage",
        faq=[
            ("Can Claude audit my website?",
             "Yes. The free connector checks one page on our server. For a whole site, install the Claude Desktop "
             "extension or add Docket to Claude Code; that audit runs on your computer."),
            ("Does Docket SEO work in ChatGPT?",
             "In the ChatGPT desktop app, which can start a local MCP server. Not on the web, which only reaches "
             "servers on the internet."),
            ("Is the Claude extension free?",
             "Yes. Without a key it returns the score, problem counts by area and the top problem in full. A key "
             "from a Docket purchase unlocks every finding."),
        ],
    )


BUILDERS = [ai_assistants]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]
