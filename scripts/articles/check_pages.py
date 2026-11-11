#!/usr/bin/env python3
"""Offline check reference, pinned to the engine revision requested by Article Studio.

The AST collector records predicates, numeric literals, constants and finding
branches without importing or running the engine. The reviewed wording below
explains those records; it is not an attempt to translate arbitrary Python.
Regenerate with --write; --check verifies both evidence and ownership decisions.
"""
from __future__ import annotations

import argparse
import ast
import csv
import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import warnings
from collections import defaultdict
from functools import lru_cache
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import facts as F
from render import render, with_next_step

ENGINE = Path("/Users/matthewkerr/Projects/docket-app")
REVISION = "0bb8e8d38a7c204064544e0ee7409fba4c25b85a"
OUTPUT = ROOT / "data/check-pages-2026-11-11.json"
CHECKS = "backend/seo_engine/checks/"
NUMBER = re.compile(r"(?<![\w])\d+(?:,\d{3})*(?:\.\d+)?(?![\w])")


class Visible(HTMLParser):
    """Article text, excluding shared chrome and the purchase block.

    Use the same extraction for drafts, saved pages and regression tests. The
    purchase block is rendered by the shared shell, not authored check copy.
    Method notes remain visible and count toward both words and similarity.
    """

    def __init__(self, *, include_chrome=False):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parts = []
        self.include_chrome = include_chrome

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get("class", "").split())
        hidden = (tag in {"head", "script", "style"} or not self.include_chrome and (
                  tag in {"nav", "header", "footer"}
                  or bool(classes & {"byline", "crumb", "skip-link", "buy-strip"})
                  or attrs.get("id") == "try"))
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input",
                       "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append((tag, hidden or bool(self.stack and self.stack[-1][1])))
        self.parts.append(" ")

    def handle_endtag(self, tag):
        for pos in range(len(self.stack) - 1, -1, -1):
            if self.stack[pos][0] == tag:
                del self.stack[pos:]
                break
        self.parts.append(" ")

    def handle_data(self, data):
        if not self.stack or not self.stack[-1][1]:
            self.parts.append(data)


def visible(raw: str, *, include_chrome=False) -> str:
    parser = Visible(include_chrome=include_chrome)
    parser.feed(raw)
    return " ".join("".join(parser.parts).split())


def shingles(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", text.casefold())
    return {" ".join(words[i:i + 5]) for i in range(max(0, len(words) - 4))}


def jaccard(a: set[str], b: set[str]) -> float:
    return len(a & b) / len(a | b) if a or b else 0.0


@lru_cache(maxsize=None)
def source_file(path: str) -> str:
    return subprocess.run(["git", "-C", str(ENGINE), "show", f"{REVISION}:{path}"],
                          check=True, capture_output=True, text=True).stdout


@lru_cache(maxsize=None)
def module(path: str):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        tree = ast.parse(source_file(path))
    definitions = {}
    imports = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            definitions[node.name] = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    definitions[target.id] = node
    candidates = defaultdict(set)
    # Some checks import optional helpers inside their function. Read those
    # declarations too, but withhold ambiguous aliases instead of guessing.
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("seo_engine"):
            imported_path = "backend/" + node.module.replace(".", "/") + ".py"
            for alias in node.names:
                candidates[alias.asname or alias.name].add((imported_path, alias.name))
    imports = {name: next(iter(values)) for name, values in candidates.items() if len(values) == 1}
    return tree, definitions, imports


def origin(path: str, function: str, node: ast.AST) -> dict:
    return {"file": path, "function": function, "line": node.lineno,
            "end_line": node.end_lineno}


def expression(node: ast.AST) -> str:
    return ast.unparse(node)


def numeric_value(node: ast.AST, path: str, seen=frozenset()):
    """Evaluate only certain numeric arithmetic; never execute engine code."""
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.Attribute):
        imported = imported_constant(node, path)
        if imported:
            other, name = imported
            return numeric_value(ast.Name(id=name), other, seen)
    if isinstance(node, ast.Name):
        key = (path, node.id)
        if key in seen:
            return None
        _, definitions, imports = module(path)
        found = definitions.get(node.id)
        if isinstance(found, (ast.Assign, ast.AnnAssign)):
            return numeric_value(found.value, path, seen | {key})
        if node.id in imports:
            other_path, name = imports[node.id]
            if other_path == "backend/seo_engine.py":
                return None  # Imported module; its attributes are resolved separately.
            return numeric_value(ast.Name(id=name), other_path, seen | {key})
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = numeric_value(node.operand, path, seen)
        return (-value if isinstance(node.op, ast.USub) else value) if value is not None else None
    if isinstance(node, ast.BinOp):
        a, b = numeric_value(node.left, path, seen), numeric_value(node.right, path, seen)
        if a is None or b is None:
            return None
        operations = {ast.Add: lambda: a + b, ast.Sub: lambda: a - b,
                      ast.Mult: lambda: a * b, ast.Div: lambda: a / b,
                      ast.FloorDiv: lambda: a // b, ast.Pow: lambda: a ** b,
                      ast.LShift: lambda: a << b}
        if type(node.op) in operations:
            return operations[type(node.op)]()
    return None


def imported_constant(node: ast.Attribute, path: str):
    if not isinstance(node.value, ast.Name) or not node.attr.isupper():
        return None
    imported = module(path)[2].get(node.value.id)
    if not imported:
        return None
    other, name = imported
    if other == "backend/seo_engine.py":
        other = f"backend/seo_engine/{name}.py"
    definitions = module(other)[1]
    if isinstance(definitions.get(node.attr), (ast.Assign, ast.AnnAssign)):
        return other, node.attr
    return None


def evidence(path: str, function: ast.FunctionDef) -> dict:
    """Follow local check helpers and imported constant definitions.

    Predicates retain their operators, so > and >= cannot silently become the
    same threshold. Numeric parameters include sample caps, slices and regex
    arguments as well as thresholds; they are deliberately not all labelled
    as decision thresholds. Nonliteral external results remain expressions.
    """
    pending = [(path, function.name)]
    visited = set()
    predicates, parameters, constants, findings, sources = [], [], [], [], []
    conditions, severity_rules, patterns, local_constants = [], [], [], []
    while pending:
        file, name = pending.pop(0)
        if (file, name) in visited:
            continue
        visited.add((file, name))
        _, definitions, imports = module(file)
        node = definitions[name]
        source = origin(file, name if isinstance(node, ast.FunctionDef) else "<module>", node)
        sources.append({**source, "sha256": hashlib.sha256(
            ast.get_source_segment(source_file(file), node).encode()).hexdigest()})
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = numeric_value(node.value, file)
            constants.append({"name": name, "expression": expression(node.value),
                              "value": value, "source": source})
        assignments = defaultdict(list)
        for child in node.body if isinstance(node, ast.FunctionDef) else []:
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        assignments[target.id].append(child)
        mutated = set()
        for child in ast.walk(node):
            if isinstance(child, ast.AugAssign) and isinstance(child.target, ast.Name):
                mutated.add(child.target.id)
            elif isinstance(child, (ast.For, ast.comprehension)):
                mutated.update(term.id for term in ast.walk(child.target) if isinstance(term, ast.Name))
            elif isinstance(child, ast.Assign) and child not in (node.body if isinstance(node, ast.FunctionDef) else []):
                for target in child.targets:
                    mutated.update(term.id for term in ast.walk(target) if isinstance(term, ast.Name))
        local_values = {}

        class ResolveLocal(ast.NodeTransformer):
            def visit_Name(self, term):
                return ast.copy_location(ast.Constant(local_values[term.id]), term) if term.id in local_values else term

        for _ in range(len(assignments)):
            changed = False
            for label, assigned in assignments.items():
                if len(assigned) != 1 or label in local_values or label in mutated:
                    continue
                resolved = ResolveLocal().visit(copy.deepcopy(assigned[0].value))
                value = numeric_value(resolved, file)
                if value is not None:
                    local_values[label] = value
                    local_constants.append({"name": label, "expression": expression(assigned[0].value),
                                            "value": value, "source": origin(file, source["function"], assigned[0])})
                    changed = True
            if not changed:
                break
        for child in ast.walk(node):
            where = origin(file, source["function"], child) if hasattr(child, "lineno") else source
            if isinstance(child, ast.Compare):
                resolved = {}
                for term in ast.walk(child):
                    if isinstance(term, (ast.Name, ast.Attribute)):
                        value = numeric_value(term, file)
                        if value is None and isinstance(term, ast.Name):
                            value = local_values.get(term.id)
                        if value is not None:
                            resolved[expression(term)] = value
                predicates.append({"expression": expression(child), "values": resolved, "source": where})
            if isinstance(child, ast.If):
                conditions.append({"expression": expression(child.test), "source": where})
            if isinstance(child, (ast.Assign, ast.AnnAssign)):
                targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                if any(isinstance(t, ast.Name) and t.id == "severity" for t in targets):
                    severity_rules.append({"expression": expression(child.value), "source": where})
            if isinstance(child, ast.Constant) and type(child.value) in (int, float):
                parameters.append({"value": child.value, "source": where})
            if (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                    and child.func.attr in {"compile", "search", "match", "fullmatch", "findall"}
                    and child.args and isinstance(child.args[0], ast.Constant)
                    and isinstance(child.args[0].value, str)):
                patterns.append({"expression": child.args[0].value, "source": where})
            if isinstance(child, ast.Call) and expression(child.func) == "Finding":
                fields = {k.arg: expression(k.value) for k in child.keywords
                          if k.arg in {"check_id", "severity", "title", "detail", "fix",
                                       "urls", "count", "requires_full_crawl", "evidence"}}
                findings.append({**fields, "source": where})
            if isinstance(child, ast.Name):
                if child.id in definitions:
                    pending.append((file, child.id))
                elif child.id in imports:
                    other, imported = imports[child.id]
                    # Check helpers and simple imported constants are evidence.
                    # General crawler, parser and network implementation is not
                    # executed or treated as a new check in this catalogue.
                    if other.startswith(CHECKS):
                        pending.append((other, imported))
                    elif other == "backend/seo_engine/words.py" and imported == "display_width":
                        pending.append((other, imported))
                    elif child.id.isupper():
                        _, external, _ = module(other)
                        if isinstance(external.get(imported), (ast.Assign, ast.AnnAssign)):
                            pending.append((other, imported))
            if isinstance(child, ast.Attribute):
                imported = imported_constant(child, file)
                if imported:
                    pending.append(imported)
    thresholds = [item for item in predicates if item["values"] or any(
        type(term.value) in (int, float) for term in ast.walk(ast.parse(item["expression"]))
        if isinstance(term, ast.Constant))]
    return {"sources": sources, "conditions": conditions, "predicates": predicates,
            "thresholds": thresholds, "numeric_parameters": parameters,
            "constants": constants, "local_constants": local_constants, "patterns": patterns,
            "severity_rules": severity_rules, "findings": findings}


# Reviewed explanations, keyed by the registry's public check IDs. Each block
# is question | short answer | measured conditions | pages read | report limits
# | why it matters | practical fix | existing supporting page.
COPY = {}


def copy_rows(text: str) -> None:
    for block in text.strip().split("\n\n"):
        lines = block.splitlines()
        key, *values = lines
        if len(values) != 8 or key in COPY:
            raise ValueError(f"Malformed or repeated copy: {key}")
        COPY[key] = dict(zip(("question", "answer", "condition", "pages", "reports",
                             "why", "fix", "guide"), values))


copy_rows("""
ai.citable_facts
Does your copy give AI answers facts to quote?
It looks for numbers backed by words that explain where the claim comes from.
The test needs at least 3 indexable pages with at least 250 words each and a supported prose language. A page qualifies as specific only when its prose matches both a number pattern and an attribution pattern. Currency amounts and percentages can supply the number. A bare number needs at least 2 digits, with comma-grouped forms also recognised. Research wording, a founding date, a qualification or a version can supply the context. A finding appears when the share of qualifying pages is below 0.3. For example, a 250-word service page can enter the sample when it is indexable and its language is supported.
Only substantial pages that can appear in search enter that share. A title alone cannot make a page qualify. Too few pages means this test produces no finding.
The report marks a low share of specific claims as medium severity. Pattern matches do not establish that a claim is true, that a source is reliable or that an AI answer will cite it.
A bare promise gives a reader little to check. The test looks for a concrete claim with enough context to understand its basis.
Read the affected pages and find claims you can support from your own records. Add the measurement, date or source beside the statement it explains. State any limits on what you know. Use numbers only when you can support them. Label estimates clearly.
/learn/ai-search-visibility/

ai.crawler_access
Can AI search crawlers read your site?
It separates crawler restrictions you chose from restrictions inherited from a general robots rule.
The check reads the saved AI crawler access decisions. An empty access table produces no finding. A robots response with HTTP status 500 or above, or a failed response with a requested robots address, prevents a confident access claim. It separates citation crawlers from training crawlers and distinguishes a named block, an allowlist omission and a wildcard block. The citation group includes OAI-SearchBot, PerplexityBot, Claude-SearchBot and Meta-WebIndexer. For example, a robots response with HTTP status 500 leaves access uncertain even if an earlier copy allowed the crawler.
This is a site policy check, based on the saved robots file and its access table. It does not need a set of crawled article pages.
Accidental citation blocks can be critical. Named choices, allowlist omissions and training restrictions are notices. The report explains which rule applies. Review it against the access you intended. A robots decision alone cannot prove that a server serves the request.
Search access and training permission are separate choices in this code. Keeping them distinct lets you review the rule that caused a finding without being told to remove a restriction you meant to keep.
Decide which crawlers should have access, then inspect the named group and the wildcard group that apply to each. Change only the rules that conflict with your policy. Use the linked guide to check the crawler names and retest the file after saving it. Review server access separately when robots allows a request that still fails.
/how-to/fix-ai-crawler-access/

ai.dead_crawler_directive
Do your AI crawler rules still name a real crawler?
It finds retired or unmatchable crawler names in the robots file.
The test needs a nonempty robots file. It compares crawler names with lists of retired names and names no crawler can match. Restrictions are compared with the wildcard group and any live replacement in the same or a separate group. An old name causes no lost restriction when its replacement already has the same restrictions or stricter ones.
The check reads the saved robots groups. It uses the policy text to identify crawler names.
A lost restriction is medium severity. Inert names whose restrictions are already covered, or which sit above no restriction, are notices. The report explains whether the old spelling changes the effective policy. It does not assume every retired name makes private pages readable.
A rule can look restrictive while naming a token no crawler sends. The useful distinction is whether your intended restriction still takes effect through another group, which is why the check compares coverage before choosing severity.
Find the exact token named in the report and identify its current replacement. Copy the restrictions you intend to keep to the live name, checking for an existing group first. Remove obsolete lines after you have checked the effective policy. Avoid blindly adding another group with a different set of rules.
/learn/ai-crawler-directives/

ai.edge_access
Does your server allow AI crawlers through?
It compares saved server responses with the crawler access your robots file allows.
The connector must have run and returned data. Its ordinary request must have HTTP status from 200 up to but below HTTP status 400 before crawler refusals can be compared. Payment responses with HTTP status 402 are separated from refusals. Challenges and verifying network edges can make a result untestable. Responses with HTTP status 429 or HTTP status 503 are separated as throttling. Other refusals conflict with policy only when the saved robots decision does not block that crawler. For example, a payment response with HTTP status 402 is handled separately from a crawler access refusal.
Saved connector input includes the baseline, search-control request and crawler requests. This is a test of the requested page from the audit's network location, not a complete server log.
Untestable, unverifiable and payment results are notices. Throttling is medium severity. A conflicting refusal is critical when a citation crawler is affected and high otherwise. Agreement can produce a pass. The report also records crawlers not asked before the connector's budget expired.
A robots permission does not override a server refusal. Comparing the policy with a real response helps locate the part of the request path that needs attention, while challenges leave room for a real verified crawler to behave differently.
Inspect the saved response and the matching firewall or bot rule. Check server logs before relaxing protection. If the server asked for a wait, respect that wait and test again. For a verified-crawler challenge, review the network verification rule rather than assuming that changing the user-agent text proves real crawler access.
/how-to/fix-ai-crawlers-blocked-by-your-cdn/

ai.entity
Does your markup identify your business?
It looks for business identity markup and recognised profile links in sameAs.
The check reads owned identity nodes in JSON-LD from the first 60 indexable pages. It collects sameAs as either a string or a list. If no identity is found there, it checks the wider indexable set for served identity types, other markup and script-built types before reporting absence. With an identity present, an empty sameAs set is reported separately from fewer than 3 recognised profile hosts. For example, an identity with fewer than 3 recognised profile hosts can need review even when sameAs is present.
Identity declarations belong to the business described by the page. The check walks owned nodes rather than treating every organisation mentioned in an article as the site's business.
Missing business identity can be high severity, absent profile links medium and weak recognised coverage low. A recognised host is a pattern match, not proof that the account belongs to you. Existing identity elsewhere can suppress a claim that the site has none.
The distinction between your business and an organisation you discuss matters here. A profile link is useful as an identity statement only when it names the same business, so adding unrelated recognised hosts would make the markup less accurate.
Review the business node in the served HTML. Give it the correct identity type and link only to profiles your business owns. Keep those links consistent with the accounts shown to visitors. Follow the guide before copying profile URLs, because a platform homepage or another company's account does not identify your business.
/how-to/fix-sameas-that-claims-the-wrong-accounts/

ai.extractability
Do your pages answer clear questions?
It counts substantial pages with question headings that are specific to the page.
The test runs only for a supported prose language. It needs at least 3 indexable pages with at least 300 words each. Headings repeated on every substantial page are removed from consideration. Remaining subheadings qualify when they end in a question mark or match the question-word pattern within its 60-character window. A finding appears when the qualifying page share is below 0.25. For example, a 300-word article with a question subheading can qualify if that heading passes the wording test.
Heading tests read subheadings from substantial indexable pages. A shared question in the page template does not count as a distinct answer structure on each page.
Low question-heading coverage is medium severity. The test identifies a structure that can be read from headings. It does not grade the answer, confirm its accuracy or promise that an AI service will use it.
A heading can tell a visitor which question the next passage answers. Repeated template questions do not describe the subject of each article, which explains why the code removes headings that occur across the whole sample.
Find real questions your page already answers. Write a short heading that names the question, then put the direct answer below it before adding detail. Leave headings as statements where that is clearer. Review the body as well as the heading so that punctuation does not become a substitute for a useful answer.
/learn/answer-extractability/

ai.freshness_signal
Can a tool read your page dates?
It checks whether substantial pages carry a date in machine-readable markup.
At least 4 indexable pages with at least 300 words each are needed. A page counts as dated when it has an article published or modified time in Open Graph, or a matching date in content JSON-LD. The JSON-LD date check excludes site-level types, accepts an ISO-shaped date prefix and stops walking beyond 8 nested levels. A finding appears when the dated share is below 0.3. For example, a 300-word article with a qualifying published date can count toward the dated share.
The sample is substantial indexable content. A date on a shared organisation or website node does not stand in for the date of the page being read.
The result is low severity. An Open Graph date counts when present. A JSON-LD date also needs the expected format. Review the date yourself to confirm when the content changed and whether it is current.
A date helps readers understand when an article was written or updated. Attach it to the content it describes. Change an update date when the work has actually changed.
Use the real publication date and change the modified date only after a meaningful edit. Add the matching article time or content schema field, then inspect the served HTML. Keep a visible date consistent with the markup. Do not update the date merely to remove the finding when the underlying page has not changed.
/how-to/content-audit/

ai.llms_txt
Does your site have an llms.txt file?
It reports whether the saved site probe found an llms.txt file it could read.
A nonempty saved file ends the check without a finding. The test also stops when the file was skipped under robots rules. A refused response is reported as unreadable rather than absent. Only the remaining missing-file case produces the notice about no llms.txt. It does not test the document's headings, links or usefulness as a content summary.
This check uses the site-level file probe. It does not search article bodies for the filename or require the crawler to discover the file through an internal link.
This is a notice about an optional file. A refusal leaves the file's presence unknown. Review that response before deciding whether to create or change the file.
The saved probe can answer a narrow file-presence question. It cannot establish that an AI service reads the file or that publishing one changes how the service answers questions about your site.
If you want to publish the file, write a short account of the site with working links to its main content. Check that the root address serves the text and that your policy allows the intended request. When the finding says unreadable, investigate the refusal first instead of creating a second copy of a file that may already exist.
/learn/what-is-llms-txt/

ai.rendering
Can AI crawlers read your initial HTML?
It finds indexable pages marked as dependent on JavaScript for their content.
The check reads which pages the crawler marked as needing JavaScript for their main content. It leaves out addresses recognised as intentionally excluded from search. If no pages remain, there is no finding. It uses the crawler's earlier observations. There is no separate word-count or timing limit here.
The check reads initial page content and whether the crawler marked it as needing JavaScript. It uses pages intended for search. Running an AI crawler or confirming a particular service's script support needs a separate test.
A finding is high severity and lists the affected URLs. Pages can match even when they work after scripts run. Review the document sent before those scripts run.
Browsers can show useful content that a plain document request does not contain. Comparing those views helps explain why a visitor's screenshot and the audit can disagree without either view being fabricated.
Open an affected URL and compare the page source with the content visible after loading. Put the main content in the HTML served by the server, using server rendering or a static output where suitable. Retest the actual URL after the change. Keep interactive features, but make the article or product details readable before those features run.
/how-to/javascript-seo-audit/

ai.unmeasurable_optout
Can an audit see every AI visibility control?
It explains an AI visibility control that cannot be checked from outside the site.
This is an explanatory notice rather than a page-content test. It reads the saved access table and suppresses the notice when that nonempty table blocks every citation-critical crawler. Otherwise the notice explains that an outside audit cannot observe the relevant provider-side control. There is no numeric score, content ratio or page-length cutoff in this test.
The site access table determines whether the explanation is relevant. Crawled article text cannot reveal the provider-side setting, so a larger sample does not make that setting observable.
This result is an explanatory notice. You need account access to check the private setting. A suppressed notice also leaves that setting unmeasured.
An outside audit can only report what it can observe. A provider's private control needs review inside that account. Record the access policy there and use public requests to check the behaviour they can show.
Review the relevant provider account and its own settings with the person who manages them. Record the policy you intend and check it against the public crawler rules separately. Use public access tests for public access questions. Avoid treating a clean crawl as proof of a private account setting that the crawler cannot read.
/learn/ai-search-visibility/
""")

