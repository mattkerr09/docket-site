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

So this renders the built pages in WebKit through Scout's own `scout-render`
helper and asserts computed values. Every expected value is derived from the
page — the amber assertion compares a link against `var(--amber-light)` as that
page resolves it, rather than against a hex typed here, because a hex typed
here is a second copy of a fact and the two will disagree.

Usage:  python3 scripts/visual_check.py [--verbose]
"""
from __future__ import annotations

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

  return {
    width: window.innerWidth,
    amber: varColor('--amber-light'),
    linkColors: colors,
    linkCount: links.length,
    navLinks: nav ? nav.querySelectorAll('a').length : 0,
    navHeight: nav ? Math.round(nav.getBoundingClientRect().height) : 0,
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
    """Locate `scout-render`, in the order it will actually be found."""
    env = os.environ.get("SCOUT_RENDER")
    if env and Path(env).exists():
        return Path(env)
    candidates = [
        ROOT / "scripts" / "scout-render",
        Path("/Applications/Scout.app/Contents/Resources/scout-render"),
        Path.home() / "Downloads" / "SEO audit app" / "dist" / "Scout.app"
        / "Contents" / "Resources" / "scout-render",
    ]
    for c in candidates:
        if c.exists():
            return c
    found = shutil.which("scout-render")
    if found:
        return Path(found)
    sys.exit(
        "visual_check: scout-render not found.\n"
        "  It is one file. Build it with:\n"
        "    swiftc -O -framework WebKit -framework AppKit \\\n"
        "      '<app repo>/packaging/render/ScoutRender.swift' \\\n"
        f"      -o {ROOT / 'scripts' / 'scout-render'}\n"
        "  or point SCOUT_RENDER at an existing copy.\n"
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
                 f"ScoutRender.swift.")


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
    colors = r["linkColors"]
    if UA_DEFAULT_LINK in colors:
        hrefs = colors[UA_DEFAULT_LINK][:4]
        bad.append(f"{name}: {len(colors[UA_DEFAULT_LINK])} link(s) are "
                   f"user-agent default blue — a colour rule is not "
                   f"resolving: {hrefs}")
    if r["amber"] not in colors:
        bad.append(f"{name}: no link resolves to --amber-light "
                   f"({r['amber']}); link colours present are "
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

    # 4. Structure, so a page that renders blank cannot pass the colour test.
    if r["h1"] != 1:
        bad.append(f"{name}: {r['h1']} h1 elements")
    if r["bodyText"] < 400:
        bad.append(f"{name}: {r['bodyText']} characters of rendered text")
    if r["footerLinks"] < 3:
        bad.append(f"{name}: footer has {r['footerLinks']} links")

    # 5. The second stray brace. Only the homepage has a hero.
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
INJECTIONS = [
    ("index.html", "homepage", "hero glow",
     ".hero-sec::before{content", ".hero-sec::befores{content"),
    ("learn/googlebot-2mb-limit/index.html", "article", "link colour",
     "a{color:var(--amber-light)", "a}{color:var(--amber-light)"),
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
    if "--self-test" in sys.argv:
        return self_test(helper)
    failures: list[str] = []
    checked = 0

    for rel, label in PAGES:
        page = SITE / rel
        if not page.exists():
            failures.append(f"{label}: {rel} was not built")
            continue
        for width in (NARROW, WIDE):
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
          f"{len(PAGES)} templates at {NARROW}px and {WIDE}px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
