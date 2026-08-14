#!/usr/bin/env python3
"""Render a Docket page into the site shell.

Same split as Crisp: this file owns the *chrome* — head, styles, nav, footer,
schema — and never generates prose. Every article's body is authored by hand in
`scripts/articles/*.py`. Sharing chrome across pages is fine and expected;
sharing phrasing is what trips the duplicate gate and what actually reads as
spam, so the body always comes from the caller.

Ships `Organization` + `SoftwareApplication` + `sameAs` on every page. Crisp's
own strategy audit recorded "no entity schema" as its single highest-ROI gap,
found months after launch — no reason to repeat that here.
"""
from __future__ import annotations

from pathlib import Path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import facts as _facts  # noqa: E402

SITE = Path(__file__).resolve().parent.parent / "site"
BASE = "https://docketseo.app"


def _check_counts() -> tuple:
    """`(checks, lanes)` read from the exported dataset.

    The count was hardcoded in nine places and went stale the moment the engine
    gained a lane. It is a fact about the product, so it is read from the
    product's own exported data and interpolated everywhere.
    """
    import csv
    path = pathlib.Path(__file__).resolve().parent.parent / "site" / "_data" / "checks.csv"
    with path.open() as fh:
        rows = list(csv.DictReader(fh))
    return len(rows), len({r["lane"] for r in rows})


N_CHECKS, N_LANES = _check_counts()


def _competitors() -> dict:
    """Every competitor row, keyed by slug.

    Same reason as the check count. Competitor prices were written into the
    prose of six pages, and an August 2026 check found four of them stale — one
    quoting a tier that no longer exists. A price is a fact about someone
    else's product, so it lives in one file and is interpolated.
    """
    import csv
    path = pathlib.Path(__file__).resolve().parent.parent / "site" / "_data" / "competitors.csv"
    with path.open() as fh:
        return {r["slug"]: r for r in csv.DictReader(fh)}


COMPETITORS = _competitors()


def price(slug: str) -> str:
    """The published price for a competitor, with en dashes for ranges."""
    return COMPETITORS[slug]["price_note"].replace("-", "–")


def price_note_html() -> str:
    """The dated caveat that must appear wherever competitor prices are shown.

    Ten competitor prices fed the homepage, the download page's three-year cost
    table and every comparison page, and not one carried a date. An undated
    price sits next to Docket's own price and reads as current forever.

    Only what was actually read from a vendor's page on a given day is dated
    here. Sitebulb's desktop pricing defeated every HTTP fetch — the prices are
    written in by script, so the markup carries placeholders — and it was
    listed as unread rather than quietly stamped, because a fetch that returns
    nothing is blindness, not a price. It was read on 2026-08-10 through
    `docket-render`, the WebKit helper Docket ships for JavaScript crawling:
    the tool built to see client-rendered pages can see this one.

    All ten are dated now, which is why the shared-date branch below exists —
    ten separate "checked on" stamps of the same date is a paragraph nobody
    finishes reading.

    **One figure here is derived, not read.** Sitebulb's yearly totals are not
    in the DOM at all; a billing toggle rewrites them client-side and the
    pre-toggle markup holds only the monthly rates. The annual pair is their
    monthly price less the 15% their own page advertises for yearly plans, and
    the note says so in the same breath rather than presenting arithmetic as a
    quotation.
    """
    checked = [(c["name"], c["price_checked"], c["price_source"])
               for c in COMPETITORS.values() if c.get("price_checked")]
    unchecked = [c["name"] for c in COMPETITORS.values() if not c.get("price_checked")]
    dates = {when for _, when, _ in checked}
    if checked and len(dates) == 1:
        links = "; ".join(f'<a href="{url}" rel="nofollow noopener">{name}</a>'
                          for name, _, url in sorted(checked))
        head = (f'<strong>Read from each vendor\'s own pricing page on '
                f'{dates.pop()}:</strong> {links}.')
    else:
        parts = [f'{name} checked {when} '
                 f'(<a href="{url}" rel="nofollow noopener">source</a>)'
                 for name, when, url in sorted(checked)]
        body = "; ".join(parts) if parts else "none checked recently"
        head = (f'<strong>Checked against the vendor\'s own pricing page:'
                f'</strong> {body}.')
    tail = ""
    if unchecked:
        # A count, not a list of names. The names are the wrong words to put
        # beside a price table, and the honest content is the number and the
        # instruction — the reader needs to know how much of this to trust and
        # what to do about it, not which vendors we ran out of time on.
        #
        # Singular is not decoration here. At len == 1 the plural read "The
        # other 1 were last confirmed earlier", which is the same defect as the
        # "Only 0%" this codebase already fixed once: a template that nobody
        # ran with the awkward number in it. It is unreachable at ten of ten
        # checked, and reachable the day an eleventh competitor is added —
        # which is exactly when nobody will be reading this line.
        tail = (' One other was last confirmed earlier and may have moved.'
                if len(unchecked) == 1 else
                f' The other {len(unchecked)} were last confirmed earlier and '
                f'may have moved.')
    return (f'<p class="price-caveat">{head}{tail} '
            f'Prices change; check before you buy, and tell us if one here is '
            f'wrong.</p>')

#: The current build. One place, because a download link that 404s is the
#: single worst bug a product site can have.
RELEASE = _facts.release_tag()
REPO = "https://github.com/mattkerr09/docket-site"
#: The contact channel, and the only one verified to receive anything. The
#: footer advertised hello@docketseo.app on all 25 pages; the domain has no MX
#: record and its address record is GitHub Pages, port 25 closed, so every
#: message bounced to a sender we never heard from. lint.py now resolves the
#: domain of any mailto: on the site and fails when it cannot accept mail.
ISSUES = f"{REPO}/issues"
DMG_NAME = _facts.dmg_name()
DMG = f"{REPO}/releases/download/{RELEASE}/{DMG_NAME}"
#: The Linux CLI. Empty when the release carries none, so a page can ask
#: rather than promise — the download page described a Linux tarball in
#: detail for seven releases during which none was published.
LINUX_NAME = _facts.linux_name()
LINUX = f"{REPO}/releases/download/{RELEASE}/{LINUX_NAME}" if LINUX_NAME else ""
LINUX_SIZE = _facts.linux_size_str()
#: Checksums for every artifact on the release, published so a Linux reader
#: has something to check. The Mac build has Apple's notarisation; this is
#: weaker and the page says so rather than implying parity.
SUMS = f"{REPO}/releases/download/{RELEASE}/SHA256SUMS"
#: What the DMG actually mounts as. build_docket.sh creates it with
#: `hdiutil create -volname "Docket ${VER}"`, and the about page documented
#: a bare /Volumes/Docket — so the codesign command it told every reader to
#: run returned "No such file or directory", on the page whose whole point
#: is that you should not have to take the signature on faith.
VOLUME = f"Docket {_facts.app_version()}"
#: Rounded DOWN from the real 17,432,048 bytes of the notarised DMG, measured
#: 2026-08-07. Rounding down is deliberate: a download is allowed to be smaller
#: than promised and never larger, and "18 MB" was already overstating it.
# Measured from the published artifact by collect_updater.py, not typed.
# It was "17 MB" against an 18.3 MB download.
DMG_SIZE = _facts.dmg_size_str()