copy_rows("""
brand.logo
Does your logo name your business?
It checks how often a readable business identity appears and whether logo text names it.
At least 3 successful pages are needed. A page counts as identified when it has a logo or a homepage link whose text contains recognised brand words. Coverage below 0.5 can produce an absence finding when the crawl supports absence claims. Logos with empty or weak alternative text are checked separately. A text link naming the business can count even without an image logo. For example, a site with 3 successful pages has enough pages to begin this comparison.
The check reads logos and homepage links from pages the crawl could load. It checks whether they name the business. You still need to review their appearance.
Both low identity coverage and weak logo text are low severity. The report does not compare logo artwork, assess a designer's work or require an image when a suitable text identity already exists.
Logo text is also the name of a link for someone who cannot see the image. The check keeps that naming job separate from the choice to use a graphic in the first place.
Check the header on the affected templates. Give a linked logo useful alternative text that names the business, or keep a clear text link to the homepage. Review the rendered link name before repeating the change across templates. Do not add an image merely because your current identity uses text.
/how-to/what-your-site-says-you-are-called/

brand.name_consistency
Does your site use a consistent business name?
It compares declared business names while allowing common forms of the same name.
The check needs at least 3 successful pages and samples the first 40 pages for title, social and logo signals, alongside business schema. Candidate names longer than 60 characters are discarded. Weak variants normally need at least the larger of 2 occurrences or a 0.08 share of the total, while authoritative declarations are retained. Normalisation, writing-system grouping, containment and initialism handling remove apparent differences before distinct names are reported. For example, a name longer than 60 characters is left out of the candidate list.
The check uses fields that name the business, such as titles and business markup. Ordinary mentions of other companies in body text are left out. The spelling still needs your review.
Remaining distinct names produce a medium-severity finding. A report is a prompt to review the declarations, not an instruction to erase a valid legal name, translated name or trading name without checking its context.
Title suffixes and business schema nodes can claim to name the same owner. Reviewing those declarations together helps reveal a template still carrying an earlier name, while the normalisation guards reduce ordinary spelling noise.
Read each cited spelling in its original location. Choose the name that belongs in that field and update stale title suffixes, logo text or business markup. Preserve legal and language distinctions that serve a real purpose. After changing a shared template, check the homepage and an inner page for agreement.
/how-to/what-your-site-says-you-are-called/

brand.positioning
Do your page summaries share a clear message?
It checks for shared subject words across page descriptions.
The test needs at least 6 indexable pages with nonempty meta descriptions and a supported prose language. It counts meaningful words by page, removing common words and brand terms. Shared words need the larger of 3 appearances or the integer part of a 0.3 share of the sample. At least 2 shared terms suppress the finding. A nonbrand term on at least half the pages also suppresses it. For example, finding 2 qualifying shared terms is enough to suppress this finding.
Only descriptions with text enter this comparison. It does not read a positioning document or judge whether every page should use the same sentence.
Lack of a shared message produces a medium-severity finding. Shared vocabulary is a clue. Different words can express the same offer, so review the descriptions before deciding that the business message is inconsistent.
Meta descriptions summarise individual pages. Shared terms can show a common subject. Give each description enough detail to explain its own page.
Compare the affected descriptions with the offer your business actually makes. Keep each summary specific to its page while using clear words for the service or product where they belong. Resolve contradictory claims first. Do not force a repeated keyword into a page whose subject genuinely differs from the rest.
/how-to/fix-a-site-that-says-something-different-every-page/

brand.visual_consistency
Does your site mix too many visual styles?
It counts typefaces and groups nearly identical colours from readable styles.
The sample needs at least 3 readable pages with font or colour data. Pages left unread because of a stylesheet cap are removed. Too few remaining pages stops the comparison. More than 4 font families produces a low-severity finding. Groups of very similar colours also produce a low finding. Each colour must be within 10.0 RGB distance units and 0.01 opacity units of every other colour in its group. RGB distance is the straight-line distance between the colour channel values. Opacity is measured as a fraction of full opacity. For example, exactly 4 font families stay within the font-count limit.
The check counts styles it could read on pages and stylesheets from the same site. When a large enough site has no readable style data, it reports that limit. It leaves the palette unknown.
Typeface counts and colour groups are clues for a design review. It does not render screenshots, measure contrast or establish that every close colour pair is accidental. A purposeful colour or font difference can be valid.
Small differences in style values can be hard to spot by eye while still leaving separate declarations to maintain. The report gives you concrete values to inspect instead of claiming that a count alone proves poor design.
Compare the listed families and colour groups with your intended styles. Remove unused families and consolidate values that were meant to be identical. Keep deliberate differences such as opacity states. Inspect a representative page after editing the shared stylesheet so that a numerical cleanup does not remove a useful visual distinction.
/learn/brand-consistency/

brand.voice_consistency
Do your pages sound like the same business?
It compares average sentence lengths across substantial pages.
At least 5 indexable pages with at least 250 words and measured rather than estimated word counts are required, together with a supported prose language. Each page needs at least 5 usable sentences. Saved sentence lengths are preferred. The fallback splits up to 20000 characters of prose and keeps sentences with at least 3 words. A population standard deviation below 7.0 words per sentence stops the check. Larger spreads reach the finding. For example, a 250-word article still needs at least 5 usable sentences to enter the comparison.
The sample is substantial prose, not short product labels or every successful response. Pages lacking enough usable sentences do not supply an average.
The finding is low severity and identifies the shortest and longest sentence-length averages. It does not measure tone, verify authorship or decide whether a technical page should read like a contact page.
Sentence length is a narrow, visible part of writing style. A large spread can help you choose pages to review, while the purpose and audience of those pages still decide whether the difference is a problem.
Read passages from the pages at either end of the comparison. Break dense sentences where a reader would benefit and remove abrupt fragments that obscure meaning. Keep necessary terms and intentional differences between page types. Use the guide to review the whole passage instead of chasing an identical average on every page.
/how-to/fix-a-site-that-sounds-like-several-companies/

brand.social_consistency
Do your social links agree with your markup?
It compares profile platforms linked on the site with those declared in sameAs.
The check needs a homepage and at least 3 successful pages. It samples up to 30 pages. A profile is relevant when linked on the homepage or on at least the larger of 2 pages or the rounded-up third of that sample. Content and sharing URLs are excluded. Profile platforms are compared with served sameAs links and script-built declarations. The comparison is by platform rather than exact account URL. For example, a footer profile repeated across the qualifying sample can enter the comparison without a homepage link.
The check reads homepage profile links, profiles linked across multiple pages and business markup. You still need to confirm that each account belongs to the business.
Missing platforms are low severity when some declarations exist and medium when none do. Script-only declarations can produce a separate notice. The platform comparison does not prove that a linked account and a declared account are the same account.
Visible links and business markup should describe the identity you intend to publish. A platform-level check can find a gap, but the owner still needs to confirm each account before adding it to a business declaration.
Compare the profile links in your header or footer with the business node. Add the correct owned profiles where missing and remove stale accounts. Inspect script-built declarations in the served document before changing them. Verify the exact account URL yourself, because a matching platform name alone cannot settle ownership.
/how-to/fix-sameas-that-claims-the-wrong-accounts/

content.ai_slop
Does your copy repeat stock AI phrases?
It flags pages containing multiple phrases from the engine's stock-copy list.
The check runs for a supported prose language and reads indexable prose. Taxonomy archive URLs are excluded. A page matches when at least 2 distinct entries from the stored phrase list occur in its prose. Repeating the same entry does not create another distinct phrase. The list is a literal set of writing tells, not a model that determines how the text was produced. For example, repeating the same stock phrase still leaves only a single distinct match toward the required 2 phrase matches.
Each page supplies its own prose as input. It does not inspect an author's writing history or use a probability score from an AI detector.
Matching pages produce a medium-severity finding with the phrases that matched. Their presence does not establish that a machine wrote the page. Review quoted examples and context before rewriting a passage that may be discussing those phrases.
Stock wording can say little about the business behind a page. The useful editorial question is whether the affected passage gives the reader information, rather than whether it can be assigned to a particular authoring tool.
Read the marked passage aloud and replace empty claims with an account of what you actually do. Keep real examples, limits and sources close to the statements they support. If the phrase is an example under discussion, review that context before changing it. A phrase list should guide an edit, not decide authorship.
/learn/ai-sounding-copy/

content.competing_pages
Are different pages making the same promise?
It finds groups of distinct pages whose title subjects overlap after several exclusions.
The test excludes the homepage, empty titles and pages with an unambiguous canonical pointing elsewhere. At least 2 usable pages and at least 2 meaningful target words per title are required. Candidate pairs need at least 2 shared meaningful words and an overlap of at least 0.5, calculated as shared title words divided by all distinct title words in the pair. Guards separate products, listings, events, named places, distinct measurements, series entries, section indexes and other distinct subjects before groups are formed. For example, titles sharing fewer than 2 meaningful words cannot form a candidate pair.
This comparison uses titles and page context from indexable pages. It is not the body-text duplicate check and does not read search query or ranking data.
Groups with different titles produce a medium-severity finding. Identical titles are left to the duplicate-title check. The exclusions are substantial, so a pair sharing ordinary words can still be correctly left out when the pages serve distinct purposes.
Title overlap can point to pages that promise the same answer. It cannot prove that the pages compete in search, and merging useful pages without reading them could remove a distinction that a short title failed to express.
Read the grouped pages side by side. Make distinct purposes clear in their titles and content. Merge only pages that truly duplicate the same job, then update links and redirects where appropriate. Preserve location, product and series differences when they are useful to visitors, even if some words overlap.
/how-to/fix-pages-competing-for-one-search/

content.dates
Do your articles publish readable dates?
It looks for article pages missing a published or modified date in markup.
The sample uses article markup and article-like addresses. A section index with at least 3 child links is left out of address-based selection. At least 3 articles are needed. A finding appears when more than a 0.5 share lacks a machine-readable date. Open Graph article dates and date fields on article objects qualify. A visible date near the start changes severity but leaves the missing markup to fix. For example, a blog section with at least 3 child links can be left out as an index.
Indexable article pages supply the comparison. A service page is not automatically an article merely because it contains prose, and a section listing is handled differently from an entry.
The finding is low severity if every affected article already shows a visible date, and medium otherwise. It does not compare the date with the age of the facts or verify that a modified date reflects a real edit.
A date printed for a person and a date attached to an article node serve related readers. The distinction in the report lets you add missing markup without claiming that an already visible date never existed.
Use the true publication and modification dates. Add them to the article markup and show the date clearly near the content when it is useful to readers. Check that the visible date agrees with the structured value. Leave the modification date alone when a rebuild did not change the article itself.
/how-to/content-audit/

content.eeat
Does your site show who stands behind it?
It checks for trust pages, a route to contact you and article authorship signals.
The test looks for about and contact pages, an enquiry form with at least 2 fields, and a recognised privacy policy. Missing contact details raise the trust-page finding from low to medium severity. Author names can come from markup or bylines in up to 2000 characters from each of the first 40 successful pages. At least 3 indexable pages with article markup are needed for the missing-author finding. For example, an enquiry form with 2 fields can satisfy the contact-route test.
The check reads page addresses, forms, business text and article markup. It looks for who publishes the content and how a visitor can contact them. You need to verify the named people and their roles.
Missing authorship is low severity. Trust-page findings name the contact, policy or authorship information the check could not find. An enquiry route can satisfy the contact check without a page named Contact. Review who publishes the content and how visitors can reach them.
Readers need a way to understand who publishes a page and how to reach them. These observable signals can help with that task, but the code's presence checks do not turn a byline into proof of expertise.
Publish accurate information about the business and give visitors a working contact route. Attach the real author or responsible organisation to articles. Keep the privacy page linked where people can find it. Check forms and schema before adding duplicate pages merely to satisfy a path-based cue.
/learn/trust-and-authorship-signals/

content.js_rendering
Does your content depend on JavaScript?
It reports indexable pages whose initial HTML lacks their main content.
The check reads the crawler's JavaScript-dependent flag and leaves out URLs recognised as intentionally excluded from search. Any remaining affected pages can produce a finding. Severity is high when their share of indexable pages is greater than 0.5, and medium otherwise. The ratio uses the indexable page set, so it does not treat failed responses as readable content. For example, an affected share of exactly 0.5 stays in the medium-severity group.
The check uses the crawler's record of pages that need JavaScript. It covers pages intended for search. Script execution time and interactive controls need separate tests.
The finding lists affected URLs and their share. A loaded browser view may show text absent from the original response. Inspect both views when reviewing the result.
Content can be present after loading and absent from the first response. That distinction explains the check without assuming that every reader executes the same scripts or that a missing initial body means the page has no useful content at all.
Compare source HTML with the loaded page. Serve the main text, links and essential details from the server or a static build where practical. Test the affected templates after changing their rendering path. Keep scripts for interaction while making the information they enhance available in the first response.
/how-to/javascript-seo-audit/

content.lang_mismatch
Does your page declare the language it uses?
It compares a page's declared language with conservative language clues in the text.
The page needs a language declaration and at least 40 words for language detection. Listing-like text with an anchor share of at least 0.7 is excluded. Name-heavy text is excluded when at least 40 usable words have a capitalised share of at least 0.55. A title favouring the declared language can suppress a mismatch. Bilingual text is accepted when its declared-language share reaches at least 0.4 of the competing language's share. For example, a page with fewer than 40 words cannot enter the language-detection comparison.
The check reads page text, titles, language attributes and link labels on pages intended for search. Pages with too little usable text are left out. It leaves their language unknown.
Remaining mismatches produce a medium-severity finding. The detector and its language coverage impose limits, so the result needs a human reading of the affected page before a declaration is changed.
Your language attribute states how the page should be read. Names, link lists and bilingual passages can confuse a simple text comparison, which is why the code includes guards for each of those patterns.
Read the affected page and confirm the main language. Correct the document language when it is wrong, keeping regional details when they are valid. Review mixed-language sections separately from the page declaration. Use the guide to distinguish a language attribute from alternate-language links, since changing one does not repair the other.
/how-to/fix-lang-attribute-mismatch/

content.language_scope
Can this audit judge your site's prose language?
It states when language-dependent copy checks were skipped.
The check asks whether the site's prose language is supported. A supported language ends the test without a finding. Otherwise it names the detected language and explains the limit. It assigns no content-quality score or sentence-length cutoff.
This is an audit-scope notice based on the saved language decision. It describes which copy checks can run, rather than inspecting every sentence for a writing fault.
The notice names the language limit. Copy checks that need to understand that language are withheld. Checks of status codes, markup and links may still run. Review the text with a fluent reader.
Clear limits matter when a report contains a mixture of measured results and withheld judgements. Naming the language limit helps you see where the tool's answer ends and a reader who knows the language must take over.
Have a fluent reader review the copy using the same questions the skipped checks would ask. Check whether the page says what it does, answers its subject and gives a clear next step. Correct a mistaken language declaration when needed, but keep the site's real language instead of translating it solely to remove this notice.
/how-to/fix-lang-attribute-mismatch/

content.placeholder
Did unfinished text reach your public pages?
It searches for known filler text while excluding many cases where a page discusses it.
The test reads indexable prose and snippet fields. It uses a literal marker list, with separate guards for comments, hidden text, quoted discussion, examples and redaction masks. Context checks use a 160-character window. Short holding-page wording, longer discussions and Latin filler have different guards. The snippet announcement case uses a 12-word limit, while the holding-page test uses 200 words. These are context rules, not a general quality score. For example, short announcement wording in a snippet is assessed with the 12-word limit.
Main prose, selected headings, descriptions and social or schema snippet text can supply a match. A marker confined to a hidden or comment area is not automatically treated as the page's own unfinished copy.
Confirmed matches produce a high-severity finding. The report still needs context review, especially on documentation that quotes a marker deliberately. A pattern match does not establish that every sentence containing the words is unfinished.
An unfinished template field can appear outside the main body, including in the text used to describe a page. That is why the check looks beyond visible paragraphs while trying to preserve useful discussions of placeholder examples.
Open the cited field and replace actual filler with finished text, or remove the unfinished page from public use until it is ready. Inspect metadata as well as the body. If the text is a quoted example, check its context before editing. Fix the template that supplied it when the same field appears across pages.
/how-to/placeholder-text-findings/

content.readability
Are your sentences hard to follow?
It finds substantial pages whose usable sentences are long on average.
The test needs a supported prose language and a page intended for search with at least 200 words. It uses recorded sentence lengths when available. Otherwise it splits the prose into sentences and keeps those longer than 2 words. At least 5 usable sentences are needed. An average greater than 25 words produces a finding. Exactly 25 words per sentence stays within the limit. For example, an average of exactly 25 words per sentence stays within the limit.
Only pages with enough prose and usable sentences enter the calculation. It does not assign a school reading age or analyse the meaning of technical terms.
The finding is low severity and reports the pages with dense sentence structure. An average can hide both short and long sentences, so use it to choose passages for review rather than treating every sentence on a reported page as a fault.
Long sentences can ask a reader to hold several ideas at once. The code measures their length as a review cue, while a human still decides which ideas belong together and which terms the intended reader needs.
Read the affected paragraphs and put the main point early. Split a sentence when it joins separate ideas, and replace vague phrases with concrete words. Keep a longer sentence when its structure is clear. Review the edited passage for meaning before checking whether the average changed.
/how-to/content-audit/

content.thin
Does a page have too little useful text?
It separates short content, sparse archives and intentionally indexable utility pages.
The main cutoffs are fewer than 60 words for very thin content and fewer than 150 words for thin content. JavaScript-dependent pages and useful hubs are treated separately. A hub needs at least 3 child targets. Archive detection uses taxonomy paths or a prose anchor share of at least 0.6 with qualifying anchor phrases of at least 4 words. Utility URLs and archive-like pages are reported differently from ordinary content. For example, a page with exactly 60 words is outside the very-thin group but remains below 150 words.
Indexable page prose supplies word counts. The check includes caveats for pages whose browser-built content may be fuller than the served HTML, so the reported count needs to be read with its source view in mind.
Ordinary very thin content is high severity. Thin content is medium. Utility and sparse archive findings are low. Use these cutoffs to choose pages for review. Judge whether each page answers its visitor's question before adding text.
Short text can mean a missing answer, a useful index or content assembled after loading. Distinguishing those cases matters before adding paragraphs, because extra words cannot repair a rendering fault or make an empty archive useful by themselves.
Decide what the page should help a visitor do. Supply missing information on genuine content pages, improve archive listings where useful and keep utility pages out of search when that is their intended role. Check the browser view before rewriting a page whose text is absent only from the initial HTML.
/how-to/fix-thin-content-pages/

content.topic_gaps
Do search suggestions point to missing topics?
It compares saved demand queries with words already used in page titles and headings.
The demand-topics connector must have run. From up to 30 top queries, it filters inferred subjects when present and collects covered words from up to 120 indexable pages. A query is a gap when its meaningful words are not all in the covered set. At most 12 gaps are shown. If topics were unavailable, the code emits a notice explaining the missing input instead of inventing suggestions. For example, a report stops at 12 suggestions even when more queries qualify as gaps.
Saved query suggestions and the site's titles and headings supply the comparison. The union of words across pages is used, so it is not a full review of whether a particular page answers a query.
Topic gaps are low severity. Unavailable suggestions are notices. It does not supply search volume, prove demand size or confirm that the business should publish on every suggested topic.
Suggestions can expose subjects worth reviewing, but a vocabulary gap is only a starting point. Reading the existing content and checking whether the subject belongs to your business prevents a list of suggestions from becoming an automatic publishing plan.
Read the suggested query and find any existing page that answers it. Improve that page when it already serves the need. Add new content when the subject fits the business and needs an answer. Use only demand estimates you can support. Explain where the suggestions came from.
/how-to/content-audit/
""")

copy_rows("""
cvr.dead_contact
Can your published email addresses receive mail?
It reports published email domains that the saved mail test says cannot accept mail.
The mail-delivery measurement must be available. Domains from mail links on successful pages are joined to saved domain results. Only a result with accepts-mail explicitly false and a published address can produce a finding. A conclusive result on a static host raises severity. Domain validity, IP-like forms and the relationship to the site's own host inform the explanation and suggested fix.
The check uses published email links and the recorded domain-level mail test. A result applies to the domain. Checking whether a specific mailbox accepts messages needs a separate test.
Severity is high for the conclusive static-host case and medium otherwise. This is a domain delivery test, not a promise that a particular inbox exists or that a person will answer a message.
A visible email link is a route a visitor may use to contact you. Without mail delivery, a domain breaks the contact route even if the link itself is correctly written and the website still loads.
Confirm the intended address with the person who receives enquiries. Correct spelling errors in the link and its visible text. For an address you own, review the domain's mail setup with its provider and retest delivery. Do not replace a valid address merely because an inconclusive network result needs investigation.
/learn/dead-contact-address/

cvr.form_friction
Can visitors send you an enquiry?
It finds long forms and checks whether key pages offer a contact route.
An enquiry form with 6 or more counted fields is flagged as long. The check also reviews key pages for forms, direct contact links, recognised booking or messaging services and useful contact-page links. If every target lacks a route, it can report no way to make contact. That absence claim needs a supported prose language. Field counting can still run in other languages.
Form scanning reads indexable pages. Contact-route review uses the homepage and pages recognised as selling, falling back to up to 5 shallow indexable pages when no such targets are found.
Long forms are medium severity. No contact route across the target set is high. The check recognises several routes besides an embedded form and does not judge whether every field is necessary for your actual service.
A visitor may need to call, write or book rather than complete a form. Keeping those routes in the check prevents a site with a working off-site booking service from being treated as unable to take enquiries.
Walk through the real enquiry route from a key page. Remove fields you do not need before the first reply and make the action clear. Keep necessary fields for the service you provide. If the route uses another service, verify the destination and link wording before adding a duplicate form solely to change the report.
/how-to/cta-findings-that-miss-the-form/

cvr.funnel
Does your site help people before they buy?
It looks for page paths that suggest educational and comparison content.
At least 6 indexable pages are needed. Educational paths include blog, guide, resources, learn, FAQ and related sections. Comparison paths include compare, alternatives, reviews, case studies, testimonials and work examples. Missing both groups produces medium severity. A single missing group produces low severity. This is a path-based presence test, not a reading of the persuasive quality of every page. For example, a site with 6 indexable pages can enter the section-presence check.
The check searches the site's page inventory for recognised path shapes. A useful page under an unusual address may not match those shapes even when its content helps visitors make a decision.
The finding names the missing content groups. It does not establish that a business needs a large publishing programme or that adding a section will create demand for its services.
Someone learning about a problem may need a different answer from someone comparing providers. Those are distinct page jobs, and the check provides a small inventory check for whether the site appears to serve either stage.
Review the questions customers ask before an enquiry and while comparing options. Link existing useful answers clearly, including work examples where relevant. Add a page only when it can answer a real question that the current site leaves open. Keep the address and title descriptive without renaming good pages merely to match a path list.
/learn/conversion-audit/

cvr.message_match
Does your headline match your page title?
It compares meaningful words in the title with a page-specific main heading.
The check runs for a supported prose language and requires both a title and a nonempty main heading. Common page-kind words, simple plurals and recognised equivalent contact phrases are normalised. On a sample of at least 5 successful pages, headings present on at least a 0.6 share are treated as shared furniture. The first remaining heading is preferred. A meaningful-word overlap below 0.2 produces a finding, except for a title made only of brand words. For example, a meaningful-word overlap of exactly 0.2 does not fall below the mismatch limit.
Indexable titles and main headings supply the comparison. Shared headings are identified from successful pages so that a repeated business heading does not automatically replace the page's actual subject.
The finding is low severity. Word overlap is a narrow clue and can miss synonyms, so review the title and headline as promises to a reader before changing either field.
A page title and the headline a visitor reaches should make sense together. The code checks a visible part of that relationship without claiming to know the full intent of a search or the visitor's next action.
Read the title as it would appear in a search result, then read the first specific headline. Make both describe the same page job. Preserve useful differences in wording and avoid copying the title mechanically when a clearer headline works. Check a shared template if the wrong heading appears across several unrelated pages.
/learn/conversion-audit/

cvr.no_cta
Do your key pages ask for a clear next step?
It checks for an action or useful enquiry form on the pages most likely to sell.
The test needs a supported prose language. A recognised call to action or a form with at least 2 fields counts as a next step. Pages without either are reported separately. When actions exist, it checks whether all their labels are generic, such as Submit or Continue. Ordinary links are kept out of that label test. For example, a form with 2 fields can count as a next step without a separate action button.
Targets are the homepage and recognised selling pages intended for search. When none match, the check uses up to 5 shallow indexable pages. It reads recorded action labels and forms. Completing a purchase or submitting an enquiry needs a separate test.
Missing actions are high severity and weak labels medium. It does not test whether the destination completes a sale, whether an off-site service works or whether a particular button colour attracts attention.
An action label tells a visitor what they can do next. A form or link can already serve that job, which is why the presence test allows more than a single style of sales button.
Choose the next useful action for each key page. Name it in words that explain the result, and link it to the correct form, booking page or product step. Test that route yourself. Keep labels consistent with what happens after clicking, rather than adding a vague action just to satisfy the presence test.
/how-to/cta-findings-that-miss-the-form/

cvr.pricing
Does your site explain cost or how to get a quote?
It looks for a pricing route or recognisable cost language.
The check runs only for a supported prose language. It first looks for pricing, plans, prices, rates, cost, quote or estimate paths. Across the sample, it also reads up to 6000 characters from each of the first 30 indexable pages for currency, price, trial, quote and estimate signals. A finding appears only when neither a matching page route nor a price-language signal was found. For example, a quote invitation in the first 6000 text characters of a sampled page can satisfy the wording test.
The check uses the page list and sampled text. A quote invitation can qualify. You still need to review whether the visitor can understand the cost or the steps to get a quote.
The absence finding is medium severity. A detected currency symbol or quote word can satisfy the check, so a clean result does not establish that visitors receive a complete or clear account of cost.
Cost can be explained as a price, a range or a route to an estimate. The check includes quote language because a business can be transparent about the next step without publishing a fixed amount for work that varies.
Read the main buying pages as a new visitor. Explain the real cost where it is known, or say how to request a quote and what information is needed. Keep any stated amount current. Link the cost explanation from the relevant page and check that the visible wording gives more help than an isolated currency sign.
/learn/conversion-audit/

cvr.social_proof
Do your selling pages show reasons to trust you?
It looks for recognised proof language on key conversion pages.
The test requires a supported prose language and a nonempty target set. Each target is searched across up to 8000 characters of text plus its subheadings for the stored proof phrases. A finding appears only when every target lacks a match. The phrase set includes review, testimonial, certification, guarantee and work-example language. It does not verify the underlying claim or count satisfied customers. For example, a work example beyond the first 8000 text characters needs a qualifying subheading to be found by this search.
Targets are the indexable homepage and selling pages, or up to 5 shallow indexable pages when the site has no recognised selling targets.
The finding is medium severity. You need to review each phrase in context and check its basis. The phrase list may also miss genuine examples written in other words.
A visitor may want to see work examples or real customer experiences before making contact. Check the truth and relevance of any claim you publish. The phrase test can only locate wording for you to review.
Publish only reviews, qualifications, guarantees and work examples you can support. Put them near the offer they describe. Keep the source clear and get any permission needed. Review each claim again when the service changes.
/learn/conversion-audit/

cvr.unusable_phone
Will your phone links dial the right number?
It checks phone-link destinations for forms that are placeholders or not defined by the link standard.
The check decodes phone-link destinations and separates pasted markup, placeholder runs, written extensions, other letters and missing international context. Repeated identical digits are placeholders when there are at least 7 digits. A local-format number without a leading plus or phone-context parameter is reported separately. At least 2 recognised hreflang regions raise that last case from low to medium severity. Extension and placeholder patterns have their own exact formats in the source. For example, a phone target made of at least 7 identical digits can be flagged as a placeholder.
The check reads phone links on pages the crawl could load. It validates their written format. You need to test the intended contact route yourself.
Pasted markup, letters and placeholders can be high severity. Written extensions are medium. Missing international context is low, or medium when language-region declarations suggest a wider audience. The check validates the written link format. Test the intended line separately.
A visible phone label can look correct while its hidden destination contains different text. Checking that destination matters because tapping a link uses the destination, not the words displayed beside it.
Inspect the full link target and compare it with the intended number. Remove pasted tags, replace placeholders and use a valid extension parameter where needed. Include an international number or the required phone context. Test the destination on a suitable device without making an unwanted call during automated checks.
/how-to/fix-phone-links-that-will-not-dial/

cvr.value_prop
Does your homepage say what you do?
It reviews the saved opening text for an absent or inward-looking statement.
The test requires a supported prose language and a successful homepage or audited page. Missing opening text, or fewer than 25 characters, produces the absent-value finding. Otherwise the code counts inward terms such as references to the company and outward terms addressing the customer. At least 3 inward matches with no outward match produce a separate medium-severity finding. It does not measure the physical fold of a rendered screen. For example, opening text shorter than 25 characters is reported as missing an offer explanation.
Saved opening text from the homepage supplies the input. In a single-page scope, the explanation names the audited page instead of asserting that the root homepage was read.
An absent statement is high severity. Inward-only statements are medium. Phrase counts do not establish whether the offer is useful or whether the language fits the audience.
The opening passage gives a visitor an early account of the page's purpose. Counting pronouns can suggest a passage to review, but a clear statement of the offer matters more than adding a customer pronoun to an unclear sentence.
Read the opening text without the rest of the site. Say what the business provides and who it helps in concrete terms. Keep the statement accurate and let supporting detail follow it. Review the rendered page after editing so that decorative headings or repeated brand text do not hide the actual explanation.
/learn/conversion-audit/
""")

