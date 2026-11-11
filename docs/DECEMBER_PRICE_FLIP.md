# Check Engine price on 1 December 2026

The host first confirms that Dodo charges $39 without FOUNDINGDOCKET. November
keeps PRICE at 59 for the live checkout check. LATER_PRICE stays 39 and LATER_STR
is derived from it. FOUNDING_NOW stays $29.50 until the flip.

1. Set render.PRICE to LATER_PRICE after Dodo changes. Keep PRICE_PREVIOUS as
   None. PRICE_STR and PRICE_TODAY then describe the $39 checkout. Comparison
   figures already use LATER_PRICE and keep the same values.
2. Keep the expired FOUNDING_ENDS_AT. FOUNDING_OPEN must be false. Remove the
   CHECKOUT_HELP sentence about entering FOUNDING_CODE when checkout shows $59.
   FOUNDING_LINE, founding_price_sentence and FOUNDING_MOUNT must produce no
   launch offer. FOUNDING_NOW remains a derived old-offer value with no display.
   The host checks that the hub has stopped applying the expired code.
3. Keep BNPL_MIN_CENTS at 5001 and the BNPL_* provider constants. At $39, PAY4,
   PAY4_BUY, PAY4_FOUNDING, BNPL_NOTE and BNPL_NOTE_HTML must produce no text.
   In offer.json, price_cents becomes 3900. founding, after_launch and instalments
   become null. Keep schema, currency, refund_days, checkout_url, buy_url and
   sample_report_url with their existing meanings. Keep the added
   later_price_cents at 3900 and later_from at 2026-12-01.
4. Rebuild with TZ=UTC python3 scripts/build.py. Check heroes, comparisons,
   buttons, FAQs, llms.txt and the assistant factbase. JSON-LD must have the
   current $39 Offer, with the expired launch Offer removed. Keep the historical
   corrections and the bundle's separate prices as recorded.
5. Update test_launch_price_copy.py and test_december_price.py for the completed
   flip. Their November checks pin PRICE to 59 and the two dated Offers. Run
   those tests, lint.py site, verify_numbers.py, verify_derived_data.py,
   verify_price_claims.py, verify_founding_offer.py --offline and
   verify_structured_data_matches_page.py. The host runs the live checkout and
   founding-offer checks, reviews the change, and ships it.
