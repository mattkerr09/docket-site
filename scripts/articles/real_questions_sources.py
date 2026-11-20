"""Frozen source readings for the 20 November articles.

The competitive-claims history keeps a literal copy in comparisons.VERIFIED.
Older measured-answer tests temporarily restore that generator from history.
Seed only missing entries so the new articles stay identical in those builds.
The real-question test requires the two copies to match.
"""
from comparisons import CHECKED_HUMAN, CHECKED_ISO, VERIFIED

READINGS = {'rq-conductor': [("contentkingapp.com now redirects to Conductor's Monitoring page",
                   'https://www.contentkingapp.com'),
                  ('Conductor Monitoring offers continuous monitoring and 60 months of history',
                   'https://www.conductor.com/platform/monitoring/'),
                  ('Conductor publishes no dollar prices on its pricing page',
                   'https://www.conductor.com/pricing/')],
 'rq-seranking': [('SE Ranking Core is $129.00 a month on monthly billing or $103.20 a month on '
                   'annual billing; Growth is $279.00 or $223.20 respectively',
                   'https://seranking.com/subscription.html'),
                  ('SE Ranking Website Audit states up to 2,000,000 pages per project and '
                   'JavaScript rendering',
                   'https://seranking.com/website-audit.html'),
                  ('Core includes 250,000 audit pages per month and Growth includes 2,000,000',
                   'https://seranking.com/subscription.html')],
 'rq-screaming-frog': [('Screaming Frog SEO Spider is desktop software; the free version allows '
                        '500 URLs per crawl',
                        'https://www.screamingfrog.co.uk/seo-spider/'),
                       ('A licence costs $279 a year in the USD view or £199 a year in the GBP '
                        'view; licences last one year',
                        'https://www.screamingfrog.co.uk/seo-spider/pricing/')],
 'rq-semrush': [('Semrush SEO includes Site Audit, 5 websites to monitor and 500 keywords to track '
                 'daily; $139.00 a month on monthly billing or $117.33 a month billed annually',
                 'https://www.semrush.com/prices/'),
                ('The free account states 1 demo project and 10 reports per day; the pages read do '
                 'not state a per-audit page limit',
                 'https://www.semrush.com/prices/'),
                ('Semrush Site Audit ranks issues by severity',
                 'https://www.semrush.com/features/site-audit/')],
 'rq-sitebulb': [('Sitebulb offers desktop software for Windows or Mac and a cloud product',
                  'https://sitebulb.com/'),
                 ('Desktop Lite is $18.00 a month for 10,000 URLs per audit; Pro is $42.00 a month '
                  'for 500,000 URLs per audit; Cloud starts at $125.00 a month',
                  'https://sitebulb.com/pricing/')],
 'rq-jetoctopus': [('JetOctopus is a cloud crawler with log analysis', 'https://jetoctopus.com/'),
                   ('Growth includes 500,000 crawled URLs and 2,000,000 log lines per month; Pro '
                    'includes 2,000,000 and 8,000,000; Ultra includes 5,000,000 and 25,000,000; '
                    "see JetOctopus's pricing page for prices",
                    'https://jetoctopus.com/pricing')],
 'rq-google-live': [("URL Inspection's live test fetches the URL in real time and confirms whether "
                     'Google-InspectionTool can access it for indexing; a screenshot is available '
                     'only in a live test',
                     'https://support.google.com/webmasters/answer/9012289')],
 'rq-google-ranges': [('Google documents reverse DNS followed by forward DNS, or matching the '
                       'visiting IP against its published CIDR ranges',
                       'https://developers.google.com/crawling/docs/crawlers-fetchers/verify-google-requests'),
                      ('We counted 317 common crawler prefixes: 170 IPv4 and 147 IPv6',
                       'https://developers.google.com/static/crawling/ipranges/common-crawlers.json'),
                      ('We counted 272 special crawler prefixes: 136 IPv4 and 136 IPv6',
                       'https://developers.google.com/static/crawling/ipranges/special-crawlers.json'),
                      ('We counted 1,088 user-triggered fetcher prefixes: 544 IPv4 and 544 IPv6',
                       'https://developers.google.com/static/crawling/ipranges/user-triggered-fetchers.json'),
                      ('We counted 504 Google-controlled user-triggered fetcher prefixes: 252 IPv4 '
                       'and 252 IPv6',
                       'https://developers.google.com/static/crawling/ipranges/user-triggered-fetchers-google.json'),
                      ('We counted 20 user-triggered agent prefixes: 12 IPv4 and 8 IPv6; each of '
                       'the five lists was created on 19 November 2026',
                       'https://developers.google.com/static/crawling/ipranges/user-triggered-agents.json')],
 'rq-noindex': [('Google describes 2 ways to set noindex: a meta tag or an HTTP response header; '
                 'the page must be accessible and not blocked by robots.txt for the rule to be '
                 'read',
                 'https://developers.google.com/search/docs/crawling-indexing/block-indexing'),
                ('Google does not support noindex rules in robots.txt; meta robots and meta '
                 'googlebot are shown as examples, as is the X-Robots-Tag header',
                 'https://developers.google.com/search/docs/crawling-indexing/block-indexing')]}

for key, claims in READINGS.items():
    VERIFIED.setdefault(key, claims)
    CHECKED_HUMAN.setdefault(key, "20 November 2026")
    CHECKED_ISO.setdefault(key, "2026-11-20")