#: One-time price, in USD. Declared once so the schema, the comparison table and
#: the download page cannot drift apart — which is exactly what happened to the
#: check count and the download size before they were centralised.
# Raised from 79 on 2026-08-14. Docket does what Screaming Frog (~$279/YEAR) and
# Sitebulb ($162-$2,940/year) do, and was charging $79 ONCE for it. That was not
# undercutting, it was a different order of pricing.
#
# The evidence is in this product's own code rather than in an opinion:
# backend/seo_engine/monitor.py exists, server.py starts and stops a scheduler,
# store.py keeps one snapshot per audit under history/<site_id>/<ts>.json and
# sizes retention with the comment "at weekly cadence that is ~4 years of
# history", and this site advertises "scheduled monitoring" in its own
# featureList. A one-shot audit tool would not need any of that.
#
# $199 is still less than ONE year of the cheapest serious competitor, so the
# position survives the rise intact.
PRICE = 199
PRICE_STR = f"${PRICE}"

#: What the download costs *today*, which is not PRICE. The beta is free, keeps
#: working, and has no checkout to pay through even if you wanted to.
#:
#: This is a fact rather than prose because it was prose, on two pages out of
#: twenty-five, while the other twenty-three said "$149 once" flatly and the
#: JSON-LD on all of them declared `price: 149, availability: InStock` — a
#: machine-readable claim to Google that a price existed to be paid. Docket's
#: own schema.price_not_visible check found it, which is the strongest argument
#: for the check that exists.
BETA_FREE = False
PRICE_TODAY = 0 if BETA_FREE else PRICE
#: The qualifier that travels with every mention of the price.
BETA_NOTE = (f"{RELEASE} is free while it is in beta; {PRICE_STR} applies "
             f"from v1.0." if BETA_FREE else "")

#: The same fact as a clause that can sit mid-sentence, because five pages were
#: writing their own version of it.
#:
#: "{RELEASE} is free while it is in beta" was hardcoded into about.py, two
#: comparison pages, the SaaS page and the download page. `BETA_FREE` went False
#: when Docket went on sale and every one of those kept saying it — the live
#: site called v1.1.0 a free beta, and the download page additionally promised
#: that $79 "applies from v1.0", a trigger that had already passed. Five copies,
#: one updated.
FREE_CLAUSE = (f"{RELEASE} is free while it is in beta"
               if BETA_FREE else
               f"{RELEASE} has no activation step yet, so it runs without a key")

#: Where the money is actually taken. Polar is the merchant of record; this link
#: is a checkout-link object on the `docketseo` organisation, whose product
#: "Docket SEO" is $79.00 one-time with a license_keys benefit attached.
#:
#: This existed and was unused. On 2026-08-14 the product, its price, its licence
#: benefit and this very link were all live in Polar while every page on the site
#: said "free in beta; $79 applies from v1.0" — a price with a trigger nobody had
#: scheduled to pull. The checkout was not the blocker. The version number was,
#: and Matthew resolved it in four words.
CHECKOUT = ("https://buy.polar.sh/"
            "polar_cl_FteABR6qSwOHHAOhrP1ObrzCOeVqsraAjhLZ323XgFR")

# --------------------------------------------------------------------------
# Who the money is paid to.
#
# DRAFT — none of the identity, tax or governing-law facts below have been
# reviewed by a lawyer. They are written from what the code and the company
# registration say, which is the right starting point and not a substitute for
# the review.
#
# The about page says "one person, in the UK". That is true about who writes
# the code and it is not the seller. A card processor's KYC, a merchant of
# record's customer-facing disclosure and a buyer asking "who am I paying" all
# want the entity. Declared here for the same reason PRICE is: three pages will
# state it and they must not drift apart.
# --------------------------------------------------------------------------
SELLER = "Kerr & Company LLC"
SELLER_CITY = "Grand Rapids, Michigan"
SELLER_COUNTRY = "United States"
#: The registered street address. EMPTY ON PURPOSE.
#:
#: Same shape as LINUX above — a page prints this line only when it is set, so
#: it asks rather than promises. A processor's onboarding review wants the full
#: postal address, and typing a plausible-looking street here to make the page
#: look finished would be the same defect as hello@docketseo.app: a detail that
#: reads as verified and is not.
SELLER_STREET = ""
#: The company number, once there is one to publish. Empty for the same reason.
SELLER_REG_NO = ""
#: Which law governs a dispute. Michigan, where the seller is.
GOVERNING_LAW = "the State of Michigan, United States"
#: Where a billing question goes. Empty until an address exists that can
#: receive one.
#:
#: This used to read "docketseo.app publishes no MX record, so every address at
#: it bounces". That was true when written and is no longer: resolved against
#: 8.8.8.8, 1.1.1.1 and 9.9.9.9 on 2026-08-13, the domain returns
#: `10 fwd1.porkbun.com` and `20 fwd2.porkbun.com`. Forwarding was configured at
#: some point and no check noticed, so the justification for this field being
#: empty had quietly expired while the field stayed empty.
#:
#: It stays empty anyway, for a narrower and still-honest reason. MX proves mail
#: reaches the DOMAIN. It does not prove a mailbox or forwarding row exists
#: behind a particular name, and at Porkbun each alias is a row somebody creates
#: by hand. A missing row bounces exactly like a missing mailbox and looks
#: identical from out here. Matthew has named support@docketseo.app as the
#: address; one real message sent and read is what promotes this from intended
#: to true, and that has not happened yet.
#:
#: A refund question is also the one message that must not go into a public
#: issue tracker, because it carries an order reference and a name. Until the
#: mailbox is confirmed, the refund page routes people to the receipt the
#: payment processor sends them and says plainly that this is why.
BILLING_EMAIL = "support@docketseo.app"
#: The company that will take the payment and appear on the card statement.
#: Not chosen. The pages say "not chosen" rather than naming a likely candidate,
#: because a buyer who reads a name here and sees a different one on their
#: statement has been told something false by us.
PROCESSOR = ""


