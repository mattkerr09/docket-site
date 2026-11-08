import { test } from 'node:test'
import assert from 'node:assert/strict'
import { checkAccessibilityHtml, STANDARD, DISCLAIMER } from '../src/access.js'

const page = (body = '', head = '<title>Garden guide</title>', lang = 'en') => `<html lang="${lang}"><head>${head}</head><body><main>${body}</main></body></html>`
const findings = (body, sc) => checkAccessibilityHtml(page(body)).findings.filter((f) => f.sc === sc)
const count = (data, sc) => data.by_sc.find((r) => r.sc === sc).count

test('a named page with text alternatives, labels and a main landmark has no findings', () => {
  const result = checkAccessibilityHtml(page(`
    <img src="leaf.png" alt="A maple leaf"><img alt=""><input type="image" alt="Search"><area alt="Map">
    <div role="img" aria-label="Rain chart"></div><svg role="img"><title>Sun</title></svg>
    <a href="/plants"><img alt="Plants"></a><button><span>Save</span></button><iframe title="Garden video"></iframe>
    <label for="email">Email</label><input id="email">
    <label>Your name <input></label><select aria-label="Plant"><option>Maple</option></select>
    <textarea title="Notes"></textarea><input type="hidden"><input type="submit"><input type="button">
  `))
  assert.deepEqual(result.findings, [])
  assert.equal(result.by_sc.length, 9)
  assert.ok(result.by_sc.every((r) => r.level === 'A' && r.count === 0 && r.sc_name))
  assert.equal(result.limits.html_only, true)
  assert.equal(result.limits.rendering, false)
  assert.ok(result.limits.not_checked.includes('Colour contrast'))
  assert.equal(STANDARD, 'WCAG 2.1 Level A and AA')
  assert.equal(DISCLAIMER, 'Automated checks find some accessibility problems, not all. This is not legal advice and does not say whether a site meets the law.')
})

test('images, image inputs, map areas and role images need text alternatives', () => {
  const result = findings(`<img src="one"><input TYPE="IMAGE"><area href="/map"><div role="img">Chart</div>
    <img alt=""><input type="image" alt=""><area alt="">
    <div role="img" aria-label=" "></div><span role="img" aria-labelledby="missing"></span>`, '1.1.1')
  assert.equal(result.length, 6)
  assert.ok(result.every((f) => f.certainty === 'fails' && f.sc_name === 'Non-text Content' && f.level === 'A'))
  assert.ok(result.every((f) => f.element.startsWith('<') && f.problem && f.fix))
})

test('page language rejects missing, empty, malformed and unknown language tags', () => {
  for (const lang of ['', ' ', 'en_US', 'english', 'zz', 'en-', '123']) {
    assert.equal(count(checkAccessibilityHtml(page('', undefined, lang)), '3.1.1'), 1, lang)
  }
  for (const lang of ['en', 'EN-us', 'zh-Hant', 'es-419', 'fr-CA', 'eng', 'x-private', 'i-klingon']) {
    assert.equal(count(checkAccessibilityHtml(page('', undefined, lang)), '3.1.1'), 0, lang)
  }
  assert.equal(count(checkAccessibilityHtml('<head><title>Guide</title></head><main></main>'), '3.1.1'), 1)
  for (const lang of ['zzx', 'zh-cmn-Hans-CN']) {
    const result = checkAccessibilityHtml(page('', undefined, lang))
    assert.equal(count(result, '3.1.1'), 1)
    assert.equal(result.findings[0].certainty, 'needs review', 'runtime data cannot prove an unfamiliar language tag is invalid')
  }
})

test('only a nonempty page title counts, not an SVG title, comment or script', () => {
  for (const head of ['', '<title> \n &nbsp;&#32; </title>', '<script>"<title>Fake</title>"</script>']) {
    const result = checkAccessibilityHtml(page('<svg><title>Icon</title></svg>', head))
    assert.equal(count(result, '2.4.2'), 1)
  }
  assert.equal(count(checkAccessibilityHtml(page('', '<title>A &amp; B &lt;img&gt;</title>')), '2.4.2'), 0)
  assert.equal(count(checkAccessibilityHtml('<html lang="en"><title>Guide</title><main></main></html>'), '2.4.2'), 0, 'HTML may omit the head start tag')
})

