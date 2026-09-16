#!/usr/bin/env python3
"""Image findings — what `onpage.images` actually computes, and what it cannot.

Everything about the check is read from its source, `onpage.images` in
`backend/seo_engine/checks/onpage.py`, from the extractor that fills the fields
it reads (`_extract_resources` in `backend/seo_engine/extract.py`), and from
`tests/test_a_count_of_images_is_not_a_count_of_pages.py`, whose fixture carries
the comment that `alt=""` is correct markup and that only a missing attribute
counts.

⚠️ THE BRIEF'S DIVISION OF THE SUBJECT WAS BACKWARDS, and this module follows
the repo instead. The brief said width/height belongs to `/how-to/fix-layout-shift/`
and that this page is `onpage.images` only. But `onpage.img_no_dimensions` is
emitted BY `onpage.images`, and it is the OWNER of that remedy: `perf.cls_risk`
carries `same_fix_as="onpage.img_no_dimensions"` and defers to it. So the
dimensions finding cannot be handed to the neighbour — the neighbour hands it
here. This page therefore names it, states which of its own findings the check
weights highest, and sends the reader to the CLS page for the causes and the
fix, which is that page's subject and is not restated.

⚠️ `has_dims` IS NARROWER THAN THE ADVICE ON THE CLS PAGE. The extractor sets it
from `width` and `height` attributes, or from the string "aspect-ratio" in the
element's own inline `style` attribute. An `aspect-ratio` rule living in a
stylesheet reserves the space correctly and Docket cannot see it. The page says
so plainly rather than letting a reader who took the CLS page's advice wonder
why the finding did not clear.

No figure is published here and there is no dataset behind this page. The
check's thresholds are quoted as source inside `<code>`, which is where they
came from, rather than paraphrased into prose where they could drift.

The body is an f-string only so the read date can interpolate; it contains no
literal braces, so no escaping is in play.

External sources, read 2026-09-15:

  * https://www.w3.org/WAI/tutorials/images/decorative/
    "a null (empty) alt text should be provided (alt="") so that they can be
    ignored by assistive technologies", and "Leaving out the alt attribute is
    also not an option because when it is not provided, some screen readers
    will announce the file name of the image instead."
  * https://developers.google.com/search/docs/appearance/google-images
    "Google uses alt text along with computer vision algorithms and the
    contents of the page to understand the subject matter of the image", and
    the warning against "filling alt attributes with keywords (also known as
    keyword stuffing)".

Google's sentence beginning "The most important attribute when it comes to…" is
deliberately NOT quoted: `scripts/lint.py` bans "when it comes to" as visible
text, in prose and in `<code>` alike, so quoting it would fail the build.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from render import render  # noqa: E402

#: The day both external sources were read, in the form the prose prints.
READ = "15 September 2026"


def howto_images() -> Path:
    body = f"""
<p class="lede">An audit hands you a page of image findings and you have a few hundred images.
The useful question is not whether they are all optimised. It is which of those findings came
from something a crawler actually measured, and which piece of image advice has been repeated
so often that nobody checks it any more. Docket's check here is
<code>onpage.images</code>, "Image optimisation", and the most useful thing to say about it is
what it cannot see.</p>

<h2>It never looks at the picture</h2>

<p>Docket reads your HTML. It does not download the image file, open it, or run anything over
the pixels. Every image finding it produces is a statement about markup.</p>

<p>That has one consequence worth more than the rest of this page: <strong>Docket cannot tell
you whether your alt text describes the image.</strong> It can tell you an alt attribute is
absent. It cannot tell you that the alt on your hero photo says "image" or "banner-final-v2" or
your company name repeated. Those are the alt attributes most worth fixing, and no crawler will
ever flag one, because a crawler has nothing to compare the words against.</p>

<p>So a clean run on this check does not mean your images are described. It means the
attributes are present. Anyone selling you the first claim on the strength of the second is
selling you a crawl.</p>

<h2>An empty alt is correct, and the check is built around that</h2>

<p>This is where most alt-text advice goes wrong, and it is the reason the check is written the
way it is. A decorative image — a divider, a spacer, a background flourish, an icon sitting
beside a word that already says the same thing — is <em>supposed</em> to carry an empty alt
attribute. It is not a defect to be cleared. It is the instruction that tells assistive
technology to skip past something that carries no information.</p>

<p>The W3C's Web Accessibility Initiative is unambiguous about both halves of it. Its tutorial
on decorative images says a null alt text should be provided so that such images can be ignored
by assistive technologies, and that leaving the attribute out is not an option, because when it
is absent some screen readers announce the file name instead. <a
href="https://www.w3.org/WAI/tutorials/images/decorative/">WAI, decorative images</a>, read
{READ}.</p>

