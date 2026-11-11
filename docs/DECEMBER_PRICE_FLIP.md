# Check Engine price after the 11 November 2026 change

Done on 11 November, from the CEO's Dodo read-back at 15:48Z. PRICE is 39.
LATER_PRICE stays 39 and LATER_STR stays derived from it. FOUNDING_CODE takes
a flat FOUNDING_OFF_CENTS of 950 off this product. FOUNDING_NOW is derived
from that code. Buy applies it for the buyer. CHECKOUT_HELP uses PRICE_STR
for the full checkout price. Both prices are below BNPL_MIN_CENTS, so PAY4,
BNPL_NOTE and the other pay-in-four text are empty. In offer.json, instalments
and founding.instalment_cents are null. checkout_price_cents is 3900.

1. At 08:00Z on 1 December, FOUNDING_OPEN is false by the clock. Keep
   FOUNDING_ENDS_AT at 2026-12-01T07:59:59Z and rebuild with
   TZ=UTC python3 scripts/build.py. The launch lines, CHECKOUT_HELP and launch
   Offer drop out. JSON-LD keeps one paid Offer at 39.00. write_offer sets
   founding to null. after_launch and later_* can then go. Check heroes,
   buttons, FAQs and llms.txt. Run test_december_price.py and the price gates,
   then lint.py site.
2. APP_LIST_PRICE_CENTS stays 5900 for installed builds 1.3.139 through
   1.3.161. They trust the live offer only when price_cents matches their own
   expected list price. Move APP_LIST_PRICE_CENTS to PRICE * 100 only after
   the host says release 1.3.162, which expects 3900, has reached users.
   Then price_cents and the app agree again at 3900.
3. Re-record the Windows still once after that app release reaches users.