def seller_address() -> str:
    """The seller's address, printing only the parts that are filled in."""
    return ", ".join(p for p in (SELLER_STREET, SELLER_CITY, SELLER_COUNTRY) if p)


# --------------------------------------------------------------------------
# Design system. Dark, high-contrast, indigo accent carried from the app icon.
# Indigo by measurement: the old amber sat 4 degrees of hue from the
# HIGH-severity colour, so brand chrome was indistinguishable from alarm.
# --warn stays amber, which is the semantic that colour should have had
# all along.
# --------------------------------------------------------------------------
STYLE = """<style>
/* Switzer, self-hosted at 74 KB. A Swiss grotesk rather than the geometric
   display faces this category defaults to: Docket is a measuring instrument that
   produces reports, and the type should read as precise rather than friendly.
   Self-hosted because Docket flags render-blocking third-party resources in its
   own audits, and shipping one would be the inconsistency it exists to catch. */
@font-face{font-family:'Switzer';src:url('/fonts/Switzer-400.woff2') format('woff2');
  font-weight:400;font-style:normal;font-display:swap}
@font-face{font-family:'Switzer';src:url('/fonts/Switzer-500.woff2') format('woff2');
  font-weight:500;font-style:normal;font-display:swap}
@font-face{font-family:'Switzer';src:url('/fonts/Switzer-600.woff2') format('woff2');
  font-weight:600;font-style:normal;font-display:swap}
@font-face{font-family:'Switzer';src:url('/fonts/Switzer-700.woff2') format('woff2');
  font-weight:700;font-style:normal;font-display:swap}
/* Clash Display and General Sans were declared here and never applied to a single
   element, and neither .woff2 is in site/fonts - only Switzer 400/500/600/700 are.
   Four @font-face blocks pointing at four 404s, styling nothing. Removed rather
   than fixed: the retheme uses Switzer throughout, so the files were never needed. */

:root{
  /* Paper, not a dashboard.
     Every SEO tool ships a dark neon dashboard, and Docket SEO is not a
     dashboard — it is a report about a website, read once and worked through.
     So: paper ground, hard 1px rules, no gradients, no glows, monospace for
     anything measured. It looks like an instrument, which is what it is, and
     it does not look like the eight other tools a buyer opened this week.
     The warmth in --bg is deliberate; pure #fff reads as an unstyled document. */
  --bg:#FBFAF7;--surface:#FFFFFF;--surface-2:#F2F1EC;--surface-3:#E6E4DC;
  --text:#16171A;--text-mid:#4A4D55;--text-dim:#5F636B;
  /* Deep teal, and deliberately NOT the desktop app's indigo. The app is a
     tool you run; this is paper you read, and #4338CA on a warm ground reads
     as a hyperlink from 2003. Measured on --bg / --surface-2 / --surface-3:
     --brand 9.08/8.38/7.44, --brand-light 11.50/10.62/9.43, and white on
     --brand is 9.48 — so it works as fill, as link text and as a rule.
     The app's own #818CF8 is 2.86:1 here and is not a candidate for anything.

     Every published image of the mark is rendered FROM this token by
     scripts/render_brand_assets.py, which is why the favicon cannot go on
     being indigo eight months after the site stopped being — it did, and
     nothing noticed until somebody looked at the file. */
  --brand:#134E4A;--brand-light:#0F3D3A;--brand-soft:rgba(19,78,74,.09);
  --on-accent:#FFFFFF;
  /* Severity, defined ONCE as a channel triple and derived from there.
     Every tinted background in this stylesheet is the severity colour at low
     alpha, and each one used to be a hand-copied `rgba(74,222,128,.18)` sitting
     next to `var(--ok)` on the same line — so a token change moved the fill and
     left the glow behind. That already happened once with amber: eight glows
     survived a token swap because no gate reads colour.
     `rgba(var(--ok-rgb),.18)` cannot drift; there is nothing to forget.

     These are the PAPER values, darkened from the dark-mode set until each one
     clears 4.5:1 as text. #FBBF24 amber is 1.7:1 on this ground — it is a fill
     colour on black and nothing else. Amber remains the warning semantic; that
     is exactly why the brand is not amber, and why a "safety orange" brand
     accent was rejected: it would make the brand colour and "this is a warning"
     the same colour. Measured on --bg / --surface-2 / --surface-3:
     ok 6.24/5.76/-, warn 5.81/5.36/4.76, bad 6.30/5.81/5.16. */
  --ok-rgb:19,108,52;--warn-rgb:122,95,0;--bad-rgb:180,35,24;
  --ok:rgb(var(--ok-rgb));--warn:rgb(var(--warn-rgb));--bad:rgb(var(--bad-rgb));
  /* On paper --bad is already 6.30:1, so the separate lighter tint the dark
     theme needed is gone: --bad-text is --bad. The dark theme's #ff9c92 existed
     because salmon-on-near-black needed hand-tuning; nothing here does. */
  --bad-text:var(--bad);
  --border:rgba(22,23,26,.14);--border-strong:rgba(22,23,26,.30);
  /* Hard corners. A 16px radius is the house style of every SaaS dashboard;
     4px reads as a printed rule, and 0 on the data surfaces reads as a table. */
  --radius:5px;--radius-sm:3px;
  --display:'Switzer',-apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;
  --sans:'Switzer',-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  /* One vertical rhythm for every section. Space is most of what separates a
     considered page from a cramped one. */
  --sec-y:clamp(5rem,11vw,9.5rem);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:17.5px;
  line-height:1.66;-webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;overflow-x:hidden;
  font-feature-settings:"ss03"}

/* No scroll-reveal. It was built twice — once hiding content by default, once
   arming from JavaScript with a timed backstop — and neither could be shown to
   work: IntersectionObserver does not fire in the webview used to verify this
   site, and nor did the setTimeout fallback.

   Shipping an effect that cannot be verified, on a page whose entire argument
   is that Docket reports only what it can prove, is the wrong trade. The type,
   spacing and depth carry the page; content renders immediately and is never
   contingent on a script.

   The rule that used to be here left its closing brace behind when it was
   deleted, and a stray `}` at the top level made the browser discard the very
   next rule — which was the one giving every link its colour. Every body link
   on every article rendered in default browser blue on a near-black page for
   as long as that brace survived, and no gate on this site looks at colour. */
a{color:var(--brand-light);text-decoration:none;transition:color .16s}
/* --- instrument, not dashboard -------------------------------------------
   Monospace carries every label, eyebrow and measured value. Prose stays in
   the sans, because a whole page of mono is a pose rather than a choice. The
   hard rules replace the soft panel fills the dark theme leaned on: on paper a
   1px line separates better than a 4% wash, and it survives being printed,
   which a report about a website eventually is. */
.eyebrow,.split-phase,.mock-rank,.rank-row .n,.split-list .n{font-family:var(--mono)}
.eyebrow{font-weight:600}
table{border-collapse:collapse}
th,td{border-bottom:1px solid var(--border)}
th{font-family:var(--mono);font-size:.72rem;letter-spacing:.08em;
  text-transform:uppercase;color:var(--text-mid);font-weight:600}
code,kbd,samp{background:var(--surface-2);border:1px solid var(--border)}
::selection{background:var(--brand);color:var(--on-accent)}
@media(hover:hover){a:hover{color:var(--text);text-decoration:underline}}
.wrap{width:min(820px,calc(100% - 2rem));margin:0 auto}
.wrap-wide{width:min(1080px,calc(100% - 2rem));margin:0 auto}

nav{position:sticky;top:0;z-index:20;background:rgba(251,250,247,.90);
  backdrop-filter:blur(14px);border-bottom:1px solid var(--border)}
.nav-inner{display:flex;align-items:center;justify-content:space-between;height:60px;gap:1rem}
.nav-brand{display:flex;align-items:center;gap:.55rem;font-weight:750;color:var(--text);
  font-size:1.1rem;letter-spacing:-.02em}
.nav-brand i{font-style:normal;font-family:var(--mono);font-weight:600;font-size:.74em;
  letter-spacing:.04em;color:var(--brand);margin-left:.28em;
  border:1px solid var(--brand);border-radius:2px;padding:.02em .3em}
.nav-brand:hover{text-decoration:none;color:var(--brand-light)}
.nav-links{display:flex;gap:1.35rem;font-size:.94rem}
.nav-links a{color:var(--text-mid)}
@media(hover:hover){.nav-links a:hover{color:var(--text);text-decoration:none}}
@media(max-width:780px){
  /* `height` cannot contain a wrapped row, so the links overflowed the sticky
     bar by 19px and floated over the page with no background behind them once
     scrolled. Measured at 375px: nav box ended at 61, links ended at 80. */
  .nav-inner{flex-wrap:wrap;row-gap:.55rem;height:auto;min-height:60px;
    padding-bottom:.5rem}
  /* These wrap. They used to be a scroll rail with the gap tuned to the exact
     width of the links, and that is why this comment is longer than the rule.

     The first version noted: "The six links total 273px of text at this size.
     At a 1.15rem gap they needed 365px in a 343px rail, so About was clipped
     to Ab at 375px. Measured: they fit at any gap up to 14px" — and set the gap
     to 12.8px. Correct, measured, and true of *six* links.

     A seventh (Best) was added later. Seven total 307px, which at that same gap
     needs 383px in the same 343px rail, so About went back off the edge — sitting
     at x=360-399 in a 375px viewport, reachable only by a horizontal swipe with
     nothing on screen suggesting one. The fade that would have hinted at it was
     behind `max-width:359px`, so at 375px there was no affordance at all. The
     live gate caught it; the pre-deploy gate did not, which is fixed too.

     A constant tuned to today's link count is a fix with an expiry date nobody
     writes down. Wrapping has no such number in it: the nav grows a second row
     instead of hiding its last item, at any count and any width. It costs ~26px
     of vertical space on phones when it wraps, and that is the whole trade. */
  .nav-links{order:3;width:100%;gap:.55rem .8rem;font-size:.88rem;
    flex-wrap:wrap;padding-bottom:.15rem}
  .nav-links a{white-space:nowrap}
  /* Stacked CTAs were 200px and 185px against a 343px column — a ragged right
     edge on the most-looked-at element of the page. Full width once they wrap. */
  .hero-cta{gap:.6rem}
  .hero-cta>*{width:100%;text-align:center}
}
.btn{display:inline-block;background:var(--brand);
  color:var(--on-accent);font-weight:600;box-shadow:none;
  none;
  padding:.62rem 1.2rem;border-radius:10px;font-size:.95rem;border:0;cursor:pointer}
.btn:hover{background:var(--brand-light);color:var(--on-accent);text-decoration:none}
.btn-ghost{display:inline-block;border:1px solid var(--border-strong);color:var(--text-mid);
  padding:.6rem 1.15rem;border-radius:10px;font-size:.95rem;font-weight:600}
.btn-ghost:hover{background:var(--surface-2);color:var(--text);text-decoration:none}

article{padding:2.8rem 0 4.5rem}
.foot-h{font-size:.82rem;font-weight:600;letter-spacing:.02em;text-transform:none;
  color:var(--text);margin:0 0 .55rem;font-family:var(--sans)}
.crumb{font-family:var(--mono);font-size:.75rem;color:var(--text-dim);
  text-transform:uppercase;letter-spacing:.1em;margin-bottom:1rem}
.crumb a{color:var(--text-dim)}
h1{font-size:2.3rem;line-height:1.14;letter-spacing:-.03em;margin-bottom:1rem}
h2{font-size:1.5rem;letter-spacing:-.02em;margin:2.6rem 0 .9rem}
h3{font-size:1.13rem;margin:1.7rem 0 .5rem}
p{color:var(--text-mid);margin-bottom:1rem}
strong{color:var(--text);font-weight:650}
.lede{font-size:1.17rem;color:var(--text);margin-bottom:1.4rem}
ul,ol{color:var(--text-mid);margin:0 0 1.1rem 1.25rem}
li{margin-bottom:.42rem}
blockquote{border-left:3px solid var(--brand);padding:.2rem 0 .2rem 1.1rem;
  margin:1.3rem 0;color:var(--text)}
code{font-family:var(--mono);font-size:.88em;background:var(--surface-2);
  padding:.14em .4em;border-radius:5px;color:var(--brand-light)}
pre{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-sm);
  padding:1rem 1.1rem;overflow-x:auto;margin:1.2rem 0;font-size:.86rem;line-height:1.6}
pre code{background:0;padding:0;color:var(--text-mid)}

table.cmp{width:100%;border-collapse:collapse;margin:1.4rem 0;font-size:.94rem}
table.cmp th,table.cmp td{text-align:left;padding:.66rem .72rem;
  border-bottom:1px solid var(--border);vertical-align:top}
table.cmp th{color:var(--text-dim);font-size:.78rem;text-transform:uppercase;
  letter-spacing:.06em;font-weight:650}
table.cmp td:first-child{color:var(--text);font-weight:600}
.yes{color:var(--ok);font-weight:650}
.no{color:var(--bad)}
.wrap-tbl{overflow-x:auto;margin:1.4rem 0}

.callout{background:var(--surface);border:1px solid var(--border);
  border-left:3px solid var(--brand);border-radius:var(--radius-sm);
  padding:1.05rem 1.2rem;margin:1.5rem 0}
.callout p:last-child{margin-bottom:0}
.callout-title{color:var(--brand-light);font-weight:700;font-size:.8rem;
  text-transform:uppercase;letter-spacing:.07em;margin-bottom:.4rem}

.stat-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:.8rem;margin:1.6rem 0}
.stat{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-sm);padding:1rem 1.1rem}
.stat b{display:block;font-size:1.85rem;letter-spacing:-.03em;color:var(--text);
  line-height:1.1;font-weight:700}
.stat span{font-size:.82rem;color:var(--text-dim)}

footer{border-top:1px solid var(--border);padding:2.6rem 0 3rem;margin-top:3rem;
  font-size:.9rem;color:var(--text-dim)}
.foot-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));
  gap:1.6rem;margin-bottom:2rem}
.foot-grid h4{font-size:.76rem;text-transform:uppercase;letter-spacing:.08em;
  color:var(--text-dim);margin-bottom:.6rem;font-weight:650}
.foot-grid a{display:block;color:var(--text-mid);padding:.17rem 0;font-size:.92rem}
.foot-bottom{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;
  border-top:1px solid var(--border);padding-top:1.3rem}

/* ============ Landing page only ============
   The article shell is a single 820px column, which is right for reading and
   wrong for a homepage. These rules only apply on pages that opt in via
   body.landing, so the article template is untouched. */
body.landing article{padding:0}
.hero-sec{padding:3.2rem 0 4.5rem;position:relative;overflow:hidden}
/* Ambient light. A flat dark page reads as unlit; two soft pools give the
   canvas depth without anything on it looking decorated. */
/* The substrate the hero sits on. This used to be two indigo radial glows —
   the exact device every dark SaaS homepage uses, and the reason this site was
   indistinguishable from eight others a buyer had already opened. A ruled grid
   says instrument instead: graph paper under a measurement.
   Kept faint on purpose. It reads at the edges of the type and disappears
   behind it; a grid you notice is a grid competing with the headline.
   The pseudo-element itself is load-bearing beyond decoration — visual_check
   asserts it generates, because a stray brace once ate this rule silently. */
.hero-sec::before{content:"";position:absolute;inset:0 -10% auto -10%;height:100%;
  background:
    repeating-linear-gradient(90deg,rgba(22,23,26,.055) 0 1px,transparent 1px 72px),
    repeating-linear-gradient(0deg,rgba(22,23,26,.055) 0 1px,transparent 1px 72px);
  background-position:center top;
  -webkit-mask-image:linear-gradient(180deg,#000 55%,transparent);
  mask-image:linear-gradient(180deg,#000 55%,transparent);
  pointer-events:none;z-index:0}
.hero-grid{position:relative;z-index:1}

/* The product sits on light rather than beside it. */
.mock{position:relative;transform:perspective(1600px) rotateY(-3.5deg) rotateX(1.5deg);
  transform-origin:left center;
  box-shadow:none;
             0 1px 0 var(--border-strong),
             0 0 0 1px var(--border);
  transition:transform .6s cubic-bezier(.16,1,.3,1)}
@media(hover:hover){.mock:hover{transform:perspective(1600px) rotateY(-1.5deg) rotateX(.5deg)}}
@media(max-width:940px){.mock{transform:none}.mock:hover{transform:none}}

/* ---- the signature: a list becoming an order ------------------------------
   Docket's whole claim is that it ranks. Saying so is weaker than showing it, so
   the rows arrive unordered and settle into sequence as the section enters. One
   move, once, on the one idea the product is actually about. */
.rank-demo{display:grid;gap:.6rem;margin:2rem 0 0}
.rank-row{display:flex;align-items:center;gap:.9rem;background:var(--surface-2);
  border:1px solid var(--border);border-radius:11px;padding:.85rem 1.05rem;
  font-size:.95rem;color:var(--text-mid)}
.rank-row .n{flex:none;width:26px;height:26px;border-radius:8px;display:grid;
  place-items:center;font-family:var(--mono);font-size:.78rem;font-weight:600;
  background:var(--surface-3);color:var(--text-dim)}
.rank-row.hot .n{background:var(--brand);color:var(--on-accent)}
.rank-row.hot{color:var(--text);border-color:var(--brand)}
/* No entrance animation here. It was built, and IntersectionObserver turned out
   not to fire at all in the webview used to verify it — so the effect could not
   be confirmed working, only confirmed shipped. A motion effect that cannot be
   verified is a liability on a page whose whole argument is rigour, and a
   static ranked list makes the same point without one.

   Second orphaned brace of the same kind, found by the same look. This one was
   dropping `.hero-sec::before` — the glow behind the homepage hero — so that
   effect was designed, shipped, and never once rendered.

   That repair then went wrong in a quieter way: it wrote a *replacement*
   `.hero-sec::before` here instead of removing the brace that was eating the
   original one above. Both fixes landed, so the page carried two rules for the
   same pseudo-element and the later one won — a single centred brand ellipse,
   where the rule at the top of this sheet asks for two pools.
   The glow rendered, the brace gate passed, and the design still was not the
   one anybody wrote. The duplicate is gone; the original is the live rule. */
.hero-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:3.2rem;
  align-items:center;position:relative}
@media(max-width:940px){.hero-grid{grid-template-columns:1fr;gap:2.4rem}}
.eyebrow{display:inline-flex;align-items:center;gap:.55rem;font-family:var(--mono);
  font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--brand-light);
  background:var(--brand-soft);
  border:1px solid var(--border-strong);border-radius:2px;padding:.5rem 1.05rem;
  margin-bottom:1.9rem}
.eyebrow::before{content:"";width:6px;height:6px;border-radius:50%;
  background:var(--ok);box-shadow:0 0 0 3px rgba(var(--ok-rgb),.18)}
.hero-h1{font-family:var(--display);font-weight:700;
  /* 84px at the top end, matching the scale premium product sites settle on.
     Tight tracking is what stops large type reading as merely big. */
  font-size:clamp(2.5rem,5.6vw,4.3rem);line-height:1.02;letter-spacing:-.035em;
  margin:0 0 1.35rem;max-width:15ch}
.hero-h1 em{font-style:normal;color:var(--brand-light);display:block}
.hero-h1 em{font-style:normal;color:var(--brand);display:block;
  -webkit-text-fill-color:currentColor}
.hero-sub{font-size:1.11rem;color:var(--text-mid);max-width:33rem;margin-bottom:1.9rem;line-height:1.6}
.hero-cta{display:flex;gap:.7rem;flex-wrap:wrap;align-items:center;margin-bottom:1.1rem}
.btn-lg{padding:1rem 2.05rem;font-size:1.02rem;border-radius:13px;letter-spacing:-.01em}
.hero-note{font-size:.86rem;color:var(--text-dim)}

/* Product mockup — an HTML replica of the app, not a screenshot. Stays sharp at
   any density, weighs nothing, and follows the page theme. */
.mock{background:var(--surface);border:1px solid var(--border-strong);border-radius:16px;
  box-shadow:0 1px 0 var(--border-strong);border:1px solid var(--border-strong);overflow:hidden}
.mock-bar{display:flex;align-items:center;gap:.45rem;padding:.62rem .85rem;
  background:var(--surface-2);border-bottom:1px solid var(--border)}
.mock-dot{width:10px;height:10px;border-radius:99px;background:var(--surface-3)}
.mock-title{margin-left:.5rem;font-size:.74rem;color:var(--text-dim);font-family:var(--mono)}
.mock-body{padding:1.05rem}
.mock-top{display:flex;gap:1.05rem;align-items:center;margin-bottom:1rem}
.mock-score{font-size:1.95rem;font-weight:720;letter-spacing:-.03em;line-height:1}
.mock-verdict{font-size:.86rem;color:var(--text-mid);line-height:1.45}
.mock-chips{display:flex;gap:.32rem;margin-top:.45rem;flex-wrap:wrap}
.mock-chip{font-size:.66rem;font-weight:680;padding:.13rem .48rem;border-radius:99px}
.mock-lanes{display:grid;grid-template-columns:1fr 1fr;gap:.42rem}
.mock-lane{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:.5rem .62rem}
.mock-lane-top{display:flex;justify-content:space-between;align-items:baseline;gap:.4rem}
.mock-lane-name{font-size:.7rem;color:var(--text-mid)}
.mock-lane-score{font-size:.86rem;font-weight:700}
.mock-lane-bar{height:3px;border-radius:0;background:var(--surface-3);margin-top:.36rem;overflow:hidden}
.mock-lane-bar i{display:block;height:100%;border-radius:99px}
.mock-find{background:var(--surface-2);border:1px solid var(--border);border-left:2px solid var(--bad);
  border-radius:8px;padding:.6rem .7rem;margin-top:.55rem}
.mock-find-h{display:flex;gap:.45rem;align-items:center;font-size:.76rem;font-weight:640;color:var(--text)}
.mock-rank{background:var(--brand-soft);color:var(--brand-light);font-size:.62rem;font-weight:720;
  width:16px;height:16px;border-radius:4px;display:flex;align-items:center;justify-content:center;flex:0 0 auto}
.mock-find-p{font-size:.68rem;color:var(--text-dim);margin:.3rem 0 0 1.35rem;line-height:1.45}

/* Sections */
.sec{padding:var(--sec-y) 0}
/* Hairlines between every section made the page read as a stack of boxes.
   Space separates them now; a rule is used only where one is doing work. */
.sec + .sec{border-top:1px solid var(--border)}
.sec-head{text-align:center;max-width:41rem;margin:0 auto 2.6rem}
.sec-head h2{font-family:var(--display);font-weight:700;
  font-size:clamp(1.9rem,4vw,2.85rem);line-height:1.1;
  letter-spacing:-.03em;margin:0 0 .85rem}
.sec-head h2 em{font-style:normal;color:var(--brand-light)}
.sec-head p{font-size:1.04rem;color:var(--text-mid);margin:0}
.grid-3{display:grid;grid-template-columns:repeat(auto-fit,minmax(268px,1fr));gap:1rem}
.card{background:var(--surface);border:1px solid var(--border);border-radius:13px;padding:1.4rem 1.5rem;
  transition:border-color .18s,transform .18s}
.card:hover{border-color:var(--border-strong);transform:translateY(-2px)}
.card-ico{width:36px;height:36px;border-radius:9px;background:var(--brand-soft);color:var(--brand-light);
  display:flex;align-items:center;justify-content:center;margin-bottom:.85rem}
.card h3{font-size:1.03rem;margin:0 0 .45rem}
.card p{font-size:.92rem;margin:0;color:var(--text-mid)}
.card.wide{grid-column:1/-1}

/* Before/after: a list vs a sequence */
.split{display:grid;grid-template-columns:1fr 1fr;gap:1rem}
@media(max-width:760px){.split{grid-template-columns:1fr}}
.split-col{background:var(--surface);border:1px solid var(--border);border-radius:13px;padding:1.3rem 1.4rem}
.split-col.good{border-color:var(--brand)}
.split-tag{font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:var(--text-dim);margin-bottom:.8rem}
.split-col.good .split-tag{color:var(--brand-light)}
.split-list{list-style:none;margin:0;padding:0;font-size:.88rem}
.split-list li{padding:.42rem 0;border-bottom:1px solid var(--border);color:var(--text-mid);
  display:flex;gap:.55rem;align-items:flex-start}
.split-list li:last-child{border-bottom:0}
.split-list .n{color:var(--brand-light);font-weight:700;font-family:var(--mono);font-size:.78rem;flex:0 0 auto}
.split-phase{font-size:.66rem;text-transform:uppercase;letter-spacing:.07em;color:var(--brand-light);
  font-weight:700;padding-top:.6rem}

/* Index chart, drawn from the measured dataset */
.chart{background:var(--surface);border:1px solid var(--border);border-radius:13px;padding:1.5rem 1.6rem}
.bar-row{display:grid;grid-template-columns:130px 1fr 46px;gap:.85rem;align-items:center;margin-bottom:.62rem}
.bar-lbl{font-size:.83rem;color:var(--text-mid);text-align:right}
.bar-track{height:9px;background:var(--surface-3);border-radius:0;overflow:hidden}
.bar-fill{display:block;height:100%;border-radius:99px;
  background:var(--brand)}
.bar-val{font-size:.82rem;font-weight:680;color:var(--text);font-variant-numeric:tabular-nums}
.chart-note{font-size:.8rem;color:var(--text-dim);margin:1.1rem 0 0}
/* Prose inside a wide container. `.wrap-wide` is 1080px so a comparison
   table is not cramped; a table wants that width and a sentence does not.
   Measured on the live homepage at 1600px: the pricing caveat ran 1080px
   wide across 316 characters, about 140 characters a line, and the chart
   note 1027px. Ordinary paragraphs sit at 820px because .wrap caps them.
   Found by probing a width the visual gate had never rendered. */
.price-caveat,.chart-note,.claims-note{max-width:68ch}

.cta-band{text-align:center;padding:4.2rem 0}
.cta-band h2{font-size:clamp(1.7rem,3vw,2.3rem);letter-spacing:-.028em;margin-bottom:.7rem}
.cta-band p{font-size:1.05rem;color:var(--text-mid);max-width:34rem;margin:0 auto 1.6rem}
.faq{padding:var(--sec-y) 0}
.faq h2{margin:0 0 1.2rem}
.faq-item{border-top:1px solid var(--border);padding:1.15rem 0}
.faq-item h3{font-size:1rem;margin:0 0 .4rem}
.faq-item p{font-size:.93rem;margin:0}
</style>
"""


