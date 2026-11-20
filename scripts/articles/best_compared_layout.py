"""HTML for the dated tool facts; page-specific advice stays in each article."""
from html import escape

from ahrefs_first_screen import checked
from best_compared_sources import OWNERSHIP, READ, ordered
from comparisons import source_link


def disclosure():
    return f'<p class="ownership">{OWNERSHIP}</p>'


def method(feature, extra=''):
    return f'''<h2>How this comparison works</h2>
<p>We compare price for a year, the free version and its limit, whether the tool is desktop, cloud or a plugin, and {feature}.
The sources are each vendor's own pages, read on {READ}. This is a comparison of stated facts, not a test score.</p>
<p>The order is free first, then lowest price for a year, with ties alphabetical. Within the free group, we use the entry paid year's price, with tools that state no paid price first.
Tools with an unknown yearly cost follow the priced tools in their group. Trials are not ongoing free versions.
We multiply a monthly price by twelve where no annual total is stated and label that calculation. Add-ons and per-client or per-report charges are marked. {extra}</p>'''


def table(tools, caption):
    rows = []
    for t in ordered(tools):
        annual = ('Year cost not confirmed.' if t.annual is None else
                  f'Year comparison: ${t.annual:,.2f}.')
        links = ', '.join(source_link(label, url) for label, url in t.sources)
        rows.append(f'''<tr data-tool="{escape(t.name)}"><th scope="row">{escape(t.name)}</th>
<td>{escape(t.kind)}</td><td>{escape(t.free)}</td><td>{escape(t.feature)}</td>
<td>{escape(t.price)} {annual}</td><td>{links}. Read {READ}.</td></tr>''')
    return f'''<div class="wrap-tbl"><table class="cmp"><caption>{caption}</caption>
<thead><tr><th scope="col">Tool</th><th scope="col">Where it runs</th><th scope="col">Free version and limit</th>
<th scope="col">Stated feature</th><th scope="col">Price and year comparison</th><th scope="col">Dated sources</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="verified-note">Checked on {escape(', '.join(t.name for t in ordered(tools)))} own pages on {READ}. Each row links the pages used.</p>'''


def sections(tools):
    return '\n'.join(f'''<section data-rival="{escape(t.name)}"><h2>{escape(t.name)}</h2>
<p>{escape(t.detail)}</p>
{checked(t.name, *t.sources)}</section>''' for t in ordered(tools))