<p>That is the whole distinction: an empty alt is an answer, and a missing alt is silence. The
comment above the loop in Docket's own source says why it matters commercially as well as
technically — conflating the two is called the single most common false positive in SEO tooling,
and one that trains people to write junk alt text onto spacer images. A tool that flags
<code>alt=""</code> is not being strict. It is asking you to make your site worse.</p>

<p>So Docket counts only an <em>absent</em> attribute, and its finding says so in its own
words:</p>

<pre><code>Note: alt="" on a purely decorative image is correct and is not counted here.</code></pre>

<h2>What it computes, from the source</h2>

<p>The check walks the indexable pages, takes the image resources on each, and accumulates
what it needs. Written out, the conditions are short enough to read:</p>

<pre><code>for img in imgs:
    if img.alt is None and img.url:
        missing_alt.append(img.url)
        pages_missing_alt.add(page.url)
without_dims = [i for i in imgs if not i.has_dims]
if len(without_dims) &gt;= 3:
    no_dims_pages.add(page.url)
if len(imgs) &gt;= 8 and not any(i.lazy for i in imgs):
    no_lazy_pages.add(page.url)</code></pre>

<p>More than one finding can come out of that, and they are not equally weighted. Missing alt
attributes are reported at MEDIUM, counted in images rather than pages, with the page list
alongside. Pages whose images have no declared width and height are reported at MEDIUM and
carry the <em>highest</em> impact weight this check emits. Image-heavy pages that lazy-load
nothing are reported at LOW, which is the lightest weight of the set.</p>

<p>Read that ordering as the answer to the question at the top. If you are triaging, the
dimensions finding outranks the alt one in Docket's own arithmetic, and the lazy-loading one
comes last. That is not the order the advice on the web puts them in.</p>

<h2>The thresholds are the interesting part</h2>

<p>The dimensions and lazy-loading findings only fire past a threshold, and the thresholds are
the check declining to nag you.</p>

<ul>
<li><strong>Dimensions.</strong> A page needs several images with no declared size before it is
listed. One undeclared image on a page is not a layout-shift problem worth a row in your report,
and a tool that reported it would bury the pages where it is.</li>
<li><strong>Lazy loading.</strong> A page must be genuinely image-heavy <em>and</em> lazy-load
nothing at all. A page with a handful of images is not helped by lazy loading, and a page that
already lazy-loads some of them has understood the idea.</li>
<li><strong>Missing alt</strong> has no threshold. One image with no alt attribute is one image
a screen reader will announce by file name.</li>
</ul>

<p>The lazy-loading detection is also wider than the attribute. An image counts as lazy if it
carries <code>loading="lazy"</code>, and also if it carries a <code>data-src</code> or
<code>data-lazy-src</code>, which is how a JavaScript lazy-loader marks one. A site using a
lazy-load plugin is not told to add lazy loading.</p>

<h2>What Docket means by "an image"</h2>

<p>Narrower than you probably mean, and worth knowing before you compare counts. The extractor
collects <code>&lt;img&gt;</code> elements. A background image set in CSS is not one. An inline
<code>&lt;svg&gt;</code> is not one. A video poster frame is not one. If your site draws most of
its imagery from stylesheets, Docket's image counts will look implausibly low, and that is the
reason.</p>

<p>The address it records comes from <code>src</code>, or failing that
<code>data-src</code> or <code>data-lazy-src</code>, or failing those the first candidate in
<code>srcset</code>. An <code>&lt;img&gt;</code> from which no address at all can be resolved is
skipped by the missing-alt count, because a finding that cannot name the file it is about is
not actionable.</p>

<p>And the pages: this check reads your <em>indexable</em> pages. A page you have set to
noindex is not asked about alt text here, which is deliberate — but note that the two
performance checks described below read a wider set, so a noindex page can appear in one image
finding and not another.</p>

<h2>Width and height, and where that subject lives</h2>

<p>The dimensions finding belongs to this check, so it is named here, but the causes and the
fix are a page of their own and are not repeated: <a href="/how-to/fix-layout-shift/">how to fix
layout shift</a> covers the reason browsers need the attributes, what to do when you cannot know
the dimensions, and the four other causes of shift that have nothing to do with images. Docket
links its own two findings on this for the same reason — the performance lane's layout-shift
risk finding carries a pointer back to this check as the owner of the remedy, so the action plan
asks for the work once while both lanes keep their deduction.</p>

<p>One caveat that page cannot give you, because it is about Docket rather than about CLS. The
extractor decides an image has dimensions if it has <code>width</code> and <code>height</code>
attributes, or if the word <code>aspect-ratio</code> appears in that element's own inline
<code>style</code> attribute. An <code>aspect-ratio</code> rule in your stylesheet reserves the
space perfectly well for a browser and is invisible to a crawler reading markup. If you took
that route and the finding did not clear, this is why — and the finding is wrong about your
page, not the other way round.</p>

