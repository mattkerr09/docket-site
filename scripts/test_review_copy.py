#!/usr/bin/env python3
"""Offline regression checks for the review copy. Run against either built brand."""
from __future__ import annotations

import datetime as dt
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brand
import render
from articles import pages
from test_rename_brand import CONTENT_UPDATED
from verify_structured_data_matches_page import blocks, norm, visible


class Metadata(HTMLParser):
    def __init__(self, raw):
        super().__init__()
        self.values = {}
        self.feed(raw)

    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            attrs = dict(attrs)
            self.values[attrs.get("name", attrs.get("property"))] = attrs.get("content", "")


class ReviewCopyTests(unittest.TestCase):
    def raw(self, route):
        return (render.SITE / route / "index.html").read_text()

    def text(self, route):
        return visible(self.raw(route))

    def faq(self, route, question):
        block = next(b for b in blocks(self.raw(route)) if b.get("@type") == "FAQPage")
        return next(q["acceptedAnswer"]["text"] for q in block["mainEntity"]
                    if q["name"] == question)

    @unittest.skipUnless(brand.SITE_BRAND == "checkengine", "Check Engine copy limits")
    def test_all_indexable_descriptions_and_faq_answers(self):
        checked = 0
        for page in render.SITE.rglob("*.html"):
            raw = page.read_text()
            meta = Metadata(raw).values
            if "noindex" in meta.get("robots", "").lower():
                continue
            checked += 1
            with self.subTest(page=str(page.relative_to(render.SITE))):
                desc = meta.get("description", "")
                self.assertGreaterEqual(len(desc), 70)
                self.assertLessEqual(len(desc), 160)
                self.assertEqual(meta.get("og:description"), desc)
                self.assertEqual(meta.get("twitter:description"), desc)
                text = visible(raw)
                for block in blocks(raw):
                    if "headline" in block and "mainEntityOfPage" in block:
                        self.assertEqual(block.get("description"), desc)
                    if block.get("@type") == "FAQPage":
                        for question in block["mainEntity"]:
                            self.assertIn(norm(question["acceptedAnswer"]["text"]), text)
        self.assertGreater(checked, 0)

    @unittest.skipUnless(brand.SITE_BRAND == "checkengine", "Check Engine visible prose")
    def test_visible_copy_uses_areas(self):
        for page in render.SITE.rglob("*.html"):
            with self.subTest(page=str(page.relative_to(render.SITE))):
                raw = page.read_text().split("<body", 1)[1]
                prose = re.sub(r"<(pre|code)\b[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
                prose = re.sub(r"(?:https?://|www\.|/)\S+", " ", visible(prose))
                self.assertNotRegex(prose, re.compile(r"\blanes?\b", re.I))

    def test_support_report_covers_both_platforms(self):
        for route in ("support", "faq"):
            with self.subTest(page=route):
                self.assertIn("include your macos or windows version", self.text(route))

    def test_download_yearly_discount_grammar(self):
        text = self.text("download")
        self.assertIn("quote a monthly price and offer a discount", text)
        self.assertNotIn("quote a monthly price and offers", text)

    def test_former_address_explained_once(self):
        phrase = "this site's address until november 2026"
        routes = ("contact", "how-to/fix-missing-security-headers",
                  "how-to/outrank-a-bigger-competitor", "how-to/redirect-http-to-https",
                  "how-to/sitemap-urls-that-are-not-stale", "", "learn/ai-substitution",
                  "learn/dead-contact-address", "learn/internal-link-equity",
                  "vs/se-ranking-vs-screaming-frog", "ai-assistants")
        for route in routes:
            with self.subTest(page=route, brand=brand.SITE_BRAND):
                text = visible(self.raw(route).split('<main id="main">', 1)[1])
                self.assertEqual(text.count(phrase),
                                 1 if brand.SITE_BRAND == "checkengine" else 0)
                if brand.SITE_BRAND == "checkengine" and route != "ai-assistants":
                    # Ignore mail addresses and retained download URLs. The note
                    # belongs in the first paragraph or caption naming the host.
                    paragraphs = re.findall(r"<(p|figcaption|li)\b[^>]*>(.*?)</\1>",
                                            self.raw(route), flags=re.S | re.I)
                    first = next(visible(body) for _, body in paragraphs
                                 if re.search(r"(?<![\w@/])docketseo\.app\b", visible(body)))
                    self.assertIn(phrase, first)

    def test_shared_platform_sentence(self):
        matched = 0
        for page in (render.SITE / "vs").rglob("index.html"):
            text = visible(page.read_text())
            self.assertNotIn("one-time purchase for macos:", text)
            if "one-time purchase for mac and windows:" in text:
                matched += 1
        self.assertEqual(matched, 13)
        self.assertIn("mac and windows", self.text("vs/semrush-site-audit-alternative"))

    def test_company_site_captions(self):
        self.assertIn("The free audit of our own company site, in the app. <strong>", self.raw(""))
        self.assertIn("on our own company site, kerrandcompanyholdings.com",
                      self.text("best/screaming-frog-alternatives"))

    def test_comparison_stays_within_recorded_evidence(self):
        text = self.text("vs/se-ranking-vs-screaming-frog")
        self.assertIn("se ranking is a cloud platform used in a browser", text)
        self.assertIn("screaming frog runs on windows, macos and ubuntu", text)
        for phrase in ("all three run", "every vendor figure", "ten projects", "manager seat",
                       "two thousand keywords", "25 prompts", "five ai engines", "thirty projects",
                       "permanently", "without telling anyone", "their hardware", "xpath",
                       "across a whole crawl", "both were read"):
            self.assertNotIn(phrase, text)
        for phrase in ("250k pages per month in audit", "25k api credits & mcp access",
                       "2m pages per month in audit", '"javascript rendering"'):
            self.assertIn(phrase, text)

    def test_free_tools_limits_and_faq(self):
        route = "best/free-seo-audit-tools"
        text = self.text(route)
        self.assertIn('"2000 qpd" and "600 qpm" per site', text)
        self.assertIn("cap how fast a large site can be inspected", text)
        for phrase in ("nothing free is better", "only source of real google data",
                       "cannot be inspected page by page", "whether you need to pay depends"):
            self.assertNotIn(phrase, text)
        answer = self.faq(route, "Can I audit my website free without signing up?")
        self.assertNotIn("None of them", answer)
        self.assertNotIn("on your computer", answer)
        self.assertIn("Lighthouse runs inside Chrome", answer)
        self.assertIn("up to 500 URLs", answer)

    def test_audit_findings_and_faq_match_the_body(self):
        text = self.text("learn/seo-audit")
        self.assertNotIn("every one of these is invisible", text)
        self.assertIn("the three that most audits skip", text)
        audits = json.loads((render.DATA / "field-audits.json").read_text())["audits"]
        areas = {key for a in audits for key in a["by_area"]}
        every = sum(all(a["by_area"].get(key, 0) > 0 for a in audits) for key in areas)
        self.assertIn(f"in {every} of the {len(areas)} areas, all {len(audits)} sites had at least one finding", text)
        answer = self.faq("learn/seo-audit", "What does an SEO audit include?")
        self.assertNotIn("outbound links", answer)
        self.assertNotIn("security", answer)

    def test_canonical_hint_and_single_crawler_paragraph(self):
        text = self.text("how-to/fix-paginated-pages-that-canonicalise-to-page-1")
        self.assertIn("a canonical is a hint", text)
        self.assertIn("may stop fetching them", text)
        self.assertNotIn("items behind them go with them", text)
        text = self.text("tools/robots-txt-tester")
        self.assertEqual(text.count("a separate check requests your homepage"), 1)
        self.assertEqual(text.count("checks robots.txt rules for"), 1)

    def test_terms_offer_and_delivery_follow_shared_constants(self):
        for opened in (True, False):
            with self.subTest(opened=opened), patch.object(pages, "FOUNDING_OPEN", opened), \
                    patch.object(render, "FOUNDING_OPEN", opened), \
                    patch.object(pages, "WIN_SETUP_SIZE", "test installer size"), \
                    patch.object(pages, "render", side_effect=lambda **kwargs: kwargs):
                body = pages.terms()["body"]
                price = body.split("<h2>What it costs</h2>", 1)[1].split("<h2>", 1)[0]
                if opened:
                    self.assertIn(render.founding_price_sentence(), price)
                else:
                    self.assertNotIn("Launch price", price)
                    self.assertIn(f"Docket costs {render.PRICE_STR} in US dollars, paid once.", price)
                if render.WINDOWS:
                    self.assertIn("a Windows installer of test installer size", body)
        end = dt.datetime.fromisoformat(render.FOUNDING_ENDS_AT.replace("Z", "+00:00"))
        self.assertFalse(render.founding_open(end))
        self.assertIn("not worth the price to you", self.text("legal/refunds"))

    def test_privacy_names_and_superlative(self):
        text = self.text("legal/privacy")
        self.assertIn("price-reminder list", text)
        self.assertIn("news list", text)
        self.assertNotIn("docket-price-reminder", text)
        self.assertNotIn("docket-news", text)
        self.assertIn("it keeps the address, the list name, the site name and the date", text)
        self.assertNotIn("price-to-power ratio is unmatched", self.text("vs/screaming-frog-alternative"))

    def test_shipped_comments_name_no_sister_site(self):
        # RULES 52 (CEO, 2026-11-09): CSS, JS and HTML comments ship in every page and must not name another of our sites.
        sisters = re.compile(r"outlier\.host|builtbykerr\.com|crispvideo\.app|adplaybook\.app|matthewkerr\.dev|bookbreaker", re.I)
        comment = re.compile(r"/\*.*?\*/|<!--.*?-->", re.S)
        for path in sorted(render.SITE.rglob("*.html")):
            with self.subTest(page=str(path.relative_to(render.SITE))):
                for found in comment.findall(path.read_text(errors="ignore")):
                    self.assertIsNone(sisters.search(found), found[:160])

    def test_terms_name_the_publisher_and_dodo_as_merchant_of_record(self):
        # CEO 2026-11-09 (answers from Matthew): Dodo Payments is the merchant of record for every sale and calculates the tax;
        # Kerr & Company LLC publishes and licenses the software; refunds are asked of us and issued through Dodo.
        terms = self.text("legal/terms")
        self.assertIn("Licences are sold through Dodo Payments, the reseller and merchant of record for each sale".lower(), terms)
        self.assertIn("Dodo Payments, as merchant of record, calculates any sales tax or VAT due and shows it at checkout".lower(), terms)
        self.assertIn("the total liability of Kerr & Company LLC, as licensor of the software".lower(), terms)
        self.assertNotIn("published and sold by".lower(), terms)
        self.assertNotIn("this paragraph will say which it is".lower(), terms)
        refunds = self.text("legal/refunds")
        self.assertIn("Licences are sold through Dodo Payments".lower(), refunds)
        self.assertIn("we issue it through Dodo Payments".lower(), refunds)
        self.assertIn("support at Dodo Payments can also help".lower(), refunds)
        self.assertNotIn("Docket is sold by".lower(), refunds)
        self.assertNotIn("Check Engine is sold by".lower(), refunds)
        self.assertIn("published by his company, Kerr & Company LLC".lower(), self.text("about"))

    def test_privacy_says_the_advertising_pixel_was_removed_on_6_november(self):
        # Quality Desk / CEO 7 Nov item: a dated line, like Crisp's and Outlier's. Matches verify_pixel: no "Meta pixel" wording.
        text = self.text("legal/privacy")
        self.assertIn("no advertising pixel. until 6 november 2026 every page here also loaded meta", text)
        self.assertIn("a cookie named _fbp", text)
        self.assertIn("all of it has been removed", text)

    def test_changed_pages_metadata_and_full_faq_answers(self):
        for route in CONTENT_UPDATED:
            with self.subTest(page=str(route), brand=brand.SITE_BRAND):
                raw = (render.SITE / route).read_text()
                title = re.search(r"<title>(.*?)</title>", raw, re.S)[1]
                desc = re.search(r'<meta name="description" content="(.*?)"', raw, re.S)[1]
                self.assertLessEqual(len(html.unescape(title)), 60)
                self.assertLessEqual(len(html.unescape(desc)), 160)
                text = visible(raw)
                for block in blocks(raw):
                    if block.get("@type") == "FAQPage":
                        for question in block["mainEntity"]:
                            self.assertIn(norm(question["acceptedAnswer"]["text"]), text)


if __name__ == "__main__":
    unittest.main()
