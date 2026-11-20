# Check Engine price after the Black Friday sale

The CEO's 13 November 2026 Dodo read-back confirms PRICE is 39.
LATER_PRICE stays 39 and LATER_STR stays derived from it. FOUNDING_CODE takes
a flat FOUNDING_OFF_CENTS of 1901 off this product. FOUNDING_NOW is derived
from cents as $19.99. NOVEMBER_OFF_CENTS is 950, so NOVEMBER_PRICE_STR is
derived as $29.50 and SALE_PERCENT_OFF is computed as 32. Buy applies the sale.
CHECKOUT_HELP says there is no code to type. Both prices are below
BNPL_MIN_CENTS, so PAY4, BNPL_NOTE and the other pay-in-four text are empty.
In offer.json, instalments and founding.instalment_cents are null.
checkout_price_cents and later_price_cents stay 3900.

1. At 08:00Z on 3 December, FOUNDING_OPEN is false by the clock. Keep
   FOUNDING_ENDS_AT at 2026-12-03T07:59:59Z and rebuild with
   TZ=UTC python3 scripts/build.py. The sale lines, CHECKOUT_HELP and sale
   Offer drop out. JSON-LD keeps one paid Offer at 39.00 with no
   priceValidUntil. write_offer sets founding and after_launch to null.
   later_* can then go. Check heroes, buttons, FAQs and llms.txt. Run
   test_december_price.py, test_black_friday_sale_copy.py and the price gates,
   then lint.py site.
2. APP_LIST_PRICE_CENTS stays 5900 until the 15 December read. Installed
   builds trust the live offer only when price_cents matches their expected
   list price. Move APP_LIST_PRICE_CENTS to PRICE * 100 only after the host
   confirms the release that expects 3900 has reached users.
3. Re-record the Windows still once after that app release reaches users.

The installed app still reads founding.code and may print FOUNDINGDOCKET.
The field and all existing keys stay for app compatibility. The site's
visible copy does not print that code or the word FOUNDING.

Matthew's 19 November order sets the other December prices. From
2026-12-03T08:00Z, Crisp is $29, Outlier is $39 and all three apps are $79.
Check Engine stays $39. The CEO changes Dodo product prices at that time.
This site states the order and does not change Dodo.

Until 2026-12-03T07:59:59Z, the sale stays Crisp $9.99, Outlier $16.99,
Check Engine $19.99 and all three $34.99. data/bundle.json stores sale_prices
apart from list_prices so changing December prices cannot change the sale.
The bought-apart total is computed from the prices in effect: $46.97 during
the sale and $107 after it. separate_total is checked against list_prices.