def _mark(size: int = 22, color: str = "var(--brand)") -> str:
    """The Docket shield, inline so there is no extra request and no flash."""
    return (
        f'<svg viewBox="0 0 1024 1024" width="{size}" height="{size}" aria-hidden="true">'
        f'<path d="M512 122 L866 242 L866 522 C866 706 714 838 512 902 '
        f'C310 838 158 706 158 522 L158 242 Z" fill="{color}"/>'
        f'<g fill="none" stroke="var(--bg)" stroke-width="112" stroke-linecap="round" '
        f'stroke-linejoin="round"><path d="M348 636 L676 396"/>'
        f'<path d="M540 388 L688 388 L688 536"/></g></svg>'
    )


NAV = f"""<nav><div class="wrap-wide nav-inner">
<a class="nav-brand" href="/">{_mark(23)}<span>Docket<i>SEO</i></span></a>
<div class="nav-links">
<a href="/index/">The Index</a>
<a href="/learn/">Learn</a>
<a href="/vs/">Compare</a>
<a href="/best/">Best</a>
<a href="/how-to/">Fix it</a>
<a href="/for/">For you</a>
<a href="/about/">About</a>
</div>
<a class="btn" href="/download/">Download Docket SEO</a>
</div></nav>"""

FOOTER = f"""<footer><div class="wrap-wide">
<div class="foot-grid">
<div><h2 class="foot-h">Docket SEO</h2>
<a href="/">Overview</a><a href="/download/">Download Docket SEO for Mac</a>
<a href="/index/">The Docket Index</a><a href="/learn/what-docket-checks/">What it checks</a></div>
<div><h2 class="foot-h">Compare</h2>
<a href="/vs/screaming-frog-alternative/">vs Screaming Frog</a>
<a href="/vs/sitebulb-alternative/">vs Sitebulb</a>
<a href="/vs/ahrefs-site-audit-alternative/">vs Ahrefs</a>
<a href="/vs/semrush-site-audit-alternative/">vs Semrush</a>
<a href="/vs/">All comparisons</a></div>
<div><h2 class="foot-h">Learn</h2>
<a href="/learn/ai-search-visibility/">AI search visibility</a>
<a href="/learn/seo-audit/">What an SEO audit is</a>
<a href="/learn/">All guides</a></div>
<div><h2 class="foot-h">Contact</h2>
<a href="/about/">About Docket</a>
<a href="/contact/">Get in touch</a>
<a href="{REPO}/issues">Issue tracker</a>
<a href="/legal/privacy/">Privacy</a><a href="/legal/terms/">Terms</a>
<a href="/legal/refunds/">Refunds</a></div>
</div>
<div class="foot-bottom">
<span>© 2026 Docket SEO · Audits run on your Mac. Nothing is uploaded.</span>
<span>{_mark(15, "var(--text-dim)")}</span>
</div></div></footer>"""