copy_rows("""
index.broken
Which pages failed during the crawl?
It separates server errors, missing pages, refusals and requests that could not finish.
Responses marked as challenges are excluded from the main status groups. Server responses with HTTP status from 500 up to but below HTTP status 600 are critical. Missing responses with HTTP status 404 or HTTP status 410 are separated from refusals with HTTP status 401 or HTTP status 403 and other rejected client requests. A zero status with an error is divided into timeouts, malformed links, connection refusals on otherwise answering hosts and hard failures. Prose-like URL paths are guarded against misleading missing-page claims. For example, a refusal with HTTP status 403 needs a different review from a missing-page response with HTTP status 404.
The check uses response statuses, errors and incoming links from the crawl. Refused or challenged requests may leave the destination unchecked. Keep those outcomes in view when deciding which link to change.
Severity ranges from medium for several refusal or timeout cases to high for hard failures and broken internal links, and critical for server errors. A refusal means the audit could not read the page. It is not automatically proof that a visitor sees a missing page.
Different failures need different fixes. Separating a missing address from a server rejecting requests avoids telling you to delete a useful page when the real issue is access or crawl pressure.
Open the cited source link and review the saved response. Correct a malformed destination, restore genuinely missing content or redirect an obsolete address to a relevant replacement. Investigate server errors and request refusals with logs. Retest timeouts before declaring the page dead, especially when other pages on the same host still answer.
/how-to/pages-an-audit-could-not-reach/

index.byte_cap
Does important markup fall beyond the fetch budget?
It compares decompressed HTML size and important markup offsets with a fixed byte budget.
The cap is 2097152 bytes, with 1024 bytes reserved for headers. Successful HTML pages larger than the remaining budget are checked. Important tags found strictly beyond that budget produce high severity. An oversized document with no identified tags beyond it produces medium severity. The header allowance is fixed for every response. For example, the same 1024-byte header allowance applies to each measured HTML response.
Successful HTML responses supply document size and recorded offsets of important markup. Images, stylesheets and other separate files are not added to this HTML-byte comparison.
Important markup beyond the read budget is high severity. An oversized document without identified lost markup is medium. A truncated response leaves its full size unknown. Keep the saved limit beside the size when reviewing it.
A large document can put important tags beyond the read budget. The check compares their recorded positions with that budget. Review the actual document order before choosing what to reduce.
Inspect the document source and the locations named in the finding. Reduce excessive inline scripts, style blocks or repeated markup, and keep essential head tags early. Retest the decompressed HTML after changing the template. Review the actual source order rather than relying on the visual location of content in a browser.
/learn/googlebot-2mb-limit/

index.canonical
Do your canonical tags name the right pages?
It checks missing, conflicting, off-site and unusable canonical targets.
The check reads canonical declarations from indexable pages. Distinct target strings after trailing-slash handling identify conflicts. It separates off-site targets from hosts whose last 2 domain labels match, recognises declared syndication, and checks saved targets for indexability. Redirect aliases and default-index spellings are treated differently from a genuinely different page. A non-self canonical can produce a low-severity result when a stronger target problem was not already reported. For example, hosts sharing their last 2 domain labels receive different handling from an unrelated off-site host.
The check compares canonical tags, redirects, measured target pages and selected wording about republished content. An uncrawled target can remain unknown. Check the intended destination before changing a declaration.
Missing canonicals are medium, conflicts and noindex targets high, and unrelated off-site targets critical. Declared syndication is medium. Spelling aliases and other non-self targets are low. These cases preserve the difference between a deliberate relationship and a template mistake.
A canonical is a statement about which address should represent content. Checking the actual target matters because a syntactically valid tag can still name another domain, an excluded page or an address that redirects back to the source.
Choose the intended representative URL for the content. Make the HTML declaration consistent, use the final address where appropriate and check that the target can be indexed. Preserve intentional syndication after confirming the agreement. Fix shared templates before editing individual pages when the same wrong host appears throughout the site.
/how-to/fix-conflicting-canonicals/

index.canonical_conflict
Do your HTTP and HTML canonicals disagree?
It compares a canonical in the response header with the canonical in the HTML.
The page must be intended for search and have a canonical in both its HTTP Link header and its HTML. Its header address is resolved against the page URL. Both targets have trailing slashes removed before comparison. Different targets produce a conflict. A page with only an HTML canonical produces no conflict here.
The check reads the saved HTTP headers and HTML canonical values. A server or proxy may add a header separately from the page template. Inspect both places before editing.
Conflicts are high severity. The report gives a source page and both targets so that the server configuration and page template can be reviewed together instead of guessing which layer supplied the wrong value.
Separate configuration layers can make separate claims for the same response. A correct-looking tag in page source does not reveal a conflicting HTTP header, which explains why looking at the browser document alone can miss this test.
Choose the intended canonical destination. Align the server or proxy header with the HTML tag. Check every layer that can add a declaration. Request the page again and inspect both values in the new response.
/how-to/fix-conflicting-canonicals/

index.depth
Are useful pages hard to reach through links?
It reports deep pages and sitemap pages with no observed internal links.
Indexable pages at a depth of 4 clicks or greater enter the deep-page test. Orphans are indexable sitemap entries with no internal inlinks, excluding the homepage. When the crawl cannot support link-graph claims, the code reports that depth or orphan status could not be checked instead of asserting the defect. A sufficiently complete graph allows the corresponding depth and orphan findings. For example, a page at a depth of 4 clicks enters the deep-page review.
The check uses measured click depth, internal links and the saved sitemap list. An incomplete crawl can leave the result unknown. Review what the crawl covered before moving pages or adding links.
Deep pages are low severity, confirmed orphans medium and withheld measurements notices. The result describes the graph the audit could establish. It does not prove how every user navigates or that every deep page needs a place in the main menu.
A sitemap can reveal a URL without showing how a visitor reaches it from another page. The graph requirement protects that distinction and prevents incomplete discovery from being presented as a confirmed absence of links.
Review the route to useful affected pages. Add relevant links from pages where a visitor would expect them, and repair links that point to obsolete addresses. Keep intentional utility pages separate from useful public content. If the finding says the graph was incomplete, improve crawl coverage before making structural changes based on that uncertainty.
/learn/click-depth-and-orphan-pages/

index.duplicate_content
Do different URLs repeat the same content?
It groups identical page bodies, titles and descriptions after checking canonical agreement.
Body comparison ignores pages with fewer than 50 words and hashes lowercased text with normalised whitespace. Groups sharing a single nonempty canonical are excluded. A separate substitution case needs at least 5 pages across at least 4 sections with no page above 200 words. Duplicate titles and descriptions are grouped independently. Redirect scheme splits and regional alternatives change the explanation rather than turning all identical text into the same diagnosis. For example, a page with exactly 50 words is long enough for the body-text comparison.
The check reads body text and metadata from pages with usable content. Body matching ignores capitalisation and extra spaces, then compares the resulting text exactly. A separate test compares the subjects suggested by titles.
Duplicate bodies are high severity, titles medium and descriptions low. Repeated short responses across unrelated sections are medium. The report distinguishes a shared error or substitute response from normal pages that genuinely contain the same text.
Identical bodies can appear because of duplicate publishing, multiple address forms or a server serving a substitute response. Understanding which case applies is necessary before deciding whether to merge content or repair delivery.
Compare the saved bodies with the expected pages. Fix substitute responses at the server or template level. For real duplicate addresses, select the intended canonical or redirect where appropriate. Write distinct titles for distinct pages. Preserve valid regional alternatives and review their language annotations before treating them as accidental copies.
/how-to/identical-content-three-causes/

index.meta_refresh
Does your page redirect through the browser?
It separates JavaScript redirects from HTML meta refresh redirects.
A successful page with a recorded JavaScript redirect produces a low finding. Meta refresh instructions produce a notice. Delays greater than zero are collected to explain when visitors must wait. The check reads redirect instructions from the document. It can find them even when the server returned a successful response.
The check reads successful responses and their recorded JavaScript or meta refresh redirects. These instructions run after the initial response. Server-side redirects are checked elsewhere.
JavaScript redirects are low severity and meta refresh results notices. The report identifies the mechanism and any delay. It does not establish whether the destination is relevant or whether a deliberate delay is justified for the page.
A page can answer successfully and still send a browser elsewhere. That makes a status-only review incomplete, which is why this test examines document instructions separately from HTTP redirect responses.
Check the source URL, destination and reason for the move. Use a server redirect for a permanent address change when suitable. Preserve intentional browser flows only after reviewing their purpose and delay. Test the source response and the final destination after editing so that a replaced redirect does not leave a second client-side hop behind.
/how-to/fix-meta-refresh-redirects/

index.noindex
Are useful pages marked to stay out of search?
It checks noindex directives while excluding several intentional and sitemap-only cases.
Successful pages with a noindex directive enter the initial set. A root homepage marked noindex is critical, with separate wording when the starting host moved elsewhere. Utility URLs and tag or author archives are excluded from the ordinary blocked-page count. Pages found only in the sitemap without observed links are also separated. Remaining blocked pages are high severity above a 0.2 share of successful pages and medium otherwise. For example, a blocked-page share of exactly 0.2 stays within the medium group after the exclusions.
The check reads meta and HTTP-header directives, homepage status, sitemap entries, redirects and observed links. A utility page can be deliberately excluded from search. Confirm the page's purpose before removing a directive.
The report separates an accidental exclusion of important content from pages commonly kept out of search. A successful HTTP response alone does not cancel a noindex directive, and a noindex flag alone does not establish that you intended the page to rank.
The directive expresses an indexing choice. Reviewing the page's purpose before removing it avoids exposing a confirmation, account or search-results page merely because it appeared in a crawl.
Confirm which affected pages should be public search entries. Remove unintended noindex directives from those pages in both HTML and response headers. Keep deliberate exclusions and remove inappropriate sitemap entries. Check the root homepage separately, then request the page again to confirm the served directive changed.
/how-to/stop-indexing-site-search-and-cart-pages/

index.redirects
Do your redirects make unnecessary stops?
It finds redirect loops, longer chains and internal links pointing at a redirect.
A recorded redirect loop produces a critical finding. Chains with at least 2 hops produce a medium finding. Exactly 1 hop with internal links to its starting address produces a low finding. For example, a menu link that redirects once can need an update to its final URL. These tests use recorded server redirects.
The check reads redirect history from the full page set. Incoming links show which old addresses the site still links to. Repair those links at the page or template that supplies them.
The report distinguishes a loop that prevents resolution from a working chain and a working redirect still used by internal links. A valid address move can remain intentional even when the links pointing to its old location need updating.
Each recorded hop is another request before the destination is reached. A loop has a different effect from a successful move, so the code keeps the most disruptive case separate from routine link cleanup.
Resolve loops first by choosing a final destination and removing rules that send requests back. Shorten chains where an old address can point directly to that destination. Update internal links to the final relevant URL. Retest both the original address and the destination to catch rules that vary by scheme or host.
/how-to/fix-redirect-problems/

index.robots_blocks_all
Does robots.txt block a whole search crawler?
It checks whole-site search restrictions and problems reading the robots policy.
The check uses the saved robots file's access rules for search crawlers. A response with HTTP status 500 or above leaves the policy unreadable and produces a critical server-error finding. Blocking Googlebot across the site is critical. Bingbot blocks are high, and another supported crawler block is low. Syntax problems are low. A crawl-delay wait skipped by the audit produces a notice. For example, a robots response with HTTP status 500 produces the server-error result and leaves the policy unreadable.
This site-wide test reads the robots response, its rules and the saved crawl-delay result. It does not need article pages to run. A failed robots request can leave the intended policy unknown.
The report distinguishes policy restrictions, parsing problems and an audit that did not honour the requested wait. A failed robots request cannot prove which individual allow or disallow rule would apply if the file were readable.
Robots rules state where a crawler may go. A site-wide restriction can prevent crawling when that was never intended. Check that the file loaded successfully before treating its absence or unreadability as a deliberate policy.
Inspect the root robots response and the exact applicable group. Remove a whole-site block only when it conflicts with your intended policy. Repair server errors before interpreting missing rule data. Correct syntax in place, then check the saved access result again. Review crawl-delay handling as an audit setting rather than changing your public policy solely to speed a test.
/learn/what-is-robots-txt/

index.sitemap
Does your sitemap list usable current URLs?
It checks sitemap discovery, responses, URL quality and coverage against the crawl.
The check separates missing or refused sitemap probes, broken declared files, malformed paths, dead entries, refused entries, redirects and noindex pages. A declared file response with HTTP status 400 or above is broken only outside the refusal set. Missing indexable entries are reported when their count exceeds the larger of 3 entries or a 0.15 share of crawled indexable pages. Redirects become medium rather than low when they exceed the larger of 1 entry or half the listed entries. For example, exactly 3 missing entries cannot exceed a threshold that is at least 3 entries.
Saved sitemap files and entries are joined to crawled pages using the current URL and redirect history. Timeouts and connections refused on otherwise answering hosts are guarded against false dead-entry claims.
Broken files are high severity. Missing files and dead entries are medium. Several coverage or indexing problems are low. Unreadable results are notices. Keep the response status beside the reported URL during review.
A sitemap is a list of addresses, so its value depends on the addresses it actually names. Comparing it with measured responses can reveal stale entries without mistaking a temporary refusal for proof that a page no longer exists.
List final public indexable URLs. Remove obsolete, redirected and intentionally excluded entries after checking their purpose. Repair the sitemap generator if malformed paths repeat. Investigate refusals and timeouts before deleting entries, then fetch the file again and compare it with a fresh crawl of the affected pages.
/how-to/sitemap-urls-that-are-not-stale/

index.soft_404
Do missing pages return a proper error status?
It reports the saved site probe for a missing page that answered as successful content.
The check uses the crawl's saved missing-page test result. A positive result produces a medium finding for a missing page returning HTTP status 200 instead of HTTP status 404. This check uses that earlier test. It does not make a new request or compare every article's text.
The check reads the site's saved missing-page test result. It needs no article sample or percentage of failed pages. Review the tested address and response before changing error handling.
The finding is medium severity. A false flag produces no finding from this check, which is narrower than proving that all possible missing addresses on the site return the correct response.
Successful statuses and not-found messages communicate different outcomes. The check highlights that disagreement so you can review the route handling rather than assuming that the visual error page alone defines the response.
Request a genuinely nonexistent address and inspect its response status as well as its appearance. Make the missing-page handler return the appropriate error while keeping useful navigation for the visitor. Avoid sending every unknown address to the homepage as successful content. Recheck the original probe case after changing the server or application route.
/how-to/fix-soft-404s/

index.soft_404_pages
Do successful pages show a not-found message?
It finds short successful pages containing one of the stored missing-page messages.
The test reads successful pages and skips any with more than 250 words. It searches the title plus the first 1500 characters of text for the literal not-found markers. Matching pages are separated according to whether another crawled page links to them. The presence of an observed source link raises severity from medium to high. Matching words alone leave the cause of the response unknown. For example, a page above 250 words is left out even if it discusses a not-found message.
Crawl records supply successful responses, short page text, titles and incoming links. This test does not use the separate site-level probe of a nonexistent address.
The finding reports a conflict between a successful response and an error-like body. A short article discussing an error message can need review before being treated as a missing page, because the check is a phrase test with a length guard.
Missing-page messages and successful statuses tell readers' software different things. An internal link to that response also gives you a source to repair. Review the message and the linking page together.
Open the affected URL from its source link. Restore the intended content if it should exist, or return a proper missing-page status if it does not. Fix internal links that still lead there. If the page is a genuine explanation of an error, verify its content and response before changing it solely because a phrase matched.
/how-to/fix-soft-404s/

index.url_hygiene
Do your URLs contain avoidable clutter?
It checks address spelling, length, query parameters and session identifiers.
The check looks for uppercase URL paths, encoded spaces and addresses longer than 115 characters. A query with at least 2 ampersands joins the multiple-parameter group. That group is reported only above the larger of 3 pages or a 0.25 share of indexable pages. Known session names are checked in queries and path parameters. Each type has its own finding and severity. For example, an address exactly 115 characters long is outside the long-URL group.
The check reads the address itself. It does not decide whether every parameter is needed. Review the destination and its use before changing the URL.
Session identifiers are high severity, multiple-parameter findings medium, uppercase and spaces low, and long URLs notices. These are review categories rather than a claim that every long or parameterised address is broken.
Different spellings and session data can make an address harder to manage consistently. A parameter can also be necessary, so the check identifies a pattern to inspect instead of proving that every matching part should be deleted.
Review which URL parts identify content and which only track a session or view. Keep stable public addresses and update links when changing them. Use redirects or canonicals deliberately for real alternatives. Test query-dependent pages before removing parameters so that cleanup does not erase filters or other useful page states.
/learn/url-structure/

index.www
Do your www and bare addresses agree?
It reports the saved result for host canonicalisation.
The check uses the saved test of www redirects. If that test failed, it produces a high finding for a site reachable with and without www, without the expected redirect. It does not choose the preferred host or inspect every internal link. Review the measured host responses before changing server settings.
The check uses the earlier host test. It does not assign a content-duplication percentage or a ranking effect to either host spelling. You choose the preferred address for the business.
The finding is high severity. It describes the observed host setup and does not mean that using www is inherently better or worse than using the bare domain.
A consistent public host gives the site a clear address policy. The useful question is whether the alternate address leads to the intended one, rather than which spelling a tool happens to prefer.
Choose the host your site should use and configure the alternate host to redirect to it. Keep the path and query where appropriate. Align internal links, canonicals and sitemap addresses with that choice. Test both host variants over the relevant schemes after editing server rules, since a working homepage rule may not cover inner paths.
/learn/www-vs-non-www/
""")

copy_rows("""
intl.hreflang_codes
Are your hreflang codes recognised?
It separates malformed, superseded, unsupported and unrecognised language-region codes.
The sample uses successful pages with hreflang. Empty values, x-default and repeated values are skipped. The format allows 2 language letters or 3 language letters, an optional 4-letter script and an optional region of 2 letters or 3 digits. Known region mistakes, private-use regions, numeric regions, old language codes and unknown values receive different explanations. A value missing from a recognition table stays unrecognised until it can be checked. For example, a 4-letter script subtag can appear between the language and region.
The check reads declared alternate-language codes. It does not judge translation quality or inspect an unavailable target's language. Review each declaration against its intended audience.
Malformed codes are medium severity. Superseded languages and unsupported regions are low, while unrecognised regions or languages are notices. The report distinguishes a known defect from a limit in the audit's own reference tables.
A language code states which audience an alternate page serves. Keeping unknown values separate from known mistakes avoids replacing a legitimate declaration on the strength of an incomplete lookup table.
Review the exact code and the audience it should identify. Correct known typos and use a supported language-region form where needed. Verify unfamiliar values against the relevant registry before changing them. Check the target page and return tags after fixing the code, since spelling alone cannot establish a complete alternate-language relationship.
/how-to/fix-invalid-hreflang-codes/

intl.hreflang_return
Do your language alternatives link back?
It checks reciprocal hreflang declarations between pages the crawl successfully read.
At least 2 successful pages with hreflang are needed. Source and target addresses are compared without trailing slashes. Self-links and targets not in the successful crawl set are skipped. For each remaining declaration, the target must declare the source in return. A missing return relationship enters the finding. It is not inferred for an alternate URL whose page was never available to compare. For example, with 2 successful alternate pages, each can be checked for a return link to the other.
The check compares alternate-language declarations on successful pages. Targets that could not be loaded are skipped. No missing return link is claimed for those unchecked pages.
Missing return links are high severity. The result names a source and target pair, while incomplete target coverage limits which relationships the audit can judge.
An alternate-language relationship is meant to connect versions of content. Comparing both directions reveals a partial template update that looking at either page in isolation can miss.
Open the source and target declarations together. Add the intended reciprocal link with the correct language code and final URL, then check the rest of the same group for consistency. Keep the self-reference where appropriate. Crawl the target before treating a relationship outside the measured page set as confirmed broken or confirmed complete.
/how-to/fix-hreflang-return-tags/

intl.hreflang_self
Does each language page include itself?
It looks for a self-reference in pages that already declare hreflang alternatives.
The check selects successful pages with hreflang. For each page, it builds the declared target set and compares the page's own URL after removing trailing slashes. A page missing from its own target set enters the finding. Sites with no hreflang pages produce no finding here, so this test does not require a single-language site to add alternate-language markup.
Only existing alternate-language declarations are reviewed. It does not infer a translation from similar text or decide which language code the page should use.
Missing self-references are medium severity. The target comparison is address-based, so an alias that differs beyond a trailing slash needs review rather than being silently treated as the page's final URL.
An alternate set should describe the page being read as well as its alternatives. A self-reference gives the same kind of address declaration for the current version that the markup gives for the others.
Inspect the page's alternate-language group. Add the current page under its correct language code and use the intended final address. Apply the same group consistently to related versions where appropriate. Review return links and target health separately, because a self-reference does not prove that the rest of the group is usable.
/how-to/fix-hreflang-return-tags/

intl.hreflang_targets
Do your language links point to usable pages?
It checks measured hreflang targets for errors, redirects and noindex directives.
Targets are matched to saved pages using the exact address and trailing-slash alternatives. Unmeasured targets are skipped. Refused responses and zero-status failures are reported as unchecked rather than dead. Other responses with HTTP status 400 or above, addresses known to redirect away and pages carrying noindex can enter the unusable-target finding. The code uses saved redirect history to recognise an alternate address that was not the final page. For example, a measured HTTP status 400 can enter the unusable-target finding after refusal handling.
Successful pages supply the alternate-language links. The wider crawl supplies responses for their destinations. An unmeasured destination stays unknown and needs a separate review.
Unusable targets are medium severity and unchecked targets notices. The distinction prevents a blocked request or failed fetch from being presented as certain proof that a translation no longer exists.
A correctly written alternate link can still name an address that does not serve an indexable page. Checking the measured destination adds details beyond code spelling and reciprocal tags.
Use the final intended URL for each alternate. Repair genuinely missing pages or remove obsolete alternatives, and review unintended noindex directives. Investigate refused requests before replacing a valid translation. Retest the target and the source declaration together after a change so that the markup names the address that actually serves the content.
/how-to/hreflang-targets-that-look-dead/

links.broken_external
Do your outbound links still work?
It separates broken external destinations from refusals, sharing links and malformed addresses.
The test uses saved external statuses, excluding image probes and recognised share-intent links. Doubled-scheme addresses are reported separately. Links to related own hosts are separated from third-party links. HTTP status 400 or above, or a zero status, can be broken only after refusal handling. Known refusal codes, HTTP statuses at or above 600 and recorded hangups are treated as unverified instead. Source links are collected for the remaining broken targets. For example, HTTP status 600 or above stays unverified under this test.
The saved external-link measurement determines coverage. Per-host caps and time limits can leave links unchecked, so this test is not a promise that every outbound URL on every page was tested.
Broken links and malformed or own-subdomain cases are low severity. Unverified destinations are notices. A destination refusing the audit may still work for a visitor, which is why the code avoids calling every unsuccessful request a dead link.
Broken and untestable destinations need different decisions. Keeping those outcomes separate helps you repair actual address errors without deleting a useful source because its server rejected an automated request.
Open the destination and inspect the cited source link. Correct doubled schemes and obsolete addresses, or replace a dead source with a relevant working one. Review refusals manually and respect rate limits. Check the source page after editing so that both the visible label and the hidden destination still describe the resource you intended.
/how-to/fix-broken-outbound-links/

links.http_on_https
Does your secure site link to plain HTTP pages?
It finds internal links written with an insecure scheme on a site served over HTTPS.
The check stops when the site is not served over HTTPS. On a secure site it scans indexable pages for internal links beginning with http. Pages with such links enter a low-severity finding, with an example destination. Even a working redirect can leave the site's own links using the older scheme. Those links can qualify without a failed destination.
The check uses the site's security status and internal links read from pages intended for search. It compares the URL schemes. You need to review the response and final destination separately.
The finding is low severity. It describes the spelling of internal destinations, not proof that the final page remains insecure after redirects or that every visitor receives an error.
A secure page can still send a visitor through a plain-scheme address in its links. Reviewing the source link makes it possible to align the site's own navigation with its intended secure address policy.
Update internal destinations to the correct secure final URLs. Check shared menus and templates before editing repeated links individually. Confirm that the destination works over HTTPS and preserve paths and queries that identify the content. Review the redirect policy separately so that old external links still reach the intended page.
/how-to/redirect-http-to-https/

links.internal_volume
Do useful pages have enough internal links?
It checks sparse outgoing links and widespread pages with a single observed incoming link.
At least 5 pages with readable content are needed. A page other than the homepage with at most 2 outgoing internal links can be flagged as sparse. Below the root, a page other than the homepage with exactly 1 incoming internal link joins the weak-link group. That group is reported only above a 0.3 share of readable pages and with enough crawl coverage to judge links. Incoming and outgoing links are checked separately. For example, a page with exactly 2 outgoing internal links can enter the sparse-link group.
The check reads pages with usable content and the internal links observed by the crawl. Missing coverage can prevent a finding. Review which sections were crawled before adding site-wide links.
Sparse outgoing links are low severity. Widespread single-inlink pages are medium. A count alone does not tell you whether a link is relevant, so adding unrelated links merely to increase the total would miss the page's purpose.
Outgoing links and incoming links describe different routes through a site. A page can link to plenty of content while being difficult to discover from elsewhere, which explains why the code checks both directions.
Review the affected page in its section. Add useful contextual links to related information and link important pages from places where visitors expect to find them. Repair obsolete destinations before adding more links. If the graph is incomplete, improve coverage before treating an apparent lack of incoming links as a confirmed structural problem.
/learn/internal-link-equity/

links.money_page_weak_inlinks
Can visitors find the pages that sell?
It finds non-homepage selling pages with exactly a single observed internal inlink.
Enough crawl coverage is needed to judge internal links. The check selects pages with readable content and a recognised selling-page address, leaving out the homepage. Exactly 1 observed incoming link qualifies. For example, a service page linked only from its menu can qualify. Business importance still needs your review.
The check uses readable pages, selling-page addresses and observed internal links. A browser-only menu or limited crawl can leave links unseen. Check that coverage before treating the count as complete.
The finding is medium severity. Its scope is the recognised selling pages with a measured single source, rather than a complete inventory of every URL that can contribute to an enquiry or purchase.
A service or product page needs a route from other useful parts of the site. The check gives extra attention to pages recognised as selling, while leaving the owner to decide which specific pages matter to the business.
Find the page's place in the site's navigation and related content. Add relevant links from category pages, useful articles or other routes that naturally lead to the offer. Use labels that explain the destination. Keep the page's purpose clear and avoid adding repeated irrelevant links solely to change a graph count.
/how-to/fix-your-money-pages-first/

links.nav_not_in_html
Is your navigation present before scripts run?
It checks the saved navigation-in-HTML result across successful HTML pages.
At least 3 successful HTML pages are needed. If the saved crawl flag says navigation is present in HTML, the check stops. Otherwise it counts internal links, calculates links per page and reports the missing navigation, with separate wording when the total is zero. Sitemap counts and unlinked pages support the explanation. The registered condition does not use an average-link cutoff to decide whether the navigation flag is true. For example, 3 successful HTML pages are enough to begin the navigation check.
The check uses successful HTML responses and the crawler's record of whether navigation is in the HTML. Its claim concerns links in the server response. Review loaded-browser navigation separately.
The finding is high severity. A browser can display a menu that was absent from the document the crawler read, so visual inspection after loading answers a different question from this source check.
Sitemaps can expose addresses without supplying the navigation links between pages. Reading the initial document shows whether those routes are available before browser code adds them.
Compare the menu visible in the browser with links in the served source. Render real navigation links in HTML on the server or during the static build. Keep script enhancements for opening and styling menus as needed. Retest several inner pages as well as the homepage, because a shared navigation fix should reach the templates it is meant to serve.
/how-to/fix-navigation-that-needs-javascript/

links.outbound_quality
How does your site handle outbound links?
It checks whether external links are absent, dominated by a host or almost all nofollow.
The check counts external links on indexable pages after excluding related own hosts. No outbound links on at least 8 indexable pages produces a notice. A host needs more than 20 links and more than a 0.6 share of all external links for the dominance finding. More than 10 total external links with a nofollow share above 0.9 produces a separate notice. Each comparison uses strict greater-than where stated. For example, exactly 20 links to a host do not exceed the host-dominance count limit.
The check counts external destinations and nofollow links read from pages intended for search. It does not inspect every target's quality or commercial relationship. Those decisions need your review.
Host dominance is medium severity. No-outbound and near-universal nofollow results are notices. These patterns can have valid explanations, so they are review cues rather than a command to add links to unrelated sites.
A concentrated link pattern can come from a shared template or a deliberate relationship. Looking at the actual destinations and labels gives the context a ratio alone cannot supply.
Review repeated external links and their purpose. Remove abandoned widgets or stale relationships where appropriate, and keep useful references. Apply nofollow according to the relationship of the link rather than automatically across every external destination. Recheck shared templates when a repeated host accounts for much of the total.
/how-to/fix-broken-outbound-links/

links.pagination
Do your paginated pages name their own content?
It looks for numbered listing pages whose canonical points to a non-paginated address.
At least 2 successful pages with recognised numbered pagination URLs are needed. The patterns cover page path segments and page or p query parameters. A paginated page enters the finding when it has a canonical whose address does not match one of those pagination patterns. The test checks the shape of the canonical target, not whether the target contains the same list items. For example, a numbered listing needs at least 2 successfully crawled pages before this comparison can run.
The check reads successful numbered-page URLs and their canonical tags. It compares address patterns. Review the list items yourself before choosing a canonical destination.
The finding is medium severity. It reports a likely collapse of separate listing content, but a real duplicate page or an intentionally different design still needs review before the canonical is changed.
Different listing pages can contain different entries. A canonical that names an unnumbered page can make a different statement from the content the visitor is reading, which is the relationship this test asks you to inspect.
Compare the listed entries on the numbered page with those on the canonical target. Use the intended canonical for genuinely distinct listing content, and keep links between listing pages readable. Preserve a canonical relationship only when it accurately describes duplicate content. Retest the final URLs and tags after changing the pagination template.
/how-to/fix-paginated-pages-that-canonicalise-to-page-1/
""")

