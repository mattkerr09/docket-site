#!/usr/bin/env python3
"""Offline help-page regression checks. Builds stay in temporary repo copies."""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch
from urllib.parse import urlsplit

from test_rename_brand import Page, build

ROOT = Path(__file__).resolve().parent.parent
ROUTES = ("help", "support", "faq")
FORBIDDEN = re.compile(r"Black Friday|half price|%\s*off", re.I)


def words(raw):
    text = " ".join(html.unescape(" ".join(Page(raw).words)).split())
    return re.sub(r"\s+([.,:;!?])", r"\1", text)


def check_built(root):
    # Run inside the scratch repo so constants and the branding pass match the build.
    import brand
    import render as R
    from articles import help_pages

    site = root / "site"
    records = help_pages.answers()
    values = help_pages.answer_values()
    assert len({item["id"] for item in records}) == len(records)
    assert len({item["question"] for item in records}) == len(records)
    questions = []
    expected_answers = []
    constant_numbers = set(re.findall(r"\d+(?:\.\d+)*", " ".join(map(str, values.values()))))
    for item in records:
        # Literal numbers and prices belong in constants, never in help copy.
        for field in ("answer", "help_answer"):
            if field not in item:
                continue
            answer = item[field].format_map(values)
            assert not re.search(r"\d|\$", item[field]), item["id"]
            assert set(re.findall(r"\d+(?:\.\d+)*", answer)) <= constant_numbers, item["id"]
            assert not FORBIDDEN.search(answer.replace(R.founding_price_sentence(), "")), item["id"]
            assert not any(dash in answer for dash in ("\u2014", "\u2013")), item["id"]
            assert 2 <= len(re.split(r"(?<=[.!?])\s+(?=[A-Z])", answer)) <= 4, item["id"]
        source = item["source"]
        path = urlsplit(source["source_path"])
        assert not path.netloc and path.path.startswith("/") and path.path.endswith("/")
        assert ".." not in Path(path.path).parts
        assert path.path not in {f"/{route}/" for route in ROUTES}
        source_file = site / path.path.lstrip("/") / "index.html"
        assert source_file.is_file(), source["source_path"]
        source_words = words(source_file.read_text())
        for claim in source["claim"]:
            supported = brand.text(claim.format_map(values))
            assert " ".join(supported.split()) in source_words, (item["id"], supported)
        question, marked_answer = help_pages.question_answer(item)
        questions.append(brand.text(html.unescape(question)))
        expected_answers.append(brand.text(marked_answer))

    sitemap = (site / "sitemap.xml").read_text()
    lastmod = json.loads((root / "data" / brand.LASTMOD_FILE).read_text())
    for route in ROUTES:
        raw = (site / route / "index.html").read_text()
        page = Page(raw)
        assert sum(tag == "h1" for tag, attrs in page.tags) == 1, route
        descriptions = [attrs["content"] for tag, attrs in page.tags
                        if tag == "meta" and attrs.get("name") == "description"]
        assert len(descriptions) == 1 and 0 < len(descriptions[0]) <= 165, route
        assert not FORBIDDEN.search(words(raw).replace(R.founding_price_sentence(), "")), route
        assert "\u2014" not in words(raw) and "\u2013" not in words(raw), route
        canonical = [attrs["href"] for tag, attrs in page.tags
                     if tag == "link" and attrs.get("rel") == "canonical"]
        assert canonical == [f"{brand.BASE}/{route}/"], route
        assert f"<loc>{brand.BASE}/{route}/</loc>" in sitemap, route
        assert f"{route}/index.html" in lastmod, route
        for tag, attrs in page.tags:
            href = urlsplit(attrs.get("href", ""))
            if href.path.startswith("/") and not href.netloc:
                target = site / href.path.lstrip("/")
                if href.path.endswith("/"):
                    target /= "index.html"
                assert target.is_file(), (route, href.path)
        footer = re.search(r"<footer\b.*?</footer>", raw, re.S)[0]
        nav = re.search(r"<nav\b.*?</nav>", raw, re.S)[0]
        for linked in ROUTES:
            assert f'href="/{linked}/"' in footer
            assert f'href="/{linked}/"' not in nav

    faq_raw = (site / "faq/index.html").read_text()
    faq_page = Page(faq_raw)
    schema = next(block for block in faq_page.json_ld if block.get("@type") == "FAQPage")
    assert [entry["name"] for entry in schema["mainEntity"]] == questions
    assert [html.unescape(entry["acceptedAnswer"]["text"]) for entry in schema["mainEntity"]] == [
        html.unescape(answer) for answer in expected_answers]
    for question, answer in zip(questions, expected_answers):
        assert question in words(faq_raw)
        assert words(answer) in words(faq_raw)
    for item in records:
        assert f'href="{item["source"]["source_path"]}"' in faq_raw
    help_raw = (site / "help/index.html").read_text()
    help_schema = next(block for block in Page(help_raw).json_ld if block.get("@type") == "FAQPage")
    assert len(help_schema["mainEntity"]) == 3
    quick = {item["id"]: item for item in records}
    for item, key in zip(help_schema["mainEntity"], ("try", "price", "activate")):
        question, answer = help_pages.question_answer(quick[key], brief=True)
        assert item["name"] == brand.text(html.unescape(question))
        assert html.unescape(item["acceptedAnswer"]["text"]) == html.unescape(brand.text(answer))
        assert words(brand.text(answer)) in words(help_raw)
    assert 'href="mailto:support@docketseo.app"' in (site / "support/index.html").read_text()

    bundle = json.loads((root / "data/bundle.json").read_text())
    pricing = (site / "pricing/index.html").read_text()
    apart = sum(bundle["list_prices"].values())
    assert set(bundle["apps"]) == set(bundle["list_prices"])
    assert bundle["list_prices"]["Docket SEO"] == R.PRICE
    expected = f'{R._usd(apart)} bought apart, {R._usd(bundle["standard_price"])} together.'
    assert expected in words(pricing)
    if R.FOUNDING_OPEN:
        launch_apart = (apart * 100 - sum(bundle["sale_off_cents"].values())) / 100
        expected = (f'{R._usd(launch_apart)} bought apart, '
                    f'{R._usd(bundle["founding_price"])} together.')
        assert expected in words(pricing)
        assert f'data-founding-until="{bundle["founding_ends_at"]}"' in pricing
    assert pricing.index('id="bundle-sum"') < pricing.index('<h2>')

    # A later rebuild must drop launch text in both the help answers and pricing.
    with patch.object(R, "FOUNDING_OPEN", False):
        closed_answer = help_pages.question_answer(quick["price"])[1]
        assert R.FOUNDING_NOW not in closed_answer
        assert R.price_sentence() in closed_answer
    import datetime
    import importlib
    builder = importlib.import_module("build")

    class AfterLaunch(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            end = cls.fromisoformat(bundle["founding_ends_at"].replace("Z", "+00:00"))
            return end + datetime.timedelta(days=1)

    with patch.object(builder.datetime, "datetime", AfterLaunch), patch.object(
            builder, "render", side_effect=lambda **kwargs: kwargs):
        closed_pricing = builder.pricing_page()["body"]
    closed_sum = re.search(r'<p class="hero-note" id="bundle-sum">(.*?)</p>', closed_pricing)[1]
    assert closed_sum == f'{R._usd(apart)} bought apart, {R._usd(bundle["standard_price"])} together.'
    # The Microsoft Store listing keeps the name Docket SEO: wherever the site says the app is in the Store,
    # the Check Engine build must say what the listing is called, and the Docket build must stay as it was.
    store_pages = []
    for page in sorted(site.rglob("index.html")):
        text = words(page.read_text(encoding="utf-8"))
        if "in the Microsoft Store" not in text:
            continue
        store_pages.append(page.relative_to(site).parent.as_posix())
        if brand.SITE_BRAND == "checkengine":
            assert "in the Microsoft Store, listed there as Docket SEO" in text, page
        else:
            assert "listed there as" not in text, page
    assert store_pages, "no page says the app is in the Microsoft Store; the Store wording test checks nothing"
    print(f"HELP OK {brand.SITE_BRAND}: sources, copy, schema, links and bundle sums")


def main():
    if "--check-built" in sys.argv:
        check_built(ROOT)
        return
    with tempfile.TemporaryDirectory(prefix="test-help-pages-") as temporary:
        for mode in ("docket", "checkengine"):
            destination = Path(temporary) / mode
            for directory in ("scripts", "data", "site", "workers"):
                shutil.copytree(ROOT / directory, destination / directory,
                                ignore=shutil.ignore_patterns("__pycache__", "*.env"))
            build(destination, mode)
            env = dict(os.environ, SITE_BRAND=mode, PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run([sys.executable, "scripts/test_help_pages.py", "--check-built"],
                                    cwd=destination, env=env, capture_output=True, text=True)
            assert result.returncode == 0, result.stdout + result.stderr
            print(result.stdout.strip())
    print("HELP OK both offline builds used DOCKET_SKIP_BRAND_ASSETS=1")


if __name__ == "__main__":
    main()