def _breadcrumb_schema(crumb: str) -> str:
    """BreadcrumbList built from the crumb already on the page.

    Derived from the visible trail rather than declared separately, so the
    markup and what a reader sees cannot drift. Without it a result shows the
    raw URL where it could show the path.
    """
    import re as _re

    parts = _re.findall(r'<a href="([^"]+)">([^<]+)</a>|>\s*([^<>]+?)\s*$', crumb)
    items, position = [], 0
    for href, label, tail in parts:
        name = (label or tail or "").strip()
        if not name:
            continue
        position += 1
        entry = ('{"@type":"ListItem","position":' + str(position)
                 + ',"name":"' + name.replace('"', "'") + '"')
        if href:
            entry += ',"item":"' + BASE + href + '"'
        items.append(entry + "}")
    if len(items) < 2:
        return ""
    # Bare JSON — the caller wraps every block in its own <script> tag, and
    # returning one here nested them and produced a block that would not parse.
    return ('{"@context":"https://schema.org","@type":"BreadcrumbList",'
            '"itemListElement":[' + ",".join(items) + "]}")


def _entity_schema() -> str:
    """Organization + SoftwareApplication + sameAs, on every page.

    `sameAs` is what lets a language model resolve "Docket" to this specific
    product rather than the dozen other things called Docket — the single
    highest-leverage piece of markup for being cited by name.

    Only two entries, both verified to resolve, because /learn/sameas-entity-signals/
    says on this same site that padding the array with URLs you do not control
    weakens the signal. There is no social presence yet; when there is, it goes
    here and nowhere else.
    """
    return (
        '{"@context":"https://schema.org","@graph":['
        '{"@type":"Organization","@id":"' + BASE + '/#org",'
        '"name":"Docket SEO","url":"' + BASE + '/",'
        '"logo":"' + BASE + '/icon.png",'
        '"description":"Docket makes local SEO and marketing audit software for Mac.",'
        '"sameAs":["https://github.com/mattkerr09",'
        '"https://github.com/mattkerr09/docket-site"]},'
        '{"@type":"WebSite","@id":"' + BASE + '/#site",'
        '"url":"' + BASE + '/","name":"Docket SEO",'
        '"publisher":{"@id":"' + BASE + '/#org"}},'
        '{"@type":"SoftwareApplication","@id":"' + BASE + '/#app",'
        '"name":"Docket SEO","applicationCategory":"BusinessApplication",'
        '"applicationSubCategory":"SEO audit software",'
        '"operatingSystem":"macOS 12 or later, Apple Silicon",'
        '"description":"Docket crawls a website, runs ' + str(N_CHECKS) + ' checks across SEO, copy, '
        'speed, structured data, local visibility, AI search visibility and marketing '
        'conversion, and returns a ranked list of what to fix. Runs entirely on your Mac.",'
        # PRICE_TODAY, not PRICE. Structured data states what a visitor would
        # pay now; the future price is prose, not an Offer. Declaring 149 while
        # the beta is free let Google advertise a number with no checkout
        # behind it.
        '"offers":{"@type":"Offer","price":"' + str(PRICE_TODAY) + '","priceCurrency":"USD",'
        '"availability":"https://schema.org/InStock"},'
        '"featureList":"' + str(N_CHECKS) + ' checks, ranked action plan, PDF report, scheduled monitoring, '
        'competitor comparison, AI crawler access audit",'
        '"publisher":{"@id":"' + BASE + '/#org"}}]}'
    )


