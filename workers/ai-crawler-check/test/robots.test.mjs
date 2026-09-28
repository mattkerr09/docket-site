// node --test workers/ai-crawler-check/test/
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { evaluate, parseRobots, truncateAgent } from '../src/robots.js'

const may = (text, agent, path) => evaluate(parseRobots(text), agent, path).allowed

// The example file in RFC 9309 §5.1, with the outcomes the RFC gives for it.
const RFC = `User-Agent: *
Disallow: *.gif$
Disallow: /example/
Allow: /publications/

User-Agent: foobot
Disallow:/
Allow:/example/page.html
Allow:/example/allowed.gif

User-Agent: barbot
User-Agent: bazbot
Disallow: /example/page.html

User-Agent: quxbot

EOF`

test('RFC 9309 §5.1: foobot may fetch only what its group allows', () => {
  assert.equal(may(RFC, 'foobot', '/example/page.html'), true)
  assert.equal(may(RFC, 'foobot', '/example/allowed.gif'), true)
  assert.equal(may(RFC, 'foobot', '/'), false)
  assert.equal(may(RFC, 'foobot', '/publications/'), false)
})

test('RFC 9309 §5.1: consecutive user-agent lines share one group', () => {
  for (const bot of ['barbot', 'bazbot']) {
    assert.equal(may(RFC, bot, '/example/page.html'), false)
    assert.equal(may(RFC, bot, '/example/other.gif'), true, `${bot} is not governed by *`)
  }
})

test('RFC 9309 §5.1: a named group with no rules allows everything, not the * rules', () => {
  assert.equal(may(RFC, 'quxbot', '/example/x'), true)
  assert.equal(evaluate(parseRobots(RFC), 'quxbot', '/').named, true)
})

test('an unnamed crawler falls back to *', () => {
  assert.equal(may(RFC, 'GPTBot', '/example/x'), false)
  assert.equal(may(RFC, 'GPTBot', '/publications/x'), true)
  assert.equal(may(RFC, 'GPTBot', '/pic.gif'), false)
  assert.equal(may(RFC, 'GPTBot', '/pic.gif?x=1'), true, '$ anchors the end')
  assert.equal(evaluate(parseRobots(RFC), 'GPTBot', '/').governedBy, 'wildcard')
})

test('agent names match case-insensitively', () => {
  assert.equal(may('User-agent: gptbot\nDisallow: /', 'GPTBot', '/'), false)
  assert.equal(may('User-agent: GPTBOT\nDisallow: /', 'gptbot', '/'), false)
})

test('the longest match wins, and Allow wins a tie', () => {
  const t = 'User-agent: *\nDisallow: /\nAllow: /page\nDisallow: /folder\nAllow: /folder'
  assert.equal(may(t, 'x', '/page'), true)
  assert.equal(may(t, 'x', '/other'), false)
  assert.equal(may(t, 'x', '/folder/a'), true)
})

test('an empty Disallow blocks nothing', () => {
  assert.equal(may('User-agent: *\nDisallow:', 'GPTBot', '/'), true)
})

test('a comment between rules does not end the group (docket-app robots.py, a government portal)', () => {
  const t = 'User-agent: *\nDisallow: /*/print$\n# Don\'t allow indexing of site search\nDisallow: /search/all*'
  assert.equal(may(t, 'x', '/search/all'), false)
})

test('two * groups are one set of rules (a CDN-managed block above the site\'s own)', () => {
  const t = '# BEGIN Cloudflare Managed content\nUser-agent: *\nAllow: /\n# END\n\nUser-agent: *\nDisallow: /core/'
  assert.equal(may(t, 'x', '/core/x'), false)
  assert.equal(may(t, 'x', '/'), true)
})

test('two groups naming one crawler are merged', () => {
  const t = 'User-agent: GPTBot\nDisallow: /a/\n\nUser-agent: GPTBot\nDisallow: /b/'
  assert.equal(may(t, 'GPTBot', '/a/x'), false)
  assert.equal(may(t, 'GPTBot', '/b/x'), false)
})

test('a written value is cut at the first character outside [A-Za-z_-], as Google does', () => {
  assert.equal(truncateAgent('ChatGPT-User/2.0'), 'ChatGPT-User')
  assert.equal(may('User-agent: ChatGPT-User/2.0\nDisallow: /', 'ChatGPT-User', '/'), false)
  // U+2011 non-breaking hyphen: the rule addresses "perplexity", nobody's name.
  const t = 'User-agent: perplexity‑user\nDisallow: /'
  assert.equal(may(t, 'Perplexity-User', '/'), true)
})

test('rules before any user-agent line are ignored, and said so', () => {
  const p = parseRobots('Disallow: /\nUser-agent: *\nAllow: /')
  assert.equal(evaluate(p, 'GPTBot', '/').allowed, true)
  assert.match(p.warnings[0], /before any User-agent/)
})

test('percent-encoding and raw UTF-8 compare equal', () => {
  assert.equal(may('User-agent: *\nDisallow: /caf%c3%a9', 'x', '/café'), false)
  assert.equal(may('User-agent: *\nDisallow: /café', 'x', '/caf%C3%A9'), false)
})

test('CRLF files, a BOM, and Sitemap lines', () => {
  const p = parseRobots('﻿User-agent: *\r\nDisallow: /x\r\nSitemap: https://a.test/s.xml\r\n')
  assert.equal(evaluate(p, 'x', '/x').allowed, false)
  assert.deepEqual(p.sitemaps, ['https://a.test/s.xml'])
})

test('no robots rules at all means everything is allowed', () => {
  assert.equal(may('', 'GPTBot', '/'), true)
  assert.equal(evaluate(parseRobots(''), 'GPTBot', '/').governedBy, 'none')
})
