#!/usr/bin/env python3
"""Every published image of the mark, rendered from one description of it.

    python3 scripts/render_brand_assets.py            # write them
    python3 scripts/render_brand_assets.py --check    # fail if they drifted

**What this was written for.** On 2026-08-13 the site was serving three
different marks across four files. `apple-touch-icon.png` was the current
brand — #134E4A teal tile, #0A2422 shield, #7DD3C8 arrow. `favicon.svg` was
indigo #818CF8, which is the *desktop app's* accent and has not been this
site's brand since `9ff83aa` ("1.0 — Docket goes on sale"). And `icon.png` and
`og.png` were still the orange #F0800F Scout diamond from before the rename —
`og.png` being the picture every Slack, iMessage and LinkedIn preview of
docketseo.app has been showing.

None of that was visible to any gate. `lint.py` reads HTML, `visual_check.py`
asserts computed CSS, and `verify_live.py` checks that files are served — a
served file that is the wrong picture passes all three. Nothing read a pixel.

**So the four files stop being four facts.** The geometry lives once, in
`MARK_PATHS`, taken from the shield the nav already draws inline. The palette
lives once, read out of `render.py`'s own `--brand` and `--bg` tokens rather
than typed here, because a hex typed here is a second copy and the two will
disagree — that is the same reasoning `visual_check.py` gives for deriving its
expected colours from the page.

**What `--check` actually checks**, since a hash comparison would only say
"different" and not "wrong":

  1. Every file re-renders to the bytes committed. Deterministic rendering is
     the whole point; if this is flaky the gate is worthless and should be
     deleted rather than tolerated.
  2. No published image contains orange. Named explicitly because "do not
     reintroduce orange" is a standing rule of this brand — amber is the
     warning severity, and a brand that shares a colour with "this is a
     warning" cannot use either meaningfully. A drift check alone would have
     let the orange back in silently as long as somebody re-ran the generator.

Rendering goes through Playwright's WebKit from the app checkout, the same
engine `visual_check.py` uses, because the honest answer to "what does this SVG
resolve to" comes from a layout engine and nowhere else.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
sys.path.insert(0, str(ROOT / "scripts"))

import app_path  # noqa: E402

#: The shield and the arrow, on a 1024 grid. Copied from nowhere: this is the
#: source, and `render.py::_mark` draws the same outline inline for the nav.
MARK_PATHS = {
    "shield": ("M512 122 L866 242 L866 522 C866 706 714 838 512 902 "
               "C310 838 158 706 158 522 L158 242 Z"),
    "arrow": ("M348 636 L676 396", "M540 388 L688 388 L688 536"),
}

#: Corner radius of the tile, as iOS and every browser tab expect one.
TILE_RADIUS = 228


def palette() -> dict:
    """The brand colours, read out of the stylesheet that defines them.

    Not typed here. `render.py` is where `--brand` and `--bg` are decided and
    argued for in a comment; duplicating the hexes into this file is how the
    favicon came to be indigo eight months after the site stopped being.
    """
    css = (ROOT / "scripts" / "render.py").read_text(encoding="utf-8")

    def token(name: str) -> str:
        m = re.search(rf"--{name}\s*:\s*(#[0-9A-Fa-f]{{6}})", css)
        if not m:
            raise SystemExit(
                f"cannot find --{name} in render.py. The brand moved and this "
                f"script did not: fix the lookup rather than hardcoding a hex.")
        return m.group(1).upper()

    brand = token("brand")
    return {
        # The tile, and the shield knocked out of it. The shield is the brand
        # darkened, not a separate colour, so a brand change carries.
        "tile": brand,
        "shield": _darken(brand, 0.42),
        # The arrow has to read against the dark shield, so it is the brand
        # lifted well past its paper value. Lifted in HLS, keeping hue and
        # saturation: mixing toward white instead desaturates, and the first
        # version of this produced a grey-green arrow that looked like a
        # rendering fault rather than a colour.
        "arrow": _lift(brand, 0.66),
        "paper": token("bg"),
        "ink": token("text"),
    }


def _mix(hexcolour: str, target: tuple, amount: float) -> str:
    r = int(hexcolour[1:3], 16), int(hexcolour[3:5], 16), int(hexcolour[5:7], 16)
    out = tuple(round(c + (t - c) * amount) for c, t in zip(r, target))
    return "#%02X%02X%02X" % out


def _darken(hexcolour: str, amount: float) -> str:
    return _mix(hexcolour, (0, 0, 0), amount)


def _lighten(hexcolour: str, amount: float) -> str:
    return _mix(hexcolour, (255, 255, 255), amount)


def _lift(hexcolour: str, lightness: float) -> str:
    """The same colour, brighter — hue and saturation untouched."""
    import colorsys

    rgb = tuple(int(hexcolour[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, _, s = colorsys.rgb_to_hls(*rgb)
    return "#%02X%02X%02X" % tuple(
        round(c * 255) for c in colorsys.hls_to_rgb(h, lightness, s))


def _luminance(hexcolour: str) -> float:
    def channel(v):
        v = int(v, 16) / 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = channel(hexcolour[1:3]), channel(hexcolour[3:5]), channel(hexcolour[5:7])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def tile_svg(pal: dict) -> str:
    """The square mark: tile, shield, arrow. Used for the favicon and both
    raster icons, so a browser tab and an iOS home screen cannot disagree."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">'
        f'<rect width="1024" height="1024" rx="{TILE_RADIUS}" fill="{pal["tile"]}"/>'
        f'<path d="{MARK_PATHS["shield"]}" fill="{pal["shield"]}"/>'
        f'<g fill="none" stroke="{pal["arrow"]}" stroke-width="104" '
        'stroke-linecap="round" stroke-linejoin="round">'
        + "".join(f'<path d="{d}"/>' for d in MARK_PATHS["arrow"])
        + "</g></svg>"
    )


