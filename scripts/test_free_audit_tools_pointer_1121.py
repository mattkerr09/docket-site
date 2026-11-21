"""One line on /best/free-seo-audit-tools/ sends a "search engine checker" searcher to the free SEO checker.

Search Console, 28 days to 21 Nov 2026: "search engine checker" (71 impressions at 41.1) lands on this list page, while Bing's top three
for it are all paste-a-URL tools. This pins: the pointer is one plain internal link to /tools/seo-checker/ (no nofollow, no absolute
URL), it adds no figure beyond the score out of 100 the page already states, and it sits in the page right after the lede block.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "articles"))

import best_free as page

SOURCE = (Path(__file__).resolve().parent / "articles" / "best_free.py").read_text(encoding="utf-8")


def test_the_pointer_is_one_plain_internal_link_to_the_checker():
    html = page.CHECKER_POINTER
    assert re.findall(r'href="([^"]*)"', html) == ["/tools/seo-checker/"]
    assert "nofollow" not in html and "http" not in html and html.count("<a ") == 1


def test_the_pointer_says_only_what_the_page_already_says():
    text = re.sub(r"<[^>]+>", " ", page.CHECKER_POINTER)
    assert "a score out of 100" in text and "no sign-up" in text
    assert not re.search(r"\d", text.replace("100", "").replace("one", ""))


def test_the_pointer_sits_right_after_the_lede_block_and_once():
    assert SOURCE.count("{CHECKER_POINTER}") == 1
    lede = SOURCE.index('<p id="measured-answer">')
    pointer = SOURCE.index("{CHECKER_POINTER}")
    first_method = SOURCE.index("{method(")
    assert lede < pointer < first_method
    between = SOURCE[lede:pointer]
    assert between.count("{checked(") == 1, "only the lede's own source note sits between the lede and the pointer"


if __name__ == "__main__":
    test_the_pointer_is_one_plain_internal_link_to_the_checker()
    test_the_pointer_says_only_what_the_page_already_says()
    test_the_pointer_sits_right_after_the_lede_block_and_once()
    print("FREE AUDIT TOOLS POINTER 1121 ok: one plain internal link, nothing new claimed, right after the lede block")
