#!/usr/bin/env python3
"""How to serve images in modern formats (WebP and AVIF).

Sourced from Docket's `perf.modern_images` / `perf.legacy_image_format`
(backend/seo_engine/checks/performance.py: an <img> whose address ends .jpg, .jpeg or .png,
reported on pages with four or more) and the classifier that decides an <img> is modern
(extract.py `_offers_modern_format`: inside a <picture> with a WebP or AVIF <source>, or a
srcset of only such files).

Every count and every quoted line of finding text comes from data/image-format-run.json,
written by docket-app/scripts/measure_image_format_fixture.py: a real Docket audit of a
small fixture site of ours, three ways. Nothing about a third-party site. Browser support and
compression claims are MDN's (Image file type and format guide, read 2026-10-10) and are
paraphrased with the link; no size saving is claimed except by quoting Docket's own finding.
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import buy_block, render  # noqa: E402

_RUN = json.loads((Path(__file__).resolve().parent.parent.parent / "data" / "image-format-run.json").read_text())


def _when() -> str:
    d = datetime.date.fromisoformat(_RUN["date"])
    return f"{d.day} {d.strftime('%B %Y')}"


def image_formats() -> Path:
    esc = html.escape
    f = _RUN["before"]["finding"]
    mk = _RUN["markup"]
    body = f"""
<p class="lede">Convert your photos to WebP, or AVIF, and serve them in a way that still works
for the rare browser that cannot read them. Either point the <code>&lt;img&gt;</code> at the
<code>.webp</code> file, or wrap it in a <code>&lt;picture&gt;</code> that offers the modern file
first and keeps the JPEG as the fallback. Most CMS platforms and CDNs will do the conversion for
you on upload.</p>

<h2>Why bother</h2>

<p>MDN's image format guide, which I read on {_when()}, says WebP offers much better compression
than PNG or JPEG, and that AVIF offers slightly better compression than WebP but is not quite as
well supported. It lists WebP and AVIF as supported in Chrome, Edge, Firefox, Opera and Safari. Its
advice for AVIF is to include fallbacks in a format with better support, using the
<code>&lt;picture&gt;</code> element. The guide is
<a href="https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types">Image file type and
format guide</a>.</p>

<p>A smaller file is less to download before the picture appears. On a page whose largest element
is a photo, that is time you can win back for the visitor. It is also one of the cheaper speed
changes, because it touches the files and not your layout.</p>

<h2>Two ways to serve them</h2>

<p><strong>Swap the file.</strong> If you do not need a fallback, point the image at the WebP
directly. Every current browser reads it.</p>

<pre><code>{esc(mk["webp"])}</code></pre>

<p><strong>Offer it first, keep the JPEG behind it.</strong> A <code>&lt;picture&gt;</code> lists
sources in order. The browser takes the first one it understands and falls back to the
<code>&lt;img&gt;</code> if it understands none. This is the way to add AVIF ahead of WebP, and the
way to keep one more format for an old browser.</p>

<pre><code>{esc(mk["picture"])}</code></pre>

<p>Keep the <code>width</code> and <code>height</code> on the <code>&lt;img&gt;</code> in both
cases. They reserve the space whichever file loads. That is covered in
<a href="/how-to/fix-layout-shift/">how to fix layout shift</a>.</p>

<h2>How to convert</h2>

<p>Convert from your original files where you have them. A JPEG that is re-encoded to WebP loses a
little more quality each time it is saved lossy, and you cannot get it back.</p>

<pre><code>cwebp -q 80 photo.jpg -o photo.webp
avifenc photo.jpg photo.avif</code></pre>

<p>Those are the command-line tools from the WebP and AVIF projects. A CMS plugin or an image CDN will
do the same on upload, and either is easier for a site with hundreds of pictures. Look at a few results
at full size before you convert the lot. PNG files with transparency convert too, because WebP and
AVIF both support transparency.</p>

<h2>What Docket reports</h2>

