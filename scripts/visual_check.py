#!/usr/bin/env python3
"""Assert what the built pages actually resolve to, in a real browser engine.

Iteration 39 shipped two stray `}` characters in the stylesheet. The first
ended the rule that coloured every link in every article, so body links fell
back to the user-agent default blue on twenty-odd pages. The second ended
`.hero-sec::before`, so the homepage hero glow never drew at all.

Neither was visible to any gate we had. `lint.py` reads HTML and now counts
braces, which catches that exact shape — but a brace-balanced stylesheet can
still resolve a rule to nothing, and a stylesheet is not the only way to lose a
colour. The question "what colour is this link, finally" has one honest answer
and only a layout engine can give it.

So this renders the built pages in WebKit through Docket's own `docket-render`
helper and asserts computed values. Every expected value is derived from the
page — the brand assertion compares a link against `var(--brand-light)` as that
page resolves it, rather than against a hex typed here, because a hex typed
here is a second copy of a fact and the two will disagree.

Usage:  python3 scripts/visual_check.py [--verbose]
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"

#: The narrow width is the one that matters. Everything that has ever been
#: wrong with this layout was wrong at 375px and fine at 1280.
NARROW = 375
WIDE = 1280

#: A width this gate had never rendered, and the reason it now does.
#:
#: Probing the live homepage at 1600px found prose sitting in a container built
#: for a table: `.wrap-wide` is 1080px so a comparison table is not cramped, and
#: the pricing caveat inherited it — 1080px across 316 characters, roughly 140
#: characters a line. Ordinary paragraphs were 820px because `.wrap` caps them,
#: so nothing at 375 or 1280 showed it.
#:
#: A measure only goes wrong above the container's own cap, which is why two
#: widths below it saw nothing.
VERY_WIDE = 1600

#: Prose must not exceed the site's OWN body measure. `.wrap` is
#: `width:min(820px, …)` in render.py, and that 820 is a deliberate, long-
#: standing choice — this gate is not here to relitigate it.
#:
#: The first version of this assertion estimated characters per line and
#: tripped at 90, which flagged every ordinary essay paragraph: 820px works out
#: near 100 characters, so the gate was calling the site's own design a bug.
#: The real defect is prose in a container built for something else —
#: `.wrap-wide` is 1080px so a comparison table is not cramped, and a caveat
#: sitting in it ran the full 1080.
#:
#: Measuring against the cap catches that and leaves the design alone. The
#: slack absorbs padding and sub-pixel rounding.
WRAP_PX = 820
MAX_PROSE_PX = WRAP_PX + 40

#: One page per template, not one page per URL. Templates are what break.
PAGES = [
    ("index.html", "homepage"),
    ("learn/googlebot-2mb-limit/index.html", "article"),
    ("learn/index.html", "hub"),
    ("download/index.html", "download"),
    ("vs/screaming-frog-alternative/index.html", "comparison"),
    ("index/ai-directives/index.html", "dataset"),
    ("legal/privacy/index.html", "legal"),
    ("about/index.html", "about"),
    ("contact/index.html", "contact"),
    ("learn/dead-contact-address/index.html", "survey"),
    ("learn/audit-tool-accuracy/index.html", "essay"),
]

PROBE = """
(function () {
  // Resolve a CSS variable the way the page resolves it, so the expected
  // value is read from the page rather than typed into the test.
  function varColor(name) {
    const el = document.createElement('span');
    el.style.color = 'var(' + name + ')';
    el.style.position = 'absolute';
    document.body.appendChild(el);
    const c = getComputedStyle(el).color;
    el.remove();
    return c;
  }

  // The regression was "links fell back to the user-agent default", so ask
  // that of every link rather than guessing which one counts as prose. A
  // single selector picks the hero note on one template and a CTA button on
  // another, and neither says anything about the rule that broke.
  const links = [...document.querySelectorAll('a[href]')];
  const colors = {};
  for (const a of links) {
    const c = getComputedStyle(a).color;
    (colors[c] = colors[c] || []).push(a.getAttribute('href'));
  }
  const nav = document.querySelector('nav');
  const hero = document.querySelector('.hero-sec');
  const heroBefore = hero ? getComputedStyle(hero, '::before') : null;

  // An element wider than the viewport is only a bug if nothing can scroll
  // it. Wide tables and code blocks sit inside `overflow-x: auto` wrappers on
  // purpose — flagging those reports the fix as the problem.
  function scrollableAncestor(el) {
    for (let p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
      const ox = getComputedStyle(p).overflowX;
      if (ox === 'auto' || ox === 'scroll' || ox === 'hidden') return true;
    }
    return false;
  }
  const over = [...document.querySelectorAll('body *')]
    .filter(e => e.getBoundingClientRect().right > window.innerWidth + 0.5)
    .filter(e => !scrollableAncestor(e))
    .map(e => e.tagName.toLowerCase() + (e.className ? '.' + String(e.className).split(' ')[0] : ''));

  // The gutter. `.wrap` is width:min(820px, calc(100% - 2rem)), and the 2rem
  // is the only thing holding body text off the glass. When that rule broke,
  // the FAQ ran flush to the viewport edge on a phone: no overflow, no
  // horizontal scroll, no clipping — every assertion stayed green, and the bug
  // was found by looking at a screenshot.
  const textish = [...document.querySelectorAll('p, h1, h2, h3, li')]
    .filter(e => (e.innerText || '').trim().length > 20)
    .filter(e => e.getBoundingClientRect().width > 0);
  const lefts = textish.map(e => Math.round(e.getBoundingClientRect().left));
  const minLeft = lefts.length ? Math.min(...lefts) : -1;
  const tightest = textish[lefts.indexOf(minLeft)];

  // Prose measure. A paragraph in a container built for a table inherits the
  // table's width: `.wrap-wide` is 1080px, and a 316-character caveat sat in
  // it at roughly 140 characters a line. Reported in characters rather than
  // pixels because that is what readability is about, estimated from the
  // element's own font size at the usual ~0.5em average glyph width.
  var widestProse = 0, widestProseAt = '';
  for (var pi = 0, ps = document.querySelectorAll('p'); pi < ps.length; pi++) {
    var el = ps[pi];
    if (el.textContent.trim().length < 120) continue;
    var px = el.getBoundingClientRect().width;
    if (!px) continue;
    px = Math.round(px);
    if (px > widestProse) {
      widestProse = px;
      widestProseAt = el.tagName.toLowerCase() +
        (el.className ? '.' + String(el.className).split(' ')[0] : '');
    }
  }

  // ---- rendered contrast -------------------------------------------------
  // Every colour pair on this page, measured where it actually lands rather
  // than where the token says it should. Two failures this session came from
  // exactly the gap between those: eight amber glows survived a token swap
  // because no gate read colour, and when the site moved from a dark ground
  // to paper the nav kept a hardcoded `rgba(11,12,15,.88)` — ink text on
  // near-black, 1.1:1, invisible, and every existing gate passed.
  //
  // Walking up for the background matters: most text sits on a transparent
  // parent, so `getComputedStyle(el).backgroundColor` is `rgba(0,0,0,0)` and
  // comparing against it scores every element as perfect black-on-black.
  function _lum(c) {
    const m = (c || '').match(/[\d.]+/g);
    if (!m) return null;
    const f = m.slice(0, 3).map(v => {
      v = Number(v) / 255;
      return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
  }
  function _bgOf(el) {
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const b = getComputedStyle(n).backgroundColor;
      const a = (b || '').match(/[\d.]+/g);
      // Anything below 85% alpha is a wash over what is behind it; keep
      // climbing rather than treating the wash as the ground.
      if (a && (a.length < 4 || Number(a[3]) > 0.85)) return b;
    }
    return getComputedStyle(document.body).backgroundColor;
  }
  const contrast = [];
  let contrastExamined = 0;
  for (const el of document.querySelectorAll(
      'p,span,li,a,h1,h2,h3,h4,h5,td,th,small,b,em,strong,div,label,button')) {
    // Only the element's OWN text. A wrapper inherits its children's text and
    // would be scored against a colour it never paints.
    const own = [...el.childNodes].filter(n => n.nodeType === 3)
      .map(n => n.textContent).join('').trim();
    if (!own) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || Number(cs.opacity) < 0.5) continue;
    contrastExamined++;
    const l1 = _lum(cs.color), l2 = _lum(_bgOf(el));
    if (l1 === null || l2 === null) continue;
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const px = parseFloat(cs.fontSize);
    const large = px >= 24 || (px >= 18.66 && parseInt(cs.fontWeight) >= 700);
    const need = large ? 3 : 4.5;
    if (ratio < need) {
      contrast.push({
        text: own.slice(0, 40), fg: cs.color, bg: _bgOf(el),
        ratio: Math.round(ratio * 100) / 100, need: need,
        px: Math.round(px * 10) / 10,
        sel: el.tagName.toLowerCase() +
             (el.className ? '.' + String(el.className).split(' ')[0] : ''),
      });
    }
  }

  return {
    width: window.innerWidth,
    widestProsePx: widestProse,
    widestProseAt: widestProseAt,
    minGutter: minLeft,
    gutterAt: tightest
      ? tightest.tagName.toLowerCase() +
        (tightest.className ? '.' + String(tightest.className).split(' ')[0] : '')
      : '',
    brand: varColor('--brand-light'),
    linkColors: colors,
    linkCount: links.length,
    contrast: contrast,
    contrastExamined: contrastExamined,
    navLinks: nav ? nav.querySelectorAll('a').length : 0,
    navHeight: nav ? Math.round(nav.getBoundingClientRect().height) : 0,

    // Nav links pushed outside their own rail. A scroll container hides its
    // overflow silently: no page-level horizontal scroll, no clipping anywhere
    // this file already looks, every other assertion green. "About" sat at
    // x=360-399 in a 375px viewport for a whole release, reachable only by a
    // sideways swipe with nothing on screen to suggest one — because the gap
    // had been tuned to the exact width of six links and a seventh was added.
    //
    // Compared against the rail rather than the viewport: the rail is what
    // clips, and a link can be off the rail while still inside the window.
    navClipped: (function () {
      if (!nav) return [];
      var rail = nav.querySelector('.nav-links');
      if (!rail) return [];
      var edge = rail.getBoundingClientRect().right;
      var out = [];
      var as = rail.querySelectorAll('a');
      for (var ni = 0; ni < as.length; ni++) {
        // 1px of tolerance for subpixel layout; a real clip is tens of px.
        if (as[ni].getBoundingClientRect().right > edge + 1) {
          out.push((as[ni].textContent || '').trim());
        }
      }
      return out;
    })(),
    footerLinks: document.querySelectorAll('footer a').length,
    h1: document.querySelectorAll('h1').length,
    bodyText: (document.body.innerText || '').trim().length,
    scrollWidth: document.documentElement.scrollWidth,
    overflowing: [...new Set(over)].slice(0, 6),
    heroGlow: heroBefore
      ? {content: heroBefore.content, w: parseFloat(heroBefore.width) || 0,
         h: parseFloat(heroBefore.height) || 0, bg: heroBefore.backgroundImage !== 'none'}
      : null
  };
})()
"""

#: What a browser paints when nothing told it otherwise. Seeing this is the
#: symptom the whole file exists for.
UA_DEFAULT_LINK = "rgb(0, 0, 238)"


def find_helper() -> Path:
    """Locate `docket-render`, in the order it will actually be found."""
    env = os.environ.get("DOCKET_RENDER")
    if env and Path(env).exists():
        return Path(env)
    candidates = [
        ROOT / "scripts" / "docket-render",
        Path("/Applications/Docket.app/Contents/Resources/docket-render"),
        app_path.find() / "dist" / "Docket.app"
        / "Contents" / "Resources" / "docket-render",
    ]
    for c in candidates:
        if c.exists():
            return c
    found = shutil.which("docket-render")
    if found:
        return Path(found)
    sys.exit(
        "visual_check: docket-render not found.\n"
        "  It is one file. Build it with:\n"
        "    swiftc -O -framework WebKit -framework AppKit \\\n"
        "      '<app repo>/packaging/render/DocketRender.swift' \\\n"
        f"      -o {ROOT / 'scripts' / 'docket-render'}\n"
        "  or point DOCKET_RENDER at an existing copy.\n"
        "  This gate fails rather than skips: a check that quietly does\n"
        "  nothing is how the stray braces shipped in the first place."
    )


def require_probe_support(helper: Path) -> None:
    """A helper too old for `--probe` ignores it and returns a DOM capture.

    That JSON parses fine and has none of the keys this gate reads, so the
    failure would surface as a KeyError halfway through a deploy rather than as
    "your helper is out of date".
    """
    proc = subprocess.run(
        [str(helper), "about:blank", "--timeout", "10", "--probe", "1 + 1"],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0 or proc.stdout.strip() != "2":
        sys.exit(f"visual_check: {helper} does not support --probe.\n"
                 f"  Rebuild it from the app repo's packaging/render/"
                 f"DocketRender.swift.")


def require_width_support(helper: Path) -> None:
    """`--width` must actually resize the viewport, not just be accepted.

    Everything below is width-specific: the gutter at 375, the prose measure at
    1600, `scrollWidth > width + 1`. All of it compares against the width this
    script *asked for*. A helper that accepted `--width` and ignored it would
    render eleven templates three times at one default size and pass, and the
    output would still say "33 renders, 375px / 1280px / 1600px".

    This is not hypothetical. The copy in this repo was a pre-rename build that
    still announced itself as `scout-render` and whose usage line lists neither
    `--width` nor `--probe`. It honours both — checked, at two widths, which is
    the only reason that sentence is "it honours both" rather than a guess. A
    binary is committed here so the gate runs standalone, and a committed
    binary is exactly the kind of thing that drifts silently from the source it
    was built from.
    """
    for want in (375, 1600):
        proc = subprocess.run(
            [str(helper), "about:blank", "--timeout", "10",
             "--width", str(want), "--probe", "window.innerWidth"],
            capture_output=True, text=True, timeout=30,
        )
        got = proc.stdout.strip()
        if proc.returncode != 0 or got != str(want):
            sys.exit(
                f"visual_check: {helper} does not honour --width.\n"
                f"  Asked for {want}px, the page reported {got or '(nothing)'}.\n"
                f"  Every width-specific assertion below would be testing one\n"
                f"  size while reporting three. Rebuild it from the app repo's\n"
                f"  packaging/render/DocketRender.swift.")


def probe(helper: Path, page: Path, width: int) -> dict:
    proc = subprocess.run(
        [str(helper), f"file://{page}", "--width", str(width),
         "--height", "1400", "--settle", "0.25", "--timeout", "15",
         "--probe", PROBE],
        capture_output=True, text=True, timeout=40,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{page.name} at {width}px: {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def check(name: str, width: int, r: dict) -> list[str]:
    """Every assertion, with the reason it exists in the message."""
    bad = []

    # 1. The bug this file was written for. Two halves: nothing fell back to
    #    the browser default, and the brand colour is actually reaching links.
    # 0. Line length against the site's own measure. Only meaningful above the
    #    container caps — at 375 and
    #    1280 every paragraph is already bounded by `.wrap`, which is why two
    #    widths saw nothing and 1600 found it.
    prose = r.get("widestProsePx") or 0
    if prose > MAX_PROSE_PX:
        bad.append(f"{name}: a paragraph is {prose}px wide "
                   f"({r.get('widestProseAt') or 'unknown'}) against a {WRAP_PX}px "
                   f"body measure — prose in a container sized for a table")

    colors = r["linkColors"]
    if UA_DEFAULT_LINK in colors:
        hrefs = colors[UA_DEFAULT_LINK][:4]
        bad.append(f"{name}: {len(colors[UA_DEFAULT_LINK])} link(s) are "
                   f"user-agent default blue — a colour rule is not "
                   f"resolving: {hrefs}")
    if r["brand"] not in colors:
        bad.append(f"{name}: no link resolves to --brand-light "
                   f"({r['brand']}); link colours present are "
                   f"{sorted(colors)}")

    # 2. The mobile nav wrapped out of its own box once.
    if r["navLinks"] < 5:
        bad.append(f"{name}: nav has {r['navLinks']} links, expected the full set")
    if r["navHeight"] < 30:
        bad.append(f"{name}: nav is {r['navHeight']}px tall — it has collapsed")

    # 3. Horizontal scroll on a phone.
    if r["scrollWidth"] > width + 1:
        bad.append(f"{name}: document is {r['scrollWidth']}px wide in a "
                   f"{width}px viewport — {r['overflowing'] or 'source unknown'}")
    if r["overflowing"]:
        bad.append(f"{name}: elements past the viewport edge: {r['overflowing']}")

    # 3b. Text flush to the glass — the opposite failure to overflow, and
    # invisible to every rule above: nothing scrolls, nothing is clipped, the
    # copy simply starts at x=0. Only meaningful on a phone; at 1600px the wrap
    # is centred and the margin is enormous.
    if width <= 480 and 0 <= r.get("minGutter", -1) < MIN_GUTTER:
        bad.append(f"{name}: text starts {r['minGutter']}px from the edge "
                   f"({r.get('gutterAt') or 'unknown element'}) in a {width}px "
                   f"viewport — the .wrap gutter is gone")

    # 3c. Navigation pushed off its own rail. Checked at every width, not just
    # phones: a nav that outgrows its container is a layout fault at any size,
    # and this one reached production because the pre-deploy gate had no
    # opinion about it while verify_live.py did — the wrong order to find out.
    if r.get("navClipped"):
        bad.append(f"{name}: nav link(s) past the edge of the nav rail: "
                   f"{r['navClipped']} — they are only reachable by a sideways "
                   f"swipe, with nothing on screen to suggest one")

    # 4. Structure, so a page that renders blank cannot pass the colour test.
    if r["h1"] != 1:
        bad.append(f"{name}: {r['h1']} h1 elements")
    if r["bodyText"] < 400:
        bad.append(f"{name}: {r['bodyText']} characters of rendered text")
    if r["footerLinks"] < 3:
        bad.append(f"{name}: footer has {r['footerLinks']} links")

    # 5. Rendered contrast, measured where the colour lands.
    #
    # A zero here can mean clean or blind, so the count is checked too: if the
    # probe examined almost nothing — a selector change, a page that failed to
    # render — an empty failure list is not evidence and must not read as one.
    if r.get("contrastExamined", 0) < 25:
        bad.append(f"{name}: contrast probe examined "
                   f"{r.get('contrastExamined', 0)} elements — too few to mean "
                   f"anything, so its silence is not a pass")
    for c in r.get("contrast", [])[:6]:
        bad.append(f"{name}: {c['ratio']}:1 needs {c['need']}:1 — "
                   f"{c['sel']} {c['fg']} on {c['bg']} at {c['px']}px "
                   f"({c['text']!r})")

    # 6. The second stray brace. Only the homepage has a hero.
    if r["heroGlow"] is not None:
        g = r["heroGlow"]
        if g["content"] == "none":
            bad.append(f"{name}: .hero-sec::before is not generated — the rule "
                       f"is gone")
        elif not g["bg"] or g["w"] < 100 or g["h"] < 100:
            bad.append(f"{name}: hero glow is {g['w']}x{g['h']} "
                       f"bg={g['bg']} — it will not be visible")
    elif name.startswith("homepage"):
        bad.append("homepage: .hero-sec is missing")

    return bad


#: The two stray braces, reconstructed. `--self-test` injects each into a
#: throwaway copy of a real page and requires the gate to fail on it.
#:
#: A gate that passes the first time it is run has proved nothing. Both of
#: these shipped past a green build, so "green" is the state that needs
#: evidence, not the red one.
#: The real gutter is 16px a side. 8 catches a collapse to zero while
#: leaving room for a deliberate design change that tightens it.
MIN_GUTTER = 8

INJECTIONS = [
    ("index.html", "homepage", "hero glow",
     ".hero-sec::before{content", ".hero-sec::befores{content"),
    ("learn/googlebot-2mb-limit/index.html", "article", "link colour",
     "a{color:var(--brand-light)", "a}{color:var(--brand-light)"),
    ("index.html", "homepage", "gutter",
     ".wrap{width:min(820px,calc(100% - 2rem))",
     ".wrap{width:min(820px,calc(100% - 0rem))"),
    # The real regression, replayed: take the wrap off the nav rail and put the
    # scroll behaviour back, which is exactly the state that shipped "About"
    # off the right edge at 375px.
    ("index.html", "homepage", "nav clipping",
     ".nav-links{order:3;width:100%;gap:.55rem .8rem;font-size:.88rem;\n"
     "    flex-wrap:wrap;padding-bottom:.15rem}",
     ".nav-links{order:3;width:100%;gap:.55rem .8rem;font-size:.88rem;\n"
     "    flex-wrap:nowrap;overflow-x:auto;padding-bottom:.15rem}"),
]


def self_test(helper: Path) -> int:
    """Break each rule in a copy and require the gate to notice."""
    import tempfile

    failures = []
    for rel, label, what, find, replace in INJECTIONS:
        source = SITE / rel
        html = source.read_text()
        if html.count(find) != 1:
            failures.append(
                f"{what}: {rel} contains {html.count(find)} copies of "
                f"{find!r}. Two rules for one pseudo-element is how the glow "
                f"came back as the wrong design — fix the duplicate, not this "
                f"line.")
            continue
        if find not in html:
            failures.append(
                f"{what}: the rule this gate guards is no longer written as "
                f"{find!r} in {rel} — the self-test is testing nothing")
            continue
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "index.html"
            broken.write_text(html.replace(find, replace, 1))
            r = probe(helper, broken, NARROW)
            found = check(f"{label}@{NARROW}", NARROW, r)
            if found:
                print(f"  caught {what}: {found[0]}")
            else:
                failures.append(
                    f"{what}: injected a stray brace into {rel} and the gate "
                    f"still passed — it does not check what it claims to")

    if failures:
        print(f"SELF-TEST FAILED ({len(failures)})")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"SELF-TEST ok — {len(INJECTIONS)} injected bugs, all caught")
    return 0


def main() -> int:
    verbose = "--verbose" in sys.argv
    helper = find_helper()
    require_probe_support(helper)
    require_width_support(helper)
    if "--self-test" in sys.argv:
        return self_test(helper)
    failures: list[str] = []
    checked = 0

    for rel, label in PAGES:
        page = SITE / rel
        if not page.exists():
            failures.append(f"{label}: {rel} was not built")
            continue
        for width in (NARROW, WIDE, VERY_WIDE):
            name = f"{label}@{width}"
            try:
                r = probe(helper, page, width)
            except Exception as exc:  # noqa: BLE001 — report, do not mask
                failures.append(f"{name}: {exc}")
                continue
            checked += 1
            found = check(name, width, r)
            failures.extend(found)
            if verbose:
                print(f"  {name}: links={r['linkCount']} nav={r['navLinks']} "
                      f"text={r['bodyText']} scroll={r['scrollWidth']}"
                      f"{' OK' if not found else ''}")

    if failures:
        print(f"VISUAL: {len(failures)} problem(s) across {checked} renders")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"VISUAL ok — {checked} renders, "
          f"{len(PAGES)} templates at {NARROW}px, {WIDE}px and {VERY_WIDE}px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
