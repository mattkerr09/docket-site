"""The worked cases on /learn/what-docket-got-wrong/: fifteen guides, folded into one page.

Search health 2026-10-19 (~/ops/launch/SEARCH-HEALTH-2026-10-19.md, rule 1.4): eighteen /how-to/ pages explained
Docket's own false positives and had never been shown in Google. Fifteen of them had no impression in any window
the audits read (09-10..09-23, 09-30..10-17) and no query among the 124 in the 90-day export of 2026-09-16 that
names their subject; the other three (/how-to/pages-an-audit-could-not-reach/, /how-to/sitemap-urls-that-are-not-stale/
and /how-to/tell-a-rate-limit-from-a-block/) had one or two impressions in the 10-15 audit's window and stay as pages.

Each of the fifteen is now a short section here, written only from what its own page said, and its old address is a
zero-delay meta refresh stub that names this page as canonical (the way /learn/what-scout-checks/ has forwarded
since August; scripts/lint.py exempts that shape). The sections are not release records: they carry no release
number and no test list, because the guides never claimed either. The registered check ids are kept, since they are
what a reader would search the engine's output for.

No site is named (third-party gate). No digit appears in the prose; quantities are words, as they were on the pages.
"""
from __future__ import annotations

#: Each case: anchor, title, check ids, the case in one or two paragraphs, what to check on your own report, and
#: related pages that still exist. `old` is the retired address, kept so the stubs and the link rewrites use one list.
GROUPS = [
    ("A number that counted the wrong thing", [
        {
            "id": "case-count-badge",
            "old": "check-the-count-on-a-finding",
            "title": "A finding's count is not decoration",
            "checks": ["ai.entity", "cvr.unusable_phone"],
            "body": [
                "On a hospital's report, a finding's badge read sixteen profiles directly above the headline "
                "“Only two recognised profiles in sameAs”. The headline counted the profiles the site "
                "had. The badge counted the ones it did not: the rest of the tool's own list. That is more than "
                "a wording problem, because the count feeds the score. The deduction grows with the logarithm of "
                "the count, so the inflated badge lifted a low severity finding above the medium one for having "
                "no sameAs at all.",
                "The phone check had the same fault in another form. It counted links, not pages, so one bad "
                "number in a header and a footer became two pages, with “and one more” printed under a "
                "list that showed the only page there was. Both checks now count what their headlines count.",
            ],
            "try": "Read the badge against the headline and the count against the URLs listed, then ask what one "
                   "fix would cover. If one edit to one template clears every instance, the count is measuring "
                   "evidence, not work.",
            "see": [("/learn/priority-model/", "How findings are ordered")],
        },
        {
            "id": "case-double-count",
            "old": "findings-that-double-count",
            "title": "When two findings count the same pages twice",
            "checks": ["schema.incomplete"],
            "body": [
                "On a shoe retailer's crawl of about thirty pages, the report carried two findings with the same "
                "check, the same fix and titles that differed only by a count of pages with incomplete product "
                "markup. Most pages sat under both, so the total was larger than the crawl. The findings were "
                "keyed on the type and the list of missing fields, so one type split into as many findings as "
                "it had field combinations. It is now one finding per type, with the combinations in the detail.",
                "The explanation beside the count had two faults of its own. It asserted that a listing or variant "
                "picker repeats the type, and on a site where the blocks were references it sent readers hunting "
                "for something that was not there. And the sentence that does say the blocks are references was "
                "shown only when blocks outnumbered pages, so the ordinary shape of one reference per page never "
                "got it.",
            ],
            "try": "Add the counts. If the total is bigger than the pages crawled, two findings overlap: compare "
                   "their URL lists and their fixes before treating them as two jobs.",
            "see": [("#case-id-pointer", "An @id is a pointer, not a definition")],
        },
        {
            "id": "case-pixel-zero-pages",
            "old": "pixels-reported-on-zero-pages",
            "title": "A pixel on part of the site, and on no pages",
            "checks": ["mar.ad_pixels", "mar.stack"],
            "body": [
                "A financial institution's report listed six advertising pixels as installed on only part of the "
                "site, each with a page count of zero. A pixel on no pages is either absent or somewhere the "
                "check could not count, and here it was the second. The installed list merged the served HTML "
                "with the rendered page, so it saw tags that JavaScript adds. The per-page count read the served "
                "HTML alone, so the same tags scored zero, which is below every coverage threshold. The same "
                "seam kept a site that loads every tag through a container from ever reaching the warning "
                "about too many tools on one page.",
                "Counting from the rendered pages instead would have been worse, because only a sample is "
                "rendered and “we only looked at a few pages” would become “it is only on a few "
                "pages”. Coverage is now judged only for tags visible in the served HTML, and the finding "
                "names the tags it did not judge.",
            ],
            "try": "When a headline says part of the site and the number says zero pages, believe the number and "
                   "distrust the headline. View source to see whether the tag is in the HTML at all, and ask the "
                   "ad platform which pages fired its pixel.",
            "see": [("/learn/marketing-tag-audit/", "The tracking checks")],
        },
        {
            "id": "case-one-template",
            "old": "read-findings-that-blame-the-whole-site",
            "title": "When an audit blames the site for one template",
            "checks": [],
            "body": [
                "A tool reported that a site had no share cards. The pages people actually share already had "
                "complete card markup; the ones without were a listing, an archive and other pages made by a "
                "different template. The count was accurate and the verdict was not. Nearly everything an audit "
                "measures is set once, in a layout, a partial or a component, so findings cluster by template, "
                "and a count with no location both overstates the work and understates the danger. A majority "
                "is not a site.",
                "The check now tells every page from most of them. A tool should also give a proportion and name "
                "the URLs, so the grouping shows without an export.",
            ],
            "try": "Sort the affected URLs by path: the grouping usually falls out at once. Then look at one page "
                   "that was not flagged. If a page of the same kind is correct, the template was fixed once and "
                   "not everywhere.",
            "see": [("/learn/audit-tool-accuracy/", "How to tell whether an audit tool is lying to you")],
        },
    ]),
    ("A finding inferred from text, markup or a name", [
        {
            "id": "case-phrase-matching",
            "old": "findings-from-phrase-matching",
            "title": "Why an audit finds reviews you do not have",
            "checks": ["local.reviews", "local.applicable"],
            "body": [
                "A software foundation was told “Reviews are shown but not marked up”. The evidence was "
                "the word review used as an ordinary verb, and the site's own sentence saying it does not "
                "provide testimonials, counted as proof that it does. A wildlife charity's joke about "
                "five-star accommodation for bees was quoted back as displayed customer ratings. One mistake was "
                "ours alone: a street-address pattern matched “that way” in this project's own marketing "
                "copy, decided a Mac software company was a local business, and produced six findings, two of "
                "them false at high severity.",
                "The phrase list is short and specific now, and the address pattern needs a capitalised street "
                "name, which knowingly misses some real addresses. The two errors are not equal. A missed review "
                "section gives advice you can ignore. A false match sends you looking for a section you do not "
                "have.",
            ],
            "try": "Read the quoted evidence before the headline, and ask whether the page is about the thing or "
                   "doing it. A policy page about reviews matches every phrase list and is not the signal.",
            "see": [],
        },
        {
            "id": "case-furniture-content",
            "old": "telling-furniture-from-content",
            "title": "Telling your site's furniture from its content",
            "checks": ["content.thin"],
            "body": [
                "Almost every judgement about what a page says depends on telling its furniture (navigation, "
                "header, footer, share buttons) from its content. We got it wrong five times in five checks, the "
                "fifth in the fix for the fourth. Counting links measures the template: an author archive "
                "carries dozens of links and only a few are the author's articles. The share of words inside "
                "links is better, until a page carries bare anchor tags with no navigation element around them. "
                "Then nothing is stripped, a genuine stub looks like an index, and an empty page is excused as "
                "an archive.",
                "What separates a label from an entry is length: an anchor needs at least four words to count as "
                "an entry. So there are three tests, each failing somewhere: repetition across pages, position "
                "inside a navigation element, and length.",
            ],
            "try": "When a tool calls a listing page thin, ask what it counted. If it counted links, it counted "
                   "your template.",
            "see": [("/how-to/content-audit/", "How to run a content audit")],
        },
        {
            "id": "case-not-your-address",
            "old": "addresses-on-your-site-that-are-not-yours",
            "title": "Not every address on your site is yours",
            "checks": ["cvr.dead_contact"],
            "body": [
                "The check that tests whether published email addresses can receive mail has to decide which "
                "addresses are yours. A software forum's how-to contained example addresses at a documentation "
                "domain, which the platform turned into links, so the site was told to publish mail records for "
                "a domain it does not own. The finding was true and the instruction was impossible. The remedy "
                "is now offered only for a domain the reader can publish records for.",
                "A law firm's share-by-email button has an empty recipient on purpose, but a branch tested the "
                "verdict and not the reason, so “not a domain” became “cannot receive mail”. "
                "That case is skipped, not renamed, because it is not an address. The case that must still fire "
                "is a bare server address, which can never have mail records.",
            ],
            "try": "Look at the domain in the address. If it is not yours, no instruction about mail records "
                   "applies to you.",
            "see": [("/learn/dead-contact-address/", "What a dead contact address is")],
        },
        {
            "id": "case-which-host",
            "old": "findings-that-name-no-host",
            "title": "Which host is that finding about?",
            "checks": ["security.https"],
            "body": [
                "An audit said a streaming service's certificate was close to expiry. The crawl began at the www "
                "address and followed a redirect, and it was the destination host's certificate that was "
                "expiring. Checking the address that had been typed showed months left, so the sentence read as "
                "false. The finding now names the host.",
                "The same shape appeared in two more places. A bakery chain was told its plain-http address did "
                "not redirect to https, true of the www spelling and not of the bare domain, which are separate "
                "hosts with their own certificates and redirect rules. And on a large retail site the plain-http "
                "address returned an error, which the report called an insecure copy of every page. Reachable, "
                "answering and refusing are three situations, and only the first is the problem it described.",
            ],
            "try": "Find the host before you check the claim, and test both spellings over plain http by hand.",
            "see": [("/how-to/redirect-http-to-https/", "How to redirect http to https"),
                    ("/learn/www-vs-non-www/", "www or no www")],
        },
    ]),
    ("Structured data read as something it was not", [
        {
            "id": "case-id-pointer",
            "old": "schema-id-references",
            "title": "An @id is a pointer, not a definition",
            "checks": ["schema.incomplete"],
            "body": [
                "An audit reported several pages as having incomplete Organization markup, but the Organization "
                "was defined once, with its name, URL and logo, and the flagged blocks were "
                "references to it by @id. Two nodes with the same @id are one node, and a bare reference is "
                "complete as written; the most used SEO plugins emit it by default. Reproduced with a controlled "
                "graph, the check counted the reference as a second, worse copy of the thing it pointed at.",
                "The real defect looks the same from outside. A search engine reads one page at a time, so if "
                "every block of a type on a page is a bare reference and nothing there defines it, it resolves "
                "to nothing, and neither a validator nor a rich result test says so. The repair is to define the "
                "entity on every page that references it, or to remove the stub, not to add a name to each stub.",
            ],
            "try": "View source on a flagged page and search for the identifier. If it appears once as a "
                   "definition and once as a reference, your markup is fine and the finding is wrong.",
            "see": [("/how-to/fix-structured-data-errors/", "How to fix structured data errors")],
        },
        {
            "id": "case-someone-elses-markup",
            "old": "schema-that-describes-someone-else",
            "title": "The markup on your page may not be about you",
            "checks": ["local.schema", "local.applicable"],
            "body": [
                "An audit said a national food-delivery marketplace was missing its address, telephone, opening "
                "hours and price range, with two fields present but blank. The only structured data on the page "
                "was a list of restaurants, other people's takeaways, and the check had judged the first node it "
                "reached as if it belonged to the publisher. One property settles whose data it is: "
                "itemListElement, whose entries are the things a page lists, not the thing it is.",
                "The finding stayed and changed its subject, because thin listing markup is real and a chain "
                "publishing its own branches in a list still needs complete entries. It now describes the "
                "businesses the page lists. A second sentence, that the tool had found restaurant markup, was "
                "literally true and read as “we think you are a restaurant”.",
            ],
            "try": "Ask whose data is missing. If the finding names fields you would never publish about "
                   "yourself, the node is probably not yours: search the page source for itemListElement.",
            "see": [("#case-id-pointer", "An @id is a pointer, not a definition")],
        },
        {
            "id": "case-wrong-type",
            "old": "completeness-findings-assume-your-type",
            "title": "A completeness check assumes your type is right",
            "checks": ["schema.incomplete"],
            "body": [
                "A property portal's homepage declared a Product node that held the company's name, address on "
                "the web, logo and profile links. It had no image, so the check advised adding one. The advice "
                "was correct for the type and the type was wrong: logo is not a property of Product, and with no "
                "offer, price or review the block was never going to produce a product rich result. A "
                "completeness check works by lookup, so the type is an input it never judges. It now speaks up "
                "only when an Organization-only property is present and every product signal is absent.",
                "The same shape in miniature: a large public-sector site wrote headLine for headline. JSON-LD "
                "keys are case sensitive, so no headline was read at all. The check matches on case and never "
                "on spelling, because a confident wrong guess is worse than a generic sentence.",
            ],
            "try": "Read the type before the missing fields, and search your block for the property without "
                   "regard to case.",
            "see": [("/how-to/fix-structured-data-errors/", "How to fix structured data errors")],
        },
    ]),
    ("A decision called a defect, a fix with a cost, a gap nobody reported", [
        {
            "id": "case-dead-crawler-rule",
            "old": "what-a-dead-crawler-rule-costs",
            "title": "What a dead robots.txt rule actually costs",
            "checks": ["ai.dead_crawler_directive"],
            "body": [
                "A computer manufacturer's robots.txt named six retired AI crawler tokens, and we reported at "
                "medium severity that those crawlers were reading pages it meant to withhold. That was false. "
                "The catch-all group carried seventeen Disallow rules, and all seven in the AI group were "
                "repeated there. A crawler that matches no group falls back to User-agent: *, so these fell "
                "back to a stricter group and lost no coverage. Only a Crawl-delay went unheard.",
                "A rule's effect belongs to the group, not to the token. A dead name costs nothing when the "
                "catch-all is stricter or carries the same rules, or when a live replacement sits in the same "
                "group. It is a real exposure only when the catch-all is looser. The comparison is an exact "
                "match on the rules, deliberately crude, so the uncertain case stays reported.",
            ],
            "try": "Compare the AI group's rules with the catch-all's. If every rule also appears under *, the "
                   "dead name has cost you nothing.",
            "see": [("/index/ai-directives/", "How often AI rules name a crawler that no longer answers"),
                    ("/learn/ai-crawler-directives/", "Which AI crawlers to block")],
        },
        {
            "id": "case-policy-or-defect",
            "old": "when-a-policy-is-reported-as-a-defect",
            "title": "When a report calls your decision a defect",
            "checks": ["ai.crawler_access"],
            "body": [
                "A national broadcaster names the AI crawlers that decide whether it can be cited and disallows "
                "them, on purpose, as editorial policy. We called that critical and capped its score. The "
                "opposite case writes the same line: a blanket User-agent: * rule added for an unrelated reason "
                "sweeps up every crawler, and nobody decided it. What separates them is whether the crawler is "
                "named.",
                "Then a worse failure. For a file that named two crawlers and let a wildcard catch a third, the "
                "report said none of them was named, a sentence that set the severity and told the reader to "
                "re-allow two crawlers they had just blocked deliberately. The set is now split: named blocks "
                "are a notice, wildcard-caught ones are the interruption, and an allowlist that names the AI "
                "crawlers it admits counts as policy. The paste-ready block is derived from what was found.",
            ],
            "try": "Open the file and look for the name. Check any report sentence that says none or every "
                   "against the file itself, because that is where reports go wrong.",
            "see": [("/how-to/fix-ai-crawler-access/", "How to fix AI crawler access"),
                    ("/how-to/tell-a-rate-limit-from-a-block/", "A rate limit is not a block")],
        },
        {
            "id": "case-fix-false-negative",
            "old": "when-a-fix-creates-a-false-negative",
            "title": "A fix that hid a real problem somewhere else",
            "checks": ["brand.name_consistency"],
            "body": [
                "A preprint archive's logo link is named “archive home”. The brand-name check strips "
                "navigation words from such a name, so “home” came off and “archive” was "
                "recorded as a second name for the organisation. The fix made the weakest source, a link name, "
                "agree with the one signal a site cannot easily fake: its own domain. The first version asked "
                "that of every residue, and it broke a case a test in the suite holds, a logo naming one "
                "institution on a site titled after another, which is exactly the disagreement the check "
                "exists to find. One site's false positive had been traded for another site's false negative, "
                "and a false negative makes no noise.",
                "The narrower condition applies only when a navigation word had to be removed, because that is "
                "what made the string suspicious. A company whose domain does not contain its name loses that "
                "one source in that case, and its declarations still count. A related guard: a name seen once "
                "across dozens of signals is a single odd page, not a second identity.",
            ],
            "try": "When a false positive you reported gets fixed, ask what the fix cost. A condition that makes a "
                   "rule quieter about you probably made it quieter about someone else.",
            "see": [("/how-to/what-your-site-says-you-are-called/", "Where the name guess comes from"),
                    ("/learn/brand-consistency/", "Brand consistency")],
        },
        {
            "id": "case-silent-gap",
            "old": "when-a-report-says-nothing-at-all",
            "title": "When a report says nothing at all",
            "checks": ["index.broken"],
            "body": [
                "Broken-page checks sort responses into buckets: server errors, not found and gone, refused "
                "requests, and no response at all. The rest of the four-hundred range, where the server "
                "understood the request and rejected it, was never asked about. So a URL on an audited site, "
                "linked from its own pages and rejected by its own server, produced no finding from any "
                "registered check. It was found by accident, while checking that a change to the external link "
                "rule had not silenced the internal one.",
                "Nobody complains about silence. The page is not a not-found, so every report that counts those "
                "shows the site clean while a search engine gets the same refusal as the visitor. Statuses that "
                "mean the crawler itself was turned away, such as a rate limit, stay out on purpose.",
            ],
            "try": "Compare the statuses your site really returns, from logs or a crawl export, with the ones "
                   "your report names. Anything in the first list and not the second is a blind spot.",
            "see": [("/how-to/pages-an-audit-could-not-reach/", "Pages an audit could not reach"),
                    ("/how-to/tell-a-rate-limit-from-a-block/", "A rate limit is not a block")],
        },
    ]),
]

#: Flat list, and the old address of each case, for the stubs and the link rewrites.
CASES = [c for _, cases in GROUPS for c in cases]
OLD_TO_ANCHOR = {c["old"]: c["id"] for c in CASES}