copy_rows("""
local.applicable
Should local business checks run on your site?
It checks whether your public business details call for local business tests.
The check looks for business markup, physical addresses, contact and location links, and local wording. It accounts for software sites and addresses belonging to listed people or businesses. If no pages load successfully, or all need scripts for their main content, local status can stay unknown. Otherwise it explains whether the site appears local. For example, a directory can list physical shops while its publisher operates entirely online.
The check reads the site's business context and readable contact details. A directory may publish other businesses' addresses. Review whose premises each address describes.
Applicable and not-applicable outcomes are passes. An undetermined outcome is a notice. A pass here describes scope, not a judgement that every local business detail is complete or correct.
Local requirements depend on what the site actually represents. A scope decision helps avoid asking an online-only product for a map while still allowing useful checks on a site that publishes real local business data.
Read the details behind the scope result. Correct misleading business markup or location text if it describes the wrong organisation. If the site is a browser-built shell, improve readable content before expecting a confident scope decision. Review individual local findings separately once the business context is established.
/how-to/where-an-audit-looks-for-your-address/

local.contact_signals
Can local customers call, write or find you?
It checks tappable contact routes, maps and enquiry forms where local checks apply.
The check requires supported prose and local-business applicability. Across the first 40 indexable pages, it looks for phone or text-message links when plain numbers are present. A map can be recognised from iframe hosts or a saved map flag. The missing-map case needs a contact page and a locally served market. Form absence is checked across all indexable pages, rather than only the initial sample. For example, a phone printed only outside the first 40 sampled pages can be missed by the tappable-number test.
The check reads published phones, link targets, map resources, contact paths and form counts. A business that only accepts texts can use message links. Check the offered contact method before changing a link to invite calls.
An untappable number is medium severity. Missing maps and forms are low and require full-crawl support for their absence claims. A business that does not welcome physical visits should not add a misleading map solely to change the report.
The routes a customer can use depend on the service. Separating calls, texts, physical visits and forms keeps the suggested change tied to the contact choice the business actually offers.
Make published numbers link to the route they support, whether calling or texting. Add a useful contact form when appropriate, and provide location help only for a place customers should visit. Check existing off-site routes before duplicating them. Test links and form completion manually after changing a shared contact template.
/how-to/fix-inconsistent-name-address-phone/

local.geo_targeting
Does your local content say where you work?
It checks place names in titles and postal codes for a local market.
Local-business status and a local market are required. The check searches address text from the first 40 indexable pages, using up to 4000 characters each. It reads all indexable titles for recognised place names and the business's own places. At least 4 titled pages with no location mention produce medium severity. No recognised postal code produces low severity. For example, 4 titled local pages with no recognised place mention can reach the title finding.
The check reads titles, address text, footer details and places declared for the business. An office address alone does not explain where an online product is sold. Review the audience and service area.
The report identifies missing location cues rather than proving the site cannot serve a place. Place and postcode recognition have limits, so inspect the actual address and audience before changing useful wording.
A local page needs to make sense to someone checking whether the service reaches them. The market gate narrows that question so that an irrelevant office location is not forced into every title.
State the real service area where it helps a visitor decide. Include a complete address or appropriate service-area information in a clear contact location. Use accurate place names in relevant titles without adding towns you do not serve. Review the displayed footer and markup when the report missed an address already published.
/how-to/where-an-audit-looks-for-your-address/

local.nap
Are your business contact details consistent?
It reviews phone numbers and addresses while allowing genuine multiple locations.
The site must qualify for local business tests. Contact details are sampled across up to 60 pages intended for search. Several phone checks need at least 7 digits. More than 2 different phone numbers can produce an inconsistency finding unless multiple locations are recognised. A set with more than 3 address variants can produce a low finding when they describe a single place. Missing-phone and missing-address claims also depend on language, coverage and service area. For example, exactly 2 varying phone numbers stay within the count limit for the inconsistency test.
The check uses address text, phone markup, published numbers, contact-page roles and available browser output. It tries to identify which details belong to the business. Review any listed person's or listed business's contact details separately.
Missing phones are high severity. Absent addresses and inconsistent phones are medium. Inconsistent addresses are low. Different departments or locations may explain valid differences. Review each cited value before deleting it.
A business may have several valid departments or premises. Group numbers and addresses by the place or team they belong to. Then look for conflicting details about the same contact route.
Confirm the intended numbers and locations with the business. Update stale templates and business markup. Preserve valid location and department details. Explain any service-area policy where customers cannot visit an office. Compare the visible page, dialling links and structured fields after editing.
/how-to/fix-inconsistent-name-address-phone/

local.reviews
Does your local site show real customer reviews?
It looks for customer reviews and for item reviews that could need markup.
The test needs a supported prose language and a site that qualifies for local business checks. It reads up to 3000 text characters from each of the first 25 pages intended for search. Review markup is checked across all indexable pages. It checks whether review phrases are negated or supported by other details. A business identified as LocalBusiness with no recognised reviews can receive a medium finding. Visible reviews of supported items without review markup can receive a low finding. Check eligibility before marking up ordinary business testimonials. For example, wording outside the first 3000 text characters can be missed in a sampled page's review search.
The check reads review and rating markup, sampled text and review-page context. It cannot verify the writer's identity or whether a review is authentic. You need to confirm the source.
Missing business reviews and missing item-review markup describe different issues. Read what the review is about before adding ratings. The visible review and declared subject need to match.
Real customer experiences can help a visitor understand a service. The wording needs context and a sound source. Finding a review phrase leaves its authenticity for a person to verify.
Publish reviews only with a sound basis and permission where needed. Keep the review attached to the business or item it actually describes. Add suitable markup only when the visible content and type support it. Review negative statements and examples before changing a page that merely discusses reviews.
/for/local-business/

local.schema
Does your local business markup fit the business?
It checks local identity markup and important fields while respecting business type and ownership.
After local applicability, the check reads owned and listed local nodes, preferring the business's own nodes. It reviews address, telephone or phone, hours, coordinates or map, URL, image or logo, and price range. Empty values count as missing. The most complete candidate supplies the gap list. Script-built types, organisation-with-address cases and specialised identity types can suppress or change a missing-LocalBusiness claim.
The check compares business markup and declared types. A directory entry may describe someone else's premises. Keep that entry attached to the business it names.
Missing or incorrectly broad identity can be high severity. Incomplete owned nodes are medium, while incomplete listed-business nodes are low. Presence of a field key alone does not establish a useful value.
A business type is a claim about what the site represents. Accurate values matter more than adding empty keys, and a different legitimate identity type can be the correct choice for a physical organisation.
Choose the identity type that matches the organisation. Fill applicable fields with real details and keep them aligned with visible contact information. Do not add invented opening hours or prices to complete a list. Review whether each node describes your business or someone listed on the site before changing shared markup.
/how-to/when-a-field-is-there-and-still-missing/

mar.ad_pixels
Are your advertising pixels present and active?
It distinguishes detected pixels, staged pixels and incomplete page coverage.
The check combines tracking code found in server responses with available browser output. Code present but unable to run can produce a high finding. No pixels or staged code produces a notice, with separate wording for a tag manager. For pixels in server responses, coverage below a 0.7 share of successful pages produces a medium finding. Pixels seen only after scripts run are excluded from that coverage claim. For example, directly served pixel coverage of exactly 0.7 stays within the coverage limit.
The check reads detected trackers and available browser output. It cannot access an advertising account. Use the platform's own tools to confirm that an event arrived.
Staging, absence and partial coverage mean different things. A tag-manager container can hide configuration from this audit, and a rendered-only observation cannot establish which unrendered pages carry the same code.
Pixel scripts can exist without being able to run. Keeping that state separate from total absence helps you inspect loading and consent setup before adding another copy of the same tag.
Confirm which advertising tools you actually use. Inspect staged markup and the relevant consent or loading rule, then test the intended events with the platform's own tools. Add coverage only to pages that need it. Remove abandoned tags rather than installing pixels simply to turn an informational notice into silence.
/learn/marketing-tag-audit/

mar.analytics
Can your analytics tags cover the pages you need?
It separates missing analytics, consent-gated tags, opaque containers and measured coverage gaps.
The check uses trackers found in server responses and available browser output. Tag-manager-only setups, tags waiting for consent and recognised built-in analytics receive their own explanations. Comparable readable pages are checked for a tagged share below 0.85. Uneven browser coverage can prevent a fair comparison. Retired Universal Analytics tags are checked separately, with different wording when another analytics tool is present. For example, comparable tagged coverage of exactly 0.85 does not fall below the gap threshold.
The check uses detected tags, code waiting to load, platform clues and measured browser coverage. It cannot access an analytics account. Check visits and conversions inside the intended service.
Several missing-tag or coverage findings are high severity. Unclear containers or platform limits can produce notices. A retired tag can be low when another tool is present. Read which tag was found and where it was found.
Finding a tag in HTML shows that it was installed. Event delivery and data quality need their own checks inside the analytics service. Use the named tag to decide what to test next.
Confirm the analytics tool the business intends to use. Review the named tag and affected templates, checking consent and rendering before adding scripts. Use the tool's own live or debug view to verify events. Remove obsolete tags carefully and retest representative page types after changing shared code.
/how-to/analytics-findings-name-the-tag/

mar.consent
Do tracking tags have visible privacy controls?
It looks for a consent banner and privacy policy alongside detected tracking.
Detected advertising pixels or the recognised session-recording tools trigger the banner-presence condition. If none of the successful pages has a saved consent-banner flag, a medium finding is emitted. Any detected analytics or advertising tracking also prompts a privacy-policy presence check, with another medium finding when the policy is not found. Legal requirements for each visitor need a separate review.
The check reads detected trackers, banner detections and the privacy-policy lookup. Code waiting for consent and a tracker already running describe different states. Review how each tag loads when a visitor makes a choice.
Both findings are medium severity. A detected banner does not prove that it blocks the right tags, records a valid choice or satisfies any particular law. The check's title must not be mistaken for a legal compliance opinion.
What this observes is between tracking code and the controls or policy the site exposes. A presence test can flag a missing piece for review, while the behaviour of that control still needs to be checked directly.
List the tracking tools you intend to run. Review their loading against the consent choices you offer and make the privacy explanation accurate. Test acceptance, refusal and later changes of choice using suitable tools. Seek jurisdiction-specific advice where needed instead of treating an installed banner as proof of compliance.
/learn/marketing-tag-audit/

mar.email_capture
Can visitors choose to hear from you again?
It looks for recognised email tools, signup forms or invitation wording.
The check needs a supported prose language. A recognised email-platform tracker ends the test without a finding. Otherwise it reads up to 40 readable pages for a signup-form flag or signup wording. Text searches use up to 8000 characters plus action labels. At least 5 indexable pages with no signup signal produce a low finding. For example, a site with 5 indexable pages can receive the finding when no signup signal is found.
The check reads detected email tools, form types, text and action labels. It does not submit an address. Test the signup route and confirm that it reaches the intended list.
The finding is low severity. A recognised tool or invitation can satisfy the presence condition without proving that the form works, and a business may deliberately choose not to run a mailing list.
Visitors may want updates without making an enquiry. This test looks for a route that appears to support that choice, while leaving the business to decide whether an email list fits its service.
If updates are useful to your visitors, provide a clear invitation and explain what they will receive. Check that the form reaches the intended list and honours the choices you state. Keep enquiry forms separate where their purpose differs. Do not add a mailing platform solely because the audit reports an optional opportunity.
/learn/email-capture-audit/

mar.stack
Which marketing tools appear on your pages?
It inventories detected tools and raises severity when a page carries many of them.
The check lists tools found on each successful page, including available browser output. No detected tools means no inventory finding. Otherwise it names the tools and the largest count on a page. A page carrying at least 8 tools changes the result from a notice to medium severity. That page count is separate from the site's total number of different tools. For example, a page with 8 detected tools reaches medium severity even if other pages carry fewer.
Tracker signatures in saved served or rendered pages supply the inventory. It does not measure each vendor's account status, invoice, usefulness or contribution to page loading time.
An ordinary inventory is a notice. A page with the larger tool count produces medium severity. Check whether each detected tool still serves a business purpose and sends the expected data.
An inventory makes old or overlapping installations easier to review. The page maximum matters because a large site-wide list can be spread across separate page types rather than loaded together on every visit.
Match each listed tool to a current business purpose and owner. Remove abandoned installations through the template or tag manager that supplies them. Keep tools required for real workflows and test those workflows after changes. Review consent and loading separately instead of assuming that a smaller list alone proves a faster or compliant site.
/learn/marketing-tag-audit/

mar.utm_hygiene
Do internal links carry campaign tags?
It reports indexable pages linking within the site with UTM parameters.
The check selects pages intended for search with recorded internal links carrying UTM parameters. Any such links produce a medium finding. It totals the recorded links, with no minimum share or page-count cutoff. For example, a menu link with utm_source is an internal campaign-tagged link. The check counts the crawler's recorded links and leaves the effect on analytics data unmeasured.
Saved internal link lists show which pages qualify and supply the reported total. External campaign links are outside this test because its subject is navigation within the same site.
The finding is medium severity. It can establish that the links carry campaign parameters, but it does not read analytics reports or calculate a resulting attribution error.
Campaign labels describe where a visit came from. Applying those labels to a route inside the site creates a different tracking statement from an ordinary internal destination, which is why the audit keeps this pattern separate.
Remove campaign parameters from ordinary internal navigation and use clean destination URLs. Keep campaign tags on the external links where they serve their intended purpose. If you need to measure an internal action, review a suitable event instead. Check shared templates so that a repeated tagged link is corrected at its source.
/learn/internal-utm-links/
""")

copy_rows("""
onpage.anchors
Do your link labels explain the destination?
It finds vague link text and a larger set of links with no text.
The check reads link labels on pages intended for search. It skips page fragments, script links, email links and phone links. A plain Download label is allowed when it points to a recognised file or download route. Other labels are checked against a list of vague wording. Empty labels produce a finding only when there are more than 3 empty labels. A vague label can be reported whenever one is found. For example, exactly 3 empty labels stay within the empty-label count limit.
The check reads link destinations and their labels. It does not click them or assess the whole surrounding paragraph. Review each label in the interface where it appears.
Both vague and empty-label findings are low severity. A recognised download destination has a different purpose from an ordinary content link, which is why its short label is not automatically treated as vague.
Link labels help a reader decide whether a destination is useful before opening it. Counting labels without context cannot judge every design, but it can point to links that deserve a direct inspection.
Replace unclear labels with words describing the destination or action. Give icon-only controls an appropriate accessible name in the interface that owns them. Keep a concise Download label where the destination is genuinely a file. Review repeated card and menu templates if the same empty label appears across the site.
/how-to/fix-vague-and-empty-link-text/

onpage.description
Are your page descriptions missing or too long?
It checks whether descriptions exist and fit the engine's display-width range.
The check trims surrounding spaces from descriptions on pages intended for search. Empty descriptions produce a medium finding. Display width below 70 half-width character units produces a low short-description finding. Width above 165 half-width character units produces a low long-description finding. Widths at the limits pass. The engine counts wide and fullwidth Unicode characters twice and all other characters once. For example, a description with measured display width exactly 165 half-width character units stays within the long-description limit.
The check reads each page's meta description. It does not compare descriptions for duplication or ask a search service which snippet it displayed. Review those questions separately.
Missing descriptions are medium. Short and long ones are low. The thresholds are the engine's review limits, not a promise that a search service displays an exact number of characters or uses your description unchanged.
A description is a short account of a particular page. Presence and width checks can expose an empty or unwieldy summary, while the wording still needs a person to decide whether it accurately describes the destination.
Write a concise, specific summary of what the page gives a visitor. Remove template filler and keep the useful point early. Review pages with the shortest and longest values before applying a shared fix. Do not pad a clear summary merely to hit a number or promise content the page does not contain.
/how-to/write-meta-descriptions/

onpage.headings
Do your headings give the page a clear outline?
It checks missing main headings, distinct repeated main headings and gaps in the outline.
Pages with readable content are checked for a missing main heading or multiple different main headings. Capitalisation and extra spaces are ignored when comparing heading text. A page with at least 300 words and no deeper subheadings can produce a missing-subheading finding. Using a third-level heading with no second-level heading produces a skipped-level notice. The check reads the heading markup. For example, a 300-word article with only a main heading can reach the missing-subheading finding.
The check reads headings and word counts on pages with usable content. Repeated copies of the same main-heading text receive different treatment from different main headings. Inspect the outline before changing shared headers.
Missing main headings are medium, multiple distinct main headings and absent subheadings low, and the skipped-level case a notice. A clean result does not establish that each heading accurately names its section.
Heading levels describe relationships between parts of a page. Visual styling alone does not provide that structure, so the check looks at actual markup rather than assuming large text is a main heading.
Give the page a clear main subject and use subheadings to divide substantial content where helpful. Keep levels in a sensible order and style them through CSS. Review repeated header furniture before removing an intentional content heading. Check the resulting outline as well as the rendered appearance after updating a template.
/how-to/fix-heading-structure/

onpage.images
Do your images have the markup they need?
It checks missing alternative text, dimensions and lazy loading on image-heavy pages.
The test reads image resources on indexable pages and excludes detected beacons. An absent alt attribute with a nonempty image URL enters the missing-alt finding. Intentionally empty alt text is allowed by this presence test. At least 3 images without saved dimensions marks a page for the dimensions finding. A set of at least 8 images with none marked lazy produces the lazy-loading finding. These are separate conditions with separate affected page sets. For example, 3 images with no recorded dimensions are enough for the dimensions finding.
The check reads image addresses and markup. It does not look at the picture to identify its subject. Review the image's purpose before deciding what alternative text it needs.
Missing alt attributes and dimensions are medium severity. Lack of lazy loading on image-heavy pages is low. A present attribute does not prove that its text is useful or that an image's dimensions are correct.
Image markup can supply a text alternative and reserve space before loading. Those jobs differ from choosing when to fetch an image, which is why the code reports them separately rather than describing every image issue as a single optimisation.
Give meaningful images useful alternative text and decorative images the appropriate empty attribute. Set correct dimensions or a suitable reserved aspect ratio. Apply lazy loading to images that should wait, reviewing prominent content separately. Check a real page after editing shared image components so that the fix does not hide useful descriptions or delay an important image.
/how-to/fix-image-seo-problems/

onpage.lang
Does your page declare language and viewport?
It checks for a language value and a mobile viewport declaration.
The check builds separate lists of indexable pages with no saved language and with no saved viewport. A missing language produces a low-severity finding, while a missing viewport produces a high-severity finding. There is no sample-size or percentage cutoff in this test. A nonempty value passes the presence test even though its accuracy must be reviewed elsewhere.
The check reads language and viewport declarations on pages intended for search. A separate test compares the declared and detected languages. You need a browser to review the narrow-screen layout.
Results identify absence rather than validating every possible value. A viewport declaration can exist while the layout still has mobile problems, and a language attribute can exist while naming the wrong language.
Language and viewport declarations give readers' software basic information about the document. Presence is a useful first check, but the page still needs a real language review and a layout check in the environments it serves.
Set the document language to the page's actual main language. Add a suitable viewport declaration through the shared head template. Review the existing values before inserting duplicates. Test representative pages at a narrow viewport and read the language markup after the change rather than treating the presence check as a full mobile audit.
/how-to/check-mobile-seo-from-a-crawl/

onpage.title
Do your page titles fit and describe the page?
It checks missing titles, display width and excessive repeated keywords.
Pages with readable content are checked for missing titles, including an empty title element. Display width below 25 half-width character units is short and above 65 half-width character units is long. A title such as 'Home' falls below the short limit. The engine counts wide and fullwidth Unicode characters twice and all other characters once. For the keyword test, the engine removes recognised brand text, then keeps words of at least 4 letters. A word repeated at least 4 times is flagged. Repeated brand fragments at the end can also be removed before counting.
The check reads title text, whether the title element exists, and the business name. A separate check compares titles across pages. Review both results to give each page a clear, distinct name.
Missing titles are high severity, short and keyword-repeating titles medium, and long titles low. The width limits are review thresholds rather than a guarantee of how much a search result will display.
A title states what a page is about in a small space. Missing or repetitive wording gives little guidance, while a long value can bury the useful distinction between this page and another.
Write a specific title that names the page's job. Keep the main subject early and a useful brand suffix concise. Remove repeated keywords without erasing necessary meaning. Review the page itself before shortening a title so that the edit preserves the information a visitor needs to choose the right destination.
/how-to/write-title-tags-that-fit/

perf.cls_risk
Could your image markup cause layout shifts?
It identifies image patterns associated with shifting layout, rather than measuring a browser score.
A page needs at least 3 images with URLs, excluding detected tracking images. More than a 0.6 share must lack recorded dimensions. At least one image missing dimensions must be outside the shared template. An image counts as shared only with at least 5 successful pages and presence on at least a 0.6 share. These limits keep repeated logos alone from triggering the same risk on every page. For example, a missing-dimensions share of exactly 0.6 does not exceed the risk threshold.
The check reads image markup from successful pages. It does not measure movement in a browser. Use a browser measurement when you need an actual layout-shift score.
The finding is medium severity. It reports a markup risk, not a measured Core Web Vitals result or a prediction of the exact amount a page moves during loading.
Dimensions can reserve space before an image arrives. The check looks for missing space in image markup and accounts for shared template images. Use a browser to see the movement a visitor actually experiences.
Set correct image dimensions or reserve the intended aspect ratio in the relevant component. Review content images as well as repeated logos. Test the page visually while images load and use suitable browser measurements for an actual layout-shift result. Keep the source fix tied to the missing space rather than claiming a numerical score improvement from this check alone.
/how-to/fix-layout-shift/

perf.compression
Are your HTML responses compressed and cacheable?
It checks response headers for missing compression and caching settings.
A successful page with more than 20000 HTML bytes and no content-encoding header can enter the compression finding. Any nonempty separate compression result suppresses that finding. This accounts for servers that use compression only when another encoding is requested. Pages missing cache-control, etag and last-modified are reported when they exceed a 0.5 share of successful pages. These header tests check presence. For example, a response of exactly 20000 HTML bytes stays outside the compression size test.
The check reads response headers, HTML size and the separate compression test. It cannot estimate savings from those fields alone. Review the response your server sends for each requested encoding.
Missing compression is high severity. Absent cache headers across the larger share produce low severity. A present cache header does not establish that its policy is useful, and a separate encoding probe can change what an apparently uncompressed response means.
Compression and caching answer different delivery questions. The probe guard matters because a server can support an encoding that the initial request did not obtain, making a direct absence claim too broad.
Inspect the response and the requested encoding. Enable suitable HTML compression where needed. Set caching rules for the content's update needs. Keep private or changing responses safe when editing shared rules. Request the same URL again and review the new headers.
/how-to/fix-compression-and-caching/

perf.modern_images
Are image-heavy pages using older formats?
It counts pages with several JPEG or PNG images lacking a modern source alternative.
The test reads successful pages and selects image resources whose URL path ends in JPEG or PNG after the query string is removed. A saved modern-source flag excludes an image from the legacy set. At least 4 remaining images on a page are needed for that page to enter the finding. The count is then totalled across qualifying pages, rather than reporting every isolated older-format image. For example, 4 JPEG images with no recognised newer-format alternative can qualify a page for review.
The check reads image addresses and whether a newer-format alternative was found. It does not measure visual quality, transfer size or the browser's actual choice. Review the delivered picture before converting files.
The finding is low severity. A newer format alternative can satisfy the check while the delivered image still needs a quality or size review, and a valid older-format file is not automatically broken.
An image-heavy page offers a concrete place to inspect format choices. The check uses that concentration as a review cue, while leaving the actual tradeoff between quality, compatibility and file size to the owner.
Compare suitable modern encodings with the current images using the same visual content. Provide source alternatives where needed and keep a working fallback for your audience. Check the actual chosen source in a browser. Avoid replacing images blindly when a conversion loses useful detail or does not reduce the delivered file.
/how-to/serve-images-in-modern-formats/

perf.page_weight
Is your HTML document unusually large?
It compares decompressed HTML bytes with the engine's document-size cutoffs.
Successful pages above 400000 HTML bytes join the larger-document group. Pages above 150000 HTML bytes and at or below 400000 HTML bytes join the moderate group. Larger documents are reported first. If none exist, a moderate group above a 0.5 share of successful pages can produce the lower-severity finding. This measures the HTML document alone. Images and separate files need their own size measurements. For example, a document of exactly 400000 HTML bytes stays in the moderate size group.
The check reads HTML sizes from successful responses. A capped response gives only the amount retained. Keep the size unit and any read limit beside the result.
The larger-document finding is medium severity. Widespread moderate documents produce low severity. Browser loading time, script execution and page painting need separate measurements.
A large document can contain repeated markup or extensive inline data. Its byte count identifies something concrete to inspect, while a separate resource review is needed to understand the weight of the whole page.
Inspect the largest served documents and identify what fills them. Remove unused inline data and repeated markup, or split long listings when that suits the content. Move reusable assets only where the resulting requests and caching make sense. Compare decompressed HTML after the change and preserve the useful content the page was meant to deliver.
/learn/page-weight/

perf.redirect_cost
Do many crawled addresses need a redirect?
It checks how much of the crawled URL set travelled through a redirect.
The check selects crawled pages with a nonempty saved redirect chain. Their count must exceed the larger of 5 pages or a 0.25 share of all crawled pages before the finding appears. The comparison is strict, so equality does not trigger it. This check uses redirect volume as the measured signal. It does not add network timings to calculate a total delay. For example, exactly 5 redirected pages cannot exceed a threshold that is at least 5 pages.
The full crawl's request history supplies the counts, including pages outside the successful content set. It is distinct from the check for a particular loop or a chain containing several hops.
The finding is low severity. A redirected address can be a correct legacy route, and a large share can reflect how the crawl was seeded rather than proof that every internal link is wrong.
Many redirects can indicate that the site still advertises old addresses. The useful follow-up is to identify the sources of those requests, rather than removing valid redirects that protect visitors arriving through older links.
Update internal links and sitemaps to the final intended addresses where you control them. Keep redirects that support old external links. Check for loops and unnecessary intermediate moves. Measure response times separately when you need to quantify delay.
/how-to/fix-redirect-problems/

perf.render_blocking
Does your page load many blocking files?
It counts resources marked as blocking the initial render.
Successful pages are scanned for resources whose saved render-blocking flag is true. A page enters the finding when it has at least 5 such resources. Qualifying pages are sorted by count, and the report gives the worst count with a limited URL sample. It does not time each request or decide that every script and stylesheet should be delayed regardless of its role. For example, a page with exactly 5 blocking resources qualifies for this finding.
The check uses the crawler's recorded blocking-resource types on successful pages. It cannot measure every file's effect on display time. Review which files the first view needs before delaying them.
The finding is medium severity. A blocking resource can be necessary for initial display, so the count points to a review rather than proving that every listed file is wasteful.
Resources needed before a page can paint occupy a different place in loading from optional enhancements. The check makes that distinction visible through saved flags, while the correct loading order still depends on what the page needs to show.
Inspect the files and identify which are required for the first useful view. Defer scripts and delay nonessential styles only where the page continues to work correctly. Combine files when that is useful, then test loading and interaction. Measure the browser result separately instead of translating a lower count into an invented time saving.
/how-to/fix-render-blocking-resources/

perf.ttfb
Is your server slow to start responding?
It compares first-response samples, repeat requests and slower-page outliers.
The check needs at least 3 positive response-time samples from successful pages. It compares the median with 0.8 seconds and 1.8 seconds. Above 1.8 seconds is medium severity when the repeat-request median is at most 0.8 seconds. Otherwise it is high. A median above 0.8 seconds and at most 1.8 seconds produces medium severity. At a median of 0.8 seconds or less, pages above 1.8 seconds can produce a low outlier finding when their share is below 0.3. For example, a slow first request followed by a repeat median of 0.8 seconds meets the warm-cache limit.
The check uses recorded first-response times and any positive repeat-request times. It compares the sampled requests. Review their timing and cache state before drawing conclusions about a visitor's experience.
Severity depends on the measured pattern. A fast repeat can point to a cache effect. Consistently slow medians call for a different review. Keep the first and repeat measurements together when reading the result.
The first byte is an early part of delivering a page. Comparing cold and repeated requests can help distinguish a cache effect from a broader response problem, without claiming that the test observed a particular visitor's connection.
Inspect slow templates and compare repeat requests before choosing a fix. Review server work, cache setup and cache expiry where the measurements point to them. Measure representative URLs again after changes. Check browser rendering and resource loading separately when reviewing the complete page experience.
/how-to/reduce-server-response-time/
""")