<h2>The image findings that are not this check</h2>

<p>Docket splits image work across lanes, and two neighbours will show up in the same report
with the word "image" in them.</p>

<ul>
<li><strong>Image formats</strong> — <code>perf.modern_images</code>, in the performance lane.
It looks at file extensions and reports pages carrying several JPEGs or PNGs where WebP or AVIF
would do. Nothing to do with alt text; it never opens a file either, so it is reasoning from the
extension.</li>
<li><strong>Layout shift risk</strong> — <code>perf.cls_risk</code>, also performance. Same
missing width and height, seen per page as a proportion rather than a count, and stated as risk
rather than measurement because a crawl cannot measure Cumulative Layout Shift.</li>
<li><strong>Social preview images</strong> — the social lane, covered in <a
href="/how-to/fix-missing-open-graph-tags/">fixing a broken link preview</a>. An
<code>og:image</code> is not an <code>&lt;img&gt;</code> on your page and is checked
differently.</li>
</ul>

<p>The full list, with what each lane is for, is on <a href="/learn/what-docket-checks/">what
Docket checks</a> — every check on this page appears there under its own identifier, which is
the thing to search for when a finding's wording is not enough to place it.</p>

<h2>So: what actually matters</h2>

<p>Write alt text that describes the picture, in a short phrase, because a person using a screen
reader gets nothing else. Google's own image documentation puts the same thing in search terms:
it says Google uses alt text along with computer vision algorithms and the contents of the page
to understand the subject matter of the image, and it warns specifically against filling alt
attributes with keywords, which it calls keyword stuffing and says may cause a site to be seen
as spam. <a href="https://developers.google.com/search/docs/appearance/google-images">Google
Images documentation</a>, read {READ}.</p>

<p>Put an explicit empty alt on the decorative ones and stop counting them as debt. Add width
and height everywhere, because it is a find-and-replace and it is the highest-weighted finding this
check emits. Lazy-load the images below the fold on your heaviest pages and leave the
hero eager.</p>

<p>Everything else in the genre — renaming files to keyword strings, captioning every decorative
divider, chasing a green tick on an accessibility widget — is work that Docket will not credit
you for, because there is nothing there to measure.</p>

<p><a class="btn" href="/download/">Download Docket</a></p>
"""
    return render(
        cat="how-to", slug="fix-image-seo-problems",
        title="Which image SEO problems actually matter",
        desc=("Docket reads image markup, not pictures. What its image check counts, "
              "why an empty alt is correct, and which image advice is cargo cult."),
        h1="How to fix image SEO problems",
        crumb='<a href="/">Docket</a> / <a href="/how-to/">Fix it</a> / image problems',
        body=body,
        schema_type="Article",
        faq=[
            ("Does an empty alt attribute hurt SEO?",
             "No. An empty alt is the correct markup for a decorative image, and Docket "
             "deliberately does not count it as a problem. The W3C's accessibility guidance "
             "is that a null alt should be provided so assistive technology can skip the "
             "image, and that leaving the attribute out entirely is not an option because "
             "some screen readers then announce the file name instead."),
            ("Can an SEO tool tell whether my alt text is any good?",
             "No. A crawler reads the attribute; it never sees the picture, so it has "
             "nothing to compare the words against. It can tell you an alt attribute is "
             "missing. It cannot tell you that yours says 'banner-final' or repeats your "
             "brand name. Those are the ones most worth fixing."),
            ("Which image problem should I fix first?",
             "By Docket's own weighting, missing width and height attributes outrank "
             "missing alt attributes, and missing lazy loading comes last. Width and height "
             "is also the cheapest of them to fix, since it is usually a template "
             "change rather than writing anything."),
            ("Why does Docket report fewer images than my site has?",
             "It counts img elements in the HTML. Background images set in CSS, inline SVG "
             "and video poster frames are not counted, and an img whose address cannot be "
             "resolved from src, data-src, data-lazy-src or srcset is skipped by the "
             "missing-alt count."),
            ("I set aspect-ratio in my stylesheet. Why is the finding still there?",
             "Because Docket reads markup. It accepts width and height attributes, or "
             "aspect-ratio inside the element's own inline style attribute. A rule in an "
             "external stylesheet reserves the space correctly for a browser and is "
             "invisible to a crawler, so the finding is wrong about your page in that case."),
            ("Do I need to rename my image files for SEO?",
             "It is far down the list. Descriptive file names are mildly useful context, but "
             "no Docket check reads them, and keyword-stuffed names are closer to a risk "
             "than a gain. Alt text and declared dimensions are worth more than every file "
             "rename on your site put together."),
        ],
    )


BUILDERS = [howto_images]


def build_all() -> list[Path]:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build_all():
        print(p)