#: Plausible, added by Matthew on 2026-08-13. It lived in `site/index.html`,
#: which is generated — the next build deleted it, and would have deleted it
#: again after every deploy. It belongs here, where the page shell is written.
#:
#: Putting it in the shared head puts it on every page rather than the homepage
#: alone. That was the choice made when the privacy policy was corrected to
#: match: the policy speaks about "this website", so the two now describe the
#: same thing.
ANALYTICS = (
    '<!-- Privacy-friendly analytics by Plausible -->\n'
    '<script async src="https://plausible.io/js/pa-9WvL8kBqk1wanjcZqTHu4.js"></script>\n'
    '<script>\n'
    'window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},'
    'plausible.init=plausible.init||function(i){plausible.o=i||{}};\n'
    'plausible.init()\n'
    '</script>\n'
    # Sled affiliate attribution, added 2026-08-14. Sets a ta_ref cookie ONLY when a
    # visitor arrives through an affiliate link; an ordinary visitor gets none. The
    # privacy page was rewritten in the same change — it said the site "sets no
    # cookies" and runs "one third-party script", and Sled falsifies both.
    #
    # Docket was the last of the four sites without it. The ops board read "tracker
    # verified real and serving", which was true of crispvideo.app alone, so an
    # affiliate who sent somebody here earned nothing and had no way to know.
    '<script async src="https://usesled.com/kerr-and-company/t.js"></script>'
)