copy_rows("""
schema.incomplete
Does your structured data have useful values?
It checks required properties by type, including empty fields and unresolved references.
The check walks supported types on indexable pages and compares each node with the source's required-property table. Same-page identifier definitions are resolved before testing fields. Empty strings, lists and objects do not count as useful values. Case errors, unresolved references, review snippets, service offers and organisation-shaped product blocks affect the explanation or required set. Findings are grouped by type and missing-field combination rather than treating every node as a separate page.
The check reads structured objects on each page intended for search. Empty fields and references to missing objects can leave gaps. Confirm the type and the subject before filling them.
Incomplete-type findings are medium severity. A required-property table is the engine's coverage, not an exhaustive validation of every schema vocabulary or search feature. Correctly filled fields can still contain inaccurate claims.
A key can be present while holding no usable value. References can also look complete while naming a definition absent from the document, so the check inspects more than whether the expected words occur in source.
Read the reported node and the type it claims. Fill applicable fields with real values and define referenced objects on the page where needed. Correct property casing and remove misleading types instead of inventing data to complete them. Use the guide to review empty fields before assuming the template omitted a key entirely.
/how-to/when-a-field-is-there-and-still-missing/

schema.invalid
Can software read your JSON-LD correctly?
It reports parsing errors, CDATA wrappers and unfilled template values.
The check groups recorded JSON-LD errors from successful pages. It explains the most common error and a matching repair. CDATA wrappers are reported separately. Readable blocks are searched for unfilled template tags, including short identity fields. That identity-field test has a 300-character limit. Longer strings with braces are left out of that short-field test. For example, a short identity field containing an unfilled template tag can be checked up to the 300-character limit.
The check reads JSON-LD blocks, recorded errors and wrapper detections. It does not repair JSON or verify the truth of a readable value. Review the declared facts after fixing syntax.
Parsing failures are high severity. CDATA wrappers and unfilled template tags are medium. A block can be valid JSON yet still carry a literal template value, which is why the check includes a separate case after parsing.
Structured content must be readable before its fields can be interpreted. A saved parser error gives a concrete starting point for repair, while template placeholders need a different fix in the code that supplied the value.
Use the reported error and location to inspect the original block. Fix quoting, commas or leftover wrappers as appropriate, and ensure templates fill values before serving the page. Generate structured JSON through a serializer where possible. Parse the final served block again and check its factual content after syntax is repaired.
/how-to/json-ld-parser-errors/

schema.mismatch
Does rating markup match what readers can see?
It checks whether declared ratings have visible reviews or rating text.
The check reads aggregate-rating markup on pages intended for search. It leaves out recognised off-page rating arrangements for supported software types. Page text is searched for stored rating words. If none match, saved browser output is checked when available. Without that output, the result stays unknown. A loaded page still lacking the wording can produce the stronger finding.
The check reads rating objects, visible prose and any saved browser output. It compares the declared rating with words it can find on the page. You need to confirm that they describe the same subject.
Confirmed nonvisible ratings are high severity. A visibility result that cannot be established is a notice. The distinction matters on pages where scripts add reviews that were absent from the initial document.
Declared ratings and visible reviews should describe the same thing. The check uses browser output when available to review a possible mismatch. Without that output, it leaves the result unknown.
Confirm the subject and values of each declared rating. Compare them with the public page and any recognised off-page rating arrangement. Show the supporting review or remove an unsupported declaration. When browser output was unavailable, inspect the loaded page before deciding whether the rating is hidden.
/how-to/fix-structured-data-that-does-not-match-the-page/

schema.missing
Does your site serve structured data?
It checks for schema coverage, business identity and breadcrumb markup.
Pages intended for search are checked for JSON-LD, microdata and recognised script-built types. No detected markup produces high severity. Missing identity and identity built only by scripts get different explanations. At least 5 indexable pages without breadcrumb markup produce a low finding. Coverage above zero but below 0.4 produces another low finding. With no indexable pages, coverage stays unknown. For example, markup coverage of exactly 0.4 stays outside the partial-coverage finding.
The check reads structured types in server responses and types known to be built by scripts. Objects it cannot read remain unknown. Review coverage before treating an apparent gap as a reason to add duplicate markup.
No schema and absent identity can be high, script-only identity medium, and breadcrumb or coverage gaps low. Presence of a type is not proof that all required properties exist or that a particular rich result is available.
Coverage and correctness are separate questions. Knowing where markup appears helps locate a template gap, while the type and completeness checks still need to establish whether the declarations fit the content.
Choose markup that accurately describes the business and page. Add it to the appropriate shared template and serve important identity in readable HTML where practical. Keep breadcrumb declarations aligned with the visible route. Check several page types after editing, then validate values and ownership instead of stopping at a presence result.
/how-to/fix-structured-data-errors/

schema.opportunity
Do your real answers have FAQ markup?
It finds pages with several qualifying question headings and no FAQPage declaration.
Pages already declaring FAQPage are excluded. A remaining page needs at least 3 headings recognised as questions. Heading text and linked destinations are checked. A question that sends readers elsewhere may be navigation. Review the local answer before adding markup. The count does not verify facts or promise a search display feature. For example, 3 accepted question headings can qualify a page that has no FAQPage declaration.
The check reads headings, question links and structured types. It looks for a page's own questions and answers. A complete factual and editorial review still needs a person.
The opportunity finding is low severity. It describes possible markup for existing answers rather than a requirement to manufacture questions or a claim that adding the type will produce a rich result.
Structured declarations should follow the content the reader can actually use. Counting locally answered questions protects that relationship and keeps an index of links from being described as a complete answer page.
Review the qualifying questions and confirm that the page provides their answers. Add matching question-and-answer markup only for that content. Keep the visible wording and declared answers aligned when editing. Do not add filler questions simply to reach the count or promise a search appearance that this test does not measure.
/how-to/fix-structured-data-errors/

schema.price
Does your marked-up price appear on the page?
It compares nonzero declared price amounts with visible and saved rendered text.
The check reads price, low-price and high-price fields from supported offer and price objects. Zero-only declarations are excluded. A matching amount in the page text can pass the comparison. Otherwise saved browser text is checked after removing tags, scripts and styles. Without browser output, the result stays unknown. No matching amount after that comparison produces a high finding.
The check reads price declarations, page text and saved browser output. It recognises different punctuation in amounts. You still need to confirm the currency, billing period and offer. It performs no currency conversion.
Confirmed absent price text is high severity. Unconfirmable visibility is a notice. Review the whole offer after finding a matching amount. Check currency, availability and any terms attached to the price.
Markup prices are claims about an offer. Comparing them with readable content can expose stale or hidden values, while a person still needs to check that the amount and the offer belong together.
Compare the declared amount with the actual offer shown to visitors. Update stale values and show relevant prices clearly, or remove declarations that no longer describe the page. Check script-rendered offers before treating them as absent. Review currency and pricing conditions separately because a shared number alone cannot validate them.
/how-to/fix-structured-data-that-does-not-match-the-page/

security.headers
Does your secure site send baseline headers?
It checks selected response headers and recognises some equivalent protections.
The check runs on HTTPS sites. Missing strict-transport-security produces a low finding unless the final host's suffix is in the source's preload list, in which case the code reports a pass for that case. It also checks x-content-type-options and referrer-policy. A nonempty meta referrer declaration in the first 25 successful pages can satisfy the referrer-policy presence test. Missing baseline headers produce a notice. For example, a nonempty meta referrer value in the first 25 successful pages can satisfy that header-presence test.
The check reads saved security headers, the final host and sampled meta declarations. It checks presence and recognised alternatives. Review each value to see whether the policy suits the site.
HSTS absence is low, recognised suffix coverage a pass and missing baseline headers a notice. The report is a focused configuration check, not a complete security assessment of the application.
Equivalent protections can live in different places. Recognising a browser-enforced suffix or an HTML referrer declaration avoids asking for a duplicate solely because a particular response-header key was absent.
Inspect the live response configuration through your normal server tools. Add appropriate baseline values and review HSTS carefully for all hosts it would cover. Keep a valid meta referrer policy where that is the intended configuration. Test representative responses after editing shared server rules, including pages served through another proxy layer.
/how-to/fix-missing-security-headers/

security.https
Does your site serve secure working responses?
It checks HTTPS, the plain-HTTP route and certificate validity.
A site not served over HTTPS produces a critical finding and ends this check. Otherwise the plain-HTTP probe is reviewed unless skipped by policy. Refusals, zero statuses and server errors produce uncertainty rather than a definite redirect fault. Other client errors and nonredirecting responses have separate cases. Certificate validity is checked separately. Expiry below 21 days is reported, with high severity below 7 days and medium otherwise. For example, a certificate with exactly 7 days left stays in the medium expiry group.
Site-level scheme and saved redirect-probe results are combined with a certificate check against the final origin. The final origin is used for the certificate host, avoiding an assumption that the starting address remained the destination.
Missing HTTPS and invalid certificates are critical. Redirect problems can be high or medium, unknown results notices, and expiry high or medium. A certificate test that cannot run is not silently treated as valid or invalid.
Secure delivery and a consistent plain-HTTP route are different configuration tasks. Keeping uncertainty separate helps avoid changing a correct redirect because a network refusal prevented this particular audit from observing it.
Use a valid certificate for the final host and review its renewal setup. Redirect the intended plain-HTTP routes to their secure equivalents where appropriate. Investigate probe failures before declaring the route broken. Test the affected host and path after changes, checking both the response destination and certificate rather than only the browser's final appearance.
/how-to/redirect-http-to-https/

security.mixed_content
Does your HTTPS page load insecure resources?
It separates insecure active resources from pages with insecure images only.
The check runs on HTTPS sites. It scans successful pages for HTTP images, scripts, stylesheets and frames. Insecure scripts, styles or frames produce high severity. Image-only cases produce medium severity. A page counted in the active group is counted there once, even if it also has an insecure image.
The check reads resource addresses and types from successful pages. It does not test every feature in a browser. Review the actual file response before changing its URL.
Active mixed content is high severity and image-only mixed content medium. The report describes the resource addresses observed in markup rather than claiming to have measured every resulting browser error.
A secure document can refer to resources through a different scheme. Separating executable or embedded content from images keeps the report tied to the types of resources that actually produced the finding.
Replace insecure resource addresses with working secure equivalents and verify that the resource exists there. Update shared templates or stored content that supplies the old addresses. Remove an obsolete resource when it has no useful role. Check the browser for loading errors after editing, since changing the scheme text alone does not guarantee that the remote server supports it.
/how-to/redirect-http-to-https/

social.favicon
Can your site's favicon be found?
It reports a confirmed missing favicon from the saved site probe.
The check needs a final or starting origin. It emits a low-severity finding only when the saved icon result is false and the saved unknown flag is also false. An unknown result is therefore not turned into a missing-icon claim. Browser tabs, icon formats and article text are outside this missing-file test.
The check uses the saved icon request result. It cannot judge the artwork, branding or every cached browser tab. Review the served icon yourself.
A confirmed missing favicon is low severity. No finding under an unknown result does not prove that the icon exists or that every browser will display the intended artwork.
The icon is a small part of the site's public identity. A presence probe can identify a delivery problem, while appearance and suitability still need a visual check in the places the icon is meant to be used.
Check the icon declaration and the file it names. Serve a valid icon from a working address and keep the declaration in the shared head template. Review fallback paths where relevant. Request the file again after publishing through your normal workflow, then inspect its appearance separately from the probe's limited existence result.
/how-to/fix-favicon-not-showing-in-search/

social.open_graph
Will shared links have useful preview metadata?
It checks Open Graph identity, images, descriptions and measured image failures.
Pages with readable content are checked for Open Graph values. Missing tags and tags without a title receive different explanations. A missing primary image is separate from an image supplied only through an image-URL subproperty. Measured image responses with HTTP status 400 or above are treated as dead after refusals are excluded. Missing descriptions are reported separately when the whole set of tags has not already been reported absent. For example, a measured image response with HTTP status 400 can be treated as dead after refusal handling.
The check reads Open Graph fields and saved image responses. A refused or unmeasured image stays uncertain. Check the served image before replacing its declaration.
Most missing fields are low severity, dead images medium and missing descriptions notices. Valid-looking metadata does not prove that every sharing service uses it or that a cached preview has refreshed.
A shared URL can carry its own title, image and description. Checking those fields separately helps locate whether an incomplete preview comes from missing metadata or a measured problem fetching the named picture.
Add accurate preview fields through the appropriate page template. Use a working image URL and confirm that the image is the one you intend to share. Keep page-specific titles and descriptions where useful. Review a sharing service's cached preview separately after fixing the source, since this check reads the page and saved response rather than clearing external caches.
/how-to/fix-missing-open-graph-tags/

social.twitter
Does your site declare a Twitter card type?
It checks widespread missing card-type declarations on sites with Open Graph titles.
The check builds a missing set from indexable pages without twitter:card. It proceeds only when some indexable page has an Open Graph title and the missing set is greater than a 0.5 share. Pages carrying other Twitter fields are distinguished from pages with no such markup, so the wording can identify a missing card type rather than falsely saying all card tags are absent. For example, a missing-card share of exactly 0.5 does not exceed the finding threshold.
The check reads card metadata and Open Graph titles. It does not ask a social platform to refresh its cache. Review the live page tags before testing an external preview.
The finding is a notice. A nonempty card-type value satisfies this presence condition without establishing that every other preview field is valid or that a particular platform will display the card.
Related metadata can be partly present while a type declaration is missing. Naming the actual gap gives a clearer template fix than replacing the whole preview setup based on an overly broad absence claim.
Review the intended preview style and add an appropriate card-type declaration where missing. Keep its title, description and image consistent with the page. Inspect existing fields before inserting duplicates through another plugin or template. Test the source output and any platform preview separately, recognising that external caches can preserve earlier metadata.
/how-to/fix-missing-open-graph-tags/
""")


