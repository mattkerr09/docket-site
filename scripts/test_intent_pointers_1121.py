"""Three one-line pointers that send a searcher to the page that answers the question.

Search Console, 28 days to 21 Nov 2026 (Article Studio's read): "search engine monitoring" (13 impressions at 65) lands on /for/,
"search engine crawler test" (11 at 65.1) on /bot/, "can ai crawlers execute javascript" (5 at 57.2) on /checks/ai-rendering/.
Each pointer is one plain internal link (no nofollow, no absolute URL) to a page that exists, states no figure, and sits in the
built page after the lede and before the first heading.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "articles"))

import bot as bot_page
import check_pages
import pages

SITE = HERE.parent / "site"
CASES = [
    ("/for/", pages.MONITORING_POINTER, "/learn/site-monitoring/"),
    ("/bot/", bot_page.GOOGLEBOT_POINTER, "/how-to/test-a-page-as-googlebot/"),
    ("/checks/ai-rendering/", check_pages.INTENT_POINTERS["ai.rendering"], "/learn/javascript-rendering/"),
]


def test_each_pointer_is_one_plain_internal_link_to_a_real_page():
    for _, html, target in CASES:
        assert re.findall(r'href="([^"]*)"', html) == [target]
        assert "nofollow" not in html and "http" not in html and html.count("<a ") == 1
        assert (SITE / target.strip("/") / "index.html").exists(), target


def test_each_pointer_states_no_figure():
    for _, html, _ in CASES:
        assert not re.search(r"\d", re.sub(r"<[^>]+>", " ", html)), html


def test_only_the_check_page_for_ai_rendering_has_a_pointer():
    assert set(check_pages.INTENT_POINTERS) == {"ai.rendering"}


def test_the_built_page_has_the_pointer_once_between_the_lede_and_the_first_heading():
    # /for/ gets the shared buy callout between its lede and the first paragraph, so "after the lede" means before the first <h2>.
    for route, html, _ in CASES:
        built = (SITE / route.strip("/") / "index.html").read_text(encoding="utf-8")
        assert built.count(html) == 1, route
        lede_end = re.search(r'<p class="lede">.*?</p>', built, re.S).end()
        first_heading = built.index("<h2", lede_end)
        assert lede_end <= built.index(html) < first_heading, route


if __name__ == "__main__":
    test_each_pointer_is_one_plain_internal_link_to_a_real_page()
    test_each_pointer_states_no_figure()
    test_only_the_check_page_for_ai_rendering_has_a_pointer()
    test_the_built_page_has_the_pointer_once_between_the_lede_and_the_first_heading()
    print("INTENT POINTERS 1121 ok: three plain internal links, no figure, once between the lede and the first heading in the built pages")
