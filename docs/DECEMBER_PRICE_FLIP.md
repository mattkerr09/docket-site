# Check Engine price on 1 December 2026

The CEO switches Dodo after 08:00Z on 1 December. Wait for confirmation that
Dodo charges $39 without a code. The November source keeps `PRICE = 59`,
`LATER_PRICE = 39` and `FOUNDING_NOW = "$29.50"`. Do not change Dodo as part
of this site job.

1. Set `render.PRICE = LATER_PRICE`. Keep `LATER_PRICE = 39` and its derived
   `LATER_STR`. `PRICE_STR` and `PRICE_TODAY` then become $39 and 39.
   Leave `PRICE_PREVIOUS = None` so the checkout gate checks the new price.
2. Keep the expired `FOUNDING_ENDS_AT = "2026-12-01T07:59:59Z"`. Do not extend
   it or reuse `FOUNDING_CODE = "FOUNDINGDOCKET"`. `FOUNDING_OPEN` becomes
   false by the clock. `FOUNDING_LINE` and `founding_price_sentence()` become
   empty, `FOUNDING_MOUNT` disappears, and no buy link should apply the code.
   `FOUNDING_PCT` stays 50 as old offer data. The derived `FOUNDING_WAS` becomes
   $39 and `FOUNDING_NOW` becomes $19.50, but neither is a live offer or should
   appear on the rebuilt site. Check the hub no longer applies the expired
   code. The host handles the hub separately if needed.
3. Keep `BNPL_MIN_CENTS = 5001`. `BNPL_LIVE` can remain true as provider data.
   At $39, `PAY4`, `PAY4_BUY`, `PAY4_FOUNDING`, `BNPL_NOTE` and `BNPL_NOTE_HTML`
   must all be empty. `BNPL_FOUNDING_OK` and `SALE_UNDER_FLOOR` are false.
   `BNPL_INSTALMENT` derives $9.75 and `BNPL_FOUNDING_INSTALMENT` derives $4.88,
   but neither may be shown. Both instalment fields in `offer.json` must be
   absent from active offers or null. `founding` and `after_launch` become null.
4. Rebuild with `TZ=UTC python3 scripts/build.py`. Check hero prices, buy
   buttons, FAQ answers, llms.txt, offer.json and JSON-LD offers now use $39.
   Comparison costs and savings recalculate from `PRICE`. Keep competitor
   prices, past release records and the bundle's separate prices as recorded.
5. Update `scripts/test_december_price.py` for the completed flip: its November
   assertions intentionally pin `PRICE == 59` and `FOUNDING_NOW == "$29.50"`.
   Run that gate, `python3 scripts/test_sitewide_copy.py`,
   `python3 scripts/test_live_site_fixes.py`, `python3 scripts/verify_price_claims.py`,
   `python3 scripts/verify_founding_offer.py --self-test`,
   `python3 scripts/verify_founding_offer.py --offline`, and
   `python3 scripts/verify_structured_data_matches_page.py` on the rebuild.
   The host then runs the live checkout and founding-offer gates and the full
   release gates, reviews the result, and deploys through the usual process.

This note authorizes no deploy from the November job.
