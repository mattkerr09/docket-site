"""One line on the Perplexity-User crawler page sends a "perplexity ai traffic" searcher to the page about visitors.

Search Console, 28 days to 21 Nov 2026: "perplexity ai traffic" (29 impressions at 21.9) and "perplexity ai website
traffic" (17 at 19.2) land on /ai-crawlers/perplexity-user/, but those people want the visitors Perplexity sends, which
/how-to/see-ai-assistant-traffic-in-analytics/ answers. This pins: the pointer exists for that crawler only, it is a plain
internal link (no nofollow, no absolute URL) to the how-to's real route, and it states that crawler fetches are not visits.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "articles"))

import ai_crawler_pages as pages
import howto_ai_assistant_traffic as traffic


def test_the_pointer_is_for_perplexity_user_only():
    assert set(pages.TRAFFIC_POINTERS) == {"Perplexity-User"}


def test_the_pointer_is_one_plain_internal_link_to_the_real_howto():
    html = pages.TRAFFIC_POINTERS["Perplexity-User"]
    hrefs = re.findall(r'href="([^"]*)"', html)
    assert hrefs == [f"/how-to/{traffic.SLUG}/"]
    assert "nofollow" not in html and "http" not in html
    assert html.count("<a ") == 1


def test_the_pointer_says_a_fetch_is_not_a_visit_and_names_the_traffic_it_means():
    text = re.sub(r"<[^>]+>", " ", pages.TRAFFIC_POINTERS["Perplexity-User"])
    assert "Perplexity-User fetches are not visits" in text
    assert "referral traffic from perplexity.ai" in text
    assert "Google Analytics" in text


if __name__ == "__main__":
    test_the_pointer_is_for_perplexity_user_only()
    test_the_pointer_is_one_plain_internal_link_to_the_real_howto()
    test_the_pointer_says_a_fetch_is_not_a_visit_and_names_the_traffic_it_means()
    print("PERPLEXITY TRAFFIC POINTER 1121 ok: Perplexity-User only, one plain internal link, fetch is not a visit")
