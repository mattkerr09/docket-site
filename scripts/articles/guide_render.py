"""Render guides whose only next step is their own free check or audit."""
from __future__ import annotations

from pathlib import Path

import render as site_render


def render_free_guide(**kwargs) -> Path:
    page = site_render.render(**kwargs)
    src = '-'.join(part for part in (kwargs['cat'], kwargs['slug']) if part)[:60]
    offer = site_render.nofollow_hub_links(site_render.brand_html(site_render.buy_strip(src)))
    html = page.read_text(encoding='utf-8')
    if html.count(offer) != 1:
        raise ValueError(f'{page}: expected one shared offer after rendering')
    html = html.replace(offer, '', 1)
    # The removed price also loses its Offer markup. Keep the site's entity schema.
    priced_entity = site_render.brand_html(
        '<script type="application/ld+json">' + site_render._entity_schema(with_offer=True) + '</script>')
    entity = site_render.brand_html(
        '<script type="application/ld+json">' + site_render._entity_schema(with_offer=False) + '</script>')
    html = html.replace(priced_entity, entity, 1)
    page.write_text(html, encoding='utf-8')
    return page