test('links and buttons resolve nested text, image alt and real forward aria references', () => {
  const result = checkAccessibilityHtml(page(`
    <a href="/empty"></a><a href="/space">&nbsp;&#x20;&#8203;</a>
    <a href="/hidden"><span hidden>Hidden</span></a><a href="/decorative"><img alt=""></a>
    <a href="/broken" aria-labelledby="absent"></a><button></button><button aria-label=" "></button>
    <a href="/nested"><b>Plants</b></a><a href="/alt"><img alt="Leaves"></a>
    <a href="/aria" aria-label="Map"></a><a href="/refs" aria-labelledby="one two"></a>
    <button aria-labelledby="later"></button><span hidden id="later">Save</span>
    <span id="one"></span><span id="two">Two</span><a href="/title" title="Garden"></a>
    <a id="anchor"></a><button aria-label="Save"><img alt=""></button>
  `))
  assert.equal(count(result, '2.4.4'), 5)
  assert.equal(count(result, '4.1.2'), 2)
})

test('empty and cyclic aria references do not count as names', () => {
  const result = findings(`<button aria-labelledby="a"></button><span id="a" aria-labelledby="b"></span>
    <span id="b" aria-labelledby="a"></span><button aria-labelledby="empty"></button><span id="empty">&nbsp;</span>`, '4.1.2')
  assert.equal(result.length, 2)
  assert.equal(findings('<button aria-labelledby="missing" aria-label="Save"></button>', '4.1.2').length, 0)
})

test('iframes require nonempty titles even when they have an aria label', () => {
  assert.equal(findings('<iframe></iframe><iframe title=" "></iframe><iframe aria-label="Video"></iframe><iframe title="Map"></iframe>', '4.1.2').length, 3)
})

test('form labels must have text and connect to the right field; values and placeholders do not label fields', () => {
  const result = checkAccessibilityHtml(page(`
    <input placeholder="Name"><input value="Name"><input aria-label=" "><select><option>Maple</option></select>
    <textarea>Notes</textarea><label for="no-text"></label><input id="no-text">
    <label for="other">Wrong <input id="wrong"></label><input aria-labelledby="missing">
    <label><textarea>Not a label</textarea></label>
    <label for="good">Good</label><input id="good"><label>Also good <input></label>
    <input aria-labelledby="after"><span id="after">Name</span><textarea title="Notes"></textarea>
    <select aria-label="Plant"></select><input type="HIDDEN"><input type="SUBMIT"><input type="BUTTON"><input type="IMAGE" alt="Save">
  `))
  assert.equal(count(result, '1.3.1'), 9)
  assert.equal(count(result, '3.3.2'), 9)
  assert.equal(result.findings.filter((f) => f.sc === '1.3.1').length, 9)
})

test('duplicate ids are case sensitive and each repeated value is reported once, including hidden elements', () => {
  const result = findings('<p id="same"></p><p id="same"></p><p id="same"></p><i id="Same"></i><i hidden id="Same"></i><i id=""></i><i id=""></i><i id="a&amp;b"></i><i id="a&#38;b"></i>', '4.1.1')
  assert.equal(result.length, 3)
  for (const id of ['same', 'Same', 'a&b']) assert.ok(result.some((f) => f.problem.includes(`"${id}"`)))
})

test('bypass blocks is only a review finding, and working skip links or main landmarks suppress it', () => {
  const check = (body) => checkAccessibilityHtml(`<html lang="en"><head><title>Guide</title></head><body>${body}</body></html>`)
  assert.equal(check('<nav>Menu</nav>').findings.at(-1).certainty, 'needs review')
  assert.equal(count(check('<main></main>'), '2.4.1'), 0)
  assert.equal(count(check('<div role="main"></div>'), '2.4.1'), 0)
  assert.equal(count(check('<a href="#start"><span>Skip to article</span></a><div id="start"></div>'), '2.4.1'), 0)
  assert.equal(count(check('<a href="#main%20area">Skip</a><div id="main area"></div>'), '2.4.1'), 0)
  for (const body of ['<a href="#missing">Skip to content</a>', '<a href="#main"></a><div id="main"></div>', '<main hidden></main>', '<div aria-hidden="true"><main></main></div>']) {
    assert.equal(count(check(body), '2.4.1'), 1, body)
  }
})

