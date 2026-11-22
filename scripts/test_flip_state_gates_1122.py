"""The two deploy gates that would have stopped the 3 December price-flip deploy on a coincidence or a stale count.

Found by the read-only price-flip review (22 Nov 2026). (1) verify_founding_offer refused any built page whose text had "$19.99" or
"Black Friday price": a rival's own plan (Squirrly PRO "$19.99 a month") and a rival's "Black Friday price shown on 20 November" are
vendor facts, not our sale, but they would have blocked the deploy before the push. (2) The privacy page said "four third-party
scripts" after the sale bar's script stopped being built, and verify_privacy_scripts failed AFTER the push. Neither needs a build here:
the first is the gate's own function on sample text, the second is the page transform on a stand-in paragraph; the frozen-clock build
in test_black_friday_sale_copy.py checks the real page in both states.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "articles"))

import verify_founding_offer as gate
import pages
from verify_pixel import _WORD_TO_INT

CODE = "FOUNDINGDOCKET"
PRICE = "$19.99"


def shows(text):
    return gate.shows_founding("page.html", f"<p>{text}</p>", PRICE, CODE)


def test_a_rivals_price_or_black_friday_price_is_not_our_sale():
    assert shows("Squirrly SEO PRO $19.99 a month, purchased annually. Year comparison: $239.88.") == ""
    assert shows("Slim SEO Personal $59.00 a year for one site. Black Friday price shown on 20 November 2026.") == ""


def test_our_own_sale_text_is_still_caught():
    for text in ("Black Friday sale: $19.99 once through December 2. Then $39.",
                 "Check Engine is $19.99 once through December 2, then $39.",
                 "Use FOUNDINGDOCKET at checkout.", "the founding price", "the launch price"):
        assert shows(text), text


def test_the_closed_state_privacy_page_stops_describing_the_sale_bar():
    sale_bar = "<p>The third is the sale bar across the top of every page, loaded from a server.</p>\n"
    body = ("<p>This site is static and runs four third-party scripts. The first is X.</p>\n" + sale_bar
            + "<p>The fourth is on every page: a small script.</p>\n")
    after = pages._privacy_after_the_sale(body)
    assert "sale bar" not in after and "runs three third-party scripts" in after
    assert "The third is on every page" in after and "fourth" not in after
    assert _WORD_TO_INT["three"] == 3


def test_the_transform_refuses_when_the_page_has_moved():
    try:
        pages._privacy_after_the_sale("<p>This site is static and runs four third-party scripts.</p>")
    except AssertionError:
        return
    raise AssertionError("the transform must fail loudly when the sale bar paragraph is gone")


if __name__ == "__main__":
    test_a_rivals_price_or_black_friday_price_is_not_our_sale()
    test_our_own_sale_text_is_still_caught()
    test_the_closed_state_privacy_page_stops_describing_the_sale_bar()
    test_the_transform_refuses_when_the_page_has_moved()
    print("FLIP STATE GATES 1122 ok: a rival's price is not our sale, our sale is still caught, the closed privacy page matches its scripts")