def og_html(pal: dict) -> str:
    """The share card: paper ground, the mark, the wordmark, one hard rule.

    Deliberately the site's own furniture rather than a poster. This image is
    what a stranger sees before they see anything else, and the site's whole
    argument is that it looks like an instrument and not a neon dashboard.
    """
    fonts = (SITE / "fonts").as_uri()
    bare_shield = (
        '<svg viewBox="0 0 1024 1024" width="150" height="150">'
        f'<path d="{MARK_PATHS["shield"]}" fill="{pal["tile"]}"/>'
        f'<g fill="none" stroke="{pal["paper"]}" stroke-width="112" '
        'stroke-linecap="round" stroke-linejoin="round">'
        + "".join(f'<path d="{d}"/>' for d in MARK_PATHS["arrow"])
        + "</g></svg>"
    )
    return f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:'Switzer';src:url('{fonts}/Switzer-400.woff2') format('woff2');font-weight:400}}
@font-face{{font-family:'Switzer';src:url('{fonts}/Switzer-700.woff2') format('woff2');font-weight:700}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1200px;height:630px}}
body{{background:{pal['paper']};color:{pal['ink']};
  font-family:'Switzer',system-ui,sans-serif;
  display:flex;flex-direction:column;justify-content:center;
  padding:0 96px;gap:34px}}
.row{{display:flex;align-items:center;gap:26px}}
.word{{font-weight:700;font-size:78px;letter-spacing:-.02em}}
.chip{{font-family:ui-monospace,Menlo,monospace;font-weight:600;font-size:30px;
  letter-spacing:.04em;color:{pal['tile']};border:2px solid {pal['tile']};
  border-radius:4px;padding:2px 12px;align-self:center}}
.rule{{height:2px;background:{pal['ink']};opacity:.14}}
.line{{font-size:38px;line-height:1.32;max-width:900px;color:{pal['ink']}}}
.foot{{font-family:ui-monospace,Menlo,monospace;font-size:24px;
  letter-spacing:.06em;color:{pal['tile']}}}