def render(
    *,
    cat: str,
    slug: str,
    title: str,
    desc: str,
    h1: str,
    crumb: str,
    body: str,
    published: str = "2026-08-06",
    modified: str | None = None,
    schema_type: str = "Article",
    faq: list[tuple[str, str]] | None = None,
    wide: bool = False,
    landing: bool = False,
    filename: str = "index.html",
    noindex: bool = False,
) -> Path:
    """Write one page. `body` is the caller's authored HTML — never generated here."""
    # A hub page is a cat with no slug. Joining blindly gives "/vs//", which
    # canonicalises the page to a URL it is not served from — the canonical then
    # argues against itself. Crisp hit exactly this.
    path_parts = [p for p in (cat, slug) if p]
    url = BASE + "/" + ("/".join(path_parts) + "/" if path_parts else "")
    esc = lambda s: s.replace('"', "&quot;")  # noqa: E731

    blocks = [_entity_schema()]
    crumb_schema = _breadcrumb_schema(crumb)
    if crumb_schema:
        blocks.append(crumb_schema)
    if schema_type:
        blocks.append(
            '{"@context":"https://schema.org","@type":"' + schema_type + '",'
            f'"headline":"{esc(h1)}","description":"{esc(desc)}",'
            f'"datePublished":"{published}","dateModified":"{modified or published}",'
            '"author":{"@type":"Person","name":"Matt Kerr",'
            '"description":"Builds Docket. Every number on this site comes from running it."},'
            '"publisher":{"@id":"' + BASE + '/#org"},'
            f'"mainEntityOfPage":"{url}","inLanguage":"en"}}'
        )
    # The questions go on the page, not only into the schema.
    #
    # `faq` built a FAQPage block and nothing else. The Q&A existed in JSON-LD
    # and appeared nowhere a reader or a model reading the rendered page could
    # see it — and the `.faq-item` rules in the stylesheet had been styling
    # markup nothing emitted. Docket's own ai.no_question_headings finding was
    # the symptom: zero question-form headings across the article set, on a
    # site whose every article ships four good questions.
    #
    # Google retired the FAQ rich result in June 2026, so the schema wins
    # nothing there now. The visible version is the whole point: it answers the
    # reader, and it gives an answer engine a self-contained passage to lift.
    faq_html = ""
    if faq:
        items = "".join(
            f'<div class="faq-item"><h3>{q}</h3><p>{a}</p></div>' for q, a in faq
        )
        # `.wrap` matters here: every other block on the page is inside one, and
        # the FAQ was emitted bare. On a wide window it ran flush to both edges
        # of the viewport with zero left padding while the nav and footer above
        # and below it stayed centred — visible immediately in a screenshot and
        # invisible to every gate, because nothing overflowed and no link broke.
        faq_html = (f'<section class="faq"><div class="wrap">'
                    f'<h2>Common questions</h2>{items}</div></section>')

    if faq:
        qa = ",".join(
            '{"@type":"Question","name":"' + esc(q) + '",'
            '"acceptedAnswer":{"@type":"Answer","text":"' + esc(a) + '"}}'
            for q, a in faq
        )
        blocks.append(
            '{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[' + qa + "]}"
        )

    schema = "\n".join(
        f'<script type="application/ld+json">{b}</script>' for b in blocks
    )
    wrap_class = "wrap-wide" if wide else "wrap"

    # A landing page supplies its own full-bleed sections; an article gets the
    # single reading column with a breadcrumb and an H1 above it.
    if landing:
        body_class = ' class="landing"'
        opening = "<article>"
        closing = "</article>"
    else:
        body_class = ""
        opening = (f'<article><div class="{wrap_class}">'
                   f'<div class="crumb">{crumb}</div><h1>{h1}</h1>')
        closing = "</div></article>"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#FBFAF7">
{'<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{url}">'}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="{'website' if schema_type == 'WebPage' else 'article'}">
<meta property="og:title" content="{esc(h1)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Docket SEO">
<meta property="og:image" content="{BASE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(h1)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{BASE}/og.png">
{STYLE}
{schema}
{ANALYTICS}
</head>
<body{body_class}>
{NAV}
{opening}
{body}{faq_html}
{closing}
{FOOTER}
</body>
</html>
"""

    out_dir = SITE.joinpath(*path_parts) if path_parts else SITE
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / filename
    out.write_text(html, encoding="utf-8")
    return out