<p>Docket counts every <code>&lt;img&gt;</code> whose address ends in <code>.jpg</code>,
<code>.jpeg</code> or <code>.png</code>, and reports the pages that have four or more. It reads the
address from <code>src</code>, or from <code>data-src</code> or the first entry of
<code>srcset</code> when there is no <code>src</code>. An image counts as modern, and is left out,
in two cases: it sits in a <code>&lt;picture&gt;</code> that has a <code>&lt;source&gt;</code> typed
as WebP or AVIF (or untyped and naming only such files), or its own <code>srcset</code> names only
such files. A <code>&lt;picture&gt;</code> of JPEG sources is still JPEG. JPEG XL is not counted as
modern, because MDN says its browser support is not yet universal.</p>

<p>Until {_when()}, Docket counted the fallback JPEG inside a <code>&lt;picture&gt;</code> as well. That
was a bug: the snippet in its own finding did not clear its own finding. It does now.</p>

<h2>A real before and after</h2>

<p>I wrote a small fixture site for this page: {_RUN["before"]["pages"]} pages of a typewriter repair workshop, four
photos on each. I audited it with Docket on {_when()} in three versions of the same pages. The pages
are ours; nothing here is measured on anyone else's site.</p>

<p>The first version used plain <code>&lt;img&gt;</code> tags pointing at JPEG and PNG files. Docket
reported this, in its own words:</p>

<pre><code>{esc(f["title"])}
{esc(f["detail"])}</code></pre>

<p>Its fix was: <em>{esc(f["fix"])}</em> I then made two versions. In one, every photo was wrapped in
a <code>&lt;picture&gt;</code> with a WebP source and the JPEG kept as the fallback, as above. In the
other, every <code>&lt;img&gt;</code> pointed at the WebP file. Docket reported nothing on either.</p>

<h2>What Docket cannot tell you</h2>

<ul>
<li><strong>It reads names, not files.</strong> It never opens an image, so it does not know how big
one is or whether a <code>.webp</code> file really is WebP.</li>
<li><strong>It cannot see what a CDN does.</strong> Some image CDNs choose the format from the browser's
request and keep the <code>.jpg</code> address. Your visitors get modern files and Docket sees JPEG, so
it may report images you have already handled.</li>
<li><strong>It does not look at CSS background images.</strong> Only <code>&lt;img&gt;</code>
elements are counted.</li>
</ul>

<h2>Where to start</h2>

<p>Start with the pages that matter most and the largest picture on each, usually the one at the top.
If the finding names a lot of images across a big site, they almost always come from one gallery or
product template, and the cheapest fix is a conversion step on upload. The rest of the image work, alt
text, dimensions and lazy-loading, is in <a href="/how-to/fix-image-seo-problems/">how to fix image SEO
problems</a>, and the other thing that holds back a first screen is in
<a href="/how-to/fix-render-blocking-resources/">how to fix render-blocking resources</a>. What Docket adds
is the same count across every page, ranked with the rest; see how that compares with
<a href="/vs/">other audit tools</a>.</p>

{buy_block("howto-image-formats", big=False, try_app="howto-image-formats-try-free")}
"""
    return render(
        cat="how-to", slug="serve-images-in-modern-formats",
        title="How to serve images in modern formats (WebP and AVIF)",
        desc=("Point the image at a WebP file, or offer WebP and AVIF in a picture element with the JPEG "
              "as fallback. What Docket counts and what it cannot see."),
        h1="How to serve images in modern formats",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / image formats',
        body=body,
        faq=[
            ("Should I use WebP or AVIF?",
             "MDN says AVIF compresses slightly better but is not quite as well supported, and advises a "
             "fallback. WebP is read by every current browser. Offering AVIF first and WebP second in a "
             "picture element gets both."),
            ("How do I keep a fallback for old browsers?",
             "Wrap the image in a picture element, list the modern sources first, and keep the original "
             "img inside it as the fallback."),
            ("Will Docket still report an image inside a picture element?",
             "Not if the picture has a source typed as WebP or AVIF, or untyped and naming only such files. "
             "A picture of JPEG sources is still reported."),
            ("Does Docket check the size of my images?",
             "No. It reads the address in the markup and never opens the file."),
        ],
    )


if __name__ == "__main__":
    print(image_formats())