REVIEW = dict(line.split("|", 1) for line in """
ai.citable_facts|Compare a matched passage with the record behind it. A price without context and a dated measurement make different statements, even when both contain digits. Check what the attribution is based on. Limit the claim to what the record supports. Put the source beside it so readers can check it.
ai.crawler_access|Start with the crawler named in the finding and follow the policy that applies to it. A broad wildcard restriction can be deliberate, just as a named allow can be deliberate. Check which choice you intended before editing either group. Keep training preferences separate from search access in your notes, so that a later template update does not silently combine policies you wanted to manage independently.
ai.dead_crawler_directive|Compare the obsolete group with its replacement before deleting either. Copying a restriction into a new group can be unnecessary when the same rule already applies, while removing an old label alone cannot restore a restriction that never reached the live name. Keep a short record of the intended policy and verify the effective rules after editing, including the wildcard restrictions that may already cover the path.
ai.edge_access|Match the recorded request with the server rule that answered it. The ordinary request and search-control request help explain whether the response is specific to an AI name, broader crawler handling or the audit's network location. Keep the response status and challenge context together when reviewing logs. Changing a robots rule cannot by itself explain a firewall response, so identify the layer that actually produced the refusal.
ai.entity|Inspect the identity object as a statement about the owner. A useful profile link names a particular account, while a general platform address merely names a service. Check unfamiliar hosts yourself before replacing a valid profile link. Keep linked accounts aligned with the public business name. Remove references that identify an article's subject as the publisher.
ai.extractability|Read a qualifying heading together with the passage that follows it. A question mark can satisfy a pattern while leaving a visitor without an answer. Keep the heading specific enough to describe that passage, and put the main answer where it can be read without hunting through unrelated sections. Shared questions about the business can remain useful navigation even when this content-structure test deliberately leaves them out.
ai.freshness_signal|Compare the date with the item it describes. A website launch, business founding and article update are different events, even when their values use the same date format. Keep the content date attached to its own content node and avoid borrowing a shared template date. After a genuine update, review the visible date and structured date together so that readers and markup receive the same account.
ai.llms_txt|Review a found file as a document in its own right. Presence does not establish that its links still work or that its description matches the site. If a request was refused, preserve that uncertainty until you can inspect the actual response. Keep any decision to publish the file tied to the information you want to provide, rather than treating an optional notice as a failed content page.
ai.rendering|Compare the same address before and after scripts run, using the main text as your reference. A loading screen may contain readable HTML while leaving the article unavailable. Keep the original server response during review. Test each shared page type that delivers its main content differently.
ai.unmeasurable_optout|Keep an account-setting review separate from a public request test. A person with access to the provider can confirm a private choice that a crawler cannot observe. Record who checked that choice and what policy it represents without inventing an outside measurement. Revisit the setting through the same account when policy changes, while using public responses only to confirm the access behaviour they can actually expose.
brand.logo|Inspect the name a linked logo supplies when its picture is unavailable. A meaningful text identity can serve the same naming purpose as an image, while a generic logo label may add little. Keep the business name clear without repeating surrounding words unnecessarily. Check the component across templates because a header can differ between the homepage, articles and other sections even when the graphic looks similar.
brand.name_consistency|Compare declarations by role before deciding that different spellings conflict. A legal entity, trading name and language-specific name may all have legitimate places. Keep obsolete template values separate from those valid distinctions in your review notes. Update the source component that owns each stale value, then inspect its output again, rather than making unrelated text changes wherever the business happens to be mentioned in an article.
brand.positioning|Read the descriptions as a group, then return to the purpose of each page. Shared vocabulary can be natural when the pages discuss the same offer. It can also arise from copied summaries. Keep the common subject clear while preserving the detail that distinguishes an individual service or article. Treat the vocabulary result as an editorial prompt, and resolve contradictory statements before trying to increase repeated terms.
brand.social_consistency|Compare the actual account addresses as well as their platforms. A platform match can hide a stale account or another organisation's profile, while a missing platform can reveal a declaration gap. Keep only accounts that identify the business in its own markup. Review repeated footer links and served identity nodes together, then inspect any script-built declarations separately before assuming that an initial-source omission means the account was never declared.
brand.visual_consistency|Compare the reported style values with your actual design choices. Slightly different colours may be accidental copies or intentional states, and separate fonts may belong to distinct content roles. Keep a value when its purpose is clear. Where duplication was accidental, change the shared declaration and inspect representative content afterwards, including text placed over backgrounds that used the previous colour or typeface choice.
brand.voice_consistency|Read the short-sentence and long-sentence pages in their intended context. Instructions, contact details and an explanatory article can have different rhythms without sounding like unrelated businesses. Keep changes focused on passages that are difficult to follow. A shared editing approach can improve clarity, but making every page's arithmetic match would remove useful variety without establishing a consistent tone or a clearer account of the service.
content.ai_slop|Inspect what the phrase is doing in the passage. A quoted example, a reader's comment and the business's own claim need different editorial treatment. Keep useful information when removing stock wording, and replace vague promises with details you can stand behind. Review the surrounding paragraph after editing so the result reads naturally, rather than substituting a different empty phrase that happens to evade the stored list.
content.competing_pages|Compare the jobs performed by grouped pages before merging anything. Similar titles may hide genuinely different products, audiences or questions, while different titles may still lead to almost the same answer. Keep a useful distinction visible in both the promise and the body. If consolidation is appropriate, plan the surviving address and links carefully instead of deleting pages based solely on a title-word relationship.
content.dates|Inspect an affected article's opening and its structured dates together. A visible publication date can already tell readers when the article was written. Keep publication and update dates attached to the correct article. Use the date of the actual work when adding or correcting markup.
content.eeat|Review the contact route as a visitor would use it. A form that looks present can still need a completion test, while an about page can exist without explaining who publishes the material. Keep real identities and responsibilities clear. Add authorship only when it truthfully describes the work, and avoid turning a presence check into an unsupported assertion that every author has expertise the business cannot verify.
content.js_rendering|Inspect the main content rather than the presence of script tags. Many pages use scripts while still serving readable text, so scripts alone are not the reported defect. Keep the original response and loaded view side by side during review. A rendering change should preserve the same useful information and working interactions, then make that information available earlier in the response path instead of merely removing visible features.
content.lang_mismatch|Ask a fluent reader to review the passage used to detect the language. A list of names or a bilingual passage can be harder to classify than ordinary prose. Keep the declaration tied to the document's main language. Review each translation and retain valid regional forms.
content.language_scope|Separate a withheld judgement from a clean result in your review notes. A page can have well-formed markup while its prose remains outside the tool's language coverage. Keep a fluent person's review attached to the copy decisions that need it. Changing an attribute to a supported language without changing the actual language would misdescribe the page and would not supply the missing understanding this notice identifies.
content.placeholder|Check the field where a marker appeared before changing the page's main text. An unfinished social description and an unfinished paragraph can come from different templates. Keep legitimate examples of filler wording when they are clearly part of an explanation. Repair the source of actual placeholder values and inspect the final served output, since editing a visible paragraph alone may leave the same unfinished text in metadata.
content.readability|Read a dense passage for the ideas it asks the reader to hold together. A list, a quotation and a long explanation can affect sentence parsing differently. Keep necessary technical meaning while separating unrelated clauses. After editing, read the whole paragraph again rather than checking the average alone. A shorter sentence can still be confusing if its subject, action or relationship to the previous sentence is unclear.
content.thin|Compare the reported word count with what the page is meant to do. A short utility response and a useful service explanation have different jobs. Keep an archive useful through its listings instead of filling it with unrelated prose. If content appears only after loading, address that delivery issue before commissioning replacement text. Review usefulness directly, because crossing a word-count cutoff does not establish that a question was answered.
content.topic_gaps|Read the suggested query as a real question and check where the site answers it. A topic can be explained in the body even when its wording is absent from a heading. Base the content decision on the business and the reader's question. Check demand separately before assigning an audience size to a saved suggestion.
cvr.dead_contact|Inspect both the visible address and the hidden mail destination. A working website domain can have a separate mail configuration, and a correctly written link cannot repair that configuration by itself. Keep domain-level delivery details distinct from a mailbox test. When another provider manages enquiries, confirm the intended destination with its owner before replacing a published address or changing records that serve other business mail.
cvr.form_friction|Follow the enquiry route through to its intended destination, including any booking or messaging service outside the page. A route can be useful without an embedded form. Keep each requested field tied to information needed at that stage. When reviewing a long form, distinguish essential service details from questions that could wait for a reply, then check that the shorter route still supports the business's real workflow.
cvr.funnel|Compare the apparent content groups with actual customer questions. A path can look educational while holding little help, and a useful comparison may live outside the recognised path list. Keep the decision tied to what the business can explain accurately. Before creating a section, identify a missing answer and the page that should provide it, rather than assuming a larger page inventory is itself a better buying experience.
cvr.message_match|Read the title without the headline, then read the headline without the title. Each should make a truthful promise about the content that follows. Keep meaningful differences in phrasing when they help a reader. If a repeated business heading displaced the specific subject, inspect the shared template before rewriting good content, and confirm that the actual page heading remains clear in the served outline after the change.
cvr.no_cta|Follow the next step named by the action. A clear label is useful only when the destination carries out the promise, and an enquiry form may already provide an appropriate action. Keep the page's purpose in mind when choosing what to emphasise. Avoid adding several competing buttons simply to increase detected actions. Review whether a new visitor can understand the route and complete it without guessing. After a trial of the route, record where a visitor lands and whether that destination still matches the action label.
cvr.pricing|Inspect the cost explanation in the context of the service. A quote request can be appropriate for variable work, while a fixed offer may need a clear amount and conditions. Keep the explanation honest about what is known. Verify any published amount against the business's current source before editing it, and make sure the route to further pricing information is easy to understand from the relevant buying page.
cvr.social_proof|Review each proof statement for its basis and relevance to the offer beside it. A recognised review word may describe the topic of a discussion. Keep the source and permission record for published reviews. State qualifications accurately and confirm their current scope. Check that approved examples still apply when an offer changes.
cvr.unusable_phone|Compare the display label with the decoded destination, including any extension or context parameter. A number can look normal on the page while its target still contains template markup. Keep call and text routes appropriate to the service offered. Review international context for the audience that uses the page, and validate the link format without placing automated calls or assuming that format validation proves a working line.
cvr.value_prop|Read the opening passage as someone unfamiliar with the business. A company name or a decorative slogan may be clear to the owner while leaving the offer unstated for a visitor. Keep the useful claim concrete and accurate. Review customer-directed wording for meaning rather than pronoun count, because inserting a customer word into an unclear headline cannot by itself explain what is provided or who the page serves.
index.broken|Trace a reported destination back to the link or discovery source that supplied it. A real page returning an access refusal needs a different response from an address containing pasted prose. Keep the saved error category alongside the URL during review. For intermittent failures, compare server logs and a later request before removing content, while correcting a clearly malformed internal link at the template or page that published it.
index.byte_cap|Inspect the actual document order around the recorded cutoff. A tag can appear visually near the top of a page while its source arrives much later, and separate resource sizes do not describe the HTML budget. Keep the byte unit and fixed header allowance visible in your notes. After reducing markup, compare the new offsets with the saved ones instead of assuming that a smaller file moved every important tag equally.
index.canonical|Compare the canonical target with the intended relationship between the pages. An alias, a syndicated article and an accidental off-site template value need different decisions. Keep details of redirects and target directives together. When the destination was not crawled, inspect it before assigning a status or indexing judgement. Update shared host settings carefully so that a correction on ordinary pages does not erase an intentional partner relationship.
index.canonical_conflict|Inspect the complete response, including headers, before editing the document template. A proxy or server can add a declaration independently of the page generator. Keep both target values in the review until the intended owner of the policy is clear. After changing the responsible layer, request the page again and compare the resulting header with the served document, rather than relying on a local source file alone.
index.depth|Trace a route from a known entry page to the affected content. Sitemap discovery alone does not show that route, and a partial crawl can miss a valid source link. Keep the coverage warning attached to any structural conclusion. Add links where they help visitors follow the subject, then check the graph again, instead of putting unrelated pages into a menu simply to lower a reported click count.
index.duplicate_content|Compare the saved text with the content expected at each address. Identical responses across unrelated sections can indicate a shared substitute page rather than duplicated editorial work. Keep that delivery case separate from genuine alternate URLs. When titles alone repeat, inspect the page purposes before rewriting them, and preserve a real canonical agreement that already describes duplicate content instead of creating contradictory address policies during cleanup.
index.meta_refresh|Review the redirect mechanism and destination together. A successful response followed by a document instruction can be intentional, but it is different from the server moving the request immediately. Keep a deliberate waiting message separate from a permanent address move. After replacing a browser redirect, inspect the served HTML as well as response headers so that an old instruction does not remain and send visitors through another move.
index.noindex|Check the page's intended audience before removing an exclusion. A confirmation or account page may be public enough to crawl while still being deliberately absent from search. Keep the homepage case separate from those utility roles. Where a page should be indexed, inspect both the document and response-header directives, then verify the served result so that a hidden header does not preserve the exclusion after a template edit.
index.redirects|Follow the saved chain in order and identify who controls each rule. A correct legacy redirect can still be linked unnecessarily from a current template. Keep working old-address support while updating sources you control. For a loop, compare host and scheme rules as well as paths, since individually plausible moves can send a request back to an earlier address when applied together by different layers.
index.robots_blocks_all|Read the applicable crawler group and the wildcard rules alongside the saved response status. A server unable to deliver the policy is not the same as an owner deliberately excluding a crawler. Keep that distinction when discussing the finding. Repair delivery before interpreting missing access data, and check the policy after editing syntax so that a cleaner file still expresses the access choice the business intended.
index.sitemap|Compare entries with the final addresses that actually serve public content. A redirecting sitemap URL and a temporarily refused page are different cases, even when neither supplied a fresh body to this crawl. Keep entries until their role is understood. Repair repeated malformed paths in the generator, and review omitted content against the measured crawl rather than assuming the sitemap must contain every address the application can produce.
index.soft_404|Inspect a genuinely nonexistent address without treating its visual design as the response status. A helpful error page can still return the wrong success response. Keep the missing-page route separate from valid content routes when changing the application. After repair, confirm that a real page still succeeds and the nonexistent address still provides useful navigation while returning the intended error, rather than replacing every unknown path with the homepage.
index.soft_404_pages|Read the short page and the source link together. A real error response disguised as success differs from an article explaining an error message. Keep the page's purpose in view before deleting it. If the content should exist, restore it. For an obsolete address, correct the response and the links that point there. Retest the served document so that an old substitute body does not remain behind a successful status.
index.url_hygiene|Inspect the role of each parameter or path segment before simplifying it. A useful filter and a session identifier do not make the same public address statement. Keep stable content identifiers while removing values that should not persist in public links. Plan redirects for changed addresses where appropriate and review generated navigation, because editing a displayed URL cannot correct the template that keeps publishing the old form.
index.www|Test the alternate host on an inner path as well as the root. A homepage move alone may not explain how the rest of the site behaves. Keep the intended path and query through the redirect where they identify real content. Inspect how the alternate host handles a meaningful inner destination before deciding that its root response represents the whole route. Align canonical and sitemap addresses with the chosen host, while preserving valid external links through a working alternate-host route instead of making those older links fail.
intl.hreflang_codes|Compare the reported code with the language and region of the target page. A familiar-looking region suffix can still be a known typo, while an unfamiliar registered value may simply exceed the audit's table. Keep uncertainty separate from a confirmed format error. After correcting declarations, review the whole alternate group so that a local spelling edit does not leave related pages using inconsistent codes for the same audience.
intl.hreflang_return|Inspect both pages in a reported pair. A declaration on the source does not establish what the target publishes, and a target outside the successful crawl remains outside this comparison. Keep the intended alternate group consistent when updating templates. After adding a return relationship, check the current page's self-reference and the final target addresses too, rather than treating reciprocity as proof that every part of the group is correct. Record which language variants belong together before editing templates, and compare the served declarations again after the shared change is built.
intl.hreflang_self|Compare the self-reference with the page's final public address. A nearby alias may describe the same content to a person while still being a different target string to this test. Keep the declared language accurate and use a consistent alternate group. Review the resulting markup on the current page and its alternatives after a template change, since adding a self-link alone cannot establish that the other pages return the relationship.
intl.hreflang_targets|Inspect the measured destination and its redirect history before replacing an alternate. A refusal leaves the target unchecked. Keep confirmed errors and noindex directives in the change list with their recorded statuses. Use the intended final address. Check its language and return links after repairing the response.
links.broken_external|Follow the cited source link and inspect the destination's response in context. A sharing endpoint is designed for a different request from an ordinary reference page, and a server may reject automated checks while serving visitors. Keep unverified links in a review list rather than deleting them as certainly dead. Where an address is genuinely wrong, correct the source component so the same malformed destination does not return on the next build.
links.http_on_https|Compare the written destination with the site's final secure address. A redirect may rescue the old spelling, but the internal source can still be updated. Keep legacy redirect support for visitors arriving through links you do not control. Review the shared navigation and stored content separately, because the same plain-scheme link can be generated by a template or copied into an individual article's body.
links.internal_volume|Review the source pages as well as the affected destination. An incoming-link count describes discovery routes, while an outgoing-link count describes choices offered from the page itself. Keep both directions in your notes. Add links that belong in the reader's journey and use accurate labels, then inspect the graph after recrawling rather than assuming a repeated footer link supplies the same context as a useful reference in related content.
links.money_page_weak_inlinks|Compare the detected selling role with the page's actual business purpose. URL patterns help select candidates but cannot replace the owner's knowledge of which services matter. Keep relevant routes from section pages and supporting explanations clear. Review those source links after editing so that they lead to the current offer, rather than adding generic links from unrelated pages merely to increase the number of observed sources.
links.nav_not_in_html|Inspect links in the initial source without judging the menu only after it opens. Text can be readable while the routes between pages are assembled later by scripts. Keep the content-rendering question separate from the navigation question. Test a representative inner page after changing the menu component, and confirm that its anchors carry real destinations even before optional browser interactions enhance their appearance or behaviour.
links.outbound_quality|Group repeated destinations by purpose before removing them. A shared attribution, a tool integration and an editorial source can create different link patterns even when their hosts repeat. Keep useful references and review the relationship behind nofollow choices. If a template supplies most of the repeated links, inspect that component directly rather than editing unrelated articles, and verify that the remaining labels still explain where each external link leads.
links.pagination|Compare the content on the numbered page with the canonical destination. Distinct listing entries deserve a deliberate address policy, while a true duplicate may justify sharing a representative URL. Keep navigation between listing pages understandable. After changing the pagination template, inspect the source tags on later pages as well as the initial list, since a correct first-page declaration does not establish what the rest of the sequence publishes.
local.applicable|Read the result as a description of what the site represents. A directory may list premises that belong to someone else. Keep the local decision attached to the business being reviewed. If useful text was unavailable, make it readable and repeat the review before deciding how local checks apply.
local.contact_signals|Review the contact method the business actually offers. A text-only route should not be rewritten to invite calls, and a service-area business should not invent a place for customers to visit. Keep maps, forms and phone links aligned with those real choices. Inspect the shared contact component after editing and verify the destination or form behaviour independently from the audit's presence flags.
local.geo_targeting|Compare place wording with the area the service really covers. A town in an office address may be less relevant than the customer's service area. Keep titles useful to readers and avoid adding places solely to satisfy a recogniser. Review address text and structured location values together, especially when the visible footer already contains the information that a limited text sample did not establish.
local.nap|Group contact details by the location or department they belong to. Different numbers and address abbreviations may all be valid. Keep a clear main contact route and useful location details. Check the displayed number, its hidden link target and the business markup when repairing an old value.
local.reviews|Read each review phrase in its surrounding passage. A page discussing reviews may contain no customer testimony. Check whether a rating belongs to the business or a supported item. Before adding markup, confirm its subject and values against the visible review and its source.
local.schema|Inspect who each business node describes before filling gaps. A directory entry, a publisher and the business accepting enquiries can be separate entities. Keep fields attached to the correct subject and use real values only where they apply. If the type is wrong, correct that claim rather than inventing details to complete its expected field list, then compare the result with the public contact information.
mar.ad_pixels|Compare a detected script with the event it is intended to send. A staged value can be present in markup without being executable, while a rendered-only observation has a narrower coverage scope. Keep consent choices intact when repairing loading. Use the advertising platform's own validation for event delivery, and remove duplicate installations only after identifying the template or manager that owns each copy.
mar.analytics|Compare the tag named in the report with the tool the business actually uses. A container can be installed while its analytics tags still wait for configuration or consent. Review each state before adding code. After changing templates, verify event delivery and check for duplicates inside the intended service.
mar.consent|Inspect the behaviour behind the banner, not only its visible presence. A policy link and an accept button do not show which scripts load before a choice. Keep the stated privacy practices aligned with actual tracking. Review the site with the people responsible for those practices, and test changed choices as well as the initial visit before treating a configuration update as a complete resolution of the concern.
mar.email_capture|Follow a signup invitation through to the intended list and confirm what a subscriber is told. A recognised phrase can be present in a discussion rather than a working invitation. Keep subscription choices clear and distinct from a service enquiry where their purposes differ. If the business deliberately does not send updates, record that choice instead of adding an unwanted workflow merely to remove an optional finding.
mar.stack|Match detected labels to the installation that supplies them. A shared tag manager and a page template can both introduce tools, so removing a visible script may leave another copy. Keep needed workflows in view during cleanup. Ask the responsible person which tools remain active, then verify the relevant events after removing abandoned code rather than treating a smaller detected inventory as proof that every remaining tool works.
mar.utm_hygiene|Inspect a tagged internal destination alongside the reason the tag was added. Ordinary navigation and an external acquisition link have different tracking roles. Keep public internal addresses clean where campaign attribution is unnecessary. Review menu builders, banners and stored article links as separate sources, then test any replacement event tracking independently because this check identifies tagged links without reading the resulting analytics session records.
onpage.anchors|Read the label without relying on nearby visual placement. A person reviewing a list of links may not have the same surrounding cues as someone looking at the whole layout. Keep destination text specific enough to choose the right page. For file links, preserve the useful download meaning, and inspect icon controls through their actual accessible names rather than adding visible words that duplicate an existing label unnecessarily.
onpage.description|Compare the description with the content it summarises. A technically present value can still be copied, stale or vague. Keep the useful point early and avoid adding claims simply to fill space. After editing a shared description template, inspect pages with different subjects so that a fix for an empty value does not replace accurate page-specific summaries with the same generic statement across the site.
onpage.headings|Read the outline independently of font size and colour. A styled paragraph does not become a heading merely because it looks prominent. Keep the structure tied to the relationships between sections. When a shared header supplies a repeated heading, distinguish that furniture from the main subject before editing, and inspect the final markup so that a visual adjustment does not leave the document hierarchy harder to follow.
onpage.images|Inspect the image's purpose before writing alternative text. A decorative element and an informative picture require different treatment. Keep the reserved dimensions consistent with the image actually delivered, including responsive variants. Review loading choices against where the picture is needed, and check a representative page after editing the component rather than assuming that adding attributes everywhere makes every image's text, size and loading priority correct.
onpage.lang|Read the declaration values as statements about the document, rather than merely checking that tags exist. A language attribute can be nonempty and wrong, while a viewport can be present on an unusable narrow layout. Keep the presence result separate from those broader reviews. Update the shared head carefully, then inspect generated pages in different languages or templates so that a common fix does not overwrite valid distinctions.
onpage.title|Read the title as a compact promise about the destination. A useful distinction can disappear when an overlong value is cut without understanding the page. Keep necessary product or topic details and remove redundant wording first. Compare the revised title with related pages as well, because satisfying width and repetition limits does not establish that each page now has its own accurate, distinct title.
perf.cls_risk|Inspect the space reserved before content images load. A template logo and a large article image can have different roles in the reported pattern. Keep the source diagnosis separate from a measured browser shift. After reserving the intended dimensions, review the layout while loading and confirm that the image still fits its container, rather than assuming any numeric width and height will preserve the desired space.
perf.compression|Inspect the encoding negotiation and response headers on the affected route. A separate probe can explain why an initially plain response did not justify a missing-compression claim. Keep cache validators separate from cache lifetime choices. Test dynamic and stable page types appropriately after changing server configuration, because a header appearing on the homepage does not establish that every route receives the same delivery policy.
perf.modern_images|Compare encodings using the actual picture and the resolution needed on the page. A file extension is only the selection signal here, not a measurement of quality or transfer cost. Keep responsive alternatives and fallbacks working after conversion. Check which source a browser chooses, then review the delivered file separately instead of assuming that a modern-source flag proves the visitor received the smallest suitable image.
perf.page_weight|Inspect what the HTML contains before moving or deleting large blocks. Embedded state, repeated listings and inline assets have different purposes. Keep required content readable while reducing avoidable duplication. Compare the same document measurement before and after editing, and record a truncated read as a lower bound, since the bytes retained by a capped fetch cannot establish how much unseen HTML remains beyond it.
perf.redirect_cost|Trace why the crawl requested old addresses in the first place. A sitemap or internal template may still publish them, while an externally discovered legacy URL can correctly rely on a redirect. Keep necessary old-address support. Update controlled sources to final destinations and compare another crawl, using actual response timing separately when the question is how much delay visitors experience rather than how often a redirect appeared.
perf.render_blocking|Review the role of each blocking file before changing its loading order. A stylesheet needed for the first view and an optional enhancement should not be treated identically. Keep dependencies intact when deferring scripts. After editing, test the initial display and later interactions together, because a lower resource count cannot establish that the page still paints correctly or that an action remains available when needed.
perf.ttfb|Compare first and repeat requests for the same page types. A warm result may reveal a cache effect that varies between visits. Check how many positive samples were available before relying on the median. Review server work and cache behaviour for slow templates. Repeat comparable measurements after editing.
schema.incomplete|Inspect the declaration and any referenced object on the same served page. A pointer can look substantial in source while contributing no local definition. Keep the type's purpose clear before filling fields. Where a value is genuinely unknown or inapplicable, review whether the node should make that claim at all, rather than inserting plausible-looking data solely to complete the engine's required-property list.
schema.invalid|Copy the exact served block into a parser before changing surrounding page content. A template may generate valid local data and still escape it incorrectly in the final document. Keep syntax repair separate from factual review. After resolving a parser error, inspect literal template values and wrapper output too, because a block can become parseable while still describing an unfinished or inaccurate business field.
schema.mismatch|Compare a declared rating with the visible material that belongs to it. A review word elsewhere may concern another subject. Keep track of which pages had a loaded-browser comparison. Inspect any recognised off-page arrangement before removing it. Use only ratings you can verify against their source.
schema.missing|Inspect several page templates to see where declarations originate. A shared business object and a page-specific content object describe different things, even when both count toward coverage. Keep their roles accurate when extending markup. After adding a type, review its properties and visible subject separately, because a presence result can improve while the new node still contains empty fields or describes another organisation.
schema.opportunity|Read each qualifying question with its answer before adding structured declarations. A heading linked to another page may be navigation rather than a locally answered question. Keep the visible answers and declared text aligned during later edits. Review the existing page's purpose first, and leave out invented questions or unsupported claims about search appearance. This opportunity identifies content shape rather than an assured display feature.
schema.price|Compare the numeric match with the exact offer and its conditions. A number elsewhere in prose may coincide with the declared amount without being its price. Keep currency, billing period and the subject of the offer clear in your manual review. When scripts supply the visible price, inspect that output before editing the declaration, and preserve uncertainty when the audit never obtained a rendered comparison.
security.headers|Inspect header values after confirming their presence. A key can exist while applying an unsuitable policy, and a shared proxy can supply values independently of the page template. Keep the recognised equivalent cases in view before adding duplicates. Review representative responses after configuration changes and check the hosts covered by a transport policy, rather than assuming that a presence-only result completes a broader application security review.
security.https|Compare the starting address, final host and certificate details as separate parts of delivery. A host move can make the final certificate the relevant one even when the original name appears in the audit setup. Keep unknown probes distinct from invalid results. After changing renewal or redirect configuration, test the affected route again without treating a successful final browser view as proof that every intermediate response behaved as intended.
security.mixed_content|Inspect the resource target as well as the page that names it. An HTTPS address needs to serve the file the page actually uses. Prioritise insecure scripts, styles and frames when reviewing the report. Find old addresses in shared templates and stored content. After updating them, test page loading and interactions in a browser.
social.favicon|Inspect the icon request independently of a cached browser tab. A tab can retain earlier artwork even after the served file changes, while a successful probe says little about how the icon looks. Keep the file's existence and visual identity as separate checks. Review the declaration generated by the shared head and request the intended resource again before treating a missing result as a reason to redesign the artwork.
social.open_graph|Compare preview metadata with the actual page and named image. A title can be useful while the picture address is stale, and an unmeasured image response remains uncertain. Keep the primary image property distinct from its subproperties during repair. After updating a shared template, inspect pages with different content so that every preview does not inherit a generic or misleading summary simply because the tags are now present.
social.twitter|Inspect which card fields already exist before adding another declaration. A page may have a useful preview title and picture while lacking only the type value. Keep the type consistent with the intended preview and avoid competing values supplied by different templates. Review the served metadata first, then check any platform preview separately, because a cached external result cannot establish exactly what the current page source publishes.
""".strip().splitlines())


# Each answer carries a short fact quoted from its own reviewed row. This
# keeps the visible FAQ and JSON-LD together and makes grounding testable.
FAQ = {}


def faq_rows(text: str) -> None:
    for block in text.strip().split("\n\n"):
        key, *lines = block.splitlines()
        if len(lines) != 3 or key in FAQ:
            raise ValueError(f"Malformed or repeated FAQ: {key}")
        entries = []
        for line in lines:
            question, answer, field, fact = line.split("|")
            if field not in {"condition", "pages", "reports"}:
                raise ValueError(f"Unknown FAQ fact field: {field}")
            if fact.casefold() not in COPY[key][field].casefold() or fact.casefold() not in answer.casefold():
                raise ValueError(f"FAQ fact missing from row or answer: {key}: {fact}")
            entries.append({"question": question, "answer": answer,
                            "fact": {"field": field, "text": fact}})
        FAQ[key] = entries


faq_rows("""
ai.citable_facts
How much text does a page need for the citable-facts check?|A sampled page needs 250 words or more. The site also needs enough indexable pages and a language the test supports.|condition|250 words
Does a number alone make my copy a citable fact?|No. Prose needs an attribution pattern as well as a numeric match. A person must still verify the resulting claim.|condition|an attribution pattern
How serious is a lack of specific claims on my pages?|The result has medium severity when too few sampled pages qualify. It does not predict whether an AI service will quote you.|reports|medium severity

ai.crawler_access
Which AI search crawlers does this robots check name?|Among the citation crawlers are OAI-SearchBot, PerplexityBot, Meta-WebIndexer and Claude-SearchBot. Training access is considered separately.|condition|OAI-SearchBot, PerplexityBot
Can a failed robots request prove that AI crawlers are allowed?|No. HTTP status 500 or higher leaves the saved policy uncertain. A failed fetch with a requested robots address also prevents a confident result.|condition|HTTP status 500
Is an intentional AI training block treated like an accidental search block?|No. An accidental citation restriction can be critical. Training restrictions are notices, preserving the distinction between search access and training choices.|reports|training restrictions are notices

ai.dead_crawler_directive
Can an old crawler name stop protecting my pages?|Yes. A retired token can leave a lost restriction when its live replacement has no matching protection.|condition|lost restriction
Does every retired crawler rule need a new restriction?|No. Existing restrictions in the wildcard group or a live replacement can already cover the intended policy.|condition|wildcard group
How serious is a crawler rule that no longer takes effect?|A lost restriction gets medium severity. An obsolete name with no lost coverage is only a notice.|reports|medium severity

ai.edge_access
Can my server block an AI crawler that robots.txt allows?|Yes. A saved server refusal can conflict with the saved robots decision. The check compares policy with the connector's responses.|condition|saved robots decision
How does the AI server-access check handle rate limits?|Throttling covers HTTP status 503 and HTTP status 429. It gets a different explanation from an ordinary access refusal.|condition|HTTP status 429
Are payment responses counted as AI crawler refusals?|No. Payment responses at HTTP status 402 are kept separate. They produce notices rather than an ordinary conflicting-refusal finding.|condition|HTTP status 402

ai.entity
How many profile hosts does my business identity need in this check?|The weak-coverage case applies below 3 recognised profile hosts. Declare only accounts your business owns.|condition|3 recognised profile hosts
Where does the identity check first look for my business?|It starts with owned JSON-LD identity nodes across the first 60 indexable pages. Broader checks can prevent a false absence claim.|condition|60 indexable pages
Is missing business markup more serious than weak profile coverage?|Yes. The absence of business identity can receive high severity. Weak recognised profile coverage is low.|reports|high severity

ai.extractability
How long must a page be for the question-heading check?|It needs at least 300 words, must be indexable and must use supported prose. Shorter pages do not enter this comparison.|condition|300 words
Do question headings repeated in every template count?|No. Questions appearing on every substantial page are set aside. Remaining subheadings must meet the question test.|condition|every substantial page
Does low question-heading coverage mean my answers are wrong?|No. The result is medium severity and describes heading structure. Answer accuracy and likely use by AI services remain unmeasured.|reports|medium severity

ai.freshness_signal
Does a date on my website node count as an article date?|No. The date test excludes site-level types. A qualifying date must describe the content itself.|condition|site-level types
How much content is needed for the machine-readable date sample?|At least 4 indexable pages must each contain 300 words or more. Smaller samples do not reach the dated-share test.|condition|4 indexable pages
How serious is missing readable date markup on substantial pages?|It is a low severity result. A detected date still needs review to confirm that it reflects the real work.|reports|low severity

ai.llms_txt
Does this check grade the contents of the AI summary file?|No. It checks the saved file probe, leaving headings, links and usefulness outside its scope.|condition|headings, links
Does a refused request for the AI summary file mean it is missing?|No. A refused response is unreadable, leaving presence uncertain. Check the refusal before creating another file.|condition|refused response
Is publishing an AI summary file required to clear a serious error?|The result concerns an optional file and is only a notice. It does not predict changes to AI answers.|reports|optional file

ai.rendering
Can my page look complete in a browser and still fail the AI HTML check?|Yes. Content marked as needing JavaScript can qualify despite appearing in a loaded browser. Review the original response alongside that view.|condition|needing JavaScript
Are pages deliberately excluded from search counted as unreadable by AI?|No. Pages intentionally excluded from search are set aside before affected content is listed.|condition|intentionally excluded from search
How serious is main content missing from the initial HTML for AI crawlers?|The result has high severity. It identifies affected URLs without testing a particular AI service's script support.|reports|high severity

ai.unmeasurable_optout
Can a public audit read private AI provider settings?|No. A provider-side control is outside what this audit can observe. Account access is needed to review that choice.|condition|provider-side control
Why might the private AI control notice be absent?|A nonempty access table blocking every citation-critical crawler suppresses it. That leaves the private setting unmeasured.|condition|every citation-critical crawler
Does the AI opt-out notice assign a content score?|No. There is no numeric score in this test. The notice explains an observation limit rather than grading your copy.|condition|numeric score

brand.logo
Can a business-name text link count instead of an image logo?|Yes. A text link can identify the business without an image. Its wording must contain recognised brand terms.|condition|text link
How many pages does the logo identity comparison need?|The check starts with 3 successful pages or more. It then compares readable business identity across them.|condition|3 successful pages
Is weak logo alternative text a serious brand error?|The finding has low severity. It asks you to review the link's readable name, without judging the artwork.|reports|low severity

brand.name_consistency
Why can a long business name be absent from the name comparison?|Candidate names exceeding 60 characters are discarded. Review a long declaration directly if it falls outside that limit.|condition|60 characters
Does mentioning another company in an article create a name mismatch?|No. Body text mentioning another company is outside the comparison. Business-naming declarations supply the input.|pages|body text
How serious are conflicting business-name declarations?|Remaining distinct names lead to a medium-severity finding. Legal, trading and translated names still need review in context.|reports|medium-severity finding

brand.positioning
How many descriptions are needed to compare my site's message?|The sample needs 6 indexable pages or more, each with a nonempty description. Supported prose is also required.|condition|6 indexable pages
How many shared subject terms clear the positioning check?|At least 2 shared terms that meet the frequency rules suppress the finding. Those terms should still make sense for each page.|condition|2 shared terms
Does matching vocabulary prove my positioning is clear?|No. Shared vocabulary is a clue. A person must decide whether the descriptions express the same real offer.|reports|Shared vocabulary

brand.visual_consistency
How many font families trigger the visual-style finding?|More than 4 font families triggers a low result. The count needs review against the site's intended design.|condition|4 font families
Can unread stylesheets make the site look free of style differences?|A stylesheet cap can leave pages unread and exclude them from the sample. Insufficient readable styles can stop the comparison.|condition|stylesheet cap
Does the visual-style check measure colour contrast?|No. It groups colours and counts fonts; it does not measure contrast. Screenshots are outside its scope.|reports|measure contrast

brand.voice_consistency
How long must pages be for the writing-voice comparison?|Each sampled page needs at least 250 words and enough usable sentences. Estimated word counts are excluded.|condition|250 words
What sentence-length spread triggers the voice finding?|A standard deviation reaching 7.0 words per sentence can qualify. This compares page averages rather than every sentence individually.|condition|7.0 words per sentence
Does a voice-consistency finding prove different people wrote the pages?|No. Its low severity reflects a sentence-length clue. The test cannot establish authorship or whether varied page roles justify the difference.|reports|low severity

brand.social_consistency
Does the social-profile check compare exact account addresses?|No. The comparison uses platforms, leaving the exact account URL for you to verify. Matching platforms can still name different accounts.|condition|exact account URL
Can a profile linked only in my footer count as relevant?|Yes. Repetition across enough sampled pages can qualify a profile. The test samples up to 30 pages and also considers homepage links.|condition|30 pages
Why can social declarations built by scripts produce a notice?|Script-only declarations are handled separately from served sameAs links. The notice keeps that delivery limit visible.|reports|Script-only declarations

content.ai_slop
How many stock phrases trigger the AI-sounding copy check?|A page must match 2 distinct entries or more from the phrase list. Repetition of a single entry cannot fill that count.|condition|2 distinct entries
Does a stock-phrase match prove an AI wrote my page?|No. The check reports wording patterns with a medium-severity finding. It cannot determine who or what wrote the text.|reports|medium-severity finding
Are taxonomy archives included in the stock-copy phrase test?|No. Taxonomy archive URLs are excluded from the prose sample. The test also requires a language it supports.|condition|Taxonomy archive URLs

content.competing_pages
How many shared title words can make pages candidates for overlap?|A candidate pair needs 2 shared meaningful words or more, then meet the overlap limit. Other guards can still keep distinct subjects apart.|condition|2 shared meaningful words
Can different products with similar titles be excluded from competing-page groups?|Yes. The guards separate products and other distinct subjects before grouping. Shared ordinary words alone do not settle page purpose.|condition|separate products
Does the competing-pages check use search rankings?|No. It compares titles and page context without reading ranking data. Read the pages before deciding to merge them.|pages|ranking data

content.dates
Can a visible article date lower the missing-date finding?|Yes. When every affected article already displays a date, the finding has low severity. Missing markup still needs repair.|reports|low severity
How many articles are needed to check missing date markup?|The sample needs at least 3 articles. Recognised section listings can be excluded from article selection.|condition|3 articles
Does the article-date check verify that an update date is truthful?|No. The check cannot establish whether an update represents a real edit. Use the date of the actual work.|reports|a real edit

content.eeat
Can an enquiry form satisfy the trust check without a Contact page?|Yes. An enquiry form can qualify with 2 fields or more. Test the actual route separately.|condition|2 fields
How many marked-up articles are needed for the missing-author test?|It needs at least 3 indexable pages carrying article markup. A smaller article sample does not reach this authorship finding.|condition|3 indexable pages
Does an author name prove expertise in the trust check?|No. Missing authorship is low severity, but a detected byline cannot establish expertise. Confirm the real publisher and their role.|reports|low severity

content.js_rendering
When does JavaScript-dependent content become a high-severity finding?|High severity applies above a 0.5 share of indexable pages. At the boundary, the affected pages stay in the medium group.|condition|0.5
Do deliberately noindex URLs count toward JavaScript content problems?|The test sets aside pages intentionally excluded from search. Its reported set concerns content meant to be found.|condition|intentionally excluded from search
Does the JavaScript content check measure interactive controls?|No. Interactive controls need separate tests. This result follows the crawler's record of missing initial content.|pages|interactive controls

content.lang_mismatch
How many words are needed to compare declared and detected language?|The text needs 40 words or more plus a language declaration. Shorter passages leave this comparison unmade.|condition|40 words
Can link-heavy pages be excluded from a language mismatch?|Yes. An anchor share reaching 0.7 can exclude listing-like text. Names and bilingual passages also have guards.|condition|0.7
How serious is a remaining language mismatch?|It gets a medium-severity finding. A fluent reader should check the text before the document declaration is changed.|reports|medium-severity finding

content.language_scope
Does an unsupported prose language mean my content is poor?|No. The notice explains a language limit and assigns no content-quality score. Have a fluent reader assess the prose.|condition|content-quality score
Can markup checks run when language-dependent copy checks are skipped?|Yes. Markup and links may be checked independently of prose. Status-code tests can also run when language understanding is unavailable.|reports|markup and links
Does a supported prose language trigger a scope warning?|No. A supported language ends this test without a finding. The notice is reserved for unsupported prose.|condition|supported language

content.placeholder
How much surrounding text is checked for a placeholder marker?|The search uses a 160-character window. Additional guards distinguish examples and quoted discussion from unfinished copy.|condition|160-character
Are snippet announcements and holding pages tested with the same word limit?|No. Snippet announcements use a 12-word limit; holding-page checks use 200 words. Each has its own context rules.|condition|12-word limit
How serious is a confirmed placeholder in published content?|It receives a high-severity finding. Read the marked passage in context before replacing a legitimate example.|reports|high-severity finding

content.readability
Is an average of 25 words per sentence too long for this check?|No. Exactly 25 words per sentence passes the length comparison. Only a higher average reaches the finding.|condition|25 words per sentence
How much text is needed for the sentence-readability sample?|A page needs at least 200 words and enough usable sentences. Unsupported prose is left out.|condition|200 words
Does a readability finding mean every sentence needs shortening?|No. It is a low severity result based on an average. Read individual passages to find where the structure becomes hard to follow.|reports|low severity

content.thin
What word count puts an ordinary page in the very-thin group?|Ordinary pages below 60 words enter the very-thin group. Utility pages, useful hubs and script-dependent pages have separate treatment.|condition|60 words
Does a page with 60 words still count as thin?|Yes. It remains below 150 words, the ordinary thin-content limit. Passing that count alone would not establish usefulness.|condition|150 words
Are sparse archives treated as severely as very thin articles?|No. Sparse archive findings are low, while ordinary very thin content can be high severity.|reports|high severity

content.topic_gaps
How many topic-gap suggestions can the report show?|It shows at most 12 suggestions. More eligible queries do not lengthen that displayed list.|condition|12 suggestions
Can the audit invent topics when the demand connector has no data?|No. The demand-topics connector supplies the input. When suggestions are unavailable, the result explains that limit instead of inventing topics.|condition|demand-topics connector
Do topic-gap suggestions include search volume?|No. The check does not supply search volume or establish demand size. Treat each saved query as a prompt to review existing answers.|reports|search volume
""")