</style>
<div class="row">{bare_shield}<span class="word">Docket</span><span class="chip">SEO</span></div>
<div class="rule"></div>
<div class="line">A desktop SEO audit that crawls your site and tells you what to
fix, in order — and says so when it could not see.</div>
<div class="foot">docketseo.app</div>
"""


#: filename → (width, height, kind). SVG is written directly; PNGs are rendered.
TARGETS = (
    ("favicon.svg", 0, 0, "svg"),
    ("icon.png", 512, 512, "tile"),
    ("apple-touch-icon.png", 180, 180, "tile"),
    ("og.png", 1200, 630, "og"),
)

_NODE_SCRIPT = """
const { webkit } = require(process.argv[2]);
const fs = require('fs');
const jobs = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
(async () => {
  const browser = await webkit.launch();
  for (const job of jobs) {
    const page = await browser.newPage({
      viewport: { width: job.width, height: job.height },
      deviceScaleFactor: 1,
    });
    await page.goto('file://' + job.html);
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: job.out, omitBackground: false });
    await page.close();
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
"""


def render(out_dir: pathlib.Path) -> None:
    """Write every asset into `out_dir`."""
    pal = palette()
    out_dir.mkdir(parents=True, exist_ok=True)

    # The arrow has to be legible on the shield it sits on. Asserted rather
    # than eyeballed: a naive colour swap breaking contrast is exactly how the
    # eight amber glows survived a token change.
    ratio = contrast(pal["arrow"], pal["shield"])
    if ratio < 4.5:
        raise SystemExit(
            f"the arrow {pal['arrow']} is {ratio:.2f}:1 on the shield "
            f"{pal['shield']} — under 4.5:1 it stops being a shape and becomes "
            f"a smudge at 16px. Adjust the mix in `palette()`.")

    svg = tile_svg(pal)
    (out_dir / "favicon.svg").write_text(svg, encoding="utf-8")

    app = app_path.find()
    playwright = app / "ui" / "node_modules" / "playwright"
    if not playwright.is_dir():
        raise SystemExit(
            f"Playwright is not installed at {playwright}. Run `npm install` in "
            f"{app / 'ui'} — this renders through the same engine "
            f"visual_check.py uses, deliberately.")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        jobs = []
        for name, w, h, kind in TARGETS:
            if kind == "svg":
                continue
            page = tmp / f"{name}.html"
            if kind == "tile":
                page.write_text(
                    "<!doctype html><meta charset='utf-8'>"
                    "<style>*{margin:0;padding:0}html,body{width:%dpx;height:%dpx}"
                    "svg{display:block;width:%dpx;height:%dpx}</style>%s"
                    % (w, h, w, h, svg), encoding="utf-8")
            else:
                page.write_text(og_html(pal), encoding="utf-8")
            jobs.append({"html": str(page), "out": str(out_dir / name),
                         "width": w, "height": h})

        script = tmp / "shot.js"
        script.write_text(_NODE_SCRIPT, encoding="utf-8")
        manifest = tmp / "jobs.json"
        manifest.write_text(json.dumps(jobs), encoding="utf-8")
        subprocess.run(
            ["node", str(script), str(playwright), str(manifest)],
            check=True, cwd=str(app / "ui"))


ORANGE_HINT = (
    "This is the Scout mark. The brand has not been orange since the rename, "
    "and amber is the warning severity — a brand sharing a colour with "
    "'this is a warning' makes both meaningless."
)


def orange_pixels(path: pathlib.Path) -> int:
    """How many pixels read as orange. Zero is the only acceptable answer."""
    from PIL import Image

    im = Image.open(path).convert("RGB")
    count = 0
    for n, (r, g, b) in im.getcolors(im.width * im.height) or []:
        # Orange: red dominant, green in the middle, blue scarce, and saturated
        # enough to be a colour rather than a warm grey.
        if r > 150 and b < 90 and 60 < g < r - 40 and (r - b) > 100:
            count += n
    return count


def check() -> int:
    pal = palette()
    print(f"  brand {pal['tile']}  shield {pal['shield']}  arrow {pal['arrow']}"
          f"  ({contrast(pal['arrow'], pal['shield']):.2f}:1)")

    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        fresh = pathlib.Path(tmp)
        render(fresh)
        for name, *_ in TARGETS:
            live, new = SITE / name, fresh / name
            if not live.exists():
                problems.append(f"{name}: not published at all")
                continue
            if live.read_bytes() != new.read_bytes():
                problems.append(
                    f"{name}: does not match a fresh render. Either somebody "
                    f"edited it by hand, or the brand moved and this was not "
                    f"regenerated. Run this script with no arguments.")

    for name, *_ in TARGETS:
        live = SITE / name
        if name.endswith(".png") and live.exists():
            n = orange_pixels(live)
            if n:
                problems.append(f"{name}: {n} orange pixels. {ORANGE_HINT}")

    if problems:
        print("BRAND ASSETS DRIFTED")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"BRAND ASSETS ok — {len(TARGETS)} files match a fresh render, no orange")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify the published files, writing nothing")
    args = ap.parse_args()
    if args.check:
        return check()
    render(SITE)
    pal = palette()
    print(f"wrote {len(TARGETS)} brand assets in {pal['tile']}")
    for name, *_ in TARGETS:
        print(f"    site/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
