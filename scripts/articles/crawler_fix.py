"""Shared browser logic for fixes to blocked AI search crawlers."""

#: The crawlers the fix block speaks about. The same set the app's own finding uses
#: (docket-app ai.blocked_citation_crawlers: OAI-SearchBot, PerplexityBot, Claude-SearchBot,
#: Meta-WebIndexer) plus the three user-fetch crawlers the home result reports per assistant.
#: Training crawlers, Google-Extended and the wider search-engine list are NOT here: a snippet is
#: something people paste (CEO yes 2026-11-12: exactly the blocked AI search crawlers).
AI_SEARCH_CRAWLERS = ("OAI-SearchBot", "PerplexityBot", "Claude-SearchBot", "Meta-WebIndexer",
                      "ChatGPT-User", "Claude-User", "Perplexity-User")


def search_names(rows) -> list[str]:
    """The names from AI_SEARCH_CRAWLERS that the checker actually tests, in the page's order."""
    have = {r["name"] for r in rows}
    return [name for name in AI_SEARCH_CRAWLERS if name in have]

FIX_JS = r"""function buildCrawlerFix(results, searchNames) {
  var by = {};
  results.forEach(function (r) { by[r.agent] = r; });
  var googleBlocked = results.some(function (r) {
    return r.agent === 'Googlebot' && r.allowed === false;
  });
  var byWildcard = [];
  var byName = [];
  var byServer = [];
  searchNames.forEach(function (name) {
    var r = by[name];
    if (!r || r.allowed !== false) return;
    if (r.governedBy === 'wildcard') byWildcard.push(name);
    else if (r.governedBy === 'name') byName.push(name);
    else byServer.push(name);
  });
  var snippet = '';
  if (!googleBlocked && byWildcard.length) {
    snippet = '# Let AI search crawlers read your site (they are not training crawlers)\n' +
      byWildcard.map(function (name) { return 'User-agent: ' + name + '\nAllow: /'; }).join('\n\n');
  }
  return {googleBlocked: googleBlocked, byWildcard: byWildcard, byName: byName,
    byServer: byServer, snippet: snippet};
}"""