faq_rows("""
cvr.dead_contact
Does the mail-link check test whether a particular inbox exists?|No. It uses domain delivery results rather than testing a particular inbox. A domain result cannot promise that someone will answer.|reports|particular inbox
When can a published email address produce a dead-contact finding?|The saved result must say accepts-mail explicitly false. Unknown delivery results cannot establish that the published address is unusable.|condition|accepts-mail explicitly false
Does a conclusive mail failure on a static host change severity?|Yes. The conclusive static-host case is high severity. Other qualifying failures are medium.|reports|conclusive static-host case

cvr.form_friction
How many fields make an enquiry form long in this audit?|A form reaches the long-form finding at 6 or more counted fields. Review whether each request is needed before the first reply.|condition|6 or more counted fields
Can a booking service count as a way to contact my business?|Yes. Recognised booking or messaging services can qualify alongside forms and contact links. An embedded form is not the only route.|condition|booking or messaging services
Is a missing contact route more serious than a long form?|Yes. No route across the target pages is high severity. Long forms are medium severity.|reports|medium severity

cvr.funnel
How many pages are needed to check educational and comparison sections?|The site needs at least 6 indexable pages. Recognised educational and comparison paths then supply the clues.|condition|6 indexable pages
Is a missing comparison section as serious as missing both content groups?|No. Missing one group gets low severity. The absence of both educational and comparison groups receives medium.|condition|low severity
Does the funnel check read whether my guides persuade visitors?|No. The path-based presence test uses addresses as clues. Useful answers under unusual paths can be missed.|condition|path-based presence test

cvr.message_match
How much title-to-heading overlap avoids a message-match finding?|A meaningful-word overlap of 0.2 passes the comparison. Lower overlap can qualify after the wording guards are applied.|condition|0.2
Can a repeated business heading be ignored when checking my page headline?|Yes. A heading seen across a 0.6 share of a large enough sample is treated as shared furniture. The comparison prefers a page-specific heading.|condition|0.6 share
Does a title-headline mismatch prove my wording misleads readers?|No. The low severity result is a word-overlap clue. Synonyms and page purpose still need a person's review.|reports|low severity

cvr.no_cta
Can a form count as my page's next step without another button?|Yes. A form containing 2 fields or more can qualify without another action button. Test the destination yourself.|condition|2 fields
Are generic action labels as serious as having no action?|No. Missing actions are high severity, while weak labels are medium. Read the wording in the context of its destination.|reports|high severity
Which pages are checked for missing calls to action?|The homepage and selling pages are preferred. Otherwise, 5 shallow indexable pages is the fallback cap.|pages|5 shallow indexable pages

cvr.pricing
Can a quote invitation satisfy the cost-information check?|Yes. The quote and estimate signals can qualify, so the test does not require every business to publish a fixed price.|condition|quote and estimate
How far into page text does the pricing check read?|It searches up to 6000 characters on each sampled page. Important cost wording beyond that sample can be missed.|condition|6000 characters
Does a clean pricing result prove my costs are clearly explained?|No. A currency symbol can satisfy the test. Read the full offer and its terms to decide whether the explanation helps.|reports|currency symbol

cvr.social_proof
How much text is searched for testimonials and work examples?|Each target contributes up to 8000 characters plus subheadings. Wording outside that text window may be missed.|condition|8000 characters
Does the social-proof check verify that a testimonial is true?|No. It looks for stored proof phrases, leaving the underlying claim unverified. Keep your own source and permission records.|condition|underlying claim
When does missing proof language trigger a selling-page finding?|The result requires that every target lacks a match. A qualifying proof phrase on a target can prevent the absence finding.|condition|every target lacks a match

cvr.unusable_phone
When do repeated digits look like a placeholder phone link?|A run containing 7 identical digits or more can qualify. The hidden destination is inspected independently of the label.|condition|7 identical digits
Can a local phone link need international context?|Yes. A local-format target without a plus prefix or phone-context parameter can qualify. Regional declarations can raise severity.|condition|phone-context parameter
Does the phone-link check prove the line works?|No. It validates the written link format. Confirm the intended contact route separately.|reports|written link format

cvr.value_prop
How short can my opening text be before the offer is treated as absent?|Opening text below 25 characters reaches the absent-value finding. The test uses saved text rather than screen position.|condition|25 characters
Can an opening statement about only the company produce a finding?|Yes. At least 3 inward matches and no outward match can trigger the separate medium result. Adding pronouns alone will not clarify an offer.|condition|3 inward matches
Does the value-proposition check measure what is above the fold?|No. The physical fold is outside this check. Saved opening text supplies the measured wording.|condition|physical fold

index.broken
Is an HTTP 403 response the same as a missing page?|No. HTTP status 403 represents a refusal here, while HTTP status 404 represents a missing response. Access restrictions need their own review.|condition|HTTP status 403
How serious are server errors in the failed-page check?|The result is critical for server errors. Missing addresses, refusals and timeouts have separate treatment.|reports|critical for server errors
Are challenge pages treated as ordinary broken-page responses?|No. Responses marked as challenges are kept outside the main status groups. They can leave the destination unchecked.|condition|marked as challenges

index.byte_cap
What is reserved for headers in the HTML fetch budget?|Each response has 1024 bytes set aside for headers. The remaining budget is compared with decompressed HTML and tag positions.|condition|1024 bytes
Are images included in the HTML byte-cap comparison?|No. The document comparison leaves out other separate files, including images and stylesheets. It measures decompressed HTML.|pages|other separate files
Is oversized HTML worse when important markup lies beyond the budget?|Yes. Important markup beyond the limit is high severity. Without identified lost tags, the oversized-document result is medium.|reports|high severity

index.canonical
Is an off-site canonical always treated as a critical error?|No. Declared syndication is medium. Unrelated off-site targets get critical severity, so review the intended relationship first.|reports|Declared syndication is medium
Can a canonical pointing to a noindex page be high severity?|Yes. The report rates noindex targets high, along with conflicting canonicals. Check whether the intended representative page can be indexed.|reports|noindex targets high
Does the canonical check treat trailing slashes as distinct targets?|The comparison applies trailing-slash handling before checking distinct target strings. Other address differences can still need review.|condition|trailing-slash handling

index.canonical_conflict
Can a response header conflict with the canonical in my HTML?|Yes. A canonical in the HTTP Link header is compared with the document declaration. Different destinations can trigger the conflict.|condition|HTTP Link header
Does having only an HTML canonical trigger a header conflict?|No. Both declarations must exist for this comparison. A page carrying only an HTML canonical has no conflict here.|condition|HTML canonical
How serious is disagreement between header and HTML canonicals?|The conflict gets high severity. Both targets and the saved source page help locate the configuration needing repair.|reports|high severity

index.depth
How many clicks make an indexable page deep in this audit?|A measured depth of 4 clicks qualifies. That distance follows the internal links the crawl could actually read.|condition|4 clicks
Can an incomplete crawl prove a page is an orphan?|No. Without support for link-graph claims, orphan status is withheld. Improve coverage before treating absent links as a confirmed defect.|condition|link-graph claims
Are confirmed orphan pages more serious than deep pages?|Yes. Confirmed orphans are medium, while deep pages have low severity. Both results still need a review of page purpose.|reports|low severity

index.duplicate_content
How many words are needed for the duplicate-body comparison?|A page needs at least 50 words. Shorter responses are left out of the ordinary body-hash comparison.|condition|50 words
Can identical pages with the same canonical be excluded from body duplicates?|Yes. A group can be excluded when its members share a single nonempty canonical. That declaration should still describe the right relationship.|condition|single nonempty canonical
Are duplicate descriptions as serious as duplicate page bodies?|No. Body duplication gets high severity. Titles have medium severity and descriptions low.|reports|high severity

index.meta_refresh
Can a successful page response still contain a redirect instruction?|Yes. A recorded JavaScript redirect can be reported even after a successful response. Document instructions and server status are separate observations.|condition|recorded JavaScript redirect
Are JavaScript redirects and meta refresh given the same severity?|No. JavaScript redirects have low severity, while meta refresh results are notices. Review whether the mechanism fits the page.|reports|low severity
Does the document-redirect check judge whether the destination is useful?|No. It reports the mechanism and any delay. The relevance of the destination needs a separate review.|reports|any delay

index.noindex
Is a noindex directive on the root homepage serious?|Yes. Homepage noindex is critical. The explanation accounts for an audited host that moved elsewhere.|condition|noindex is critical
Are utility pages included in the ordinary blocked-page share?|No. The count excludes tag or author archives along with utility URLs. Sitemap-only discoveries are separated too.|condition|tag or author archives
When does noindex coverage move from medium to high severity?|High severity applies when blocked pages exceed a 0.2 share after exclusions. The denominator is successful pages.|condition|0.2 share

index.redirects
How many redirect hops count as a chain finding?|At least 2 hops reaches the medium chain result. A working move still needs review before changing a useful redirect.|condition|2 hops
Can a single redirect be reported when my menu uses the old address?|Yes. Exactly 1 hop can trigger the low result when internal links still point to its start. Update links you control.|condition|1 hop
How serious is a redirect loop?|A recorded redirect loop is critical. It is kept separate from a working chain or an outdated internal link.|condition|redirect loop

index.robots_blocks_all
Is blocking Googlebot across the site more serious than blocking Bingbot?|Yes. The Googlebot case is critical, while Bingbot blocks are high. Review the intended crawler policy before changing either.|condition|Bingbot blocks are high
Can a robots.txt server error leave search policy unknown?|Yes. HTTP status 500 or higher leaves robots policy unreadable and gets a critical server-error result.|condition|HTTP status 500
Does an ignored crawl-delay request mean the site blocks every crawler?|No. The crawl-delay wait concerns a notice about audit behaviour. It is separate from a policy blocking search crawlers.|condition|crawl-delay wait

index.sitemap
Can exactly three missing sitemap entries trigger the coverage finding?|No. The threshold is at least 3 entries and the count must exceed it. Larger crawls can raise that threshold through the share rule.|condition|3 entries
Are refused sitemap requests treated as missing files?|No. Missing and refused sitemap probes are separated. An unreadable result is a notice because file presence may remain unknown.|condition|refused sitemap probes
Are broken sitemap files more serious than missing sitemap files?|Yes. Broken files get high severity; missing files get medium. Inspect the saved response before deciding which repair applies.|reports|high severity

index.soft_404
What does the saved missing-page probe flag as a soft 404?|The saved probe can identify HTTP status 200 on a missing page where HTTP status 404 was expected. This mismatch gets a medium result.|condition|HTTP status 200
Does the site-level soft-404 check make a fresh request?|No. The missing-page test result was saved earlier. This check reviews that record without another request.|condition|missing-page test result
Does a clear site-level soft-404 result prove every missing URL works correctly?|No. A false flag only clears this saved test. Other missing addresses may need separate response checks.|reports|false flag

index.soft_404_pages
How long can a page be and still enter the error-body check?|Pages above 250 words are skipped. Short successful responses can be searched for stored not-found wording.|condition|250 words
Does an internal link to an error-like page raise severity?|Yes. An observed source link moves the result from medium to high. The text still needs review before calling the page missing.|condition|medium to high
How much text is searched for not-found markers on successful pages?|It searches the title and first 1500 characters. A matching phrase leaves the cause uncertain until the response is inspected.|condition|1500 characters

index.url_hygiene
How long must a URL be for the long-address notice?|It must exceed 115 characters. Equality does not enter the long-address group.|condition|115 characters
How many ampersands put a URL query in the multiple-parameter group?|At least 2 ampersands qualifies the query. The group must also clear the page-count or share requirement before it is reported.|condition|2 ampersands
Are session identifiers as minor as uppercase URL paths?|No. Session identifiers have high severity, while uppercase paths are low. Long addresses receive notices.|reports|high severity

index.www
Does the www check choose which host spelling I should use?|No. Choosing the preferred host is left to you. The test reads the saved www redirect result.|condition|preferred host
How serious is a failed www-to-preferred-host setup?|It gets high severity. Inspect the saved host responses to decide which redirect setting needs repair.|reports|high severity
Does a www finding mean the bare domain is inherently worse?|No. The bare domain and www can both be valid choices. What matters here is the observed host setup and expected redirect.|reports|bare domain

intl.hreflang_codes
Can a hreflang code contain a script subtag?|Yes. An optional 4-letter script can sit between language and region. The full value must still match the allowed format.|condition|4-letter script
Does an unrecognised hreflang region always mean the region is invalid?|No. Unrecognised regions or languages receive notices. A missing reference-table entry is kept separate from a known defect.|reports|regions or languages
Are empty hreflang values and x-default checked as ordinary language codes?|No. Empty values, x-default and repeats are skipped. The format comparison uses the remaining values on successful pages.|condition|x-default

intl.hreflang_return
How many pages are needed to check alternate-language return links?|At least 2 successful pages carrying hreflang are needed. Both sides must be available for the relationship to be judged.|condition|2 successful pages
Can an uncrawled translation be called missing a hreflang return link?|No. A target outside the successful crawl set is left unchecked. Its return declaration cannot be inferred from an unavailable page.|condition|successful crawl set
How serious is a confirmed missing hreflang return link?|It has high severity. Review the reported source and target together before updating the alternate declarations.|reports|high severity

intl.hreflang_self
Must a page appear in its own hreflang target set?|Yes. Each qualifying page should belong to its declared target set. The address comparison ignores trailing slashes.|condition|target set
Does a single-language site need hreflang to pass the self-reference check?|No. With no hreflang pages, there is nothing for this comparison to test. It reviews existing declarations rather than requiring new ones.|condition|no hreflang pages
How serious is a missing hreflang self-reference?|The result receives medium severity. Address aliases beyond trailing-slash differences still need review.|reports|medium severity

intl.hreflang_targets
Can an alternate-language target returning an error be unusable?|Yes. After refusals are handled, HTTP status 400 or higher can qualify. Redirects and noindex targets have their own qualifying cases.|condition|HTTP status 400
Are refused translation requests reported as dead hreflang targets?|No. Refused responses are unchecked. They receive notices because the saved request cannot establish that the translation is gone.|condition|Refused responses
Does the hreflang-target check judge translations it never measured?|No. Unmeasured targets are skipped. Inspect those destinations separately when the crawl did not save a usable result.|condition|Unmeasured targets are skipped
""")