test('token reading handles quoted brackets, upper case, entities, comments, raw text and inert templates', () => {
  const result = checkAccessibilityHtml(`<!doctype html><HTML LANG='en'><HEAD><TITLE>Guide</TITLE></HEAD><BODY><MAIN>
    <!-- <img><input><div id="repeat"> -->
    <script>const fake = '<img><button><div id="repeat">';</script>
    <style>/* <img><input> */</style><template><template><img></template><button></button></template>
    <BUTTON aria-label='A > B'></BUTTON><IMG ALT=''><input title="A > B">
    <textarea aria-label="HTML example"><img><button></textarea><div id="repeat"></div>
    <a href=/plants aria-label='Plants &amp; trees'></a>
    </MAIN></BODY></HTML>`)
  assert.deepEqual(result.findings, [])
  assert.deepEqual(checkAccessibilityHtml(page('<!-- <img>')).findings, [])
  assert.equal(count(checkAccessibilityHtml(page('<img ALT="" alt="second">')), '1.1.1'), 0)
  assert.deepEqual(checkAccessibilityHtml(page('<button aria-label="&amp;nbsp;"></button><a href="/x"><img alt="&amp;nbsp;"></a><iframe title="&amp;nbsp;"></iframe>')).findings, [], 'attribute entities are decoded exactly once')
})

test('hidden HTML is excluded from content checks and cannot name visible controls through normal descendants', () => {
  const result = checkAccessibilityHtml(page('<div hidden><img><button></button><input><iframe></iframe></div><a href="/x"><span aria-hidden="true">Name</span></a>'))
  assert.equal(result.findings.length, 1)
  assert.equal(result.findings[0].sc, '2.4.4')
})

test('counts include findings beyond the 25-item response cap', () => {
  const result = checkAccessibilityHtml(page('<img>'.repeat(40) + '<button></button>'))
  assert.equal(count(result, '1.1.1'), 40)
  assert.equal(count(result, '4.1.2'), 1)
  assert.equal(result.findings.length, 25)
  assert.equal(result.limits.findings_truncated, true)
  assert.ok(result.findings.every((f) => f.element.length <= 180))
})

test('incomplete HTML discloses limits and marks missing page facts for review', () => {
  const partial = checkAccessibilityHtml('<html>', { truncated: true })
  assert.equal(partial.limits.page_truncated, true)
  assert.ok(partial.findings.every((f) => f.certainty === 'needs review'))
  const many = checkAccessibilityHtml(page('<i></i>'.repeat(20001)))
  assert.equal(many.limits.parser_truncated, true)
  assert.equal(many.limits.max_elements, 20000)
  const deep = checkAccessibilityHtml(page(`<button>${'<span>'.repeat(70)}Save${'</span>'.repeat(70)}</button>`))
  assert.equal(deep.limits.name_depth_limited, true)
  assert.equal(deep.findings[0].certainty, 'needs review')
  const refs = checkAccessibilityHtml(page('<button aria-labelledby="later"></button><input aria-labelledby="later">'), { truncated: true })
  assert.ok(refs.findings.every((f) => f.certainty === 'needs review'))
})

test('repeated name references have a work bound instead of expanding without limit', () => {
  const graph = Array.from({ length: 30 }, (_, i) => `<span id="n${i}" aria-labelledby="n${i + 1} n${i + 1}"></span>`).join('')
  const result = checkAccessibilityHtml(page(`<button aria-labelledby="n0"></button>${graph}`))
  assert.equal(result.limits.name_work_limited, true)
  assert.equal(result.findings[0].certainty, 'needs review')
})

test('unmatched end tags and an unfinished quoted attribute do not unbound the token reader', () => {
  const result = checkAccessibilityHtml(page('<div>'.repeat(1000) + '</unknown>'.repeat(1000) + '</div>'.repeat(1000)))
  assert.deepEqual(result.findings, [])
  assert.doesNotThrow(() => checkAccessibilityHtml(page('<a title="' + '<img '.repeat(10000))))
})
