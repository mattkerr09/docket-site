"""robots.txt parsing to RFC 9309 / Google's spec.

`urllib.robotparser` is not usable for an audit: it has no `*`/`$` wildcard
support, resolves Allow-vs-Disallow by rule *order* instead of by longest match,
and drops Sitemap lines. Each of those produces confidently wrong answers — the
common "Disallow: /wp-admin/ + Allow: /wp-admin/admin-ajax.php" pair alone gets
misjudged — so an audit tool has to bring its own.

Rules implemented here, in the order they decide an outcome:
  1. Group lines by the user-agent block they belong to.
  2. Pick the most specific matching group: exact UA substring match beats `*`.
     A UA matching several named groups takes the longest name.
  3. Within the group, the longest matching path pattern wins.
  4. Tie between an Allow and a Disallow of equal length: Allow wins.
  5. No matching rule: allowed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

#: Crawlers whose access decides whether a business shows up in AI answers.
#: Split by what blocking each one actually costs, because site owners routinely
#: block the training bots on purpose and should not be told that is a bug.
AI_USER_AGENTS: Dict[str, Dict[str, str]] = {
    "GPTBot": {
        "owner": "OpenAI",
        "purpose": "training",
        "impact": "Blocks OpenAI from training on your content. Does not affect "
                  "whether ChatGPT can cite you live.",
    },
    "OAI-SearchBot": {
        "owner": "OpenAI",
        "purpose": "search index",
        "impact": "Blocks your pages from ChatGPT Search results entirely.",
    },
    "ChatGPT-User": {
        "owner": "OpenAI",
        "purpose": "live fetch",
        "impact": "Stops ChatGPT fetching your page when a user asks about you.",
    },
    "ClaudeBot": {
        "owner": "Anthropic",
        "purpose": "training",
        "impact": "Blocks Anthropic from training on your content.",
    },
    "Claude-SearchBot": {
        "owner": "Anthropic",
        "purpose": "search index",
        "impact": "Blocks your pages from Claude's search results.",
    },
    "Claude-User": {
        "owner": "Anthropic",
        "purpose": "live fetch",
        "impact": "Stops Claude fetching your page on a user's behalf.",
    },
    "PerplexityBot": {
        "owner": "Perplexity",
        "purpose": "search index",
        "impact": "Removes you from Perplexity's index and citations.",
    },
    "Perplexity-User": {
        "owner": "Perplexity",
        "purpose": "live fetch",
        "impact": "Stops Perplexity fetching your page on a user's behalf.",
    },
    "Google-Extended": {
        "owner": "Google",
        "purpose": "Gemini grounding",
        "impact": "Removes you from Gemini and AI Overviews grounding. Does NOT "
                  "affect classic Google Search ranking.",
    },
    "Applebot-Extended": {
        "owner": "Apple",
        "purpose": "training",
        "impact": "Blocks Apple Intelligence training. Applebot (search) is separate.",
    },
    "Amazonbot": {
        "owner": "Amazon",
        "purpose": "search index",
        "impact": "Blocks Alexa and Amazon's answer surfaces.",
    },
    "Bytespider": {
        "owner": "ByteDance",
        "purpose": "training",
        "impact": "Blocks ByteDance/TikTok AI crawling.",
    },
    "meta-externalagent": {
        "owner": "Meta",
        "purpose": "training",
        "impact": "Blocks Meta AI training and grounding.",
    },
    "CCBot": {
        "owner": "Common Crawl",
        "purpose": "open corpus",
        "impact": "Removes you from Common Crawl, an input to many open models.",
    },
}

#: The search crawlers whose access is non-negotiable — blocking any of these is
#: a critical finding, not a policy choice.
SEARCH_USER_AGENTS = ("Googlebot", "Bingbot", "DuckDuckBot", "Applebot")


def _pattern_to_regex(pattern: str) -> re.Pattern:
    """Compile a robots path pattern. `*` = any run, `$` = end anchor.

    Everything else is escaped, so a literal `?` or `.` in a path — extremely
    common in query strings — cannot act as a regex metacharacter.
    """
    out = ["^"]
    i = 0
    end_anchored = pattern.endswith("$")
    body = pattern[:-1] if end_anchored else pattern
    while i < len(body):
        ch = body[i]
        if ch == "*":
            out.append(".*")
        else:
            out.append(re.escape(ch))
        i += 1
    if end_anchored:
        out.append("$")
    try:
        return re.compile("".join(out))
    except re.error:
        return re.compile("^(?!)")  # never matches


@dataclass
class Rule:
    allow: bool
    pattern: str
    regex: re.Pattern = field(init=False)

    def __post_init__(self) -> None:
        self.regex = _pattern_to_regex(self.pattern)

    @property
    def length(self) -> int:
        """Specificity for longest-match. `$` is an anchor, not a matched char."""
        return len(self.pattern.rstrip("$"))


@dataclass
class Group:
    agents: List[str] = field(default_factory=list)
    rules: List[Rule] = field(default_factory=list)
    crawl_delay: Optional[float] = None


class RobotsTxt:
    """A parsed robots.txt. Construct from text; `allowed()` answers queries."""

    def __init__(self, text: str = "", status: int = 200, url: str = "") -> None:
        self.text = text or ""
        self.status = status
        self.url = url
        self.groups: List[Group] = []
        self.sitemaps: List[str] = []
        self.parse_errors: List[str] = []
        self._parse()

    # ------------------------------------------------------------------ parse
    def _parse(self) -> None:
        current: Optional[Group] = None
        # A blank line ends a group, but consecutive `User-agent:` lines *extend*
        # it — that is how one rule block applies to several bots, and treating
        # each as a fresh group would silently drop the rules from all but the last.
        expecting_agents = False

        for raw_line in self.text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                current = None
                expecting_agents = False
                continue
            if ":" not in line:
                self.parse_errors.append(f"malformed line: {raw_line.strip()[:80]}")
                continue

            field_name, _, value = line.partition(":")
            key = field_name.strip().lower()
            value = value.strip()

            if key == "user-agent":
                if current is None or not expecting_agents:
                    current = Group()
                    self.groups.append(current)
                    expecting_agents = True
                current.agents.append(value.lower())
                continue

            if key == "sitemap":
                if value:
                    self.sitemaps.append(value)
                continue

            if current is None:
                # Rules before any User-agent line belong to no group. Google
                # ignores them; record it so the check can say so.
                self.parse_errors.append(
                    f"'{field_name.strip()}' appears before any User-agent line and is ignored"
                )
                continue

            expecting_agents = False

            if key == "disallow":
                # "Disallow:" with an empty value means allow-everything, and is
                # NOT the same as "Disallow: /". Modelling it as a zero-length
                # rule would make it lose every longest-match comparison, which
                # is the correct behaviour.
                current.rules.append(Rule(allow=False, pattern=value))
            elif key == "allow":
                current.rules.append(Rule(allow=True, pattern=value))
            elif key == "crawl-delay":
                try:
                    current.crawl_delay = max(0.0, float(value))
                except ValueError:
                    self.parse_errors.append(f"invalid crawl-delay: {value[:40]}")

    # ------------------------------------------------------------------ query
    def _group_for(self, user_agent: str) -> Optional[Group]:
        ua = (user_agent or "").lower()
        best: Optional[Group] = None
        best_len = -1
        wildcard: Optional[Group] = None

        for group in self.groups:
            for agent in group.agents:
                if agent == "*":
                    if wildcard is None:
                        wildcard = group
                    continue
                # Google matches on substring, case-insensitively: a group named
                # "googlebot" governs "Googlebot-Image/1.0".
                if agent and agent in ua and len(agent) > best_len:
                    best, best_len = group, len(agent)
        return best or wildcard

    def allowed(self, path: str, user_agent: str = "*") -> bool:
        """Is `path` (a path+query, or a full URL) crawlable by `user_agent`?"""
        # An unreachable robots.txt (5xx / connection failure) means "assume
        # disallowed" per spec; a 404 means "no restrictions".
        if self.status >= 500 or self.status == 0:
            return False
        if not self.text.strip():
            return True

        if path.startswith(("http://", "https://")):
            parsed = urlparse(path)
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
        if not path.startswith("/"):
            path = "/" + path

        group = self._group_for(user_agent)
        if group is None:
            return True

        # Match against both the raw and percent-decoded path: sites disallow
        # "/private" while linking "/priv%61te", and the spec resolves on the
        # decoded form.
        candidates = {path}
        try:
            candidates.add(unquote(path))
        except Exception:  # noqa: BLE001 — undecodable path just uses the raw form
            pass

        best: Optional[Rule] = None
        for rule in group.rules:
            if not rule.pattern:
                continue  # "Disallow:" (empty) never matches anything
            if any(rule.regex.match(c) for c in candidates):
                if (
                    best is None
                    or rule.length > best.length
                    or (rule.length == best.length and rule.allow and not best.allow)
                ):
                    best = rule

        return True if best is None else best.allow

    def crawl_delay(self, user_agent: str = "*") -> Optional[float]:
        group = self._group_for(user_agent)
        return group.crawl_delay if group else None

    def ai_access(self) -> Dict[str, bool]:
        """Whether each known AI crawler may fetch the site root."""
        return {name: self.allowed("/", name) for name in AI_USER_AGENTS}

    def search_access(self) -> Dict[str, bool]:
        return {name: self.allowed("/", name) for name in SEARCH_USER_AGENTS}

    def blocks_everything(self, user_agent: str = "Googlebot") -> bool:
        """True when the site is walled off wholesale for `user_agent`."""
        return not self.allowed("/", user_agent)

    def disallowed_patterns(self, user_agent: str = "Googlebot") -> List[str]:
        group = self._group_for(user_agent)
        if not group:
            return []
        return [r.pattern for r in group.rules if not r.allow and r.pattern]


def parse_sitemap_xml(text: str) -> Tuple[List[str], List[str]]:
    """Extract (page URLs, nested sitemap URLs) from a sitemap or index.

    Regex rather than an XML parser on purpose. Real sitemaps are frequently
    served with a stray BOM, an undeclared entity, or truncated output, and
    `xml.etree` throws away the entire document on any of those — losing 40,000
    valid URLs to one bad character. This extracts what is there and moves on.
    """
    urls: List[str] = []
    sitemaps: List[str] = []

    is_index = "<sitemapindex" in text[:2000].lower()
    for match in re.finditer(r"<loc>\s*(.*?)\s*</loc>", text, re.I | re.S):
        loc = match.group(1).strip()
        loc = re.sub(r"^<!\[CDATA\[|\]\]>$", "", loc).strip()
        if not loc:
            continue
        loc = (
            loc.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&apos;", "'")
        )
        (sitemaps if is_index else urls).append(loc)

    return urls, sitemaps


def is_sitemap_index(text: str) -> bool:
    return "<sitemapindex" in text[:2000].lower()