faq_rows("""
links.broken_external
Is an external link refusing the audit definitely broken?|No. Known refusal codes are treated as unverified. A visitor may still be able to reach the destination.|condition|refusal codes
Can a doubled-scheme external address get its own finding?|Yes. Doubled-scheme addresses are separated from ordinary third-party failures. Inspect the original source link for the malformed target.|condition|Doubled-scheme addresses
How serious are confirmed broken external links?|They receive low severity. Unverified destinations receive notices so that blocked requests are not presented as proven dead links.|reports|low severity

links.http_on_https
Can an HTTP internal link be reported even when it redirects successfully?|Yes. A failed destination is not required. An HTTP link on a secure site can qualify even when a redirect reaches the right page.|condition|failed destination
Does the HTTP internal-link check run on an HTTP-only site?|No. This test applies to a site served over HTTPS. Plain-HTTP sites do not enter the internal-scheme comparison.|condition|served over HTTPS
How serious are HTTP internal links on an HTTPS site?|The finding has low severity. It reports the address spelling rather than establishing that the final response remains insecure.|reports|low severity

links.internal_volume
How few outgoing links make a page sparse in this audit?|A non-homepage can qualify with 2 outgoing internal links or fewer. Add useful routes rather than unrelated links.|condition|2 outgoing internal links
How many readable pages does the internal-link volume check need?|The comparison starts with at least 5 pages that have readable content. Insufficient graph coverage can withhold incoming-link claims.|condition|5 pages
Are widespread single-inlink pages treated like sparse outgoing links?|No. The sparse-link result has low severity. A widespread single-inlink pattern can receive medium severity when coverage supports the claim.|reports|low severity

links.money_page_weak_inlinks
How many incoming links trigger the weak selling-page finding?|The qualifying count is 1 observed incoming link on an eligible selling page. Enough graph coverage is also required.|condition|1 observed incoming link
Is the homepage included in the weak selling-page link check?|No. The check selects selling pages while leaving out the homepage. It also requires readable content and enough crawl coverage.|condition|leaving out the homepage
How serious is a selling page with only one measured source link?|The result has medium severity. Confirm that the recognised address really serves an important selling role before adding links.|reports|medium severity

links.nav_not_in_html
How many HTML pages are needed to check missing source navigation?|The sample needs 3 successful HTML pages or more. A saved navigation flag and link records then supply the result.|condition|3 successful HTML pages
Can a menu visible after loading still be absent from the HTML crawl?|Yes. A menu can appear in a loaded browser despite missing source navigation. The finding has high severity.|reports|high severity
Does a low average link count alone decide whether navigation is missing?|No. An average-link cutoff does not decide the saved flag. The check uses the crawler's navigation-in-HTML observation.|condition|average-link cutoff

links.outbound_quality
How many links to one external host trigger the dominance finding?|The count must exceed 20 links to a host, and its share must exceed 0.6 of external links. Both requirements apply.|condition|20 links
Does a site with no outbound links always get a warning?|The no-outbound result needs at least 8 indexable pages. It is a notice rather than proof that unrelated links should be added.|condition|8 indexable pages
When does near-universal nofollow use get reported?|The sample must exceed 10 total external links. A nofollow share greater than 0.9 then qualifies for a notice.|condition|10 total external links

links.pagination
How many numbered listing pages are needed for the pagination check?|The sample requires 2 successful pages or more with recognised numbered addresses. Smaller sets do not enter this comparison.|condition|2 successful pages
Does the pagination check compare the items on each listing?|No. The canonical target is compared with address patterns. Whether the target repeats the same listing items needs review separately.|condition|canonical target
How serious is a numbered page canonical pointing outside a pagination pattern?|It receives medium severity. Review whether the destination is intentional before changing the canonical.|reports|medium severity

local.applicable
Can a directory list shops without being a local business itself?|Yes. The test considers listed people or businesses separately from the publisher. A directory can operate online while listing physical locations.|condition|listed people or businesses
Can local-business applicability remain unknown?|Yes. If no pages load successfully, local scope can remain undetermined. Script-dependent main content can also limit the decision.|condition|no pages load successfully
Does a local-business applicability pass mean my contact details are complete?|No. It is a scope result. An undetermined outcome gets a notice rather than establishing that contact details are complete.|reports|undetermined outcome

local.contact_signals
How many pages are sampled for tappable phone numbers?|The first 40 indexable pages are sampled. A printed number outside that window may be missed by this part of the check.|condition|40 indexable pages
Does the missing-map check apply to every local business?|No. A locally served market is required, together with a contact page. Avoid a map implying visits your business does not accept.|condition|locally served market
Is an untappable number as minor as a missing map?|No. An untappable number gets medium severity, while a qualifying missing-map result is low.|reports|medium severity

local.geo_targeting
How many local-page titles without place names trigger the title finding?|The result can apply with 4 titled pages or more lacking a location mention. Local applicability and market requirements must also be met.|condition|4 titled pages
How much address text is searched for local place clues?|The first 40 indexable pages contribute up to 4000 characters each. All indexable titles are read separately for the title check.|condition|4000 characters
Does missing postal-code recognition prove my service area is absent?|No. Postcode recognition and place matching can miss valid wording. Inspect the address and intended audience directly.|reports|postcode recognition

local.nap
How many different phone numbers can trigger local contact inconsistency?|The count must exceed 2 different phone numbers. Multiple recognised locations can explain that variation and suppress the case.|condition|2 different phone numbers
How many address variants can be flagged for a single place?|A count exceeding 3 address variants can qualify. Confirm that the values describe a single location before removing one.|condition|3 address variants
Is a missing phone more serious than an inconsistent address?|Yes. Missing phones are high severity. Inconsistent addresses are low, with other contact findings handled separately.|reports|high severity

local.reviews
How much text is sampled for local review wording?|Each of the first 25 sampled pages contributes up to 3000 text characters. Review markup is inspected across the wider indexable set.|condition|3000 text characters
Does every business testimonial need review markup?|No. Ordinary business testimonials need an eligibility review before markup is added. The declared subject must match the review.|condition|business testimonials
Can missing local reviews and missing item-review markup have different severity?|Yes. The LocalBusiness case can receive a medium finding when reviews are unrecognised. Missing markup on a supported item review can get low severity.|condition|medium finding

local.schema
Do empty LocalBusiness properties count as complete?|No. Empty values count as missing. Fill applicable fields with real information rather than adding empty keys.|condition|Empty values
Which local-business node supplies the list of missing details?|The gap list comes from the most complete candidate. Owned nodes are preferred over those describing listed businesses.|condition|most complete candidate
Are incomplete owned and listed local-business nodes equally serious?|No. Owned-node gaps get medium severity. For incomplete listed-business nodes, the result is low.|reports|incomplete listed-business nodes

mar.ad_pixels
What served-pixel coverage avoids the partial-coverage finding?|A share of 0.7 passes the coverage limit. The comparison uses pixels found in server responses.|condition|0.7
Are pixels seen only after scripts run included in served-code coverage?|No. An observation made only after scripts run is outside the served-code share. It cannot establish the code on unrendered pages.|condition|only after scripts run
Can advertising pixel code be present but unable to run?|Yes. That pattern can produce a high finding. It differs from absence, staging or incomplete coverage.|condition|high finding

mar.analytics
What analytics coverage avoids the missing-tag share finding?|Comparable tagged coverage at 0.85 passes. Browser coverage must be fair enough for the comparison to be made.|condition|0.85
Can uneven browser coverage stop an analytics comparison?|Yes. Uneven browser coverage can make pages incomparable. The audit should not infer missing tags from unequal observations.|condition|Uneven browser coverage
Are retired analytics tags always a high-severity problem?|No. When another tool is present, a retired tag can receive low severity. Review the named tracker and where it appeared.|reports|another tool is present

mar.consent
Which tracking tools trigger the consent-banner presence check?|Detected advertising pixels or recognised session-recording tools trigger it. Missing banner flags across successful pages can then produce a finding.|condition|session-recording tools
Does finding a banner prove that tracking waits for consent?|No. Banner detection cannot establish that the right tags wait for a choice. Its behaviour needs separate review.|reports|the right tags
Does analytics tracking also trigger a privacy-policy check?|Yes. A privacy-policy presence check also follows detected analytics or advertising tracking. Missing policy wording produces a medium result.|condition|privacy-policy presence check

mar.email_capture
How many pages are needed for a missing-signup finding?|The sample needs 5 indexable pages or more without a signup signal. This is a low-priority presence finding.|condition|5 indexable pages
Can a recognised email-platform tracker satisfy the capture check?|Yes. The presence of a recognised email-platform tracker clears this test. It does not establish that a signup form works.|condition|recognised email-platform tracker
How much page text is searched for an email signup invitation?|The text window reaches 8000 characters. Action labels and a saved signup-form flag provide additional clues.|condition|8000 characters

mar.stack
How many tools on one page raise the marketing-stack severity?|A page reaches medium severity at 8 detected tools. The threshold concerns the largest page count rather than the site's whole inventory.|condition|8 detected tools
Does an audit with no detected tools get a stack inventory finding?|No. When there are no detected tools, the inventory finding is omitted. That result does not establish which tools may exist outside the observations.|condition|No detected tools
Is an ordinary marketing-tool inventory an error?|The ordinary inventory gets only a notice. Use the named tools to review purpose and expected data collection.|reports|ordinary inventory

mar.utm_hygiene
How many internal campaign-tagged links trigger the UTM finding?|Any recorded internal campaign link can qualify. The page-count cutoff and minimum-share limits used elsewhere do not apply here.|condition|page-count cutoff
Does the UTM check include campaign links to other sites?|No. External campaign links belong to a different scope. This test concerns internal navigation on the audited site.|pages|External campaign links
Does an internal UTM finding calculate an analytics attribution error?|No. It has medium severity and identifies parameters on links. Analytics reports are not read to quantify an effect.|reports|medium severity

onpage.anchors
How many empty link labels trigger a finding?|More than 3 empty labels are needed. Exactly that count stays within the empty-label limit.|condition|3 empty labels
Is a Download link label always considered vague?|No. A download route or recognised file can justify a plain Download label. Its destination changes the interpretation.|condition|download route
Are email and phone links tested for vague labels here?|No. Email links and phone links are skipped along with fragments and script links. Other contact tests handle different concerns.|condition|phone links

onpage.description
What counts as a short meta description?|A description is short under 70 half-width character units. Wide and fullwidth characters count twice, and other characters once.|condition|70 half-width character units
Is a description width of 165 units too long?|No. At 165 half-width character units, the value passes. This approximates text width without measuring pixels.|condition|165 half-width character units
Is a missing meta description worse than a long one?|Yes. Missing descriptions are medium, while long descriptions are low. Review the actual summary as well as its width.|reports|Missing descriptions are medium

onpage.headings
How much text can trigger the missing-subheading finding?|The test can apply from 300 words when deeper subheadings are absent. It reads markup rather than visual text size.|condition|300 words
Are identical repeated main headings treated like different main headings?|No. Copies containing the same main-heading text are handled differently. Review the actual outline before removing template elements.|pages|same main-heading text
How serious is skipping straight to a third-level heading?|A third-level heading without a second-level heading can produce a skipped-level notice. Missing main headings have a separate result.|condition|skipped-level notice

onpage.images
How many images without dimensions trigger the image-markup finding?|At least 3 images lacking saved dimensions are enough. This count is separate from the lazy-loading test.|condition|3 images
Does an intentionally empty alt attribute count as missing alternative text?|No. Intentionally empty alt text passes the presence test. A person still needs to decide whether the image is decorative.|condition|Intentionally empty alt text
How many images are needed before absent lazy loading is reported?|The page needs 8 images or more, without any marked lazy. Review prominent images before delaying their loading.|condition|8 images

onpage.lang
Is a missing viewport treated more seriously than a missing language value?|Yes. A missing viewport gets a high-severity finding. Missing language has a low result in this presence check.|condition|high-severity finding
Does a nonempty language declaration prove it names the right language?|No. Presence of a nonempty value clears this test. Text-language clues are compared by another check.|condition|nonempty value
Can viewport markup be present while mobile layout is still broken?|Yes. A viewport declaration can exist despite mobile problems. Review the narrow-screen layout in a browser.|reports|mobile problems

onpage.title
What counts as a short page title?|A title is short under 25 half-width character units. Wide and fullwidth characters count twice, with other characters counted once.|condition|25 half-width character units
Is a title width of 65 units too long?|No. Exactly 65 half-width character units passes. A plain character count can differ when the title includes wide characters.|condition|65 half-width character units
Is a missing page title worse than a long one?|Yes. Missing titles are high severity; a long title has low severity. A short title or repeated keyword gets medium severity.|reports|Missing titles are high severity

perf.cls_risk
How many images are needed for the markup-based layout-shift risk check?|The minimum is 3 images with URLs after tracking-image exclusions. Missing dimensions must also pass the share and template guards.|condition|3 images with URLs
Does a missing-dimensions share of 0.6 trigger layout-shift risk?|No. The share must be greater than 0.6. A qualifying image outside the shared template is also required.|condition|0.6
Does the image layout-shift check measure a browser CLS score?|No. It reports a medium severity markup risk. Actual movement and the browser score need separate measurement.|reports|medium severity

perf.compression
How large must HTML be for the missing-compression finding?|The successful response must exceed 20000 HTML bytes. Missing encoding alone is not enough if a separate compression result exists.|condition|20000 HTML bytes
Can a separate encoding probe prevent a false missing-compression claim?|Yes. Any nonempty separate compression result prevents that finding. The server may compress only for a different requested encoding.|condition|separate compression result
Is absent compression as minor as missing cache headers?|No. Missing compression is high severity. Widespread absent cache headers receive low severity.|reports|high severity

perf.modern_images
How many older-format images trigger the modern-image check?|The minimum is 4 remaining images after checking for newer alternatives. Fewer qualifying images do not reach the page finding.|condition|4 remaining images
Can a JPEG image with a newer source alternative be excluded?|Yes. A JPEG or PNG image can be left out when a modern alternative is recognised. Review the actual delivered picture separately.|condition|JPEG or PNG
Does the image-format check calculate the bytes a conversion would save?|No. Transfer size is not measured. Image URLs and newer-format alternatives supply the comparison.|pages|transfer size

perf.page_weight
What counts as a very large HTML document in this audit?|A successful page above 400000 HTML bytes enters the larger-document group. Separate page resources are outside this HTML-size measure.|condition|400000 HTML bytes
Is an HTML document of exactly 400000 bytes in the larger group?|No. Exactly 400000 HTML bytes stays moderate. The larger group requires a strict excess over the limit.|condition|400000 HTML bytes
How small can HTML be and still enter the moderate-weight group?|Moderate documents must exceed 150000 HTML bytes. A qualifying site's share of moderate pages can affect the lower-severity result.|condition|150000 HTML bytes

perf.redirect_cost
Can exactly five redirected pages trigger the redirect-volume finding?|No. The count must exceed a threshold of at least 5 pages. Larger crawls can raise the limit through the share rule.|condition|5 pages
Does the redirect-cost check add up network delay?|No. It counts the saved redirect chain entries rather than adding network timings. Measure response time separately to quantify delay.|condition|network timings
How serious is a high volume of redirected crawl requests?|It has low severity. A high count can reflect the crawl's starting addresses as well as outdated links.|reports|low severity

perf.render_blocking
How many blocking files trigger the resource-count finding?|At least 5 blocking resources on a successful page qualifies. Saved flags determine which files enter that count.|condition|5 blocking resources
Does a blocking-resource finding mean every listed file should be delayed?|No. Some blocking files are needed for initial display. Review the first useful view before changing their loading order.|reports|initial display
Does the blocking-file check time the delay from each request?|No. Display time is not measured for each file. The medium result uses saved blocking flags as a review prompt.|pages|display time

perf.ttfb
Is a first-response median of 0.8 seconds too slow?|No. At 0.8 seconds, the site median stays within the fast group. Individual slower pages can still qualify for an outlier result.|condition|0.8 seconds
When can a slow first response get medium rather than high severity?|A first median exceeding 1.8 seconds gets medium severity if the repeat median does not exceed 0.8 seconds. Otherwise it gets high.|condition|1.8 seconds
How many response-time samples does the TTFB check need?|The minimum is 3 positive response-time samples. They must come from successful pages; zero or missing timings do not fill the sample.|condition|3 positive response-time samples

schema.incomplete
Can a schema property be present and still count as missing?|Yes. Empty strings, lists and objects leave a required field unfilled. A property name cannot provide the missing value.|condition|Empty strings, lists and objects
Does the incomplete-schema check resolve same-page identifier references?|Yes. The check resolves same-page identifier definitions first. A reference with no definition can still leave a required-field gap.|condition|Same-page identifier definitions
How serious is an incomplete supported schema type?|It receives medium severity. The required-property table covers supported types rather than every schema vocabulary or display feature.|reports|medium severity

schema.invalid
Are JSON-LD syntax errors more serious than leftover CDATA wrappers?|Yes. Syntax failures get high severity. Leftover CDATA wrappers and template tags receive medium results.|reports|high severity
How long can an identity field be for the unfilled-template check?|The identity value can reach a 300-character limit in that test. Longer brace-containing strings are left out of this comparison.|condition|300-character
Can valid JSON-LD still contain unfinished template values?|Yes. Readable blocks are checked for unfilled template tags. Syntax validity alone does not ensure the declared value was filled.|condition|unfilled template tags

schema.mismatch
Can the rating-visibility check use saved browser output?|Yes. The check can search saved browser output when initial text has no rating wording. That can reveal reviews supplied by scripts.|condition|saved browser output
Is a rating definitely hidden if browser output was never obtained?|No. The result stays unknown when loaded output is unavailable. A notice preserves that limit instead of confirming hidden ratings.|condition|result stays unknown
How serious is a confirmed rating absent from the loaded page?|The result gets high severity when the loaded comparison confirms the absence. Also verify that the rating describes the right reviewed item.|reports|high severity

schema.missing
Can missing breadcrumbs be reported on a small schema sample?|The count must reach 5 indexable pages lacking breadcrumbs. Smaller sets do not reach that finding.|condition|5 indexable pages
Does markup coverage of 0.4 trigger the partial-coverage finding?|No. The partial-coverage comparison applies below 0.4 and above zero. Equality stays outside that result.|condition|0.4
Is identity markup built only by scripts treated like served identity?|No. The report rates script-only identity medium, with a separate explanation for absence. Served JSON-LD and microdata are also recognised.|reports|script-only identity medium

schema.opportunity
How many question headings suggest an FAQ markup opportunity?|At least 3 headings must be recognised as questions. Their answers should already belong to the page before markup is added.|condition|3 headings
Are pages that already declare FAQPage included in the opportunity check?|No. Declaring FAQPage takes a page out of the sample. Remaining pages are checked for potential declarations.|condition|declaring FAQPage
Can a question linked elsewhere be navigation rather than an FAQ answer?|Yes. An onward question link may be navigation. Confirm that the answer really belongs to this page before adding FAQ markup.|condition|may be navigation

schema.price
Are zero-only price declarations included in the visible-price test?|No. Zero-only declarations are excluded. The comparison uses supported price and offer objects with qualifying amounts.|condition|Zero-only declarations are excluded
Can browser text satisfy the declared-price visibility check?|Yes. The comparison searches saved browser text if page text has no matching amount. Missing browser output leaves visibility unknown.|condition|saved browser text
Does a matching price amount prove the whole offer is accurate?|No. Currency, availability and any terms still need review. A numeric match does not establish the complete offer's accuracy.|reports|any terms

security.headers
Can a meta referrer declaration satisfy the referrer-policy check?|Yes. The first 25 successful pages are searched for a nonempty meta referrer value. That can satisfy the policy-presence test.|condition|25 successful pages
Is missing HSTS always reported when no header is saved?|No. A final-host suffix in the source's preload list gets a pass for that case. Check the actual host and policy separately.|condition|preload list
Does passing the header check mean the application is fully secure?|No. It is a focused configuration check. The result cannot complete a broader application security assessment.|reports|focused configuration check

security.https
How soon before certificate expiry does the HTTPS check report a finding?|It reports fewer than 21 days remaining. Expiry with fewer than 7 days left is high, with the remaining reported window medium.|condition|21 days
Is a certificate with seven days left in the high-expiry group?|No. Exactly 7 days remaining stays medium. The high group requires less time than that.|condition|7 days
Does an unavailable certificate probe mean the certificate is invalid?|No. The report calls unknown results notices. An uncompleted test does not establish validity or invalidity.|reports|unknown results notices

security.mixed_content
Are insecure scripts treated more seriously than insecure images?|Yes. Scripts and other active resources get high severity. An image-only case receives medium.|reports|high severity
Which resource types are checked for mixed content?|The scanned types are images, scripts, stylesheets and frames using HTTP addresses on successful secure pages. Saved markup supplies the resource addresses.|condition|images, scripts, stylesheets and frames
Does the mixed-content check also run on an HTTP-only site?|No. Only HTTPS sites enter the check. It looks for insecure resources within that secure-page context.|condition|HTTPS sites

social.favicon
Does an unknown favicon probe mean the icon is missing?|No. An unknown result is kept separate from a confirmed absence. The missing-icon finding needs both saved flags to support that claim.|condition|unknown result
How serious is a confirmed missing favicon?|It receives low severity. Check the actual icon request separately from a cached tab image.|reports|low severity
Does the icon check inspect the artwork shown in my browser tab?|No. Browser tabs and icon formats are outside this file-presence test. A successful probe does not judge the design.|condition|Browser tabs

social.open_graph
Can an Open Graph image error be reported without a dead page?|Yes. HTTP status 400 or higher can establish a dead preview image once refusals are excluded. Its page can still respond successfully.|condition|HTTP status 400
Are missing Open Graph descriptions as serious as dead preview images?|No. The report rates dead images medium. Missing descriptions receive notices, and most other missing fields are low.|reports|dead images medium
Does finding Open Graph tags guarantee the current sharing preview?|No. A cached preview can be stale despite correct metadata. The check cannot promise a service's current display.|reports|cached preview

social.twitter
Does a missing-card share of 0.5 trigger the Twitter card finding?|No. The missing-card share must exceed 0.5. An indexable page with an Open Graph title is also required.|condition|0.5
Can a page have Twitter preview fields but still lack a card type?|Yes. The check distinguishes other Twitter fields from a missing card type. That allows a narrower explanation without claiming all preview tags are absent.|condition|other Twitter fields
Is a missing twitter:card declaration treated as a serious error?|It is only a notice. A card-type value that is nonempty clears the presence comparison. Other preview details still need review.|reports|card-type value
""")


def catalogue() -> list[dict]:
    with (ROOT / "data/checks.csv").open() as handle:
        return list(csv.DictReader(handle))


def registry() -> dict:
    paths = subprocess.run(["git", "-C", str(ENGINE), "ls-tree", "-r", "--name-only",
                            REVISION, CHECKS], check=True, capture_output=True, text=True).stdout
    found = {}
    for path in paths.splitlines():
        if not path.endswith(".py"):
            continue
        tree, _, _ = module(path)
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and expression(decorator.func) == "register":
                    key = ast.literal_eval(decorator.args[0])
                    found[key] = (path, node)
    return found


def existing_pages(site: Path) -> dict[str, str]:
    """All ownership candidates, including the crawler reference pages."""
    paths = []
    for section in ("learn", "how-to", "ai-crawlers"):
        paths.extend((site / section).rglob("*.html"))
    return {"/" + path.parent.relative_to(site).as_posix() + "/": path.read_text()
            for path in sorted(paths)}


def faq(row: dict) -> list[tuple[str, str]]:
    return [(item["question"], item["answer"]) for item in row["faq"]]


def body(row: dict) -> str:
    e = escape
    fields = row["field_audits"]
    # Area evidence is deliberately never described as a count for this check.
    field_note = (f'<p>Problems in {e(row["lane_label"])} were found on '
                  f'{fields["found"]} of the {fields["sites"]} sites we audited. '
                  'These are area totals. '
                  '<a href="/learn/audit-tool-accuracy/">Read the field-audit method</a>.</p>')
    source = row["source"]
    related = (f'<p><a href="{e(row["guide"])}">{e(row["guide_title"])}</a></p>'
               if row["guide"] else "")
    return (f'<p class="lede">{e(row["answer"])}</p>'
            '<h2>What Check Engine measures</h2>'
            f'<p>{e(row["condition"]["text"])}</p>'
            f'<p>{e(row["pages"]["text"])}</p>'
            '<h2>How to read the result</h2>'
            f'<p>{e(row["reports"]["text"])}</p>'
            '<h2>Why it matters</h2>'
            f'<p>{e(row["why"])}</p>'
            '<h2>How to fix it</h2>'
            f'<p>{e(row["fix"]["text"])}</p>' + related +
            '<h2>What we found in field audits</h2>' + field_note +
            '<h2>Method note</h2>'
            f'<p><code>{e(source["file"])}</code>, '
            f'<code>{e(source["function"])}</code>, '
            f'revision <code>{REVISION[:8]}</code>.</p>')


def next_step(tag: str) -> str:
    """Place the shared next step at the end, as on the AI-crawler pages."""
    result = with_next_step("", tag)
    result = re.sub(r'<p class="hero-note price-anchor">.*?</p>', '', result, flags=re.S)
    return '<footer aria-label="Next step">' + result + '</footer>'


def draft(row: dict) -> str:
    questions = "".join(f"<h3>{q}</h3><p>{a}</p>" for q, a in faq(row))
    return f'<h1>{escape(row["question"])}</h1>{body(row)}<h2>Questions</h2>{questions}'


def owner_for(raw: str, candidates: dict[str, set[str]]) -> tuple[str | None, float]:
    own = shingles(visible(raw))
    # Stable ties: highest score, then lexicographically first URL.
    scores = sorted(((jaccard(own, other), url) for url, other in candidates.items()),
                    key=lambda item: (-item[0], item[1]))
    score, url = scores[0] if scores else (0.0, None)
    return (url if score >= 0.5 else None), score


def presentation_numbers() -> dict:
    """Read shared prices, dates and footer numbers from the existing renderer.

    These are UI facts, not check thresholds. Render an empty article in a
    temporary directory so the inventory cannot launder a number in our copy.
    """
    import render as shell

    with tempfile.TemporaryDirectory(prefix="check-reference-shell-") as directory:
        with patch.object(shell, "SITE", Path(directory)):
            path = render(
                cat="checks", slug="shell", title="Check reference", desc="Check reference",
                h1="Check reference", crumb="Checks",
                body="<p>Check reference.</p>", closer=next_step("check-reference-shell"),
                published="2026-11-11",
            )
        text = visible(path.read_text(), include_chrome=True)
    # Include both offer states, so expiration alone cannot change the dataset.
    for field in ("FOUNDING_NOW", "FOUNDING_END_DAY", "FOUNDING_AFTER_DAY"):
        text += " " + str(getattr(shell, field))
    return {"numbers": sorted({n.replace(",", "") for n in NUMBER.findall(text)}),
            "source": {"file": "scripts/render.py", "function": "render and with_next_step"},
            "scope": "shared UI only, not check thresholds"}


def derive_data(site: Path | None = None) -> dict:
    rows = catalogue()
    registered = registry()
    if (set(COPY) != {row["id"] for row in rows} or set(REVIEW) != set(COPY)
            or set(FAQ) != set(COPY)):
        raise ValueError(f"Copy/catalogue mismatch: {set(COPY) ^ {r['id'] for r in rows}}; "
                         f"review mismatch: {set(REVIEW) ^ set(COPY)}")
    audits = json.loads((ROOT / "data/field-audits.json").read_text())
    guides = existing_pages(site or ROOT / "site")
    candidates = {url: shingles(visible(raw)) for url, raw in guides.items()}
    if not candidates:
        raise ValueError("Build existing learn, how-to and AI-crawler pages before deriving ownership")
    result = []
    presentation = presentation_numbers()
    for item in rows:
        path, function = registered[item["id"]]
        declaration = next(d for d in function.decorator_list if isinstance(d, ast.Call)
                           and expression(d.func) == "register")
        engine_title = ast.literal_eval(declaration.args[2])
        engine_lane = declaration.args[1].attr.lower()
        if (item["title"], item["lane"]) != (engine_title, engine_lane):
            raise ValueError(f"Catalogue differs from the pinned registration: {item['id']}")
        source = origin(path, function.name, function)
        wording = COPY[item["id"]]
        row = {**item, "slug": item["id"].replace(".", "-").replace("_", "-"),
               "source": source, "evidence": evidence(path, function),
               "presentation": presentation,
               **{key: wording[key] for key in ("question", "answer", "why", "guide")}}
        for key in ("condition", "pages", "reports", "fix"):
            row[key] = {"text": wording[key], "source": source}
        guide = row["guide"]
        heading = re.search(r'<h1\b[^>]*>(.*?)</h1>', guides.get(guide, ""), re.S)
        row["guide_title"] = (visible(heading[1])
                              if heading and guide.startswith(("/how-to/", "/learn/")) else "")
        if not row["guide_title"]:
            row["guide"] = ""
        row["review"] = {"text": REVIEW[item["id"]], "source": source}
        row["faq"] = copy.deepcopy(FAQ[item["id"]])
        for entry in row["faq"]:
            entry["fact"]["source"] = source
        row["severity"] = [{"expression": finding["severity"], "source": finding["source"]}
                           for finding in row["evidence"]["findings"]]
        row["field_audits"] = {
            "found": sum(a.get("by_area", {}).get(item["lane_label"], 0) > 0
                         for a in audits["audits"]),
            "sites": audits["sites"], "source": "data/field-audits.json",
            "scope": "area only, not this check"}
        row["owner"], score = owner_for(draft(row), candidates)
        row["ownership_jaccard"] = round(score, 8)
        row["publish"] = row["owner"] is None
        result.append(row)
    return {"source_revision": REVISION, "published": "2026-11-11",
            "method": "AST evidence and reviewed explanations; five-word Jaccard on article text, cutoff 0.5",
            "rows": result}


def encoded(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def check_page(row: dict) -> Path:
    return render(
        cat="checks", slug=row["slug"], title=row["question"], h1=row["question"],
        desc=row["answer"],
        crumb='<a href="/">Check Engine</a> / <a href="/checks/">Checks</a> / Reference',
        body=body(row), closer=next_step("check-" + row["slug"]),
        faq=faq(row), published="2026-11-11",
    )


def index_page(rows: list[dict]) -> Path:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["lane_label"]].append(row)
    sections = []
    for label, items in grouped.items():
        links = []
        for row in items:
            href = row["owner"] or f'/checks/{row["slug"]}/'
            links.append(f'<li><a href="{escape(href)}">{escape(row["title"])}</a>: '
                         f'{escape(row["answer"])}</li>')
        sections.append(f'<h2>{escape(label)}</h2><ul>{"".join(links)}</ul>')
    intro = ('<p class="lede">Find what each Check Engine test reads, what it reports '
             'and what to review before changing your site.</p>'
             '<p>Choose an area below, then open a check. Each reference explains the '
             'test rules, sample limits and severity. When an existing guide '
             'already owns the same explanation, the link leads to that guide.</p>'
             '<p>Findings describe what the audit could check. A missing '
             'measurement is different from a measured problem. Read the scope and '
             'the saved example before deciding which fix applies.</p>')
    return render(
        cat="checks", slug="", title="What does each Check Engine check measure?",
        desc="Every Check Engine check, grouped by area, with measured conditions, source limits and practical next steps.",
        h1="What does each check measure?", crumb='<a href="/">Check Engine</a> / Checks',
        body=intro + "".join(sections), closer=next_step("checks-index"),
        schema_type="CollectionPage", published="2026-11-11",
    )


def build_all() -> list[Path]:
    rows = F.check_pages()["rows"]
    return [index_page(rows)] + [check_page(row) for row in rows if row["publish"]]


def report(site: Path | None = None) -> None:
    """Print the requested review figures; never write a report in the repo."""
    data = F.check_pages()
    rows = data["rows"]
    published = [r for r in rows if r["publish"]]
    print(f"Check pages built: {len(published)}; index pages: 1")
    print("Checks skipped as owned:")
    for row in rows:
        if not row["publish"]:
            print(f'  {row["id"]} -> {row["owner"]} ({row["ownership_jaccard"]:.6f})')
    if all(r["publish"] for r in rows):
        print("  none reached the requested 0.5 cutoff")
    site = site or ROOT / "site"
    pages = {}
    for path in sorted(site.rglob("*.html")):
        rel = path.relative_to(site).as_posix()
        if rel.startswith("checks/") and rel != "checks/index.html":
            continue
        url = "/" + (rel.removesuffix("index.html") if path.name == "index.html" else rel)
        pages[url] = shingles(visible(path.read_text()))
    shortest = []
    best = (0.0, "", "")
    for row in published:
        url = f'/checks/{row["slug"]}/'
        built = site / "checks" / row["slug"] / "index.html"
        raw = built.read_text() if built.exists() else draft(row)
        tokens = shingles(visible(raw))
        for other, values in pages.items():
            score = jaccard(tokens, values)
            if score > best[0]:
                best = (score, url, other)
        pages[url] = tokens
        shortest.append((len(visible(raw).split()), url))
    print(f"Highest five-word Jaccard: {best[0]:.6f} {best[1]} ~ {best[2]}")
    print("Five shortest check pages, visible article words:")
    for count, url in sorted(shortest)[:5]:
        print(f"  {count} {url}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.write or args.check:
        wanted = encoded(derive_data())
        if args.write:
            OUTPUT.write_text(wanted)
            print(f"wrote {OUTPUT.relative_to(ROOT)}")
        elif not OUTPUT.exists() or OUTPUT.read_text() != wanted:
            print("Check reference is stale; run scripts/articles/check_pages.py --write", file=sys.stderr)
            return 1
        else:
            print("PASS: source evidence, copy and ownership match the pinned inputs")
    if args.report:
        report()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

