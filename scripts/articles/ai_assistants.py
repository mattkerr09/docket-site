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

RUN = json.loads((Path(__file__).resolve().parents[2] / "data" / "ai-assistants-run.json").read_text())
ENGINE_MAC = "/Applications/Docket.app/Contents/Resources/docket/docket"
ENGINE_WIN = r"C:\Users\YOU\AppData\Local\Docket\docket\docket.exe"
CLAUDE_DESKTOP_HELP = ("https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-"
                       "on-claude-desktop")
CLAUDE_CODE_DOCS = "https://code.claude.com/docs/en/mcp"


def _day(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


def _bundle(platform: str) -> str:
    version = RELEASE.lstrip("v")
    return f"{REPO}/releases/download/{RELEASE}/Docket-{version}-{platform}.mcpb"


def ai_assistants() -> Path:
    when = _day(RUN["measured"])
    links = " · ".join(
        f'<a href="{download_url("ai-assistants-mcpb-" + key, to=_bundle(key))}" data-ev="Download" '
        f'data-ev-button="ai-assistants-mcpb-{key}">{label}</a>'
        for key, label in (("macos", "Mac"), ("windows-x64", "Windows"), ("linux-x86_64", "Linux")))
    body = f"""
<p class="lede">Docket SEO&rsquo;s audit engine runs as an MCP server on your own computer, so Claude or
ChatGPT can audit a site for you in conversation. Ask &ldquo;audit example.com&rdquo; and the crawl runs on
your machine. Without a key it is the free version: the score, how many problems each area has, and the
worst one in full with its fix.</p>

<h2>Claude Desktop: install the extension</h2>
<p>Download the extension for your computer: {links}. Then, in Claude Desktop, open Settings, choose
Extensions (under Desktop app in the newer layout), click Advanced settings and then Install Extension, and
pick the file. Leave the licence key setting empty for the free version, or paste the key from your Docket
receipt for every finding. These steps are from <a href="{CLAUDE_DESKTOP_HELP}" rel="nofollow noopener">Anthropic&rsquo;s
help page</a>, read {when}.</p>

<h2>Claude Code: one line</h2>
<p>With the Docket app installed, run this in a terminal:</p>
<pre><code>claude mcp add --transport stdio docket -- {ENGINE_MAC} mcp</code></pre>
<p>On Windows the engine is <code>{ENGINE_WIN}</code>, with your own account name for <code>YOU</code>. The
syntax is from <a href="{CLAUDE_CODE_DOCS}" rel="nofollow noopener">Claude Code&rsquo;s MCP documentation</a>,
read {when}: everything after <code>--</code> is the command that starts the server.</p>

<h2>ChatGPT: the desktop app</h2>
<p>The ChatGPT desktop app can start a local MCP server. Add one, choose STDIO, and give it the same engine
path with the argument <code>mcp</code>. ChatGPT on the web cannot, because it only reaches servers on the
internet and Docket runs on your computer. The <a href="/how-to/audit-your-site-from-an-ai-assistant/">full
setup guide</a> has OpenAI&rsquo;s wording and every tool&rsquo;s options.</p>

<h2>What the free version returns</h2>
<p>On {when} we took the released {RUN["release"]} Mac extension, started it the way Claude Desktop does
with the key setting empty and a fresh home folder, and asked it to audit {RUN["site"]}, this site. It
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
<li><strong>Your audits never reach us.</strong> They run on your computer and are never uploaded. What
an audit does contact, and how to turn the optional parts off, is on the
<a href="/legal/privacy/">privacy page</a>.</li>
</ul>
{buy_block("ai-assistants", try_app="ai-assistants-try-free")}

<h2>Related</h2>
<ul>
<li><a href="/how-to/audit-your-site-from-an-ai-assistant/">Every tool and option, in full</a></li>
<li><a href="/learn/claude-search-crawlers/">Which crawlers feed Claude&rsquo;s web search?</a></li>
<li><a href="/tools/seo-checker/">Free SEO checker, in your browser</a></li>
</ul>
"""
    return render(
        cat="ai-assistants", slug="",
        title="Use Docket SEO from Claude, Claude Code or ChatGPT",
        desc=("Install Docket SEO's audit engine in Claude Desktop, Claude Code or ChatGPT's desktop app. "
              "Ask it to audit a site; it runs on your computer. Free without a key."),
        h1="Use Docket SEO from your AI assistant",
        crumb='<a href="/">Docket</a> / AI assistants',
        body=body,
        published=RUN["measured"],
        schema_type="WebPage",
        faq=[
            ("Can Claude audit my website?",
             "Yes, with Docket SEO installed as an extension in Claude Desktop or added to Claude Code. Ask it to "
             "audit a site and the audit runs on your computer."),
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
